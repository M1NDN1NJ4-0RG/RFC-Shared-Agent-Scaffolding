//! # Configuration Module
//!
//! Parse and manage .bootstrap.toml configuration files.
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Top-level configuration
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Config {
    /// Profiles (dev, ci, full)
    #[serde(default)]
    pub profiles: HashMap<String, Profile>,

    /// Tool-specific configuration
    #[serde(default)]
    pub tools: HashMap<String, ToolConfig>,
}

impl Config {
    /// Get required tools for current profile (defaults to "dev")
    pub fn get_required_tools(&self) -> Vec<&str> {
        // For now, return a default set of tools
        // TODO: Add profile selection based on CLI args
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

    /// Resolve tools for a specific profile
    pub fn resolve_tools(&self, profile: &str, overrides: &[String]) -> Vec<String> {
        let mut tools = if let Some(prof) = self.profiles.get(profile) {
            prof.tools.clone()
        } else {
            // Default tools if profile not found
            self.get_required_tools()
                .into_iter()
                .map(|s| s.to_string())
                .collect()
        };

        tools.extend_from_slice(overrides);
        tools
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
