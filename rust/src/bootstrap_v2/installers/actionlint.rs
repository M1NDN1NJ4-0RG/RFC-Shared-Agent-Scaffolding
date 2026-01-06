//! # actionlint Installer
//!
//! Installer for actionlint (GitHub Actions workflow linter).
//!
//! # Purpose
//!
//! Provides installation logic for actionlint via system package managers.
//! Actionlint is a REQUIRED tool per the bootstrap contract and validates
//! GitHub Actions workflow files.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::actionlint::ActionlintInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! let installer = ActionlintInstaller;
//! assert_eq!(installer.id(), "actionlint");
//! ```

use crate::bootstrap_v2::context::{Context, PackageManager};
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// actionlint installer
pub struct ActionlintInstaller;

#[async_trait]
impl Installer for ActionlintInstaller {
    fn id(&self) -> &'static str {
        "actionlint"
    }

    fn name(&self) -> &'static str {
        "actionlint"
    }

    fn description(&self) -> &'static str {
        "GitHub Actions workflow linter"
    }

    fn concurrency_safe(&self) -> bool {
        // Package manager operations need lock
        false
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        // Check if actionlint is in PATH
        let output = Command::new("actionlint").arg("--version").output().await;

        match output {
            Ok(out) if out.status.success() => {
                // Parse version from output (format: "1.7.10" or similar)
                let version_str = String::from_utf8_lossy(&out.stdout);
                let version_str = version_str.trim();

                // Try to parse as semver
                Version::parse(version_str)
                    .ok()
                    .or_else(|| {
                        // Try parsing just the numbers if it starts with a digit
                        version_str
                            .split_whitespace()
                            .find(|s| s.chars().next().is_some_and(|c| c.is_ascii_digit()))
                            .and_then(|v| Version::parse(v).ok())
                    })
                    .map(Some)
                    .ok_or_else(|| {
                        BootstrapError::DetectionFailed(format!(
                            "actionlint version output not parseable: {}",
                            version_str
                        ))
                    })
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install actionlint via package manager");
            return Ok(InstallResult {
                version: Version::new(0, 0, 0),
                installed_new: true,
                log_messages: vec!["Dry-run mode".to_string()],
            });
        }

        let package_name = match &ctx.package_manager {
            PackageManager::Homebrew => "actionlint",
            PackageManager::Apt => {
                // Actionlint may not be in apt, may need direct download
                // For now, try apt package
                "actionlint"
            }
            PackageManager::Snap => "actionlint",
            PackageManager::None => {
                return Err(BootstrapError::NoPackageManager(
                    "Cannot install actionlint: no package manager available".to_string(),
                ))
            }
        };

        ctx.package_manager_ops
            .install(ctx, package_name, None)
            .await
            .map_err(|e| BootstrapError::InstallFailed {
                tool: "actionlint".to_string(),
                exit_code: 1,
                stderr: e.to_string(),
            })?;

        // Detect version after install
        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::VerificationFailed("actionlint not found after install".to_string())
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec![format!("Installed actionlint via {}", package_name)],
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
                issues: vec!["actionlint not found in PATH".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_installer_metadata() {
        let installer = ActionlintInstaller;
        assert_eq!(installer.id(), "actionlint");
        assert_eq!(installer.name(), "actionlint");
        assert!(!installer.concurrency_safe());
    }
}
