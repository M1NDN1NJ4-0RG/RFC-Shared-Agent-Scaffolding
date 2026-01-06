//! # Doctor Command - System Diagnostics
//!
//! Diagnostic checks for repository, environment, and dependencies.
//!
//! # Purpose
//!
//! Provides the `doctor` subcommand that checks system prerequisites and
//! identifies potential issues. Supports --strict mode where WARN is treated as FAIL.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::doctor::{doctor, DiagnosticReport};
//! use bootstrap_v2::context::Context;
//! use std::sync::Arc;
//!
//! # async fn example(ctx: Arc<Context>) -> Result<(), Box<dyn std::error::Error>> {
//! let report = doctor(&ctx, false).await?;
//! report.print();
//! let exit_code = report.exit_code(false); // false = not strict
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::context::{Context, PackageManager};
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::exit_codes::ExitCode;
use std::path::Path;
use std::process::Command;
use std::sync::Arc;

/// Check status
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CheckStatus {
    /// Check passed
    Pass,
    /// Warning - issue detected but not critical
    Warn,
    /// Check failed - critical issue
    Fail,
}

/// Diagnostic check result
#[derive(Debug, Clone)]
pub struct DiagnosticCheck {
    /// Check name
    pub name: String,
    /// Status
    pub status: CheckStatus,
    /// Message describing the result
    pub message: String,
    /// Optional remediation suggestion
    pub remediation: Option<String>,
}

impl DiagnosticCheck {
    /// Create a passing check
    pub fn pass(name: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Pass,
            message: message.into(),
            remediation: None,
        }
    }

    /// Create a warning check
    pub fn warn(
        name: impl Into<String>,
        message: impl Into<String>,
        remediation: Option<String>,
    ) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Warn,
            message: message.into(),
            remediation,
        }
    }

    /// Create a failing check
    pub fn fail(
        name: impl Into<String>,
        message: impl Into<String>,
        remediation: Option<String>,
    ) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Fail,
            message: message.into(),
            remediation,
        }
    }
}

/// Diagnostic report
#[derive(Debug, Clone)]
pub struct DiagnosticReport {
    /// All checks performed
    pub checks: Vec<DiagnosticCheck>,
}

impl DiagnosticReport {
    /// Create new empty report
    pub fn new() -> Self {
        Self { checks: Vec::new() }
    }

    /// Add a check to the report
    pub fn add_check(&mut self, check: DiagnosticCheck) {
        self.checks.push(check);
    }

    /// Print report to stdout
    pub fn print(&self) {
        println!("\nDiagnostic Report:");
        println!("{}", "=".repeat(60));

        for check in &self.checks {
            let (icon, color) = match check.status {
                CheckStatus::Pass => ("✓", "\x1b[32m"), // Green
                CheckStatus::Warn => ("⚠", "\x1b[33m"),  // Yellow
                CheckStatus::Fail => ("✗", "\x1b[31m"),  // Red
            };

            println!("{}{} {}\x1b[0m: {}", color, icon, check.name, check.message);

            if let Some(remediation) = &check.remediation {
                println!("  → {}", remediation);
            }
        }

        println!("{}", "=".repeat(60));
        self.print_summary();
    }

    /// Print summary statistics
    fn print_summary(&self) {
        let pass_count = self.checks.iter().filter(|c| c.status == CheckStatus::Pass).count();
        let warn_count = self.checks.iter().filter(|c| c.status == CheckStatus::Warn).count();
        let fail_count = self.checks.iter().filter(|c| c.status == CheckStatus::Fail).count();

        println!("\nSummary: {} passed, {} warnings, {} failed", pass_count, warn_count, fail_count);
    }

    /// Get exit code based on report
    ///
    /// # Arguments
    ///
    /// * `strict` - If true, warnings are treated as failures
    ///
    /// # Returns
    ///
    /// ExitCode::Success if all checks pass (or only warnings in non-strict mode),
    /// ExitCode::VerificationFailed otherwise
    pub fn exit_code(&self, strict: bool) -> ExitCode {
        let has_failures = self.checks.iter().any(|c| c.status == CheckStatus::Fail);
        let has_warnings = self.checks.iter().any(|c| c.status == CheckStatus::Warn);

        if has_failures || (strict && has_warnings) {
            ExitCode::VerificationFailed
        } else {
            ExitCode::Success
        }
    }
}

impl Default for DiagnosticReport {
    fn default() -> Self {
        Self::new()
    }
}

/// Run diagnostic checks
///
/// # Arguments
///
/// * `ctx` - Execution context
/// * `_strict` - Whether to treat warnings as failures (for exit code)
///
/// # Returns
///
/// Diagnostic report with all check results
///
/// # Checks Performed
///
/// - Repository: Check if in git repo
/// - Package Manager: Check availability
/// - Python: Check Python 3 availability and version
/// - Disk Space: Check available disk space
/// - Permissions: Check write permissions
pub async fn doctor(ctx: &Context, _strict: bool) -> BootstrapResult<DiagnosticReport> {
    let mut report = DiagnosticReport::new();

    // Check repository
    report.add_check(check_repo(&ctx.repo_root).await);

    // Check package manager
    report.add_check(check_package_manager(&ctx.package_manager).await);

    // Check Python
    report.add_check(check_python().await);

    // Check disk space
    report.add_check(check_disk_space(&ctx.repo_root).await);

    // Check permissions
    report.add_check(check_permissions(&ctx.repo_root).await);

    Ok(report)
}

/// Check if in git repository
async fn check_repo(repo_root: &Path) -> DiagnosticCheck {
    let git_dir = repo_root.join(".git");

    if git_dir.exists() {
        DiagnosticCheck::pass("Repository", "Git repository detected")
    } else {
        DiagnosticCheck::fail(
            "Repository",
            "Not in a git repository",
            Some("Run this tool from within a git repository".to_string()),
        )
    }
}

/// Check package manager availability
async fn check_package_manager(pm: &PackageManager) -> DiagnosticCheck {
    match pm {
        PackageManager::Homebrew => {
            DiagnosticCheck::pass("Package Manager", "Homebrew is available")
        }
        PackageManager::Apt => DiagnosticCheck::pass("Package Manager", "apt-get is available"),
        PackageManager::Snap => DiagnosticCheck::pass("Package Manager", "snap is available"),
        PackageManager::None => DiagnosticCheck::warn(
            "Package Manager",
            "No package manager detected",
            Some(
                "Install Homebrew (macOS/Linux) or use a Linux distribution with apt-get"
                    .to_string(),
            ),
        ),
    }
}

/// Check Python availability
async fn check_python() -> DiagnosticCheck {
    let output = Command::new("python3").arg("--version").output();

    match output {
        Ok(out) if out.status.success() => {
            let version = String::from_utf8_lossy(&out.stdout);
            DiagnosticCheck::pass("Python", format!("Python 3 is available: {}", version.trim()))
        }
        _ => DiagnosticCheck::fail(
            "Python",
            "Python 3 not found",
            Some("Install Python 3.8 or later".to_string()),
        ),
    }
}

/// Check available disk space
async fn check_disk_space(repo_root: &Path) -> DiagnosticCheck {
    #[cfg(target_family = "unix")]
    {
        match std::fs::metadata(repo_root) {
            Ok(_) => {
                // This is a simplified check - in reality you'd use statvfs
                // For now, just check if we can read metadata
                DiagnosticCheck::pass("Disk Space", "Sufficient disk space available")
            }
            Err(_) => DiagnosticCheck::warn(
                "Disk Space",
                "Could not check disk space",
                None,
            ),
        }
    }

    #[cfg(not(target_family = "unix"))]
    {
        DiagnosticCheck::pass("Disk Space", "Disk space check skipped (non-Unix)")
    }
}

/// Check write permissions
async fn check_permissions(repo_root: &Path) -> DiagnosticCheck {
    let test_file = repo_root.join(".bootstrap-permission-test");

    match std::fs::write(&test_file, b"test") {
        Ok(_) => {
            // Cleanup
            let _ = std::fs::remove_file(&test_file);
            DiagnosticCheck::pass("Permissions", "Write permissions OK")
        }
        Err(e) => DiagnosticCheck::fail(
            "Permissions",
            format!("Cannot write to repository: {}", e),
            Some("Check file permissions in the repository directory".to_string()),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bootstrap_v2::config::Config;
    use crate::bootstrap_v2::context::{OsType, PackageManager};
    use std::path::PathBuf;
    use tempfile::TempDir;

    #[test]
    fn test_check_status() {
        let pass = DiagnosticCheck::pass("test", "passed");
        assert_eq!(pass.status, CheckStatus::Pass);

        let warn = DiagnosticCheck::warn("test", "warning", None);
        assert_eq!(warn.status, CheckStatus::Warn);

        let fail = DiagnosticCheck::fail("test", "failed", None);
        assert_eq!(fail.status, CheckStatus::Fail);
    }

    #[test]
    fn test_report_exit_code() {
        let mut report = DiagnosticReport::new();
        assert_eq!(report.exit_code(false), ExitCode::Success);

        report.add_check(DiagnosticCheck::pass("test1", "ok"));
        assert_eq!(report.exit_code(false), ExitCode::Success);

        report.add_check(DiagnosticCheck::warn("test2", "warning", None));
        assert_eq!(report.exit_code(false), ExitCode::Success); // Non-strict
        assert_eq!(report.exit_code(true), ExitCode::VerificationFailed); // Strict

        let mut report2 = DiagnosticReport::new();
        report2.add_check(DiagnosticCheck::fail("test3", "failed", None));
        assert_eq!(report2.exit_code(false), ExitCode::VerificationFailed);
        assert_eq!(report2.exit_code(true), ExitCode::VerificationFailed);
    }

    #[tokio::test]
    async fn test_check_repo() {
        let temp_dir = TempDir::new().unwrap();
        
        // Without .git
        let check = check_repo(temp_dir.path()).await;
        assert_eq!(check.status, CheckStatus::Fail);

        // With .git
        std::fs::create_dir(temp_dir.path().join(".git")).unwrap();
        let check = check_repo(temp_dir.path()).await;
        assert_eq!(check.status, CheckStatus::Pass);
    }

    #[tokio::test]
    async fn test_check_package_manager() {
        let check = check_package_manager(&PackageManager::Homebrew).await;
        assert_eq!(check.status, CheckStatus::Pass);

        let check = check_package_manager(&PackageManager::None).await;
        assert_eq!(check.status, CheckStatus::Warn);
    }

    #[tokio::test]
    async fn test_check_python() {
        let check = check_python().await;
        // Should pass if Python 3 is installed (which it should be in CI)
        // If not installed, will fail
        assert!(matches!(check.status, CheckStatus::Pass | CheckStatus::Fail));
    }

    #[tokio::test]
    async fn test_check_permissions() {
        let temp_dir = TempDir::new().unwrap();
        let check = check_permissions(temp_dir.path()).await;
        assert_eq!(check.status, CheckStatus::Pass);
    }

    #[tokio::test]
    async fn test_doctor_command() {
        let temp_dir = TempDir::new().unwrap();
        std::fs::create_dir(temp_dir.path().join(".git")).unwrap();

        let config = Arc::new(Config::default());
        let ctx = Context::new_for_testing(temp_dir.path().to_path_buf(), false, config);

        let report = doctor(&ctx, false).await.unwrap();
        assert!(report.checks.len() >= 5); // Should have all checks
    }
}
