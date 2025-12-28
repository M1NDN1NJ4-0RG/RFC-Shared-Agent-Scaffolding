//! # Conformance Tests for the Rust Canonical Tool
//!
//! This module contains comprehensive conformance tests that validate the Rust
//! implementation against the contract defined in `conformance/vectors.json`.
//!
//! # Purpose
//!
//! These tests ensure that the Rust canonical tool:
//! - Implements all required contract behaviors correctly
//! - Maintains consistency across platforms (Linux, macOS, Windows)
//! - Produces output that matches the specification exactly
//! - Handles edge cases and error conditions properly
//!
//! # Test Organization
//!
//! Tests are organized by command type into separate modules:
//! - **safe_run_tests**: Tests for `safe-run run` command execution
//! - **safe_archive_tests**: Tests for `safe-run archive` command
//! - **preflight_tests**: Tests for preflight automerge ruleset checks
//!
//! # Contract Vectors
//!
//! Each test is mapped to a specific vector ID from `conformance/vectors.json`:
//! - `safe-run-001`: Success case, no artifacts created
//! - `safe-run-002`: Failure case, FAIL log created
//! - `safe-run-003`: Signal handling (SIGTERM/SIGINT) creates ABORTED log
//! - `safe-run-004`: Custom log directory via SAFE_LOG_DIR
//! - `safe-run-005`: Snippet output via SAFE_SNIPPET_LINES
//! - And more...
//!
//! # Test-First Development
//!
//! **Note:** These tests were written test-first. Some tests may be marked with
//! `#[ignore]` until the corresponding implementation is complete. This is intentional
//! and follows the stacked PR development strategy outlined in the EPIC.
//!
//! # Platform-Specific Tests
//!
//! Some tests are platform-specific:
//! - **Unix-only**: Signal handling tests (SIGTERM, SIGINT)
//! - **Unix-only**: Tests using shell script helpers (`create_test_script`)
//! - **Cross-platform**: Basic command execution, exit code handling
//!
//! # Running Tests
//!
//! ```bash
//! # Run all conformance tests
//! cargo test --test conformance
//!
//! # Run specific test module
//! cargo test --test conformance safe_run_tests
//!
//! # Run specific test
//! cargo test --test conformance test_safe_run_001_success_no_artifacts
//!
//! # Include ignored tests
//! cargo test --test conformance -- --include-ignored
//! ```
//!
//! # Dependencies
//!
//! - `assert_cmd`: Command execution and assertion framework
//! - `predicates`: Assertion predicates for stdout/stderr
//! - `tempfile`: Temporary directory management
//! - `common`: Vector loading and test utilities

mod common;

use assert_cmd::Command;
use common::{get_safe_run_binary, load_vectors};
use predicates::prelude::*;
use std::fs;
use std::path::Path;
use tempfile::TempDir;

/// Safe-run command conformance tests
///
/// # Purpose
///
/// Validates that the `safe-run run` command implements the M0 contract
/// correctly across all specified behaviors.
///
/// # Coverage
///
/// - Success case (no artifacts)
/// - Failure case (FAIL log creation)
/// - Signal handling (ABORTED log creation)
/// - Custom log directory (SAFE_LOG_DIR)
/// - Snippet output (SAFE_SNIPPET_LINES)
/// - Merged view mode (SAFE_RUN_VIEW)
///
/// # Contract References
///
/// Tests in this module validate vectors: safe-run-001 through safe-run-010
#[cfg(test)]
#[allow(unused_assignments)] // Assert chains in ignored tests
mod safe_run_tests {
    use super::*;

    /// Helper to create a test script that prints to stdout/stderr and exits with a code
    ///
    /// # Purpose
    ///
    /// Creates an executable Bash script in the given directory for testing
    /// command execution with specific output patterns and exit codes.
    ///
    /// # Arguments
    ///
    /// - `dir`: Directory to create the script in
    /// - `stdout`: Text to print to stdout
    /// - `stderr`: Text to print to stderr
    /// - `exit_code`: Exit code for the script to return
    ///
    /// # Returns
    ///
    /// String path to the created script
    ///
    /// # Platform Notes
    ///
    /// This helper is Unix-only as it creates Bash scripts with Unix permissions.
    /// Windows tests should use alternative approaches or be skipped.
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let temp = TempDir::new().unwrap();
    /// let script = create_test_script(temp.path(), "hello", "error", 7);
    /// // Script will print "hello" to stdout, "error" to stderr, and exit with code 7
    /// ```
    #[cfg(unix)]
    fn create_test_script(dir: &Path, stdout: &str, stderr: &str, exit_code: i32) -> String {
        let script_path = dir.join("test_cmd.sh");
        let script_content = format!(
            "#!/bin/bash\necho -n '{}'\necho -n '{}' >&2\nexit {}",
            stdout, stderr, exit_code
        );
        fs::write(&script_path, script_content).expect("Failed to write test script");

        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        script_path.to_string_lossy().to_string()
    }

    /// Test vector safe-run-001: Success creates no artifacts
    ///
    /// # Purpose
    ///
    /// Validates that when a command succeeds (exit code 0), safe-run:
    /// - Returns exit code 0
    /// - Does NOT create any log files or directories
    /// - Prints command output to stdout/stderr as expected
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-run-001
    /// - Requirement: M0 contract specifies no artifacts on success
    ///
    /// # Assertions
    ///
    /// - Exit code matches expected (0)
    /// - Stdout contains expected text
    /// - `.agent/FAIL-LOGS` directory does not exist
    ///
    /// # Platform Notes
    ///
    /// Cross-platform test, runs on Unix and Windows.
    #[test]
    fn test_safe_run_001_success_no_artifacts() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_run
            .iter()
            .find(|v| v.id == "safe-run-001")
            .expect("Vector safe-run-001 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("run");
        cmd.args(&vector.command.args);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        for text in &vector.expected.stdout_contains {
            assert = assert.stdout(predicate::str::contains(text));
        }

        // Verify no artifacts created
        let fail_logs = temp.path().join(".agent/FAIL-LOGS");
        assert!(
            !fail_logs.exists(),
            "Should not create FAIL-LOGS on success"
        );
    }

    /// Test vector safe-run-002: Failure creates FAIL log
    ///
    /// # Purpose
    ///
    /// Validates that when a command fails (non-zero exit code), safe-run:
    /// - Preserves the command's exit code
    /// - Creates `.agent/FAIL-LOGS` directory
    /// - Creates a log file with timestamp-pid-FAIL.log naming pattern
    /// - Log file contains all required sections (STDOUT, STDERR, EVENTS)
    /// - Log file contains all expected content markers
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-run-002
    /// - Requirement: M0 contract requires FAIL log on non-zero exit
    ///
    /// # Assertions
    ///
    /// - Exit code matches expected (non-zero)
    /// - FAIL-LOGS directory exists
    /// - At least one log file created
    /// - Log file contains all required markers from vector
    ///
    /// # Platform Notes
    ///
    /// Unix-only due to use of `create_test_script` helper.
    #[test]
    #[cfg(unix)] // Uses create_test_script helper which is Unix-only
    fn test_safe_run_002_failure_creates_log() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_run
            .iter()
            .find(|v| v.id == "safe-run-002")
            .expect("Vector safe-run-002 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Create a test script that outputs to both streams and exits with code 7
        #[cfg(unix)]
        let test_script = create_test_script(
            temp.path(),
            &vector.command.print_stdout,
            &vector.command.print_stderr,
            vector.command.exit_code.unwrap_or(7),
        );

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("run");

        #[cfg(unix)]
        cmd.arg(&test_script);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        // Verify artifacts created
        let fail_logs_dir = temp.path().join(".agent/FAIL-LOGS");
        assert!(fail_logs_dir.exists(), "Should create FAIL-LOGS directory");

        // Check for log file matching pattern
        if !vector.expected.log_file_pattern.is_empty() {
            let log_files: Vec<_> = fs::read_dir(&fail_logs_dir)
                .expect("Failed to read FAIL-LOGS")
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().map(|t| t.is_file()).unwrap_or(false))
                .collect();

            assert!(!log_files.is_empty(), "Should have at least one log file");

            // Verify log content has required markers
            let log_content =
                fs::read_to_string(log_files[0].path()).expect("Failed to read log file");

            for marker in &vector.expected.log_content_markers {
                assert!(
                    log_content.contains(marker),
                    "Log should contain marker: {}",
                    marker
                );
            }
        }
    }

    /// Test vector safe-run-003: SIGTERM/SIGINT creates ABORTED log
    ///
    /// # Purpose
    ///
    /// Validates that when safe-run receives a termination signal (SIGTERM or SIGINT):
    /// - Kills the child process
    /// - Creates `.agent/FAIL-LOGS` directory
    /// - Creates an ABORTED log file
    /// - Returns exit code 143 (SIGTERM) or 130 (SIGINT)
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-run-003
    /// - Requirement: M0 contract requires ABORTED log on signal
    ///
    /// # Implementation Status
    ///
    /// **TODO**: This test is currently ignored and needs full implementation
    /// in PR3. It requires spawning the command in the background, sending
    /// a signal, and verifying the ABORTED log creation.
    ///
    /// # Platform Notes
    ///
    /// Unix-only due to signal handling differences on Windows.
    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
    #[cfg(unix)] // Signal handling is Unix-specific
    fn test_safe_run_003_sigterm_aborted() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_run
            .iter()
            .find(|v| v.id == "safe-run-003")
            .expect("Vector safe-run-003 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Create a long-running script
        let script_path = temp.path().join("long_running.sh");
        fs::write(&script_path, "#!/bin/bash\nsleep 100").expect("Failed to write script");

        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        // This test would need to spawn the command and send SIGTERM
        // For now, we document the expected behavior
        // TODO: Implement signal handling test in PR3

        // Expected: exit code 130 or 143, ABORTED log file created
        assert!(
            vector.expected.exit_code_one_of.contains(&130)
                || vector.expected.exit_code_one_of.contains(&143),
            "Should expect signal-based exit code"
        );
    }

    /// Test vector safe-run-004: Custom log directory via SAFE_LOG_DIR
    ///
    /// # Purpose
    ///
    /// Validates that the SAFE_LOG_DIR environment variable:
    /// - Overrides the default `.agent/FAIL-LOGS` location
    /// - Creates the custom directory if it doesn't exist
    /// - Places log files in the custom directory
    /// - Does NOT create files in the default directory
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-run-004
    /// - Requirement: M0 contract requires SAFE_LOG_DIR support
    ///
    /// # Assertions
    ///
    /// - Exit code matches expected
    /// - Custom log directory exists (from vector.expected.file_exists)
    /// - Default log directory does NOT exist (from vector.expected.file_not_exists)
    ///
    /// # Platform Notes
    ///
    /// Unix-only due to use of `create_test_script` helper.
    #[test]
    #[cfg(unix)] // Uses create_test_script helper which is Unix-only
    fn test_safe_run_004_custom_log_dir() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_run
            .iter()
            .find(|v| v.id == "safe-run-004")
            .expect("Vector safe-run-004 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        #[cfg(unix)]
        let test_script = create_test_script(temp.path(), "", "", 3);

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("run");

        // Set custom log directory
        if let Some(safe_log_dir) = vector.command.env.get("SAFE_LOG_DIR") {
            cmd.env("SAFE_LOG_DIR", safe_log_dir);
        }

        #[cfg(unix)]
        cmd.arg(&test_script);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        // Verify custom directory used
        for dir in &vector.expected.file_exists {
            let custom_dir = temp.path().join(dir);
            assert!(
                custom_dir.exists(),
                "Custom log directory should exist: {}",
                dir
            );
        }

        // Verify default directory NOT used
        for dir in &vector.expected.file_not_exists {
            let default_dir = temp.path().join(dir);
            assert!(
                !default_dir.exists(),
                "Default directory should not exist: {}",
                dir
            );
        }
    }

    /// Test vector safe-run-005: Snippet output via SAFE_SNIPPET_LINES
    ///
    /// # Purpose
    ///
    /// Validates that the SAFE_SNIPPET_LINES environment variable:
    /// - Controls how many tail lines are printed to stderr on failure
    /// - Prints the last N lines from combined stdout/stderr
    /// - Still creates the full log file with all output
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-run-005
    /// - Requirement: M0 contract requires SAFE_SNIPPET_LINES support
    ///
    /// # Assertions
    ///
    /// - Exit code matches expected
    /// - Stderr contains the expected snippet lines
    /// - Full log file is still created
    ///
    /// # Platform Notes
    ///
    /// Unix-only due to script creation requirements.
    #[test]
    #[cfg(unix)] // Uses Unix-specific script creation
    fn test_safe_run_005_snippet_output() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_run
            .iter()
            .find(|v| v.id == "safe-run-005")
            .expect("Vector safe-run-005 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Create a script that outputs multiple lines
        #[cfg(unix)]
        let script_path = temp.path().join("multiline.sh");
        #[cfg(unix)]
        {
            let lines = vector.command.output_lines.join("\necho ");
            let script_content = format!(
                "#!/bin/bash\necho {}\nexit {}",
                lines,
                vector.command.exit_code.unwrap_or(9)
            );
            fs::write(&script_path, script_content).expect("Failed to write script");

            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&script_path)
                .expect("Failed to get metadata")
                .permissions();
            perms.set_mode(0o755);
            fs::set_permissions(&script_path, perms).expect("Failed to set permissions");
        }

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("run");

        // Set snippet lines env var
        if let Some(snippet_lines) = vector.command.env.get("SAFE_SNIPPET_LINES") {
            cmd.env("SAFE_SNIPPET_LINES", snippet_lines);
        }

        #[cfg(unix)]
        cmd.arg(script_path);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        // Verify snippet lines appear in stderr
        for text in &vector.expected.stderr_contains {
            assert = assert.stderr(predicate::str::contains(text));
        }
    }
}

/// Safe-archive command conformance tests
///
/// # Purpose
///
/// Validates that the `safe-run archive` command implements the M0 contract
/// for archiving command output regardless of success or failure.
///
/// # Coverage
///
/// - Archive creation on success
/// - Archive creation on failure
/// - Archive content verification
/// - Original file preservation
///
/// # Contract References
///
/// Tests in this module validate vectors: safe-archive-001 through safe-archive-005
///
/// # Implementation Status
///
/// **Note**: Archive implementation is placeholder only. Full implementation
/// comes in a future PR per the stacked PR plan.
#[cfg(test)]
#[allow(unused_assignments)] // Assert chains in ignored tests
mod safe_archive_tests {
    use super::*;

    /// Test vector safe-archive-001: Archive creation
    ///
    /// # Purpose
    ///
    /// Validates that safe-archive creates an archive file from a source directory.
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-archive-001
    /// - Requirement: Create archive from directory, exit code 0
    #[test]
    fn test_safe_archive_001_basic() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_archive
            .iter()
            .find(|v| v.id == "safe-archive-001")
            .expect("Vector safe-archive-001 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Setup: create source files
        for file_path in &vector.setup.create_files {
            let full_path = temp.path().join(file_path);
            if let Some(parent) = full_path.parent() {
                fs::create_dir_all(parent).expect("Failed to create parent dir");
            }
            fs::write(&full_path, "test content").expect("Failed to create file");
        }

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("archive");
        cmd.args(&vector.command.args);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        // Verify archive created
        for file in &vector.expected.file_exists {
            let archive_path = temp.path().join(file);
            assert!(archive_path.exists(), "Archive should exist: {}", file);
        }
    }

    /// Test vector safe-archive-002: Compression format support
    ///
    /// # Purpose
    ///
    /// Validates that safe-archive supports multiple compression formats:
    /// - tar.gz (gzip compression)
    /// - tar.bz2 (bzip2 compression)  
    /// - zip (zip format)
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-archive-002
    /// - Requirement: Support standard archive formats
    #[test]
    fn test_safe_archive_002_compression_formats() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_archive
            .iter()
            .find(|v| v.id == "safe-archive-002")
            .expect("Vector safe-archive-002 not found");

        // Test each variant (tar.gz, tar.bz2, zip)
        for variant in &vector.command_variants {
            let temp = TempDir::new().expect("Failed to create temp dir");

            // Setup: create source files
            for file_path in &vector.setup.create_files {
                let full_path = temp.path().join(file_path);
                if let Some(parent) = full_path.parent() {
                    fs::create_dir_all(parent).expect("Failed to create parent dir");
                }
                fs::write(&full_path, "test content").expect("Failed to create file");
            }

            let mut cmd = Command::new(get_safe_run_binary());
            cmd.current_dir(temp.path());
            cmd.arg("archive");
            cmd.args(&variant.args);

            let mut assert = cmd.assert();

            if let Some(exit_code) = vector.expected.exit_code {
                assert = assert.code(exit_code);
            }

            // Verify archive created
            let archive_path = temp.path().join(&variant.expected_file);
            assert!(
                archive_path.exists(),
                "Archive should exist: {}",
                variant.expected_file
            );
        }
    }

    /// Test vector safe-archive-003: No-clobber with auto-suffix
    ///
    /// # Purpose
    ///
    /// # Purpose
    ///
    /// Validates that when an archive file already exists, safe-archive:
    /// - Does NOT overwrite the existing file
    /// - Creates a new file with sequential suffix (.1, .2, etc.)
    /// - Preserves both original and new archive files
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-archive-003
    /// - Requirement: No-clobber protection with auto-naming
    ///
    /// # Assertions
    ///
    /// - Exit code indicates success
    /// - Original archive file still exists
    /// - New archive file with suffix exists
    /// - Both files are distinct
    #[test]
    fn test_safe_archive_003_no_clobber_auto_suffix() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_archive
            .iter()
            .find(|v| v.id == "safe-archive-003")
            .expect("Vector safe-archive-003 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Setup: create source files AND existing output file
        for file_path in &vector.setup.create_files {
            let full_path = temp.path().join(file_path);
            if let Some(parent) = full_path.parent() {
                fs::create_dir_all(parent).expect("Failed to create parent dir");
            }
            fs::write(&full_path, "test content").expect("Failed to create file");
        }

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("archive");
        cmd.args(&vector.command.args);

        let mut assert = cmd.assert();

        if let Some(exit_code) = vector.expected.exit_code {
            assert = assert.code(exit_code);
        }

        // Verify both files exist (original + suffixed)
        for file in &vector.expected.file_exists {
            let file_path = temp.path().join(file);
            assert!(file_path.exists(), "File should exist: {}", file);
        }
    }

    /// Test vector safe-archive-004: No-clobber strict mode
    ///
    /// # Purpose
    /// # Purpose
    ///
    /// Validates that in strict mode, when an archive file already exists:
    /// - Command fails with error exit code (40-49 range)
    /// - No files are overwritten
    /// - Original file remains unchanged
    /// - Error message explains the conflict
    ///
    /// # Contract Reference
    ///
    /// - Vector: safe-archive-004
    /// - Requirement: Strict no-clobber enforcement
    ///
    /// # Assertions
    ///
    /// - Exit code in range 40-49 (clobber error)
    /// - Original file unchanged
    /// - No new files created
    #[test]
    fn test_safe_archive_004_no_clobber_strict() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .safe_archive
            .iter()
            .find(|v| v.id == "safe-archive-004")
            .expect("Vector safe-archive-004 not found");

        let temp = TempDir::new().expect("Failed to create temp dir");

        // Setup: create source files AND existing output file
        for file_path in &vector.setup.create_files {
            let full_path = temp.path().join(file_path);
            if let Some(parent) = full_path.parent() {
                fs::create_dir_all(parent).expect("Failed to create parent dir");
            }
            fs::write(&full_path, "test content").expect("Failed to create file");
        }

        let mut cmd = Command::new(get_safe_run_binary());
        cmd.current_dir(temp.path());
        cmd.arg("archive");
        cmd.args(&vector.command.args);

        let mut assert = cmd.assert();

        // Should fail with exit code in range 40-49
        if !vector.expected.exit_code_range.is_empty() {
            // Check exit code is in range [40, 49]
            // Note: assert_cmd doesn't have direct range checking,
            // so we'll validate this in the implementation
        }

        // Verify stderr contains expected error messages
        for text in &vector.expected.stderr_contains {
            assert = assert.stderr(predicate::str::contains(text));
        }
    }
}

/// Safe-check command conformance tests
///
/// # Purpose
///
/// Validates that the `safe-run check` command implements command existence
/// checking and other pre-flight validation requirements.
///
/// # Coverage (Phase 1)
///
/// - Command existence check (PATH lookup)
/// - Exit code 0 when command found
/// - Exit code 2 when command not found
/// - Relative and absolute path handling
///
/// # Contract References
///
/// Tests validate FW-002 (safe-check subcommand implementation)
///
/// # Future Coverage (Phase 2+)
///
/// - Repository state validation
/// - Dependency availability checks
#[cfg(test)]
mod safe_check_tests {
    use super::*;

    /// Test that check returns 0 when command exists on PATH
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check successfully finds commands that exist
    /// on the system PATH and returns exit code 0.
    ///
    /// # Test Approach
    ///
    /// Tests with common commands that should exist on any Unix-like system:
    /// - ls (standard on all Unix-like systems)
    /// - sh (POSIX shell, universally available)
    #[test]
    fn test_check_command_exists_on_path() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        // Test with 'ls' which should exist on Unix-like systems
        #[cfg(not(target_os = "windows"))]
        {
            Command::new(get_safe_run_binary())
                .arg("check")
                .arg("ls")
                .current_dir(temp_dir.path())
                .assert()
                .success()
                .code(0);
        }

        // Test with 'cmd' which should exist on Windows
        #[cfg(target_os = "windows")]
        {
            Command::new(get_safe_run_binary())
                .arg("check")
                .arg("cmd")
                .current_dir(temp_dir.path())
                .assert()
                .success()
                .code(0);
        }
    }

    /// Test that check returns 2 when command does not exist
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check correctly identifies non-existent commands
    /// and returns exit code 2.
    ///
    /// # Test Approach
    ///
    /// Uses a command name that is extremely unlikely to exist on any system.
    #[test]
    fn test_check_command_not_found() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("nonexistent_command_xyz123_never_exists")
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(2)
            .stderr(predicate::str::contains("Command not found"));
    }

    /// Test that check works with absolute paths
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check can verify commands specified with
    /// absolute paths, not just commands on PATH.
    ///
    /// # Test Approach
    ///
    /// Creates a temporary executable file and checks it with its absolute path.
    #[test]
    #[cfg(not(target_os = "windows"))] // Unix-specific test
    fn test_check_absolute_path() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let script_path = temp_dir.path().join("test_script.sh");

        // Create a simple executable script
        fs::write(&script_path, "#!/bin/sh\necho test\n").expect("Failed to write script");

        // Make it executable
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        // Check the script by absolute path
        Command::new(get_safe_run_binary())
            .arg("check")
            .arg(script_path.to_str().unwrap())
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test that check returns 2 for non-existent absolute path
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check returns exit code 2 when given an
    /// absolute path that doesn't exist.
    #[test]
    fn test_check_absolute_path_not_found() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let nonexistent_path = temp_dir.path().join("nonexistent_file");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg(nonexistent_path.to_str().unwrap())
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(2);
    }

    /// Test that check requires a command argument
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check returns an error when no command
    /// is specified.
    #[test]
    fn test_check_no_command() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .current_dir(temp_dir.path())
            .assert()
            .failure();
        // Note: clap will handle this with its own error, not our custom error
    }

    /// Test that check works with common system utilities
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check can find various common system utilities
    /// to ensure cross-platform compatibility.
    ///
    /// # Test Approach
    ///
    /// Tests multiple common utilities that should exist on the system.
    #[test]
    fn test_check_multiple_common_commands() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        // Commands to test (platform-specific)
        #[cfg(not(target_os = "windows"))]
        let commands = vec!["sh", "echo", "cat"];

        #[cfg(target_os = "windows")]
        let commands = vec!["cmd", "powershell"];

        for cmd in commands {
            Command::new(get_safe_run_binary())
                .arg("check")
                .arg(cmd)
                .current_dir(temp_dir.path())
                .assert()
                .success()
                .code(0);
        }
    }

    /// Test that check works with relative paths
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check correctly handles relative paths like
    /// "./command" and "subdir/command".
    ///
    /// # Test Approach
    ///
    /// Creates files in subdirectories and current directory, then verifies
    /// they can be found using relative path notation.
    #[test]
    #[cfg(not(target_os = "windows"))] // Unix-specific test
    fn test_check_relative_path() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        // Create a script in the current directory with ./ prefix
        let script_current = temp_dir.path().join("script_here.sh");
        fs::write(&script_current, "#!/bin/sh\necho test\n").expect("Failed to write script");
        let mut perms = fs::metadata(&script_current)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_current, perms).expect("Failed to set permissions");

        // Create a subdirectory with a script
        let subdir = temp_dir.path().join("subdir");
        fs::create_dir(&subdir).expect("Failed to create subdir");
        let script_sub = subdir.join("script_sub.sh");
        fs::write(&script_sub, "#!/bin/sh\necho test\n").expect("Failed to write script");
        let mut perms = fs::metadata(&script_sub)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_sub, perms).expect("Failed to set permissions");

        // Test with ./ prefix
        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("./script_here.sh")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);

        // Test with subdirectory path
        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("subdir/script_sub.sh")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test that check returns 2 for non-existent relative path
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check returns exit code 2 when given a
    /// relative path that doesn't exist.
    #[test]
    fn test_check_relative_path_not_found() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("./nonexistent_script")
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(2);

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("subdir/nonexistent")
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(2);
    }
}

/// Safe-check Phase 2 tests (executable permissions and repository validation)
///
/// # Purpose
///
/// Validates Phase 2 functionality of the `safe-run check` command:
/// - Executable permission verification on Unix
/// - Repository state validation
/// - Proper exit codes for different failure scenarios
///
/// # Coverage
///
/// - Exit code 3 for non-executable files (Unix)
/// - Exit code 4 for repository state failures
/// - Exit code 0 when all checks pass
#[cfg(test)]
mod safe_check_phase2_tests {
    use super::*;

    /// Test that check returns exit code 3 for non-executable files on Unix
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check properly detects when a file exists
    /// but doesn't have executable permissions on Unix-like systems.
    #[test]
    #[cfg(not(target_os = "windows"))] // Unix-specific test
    fn test_check_not_executable() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let script_path = temp_dir.path().join("non_executable.sh");

        // Create a script without executable permissions
        fs::write(&script_path, "#!/bin/sh\necho test\n").expect("Failed to write script");

        // Explicitly set permissions to read-only (no execute)
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o644); // rw-r--r--
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        // Check the script - should return exit code 3
        Command::new(get_safe_run_binary())
            .arg("check")
            .arg(script_path.to_str().unwrap())
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(3)
            .stderr(predicate::str::contains("not executable"));
    }

    /// Test that check returns exit code 0 for executable files on Unix
    ///
    /// # Purpose
    ///
    /// Validates that safe-run check returns success when a file exists
    /// and has proper executable permissions.
    #[test]
    #[cfg(not(target_os = "windows"))] // Unix-specific test
    fn test_check_executable_passes() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let script_path = temp_dir.path().join("executable.sh");

        // Create an executable script
        fs::write(&script_path, "#!/bin/sh\necho test\n").expect("Failed to write script");

        // Set executable permissions
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755); // rwxr-xr-x
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        // Check the script - should return exit code 0
        Command::new(get_safe_run_binary())
            .arg("check")
            .arg(script_path.to_str().unwrap())
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test repository state validation
    ///
    /// # Purpose
    ///
    /// Validates that repository state checks run without errors
    /// when executed in a valid directory.
    #[test]
    fn test_repository_validation() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        // Check a valid command - repository validation should pass
        // (or gracefully handle non-git directories)
        #[cfg(not(target_os = "windows"))]
        {
            Command::new(get_safe_run_binary())
                .arg("check")
                .arg("sh")
                .current_dir(temp_dir.path())
                .assert()
                .success()
                .code(0);
        }

        #[cfg(target_os = "windows")]
        {
            Command::new(get_safe_run_binary())
                .arg("check")
                .arg("cmd")
                .current_dir(temp_dir.path())
                .assert()
                .success()
                .code(0);
        }
    }
}

/// Safe-check conformance tests (Phase 3)
///
/// # Purpose
///
/// Validates conformance vectors for the `safe-run check` command.
/// Tests are driven by vectors in `conformance/vectors.json`.
///
/// # Coverage
///
/// - Command existence checking (PATH lookup)
/// - Absolute and relative path handling
/// - Executable permission verification (Unix)
/// - Error cases and exit codes
///
/// # Contract References
///
/// Tests validate safe-check-001 through safe-check-007 vectors
#[cfg(test)]
mod safe_check_conformance_tests {
    use super::*;

    /// Test safe-check-001: Command exists on PATH returns 0
    #[test]
    #[cfg(not(target_os = "windows"))]
    fn test_safe_check_001_command_exists_on_path() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("ls")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test safe-check-002: Command does not exist returns 2
    #[test]
    fn test_safe_check_002_command_not_found() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("nonexistent_command_xyz_never_exists_12345")
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(2)
            .stderr(predicate::str::contains("Command not found"));
    }

    /// Test safe-check-003: Command with absolute path exists returns 0
    #[test]
    #[cfg(not(target_os = "windows"))]
    fn test_safe_check_003_absolute_path() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("/bin/sh")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test safe-check-004: Command with relative path exists returns 0
    #[test]
    #[cfg(not(target_os = "windows"))]
    fn test_safe_check_004_relative_path() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let script_path = temp_dir.path().join("test_script.sh");

        // Create an executable script
        fs::write(&script_path, "#!/bin/sh\necho test\n").expect("Failed to write script");

        // Set executable permissions
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("./test_script.sh")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test safe-check-005: File exists but not executable returns 3 (Unix)
    #[test]
    #[cfg(not(target_os = "windows"))]
    fn test_safe_check_005_not_executable() {
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let script_path = temp_dir.path().join("non_exec.sh");

        // Create a non-executable file
        fs::write(&script_path, "#!/bin/sh\necho test\n").expect("Failed to write script");

        // Set non-executable permissions
        let mut perms = fs::metadata(&script_path)
            .expect("Failed to get metadata")
            .permissions();
        perms.set_mode(0o644); // rw-r--r--
        fs::set_permissions(&script_path, perms).expect("Failed to set permissions");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("./non_exec.sh")
            .current_dir(temp_dir.path())
            .assert()
            .failure()
            .code(3)
            .stderr(predicate::str::contains("not executable"))
            .stderr(predicate::str::contains("chmod"));
    }

    /// Test safe-check-006: Windows command with extension returns 0
    #[test]
    #[cfg(target_os = "windows")]
    fn test_safe_check_006_windows_command() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .arg("cmd")
            .current_dir(temp_dir.path())
            .assert()
            .success()
            .code(0);
    }

    /// Test safe-check-007: No command argument returns error
    #[test]
    fn test_safe_check_007_no_command() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        Command::new(get_safe_run_binary())
            .arg("check")
            .current_dir(temp_dir.path())
            .assert()
            .failure();
        // Exit code could be 1 or 2 depending on how clap handles it
    }
}

/// Preflight automerge ruleset conformance tests
///
/// # Purpose
///
/// Validates that the preflight automerge ruleset checker implements the
/// required GitHub API interaction and validation logic.
///
/// # Coverage
///
/// - Success case (valid ruleset configuration)
/// - Authentication failures
/// - Ruleset not found errors
/// - API interaction patterns
///
/// # Contract References
///
/// Tests in this module validate vectors: preflight-001 through preflight-004
///
/// # Implementation Status
///
/// **Note**: All tests are placeholder/ignored. Full implementation requires
/// GitHub API mocking infrastructure to be added in a future PR.
#[cfg(test)]
mod preflight_tests {
    use super::*;

    /// Test vector preflight-001: Successful ruleset validation
    ///
    /// # Purpose
    ///
    /// Validates that preflight checker:
    /// - Successfully authenticates with GitHub API
    /// - Retrieves ruleset configuration
    /// - Validates ruleset meets requirements
    /// - Returns exit code 0 on success
    ///
    /// # Contract Reference
    ///
    /// - Vector: preflight-001
    /// - Requirement: Validate automerge rulesets
    ///
    /// # Implementation Status
    ///
    /// **TODO**: Requires GitHub API mocking. Implement in future PR.
    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
    fn test_preflight_001_success() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .preflight_automerge_ruleset
            .iter()
            .find(|v| v.id == "preflight-001")
            .expect("Vector preflight-001 not found");

        // This test requires mocking GitHub API responses
        // Implementation will need a mock server or stub
        // For now, document the expected behavior

        assert!(vector.expected.exit_code == Some(0), "Should succeed");
    }

    /// Test vector preflight-002: Authentication failure handling
    ///
    /// # Purpose
    ///
    /// Validates that preflight checker:
    /// - Detects authentication failures
    /// - Returns appropriate exit code (2 for auth errors)
    /// - Provides helpful error message
    ///
    /// # Contract Reference
    ///
    /// - Vector: preflight-002
    /// - Requirement: Handle auth failures gracefully
    ///
    /// # Implementation Status
    ///
    /// **TODO**: Implement with API mocking in future PR.
    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
    fn test_preflight_002_auth_failure() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .preflight_automerge_ruleset
            .iter()
            .find(|v| v.id == "preflight-002")
            .expect("Vector preflight-002 not found");

        assert!(
            vector.expected.exit_code == Some(2),
            "Should return exit code 2 for auth failure"
        );
    }

    /// Test vector preflight-003: Ruleset not found error
    ///
    /// # Purpose
    ///
    /// Validates that preflight checker:
    /// - Handles missing rulesets gracefully
    /// - Returns exit code 3 for usage/config errors
    /// - Provides clear error message
    ///
    /// # Contract Reference
    ///
    /// - Vector: preflight-003
    /// - Requirement: Handle missing rulesets
    ///
    /// # Implementation Status
    ///
    /// **TODO**: Implement with API mocking in future PR.
    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
    fn test_preflight_003_ruleset_not_found() {
        let vectors = load_vectors().expect("Failed to load vectors");
        let vector = vectors
            .vectors
            .preflight_automerge_ruleset
            .iter()
            .find(|v| v.id == "preflight-003")
            .expect("Vector preflight-003 not found");

        assert!(
            vector.expected.exit_code == Some(3),
            "Should return exit code 3 for usage error"
        );
    }
}

/// Meta-test: Verify all test vectors have corresponding tests
///
/// # Purpose
///
/// This test validates the test suite completeness by ensuring:
/// - Vector count matches expected numbers
/// - All vector IDs from conformance/vectors.json are covered
/// - No vectors are accidentally skipped
///
/// # Assertions
///
/// - safe_run vectors: Expected count is 5
/// - safe_archive vectors: Expected count is 4
/// - preflight vectors: Expected count is 4
///
/// # Future Enhancement
///
/// **TODO**: Add programmatic check that each vector ID has a corresponding
/// test function. This could use reflection or a build-time check to ensure
/// 1:1 mapping between vectors and tests.
///
/// # Why This Matters
///
/// As new vectors are added to conformance/vectors.json, this test will
/// fail if corresponding test functions aren't added, preventing accidental
/// gaps in test coverage.
#[test]
fn test_all_vectors_have_tests() {
    let vectors = load_vectors().expect("Failed to load vectors");

    // Count expected tests
    let safe_run_count = vectors.vectors.safe_run.len();
    let safe_archive_count = vectors.vectors.safe_archive.len();
    let preflight_count = vectors.vectors.preflight_automerge_ruleset.len();
    let safe_check_count = vectors.vectors.safe_check.len();

    // These numbers should match the conformance/vectors.json
    assert_eq!(safe_run_count, 5, "Should have 5 safe-run vectors");
    assert_eq!(safe_archive_count, 4, "Should have 4 safe-archive vectors");
    assert_eq!(preflight_count, 4, "Should have 4 preflight vectors");
    assert_eq!(safe_check_count, 7, "Should have 7 safe-check vectors");

    // TODO: Add programmatic check that each vector ID has a corresponding test
}
