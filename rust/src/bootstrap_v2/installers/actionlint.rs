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
use std::collections::HashSet;
use std::path::PathBuf;
use tokio::process::Command;

/// Get candidate paths where actionlint might be installed
///
/// Returns a list of paths to check for actionlint, in priority order:
/// 1. "actionlint" (PATH lookup - fastest if it works)
/// 2. $HOME/go/bin/actionlint (default go install location)
/// 3. $GOPATH/bin/actionlint (if GOPATH is set)
///
/// This is necessary because actionlint is installed via `go install` which
/// puts binaries in the Go bin directory, not in system PATH by default.
fn get_actionlint_candidates() -> Vec<String> {
    let mut candidates = vec!["actionlint".to_string()];
    let mut seen = HashSet::new();
    seen.insert("actionlint".to_string());

    // Try $HOME/go/bin/actionlint (default location for go install)
    if let Ok(home) = std::env::var("HOME") {
        let go_bin_path = PathBuf::from(home)
            .join("go")
            .join("bin")
            .join("actionlint");
        let path_str = go_bin_path.to_string_lossy().to_string();
        if seen.insert(path_str.clone()) {
            candidates.push(path_str);
        }
    }

    // Try $GOPATH/bin/actionlint (custom GOPATH)
    if let Ok(gopath) = std::env::var("GOPATH") {
        let gopath_bin = PathBuf::from(gopath).join("bin").join("actionlint");
        let path_str = gopath_bin.to_string_lossy().to_string();
        if seen.insert(path_str.clone()) {
            candidates.push(path_str);
        }
    }

    candidates
}

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
        // Try multiple locations where actionlint might be installed:
        // 1. PATH (default lookup)
        // 2. $HOME/go/bin (default go install location)
        // 3. $(go env GOPATH)/bin (custom GOPATH)

        let candidates = get_actionlint_candidates();

        for candidate in candidates {
            let output = Command::new(&candidate).arg("--version").output().await;

            if let Ok(out) = output {
                if out.status.success() {
                    // Parse version from output (format: "v1.7.10" or "1.7.10" on first line)
                    let version_str = String::from_utf8_lossy(&out.stdout);
                    // Take only the first line since output may be multi-line
                    let version_str = version_str.lines().next().unwrap_or("").trim();

                    // Skip empty version strings
                    if version_str.is_empty() {
                        continue;
                    }

                    // Try to parse as semver, handling optional 'v' prefix
                    let version_without_v = version_str.strip_prefix('v').unwrap_or(version_str);
                    let version = Version::parse(version_without_v).ok().or_else(|| {
                        // Try parsing just the numbers if it starts with a digit
                        version_str
                            .split_whitespace()
                            .find(|s| s.chars().next().is_some_and(|c| c.is_ascii_digit()))
                            .and_then(|v| {
                                let v_clean = v.strip_prefix('v').unwrap_or(v);
                                Version::parse(v_clean).ok()
                            })
                    });

                    if let Some(v) = version {
                        return Ok(Some(v));
                    }
                }
            }
        }

        // Not found in any location
        Ok(None)
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
