//! # Ripgrep Installer
//!
//! Ripgrep is a REQUIRED tool and must not fail.
//!
//! # Purpose
//!
//! Installs ripgrep via system package managers (Homebrew or apt-get).
//! Ripgrep is mandatory for the repository and failures result in exit code 21.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::ripgrep::RipgrepInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! # async fn example() {
//! let installer = RipgrepInstaller;
//! // Use installer.detect(), install(), verify()
//! # }
//! ```

use crate::bootstrap_v2::context::{Context, PackageManager};
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use crate::bootstrap_v2::package_manager::{AptOps, HomebrewOps, PackageManagerOps};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// Ripgrep installer
pub struct RipgrepInstaller;

#[async_trait]
impl Installer for RipgrepInstaller {
    fn id(&self) -> &'static str {
        "ripgrep"
    }

    fn name(&self) -> &'static str {
        "ripgrep"
    }

    fn description(&self) -> &'static str {
        "Fast grep alternative (REQUIRED)"
    }

    fn concurrency_safe(&self) -> bool {
        false // Package manager operations need locks
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        let output = Command::new("rg").arg("--version").output().await;

        match output {
            Ok(out) if out.status.success() => {
                let version_str = String::from_utf8_lossy(&out.stdout);
                // Parse version from "ripgrep X.Y.Z"
                if let Some(line) = version_str.lines().next() {
                    if let Some(ver) = line.split_whitespace().nth(1) {
                        if let Ok(version) = Version::parse(ver) {
                            return Ok(Some(version));
                        }
                    }
                }
                Ok(Some(Version::new(0, 0, 0))) // Unknown version but present
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install ripgrep");
            return Ok(InstallResult {
                version: Version::new(0, 0, 0),
                installed_new: true,
                log_messages: vec!["Dry-run: ripgrep would be installed".to_string()],
            });
        }

        // Check if ripgrep is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "ripgrep already installed (version {})",
                    existing_version
                )],
            });
        }

        let pm: Box<dyn PackageManagerOps> = match ctx.package_manager {
            PackageManager::Homebrew => Box::new(HomebrewOps),
            PackageManager::Apt => Box::new(AptOps),
            _ => {
                return Err(BootstrapError::InstallFailed {
                    tool: "ripgrep".to_string(),
                    exit_code: 1,
                    stderr: "No supported package manager available".to_string(),
                })
            }
        };

        pm.install(ctx, "ripgrep", None).await?;

        // Verify it's now available
        let version = self
            .detect(ctx)
            .await?
            .ok_or_else(|| BootstrapError::InstallFailed {
                tool: "ripgrep".to_string(),
                exit_code: 1,
                stderr: "Installation completed but ripgrep not found".to_string(),
            })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["ripgrep installed successfully".to_string()],
        })
    }

    async fn verify(&self, ctx: &Context) -> BootstrapResult<VerifyResult> {
        match self.detect(ctx).await? {
            Some(version) => Ok(VerifyResult {
                success: true,
                version: Some(version),
                issues: vec![],
            }),
            None => Ok(VerifyResult {
                success: false,
                version: None,
                issues: vec!["ripgrep not found (REQUIRED)".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bootstrap_v2::context::OsType;
    use std::path::PathBuf;

    #[tokio::test]
    async fn test_ripgrep_detect() {
        let ctx = Context::new(
            PathBuf::from("/tmp"),
            OsType::Linux,
            PackageManager::Apt,
            false,
        );

        let installer = RipgrepInstaller;
        let result = installer.detect(&ctx).await;
        // May or may not be installed, just shouldn't error
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_ripgrep_dry_run() {
        let ctx = Context::new(
            PathBuf::from("/tmp"),
            OsType::Linux,
            PackageManager::Homebrew,
            true, // dry-run
        );

        let installer = RipgrepInstaller;
        let result = installer.install(&ctx).await;
        assert!(result.is_ok());
    }
}
