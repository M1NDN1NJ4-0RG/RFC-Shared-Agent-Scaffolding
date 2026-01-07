//! # shfmt Installer
//!
//! Installer for shfmt (Shell script formatter).
//!
//! # Purpose
//!
//! Provides installation logic for shfmt via system package managers.
//! Shfmt is a REQUIRED tool per the bootstrap contract for Shell toolchain formatting.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::shfmt::ShfmtInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! let installer = ShfmtInstaller;
//! assert_eq!(installer.id(), "shfmt");
//! ```

use crate::bootstrap_v2::context::{Context, PackageManager};
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// shfmt installer
pub struct ShfmtInstaller;

#[async_trait]
impl Installer for ShfmtInstaller {
    fn id(&self) -> &'static str {
        "shfmt"
    }

    fn name(&self) -> &'static str {
        "shfmt"
    }

    fn description(&self) -> &'static str {
        "Shell script formatter"
    }

    fn concurrency_safe(&self) -> bool {
        // Package manager operations need lock
        false
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        // Check if shfmt is in PATH
        let output = Command::new("shfmt").arg("--version").output().await;

        match output {
            Ok(out) if out.status.success() => {
                // Parse version from output (format: "v3.8.0" or "3.8.0")
                let version_str = String::from_utf8_lossy(&out.stdout);
                let version_str = version_str.trim();

                // Remove leading 'v' if present
                let version_str = version_str.strip_prefix('v').unwrap_or(version_str);

                Version::parse(version_str).ok().map(Some).ok_or_else(|| {
                    BootstrapError::DetectionFailed(format!(
                        "shfmt version output not parseable: {}",
                        version_str
                    ))
                })
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install shfmt via package manager");
            return Ok(InstallResult {
                version: Version::new(0, 0, 0),
                installed_new: true,
                log_messages: vec!["Dry-run mode".to_string()],
            });
        }

        // Check if shfmt is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "shfmt already installed (version {})",
                    existing_version
                )],
            });
        }

        let package_name = match &ctx.package_manager {
            PackageManager::Homebrew => "shfmt",
            PackageManager::Apt => {
                // shfmt may not be in apt repos directly
                "shfmt"
            }
            PackageManager::Snap => "shfmt",
            PackageManager::None => {
                return Err(BootstrapError::NoPackageManager(
                    "Cannot install shfmt: no package manager available".to_string(),
                ))
            }
        };

        ctx.package_manager_ops
            .install(ctx, package_name, None)
            .await
            .map_err(|e| BootstrapError::InstallFailed {
                tool: "shfmt".to_string(),
                exit_code: 1,
                stderr: e.to_string(),
            })?;

        // Detect version after install
        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::VerificationFailed("shfmt not found after install".to_string())
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec![format!("Installed shfmt via {}", package_name)],
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
                issues: vec!["shfmt not found in PATH".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_installer_metadata() {
        let installer = ShfmtInstaller;
        assert_eq!(installer.id(), "shfmt");
        assert_eq!(installer.name(), "shfmt");
        assert!(!installer.concurrency_safe());
    }
}
