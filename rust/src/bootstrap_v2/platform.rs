//! # Unix/Linux Platform Abstractions
//!
//! Unix/Linux-specific utilities for virtual environment management, shell integration,
//! and PATH manipulation.
//!
//! # Purpose
//!
//! Provides Unix/Linux platform abstractions for Phase 8 of Issue #235, including:
//! - Virtual environment creation and validation
//! - Shell environment setup (PATH, VIRTUAL_ENV)
//! - Platform-specific command execution helpers for Unix-like systems
//!
//! **Note:** This v1 implementation supports Unix/Linux platforms only. Windows is
//! explicitly not supported and will be added in a future version.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::platform::{create_venv, VenvInfo};
//! use std::path::PathBuf;
//!
//! # async fn example() -> anyhow::Result<()> {
//! let venv_path = PathBuf::from(".venv");
//! create_venv(&venv_path, false).await?;
//!
//! let info = VenvInfo::from_path(&venv_path)?;
//! println!("Python: {}", info.python_path.display());
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::errors::BootstrapError;
use anyhow::{Context as AnyhowContext, Result};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tokio::process::Command;

/// Information about a virtual environment
#[derive(Debug, Clone)]
pub struct VenvInfo {
    /// Path to the venv root
    pub venv_path: PathBuf,

    /// Path to the Python executable
    pub python_path: PathBuf,

    /// Path to the pip executable
    pub pip_path: PathBuf,

    /// Path to the bin directory
    pub bin_path: PathBuf,

    /// Python version (if detectable)
    pub python_version: Option<String>,
}

impl VenvInfo {
    /// Create VenvInfo from a venv path
    pub fn from_path(venv_path: &Path) -> Result<Self> {
        let bin_path = venv_path.join("bin");
        let python_path = bin_path.join("python3");
        let pip_path = bin_path.join("pip");

        // Verify that the venv exists and has a python executable
        if !python_path.exists() {
            return Err(BootstrapError::VenvActivation(format!(
                "Virtual environment not found at: {}",
                venv_path.display()
            ))
            .into());
        }

        Ok(Self {
            venv_path: venv_path.to_path_buf(),
            python_path,
            pip_path,
            bin_path,
            python_version: None,
        })
    }

    /// Get Python version by executing python --version
    pub async fn detect_python_version(&mut self) -> Result<String> {
        if let Some(ref version) = self.python_version {
            return Ok(version.clone());
        }

        let output = Command::new(&self.python_path)
            .arg("--version")
            .output()
            .await
            .context("Failed to execute python --version")?;

        if !output.status.success() {
            return Err(BootstrapError::VenvActivation(format!(
                "Python version check failed with exit code: {}",
                output.status.code().unwrap_or(-1)
            ))
            .into());
        }

        // Parse "Python 3.12.3" -> "3.12.3"
        let version_str = String::from_utf8_lossy(&output.stdout);
        let version = version_str
            .strip_prefix("Python ")
            .and_then(|s| s.split_whitespace().next())
            .ok_or_else(|| {
                BootstrapError::VenvActivation(format!(
                    "Failed to parse Python version from: {}",
                    version_str
                ))
            })?
            .to_string();

        self.python_version = Some(version.clone());
        Ok(version)
    }

    /// Get environment variables for this venv
    pub fn env_vars(&self) -> HashMap<String, String> {
        let mut env = HashMap::new();

        // Set VIRTUAL_ENV
        env.insert(
            "VIRTUAL_ENV".to_string(),
            self.venv_path.display().to_string(),
        );

        // Note: PATH manipulation is done via prepend_to_path()
        // to compose with existing PATH

        env
    }

    /// Prepend venv bin directory to PATH
    pub fn prepend_to_path(&self, current_path: Option<&str>) -> String {
        let bin_dir = self.bin_path.display().to_string();

        // Use platform-specific PATH separator: ':' on Unix, ';' on Windows
        let sep = if cfg!(windows) { ';' } else { ':' };

        if let Some(path) = current_path {
            format!("{}{}{}", bin_dir, sep, path)
        } else {
            bin_dir
        }
    }
}

/// Create a Python virtual environment
///
/// # Platform Support
///
/// This function is designed for Unix/Linux platforms and uses Unix-specific paths:
/// - Uses `bin/` subdirectory for executables (not `Scripts/` as on Windows)
/// - Uses `python3` and `pip` executable names (not `.exe` extensions)
///
/// Windows support is explicitly excluded in v1 of this implementation.
///
/// # Arguments
///
/// * `venv_path` - Path where venv should be created
/// * `dry_run` - If true, only simulate the operation
///
/// # Errors
///
/// Returns error if:
/// - Python3 is not available
/// - Venv creation fails
/// - Created venv is invalid
pub async fn create_venv(venv_path: &Path, dry_run: bool) -> Result<VenvInfo> {
    if dry_run {
        println!("[DRY-RUN] Would create venv at: {}", venv_path.display());
        // In dry-run, create a mock VenvInfo
        return Ok(VenvInfo {
            venv_path: venv_path.to_path_buf(),
            python_path: venv_path.join("bin").join("python3"),
            pip_path: venv_path.join("bin").join("pip"),
            bin_path: venv_path.join("bin"),
            python_version: Some("3.12.0".to_string()),
        });
    }

    // Check if venv already exists
    if venv_path.exists() {
        // Verify it's valid
        return VenvInfo::from_path(venv_path);
    }

    // Create venv using python3 -m venv
    let output = Command::new("python3")
        .arg("-m")
        .arg("venv")
        .arg(venv_path)
        .output()
        .await
        .context("Failed to execute python3 -m venv")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(BootstrapError::VenvActivation(format!(
            "Failed to create virtual environment: {}",
            stderr
        ))
        .into());
    }

    // Verify the created venv
    VenvInfo::from_path(venv_path)
}

/// Upgrade pip in a virtual environment
///
/// # Arguments
///
/// * `venv_info` - Virtual environment information
/// * `dry_run` - If true, only simulate the operation
///
/// # Errors
///
/// Returns error if pip upgrade fails
pub async fn upgrade_pip(venv_info: &VenvInfo, dry_run: bool) -> Result<()> {
    if dry_run {
        println!(
            "[DRY-RUN] Would upgrade pip in: {}",
            venv_info.venv_path.display()
        );
        return Ok(());
    }

    let output = Command::new(&venv_info.python_path)
        .arg("-m")
        .arg("pip")
        .arg("install")
        .arg("--upgrade")
        .arg("pip")
        .output()
        .await
        .context("Failed to execute pip upgrade")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(BootstrapError::PythonToolsFailed(format!(
            "Failed to upgrade pip: {}",
            stderr
        ))
        .into());
    }

    Ok(())
}

/// Check if a command exists in PATH
///
/// # Implementation Note
///
/// This function checks command existence by attempting to execute it with `--version`.
/// This approach works for most standard CLI tools but may produce false negatives for:
/// - Commands that don't support `--version` (use `-v`, `-V`, `--help`, or no args)
/// - Commands that are valid but fail with non-zero exit for `--version`
///
/// The function checks both that the command can be spawned AND that it exits successfully.
///
/// For more robust existence checking, callers requiring higher accuracy should use
/// platform-specific methods like `which` or PATH scanning.
pub fn command_exists(cmd: &str) -> bool {
    std::process::Command::new(cmd)
        .arg("--version")
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

/// Get the current PATH environment variable
pub fn get_current_path() -> Option<String> {
    std::env::var("PATH").ok()
}

/// Parse version from command output
///
/// Common patterns:
/// - "tool 1.2.3" -> "1.2.3"
/// - "v1.2.3" -> "1.2.3"
/// - "tool version 1.2.3" -> "1.2.3"
pub fn parse_version_from_output(output: &str) -> Option<String> {
    use once_cell::sync::Lazy;

    // Compile regex once and cache it for reuse across calls
    static VERSION_RE: Lazy<regex::Regex> = Lazy::new(|| {
        regex::Regex::new(r"(\d+\.\d+\.\d+)").expect("VERSION_RE regex pattern is valid")
    });

    VERSION_RE
        .captures(output)
        .and_then(|caps| caps.get(1))
        .map(|m| m.as_str().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_venv_info_from_nonexistent_path() {
        let result = VenvInfo::from_path(Path::new("/nonexistent/path"));
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_create_venv_dry_run() {
        let venv_path = PathBuf::from("/tmp/test-venv-dry-run");
        let result = create_venv(&venv_path, true).await;
        assert!(result.is_ok());

        let info = result.unwrap();
        assert_eq!(info.venv_path, venv_path);
        assert_eq!(info.python_version, Some("3.12.0".to_string()));
    }

    #[test]
    fn test_venv_info_prepend_to_path() {
        let info = VenvInfo {
            venv_path: PathBuf::from("/test/venv"),
            python_path: PathBuf::from("/test/venv/bin/python3"),
            pip_path: PathBuf::from("/test/venv/bin/pip"),
            bin_path: PathBuf::from("/test/venv/bin"),
            python_version: None,
        };

        let path = info.prepend_to_path(Some("/usr/bin:/bin"));
        assert_eq!(path, "/test/venv/bin:/usr/bin:/bin");

        let path_no_existing = info.prepend_to_path(None);
        assert_eq!(path_no_existing, "/test/venv/bin");
    }

    #[test]
    fn test_venv_info_env_vars() {
        let info = VenvInfo {
            venv_path: PathBuf::from("/test/venv"),
            python_path: PathBuf::from("/test/venv/bin/python3"),
            pip_path: PathBuf::from("/test/venv/bin/pip"),
            bin_path: PathBuf::from("/test/venv/bin"),
            python_version: None,
        };

        let env = info.env_vars();
        assert_eq!(env.get("VIRTUAL_ENV"), Some(&"/test/venv".to_string()));
    }

    #[test]
    fn test_parse_version_from_output() {
        assert_eq!(
            parse_version_from_output("black, 25.12.0"),
            Some("25.12.0".to_string())
        );
        assert_eq!(
            parse_version_from_output("ruff 0.14.10"),
            Some("0.14.10".to_string())
        );
        assert_eq!(
            parse_version_from_output("v1.2.3"),
            Some("1.2.3".to_string())
        );
        assert_eq!(
            parse_version_from_output("tool version 2.0.1 (build)"),
            Some("2.0.1".to_string())
        );
        assert_eq!(parse_version_from_output("no version here"), None);
    }

    #[test]
    fn test_command_exists() {
        // Test with a command that should exist
        assert!(command_exists("ls") || command_exists("dir"));

        // Test with a command that should not exist
        assert!(!command_exists("nonexistent-command-12345"));
    }
}
