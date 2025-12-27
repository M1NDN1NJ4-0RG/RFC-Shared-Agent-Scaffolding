//! # Snapshot Testing Utilities for Golden Output Comparison
//!
//! This module provides infrastructure for snapshot testing - comparing actual
//! command outputs against golden/expected outputs stored in the `snapshots/` directory.
//!
//! # Purpose
//!
//! Enables regression testing by capturing "golden" outputs from known-good runs
//! and comparing future runs against them. This is essential for validating that
//! the Rust canonical tool produces byte-for-byte identical output to the contract
//! specification.
//!
//! # Normalization Strategy
//!
//! Since some output elements vary between runs (PIDs, timestamps) or platforms
//! (line endings), this module provides normalization to make comparisons deterministic:
//!
//! - **Line endings**: CRLF → LF (Windows/Unix compatibility)
//! - **Trailing whitespace**: Stripped per line
//! - **PIDs**: Replaced with `{PID}` placeholder
//! - **Timestamps**: Replaced with `{TIMESTAMP}` placeholder (ISO 8601 format)
//!
//! # Snapshot Storage
//!
//! Snapshots are stored as `.txt` files in `rust/tests/snapshots/` with names
//! corresponding to the test case they represent.
//!
//! # Usage Pattern
//!
//! 1. Run test with actual command execution
//! 2. Normalize output using `normalize_output()`
//! 3. Compare against stored snapshot using `matches_snapshot()`
//! 4. Generate new snapshots using `save_snapshot()` when updating goldens
//!
//! # Contract References
//!
//! - Supports conformance testing for all safe-run vectors
//! - Enables wrapper parity validation (compare Bash/Perl/Python/PowerShell against Rust)
//! - Enforces output stability guarantees
//!
//! # Platform Notes
//!
//! - **Unix**: LF line endings native
//! - **Windows**: CRLF normalized to LF for comparison
//! - **PIDs**: Process IDs vary, always normalized
//! - **Timestamps**: UTC timestamps vary, always normalized
//!
//! # Examples
//!
//! ```no_run
//! # use std::fs;
//! // Save a golden output
//! save_snapshot("safe-run-001-success", "=== STDOUT ===\nhello\n").unwrap();
//!
//! // Compare actual against golden
//! let actual = "=== STDOUT ===\r\nhello\r\n";  // Windows line endings
//! assert!(matches_snapshot("safe-run-001-success", actual));
//! ```

#![allow(dead_code)] // Functions will be used in PR3

use once_cell::sync::Lazy;
use regex::Regex;
use std::fs;
use std::path::{Path, PathBuf};

// Compile regexes once at module initialization for performance
// These regexes are used for normalizing variable output elements

/// Regex for matching PID patterns in log filenames and content
///
/// Matches patterns like `pid12345` for replacement with `{PID}` placeholder.
/// Uses lazy static initialization to compile once and reuse.
static PID_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"pid\d+").unwrap());

/// Regex for matching ISO 8601 compact timestamp patterns
///
/// Matches timestamps like `20241227T120530Z` for replacement with `{TIMESTAMP}` placeholder.
/// Uses lazy static initialization to compile once and reuse.
static TIMESTAMP_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d{8}T\d{6}Z").unwrap());

/// Get the snapshots directory path
///
/// # Purpose
///
/// Returns the absolute path to the `tests/snapshots/` directory where
/// golden output files are stored.
///
/// # Returns
///
/// PathBuf pointing to `rust/tests/snapshots/` relative to the cargo manifest
///
/// # Examples
///
/// ```text
/// let dir = snapshots_dir();
/// assert!(dir.ends_with("tests/snapshots"));
/// ```
pub fn snapshots_dir() -> PathBuf {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    Path::new(manifest_dir).join("tests").join("snapshots")
}

/// Load a snapshot file
///
/// # Purpose
///
/// Reads a golden output file from the snapshots directory.
///
/// # Arguments
///
/// - `name`: Snapshot name (without `.txt` extension)
///
/// # Returns
///
/// - `Ok(String)`: Snapshot content
/// - `Err(std::io::Error)`: File not found or read error
///
/// # File Naming
///
/// Snapshot files are stored as `{name}.txt` in the snapshots directory.
///
/// # Examples
///
/// ```no_run
/// let content = load_snapshot("safe-run-001-success").unwrap();
/// assert!(content.contains("STDOUT"));
/// ```
pub fn load_snapshot(name: &str) -> Result<String, std::io::Error> {
    let snapshot_path = snapshots_dir().join(format!("{}.txt", name));
    fs::read_to_string(snapshot_path)
}

/// Save a snapshot file (for generating golden outputs)
///
/// # Purpose
///
/// Writes content to a snapshot file, creating the snapshots directory
/// if it doesn't exist. Used to update golden outputs when contract behavior
/// changes or new test cases are added.
///
/// # Arguments
///
/// - `name`: Snapshot name (without `.txt` extension)
/// - `content`: Golden output content to save
///
/// # Returns
///
/// - `Ok(())`: File saved successfully
/// - `Err(std::io::Error)`: Directory creation or write error
///
/// # Side Effects
///
/// - Creates `tests/snapshots/` directory if missing
/// - Overwrites existing snapshot file if present
///
/// # Security Notes
///
/// - Caller must validate `name` doesn't contain path traversal sequences
/// - Files written with default permissions
///
/// # Examples
///
/// ```no_run
/// save_snapshot("safe-run-001-success", "=== STDOUT ===\nhello\n").unwrap();
/// ```
pub fn save_snapshot(name: &str, content: &str) -> Result<(), std::io::Error> {
    let snapshot_path = snapshots_dir().join(format!("{}.txt", name));

    // Create snapshots directory if it doesn't exist
    if let Some(parent) = snapshot_path.parent() {
        fs::create_dir_all(parent)?;
    }

    fs::write(snapshot_path, content)
}

/// Compare actual output with snapshot
///
/// # Purpose
///
/// Performs normalized comparison between actual command output and
/// stored golden output. Returns true if outputs match after normalization.
///
/// # Arguments
///
/// - `name`: Snapshot name to compare against
/// - `actual`: Actual output from command execution
///
/// # Returns
///
/// - `true`: Outputs match (after normalization)
/// - `false`: Outputs differ or snapshot not found
///
/// # Normalization
///
/// Both expected and actual outputs are normalized before comparison:
/// - Line endings normalized to LF
/// - Trailing whitespace stripped
/// - PIDs replaced with `{PID}`
/// - Timestamps replaced with `{TIMESTAMP}`
///
/// # Contract References
///
/// - Enforces output stability per conformance vectors
/// - Validates cross-platform consistency
///
/// # Examples
///
/// ```no_run
/// let actual = "=== STDOUT ===\r\nhello\r\n";  // Windows format
/// assert!(matches_snapshot("safe-run-001-success", actual));
/// ```
pub fn matches_snapshot(name: &str, actual: &str) -> bool {
    match load_snapshot(name) {
        Ok(expected) => normalize_output(&expected) == normalize_output(actual),
        Err(_) => false,
    }
}

/// Normalize output for comparison
///
/// # Purpose
///
/// Applies platform-independent normalization to command output, making
/// comparisons deterministic across different runs and platforms.
///
/// # Arguments
///
/// - `output`: Raw command output
///
/// # Returns
///
/// Normalized string suitable for comparison
///
/// # Normalization Rules (Contract-Allowed)
///
/// 1. **Line endings**: CRLF (`\r\n`) → LF (`\n`)
/// 2. **Trailing whitespace**: Stripped from each line
/// 3. **PIDs**: Patterns like `pid12345` → `pid{PID}`
/// 4. **Timestamps**: Patterns like `20241227T120530Z` → `{TIMESTAMP}`
///
/// # Contract Compliance
///
/// These normalizations are explicitly allowed by the M0 contract specification
/// for cross-platform testing. Core output content must remain byte-for-byte
/// identical after normalization.
///
/// # Platform Notes
///
/// - **Unix**: Already uses LF, normalization is a no-op for line endings
/// - **Windows**: CRLF normalized to LF for comparison with Unix snapshots
/// - **PIDs**: Always vary between runs, must be normalized
/// - **Timestamps**: Always vary between runs, must be normalized
///
/// # Examples
///
/// ```
/// let windows_output = "hello\r\nworld\r\n";
/// let unix_output = "hello\nworld\n";
/// assert_eq!(normalize_output(windows_output), normalize_output(unix_output));
///
/// let output_with_pid = "log: pid12345-FAIL.log";
/// let normalized = normalize_output(output_with_pid);
/// assert!(normalized.contains("pid{PID}"));
/// ```
pub fn normalize_output(output: &str) -> String {
    output
        // Normalize line endings to LF
        .replace("\r\n", "\n")
        // Trim trailing whitespace from each line
        .lines()
        .map(|line| line.trim_end())
        .collect::<Vec<_>>()
        .join("\n")
        // Normalize PID values to a placeholder
        .replace_pid_with_placeholder()
        // Normalize timestamps to a placeholder
        .replace_timestamp_with_placeholder()
}

/// Helper trait to normalize PIDs in output
///
/// # Purpose
///
/// Extends `str` with a method to replace variable PID values with a
/// consistent placeholder for snapshot comparison.
///
/// # Pattern
///
/// Replaces `pid` followed by digits (e.g., `pid12345`) with `pid{PID}`.
trait NormalizePid {
    fn replace_pid_with_placeholder(&self) -> String;
}

impl NormalizePid for str {
    /// Replace PID patterns with placeholder
    ///
    /// # Behavior
    ///
    /// Uses compiled regex to find and replace all occurrences of `pid\d+`
    /// with the placeholder `pid{PID}`.
    ///
    /// # Examples
    ///
    /// - `pid12345` → `pid{PID}`
    /// - `20241227T120530Z-pid9876-FAIL.log` → `20241227T120530Z-pid{PID}-FAIL.log`
    fn replace_pid_with_placeholder(&self) -> String {
        // Replace patterns like "pid12345" or "PID=12345" with placeholder
        // This is a simple implementation; may need refinement based on actual output format
        PID_REGEX.replace_all(self, "pid{PID}").to_string()
    }
}

/// Helper trait to normalize timestamps in output
///
/// # Purpose
///
/// Extends `str` with a method to replace variable timestamp values with a
/// consistent placeholder for snapshot comparison.
///
/// # Pattern
///
/// Replaces ISO 8601 compact timestamps (e.g., `20241227T120530Z`) with `{TIMESTAMP}`.
trait NormalizeTimestamp {
    fn replace_timestamp_with_placeholder(&self) -> String;
}

impl NormalizeTimestamp for str {
    /// Replace timestamp patterns with placeholder
    ///
    /// # Behavior
    ///
    /// Uses compiled regex to find and replace all occurrences of ISO 8601
    /// compact timestamps with the placeholder `{TIMESTAMP}`.
    ///
    /// # Format
    ///
    /// Matches: `YYYYMMDDTHHMMSSZ` (e.g., `20241227T120530Z`)
    ///
    /// # Examples
    ///
    /// - `20241227T120530Z` → `{TIMESTAMP}`
    /// - `20241227T120530Z-pid123-FAIL.log` → `{TIMESTAMP}-pid123-FAIL.log`
    fn replace_timestamp_with_placeholder(&self) -> String {
        // Replace ISO8601 timestamps (20241226T205701Z) with placeholder
        TIMESTAMP_REGEX.replace_all(self, "{TIMESTAMP}").to_string()
    }
}

/// Unit tests for snapshot utilities
///
/// # Purpose
///
/// Validates normalization behavior for platform-specific output differences.
/// These tests ensure golden output comparison works correctly across
/// Unix/Windows platforms.
///
/// # Coverage
///
/// - Line ending normalization (CRLF → LF)
/// - PID placeholder replacement
/// - Timestamp placeholder replacement
///
/// # Contract References
///
/// These normalization rules are specified in the M0 contract as allowed
/// differences for cross-platform testing.
#[cfg(test)]
mod tests {
    use super::*;

    /// Test line ending normalization from Windows format to Unix format
    ///
    /// # Purpose
    ///
    /// Verifies that CRLF line endings are converted to LF for consistent
    /// comparison across platforms.
    ///
    /// # Contract Reference
    ///
    /// Line ending normalization is explicitly allowed by the M0 contract
    /// specification for cross-platform conformance testing.
    ///
    /// # Asserts
    ///
    /// `line1\r\nline2\r\nline3` → `line1\nline2\nline3`
    #[test]
    fn test_normalize_line_endings() {
        let input = "line1\r\nline2\r\nline3";
        let expected = "line1\nline2\nline3";
        assert_eq!(normalize_output(input), expected);
    }

    /// Test PID value replacement with placeholder
    ///
    /// # Purpose
    ///
    /// Verifies that variable PID values in log filenames and content are
    /// replaced with a consistent placeholder for snapshot comparison.
    ///
    /// # Contract Reference
    ///
    /// PID normalization is required because process IDs vary between runs
    /// and cannot be used for golden output comparison.
    ///
    /// # Asserts
    ///
    /// `pid12345-FAIL.log` → `pid{PID}-FAIL.log`
    #[test]
    fn test_normalize_pid() {
        let input = "pid12345-FAIL.log";
        let output = input.replace_pid_with_placeholder();
        assert_eq!(output, "pid{PID}-FAIL.log");
    }

    /// Test timestamp replacement with placeholder
    ///
    /// # Purpose
    ///
    /// Verifies that variable timestamp values in log filenames and content
    /// are replaced with a consistent placeholder for snapshot comparison.
    ///
    /// # Contract Reference
    ///
    /// Timestamp normalization is required because timestamps vary between runs
    /// and cannot be used for golden output comparison.
    ///
    /// # Asserts
    ///
    /// `20241226T205701Z-pid123-FAIL.log` → `{TIMESTAMP}-pid123-FAIL.log`
    #[test]
    fn test_normalize_timestamp() {
        let input = "20241226T205701Z-pid123-FAIL.log";
        let output = input.replace_timestamp_with_placeholder();
        assert_eq!(output, "{TIMESTAMP}-pid123-FAIL.log");
    }
}
