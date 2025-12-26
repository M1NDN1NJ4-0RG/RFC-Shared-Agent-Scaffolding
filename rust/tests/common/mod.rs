use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

pub mod snapshots;

/// Conformance test vectors loaded from conformance/vectors.json
#[derive(Debug, Deserialize, Serialize)]
pub struct ConformanceVectors {
    pub version: String,
    pub m0_contract_version: String,
    pub description: String,
    #[serde(default)]
    pub vectors: VectorCategories,
}

#[derive(Debug, Deserialize, Serialize, Default)]
pub struct VectorCategories {
    #[serde(default)]
    pub safe_run: Vec<SafeRunVector>,
    #[serde(default)]
    pub safe_archive: Vec<SafeArchiveVector>,
    #[serde(default)]
    pub preflight_automerge_ruleset: Vec<PreflightVector>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SafeRunVector {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub m0_spec: Vec<String>,
    pub description: String,
    #[serde(default)]
    pub command: CommandSpec,
    pub expected: ExpectedOutcome,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SafeArchiveVector {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub m0_spec: Vec<String>,
    pub description: String,
    #[serde(default)]
    pub setup: SetupSpec,
    #[serde(default)]
    pub command: CommandSpec,
    #[serde(default)]
    pub command_variants: Vec<CommandVariant>,
    pub expected: ExpectedOutcome,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct PreflightVector {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub m0_spec: Vec<String>,
    pub description: String,
    #[serde(default)]
    pub mock_responses: MockResponses,
    pub command: CommandSpec,
    pub expected: ExpectedOutcome,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct SetupSpec {
    #[serde(default)]
    pub create_files: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct CommandSpec {
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub args_template: String,
    #[serde(default)]
    pub print_stdout: String,
    #[serde(default)]
    pub print_stderr: String,
    #[serde(default)]
    pub exit_code: Option<i32>,
    #[serde(default)]
    pub output_lines: Vec<String>,
    #[serde(default)]
    pub interrupt_signal: String,
    #[serde(default)]
    pub env: HashMap<String, String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CommandVariant {
    pub args: Vec<String>,
    pub expected_file: String,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct MockResponses {
    #[serde(default)]
    pub rulesets_list: serde_json::Value,
    #[serde(default)]
    pub ruleset_detail: serde_json::Value,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ExpectedOutcome {
    #[serde(default)]
    pub exit_code: Option<i32>,
    #[serde(default)]
    #[serde(rename = "exit_code_oneOf")]
    pub exit_code_one_of: Vec<i32>,
    #[serde(default)]
    pub exit_code_range: Vec<i32>,
    #[serde(default)]
    pub stdout_contains: Vec<String>,
    #[serde(default)]
    pub stderr_contains: Vec<String>,
    #[serde(default)]
    pub artifacts_created: Option<bool>,
    #[serde(default)]
    pub file_exists: Vec<String>,
    #[serde(default)]
    pub file_not_exists: Vec<String>,
    #[serde(default)]
    pub log_file_pattern: String,
    #[serde(default)]
    pub log_content_markers: Vec<String>,
    #[serde(default)]
    pub log_file_in_dir: String,
    #[serde(default)]
    pub archive_contains: Vec<String>,
    #[serde(default)]
    pub original_file_unchanged: String,
    #[serde(default)]
    pub file_count_unchanged: Option<bool>,
    #[serde(default)]
    pub auth_header_format: String,
}

/// Load conformance vectors from the repository root
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

#[cfg(test)]
mod tests {
    use super::*;

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

    #[test]
    fn test_safe_run_vector_structure() {
        let vectors = load_vectors().expect("Should load conformance vectors");
        let first = &vectors.vectors.safe_run[0];
        assert!(!first.id.is_empty());
        assert!(!first.name.is_empty());
        assert!(!first.description.is_empty());
    }
}
