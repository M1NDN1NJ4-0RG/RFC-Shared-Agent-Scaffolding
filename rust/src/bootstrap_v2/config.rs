//! # Configuration Module
//!
//! Parse and manage .bootstrap.toml configuration files.

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
