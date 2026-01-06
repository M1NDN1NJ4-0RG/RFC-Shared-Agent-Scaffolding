//! # Error Type Hierarchy
//!
//! Defines all error types used by the bootstrap CLI with proper error chaining.
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.
//! Uses thiserror for ergonomic error handling and anyhow for error context.
//!
//! # Error Categories
//!
//! - Repository errors: NotInRepo, NoInstallTarget
//! - Installation errors: VenvActivation, InstallFailed
//! - Verification errors: VerificationFailed
//! - Configuration errors: ConfigError
//! - Runtime errors: IoError, CommandFailed
//!
//! # Examples
//!
//! ```
//! use bootstrap_v2::errors::BootstrapError;
//! use bootstrap_v2::exit_codes::ExitCode;
//!
//! fn do_something() -> Result<(), BootstrapError> {
//!     Err(BootstrapError::NotInRepo)
//! }
//!
//! match do_something() {
//!     Err(e) => {
//!         let code = e.exit_code();
//!         eprintln!("Error: {}", e);
//!         std::process::exit(code.as_i32());
//!     }
//!     Ok(_) => {}
//! }
//! ```

use crate::bootstrap_v2::exit_codes::ExitCode;
use thiserror::Error;

/// Main error type for bootstrap operations
#[derive(Debug, Error)]
pub enum BootstrapError {
    /// Not in a git repository
    #[error("Not in git repository")]
    NotInRepo,

    /// Virtual environment activation failed
    #[error("Virtual environment activation failed: {0}")]
    VenvActivation(String),

    /// Installation failed for a specific tool
    #[error("Installation failed: {tool} (exit code {exit_code})")]
    InstallFailed {
        tool: String,
        exit_code: i32,
        stderr: String,
    },

    /// No install target found (no pyproject.toml, setup.py, etc.)
    #[error("Could not determine where to install repo-lint (no packaging metadata found)")]
    NoInstallTarget,

    /// repo-lint upgrade failed
    #[error("Failed to upgrade repo-lint: {0}")]
    RepoLintUpgradeFailed(String),

    /// repo-lint install failed
    #[error("Failed to install repo-lint: {0}")]
    RepoLintInstallFailed(String),

    /// Python tools failed
    #[error("Python tools failed: {0}")]
    PythonToolsFailed(String),

    /// Verification failed
    #[error("Verification failed: {0}")]
    VerificationFailed(String),

    /// Configuration error
    #[error("Configuration error: {0}")]
    ConfigError(String),

    /// IO error
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    /// Command execution failed
    #[error("Command failed: {command}")]
    CommandFailed {
        command: String,
        exit_code: Option<i32>,
        stderr: String,
    },

    /// Tool not found
    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    /// Detection failed
    #[error("Detection failed: {0}")]
    DetectionFailed(String),

    /// No package manager available
    #[error("No package manager available: {0}")]
    NoPackageManager(String),

    /// Dependency resolution failed
    #[error("Dependency resolution failed: {0}")]
    DependencyResolution(String),

    /// Cyclic dependency detected
    #[error("Cyclic dependency detected in installer graph")]
    CyclicDependency,

    /// HTTP request failed
    #[error("HTTP request failed: {0}")]
    HttpError(String),

    /// Checksum verification failed
    #[error("Checksum verification failed for {artifact}: expected {expected}, got {actual}")]
    ChecksumMismatch {
        artifact: String,
        expected: String,
        actual: String,
    },

    /// Generic error with context
    #[error(transparent)]
    Other(#[from] anyhow::Error),
}

impl BootstrapError {
    /// Map error to appropriate exit code
    pub fn exit_code(&self) -> ExitCode {
        match self {
            Self::NotInRepo => ExitCode::NotInRepo,
            Self::VenvActivation(_) => ExitCode::VenvActivationFailed,
            Self::NoInstallTarget => ExitCode::NoInstallTarget,
            Self::RepoLintUpgradeFailed(_) => ExitCode::RepoLintUpgradeFailed,
            Self::RepoLintInstallFailed(_) => ExitCode::RepoLintInstallFailed,
            Self::PythonToolsFailed(_) => ExitCode::PythonToolsFailed,
            Self::VerificationFailed(_) => ExitCode::VerificationFailed,
            Self::InstallFailed { tool, .. } => {
                // Map tool-specific failures to appropriate exit codes
                match tool.as_str() {
                    "actionlint" => ExitCode::ActionlintFailed,
                    "ripgrep" | "rg" => ExitCode::RipgrepFailed,
                    t if t.starts_with("python")
                        || t.starts_with("black")
                        || t.starts_with("ruff")
                        || t.starts_with("pylint") =>
                    {
                        ExitCode::PythonToolsFailed
                    }
                    t if t.starts_with("shell") || t == "shfmt" => ExitCode::ShellToolchainFailed,
                    t if t.starts_with("pwsh") || t.starts_with("PowerShell") => {
                        ExitCode::PowerShellToolchainFailed
                    }
                    t if t.starts_with("perl") || t == "perlcritic" => {
                        ExitCode::PerlToolchainFailed
                    }
                    _ => ExitCode::VerificationFailed,
                }
            }
            Self::ConfigError(_) => ExitCode::UsageError,
            Self::CommandFailed { .. } => ExitCode::VerificationFailed,
            Self::ToolNotFound(_) => ExitCode::VerificationFailed,
            Self::DetectionFailed(_) => ExitCode::VerificationFailed,
            Self::NoPackageManager(_) => ExitCode::UsageError,
            Self::DependencyResolution(_) | Self::CyclicDependency => ExitCode::UsageError,
            Self::HttpError(_) | Self::ChecksumMismatch { .. } => ExitCode::VerificationFailed,
            Self::IoError(_) | Self::Other(_) => ExitCode::VerificationFailed,
        }
    }
}

/// Result type alias for bootstrap operations
pub type BootstrapResult<T> = Result<T, BootstrapError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_exit_codes() {
        assert_eq!(BootstrapError::NotInRepo.exit_code(), ExitCode::NotInRepo);

        assert_eq!(
            BootstrapError::InstallFailed {
                tool: "ripgrep".to_string(),
                exit_code: 1,
                stderr: String::new(),
            }
            .exit_code(),
            ExitCode::RipgrepFailed
        );

        assert_eq!(
            BootstrapError::InstallFailed {
                tool: "actionlint".to_string(),
                exit_code: 1,
                stderr: String::new(),
            }
            .exit_code(),
            ExitCode::ActionlintFailed
        );
    }

    #[test]
    fn test_error_messages() {
        let err = BootstrapError::NotInRepo;
        assert_eq!(err.to_string(), "Not in git repository");

        let err = BootstrapError::ChecksumMismatch {
            artifact: "test.tar.gz".to_string(),
            expected: "abc123".to_string(),
            actual: "def456".to_string(),
        };
        assert!(err.to_string().contains("test.tar.gz"));
        assert!(err.to_string().contains("abc123"));
    }
}
