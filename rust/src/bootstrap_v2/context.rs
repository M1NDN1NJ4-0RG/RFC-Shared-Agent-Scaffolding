//! # Execution Context
//!
//! Shared context object passed to all installer operations.
//! Contains configuration, environment info, and shared state.
//!
//! # Design
//!
//! The Context is immutable once created and provides:
//! - Repository root path
//! - Virtual environment path
//! - OS and package manager detection
//! - Dry-run mode flag
//! - Verbosity settings
//! - Progress reporter
//! - Configuration
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::context::{Context, OsType, PackageManager};
//! use std::path::PathBuf;
//!
//! let ctx = Context::new(
//!     PathBuf::from("/repo"),
//!     OsType::Linux,
//!     PackageManager::Apt,
//!     false, // not dry-run
//! );
//! ```

use crate::bootstrap_v2::config::Config;
use crate::bootstrap_v2::progress::ProgressReporter;
use std::path::PathBuf;
use std::sync::Arc;

/// Operating system type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OsType {
    /// macOS (Darwin)
    MacOS,

    /// Linux (any distribution)
    Linux,

    /// Windows (not supported in v1)
    #[allow(dead_code)]
    Windows,
}

impl OsType {
    /// Detect current OS
    pub fn detect() -> Self {
        #[cfg(target_os = "macos")]
        return Self::MacOS;

        #[cfg(target_os = "linux")]
        return Self::Linux;

        #[cfg(target_os = "windows")]
        return Self::Windows;

        #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
        compile_error!("Unsupported operating system");
    }
}

/// Package manager type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PackageManager {
    /// Homebrew (macOS, Linux)
    Homebrew,

    /// apt-get (Debian, Ubuntu)
    Apt,

    /// snap (Ubuntu, others)
    Snap,

    /// No package manager available
    None,
}

impl PackageManager {
    /// Detect available package manager
    pub fn detect(os: OsType) -> Self {
        match os {
            OsType::MacOS => {
                if Self::command_exists("brew") {
                    Self::Homebrew
                } else {
                    Self::None
                }
            }
            OsType::Linux => {
                if Self::command_exists("apt-get") {
                    Self::Apt
                } else if Self::command_exists("snap") {
                    Self::Snap
                } else if Self::command_exists("brew") {
                    Self::Homebrew
                } else {
                    Self::None
                }
            }
            OsType::Windows => Self::None,
        }
    }

    fn command_exists(cmd: &str) -> bool {
        std::process::Command::new(cmd)
            .arg("--version")
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .is_ok()
    }
}

/// Verbosity level
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Verbosity {
    /// Quiet (errors only)
    Quiet = 0,

    /// Normal (info and above)
    Normal = 1,

    /// Verbose (debug and above)
    Verbose = 2,

    /// Trace (all messages)
    Trace = 3,
}

impl Verbosity {
    /// Create from count (0 = normal, 1 = verbose, 2+ = trace)
    pub fn from_count(count: u8) -> Self {
        match count {
            0 => Self::Normal,
            1 => Self::Verbose,
            _ => Self::Trace,
        }
    }
}

/// Shared execution context
#[derive(Clone)]
pub struct Context {
    /// Repository root directory
    pub repo_root: PathBuf,

    /// Virtual environment directory
    pub venv_path: PathBuf,

    /// Operating system type
    pub os: OsType,

    /// Package manager
    pub package_manager: PackageManager,

    /// Dry-run mode (no actual changes)
    pub dry_run: bool,

    /// Verbosity level
    pub verbosity: Verbosity,

    /// Progress reporter
    pub progress: Arc<ProgressReporter>,

    /// Configuration
    pub config: Arc<Config>,

    /// CI mode
    pub ci_mode: bool,

    /// Number of parallel jobs
    pub jobs: usize,

    /// Offline mode (no network)
    pub offline: bool,

    /// Allow downgrades
    pub allow_downgrade: bool,
}

impl Context {
    /// Create new context with defaults
    pub fn new(
        repo_root: PathBuf,
        os: OsType,
        package_manager: PackageManager,
        dry_run: bool,
    ) -> Self {
        let venv_path = repo_root.join(".venv");
        let progress = Arc::new(ProgressReporter::new_auto());
        let config = Arc::new(Config::default());

        Self {
            repo_root,
            venv_path,
            os,
            package_manager,
            dry_run,
            verbosity: Verbosity::Normal,
            progress,
            config,
            ci_mode: false,
            jobs: Self::default_jobs(false),
            offline: false,
            allow_downgrade: false,
        }
    }

    /// Create context with full configuration
    #[allow(clippy::too_many_arguments)]
    pub fn with_config(
        repo_root: PathBuf,
        os: OsType,
        package_manager: PackageManager,
        dry_run: bool,
        verbosity: Verbosity,
        progress: Arc<ProgressReporter>,
        config: Arc<Config>,
        ci_mode: bool,
        jobs: Option<usize>,
        offline: bool,
        allow_downgrade: bool,
    ) -> Self {
        let venv_path = repo_root.join(".venv");
        let jobs = jobs.unwrap_or_else(|| Self::default_jobs(ci_mode));

        Self {
            repo_root,
            venv_path,
            os,
            package_manager,
            dry_run,
            verbosity,
            progress,
            config,
            ci_mode,
            jobs,
            offline,
            allow_downgrade,
        }
    }

    /// Get default number of jobs based on CI mode
    fn default_jobs(ci_mode: bool) -> usize {
        if ci_mode {
            2
        } else {
            std::cmp::min(4, num_cpus::get())
        }
    }

    /// Check if running in CI mode
    pub fn is_ci(&self) -> bool {
        self.ci_mode
    }

    /// Get venv python path
    pub fn venv_python(&self) -> PathBuf {
        self.venv_path.join("bin").join("python3")
    }

    /// Get venv pip path
    pub fn venv_pip(&self) -> PathBuf {
        self.venv_path.join("bin").join("pip")
    }

    /// Get repo-lint binary path
    pub fn repo_lint_bin(&self) -> PathBuf {
        self.venv_path.join("bin").join("repo-lint")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_os_detection() {
        let os = OsType::detect();
        // Should not panic and return a valid OS
        match os {
            OsType::MacOS | OsType::Linux | OsType::Windows => {}
        }
    }

    #[test]
    fn test_verbosity_from_count() {
        assert_eq!(Verbosity::from_count(0), Verbosity::Normal);
        assert_eq!(Verbosity::from_count(1), Verbosity::Verbose);
        assert_eq!(Verbosity::from_count(2), Verbosity::Trace);
        assert_eq!(Verbosity::from_count(10), Verbosity::Trace);
    }

    #[test]
    fn test_context_paths() {
        let ctx = Context::new(
            PathBuf::from("/test/repo"),
            OsType::Linux,
            PackageManager::Apt,
            false,
        );

        assert_eq!(ctx.repo_root, PathBuf::from("/test/repo"));
        assert_eq!(ctx.venv_path, PathBuf::from("/test/repo/.venv"));
        assert_eq!(
            ctx.venv_python(),
            PathBuf::from("/test/repo/.venv/bin/python3")
        );
    }

    #[test]
    fn test_default_jobs() {
        assert_eq!(Context::default_jobs(true), 2); // CI mode
        let interactive = Context::default_jobs(false);
        assert!(interactive >= 2);
        assert!(interactive <= 4);
    }
}
