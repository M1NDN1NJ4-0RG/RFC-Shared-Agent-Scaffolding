//! # shellcheck Installer
//!
//! Installer for shellcheck (Bash/shell script linter).
//!
//! # Purpose
//!
//! Provides installation logic for shellcheck via system package managers.
//! Shellcheck is a REQUIRED tool per the bootstrap contract for Shell toolchain.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::shellcheck::ShellcheckInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! let installer = ShellcheckInstaller;
//! assert_eq!(installer.id(), "shellcheck");
//! ```

use crate::bootstrap_v2::context::{Context, PackageManager};
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// shellcheck installer
pub struct ShellcheckInstaller;

#[async_trait]
impl Installer for ShellcheckInstaller {
    fn id(&self) -> &'static str {
        "shellcheck"
    }

    fn name(&self) -> &'static str {
        "shellcheck"
    }

    fn description(&self) -> &'static str {
        "Shell script linter"
    }

    fn concurrency_safe(&self) -> bool {
        // Package manager operations need lock
        false
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        // Check if shellcheck is in PATH
        let output = Command::new("shellcheck").arg("--version").output().await;

        match output {
            Ok(out) if out.status.success() => {
                // Parse version from output (format: "ShellCheck - shell script analysis tool\nversion: 0.9.0")
                let version_str = String::from_utf8_lossy(&out.stdout);

                // Find the version line
                for line in version_str.lines() {
                    if line.starts_with("version:") {
                        if let Some(v) = line.split(':').nth(1) {
                            let v = v.trim();
                            if let Ok(version) = Version::parse(v) {
                                return Ok(Some(version));
                            }
                        }
                    }
                }

                Err(BootstrapError::DetectionFailed(format!(
                    "shellcheck version output not parseable: {}",
                    version_str
                )))
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            println!("[DRY-RUN] Would install shellcheck via package manager");
            return Ok(InstallResult {
                version: Version::new(0, 0, 0),
                installed_new: true,
                log_messages: vec!["Dry-run mode".to_string()],
            });
        }

        // Check if shellcheck is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "shellcheck already installed (version {})",
                    existing_version
                )],
            });
        }

        let package_name = match &ctx.package_manager {
            PackageManager::Homebrew => "shellcheck",
            PackageManager::Apt => "shellcheck",
            PackageManager::Snap => "shellcheck",
            PackageManager::None => {
                return Err(BootstrapError::NoPackageManager(
                    "Cannot install shellcheck: no package manager available".to_string(),
                ))
            }
        };

        ctx.package_manager_ops
            .install(ctx, package_name, None)
            .await
            .map_err(|e| BootstrapError::InstallFailed {
                tool: "shellcheck".to_string(),
                exit_code: 1,
                stderr: e.to_string(),
            })?;

        // Detect version after install
        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::VerificationFailed("shellcheck not found after install".to_string())
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec![format!("Installed shellcheck via {}", package_name)],
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
                issues: vec!["shellcheck not found in PATH".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_installer_metadata() {
        let installer = ShellcheckInstaller;
        assert_eq!(installer.id(), "shellcheck");
        assert_eq!(installer.name(), "shellcheck");
        assert!(!installer.concurrency_safe());
    }
}
