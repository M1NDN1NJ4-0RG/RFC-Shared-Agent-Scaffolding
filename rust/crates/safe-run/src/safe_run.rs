//! # Safe-Run Implementation Module
//!
//! This module implements the core safe-run contract behavior as specified in
//! RFC-Shared-Agent-Scaffolding-v0.1.0.md.
//!
//! # Purpose
//!
//! Provides the canonical implementation of command execution with:
//! - Structured event ledger with monotonic sequence numbers
//! - Separate stdout/stderr capture and pass-through
//! - Artifact generation only on failure or abort
//! - Signal handling for graceful interruption
//! - Configurable output modes (ledger vs merged)
//!
//! # Contract Compliance
//!
//! This implementation conforms to the M0 contract specification:
//! - Event ledger format: `[SEQ=N][STREAM] content`
//! - Log creation: Only on non-zero exit or signal abort
//! - Exit code preservation: Exact exit codes propagated
//! - Signal mapping: SIGINT → 130, SIGTERM → 143
//! - No-clobber file naming with sequential suffixes
//!
//! # Environment Variables Consumed
//!
//! - `SAFE_LOG_DIR`: Directory for failure logs (default: `.agent/FAIL-LOGS`)
//! - `SAFE_SNIPPET_LINES`: Number of tail lines to print on failure (default: 0)
//! - `SAFE_RUN_VIEW`: Output mode (`merged` for human-readable view, default: ledger-only)
//!
//! # Thread Safety
//!
//! This module uses thread-safe primitives (Arc, Mutex, AtomicU64, AtomicBool) to
//! coordinate between the main thread and stdout/stderr capture threads.
//!
//! # Platform Notes
//!
//! - **Unix**: Full signal handling support
//! - **Windows**: Limited signal support (uses signal_hook crate compatibility layer)
//! - **Newlines**: Platform-native line endings in log files
//!
//! # Examples
//!
//! ```no_run
//! # mod safe_run { pub fn execute(cmd: &[String]) -> Result<i32, String> { Ok(0) } }
//! # use std::env;
//! use safe_run::execute;
//!
//! // Execute a simple command
//! let result = execute(&["echo".to_string(), "hello".to_string()]);
//! assert_eq!(result.unwrap(), 0);
//!
//! // Execute with custom log directory
//! env::set_var("SAFE_LOG_DIR", "custom_logs");
//! let result = execute(&["false".to_string()]);
//! assert_eq!(result.unwrap(), 1);
//! ```

#[cfg(unix)]
use signal_hook::consts::{SIGINT, SIGTERM};
#[cfg(unix)]
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
/// # Purpose
///
/// Implements the M0 contract for command execution with structured logging
/// and artifact generation. This is the primary entry point for the safe-run
/// subcommand.
///
/// # Arguments
///
/// - `command`: Slice of strings representing the command and its arguments.
///   First element is the command name, remaining elements are arguments.
///
/// # Returns
///
/// - `Ok(exit_code)`: Command executed, returns the exit code (0 for success, non-zero for failure)
/// - `Err(message)`: Tool error (spawn failure, signal handler registration failure)
///
/// # Behavior
///
/// 1. Validates command is non-empty
/// 2. Reads configuration from environment variables
/// 3. Spawns command with piped stdout/stderr
/// 4. Captures output in separate threads with event ledger
/// 5. Waits for completion while monitoring for signals
/// 6. On success (exit 0): Returns with no artifacts
/// 7. On failure (exit ≠ 0): Creates FAIL log and optionally prints snippet
/// 8. On signal: Kills command, creates ABORTED log, exits with 130/143
///
/// # Environment Variables
///
/// - `SAFE_LOG_DIR`: Log directory path (default: `.agent/FAIL-LOGS`)
/// - `SAFE_SNIPPET_LINES`: Tail lines to print on failure, 0 disables (default: 0)
/// - `SAFE_RUN_VIEW`: View mode, `merged` for human-readable (default: empty/ledger-only)
///
/// # Exit Codes
///
/// - 0: Command succeeded
/// - 1-127: Command exit code (preserved exactly)
/// - 130: Command interrupted by SIGINT (Ctrl-C)
/// - 143: Command interrupted by SIGTERM
/// - 2: Invalid usage (empty command)
///
/// # Thread Safety
///
/// Uses Arc/Mutex for shared state between main thread and capture threads.
/// Atomic operations ensure correct event sequencing and signal detection.
///
/// # Platform Notes
///
/// - **Unix**: Full signal support, pid-based log naming
/// - **Windows**: signal_hook provides compatibility layer for signals
/// - **Line buffering**: BufReader::lines() handles platform line endings
///
/// # Contract References
///
/// - safe-run-001: Success creates no artifacts
/// - safe-run-002: Failure creates FAIL log with stdout/stderr/events
/// - safe-run-003: Exit code preservation
/// - safe-run-004: Snippet lines feature (SAFE_SNIPPET_LINES)
/// - safe-run-005: Custom log directory (SAFE_LOG_DIR)
/// - safe-run-006: Signal handling creates ABORTED log
/// - safe-run-007: Event ledger with SEQ monotonicity
/// - safe-run-008: Merged view mode support
///
/// # Panics
///
/// Does not panic. All errors are returned as `Result::Err` with descriptive messages.
///
/// # Examples
///
/// ```no_run
/// # fn execute(cmd: &[String]) -> Result<i32, String> { Ok(0) }
/// // Success case (no artifacts)
/// let result = execute(&["echo".to_string(), "hello".to_string()]);
/// assert_eq!(result.unwrap(), 0);
///
/// // Failure case (creates FAIL log)
/// let result = execute(&["false".to_string()]);
/// assert_eq!(result.unwrap(), 1);
///
/// // With snippet output
/// std::env::set_var("SAFE_SNIPPET_LINES", "5");
/// let result = execute(&["sh".to_string(), "-c".to_string(), "echo ERR >&2; exit 3".to_string()]);
/// assert_eq!(result.unwrap(), 3);
/// ```
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

    // Signal handling: track which signal we received
    // Use separate flags so we can differentiate SIGINT (130) from SIGTERM (143)
    #[cfg(unix)]
    let sigint_received = Arc::new(AtomicBool::new(false));
    #[cfg(unix)]
    let sigterm_received = Arc::new(AtomicBool::new(false));

    // Register signal handlers for both SIGTERM and SIGINT
    #[cfg(unix)]
    flag::register(SIGTERM, Arc::clone(&sigterm_received))
        .map_err(|e| format!("Failed to register SIGTERM handler: {}", e))?;
    #[cfg(unix)]
    flag::register(SIGINT, Arc::clone(&sigint_received))
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
    let stdout_handle = thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines().map_while(Result::ok) {
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
    let stderr_handle = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines().map_while(Result::ok) {
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
        // Check if we received a signal - check SIGINT first (more specific)
        #[cfg(unix)]
        let got_sigint = sigint_received.load(Ordering::SeqCst);
        #[cfg(unix)]
        let got_sigterm = sigterm_received.load(Ordering::SeqCst);
        #[cfg(not(unix))]
        let got_sigint = false;
        #[cfg(not(unix))]
        let got_sigterm = false;

        if got_sigint || got_sigterm {
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

            // Exit with conventional signal exit code (128 + signal number).
            // SIGINT (2) → 130, SIGTERM (15) → 143
            // Check SIGINT first since it's more specific (user Ctrl-C)
            let exit_code = if got_sigint {
                130 // 128 + SIGINT (2)
            } else {
                143 // 128 + SIGTERM (15)
            };
            return Ok(exit_code);
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
///
/// # Purpose
///
/// Records an event with a monotonically increasing sequence number in the shared
/// event ledger. Events are formatted according to the contract specification:
/// `[SEQ=N][STREAM] content`
///
/// # Arguments
///
/// - `seq_counter`: Atomic counter for monotonic sequence numbers
/// - `events`: Thread-safe vector of event strings
/// - `stream`: Event stream type (`STDOUT`, `STDERR`, or `META`)
/// - `text`: Event content (line of output or metadata message)
///
/// # Behavior
///
/// 1. Atomically increments sequence counter (fetch_add ensures no gaps)
/// 2. Formats event as `[SEQ=N][STREAM] text`
/// 3. Appends to events vector (mutex-protected for thread safety)
/// 4. Logs error to stderr if mutex is poisoned (non-fatal)
///
/// # Thread Safety
///
/// Safe to call concurrently from multiple threads. Sequence numbers are guaranteed
/// to be unique and monotonic (no gaps, no duplicates).
///
/// # Contract References
///
/// - Event format: `[SEQ=N][STREAM] content` per M0 specification
/// - Sequence monotonicity: Required by safe-run-007 vector
/// - Stream types: STDOUT, STDERR, META per contract
///
/// # Examples
///
/// ```no_run
/// use std::sync::{Arc, Mutex};
/// use std::sync::atomic::{AtomicU64, Ordering};
///
/// let seq = Arc::new(AtomicU64::new(0));
/// let events = Arc::new(Mutex::new(Vec::new()));
///
/// emit_event(&seq, &events, "STDOUT", "Hello");
/// emit_event(&seq, &events, "META", "Command started");
///
/// let events_vec = events.lock().unwrap();
/// assert_eq!(events_vec[0], "[SEQ=1][STDOUT] Hello");
/// assert_eq!(events_vec[1], "[SEQ=2][META] Command started");
/// ```
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
///
/// # Purpose
///
/// Creates a timestamped log file containing the complete execution record:
/// stdout section, stderr section, event ledger, and optionally a merged view.
///
/// # Arguments
///
/// - `log_dir`: Directory path for log file (created if doesn't exist)
/// - `status`: Status suffix for filename (`FAIL` or `ABORTED`)
/// - `stdout_buffer`: Captured stdout lines
/// - `stderr_buffer`: Captured stderr lines
/// - `events`: Event ledger entries
/// - `view_mode`: Output mode (`merged` enables merged view section)
///
/// # Returns
///
/// - `Ok(PathBuf)`: Path to created log file
/// - `Err(String)`: Error message if directory creation or file write fails
///
/// # Behavior
///
/// 1. Creates log directory if it doesn't exist
/// 2. Generates filename: `YYYYMMDDTHHMMSSZ-pidN-STATUS.log`
/// 3. Finds non-clobbering filename (appends -1, -2, etc. if file exists)
/// 4. Writes log sections in order:
///    - `=== STDOUT ===` (all captured stdout lines)
///    - `=== STDERR ===` (all captured stderr lines)
///    - `--- BEGIN EVENTS ---` ... `--- END EVENTS ---` (event ledger)
///    - `--- BEGIN MERGED (OBSERVED ORDER) ---` ... `--- END MERGED ---` (if view_mode=merged)
/// 5. Logs write errors to stderr but continues (best-effort)
///
/// # File Naming
///
/// - Base: `20241227T120530Z-pid12345-FAIL.log`
/// - If exists: `20241227T120530Z-pid12345-FAIL-1.log`, then `-2.log`, etc.
/// - Timestamp: UTC in ISO 8601 compact format
/// - PID: Process ID for uniqueness across concurrent runs
///
/// # Security Notes
///
/// - **No-clobber**: Ensures existing files are never overwritten
/// - **Path traversal**: log_dir is used as-is (caller must validate)
/// - **Permissions**: Files created with default permissions (not hardened)
///
/// # Environment Variables
///
/// None directly consumed, but `log_dir` parameter typically comes from `SAFE_LOG_DIR`.
///
/// # Performance Notes
///
/// - Writes are buffered through File handle
/// - Write errors logged but don't abort (best-effort delivery)
/// - Mutex locking is brief (clone data then release)
///
/// # Contract References
///
/// - safe-run-002: Log format with STDOUT/STDERR/EVENTS sections
/// - safe-run-006: ABORTED status for signal interruption
/// - safe-run-008: Merged view mode support
/// - No-clobber: Implicit requirement for CI artifact safety
///
/// # Examples
///
/// ```no_run
/// use std::sync::{Arc, Mutex};
///
/// let stdout_buf = Arc::new(Mutex::new(vec!["line1".to_string()]));
/// let stderr_buf = Arc::new(Mutex::new(vec!["error1".to_string()]));
/// let events = Arc::new(Mutex::new(vec!["[SEQ=1][META] start".to_string()]));
///
/// let path = save_log(".agent/FAIL-LOGS", "FAIL", &stdout_buf, &stderr_buf, &events, "");
/// assert!(path.is_ok());
/// ```
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
///
/// # Purpose
///
/// Provides a quick failure diagnostic by printing the tail of captured output
/// to stderr. This is used when `SAFE_SNIPPET_LINES` is set to show context
/// without requiring the user to open the log file.
///
/// # Arguments
///
/// - `stdout_buffer`: Captured stdout lines
/// - `stderr_buffer`: Captured stderr lines
/// - `lines`: Number of lines to print from the end of each buffer
///
/// # Behavior
///
/// 1. Prints header: `--- safe-run failure tail (N lines) ---`
/// 2. Prints last N lines from stdout (or all if fewer than N)
/// 3. Prints last N lines from stderr (or all if fewer than N)
/// 4. Prints footer: `--- end tail ---`
/// 5. All output goes to stderr (so it doesn't mix with stdout in pipelines)
///
/// # Thread Safety
///
/// Safe to call after capture threads have completed. Brief mutex locks to read buffers.
///
/// # Environment Variables
///
/// - `SAFE_SNIPPET_LINES`: Controls N (parsed by caller)
///
/// # Contract References
///
/// - safe-run-004: Snippet lines feature (SAFE_SNIPPET_LINES)
/// - safe-run-005: Must show last N lines from combined output
///
/// # Examples
///
/// ```no_run
/// use std::sync::{Arc, Mutex};
///
/// let stdout_buf = Arc::new(Mutex::new(vec!["line1".to_string(), "line2".to_string(), "line3".to_string()]));
/// let stderr_buf = Arc::new(Mutex::new(vec!["error1".to_string()]));
///
/// print_snippet_from_buffers(&stdout_buf, &stderr_buf, 2);
/// // Prints to stderr:
/// // --- safe-run failure tail (2 lines) ---
/// // line2
/// // line3
/// // error1
/// // --- end tail ---
/// ```
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
///
/// # Purpose
///
/// Legacy implementation of snippet printing that reads from the log file
/// instead of the in-memory buffers. This function is kept for reference
/// but is not currently used in favor of `print_snippet_from_buffers`.
///
/// # Arguments
///
/// - `log_path`: Path to log file
/// - `lines`: Number of lines to print from the end
///
/// # Behavior
///
/// 1. Opens log file and reads all lines
/// 2. Prints last N lines to stderr
/// 3. Silently continues if file cannot be opened
///
/// # Why Not Used
///
/// The in-memory buffer approach (`print_snippet_from_buffers`) is preferred because:
/// - More efficient (no file I/O required)
/// - More reliable (doesn't depend on successful file write)
/// - Available even if log file creation fails
///
/// # Usage Notes
///
/// This helper is intentionally kept private and is not part of the public API.
/// It exists as an alternative implementation that operates on log files directly.
/// Callers should prefer `print_snippet_from_buffers`, which avoids file I/O.
///
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
/// # Purpose
///
/// Generates a human-readable shell-style representation of the command for
/// logging in META events. This is for display/diagnostics only, not for
/// actual shell execution.
///
/// # Arguments
///
/// - `command`: Command and arguments to escape
///
/// # Returns
///
/// String with space-separated arguments, quoting applied where needed
///
/// # Quoting Rules
///
/// - Simple args (no special chars): `echo hello` → `echo hello`
/// - Args with spaces: `echo "hello world"` → `echo 'hello world'`
/// - Args with quotes: `echo "I'm here"` → `echo 'I'\''m here'`
/// - Args with shell metacharacters ($, \, etc.): Single-quoted
///
/// # Security Warning
///
/// **This function is for logging only, NOT for safe shell execution.**
/// The actual command execution uses `Command::new()` which does NOT
/// involve shell interpretation, making it safe from shell injection.
///
/// Using the output of this function to construct shell commands would
/// be UNSAFE and is NOT the intended use case.
///
/// # Platform Notes
///
/// - Uses POSIX shell quoting rules (single quotes with '\'' escape)
/// - Output may not be valid for cmd.exe or PowerShell
/// - Intended for Unix-like shell display only
///
/// # Examples
///
/// ```
/// # fn shell_escape_command(cmd: &[String]) -> String { String::new() }
/// let cmd1 = vec!["echo".to_string(), "hello".to_string()];
/// assert_eq!(shell_escape_command(&cmd1), "echo hello");
///
/// let cmd2 = vec!["echo".to_string(), "hello world".to_string()];
/// assert_eq!(shell_escape_command(&cmd2), "echo 'hello world'");
///
/// let cmd3 = vec!["echo".to_string(), "I'm here".to_string()];
/// assert_eq!(shell_escape_command(&cmd3), r"echo 'I'\''m here'");
/// ```
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

/// Unit tests for shell escape functionality
///
/// # Purpose
///
/// Validates the shell_escape_command function's quoting behavior for various
/// input patterns. These tests ensure META event logging displays commands
/// correctly without introducing quoting bugs.
///
/// # Coverage
///
/// - Simple arguments (no quoting needed)
/// - Arguments with spaces (single-quoted)
/// - Arguments with single quotes (escaped as '\'' sequence)
///
/// # Contract References
///
/// While not directly specified in the contract, proper command logging
/// in META events is essential for debugging and audit trails.
#[cfg(test)]
mod tests {
    use super::*;

    /// Test shell escaping for simple arguments without special characters
    ///
    /// # Purpose
    ///
    /// Verifies that simple arguments are passed through unquoted for
    /// readability in log files.
    ///
    /// # Asserts
    ///
    /// `echo hello` → `echo hello` (no quoting applied)
    #[test]
    fn test_shell_escape_simple() {
        let cmd = vec!["echo".to_string(), "hello".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo hello");
    }

    /// Test shell escaping for arguments containing spaces
    ///
    /// # Purpose
    ///
    /// Verifies that arguments with spaces are single-quoted to preserve
    /// them as a single argument in the displayed command.
    ///
    /// # Asserts
    ///
    /// `echo "hello world"` → `echo 'hello world'`
    #[test]
    fn test_shell_escape_spaces() {
        let cmd = vec!["echo".to_string(), "hello world".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo 'hello world'");
    }

    /// Test shell escaping for arguments containing single quotes
    ///
    /// # Purpose
    ///
    /// Verifies that single quotes within arguments are properly escaped
    /// using the '\'' sequence (end quote, escaped quote, start quote).
    ///
    /// # Asserts
    ///
    /// `echo "hello'world"` → `echo 'hello'\''world'`
    ///
    /// # Notes
    ///
    /// The '\'' escape sequence is the standard POSIX way to include a
    /// literal single quote within a single-quoted string.
    #[test]
    fn test_shell_escape_quotes() {
        let cmd = vec!["echo".to_string(), "hello'world".to_string()];
        assert_eq!(shell_escape_command(&cmd), "echo 'hello'\\''world'");
    }
}
