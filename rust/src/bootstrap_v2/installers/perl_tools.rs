//! # Perl Tool Installers
//!
//! Installers for Perl development tools (Perl::Critic, PPI).
//!
//! # Purpose
//!
//! Provides installers for Perl linting and parsing tools using cpanm for installation.
//! Tools are installed to ~/perl5 following local::lib conventions.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::perl_tools::PerlCriticInstaller;
//! use bootstrap_v2::context::Context;
//! use bootstrap_v2::installer::Installer;
//!
//! # async fn example(ctx: &Context) -> anyhow::Result<()> {
//! let installer = PerlCriticInstaller;
//! let version = installer.detect(ctx).await?;
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::context::Context;
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;

/// Installer for Perl::Critic
pub struct PerlCriticInstaller;

#[async_trait]
impl Installer for PerlCriticInstaller {
    fn id(&self) -> &'static str {
        "perlcritic"
    }

    fn name(&self) -> &'static str {
        "Perl::Critic"
    }

    fn description(&self) -> &'static str {
        "Perl source code analyzer"
    }

    fn dependencies(&self) -> Vec<&'static str> {
        vec![]
    }

    fn concurrency_safe(&self) -> bool {
        false // cpanm uses package manager-like behavior
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        let output = tokio::process::Command::new("perlcritic")
            .arg("--version")
            .output()
            .await;

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                // perlcritic --version outputs: "Perl::Critic version 1.150"
                if let Some(version_str) = stdout.split_whitespace().nth(2) {
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
                log_messages: vec!["[DRY-RUN] Would install Perl::Critic via cpanm".to_string()],
            });
        }

        // Install using cpanm to ~/perl5
        let home = std::env::var("HOME").map_err(|e| match e {
            std::env::VarError::NotPresent => BootstrapError::PerlToolchainFailed(
                "HOME environment variable not set - cannot determine Perl install location"
                    .to_string(),
            ),
            std::env::VarError::NotUnicode(_) => BootstrapError::PerlToolchainFailed(
                "HOME environment variable contains invalid Unicode - cannot determine Perl install location"
                    .to_string(),
            ),
        })?;

        let output = tokio::process::Command::new("cpanm")
            .arg("--local-lib")
            .arg(format!("{}/perl5", home))
            .arg("Perl::Critic")
            .output()
            .await
            .map_err(|e| BootstrapError::PerlToolchainFailed(e.to_string()))?;

        if !output.status.success() {
            return Err(BootstrapError::PerlToolchainFailed(format!(
                "cpanm failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )));
        }

        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::PerlToolchainFailed(
                "Failed to detect version after install".to_string(),
            )
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["Installed Perl::Critic via cpanm".to_string()],
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
                issues: vec!["perlcritic not found on PATH".to_string()],
            }),
        }
    }
}

/// Installer for PPI (Perl parsing library)
pub struct PPIInstaller;

#[async_trait]
impl Installer for PPIInstaller {
    fn id(&self) -> &'static str {
        "ppi"
    }

    fn name(&self) -> &'static str {
        "PPI"
    }

    fn description(&self) -> &'static str {
        "Perl parsing and manipulation library"
    }

    fn dependencies(&self) -> Vec<&'static str> {
        vec![]
    }

    fn concurrency_safe(&self) -> bool {
        false // cpanm uses package manager-like behavior
    }

    async fn detect(&self, _ctx: &Context) -> BootstrapResult<Option<Version>> {
        // PPI is a library, check via perl -MPPI -e
        let output = tokio::process::Command::new("perl")
            .arg("-MPPI")
            .arg("-e")
            .arg("print $PPI::VERSION")
            .output()
            .await;

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                if let Ok(version) = Version::parse(stdout.trim()) {
                    return Ok(Some(version));
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
                log_messages: vec!["[DRY-RUN] Would install PPI via cpanm".to_string()],
            });
        }

        // Install using cpanm to ~/perl5
        let home = std::env::var("HOME").map_err(|_| {
            BootstrapError::PerlToolchainFailed(
                "HOME environment variable not set - cannot determine Perl install location"
                    .to_string(),
            )
        })?;

        let output = tokio::process::Command::new("cpanm")
            .arg("--local-lib")
            .arg(format!("{}/perl5", home))
            .arg("PPI")
            .output()
            .await
            .map_err(|e| BootstrapError::PerlToolchainFailed(e.to_string()))?;

        if !output.status.success() {
            return Err(BootstrapError::PerlToolchainFailed(format!(
                "cpanm failed: {}",
                String::from_utf8_lossy(&output.stderr)
            )));
        }

        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::PerlToolchainFailed(
                "Failed to detect version after install".to_string(),
            )
        })?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["Installed PPI via cpanm".to_string()],
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
                issues: vec!["PPI Perl module not found".to_string()],
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_perlcritic_metadata() {
        let installer = PerlCriticInstaller;
        assert_eq!(installer.id(), "perlcritic");
        assert_eq!(installer.name(), "Perl::Critic");
        assert!(!installer.concurrency_safe());
    }

    #[test]
    fn test_ppi_metadata() {
        let installer = PPIInstaller;
        assert_eq!(installer.id(), "ppi");
        assert_eq!(installer.name(), "PPI");
        assert!(!installer.concurrency_safe());
    }
}
