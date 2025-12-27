use signal_hook::consts::{SIGINT, SIGTERM};
use signal_hook::flag;
use std::env;
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

/// Execute a command with safe-run semantics
///
/// This implements the M0 contract:
/// - Captures stdout/stderr separately with event ledger
/// - Creates log file only on failure (FAIL) or abort (ABORTED)
/// - Preserves exit codes
/// - Handles SIGTERM/SIGINT to create ABORTED logs
/// - Supports SAFE_LOG_DIR, SAFE_SNIPPET_LINES, SAFE_RUN_VIEW environment variables
pub fn execute(command: &[String]) -> Result<i32, String> {
    if command.is_empty() {
        eprintln!("usage: safe-run run <command> [args...]");
        return Ok(2);
    }

    // Get configuration from environment
    let log_dir = env::var("SAFE_LOG_DIR").unwrap_or_else(|_| ".agent/FAIL-LOGS".to_string());
    let snippet_lines: usize = env::var("SAFE_SNIPPET_LINES")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);
    let view_mode = env::var("SAFE_RUN_VIEW").unwrap_or_default();

    // Build command string for META event
    let cmd_str = shell_escape_command(command);

    // Event ledger tracking
    let seq_counter = Arc::new(AtomicU64::new(0));
    let events = Arc::new(Mutex::new(Vec::new()));
    let stdout_buffer = Arc::new(Mutex::new(Vec::new()));
    let stderr_buffer = Arc::new(Mutex::new(Vec::new()));

    // Signal handling: track if we received SIGTERM/SIGINT
    let interrupted = Arc::new(AtomicBool::new(false));

    // Register signal handlers for both SIGTERM and SIGINT
    flag::register(SIGTERM, Arc::clone(&interrupted))
        .map_err(|e| format!("Failed to register SIGTERM handler: {}", e))?;
    flag::register(SIGINT, Arc::clone(&interrupted))
        .map_err(|e| format!("Failed to register SIGINT handler: {}", e))?;

    // Emit start event
    emit_event(
        &seq_counter,
        &events,
        "META",
        &format!("safe-run start: cmd=\"{}\"", cmd_str),
    );

    // Spawn the command
    let mut child = Command::new(&command[0])
        .args(&command[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn command: {}", e))?;

    // Capture stdout
    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    let stdout_events = Arc::clone(&events);
    let stdout_seq = Arc::clone(&seq_counter);
    let stdout_buf = Arc::clone(&stdout_buffer);
    #[allow(clippy::lines_filter_map_ok)]
    let stdout_handle = thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines().flatten() {
            // Print to console
            println!("{}", line);
            // Store in buffer
            match stdout_buf.lock() {
                Ok(mut buf) => {
                    buf.push(line.clone());
                }
                Err(e) => {
                    eprintln!("safe-run: failed to store stdout line: {}", e);
                }
            }
            // Emit event
            emit_event(&stdout_seq, &stdout_events, "STDOUT", &line);
        }
    });

    // Capture stderr
    let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;
    let stderr_events = Arc::clone(&events);
    let stderr_seq = Arc::clone(&seq_counter);
    let stderr_buf = Arc::clone(&stderr_buffer);
    #[allow(clippy::lines_filter_map_ok)]
    let stderr_handle = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines().flatten() {
            // Print to console
            eprintln!("{}", line);
            // Store in buffer
            match stderr_buf.lock() {
                Ok(mut buf) => {
                    buf.push(line.clone());
                }
                Err(e) => {
                    eprintln!("safe-run: failed to store stderr line: {}", e);
                }
            }
            // Emit event
            emit_event(&stderr_seq, &stderr_events, "STDERR", &line);
        }
    });

    // Wait for the command to complete, checking for signals
    let exit_status = loop {
        // Check if we received a signal
        if interrupted.load(Ordering::SeqCst) {
            // Kill the child process
            let _ = child.kill();

            // Wait for threads to finish capturing output
            let _ = stdout_handle.join();
            let _ = stderr_handle.join();

            // Emit exit event for interruption
            emit_event(
                &seq_counter,
                &events,
                "META",
                "safe-run interrupted by signal",
            );

            // Create ABORTED log
            let log_path = save_log(
                &log_dir,
                "ABORTED",
                &stdout_buffer,
                &stderr_buffer,
                &events,
                &view_mode,
            )?;

            eprintln!(
                "safe-run: command aborted by signal. log: {}",
                log_path.display()
            );

            // Exit with conventional signal exit code (128 + signal number)
            // SIGTERM is 15, so 143; SIGINT is 2, so 130
            // We can't distinguish which signal we got with ctrlc, so use SIGTERM code
            return Ok(143);
        }

        // Try to get exit status without blocking forever
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => {
                // Child still running, sleep briefly and check again
                std::thread::sleep(std::time::Duration::from_millis(100));
            }
            Err(e) => return Err(format!("Failed to wait for child: {}", e)),
        }
    };

    // Wait for output capture to complete (propagate panics if they occurred)
    stdout_handle
        .join()
        .map_err(|_| "stdout capture thread panicked".to_string())?;
    stderr_handle
        .join()
        .map_err(|_| "stderr capture thread panicked".to_string())?;

    // Get exit code
    let exit_code = exit_status.code().unwrap_or(1);

    // Emit exit event
    emit_event(
        &seq_counter,
        &events,
        "META",
        &format!("safe-run exit: code={}", exit_code),
    );

    // Success: no artifacts
    if exit_code == 0 {
        return Ok(0);
    }

    // Failure: create log
    let log_path = save_log(
        &log_dir,
        "FAIL",
        &stdout_buffer,
        &stderr_buffer,
        &events,
        &view_mode,
    )?;

    eprintln!(
        "safe-run: command failed (rc={}). log: {}",
        exit_code,
        log_path.display()
    );

    // Print snippet if requested
    if snippet_lines > 0 {
        print_snippet_from_buffers(&stdout_buffer, &stderr_buffer, snippet_lines);
    }

    Ok(exit_code)
}

/// Emit an event to the event ledger
fn emit_event(
    seq_counter: &Arc<AtomicU64>,
    events: &Arc<Mutex<Vec<String>>>,
    stream: &str,
    text: &str,
) {
    let seq = seq_counter.fetch_add(1, Ordering::SeqCst) + 1;
    let event = format!("[SEQ={}][{}] {}", seq, stream, text);

    match events.lock() {
        Ok(mut events_vec) => {
            events_vec.push(event);
        }
        Err(e) => {
            eprintln!(
                "safe-run: failed to record event for stream '{}': {}",
                stream, e
            );
        }
    }
}

/// Save log file with stdout/stderr/events
fn save_log(
    log_dir: &str,
    status: &str,
    stdout_buffer: &Arc<Mutex<Vec<String>>>,
    stderr_buffer: &Arc<Mutex<Vec<String>>>,
    events: &Arc<Mutex<Vec<String>>>,
    view_mode: &str,
) -> Result<PathBuf, String> {
    // Create log directory if it doesn't exist
    fs::create_dir_all(log_dir).map_err(|e| format!("Failed to create log directory: {}", e))?;

    // Generate filename
    let timestamp = chrono::Utc::now().format("%Y%m%dT%H%M%SZ").to_string();
    let pid = std::process::id();
    let base_name = format!("{}-pid{}-{}", timestamp, pid, status);

    // Find non-clobbering filename
    let mut n = 0;
    let mut log_path = PathBuf::from(log_dir).join(format!("{}.log", base_name));
    while log_path.exists() {
        n += 1;
        log_path = PathBuf::from(log_dir).join(format!("{}-{}.log", base_name, n));
    }

    // Write log file with error tracking
    let mut file =
        File::create(&log_path).map_err(|e| format!("Failed to create log file: {}", e))?;

    let mut write_error_logged = false;
    let mut log_write = |result: std::io::Result<()>| {
        if let Err(e) = result {
            if !write_error_logged {
                eprintln!("safe-run: failed writing to log file: {}", e);
                write_error_logged = true;
            }
        }
    };

    // Write stdout section
    log_write(writeln!(file, "=== STDOUT ==="));
    if let Ok(stdout) = stdout_buffer.lock() {
        for line in stdout.iter() {
            log_write(writeln!(file, "{}", line));
        }
    }
    log_write(writeln!(file));

    // Write stderr section
    log_write(writeln!(file, "=== STDERR ==="));
    if let Ok(stderr) = stderr_buffer.lock() {
        for line in stderr.iter() {
            log_write(writeln!(file, "{}", line));
        }
    }
    log_write(writeln!(file));

    // Write events section
    log_write(writeln!(file, "--- BEGIN EVENTS ---"));
    if let Ok(events_vec) = events.lock() {
        for event in events_vec.iter() {
            log_write(writeln!(file, "{}", event));
        }
    }
    log_write(writeln!(file, "--- END EVENTS ---"));

    // Optional merged view
    if view_mode == "merged" {
        log_write(writeln!(file));
        log_write(writeln!(file, "--- BEGIN MERGED (OBSERVED ORDER) ---"));
        if let Ok(events_vec) = events.lock() {
            for event in events_vec.iter() {
                // Convert [SEQ=N] to [#N]
                let merged_line = event.replace("[SEQ=", "[#");
                log_write(writeln!(file, "{}", merged_line));
            }
        }
        log_write(writeln!(file, "--- END MERGED ---"));
    }

    Ok(log_path)
}

/// Print last N lines of stdout/stderr to stderr for quick diagnostics
fn print_snippet_from_buffers(
    stdout_buffer: &Arc<Mutex<Vec<String>>>,
    stderr_buffer: &Arc<Mutex<Vec<String>>>,
    lines: usize,
) {
    eprintln!("--- safe-run failure tail ({} lines) ---", lines);

    // Print last N lines from stdout
    if let Ok(stdout) = stdout_buffer.lock() {
        let start = if stdout.len() > lines {
            stdout.len() - lines
        } else {
            0
        };
        for line in &stdout[start..] {
            eprintln!("{}", line);
        }
    }

    // Print last N lines from stderr
    if let Ok(stderr) = stderr_buffer.lock() {
        let start = if stderr.len() > lines {
            stderr.len() - lines
        } else {
            0
        };
        for line in &stderr[start..] {
            eprintln!("{}", line);
        }
    }

    eprintln!("--- end tail ---");
}

/// Print last N lines of log file to stderr (legacy function, not currently used)
#[allow(dead_code)]
fn print_snippet(log_path: &Path, lines: usize) {
    eprintln!("--- safe-run failure tail ({} lines) ---", lines);

    if let Ok(file) = File::open(log_path) {
        let reader = BufReader::new(file);
        let all_lines: Vec<String> = reader.lines().map_while(Result::ok).collect();
        let start = if all_lines.len() > lines {
            all_lines.len() - lines
        } else {
            0
        };

        for line in &all_lines[start..] {
            eprintln!("{}", line);
        }
    }

    eprintln!("--- end tail ---");
}

/// Escape command for shell representation in META events.
///
/// NOTE: This is for display/logging purposes only, not for safe shell execution.
/// The actual command execution uses Command::new() which does not involve shell
/// interpretation. This function provides a readable representation of the command
/// in log files, but should NOT be used to construct shell commands for execution.
fn shell_escape_command(command: &[String]) -> String {
    command
        .iter()
        .map(|arg| {
            if arg.contains(' ')
                || arg.contains('"')
                || arg.contains('\'')
                || arg.contains('$')
                || arg.contains('\\')
            {
                // Use single quotes and escape any single quotes in the string
                format!("'{}'", arg.replace('\'', "'\\''"))
            } else {
                arg.clone()
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shell_escape_simple() {
        let cmd = vec!["echo".to_string(), "hello".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo hello");
    }

    #[test]
    fn test_shell_escape_spaces() {
        let cmd = vec!["echo".to_string(), "hello world".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo 'hello world'");
    }

    #[test]
    fn test_shell_escape_quotes() {
        let cmd = vec!["echo".to_string(), "hello'world".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo 'hello'\\''world'");
    }
}
