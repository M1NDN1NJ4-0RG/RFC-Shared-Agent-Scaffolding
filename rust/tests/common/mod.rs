//! # Common Test Utilities and Conformance Vector Loading
//!
//! This module provides shared infrastructure for conformance testing of the
//! Rust canonical tool against the RFC contract specification.
//!
//! # Purpose
//!
//! - Loads and parses conformance vectors from `conformance/vectors.json`
//! - Defines type-safe structures for test case specifications
//! - Provides helper functions for locating the safe-run binary
//! - Enables consistent test execution across all conformance test suites
//!
//! # Architecture
//!
//! ## Vector Categories
//!
//! Conformance vectors are organized by command type:
//! - **safe_run**: Command execution with logging (vectors safe-run-001 through safe-run-010)
//! - **safe_archive**: Command execution with archiving
//! - **preflight_automerge_ruleset**: GitHub preflight checks
//!
//! ## Data Structures
//!
//! - `ConformanceVectors`: Top-level container with version and vector categories
//! - `SafeRunVector`, `SafeArchiveVector`, `PreflightVector`: Type-specific test cases
//! - `CommandSpec`: Command invocation details
//! - `ExpectedOutcome`: Assertions for test validation
//!
//! # Contract Compliance
//!
//! This module enforces the contract specification by:
//! - Loading vectors from the canonical `conformance/vectors.json` file
//! - Validating vector structure via strongly-typed deserialization
//! - Providing M0 spec references for each test case
//!
//! # Usage Pattern
//!
//! ```no_run
//! use common::{load_vectors, get_safe_run_binary};
//!
//! let vectors = load_vectors().expect("Failed to load vectors");
//! let binary = get_safe_run_binary();
//!
//! for vector in &vectors.vectors.safe_run {
//!     // Execute test case using vector.command and validate vector.expected
//! }
//! ```
//!
//! # Contract References
//!
//! - Conformance vectors specification: `conformance/vectors.json`
//! - M0 contract: `RFC-Shared-Agent-Scaffolding-v0.1.0.md`
//! - Vector format documentation: `conformance/README.md`

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

pub mod snapshots;

/// Conformance test vectors loaded from conformance/vectors.json
///
/// # Purpose
///
/// Top-level container for all conformance test vectors. Provides version
/// tracking and categorized test cases.
///
/// # Fields
///
/// - `version`: Conformance vector format version (currently "1.0")
/// - `m0_contract_version`: M0 contract specification version
/// - `description`: Human-readable description of the vector set
/// - `vectors`: Categorized test cases by command type
///
/// # File Format
///
/// Loaded from JSON file with structure:
/// ```json
/// {
///   "version": "1.0",
///   "m0_contract_version": "M0-v0.1.0",
///   "description": "...",
///   "vectors": { "safe_run": [...], "safe_archive": [...], ... }
/// }
/// ```
///
/// # Examples
///
/// ```no_run
/// let vectors = load_vectors().unwrap();
/// assert_eq!(vectors.version, "1.0");
/// assert!(!vectors.vectors.safe_run.is_empty());
/// ```
#[derive(Debug, Deserialize, Serialize)]
pub struct ConformanceVectors {
    pub version: String,
    pub m0_contract_version: String,
    pub description: String,
    #[serde(default)]
    pub vectors: VectorCategories,
}

/// Vector categories organizing test cases by command type
///
/// Each category contains vectors for a specific command in the contract.
/// All fields default to empty vectors if not present in JSON.
#[derive(Debug, Deserialize, Serialize, Default)]
pub struct VectorCategories {
    /// Safe-run command test vectors (safe-run-001 through safe-run-010)
    #[serde(default)]
    pub safe_run: Vec<SafeRunVector>,
    /// Safe-archive command test vectors
    #[serde(default)]
    pub safe_archive: Vec<SafeArchiveVector>,
    /// Preflight automerge ruleset test vectors
    #[serde(default)]
    pub preflight_automerge_ruleset: Vec<PreflightVector>,
}

/// Test vector for safe-run command execution
///
/// Specifies command to run, expected behavior, and M0 contract references.
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SafeRunVector {
    /// Unique vector ID (e.g., "safe-run-001")
    pub id: String,
    /// Human-readable test name
    pub name: String,
    /// M0 specification requirement IDs covered by this vector
    #[serde(default)]
    pub m0_spec: Vec<String>,
    /// Detailed description of what this vector tests
    pub description: String,
    /// Command specification (what to execute)
    #[serde(default)]
    pub command: CommandSpec,
    /// Expected outcome (assertions)
    pub expected: ExpectedOutcome,
}

/// Test vector for safe-archive command execution
///
/// Similar to SafeRunVector but includes setup steps and command variants.
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SafeArchiveVector {
    /// Unique vector ID (e.g., "safe-archive-001")
    pub id: String,
    /// Human-readable test name
    pub name: String,
    /// M0 specification requirement IDs
    #[serde(default)]
    pub m0_spec: Vec<String>,
    /// Detailed description
    pub description: String,
    /// Pre-test setup actions
    #[serde(default)]
    pub setup: SetupSpec,
    /// Command specification
    #[serde(default)]
    pub command: CommandSpec,
    /// Alternative command variants to test
    #[serde(default)]
    pub command_variants: Vec<CommandVariant>,
    /// Expected outcome
    pub expected: ExpectedOutcome,
}

/// Test vector for preflight automerge ruleset checks
///
/// Includes mock API responses for GitHub API interactions.
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct PreflightVector {
    /// Unique vector ID
    pub id: String,
    /// Human-readable test name
    pub name: String,
    /// M0 specification requirement IDs
    #[serde(default)]
    pub m0_spec: Vec<String>,
    /// Detailed description
    pub description: String,
    /// Mock GitHub API responses
    #[serde(default)]
    pub mock_responses: MockResponses,
    /// Command specification
    pub command: CommandSpec,
    /// Expected outcome
    pub expected: ExpectedOutcome,
}

/// Setup actions to perform before test execution
#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct SetupSpec {
    /// File paths to create before running test
    #[serde(default)]
    pub create_files: Vec<String>,
}

/// Command specification: what to execute and how
#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct CommandSpec {
    /// Command arguments (e.g., ["echo", "hello"])
    #[serde(default)]
    pub args: Vec<String>,
    /// Template for generating args
    #[serde(default)]
    pub args_template: String,
    /// Text to print to stdout (for test helper scripts)
    #[serde(default)]
    pub print_stdout: String,
    /// Text to print to stderr (for test helper scripts)
    #[serde(default)]
    pub print_stderr: String,
    /// Expected exit code from command
    #[serde(default)]
    pub exit_code: Option<i32>,
    /// Lines of output (for verification)
    #[serde(default)]
    pub output_lines: Vec<String>,
    /// Signal to send for interrupt testing (e.g., "SIGTERM")
    #[serde(default)]
    pub interrupt_signal: String,
    /// Environment variables to set
    #[serde(default)]
    pub env: HashMap<String, String>,
}

/// Alternative command variant for testing multiple invocation patterns
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CommandVariant {
    /// Command arguments for this variant
    pub args: Vec<String>,
    /// Expected output file path
    pub expected_file: String,
}

/// Mock API responses for preflight testing
#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct MockResponses {
    /// Mock response for rulesets list API call
    #[serde(default)]
    pub rulesets_list: serde_json::Value,
    /// Mock response for ruleset detail API call
    #[serde(default)]
    pub ruleset_detail: serde_json::Value,
}

/// Expected outcome assertions for test validation
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ExpectedOutcome {
    /// Exact exit code expected (if specified)
    #[serde(default)]
    pub exit_code: Option<i32>,
    /// One of these exit codes is acceptable
    #[serde(default)]
    #[serde(rename = "exit_code_oneOf")]
    pub exit_code_one_of: Vec<i32>,
    /// Exit code must be in this range [min, max]
    #[serde(default)]
    pub exit_code_range: Vec<i32>,
    /// Stdout must contain these strings
    #[serde(default)]
    pub stdout_contains: Vec<String>,
    /// Stderr must contain these strings
    #[serde(default)]
    pub stderr_contains: Vec<String>,
    /// Whether artifacts should be created
    #[serde(default)]
    pub artifacts_created: Option<bool>,
    /// These files must exist after execution
    #[serde(default)]
    pub file_exists: Vec<String>,
    /// These files must not exist after execution
    #[serde(default)]
    pub file_not_exists: Vec<String>,
    /// Pattern for log file name
    #[serde(default)]
    pub log_file_pattern: String,
    /// Markers that must appear in log content
    #[serde(default)]
    pub log_content_markers: Vec<String>,
    /// Directory where log file should be created
    #[serde(default)]
    pub log_file_in_dir: String,
    /// Archive must contain these entries
    #[serde(default)]
    pub archive_contains: Vec<String>,
    /// This file path must remain unchanged
    #[serde(default)]
    pub original_file_unchanged: String,
    /// Number of files must not change
    #[serde(default)]
    pub file_count_unchanged: Option<bool>,
    /// Expected format for auth header
    #[serde(default)]
    pub auth_header_format: String,
}

/// Load conformance vectors from the repository root
///
/// # Purpose
///
/// Reads and parses the canonical conformance vectors file from
/// `conformance/vectors.json`. This file defines all test cases for
/// the M0 contract.
///
/// # Returns
///
/// - `Ok(ConformanceVectors)`: Parsed vectors
/// - `Err(Box<dyn std::error::Error>)`: File not found or parse error
///
/// # File Location
///
/// Navigates from `rust/tests/` up to repository root, then loads
/// `conformance/vectors.json`.
///
/// # Error Handling
///
/// Returns descriptive error messages for common failures:
/// - File not found (check working directory)
/// - JSON parse error (check file format)
/// - Missing parent directory (unexpected repo structure)
///
/// # Examples
///
/// ```no_run
/// let vectors = load_vectors().expect("Failed to load vectors");
/// println!("Loaded {} safe-run vectors", vectors.vectors.safe_run.len());
/// ```
pub fn load_vectors() -> Result<ConformanceVectors, Box<dyn std::error::Error>> {
    // Navigate from rust/tests/ up to repo root
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    let vectors_path = Path::new(manifest_dir)
        .parent()
        .ok_or("Cannot find parent directory")?
        .join("conformance")
        .join("vectors.json");

    let content = fs::read_to_string(&vectors_path)
        .map_err(|e| format!("Failed to read vectors.json: {}", e))?;

    let vectors: ConformanceVectors = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse vectors.json: {}", e))?;

    Ok(vectors)
}

/// Get the path to the safe-run binary (debug or release build)
///
/// # Purpose
///
/// Locates the compiled safe-run binary for use in integration tests.
/// Prefers release build over debug build for more realistic testing.
///
/// # Returns
///
/// PathBuf to the binary (may not exist if not yet built)
///
/// # Search Order
///
/// 1. `rust/target/release/safe-run[.exe]` (release build)
/// 2. `rust/target/debug/safe-run[.exe]` (debug build)
/// 3. Returns debug path as fallback (test will fail with clear message)
///
/// # Platform Notes
///
/// - **Windows**: Uses `safe-run.exe` extension
/// - **Unix**: Uses `safe-run` (no extension)
///
/// # Examples
///
/// ```no_run
/// let binary = get_safe_run_binary();
/// assert!(binary.exists(), "Binary not built yet");
/// ```
pub fn get_safe_run_binary() -> PathBuf {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");

    // Platform-specific binary name
    #[cfg(windows)]
    let bin_name = "safe-run.exe";
    #[cfg(not(windows))]
    let bin_name = "safe-run";

    let debug_bin = Path::new(manifest_dir).join("target/debug").join(bin_name);
    let release_bin = Path::new(manifest_dir)
        .join("target/release")
        .join(bin_name);

    // Prefer release build if it exists
    if release_bin.exists() {
        release_bin
    } else if debug_bin.exists() {
        debug_bin
    } else {
        // Return debug path as default, test will fail with clear message
        debug_bin
    }
}

/// Unit tests for conformance vector loading
///
/// # Purpose
///
/// Validates that conformance vectors can be loaded and have expected structure.
///
/// # Coverage
///
/// - Vector file loading
/// - Version validation
/// - Category presence
/// - Vector structure validation
#[cfg(test)]
mod tests {
    use super::*;

    /// Test that conformance vectors load successfully
    ///
    /// # Purpose
    ///
    /// Validates that `vectors.json` exists, is valid JSON, and contains
    /// all expected vector categories.
    ///
    /// # Asserts
    ///
    /// - Version is "1.0"
    /// - safe_run vectors exist
    /// - safe_archive vectors exist
    /// - preflight vectors exist
    #[test]
    fn test_load_vectors() {
        let vectors = load_vectors().expect("Should load conformance vectors");
        assert_eq!(vectors.version, "1.0");
        assert!(
            !vectors.vectors.safe_run.is_empty(),
            "Should have safe_run vectors"
        );
        assert!(
            !vectors.vectors.safe_archive.is_empty(),
            "Should have safe_archive vectors"
        );
        assert!(
            !vectors.vectors.preflight_automerge_ruleset.is_empty(),
            "Should have preflight vectors"
        );
    }

    /// Test safe-run vector structure is well-formed
    ///
    /// # Purpose
    ///
    /// Validates that vectors have required fields populated.
    ///
    /// # Asserts
    ///
    /// - Vector has non-empty ID
    /// - Vector has non-empty name
    /// - Vector has non-empty description
    #[test]
    fn test_safe_run_vector_structure() {
        let vectors = load_vectors().expect("Should load conformance vectors");
        let first = &vectors.vectors.safe_run[0];
        assert!(!first.id.is_empty());
        assert!(!first.name.is_empty());
        assert!(!first.description.is_empty());
    }
}
