//! # Exit Code Constants
//!
//! Defines all exit codes used by the bootstrap CLI.
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! These codes match the existing bash script contract and must remain stable.
//!
//! # Exit Code Ranges
//!
//! - 0: Success
//! - 1: Usage error
//! - 10-21: Specific failure modes
//!
//! # Examples
//!
//! ```
//! use bootstrap_v2::exit_codes::ExitCode;
//!
//! fn main() -> std::process::ExitCode {
//!     std::process::ExitCode::from(ExitCode::Success.as_u8())
//! }
//! ```

/// Bootstrap exit codes matching the bash script contract
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum ExitCode {
    /// Success (0)
    Success = 0,

    /// Usage error - invalid arguments (1)
    UsageError = 1,

    /// Not in a git repository (10)
    NotInRepo = 10,

    /// Virtual environment activation failed (11)
    VenvActivationFailed = 11,

    /// No install target found (12)
    NoInstallTarget = 12,

    /// repo-lint upgrade failed (13)
    RepoLintUpgradeFailed = 13,

    /// repo-lint install failed (14)
    RepoLintInstallFailed = 14,

    /// Python tools failed (15)
    PythonToolsFailed = 15,

    /// Shell toolchain failed (16)
    ShellToolchainFailed = 16,

    /// PowerShell toolchain failed (17)
    PowerShellToolchainFailed = 17,

    /// Perl toolchain failed (18)
    PerlToolchainFailed = 18,

    /// Verification failed (19)
    VerificationFailed = 19,

    /// actionlint installation failed (20)
    ActionlintFailed = 20,

    /// ripgrep installation failed (21)
    /// REQUIRED: ripgrep is mandatory and must not fail
    RipgrepFailed = 21,
}

impl ExitCode {
    /// Convert to i32 for compatibility
    pub const fn as_i32(self) -> i32 {
        self as i32
    }

    /// Convert to u8 for std::process::ExitCode
    pub const fn as_u8(self) -> u8 {
        self as u8
    }

    /// Get human-readable description
    pub const fn description(self) -> &'static str {
        match self {
            Self::Success => "Success",
            Self::UsageError => "Usage error",
            Self::NotInRepo => "Not in git repository",
            Self::VenvActivationFailed => "Virtual environment activation failed",
            Self::NoInstallTarget => "No install target found",
            Self::RepoLintUpgradeFailed => "repo-lint upgrade failed",
            Self::RepoLintInstallFailed => "repo-lint install failed",
            Self::PythonToolsFailed => "Python tools installation failed",
            Self::ShellToolchainFailed => "Shell toolchain installation failed",
            Self::PowerShellToolchainFailed => "PowerShell toolchain installation failed",
            Self::PerlToolchainFailed => "Perl toolchain installation failed",
            Self::VerificationFailed => "Verification failed",
            Self::ActionlintFailed => "actionlint installation failed",
            Self::RipgrepFailed => "ripgrep installation failed (REQUIRED)",
        }
    }
}

impl From<ExitCode> for std::process::ExitCode {
    fn from(code: ExitCode) -> Self {
        std::process::ExitCode::from(code.as_u8())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exit_code_values() {
        assert_eq!(ExitCode::Success.as_i32(), 0);
        assert_eq!(ExitCode::UsageError.as_i32(), 1);
        assert_eq!(ExitCode::NotInRepo.as_i32(), 10);
        assert_eq!(ExitCode::RipgrepFailed.as_i32(), 21);
    }

    #[test]
    fn test_exit_code_descriptions() {
        assert_eq!(ExitCode::Success.description(), "Success");
        assert!(ExitCode::RipgrepFailed.description().contains("REQUIRED"));
    }
}
