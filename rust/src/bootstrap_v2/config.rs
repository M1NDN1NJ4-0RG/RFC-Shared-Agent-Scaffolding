//! # Configuration Module
//!
//! Parse and manage .bootstrap.toml configuration files.
//!
//! # Purpose
//!
//! Parses .bootstrap.toml files with profile and tool-specific configuration.
//! Enforces policy that config is required in CI mode for this repo.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::config::Config;
//! use std::path::Path;
//!
//! # fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let config = Config::load(Path::new("/repo"), false)?;
//! let tools = config.resolve_tools("dev", &[]);
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

/// Top-level configuration wrapper for TOML parsing
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct ConfigFile {
    /// Profiles section
    #[serde(default)]
    pub profile: HashMap<String, Profile>,

    /// Tool-specific configuration
    #[serde(default)]
    pub tool: HashMap<String, ToolConfig>,
}

/// Top-level configuration
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Config {
    /// Profiles (dev, ci, full)
    #[serde(skip)]
    pub profiles: HashMap<String, Profile>,

    /// Tool-specific configuration
    #[serde(skip)]
    pub tools: HashMap<String, ToolConfig>,
}

impl Config {
    /// Load configuration from file or use defaults
    ///
    /// # Arguments
    ///
    /// * `repo_root` - Repository root directory
    /// * `ci_mode` - Whether running in CI mode
    ///
    /// # Returns
    ///
    /// Configuration loaded from .bootstrap.toml or defaults
    ///
    /// # Errors
    ///
    /// Returns error if:
    /// - .bootstrap.toml is required (CI mode for this repo) but missing
    /// - TOML parsing fails
    /// - Invalid configuration structure
    ///
    /// # Policy
    ///
    /// - Binary supports defaults when .bootstrap.toml is absent
    /// - For this repo in CI: .bootstrap.toml is REQUIRED (exit UsageError if missing)
    pub fn load(repo_root: &Path, ci_mode: bool) -> BootstrapResult<Self> {
        let config_path = repo_root.join(".bootstrap.toml");

        if config_path.exists() {
            // Parse TOML file
            let contents = fs::read_to_string(&config_path).map_err(|e| {
                BootstrapError::ConfigError(format!("Failed to read .bootstrap.toml: {}", e))
            })?;

            let config_file: ConfigFile = toml::from_str(&contents).map_err(|e| {
                BootstrapError::ConfigError(format!("Failed to parse .bootstrap.toml: {}", e))
            })?;

            // Convert ConfigFile to Config
            Ok(Config {
                profiles: config_file.profile,
                tools: config_file.tool,
            })
        } else if ci_mode {
            // POLICY: For this repo in CI, .bootstrap.toml is REQUIRED
            // See docs/contributing/bootstrap-config-requirements.md for details
            Err(BootstrapError::ConfigError(
                ".bootstrap.toml is required in CI mode but was not found. \
                 Create a .bootstrap.toml file with at least a [profile.ci] section."
                    .to_string(),
            ))
        } else {
            // Use defaults when not in CI
            Ok(Self::default())
        }
    }

    /// Get required tools for current profile (defaults to "dev")
    pub fn get_required_tools(&self) -> Vec<&str> {
        // Default profile is "dev"
        self.get_tools_for_profile("dev")
    }

    /// Get tools for a specific profile
    pub fn get_tools_for_profile(&self, profile: &str) -> Vec<&str> {
        if let Some(prof) = self.profiles.get(profile) {
            prof.tools.iter().map(|s| s.as_str()).collect()
        } else {
            // Fallback to default tools if profile not found
            vec![
                "ripgrep",
                "python-black",
                "python-ruff",
                "python-pylint",
                "yamllint",
                "pytest",
                "actionlint",
                "shellcheck",
                "shfmt",
            ]
        }
    }

    /// Resolve tools for a specific profile with overrides
    ///
    /// # Arguments
    ///
    /// * `profile` - Profile name (e.g., "dev", "ci", "full")
    /// * `overrides` - Additional tools to add
    ///
    /// # Returns
    ///
    /// Vector of tool IDs to install
    pub fn resolve_tools(&self, profile: &str, overrides: &[String]) -> Vec<String> {
        let mut tools = if let Some(prof) = self.profiles.get(profile) {
            prof.tools.clone()
        } else {
            // Default tools if profile not found
            self.get_tools_for_profile(profile)
                .into_iter()
                .map(|s| s.to_string())
                .collect()
        };

        tools.extend_from_slice(overrides);
        tools
    }

    /// Get tool-specific configuration
    ///
    /// # Arguments
    ///
    /// * `tool_id` - Tool identifier
    ///
    /// # Returns
    ///
    /// Tool configuration if specified, None otherwise
    pub fn get_tool_config(&self, tool_id: &str) -> Option<&ToolConfig> {
        self.tools.get(tool_id)
    }
}

/// Profile configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Profile {
    /// Tools to install in this profile
    pub tools: Vec<String>,
}

/// Tool-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolConfig {
    /// Required version (exact)
    pub version: Option<String>,

    /// Minimum version
    pub min_version: Option<String>,

    /// Custom install arguments
    #[serde(default)]
    pub install_args: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::TempDir;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert!(config.profiles.is_empty());
        assert!(config.tools.is_empty());
    }

    #[test]
    fn test_load_missing_file_non_ci() {
        let temp_dir = TempDir::new().unwrap();
        let config = Config::load(temp_dir.path(), false).unwrap();
        assert!(config.profiles.is_empty());
    }

    #[test]
    fn test_load_missing_file_ci_fails() {
        let temp_dir = TempDir::new().unwrap();
        let result = Config::load(temp_dir.path(), true);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(err.to_string().contains("required in CI mode"));
    }

    #[test]
    fn test_load_valid_toml() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join(".bootstrap.toml");

        let toml_content = r#"
[profile.dev]
tools = ["ripgrep", "python-black"]

[profile.ci]
tools = ["ripgrep"]

[tool.ripgrep]
min_version = "14.0.0"
"#;

        let mut file = fs::File::create(&config_path).unwrap();
        file.write_all(toml_content.as_bytes()).unwrap();

        let config = Config::load(temp_dir.path(), false).unwrap();
        assert_eq!(config.profiles.len(), 2);
        assert!(config.profiles.contains_key("dev"));
        assert!(config.profiles.contains_key("ci"));

        let dev_tools = &config.profiles["dev"].tools;
        assert_eq!(dev_tools.len(), 2);
        assert_eq!(dev_tools[0], "ripgrep");
        assert_eq!(dev_tools[1], "python-black");

        let ripgrep_config = config.get_tool_config("ripgrep").unwrap();
        assert_eq!(ripgrep_config.min_version.as_deref(), Some("14.0.0"));
    }

    #[test]
    fn test_resolve_tools_with_overrides() {
        let mut config = Config::default();
        let profile = Profile {
            tools: vec!["ripgrep".to_string(), "python-black".to_string()],
        };
        config.profiles.insert("dev".to_string(), profile);

        let tools = config.resolve_tools("dev", &["shellcheck".to_string()]);
        assert_eq!(tools.len(), 3);
        assert!(tools.contains(&"ripgrep".to_string()));
        assert!(tools.contains(&"python-black".to_string()));
        assert!(tools.contains(&"shellcheck".to_string()));
    }

    #[test]
    fn test_get_tools_for_profile_fallback() {
        let config = Config::default();
        let tools = config.get_tools_for_profile("nonexistent");
        // Should return default tools
        assert!(!tools.is_empty());
        assert!(tools.contains(&"ripgrep"));
        assert!(tools.contains(&"python-black"));
    }

    #[test]
    fn test_invalid_toml() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join(".bootstrap.toml");

        let invalid_toml = "this is not valid toml [[[";
        let mut file = fs::File::create(&config_path).unwrap();
        file.write_all(invalid_toml.as_bytes()).unwrap();

        let result = Config::load(temp_dir.path(), false);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(err.to_string().contains("Failed to parse"));
    }
}
