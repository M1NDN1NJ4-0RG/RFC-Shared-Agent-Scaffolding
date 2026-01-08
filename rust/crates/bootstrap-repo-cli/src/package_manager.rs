//! # Package Manager Operations
//!
//! Abstract interface for package managers (Homebrew, apt-get, etc.)
//!
//! # Purpose
//!
//! Provides platform-agnostic interface for package management operations.
//! Implements concrete package managers (Homebrew for macOS/Linux, apt-get for Debian/Ubuntu).
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::package_manager::{HomebrewOps, PackageManagerOps};
//!
//! # async fn example() {
//! let pm = HomebrewOps;
//! // pm.install(ctx, "ripgrep", None).await
//! # }
//! ```

use crate::context::Context;
use crate::errors::{BootstrapError, BootstrapResult};
use async_trait::async_trait;
use tokio::process::Command;

/// Package manager operations trait
#[async_trait]
pub trait PackageManagerOps: Send + Sync {
    /// Refresh package metadata
    async fn refresh(&self, ctx: &Context) -> BootstrapResult<()>;

    /// Install a package
    async fn install(
        &self,
        ctx: &Context,
        package: &str,
        version: Option<&str>,
    ) -> BootstrapResult<()>;

    /// Check if package is installed
    async fn is_installed(&self, ctx: &Context, package: &str) -> BootstrapResult<bool>;
}

/// Homebrew package manager
pub struct HomebrewOps;

#[async_trait]
impl PackageManagerOps for HomebrewOps {
    async fn refresh(&self, _ctx: &Context) -> BootstrapResult<()> {
        // Homebrew doesn't require explicit refresh
        Ok(())
    }

    async fn install(
        &self,
        ctx: &Context,
        package: &str,
        _version: Option<&str>,
    ) -> BootstrapResult<()> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install via brew: {}", package);
            return Ok(());
        }

        let output = Command::new("brew")
            .arg("install")
            .arg(package)
            .output()
            .await
            .map_err(|e| BootstrapError::CommandFailed {
                command: format!("brew install {}", package),
                exit_code: None,
                stderr: e.to_string(),
            })?;

        if !output.status.success() {
            return Err(BootstrapError::InstallFailed {
                tool: package.to_string(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            });
        }

        Ok(())
    }

    async fn is_installed(&self, _ctx: &Context, package: &str) -> BootstrapResult<bool> {
        let output = Command::new("brew")
            .arg("list")
            .arg(package)
            .output()
            .await
            .map_err(|e| BootstrapError::CommandFailed {
                command: format!("brew list {}", package),
                exit_code: None,
                stderr: e.to_string(),
            })?;

        Ok(output.status.success())
    }
}

/// apt-get package manager
pub struct AptOps;

#[async_trait]
impl PackageManagerOps for AptOps {
    async fn refresh(&self, ctx: &Context) -> BootstrapResult<()> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would run: sudo apt-get update");
            return Ok(());
        }

        // NOTE: Using sudo -n (non-interactive) which will fail fast if password required
        // This is intentional: CI environments should have passwordless sudo configured
        // TODO: Consider checking for passwordless sudo availability before attempting
        // FUTURE: Provide fallback authentication methods or clearer error messages
        let output = Command::new("sudo")
            .args(["-n", "apt-get", "update", "-qq"])
            .output()
            .await
            .map_err(|e| BootstrapError::CommandFailed {
                command: "sudo apt-get update".to_string(),
                exit_code: None,
                stderr: e.to_string(),
            })?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);

            // Provide helpful error message if sudo password is required
            if stderr.contains("a password is required") || stderr.contains("no password") {
                return Err(BootstrapError::CommandFailed {
                    command: "sudo apt-get update".to_string(),
                    exit_code: output.status.code(),
                    stderr: format!(
                        "sudo requires password (passwordless sudo not configured). \
                        In CI environments, ensure the runner has passwordless sudo access. \
                        Original error: {}",
                        stderr
                    ),
                });
            }
            let stderr = String::from_utf8_lossy(&output.stderr);
            eprintln!(
                "Warning: `sudo apt-get update -qq` failed (treated as non-fatal, continuing). stderr:\n{}",
                stderr
            );
        }

        Ok(())
    }

    async fn install(
        &self,
        ctx: &Context,
        package: &str,
        _version: Option<&str>,
    ) -> BootstrapResult<()> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install via apt-get: {}", package);
            return Ok(());
        }

        // Use non-interactive mode and deterministic flags for CI
        // NOTE: sudo -n will fail fast if password required (intentional for CI)
        let mut cmd = Command::new("sudo");
        cmd.args(["-n", "apt-get", "install", "-y", "-qq", package]);
        cmd.env("DEBIAN_FRONTEND", "noninteractive");

        let output = cmd
            .output()
            .await
            .map_err(|e| BootstrapError::CommandFailed {
                command: format!("sudo apt-get install -y {}", package),
                exit_code: None,
                stderr: e.to_string(),
            })?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);

            // Provide helpful error if sudo password required
            if stderr.contains("a password is required") || stderr.contains("no password") {
                return Err(BootstrapError::CommandFailed {
                    command: format!("sudo apt-get install {}", package),
                    exit_code: output.status.code(),
                    stderr: format!(
                        "sudo requires password (passwordless sudo not configured). \
                        Ensure CI runner has passwordless sudo. Original error: {}",
                        stderr
                    ),
                });
            }

            return Err(BootstrapError::InstallFailed {
                tool: package.to_string(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr: stderr.to_string(),
            });
        }

        Ok(())
    }

    async fn is_installed(&self, _ctx: &Context, package: &str) -> BootstrapResult<bool> {
        let output = Command::new("dpkg")
            .args(["-s", package])
            .output()
            .await
            .map_err(|e| BootstrapError::CommandFailed {
                command: format!("dpkg -s {}", package),
                exit_code: None,
                stderr: e.to_string(),
            })?;

        Ok(output.status.success())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::context::{OsType, PackageManager};
    use std::path::PathBuf;

    #[tokio::test]
    async fn test_homebrew_dry_run() {
        let ctx = Context::new(
            PathBuf::from("/tmp"),
            OsType::Linux,
            PackageManager::Homebrew,
            true, // dry-run
        );

        let brew = HomebrewOps;
        // Should not error in dry-run
        let result = brew.install(&ctx, "test-package", None).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_apt_dry_run() {
        let ctx = Context::new(
            PathBuf::from("/tmp"),
            OsType::Linux,
            PackageManager::Apt,
            true, // dry-run
        );

        let apt = AptOps;
        let result = apt.install(&ctx, "test-package", None).await;
        assert!(result.is_ok());
    }
}
