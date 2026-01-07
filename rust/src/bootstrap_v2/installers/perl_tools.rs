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

/// Normalize Perl version string to semver format
///
/// Perl tools often report versions with only 2 components (e.g., "1.156").
/// This function adds ".0" as the patch version to make them semver-compatible.
///
/// # Arguments
///
/// * `version_str` - Version string from Perl tool (e.g., "1.156" or "1.2.3")
///
/// # Returns
///
/// Version string with 3 components (e.g., "1.156.0" or "1.2.3")
fn normalize_perl_version(version_str: &str) -> String {
    let mut normalized = version_str.to_string();
    // If version has only 2 components (e.g., "1.156"), add ".0" for semver compatibility
    if normalized.matches('.').count() == 1 {
        normalized.push_str(".0");
    }
    normalized
}

/// Detect a Perl tool version with fallback path logic
///
/// Tries to detect a Perl tool by first checking an explicit path (e.g., ~/perl5/bin/tool),
/// then falling back to PATH if the explicit path fails. This handles tools installed via
/// cpanm to local::lib (~/ perl5) which may not be in PATH.
///
/// # Arguments
///
/// * `tool_name` - Name of the tool binary (e.g., "perlcritic")
/// * `explicit_path` - Full path to try first (e.g., "/home/user/perl5/bin/perlcritic")
/// * `version_arg` - Argument to get version (e.g., "--version")
/// * `perl5lib` - PERL5LIB environment value to set
/// * `parse_version` - Function to extract version from command output
///
/// # Returns
///
/// * `Ok(Some(Version))` - Tool found and version parsed successfully
/// * `Ok(None)` - Tool not found or version could not be parsed
/// * `Err(_)` - Command execution failed unexpectedly
async fn detect_perl_tool_with_fallback<F>(
    tool_name: &str,
    explicit_path: &str,
    version_arg: &str,
    perl5lib: &str,
    parse_version: F,
) -> BootstrapResult<Option<Version>>
where
    F: Fn(&str) -> Option<Version>,
{
    // Try explicit path first (handles tools installed to ~/perl5)
    let output = tokio::process::Command::new(explicit_path)
        .arg(version_arg)
        .env("PERL5LIB", perl5lib)
        .output()
        .await;

    // If explicit path doesn't work, try PATH
    let output = if output.is_err() || !output.as_ref().unwrap().status.success() {
        tokio::process::Command::new(tool_name)
            .arg(version_arg)
            .env("PERL5LIB", perl5lib)
            .output()
            .await
    } else {
        output
    };

    match output {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            Ok(parse_version(stdout.trim()))
        }
        _ => Ok(None),
    }
}

/// Get the Perl installation directory (~/perl5)
///
/// Returns the full path to the perl5 directory in the user's home directory.
/// Validates that the HOME environment variable is set and contains valid Unicode.
///
/// # Errors
///
/// Returns `BootstrapError::PerlToolchainFailed` if:
/// - HOME environment variable is not set
/// - HOME environment variable contains invalid Unicode
fn get_perl_install_dir() -> BootstrapResult<String> {
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
    Ok(format!("{}/perl5", home))
}

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
        // Set up Perl environment to detect tools installed in ~/perl5
        let perl_dir = get_perl_install_dir()?;
        let perl5lib = format!("{}/lib/perl5", perl_dir);
        let perlcritic_path = format!("{}/bin/perlcritic", perl_dir);

        detect_perl_tool_with_fallback(
            "perlcritic",
            &perlcritic_path,
            "--version",
            &perl5lib,
            |output| {
                // perlcritic --version outputs just the version number: "1.156"
                let version_str = normalize_perl_version(output);
                Version::parse(&version_str).ok()
            },
        )
        .await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        if ctx.dry_run {
            return Ok(InstallResult {
                version: Version::new(1, 0, 0),
                installed_new: false,
                log_messages: vec!["[DRY-RUN] Would install Perl::Critic via cpanm".to_string()],
            });
        }

        // Check if Perl::Critic is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "Perl::Critic already installed (version {})",
                    existing_version
                )],
            });
        }

        // Install using cpanm to ~/perl5
        let perl_dir = get_perl_install_dir()?;

        let output = tokio::process::Command::new("cpanm")
            .arg("--local-lib")
            .arg(&perl_dir)
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
        // Set up Perl environment to detect modules installed in ~/perl5
        let perl_dir = get_perl_install_dir()?;
        let perl5lib = format!("{}/lib/perl5", perl_dir);

        // PPI is a library, check via perl -MPPI -e
        let output = tokio::process::Command::new("perl")
            .arg("-MPPI")
            .arg("-e")
            .arg("print $PPI::VERSION")
            .env("PERL5LIB", &perl5lib)
            .output()
            .await;

        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let version_str = normalize_perl_version(stdout.trim());

                if let Ok(version) = Version::parse(&version_str) {
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

        // Check if PPI is already installed
        if let Some(existing_version) = self.detect(ctx).await? {
            return Ok(InstallResult {
                version: existing_version.clone(),
                installed_new: false,
                log_messages: vec![format!(
                    "PPI already installed (version {})",
                    existing_version
                )],
            });
        }

        // Install using cpanm to ~/perl5
        let perl_dir = get_perl_install_dir()?;

        let output = tokio::process::Command::new("cpanm")
            .arg("--local-lib")
            .arg(&perl_dir)
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
