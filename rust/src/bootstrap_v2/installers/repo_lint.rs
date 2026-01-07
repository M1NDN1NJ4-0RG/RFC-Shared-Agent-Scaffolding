//! # repo-lint Installer
//!
//! Installer for the repo-lint tool via editable pip install.
//!
//! # Purpose
//!
//! Provides installer implementation for repo-lint that installs the package
//! in editable mode from the repository root (where pyproject.toml is located).
//! This achieves parity with the Bash bootstrapper's `pip install -e .` behavior.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::repo_lint::RepoLintInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! # async fn example() {
//! let installer = RepoLintInstaller;
//! // Use installer.detect(), install(), verify()
//! # }
//! ```

use crate::bootstrap_v2::context::Context;
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// Helper to install repo-lint in editable mode
async fn pip_install_editable(ctx: &Context) -> BootstrapResult<()> {
    if ctx.dry_run {
        println!("[DRY-RUN] Would install repo-lint via pip install -e .");
        return Ok(());
    }

    let venv_python = ctx.venv_python();

    // First upgrade pip, setuptools, and wheel
    let upgrade_output = Command::new(&venv_python)
        .args([
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ])
        .output()
        .await
        .map_err(|e| BootstrapError::CommandFailed {
            command: "pip install --upgrade pip setuptools wheel".to_string(),
            exit_code: None,
            stderr: e.to_string(),
        })?;

    if !upgrade_output.status.success() {
        return Err(BootstrapError::InstallFailed {
            tool: "pip/setuptools/wheel".to_string(),
            exit_code: upgrade_output.status.code().unwrap_or(-1),
            stderr: String::from_utf8_lossy(&upgrade_output.stderr).to_string(),
        });
    }

    // Install repo-lint in editable mode from repo root
    let output = Command::new(&venv_python)
        .args(["-m", "pip", "install", "-e", "."])
        .current_dir(&ctx.repo_root)
        .output()
        .await
        .map_err(|e| BootstrapError::CommandFailed {
            command: "pip install -e .".to_string(),
            exit_code: None,
            stderr: e.to_string(),
        })?;

    if !output.status.success() {
        return Err(BootstrapError::InstallFailed {
            tool: "repo-lint".to_string(),
            exit_code: output.status.code().unwrap_or(-1),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        });
    }

    Ok(())
}

/// Helper to detect repo-lint version
async fn detect_repo_lint(ctx: &Context) -> BootstrapResult<Option<Version>> {
    let repo_lint_bin = ctx.repo_lint_bin();

    // Check if repo-lint binary exists
    if !repo_lint_bin.exists() {
        return Ok(None);
    }

    // Try to get version from repo-lint --version
    let output = Command::new(&repo_lint_bin).arg("--version").output().await;

    match output {
        Ok(out) if out.status.success() => {
            let output_str = String::from_utf8_lossy(&out.stdout);
            // Try to parse version from output (format: "repo-lint, version X.Y.Z")
            for line in output_str.lines() {
                if line.contains("version") {
                    if let Some(ver_str) = line.split_whitespace().last() {
                        if let Ok(version) = Version::parse(ver_str) {
                            return Ok(Some(version));
                        }
                    }
                }
            }
            // If we can't parse version but command succeeded, return a placeholder
            Ok(Some(Version::new(0, 0, 0)))
        }
        _ => Ok(None),
    }
}

/// Helper to verify repo-lint --help works
async fn verify_repo_lint_help(ctx: &Context) -> BootstrapResult<bool> {
    let repo_lint_bin = ctx.repo_lint_bin();

    if !repo_lint_bin.exists() {
        return Ok(false);
    }

    let output = Command::new(&repo_lint_bin).arg("--help").output().await;

    Ok(matches!(output, Ok(out) if out.status.success()))
}

/// repo-lint installer
pub struct RepoLintInstaller;

#[async_trait]
impl Installer for RepoLintInstaller {
    fn id(&self) -> &'static str {
        "repo-lint"
    }

    fn name(&self) -> &'static str {
        "repo-lint"
    }

    fn description(&self) -> &'static str {
        "Multi-language linting and docstring validation tool"
    }

    fn concurrency_safe(&self) -> bool {
        false // pip operations need venv lock
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_repo_lint(ctx).await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        pip_install_editable(ctx).await?;

        let version = self.detect(ctx).await?.ok_or_else(|| {
            BootstrapError::PythonToolsFailed("repo-lint install verification failed".to_string())
        })?;

        // Verify that --help works
        if !verify_repo_lint_help(ctx).await? {
            return Err(BootstrapError::PythonToolsFailed(
                "repo-lint installed but --help command failed".to_string(),
            ));
        }

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec!["repo-lint installed successfully".to_string()],
        })
    }

    async fn verify(&self, ctx: &Context) -> BootstrapResult<VerifyResult> {
        match self.detect(ctx).await? {
            Some(version) => {
                // Also verify --help works
                if !verify_repo_lint_help(ctx).await? {
                    return Ok(VerifyResult {
                        success: false,
                        version: Some(version),
                        issues: vec!["repo-lint found but --help command failed".to_string()],
                    });
                }

                Ok(VerifyResult {
                    success: true,
                    version: Some(version),
                    issues: vec![],
                })
            }
            None => Ok(VerifyResult {
                success: false,
                version: None,
                issues: vec!["repo-lint not found".to_string()],
            }),
        }
    }
}
