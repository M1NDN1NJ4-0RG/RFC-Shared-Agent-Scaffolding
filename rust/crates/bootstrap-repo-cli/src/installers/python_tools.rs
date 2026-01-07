//! # Python Tools Installers
//!
//! Installers for Python-based tools (black, ruff, pylint, etc.)
//!
//! # Purpose
//!
//! Provides installer implementations for Python tools that are installed via pip
//! in the repository's virtual environment (.venv).
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::python_tools::BlackInstaller;
//! use bootstrap_v2::installer::Installer;
//!
//! # async fn example() {
//! let installer = BlackInstaller;
//! // Use installer.detect(), install(), verify()
//! # }
//! ```

use crate::context::Context;
use crate::errors::{BootstrapError, BootstrapResult};
use crate::installer::{InstallResult, Installer, VerifyResult};
use async_trait::async_trait;
use semver::Version;
use tokio::process::Command;

/// Helper to run pip install in venv
async fn pip_install(ctx: &Context, package: &str) -> BootstrapResult<()> {
    if ctx.dry_run {
        println!("[DRY-RUN] Would install {} via pip", package);
        return Ok(());
    }

    let venv_python = ctx.venv_python();
    let output = Command::new(&venv_python)
        .args(["-m", "pip", "install", package])
        .output()
        .await
        .map_err(|e| BootstrapError::CommandFailed {
            command: format!("pip install {}", package),
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

/// Helper to install and verify a Python package
/// Returns placeholder version in dry-run mode
async fn install_and_verify_python_tool(
    ctx: &Context,
    package_name: &str,
    tool_name: &str,
) -> BootstrapResult<InstallResult> {
    pip_install(ctx, package_name).await?;

    // In dry-run mode, return placeholder version without detection
    if ctx.dry_run {
        return Ok(InstallResult {
            version: Version::new(0, 0, 0),
            installed_new: true,
            log_messages: vec![format!("[DRY-RUN] Would install {}", tool_name)],
        });
    }

    // Real install: verify by detecting version
    let version = detect_python_tool(ctx, tool_name).await?.ok_or_else(|| {
        BootstrapError::PythonToolsFailed(format!(
            "{} install verification failed - not found after installation",
            tool_name
        ))
    })?;

    Ok(InstallResult {
        version,
        installed_new: true,
        log_messages: vec![format!("{} installed successfully", tool_name)],
    })
}

/// Helper to detect Python package version
async fn detect_python_tool(ctx: &Context, tool_name: &str) -> BootstrapResult<Option<Version>> {
    let venv_python = ctx.venv_python();
    let output = Command::new(&venv_python)
        .args(["-m", "pip", "show", tool_name])
        .output()
        .await;

    match output {
        Ok(out) if out.status.success() => {
            let output_str = String::from_utf8_lossy(&out.stdout);
            for line in output_str.lines() {
                if line.starts_with("Version:") {
                    if let Some(ver) = line.split_whitespace().nth(1) {
                        if let Ok(version) = Version::parse(ver) {
                            return Ok(Some(version));
                        }
                    }
                }
            }
            Ok(Some(Version::new(0, 0, 0)))
        }
        _ => Ok(None),
    }
}

/// Black formatter installer
pub struct BlackInstaller;

#[async_trait]
impl Installer for BlackInstaller {
    fn id(&self) -> &'static str {
        "python-black"
    }

    fn name(&self) -> &'static str {
        "black"
    }

    fn description(&self) -> &'static str {
        "Python code formatter"
    }

    fn concurrency_safe(&self) -> bool {
        false // pip operations need venv lock
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_python_tool(ctx, "black").await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        install_and_verify_python_tool(ctx, "black", "black").await
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
                issues: vec!["black not found".to_string()],
            }),
        }
    }
}

/// Ruff linter installer
pub struct RuffInstaller;

#[async_trait]
impl Installer for RuffInstaller {
    fn id(&self) -> &'static str {
        "python-ruff"
    }

    fn name(&self) -> &'static str {
        "ruff"
    }

    fn description(&self) -> &'static str {
        "Fast Python linter"
    }

    fn concurrency_safe(&self) -> bool {
        false
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_python_tool(ctx, "ruff").await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        install_and_verify_python_tool(ctx, "ruff", "ruff").await
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
                issues: vec!["ruff not found".to_string()],
            }),
        }
    }
}

/// Pylint installer
pub struct PylintInstaller;

#[async_trait]
impl Installer for PylintInstaller {
    fn id(&self) -> &'static str {
        "python-pylint"
    }

    fn name(&self) -> &'static str {
        "pylint"
    }

    fn description(&self) -> &'static str {
        "Python linter"
    }

    fn concurrency_safe(&self) -> bool {
        false
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_python_tool(ctx, "pylint").await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        install_and_verify_python_tool(ctx, "pylint", "pylint").await
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
                issues: vec!["pylint not found".to_string()],
            }),
        }
    }
}

/// yamllint installer
pub struct YamllintInstaller;

#[async_trait]
impl Installer for YamllintInstaller {
    fn id(&self) -> &'static str {
        "yamllint"
    }

    fn name(&self) -> &'static str {
        "yamllint"
    }

    fn description(&self) -> &'static str {
        "YAML linter"
    }

    fn concurrency_safe(&self) -> bool {
        false
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_python_tool(ctx, "yamllint").await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        install_and_verify_python_tool(ctx, "yamllint", "yamllint").await
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
                issues: vec!["yamllint not found".to_string()],
            }),
        }
    }
}

/// pytest installer
pub struct PytestInstaller;

#[async_trait]
impl Installer for PytestInstaller {
    fn id(&self) -> &'static str {
        "pytest"
    }

    fn name(&self) -> &'static str {
        "pytest"
    }

    fn description(&self) -> &'static str {
        "Python testing framework"
    }

    fn concurrency_safe(&self) -> bool {
        false
    }

    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>> {
        detect_python_tool(ctx, "pytest").await
    }

    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult> {
        install_and_verify_python_tool(ctx, "pytest", "pytest").await
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
                issues: vec!["pytest not found".to_string()],
            }),
        }
    }
}
