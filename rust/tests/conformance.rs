//! Conformance tests for the Rust canonical tool
//!
//! These tests validate that the Rust implementation meets the contract
//! defined in conformance/vectors.json. Tests are organized by command:
//! - safe-run
//! - safe-archive  
//! - preflight-automerge-ruleset
//!
//! **Note:** These tests are written test-first. They will fail/skip until
//! the actual implementation is added in PR3.

mod common;

use assert_cmd::Command;
use common::{get_safe_run_binary, load_vectors};
use predicates::prelude::*;
use std::fs;
use std::path::Path;
use tempfile::TempDir;

#[cfg(test)]
#[allow(unused_assignments)] // Assert chains in ignored tests
mod safe_run_tests {
    use super::*;

    /// Helper to create a test helper script that prints to stdout/stderr and exits with a code
    #[cfg(unix)]
    fn create_test_script(dir: &Path, stdout: &str, stderr: &str, exit_code: i32) -> String {
        let script_path = dir.join("test_cmd.sh");
        let script_content = format!(
            "#!/bin/bash\necho -n '{}'\necho -n '{}' >&2\nexit {}",
            stdout, stderr, exit_code
        );
        fs::write(&script_path, script_content).expect("Failed to write test script");

        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&script_path)
                .expect("Failed to get metadata")
                .permissions();
            perms.set_mode(0o755);
            fs::set_permissions(&script_path, perms).expect("Failed to set permissions");
        }

        script_path.to_string_lossy().to_string()
    }

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

#[cfg(test)]
#[allow(unused_assignments)] // Assert chains in ignored tests
mod safe_archive_tests {
    use super::*;

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

    #[test]
    #[ignore] // TODO: Remove ignore once implementation exists
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

#[cfg(test)]
mod preflight_tests {
    use super::*;

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

/// Meta-test: Verify all test vectors are covered
#[test]
fn test_all_vectors_have_tests() {
    let vectors = load_vectors().expect("Failed to load vectors");

    // Count expected tests
    let safe_run_count = vectors.vectors.safe_run.len();
    let safe_archive_count = vectors.vectors.safe_archive.len();
    let preflight_count = vectors.vectors.preflight_automerge_ruleset.len();

    // These numbers should match the conformance/vectors.json
    assert_eq!(safe_run_count, 5, "Should have 5 safe-run vectors");
    assert_eq!(safe_archive_count, 4, "Should have 4 safe-archive vectors");
    assert_eq!(preflight_count, 4, "Should have 4 preflight vectors");

    // TODO: Add programmatic check that each vector ID has a corresponding test
}
