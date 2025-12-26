//! Snapshot testing utilities for golden output comparison
//!
//! This module provides helpers for snapshot testing - comparing actual
//! outputs against golden/expected outputs stored in the snapshots/ directory.

#![allow(dead_code)] // Functions will be used in PR3

use once_cell::sync::Lazy;
use regex::Regex;
use std::fs;
use std::path::{Path, PathBuf};

// Compile regexes once at module initialization
static PID_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"pid\d+").unwrap());
static TIMESTAMP_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d{8}T\d{6}Z").unwrap());

/// Get the snapshots directory path
pub fn snapshots_dir() -> PathBuf {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    Path::new(manifest_dir).join("tests").join("snapshots")
}

/// Load a snapshot file
pub fn load_snapshot(name: &str) -> Result<String, std::io::Error> {
    let snapshot_path = snapshots_dir().join(format!("{}.txt", name));
    fs::read_to_string(snapshot_path)
}

/// Save a snapshot file (for generating golden outputs)
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
/// Returns true if they match, false otherwise
pub fn matches_snapshot(name: &str, actual: &str) -> bool {
    match load_snapshot(name) {
        Ok(expected) => normalize_output(&expected) == normalize_output(actual),
        Err(_) => false,
    }
}

/// Normalize output for comparison
///
/// This handles platform-specific differences that are allowed by the contract:
/// - Line endings (CRLF vs LF)
/// - Trailing whitespace
/// - Process IDs (PID values)
/// - Timestamps
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
trait NormalizePid {
    fn replace_pid_with_placeholder(&self) -> String;
}

impl NormalizePid for str {
    fn replace_pid_with_placeholder(&self) -> String {
        // Replace patterns like "pid12345" or "PID=12345" with placeholder
        // This is a simple implementation; may need refinement based on actual output format
        PID_REGEX.replace_all(self, "pid{PID}").to_string()
    }
}

/// Helper trait to normalize timestamps in output
trait NormalizeTimestamp {
    fn replace_timestamp_with_placeholder(&self) -> String;
}

impl NormalizeTimestamp for str {
    fn replace_timestamp_with_placeholder(&self) -> String {
        // Replace ISO8601 timestamps (20241226T205701Z) with placeholder
        TIMESTAMP_REGEX.replace_all(self, "{TIMESTAMP}").to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize_line_endings() {
        let input = "line1\r\nline2\r\nline3";
        let expected = "line1\nline2\nline3";
        assert_eq!(normalize_output(input), expected);
    }

    #[test]
    fn test_normalize_pid() {
        let input = "pid12345-FAIL.log";
        let output = input.replace_pid_with_placeholder();
        assert_eq!(output, "pid{PID}-FAIL.log");
    }

    #[test]
    fn test_normalize_timestamp() {
        let input = "20241226T205701Z-pid123-FAIL.log";
        let output = input.replace_timestamp_with_placeholder();
        assert_eq!(output, "{TIMESTAMP}-pid123-FAIL.log");
    }
}
