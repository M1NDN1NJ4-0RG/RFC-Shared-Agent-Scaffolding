//! # PowerShell Tool Installers
//!
//! Installers for PowerShell development tools (pwsh, PSScriptAnalyzer).
//!
//! # Purpose
//!
//! Provides installers for PowerShell interpreter and linting tools.
//! PSScriptAnalyzer is installed as a PowerShell module.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::powershell_tools::PwshInstaller;
//! use bootstrap_v2::context::Context;
//! use bootstrap_v2::installer::Installer;
//!
//! # async fn example(ctx: &Context) -> anyhow::Result<()> {
//! let installer = PwshInstaller;
//! let version = installer.detect(ctx).await?;
//! # Ok(())
//! # }
//! ```

use crate::context::Context;
use crate::context::PackageManager;
use crate::errors::{BootstrapError, BootstrapResult};
use crate::installer::{InstallResult, Installer, VerifyResult};
use crate::package_manager::{HomebrewOps, PackageManagerOps};
use async_trait::async_trait;
use semver::Version;

/// Installer for pwsh (PowerShell Core)
pub struct PwshInstaller;

#[async_trait]
impl Installer for PwshInstaller {
    fn id(&self) -> &'static str {
        "pwsh"
    }

    fn name(&self) -> &'static str {
        "PowerShell Core"
    }

    fn description(&self) -> &'static str {
        "PowerShell interpreter (cross-platform)"
    }

    fn dependencies(&self) -> Vec<&'static str> {
        vec![]
    }

    fn concurrency_safe(&self) -> bool {
        false // Uses package manager
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        let output = tokio::process::Command::new("pwsh")
            .arg("-Version")
            .output()
            .await;

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                // pwsh -Version outputs: "PowerShell 7.4.0"
                if let Some(version_str) = stdout.split_whitespace().nth(1) {
                    if let Ok(version) = Version::parse(version_str) {
                        return Ok(Some(version));
                    }
                }
                Ok(None)
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            return Ok(InstallResult {
                version: Version::new(7, 0, 0),
                installed_new: false,
                log_messages: vec!["[DRY-RUN] Would install pwsh via package manager".to_string()],
            });
        }

        // Check if PowerShell is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "PowerShell Core already installed (version {})",
                    existing_version
                )],
            });
        }

        match ctx.package_manager {
            PackageManager::Homebrew => {
                let pm: Box<dyn PackageManagerOps> = Box::new(HomebrewOps);
                pm.install(ctx, "powershell", None).await?;
            }
            PackageManager::Apt => {
                // On Ubuntu/Debian, pwsh requires snap or manual installation
                // Try snap first if available
                let snap_check = tokio::process::Command::new("snap")
                    .arg("version")
                    .output()
                    .await;

                if snap_check.is_ok() {
                    // Check if sudo is available and passwordless
                    let sudo_check = tokio::process::Command::new("sudo")
                        .arg("-n")
                        .arg("true")
                        .output()
                        .await;

                    match sudo_check {
                        Ok(output) if output.status.success() => {
                            // sudo is available and passwordless, proceed with installation
                        }
                        _ => {
                            return Err(BootstrapError::PowerShellToolchainFailed(
                                "sudo -n failed: passwordless sudo required for snap installation. \
                                 Please run: sudo snap install powershell --classic"
                                    .to_string(),
                            ));
                        }
                    }

                    let output = tokio::process::Command::new("sudo")
                        .arg("-n")
                        .arg("snap")
                        .arg("install")
                        .arg("powershell")
                        .arg("--classic")
                        .output()
                        .await
                        .map_err(|e| BootstrapError::PowerShellToolchainFailed(e.to_string()))?;

                    if !output.status.success() {
                        return Err(BootstrapError::PowerShellToolchainFailed(format!(
                            "snap install failed: {}",
                            String::from_utf8_lossy(&output.stderr)
                        )));
                    }
                } else {
                    return Err(BootstrapError::PowerShellToolchainFailed(
                        "PowerShell requires snap on Linux systems without Homebrew. \
                         Please install manually: sudo snap install powershell --classic"
                            .to_string(),
                    ));
                }
            }
            _ => {
                return Err(BootstrapError::PowerShellToolchainFailed(
                    "No package manager available for PowerShell installation".to_string(),
                ));
            }
        }

        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::PowerShellToolchainFailed(
                "Failed to detect version after install".to_string(),
            )
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["Installed PowerShell Core".to_string()],
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
                issues: vec!["pwsh not found on PATH".to_string()],
            }),
        }
    }
}

/// Installer for PSScriptAnalyzer
pub struct PSScriptAnalyzerInstaller;

#[async_trait]
impl Installer for PSScriptAnalyzerInstaller {
    fn id(&self) -> &'static str {
        "psscriptanalyzer"
    }

    fn name(&self) -> &'static str {
        "PSScriptAnalyzer"
    }

    fn description(&self) -> &'static str {
        "PowerShell script analyzer and linter"
    }

    fn dependencies(&self) -> Vec<&'static str> {
        vec!["pwsh"] // Requires PowerShell
    }

    fn concurrency_safe(&self) -> bool {
        false // PowerShell module installation is not concurrency-safe
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        // Check if PSScriptAnalyzer module is installed
        let output = tokio::process::Command::new("pwsh")
            .arg("-NoProfile")
            .arg("-Command")
            .arg("(Get-Module -ListAvailable PSScriptAnalyzer).Version.ToString()")
            .output()
            .await;

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let version_str = stdout.trim();
                if !version_str.is_empty() {
                    if let Ok(version) = Version::parse(version_str) {
                        return Ok(Some(version));
                    }
                }
                Ok(None)
            }
            _ => Ok(None),
        }
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            return Ok(InstallResult {
                version: Version::new(1, 0, 0),
                installed_new: false,
                log_messages: vec![
                    "[DRY-RUN] Would install PSScriptAnalyzer PowerShell module".to_string()
                ],
            });
        }

        // Install PSScriptAnalyzer module for current user
        let output = tokio::process::Command::new("pwsh")
            .arg("-NoProfile")
            .arg("-Command")
            .arg("Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force -SkipPublisherCheck")
            .output()
            .await
            .map_err(|e| BootstrapError::PowerShellToolchainFailed(e.to_string()))?;

        if !output.status.success() {
            return Err(BootstrapError::PowerShellToolchainFailed(format!(
                "Install-Module failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )));
        }

        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::PowerShellToolchainFailed(
                "Failed to detect version after install".to_string(),
            )
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["Installed PSScriptAnalyzer PowerShell module".to_string()],
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
                issues: vec!["PSScriptAnalyzer PowerShell module not installed".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pwsh_metadata() {
        let installer = PwshInstaller;
        assert_eq!(installer.id(), "pwsh");
        assert_eq!(installer.name(), "PowerShell Core");
        assert!(!installer.concurrency_safe());
    }

    #[test]
    fn test_psscriptanalyzer_metadata() {
        let installer = PSScriptAnalyzerInstaller;
        assert_eq!(installer.id(), "psscriptanalyzer");
        assert_eq!(installer.name(), "PSScriptAnalyzer");
        assert_eq!(installer.dependencies(), vec!["pwsh"]);
        assert!(!installer.concurrency_safe());
    }
}
