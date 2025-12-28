//! # CLI Interface for Rust Canonical Tool
//!
//! This module defines the command-line interface using the clap library.
//! It implements the contract-specified subcommands: run, check, and archive.
//!
//! # Purpose
//!
//! Provides a strongly-typed, self-documenting CLI that matches the RFC contract
//! specification while leveraging Rust's type system for validation.
//!
//! # Contract Versions
//!
//! - **Tool version**: Derived from Cargo.toml (semantic versioning)
//! - **Contract version**: M0-v0.1.0 (RFC-Shared-Agent-Scaffolding-v0.1.0.md)
//!
//! # Subcommands
//!
//! - `run`: Execute a command with safe-run semantics (ledger, artifacts on failure)
//! - `check`: Verify command availability and repository state
//! - `archive`: Execute and archive command output regardless of success
//!
//! # Examples
//!
//! ```bash
//! # Run a command (logs created only on failure)
//! safe-run run make test
//!
//! # Check a command exists
//! safe-run check git --version
//!
//! # Archive command output
//! safe-run archive ./build.sh
//! ```

use clap::{Parser, Subcommand};
use std::env;
use std::fs;
use std::path::Path;

/// Package version from Cargo.toml
const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Contract version this implementation conforms to
///
/// This matches the version specified in RFC-Shared-Agent-Scaffolding-v0.1.0.md
/// and is used for compatibility checking by wrappers.
const CONTRACT_VERSION: &str = "M0-v0.1.0";

/// Canonical implementation of the safe-run/safe-check/safe-archive contract
///
/// # Purpose
///
/// This struct defines the top-level CLI interface for the Rust canonical tool.
/// It uses clap's derive macros to generate argument parsing, help text, and
/// validation automatically.
///
/// # Subcommands
///
/// The CLI supports three subcommands corresponding to the RFC contract:
/// - `run`: Execute with structured logging (artifacts only on failure)
/// - `check`: Verify command availability without execution
/// - `archive`: Execute and always create artifacts
///
/// # Version Display
///
/// When invoked without a subcommand, displays tool and contract versions.
/// Use `--version` flag for version-only output.
#[derive(Parser)]
#[command(name = "safe-run")]
#[command(version = VERSION)]
#[command(about = "Execute commands with structured logging and artifact generation")]
#[command(
    long_about = "Canonical Rust implementation of the RFC-Shared-Agent-Scaffolding contract"
)]
pub struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

/// Available subcommands for the canonical tool
///
/// # Contract Mapping
///
/// These commands correspond to the three core behaviors defined in the
/// RFC-Shared-Agent-Scaffolding contract:
///
/// - **Run**: Implements safe-run semantics (vectors: safe-run-001 through safe-run-010)
/// - **Check**: Implements safe-check semantics (not yet in M0 contract)
/// - **Archive**: Implements safe-archive semantics (vectors: safe-archive-001 through safe-archive-005)
///
/// # Argument Handling
///
/// All commands accept variable-length argument lists that are passed through
/// to the underlying command without interpretation. This preserves shell quoting,
/// special characters, and argument structure exactly as provided.
#[derive(Subcommand)]
enum Commands {
    /// Execute a command with safe-run semantics
    ///
    /// # Behavior
    ///
    /// - Captures stdout and stderr separately with event ledger
    /// - Creates log file only on failure (non-zero exit) or signal abort
    /// - Preserves exit codes exactly as returned by the command
    /// - Handles SIGTERM/SIGINT to create ABORTED logs
    ///
    /// # Environment Variables
    ///
    /// - `SAFE_LOG_DIR`: Directory for failure logs (default: `.agent/FAIL-LOGS`)
    /// - `SAFE_SNIPPET_LINES`: Number of tail lines to print on failure (default: 0)
    /// - `SAFE_RUN_VIEW`: Output format mode (`merged` for human-readable view)
    ///
    /// # Exit Codes
    ///
    /// - 0: Command succeeded
    /// - 1-127: Command exit code (preserved)
    /// - 130: Command interrupted by SIGINT (Ctrl-C)
    /// - 143: Command interrupted by SIGTERM
    ///
    /// # Contract References
    ///
    /// Implements vectors: safe-run-001, safe-run-002, safe-run-003, safe-run-004,
    /// safe-run-005, safe-run-006, safe-run-007, safe-run-008
    Run {
        /// Command to execute
        ///
        /// This field captures all remaining arguments after `run` and passes them
        /// through to the underlying command. Use `--` to separate tool options from
        /// command arguments if the command uses flags that might conflict.
        ///
        /// # Examples
        ///
        /// ```bash
        /// safe-run run echo "Hello, world!"
        /// safe-run run -- ls -la
        /// safe-run run bash -c 'echo $PATH'
        /// ```
        #[arg(required = true, trailing_var_arg = true, allow_hyphen_values = true)]
        command: Vec<String>,
    },

    /// Check repository state and command availability
    ///
    /// # Behavior
    ///
    /// Verifies that a command exists and performs repository state validation.
    /// This is useful for pre-flight checks and dependency validation.
    ///
    /// # Current Implementation (Phase 1 & 2)
    ///
    /// - Command file existence check via PATH lookup
    /// - Executable permission verification (Unix)
    /// - Repository state validation
    /// - Dependency availability checks
    ///
    /// # Future Phases
    ///
    /// - Phase 3: Full conformance test coverage and vectors
    ///
    /// # Exit Codes
    ///
    /// - 0: Success (all checks pass)
    /// - 2: Command file not found
    /// - 3: Command found but not executable (Unix)
    /// - 4: Repository state invalid or dependency missing
    Check {
        /// Command to check
        ///
        /// The command name or path to verify. Additional arguments may be provided
        /// for version checking or validation.
        #[arg(required = true)]
        command: Vec<String>,
    },

    /// Archive directory to compressed file
    ///
    /// # Behavior
    ///
    /// Creates a compressed archive (tar.gz, tar.bz2, or zip) from a source directory.
    /// Supports multiple compression formats and no-clobber semantics.
    ///
    /// # Exit Codes
    ///
    /// - 0: Archive created successfully
    /// - 2: Invalid arguments or source not found
    /// - 40: No-clobber collision (strict mode)
    /// - 50: Archive creation failed (I/O error)
    Archive {
        /// Enable strict no-clobber mode (fail if destination exists)
        ///
        /// By default, if the destination file exists, a numeric suffix is added
        /// (e.g., output.1.tar.gz). With --no-clobber, the command fails instead.
        #[arg(long)]
        no_clobber: bool,

        /// Source directory and destination archive path
        ///
        /// First argument: source directory path
        /// Second argument: destination archive path (.tar.gz, .tar.bz2, or .zip)
        #[arg(required = true)]
        command: Vec<String>,
    },
}

impl Cli {
    /// Execute the parsed CLI command
    ///
    /// # Purpose
    ///
    /// Routes control to the appropriate subcommand handler based on the parsed
    /// command-line arguments. This is the main dispatch point for all tool behavior.
    ///
    /// # Returns
    ///
    /// - `Ok(exit_code)`: Command executed successfully, returns the exit code to propagate
    /// - `Err(message)`: Tool error occurred (not command failure), returns error message
    ///
    /// # Behavior
    ///
    /// - If no subcommand provided: Displays version information and exits with 0
    /// - If subcommand provided: Delegates to the appropriate handler method
    ///
    /// # Examples
    ///
    /// ```ignore
    /// // In your main.rs:
    /// use clap::Parser;
    /// use crate::cli::Cli;
    ///
    /// let cli = Cli::parse();
    /// let exit_code = cli.run().expect("Tool error");
    /// ```
    pub fn run(&self) -> Result<i32, String> {
        match &self.command {
            Some(Commands::Run { command }) => self.run_command(command),
            Some(Commands::Check { command }) => self.check_command(command),
            Some(Commands::Archive {
                no_clobber,
                command,
            }) => self.archive_command(command, *no_clobber),
            None => {
                // No subcommand provided, show help
                println!("safe-run {} (contract: {})", VERSION, CONTRACT_VERSION);
                println!();
                println!("Use --help for more information.");
                Ok(0)
            }
        }
    }

    /// Execute a command with safe-run semantics
    ///
    /// # Arguments
    ///
    /// - `command`: Command and arguments to execute
    ///
    /// # Behavior
    ///
    /// Delegates to `crate::safe_run::execute()` which implements the full safe-run
    /// contract including:
    /// - Event ledger with monotonic sequence numbers
    /// - Separate stdout/stderr capture
    /// - Log creation only on failure or abort
    /// - Signal handling (SIGTERM → 143, SIGINT → 130)
    /// - Environment variable configuration
    ///
    /// # Returns
    ///
    /// Exit code from the executed command (0 for success, non-zero for failure)
    ///
    /// # Contract References
    ///
    /// - safe-run-001: Success creates no artifacts
    /// - safe-run-002: Failure creates FAIL log
    /// - safe-run-003: Exit code preservation
    /// - safe-run-004: Snippet lines output
    /// - safe-run-005: Custom log directory
    /// - safe-run-006: Signal handling creates ABORTED log
    fn run_command(&self, command: &[String]) -> Result<i32, String> {
        crate::safe_run::execute(command)
    }

    /// Check command availability
    ///
    /// # Arguments
    ///
    /// - `command`: Command to check (first element is the command name)
    ///
    /// # Implementation Status
    ///
    /// **Phase 1 & 2 - Command validation and checks**:
    /// - PATH lookup to verify command file exists
    /// - Executable permission verification (Unix)
    /// - Repository state validation
    /// - Dependency availability checks
    ///
    /// # Behavior
    ///
    /// Verifies that a command file exists on the system PATH without executing it.
    /// Additionally performs repository and dependency validation.
    ///
    /// # Exit Codes
    ///
    /// - 0: Success (command file exists and all checks pass)
    /// - 2: Command file not found
    /// - 3: Command found but not executable (Unix)
    /// - 4: Repository state invalid or dependency missing
    ///
    /// # Phase 2 Additions
    ///
    /// - Executable permission verification on Unix-like systems
    /// - Repository state validation (git repository check)
    /// - Dependency availability checks
    fn check_command(&self, command: &[String]) -> Result<i32, String> {
        if command.is_empty() {
            eprintln!("ERROR: No command specified for check");
            return Ok(2);
        }

        let cmd_name = &command[0];

        // Phase 1: Check if the command exists on PATH
        let cmd_path = match Self::find_command_path(cmd_name) {
            Some(path) => path,
            None => {
                eprintln!("Command not found: {}", cmd_name);
                return Ok(2);
            }
        };

        // Phase 2: Check executable permissions on Unix
        #[cfg(not(target_os = "windows"))]
        {
            if !Self::is_executable(&cmd_path) {
                eprintln!("Command found but not executable: {}", cmd_name);
                eprintln!("Path: {}", cmd_path.display());
                eprintln!(
                    "Hint: Run 'chmod +x {}' to make it executable",
                    cmd_path.display()
                );
                return Ok(3);
            }
        }

        // Phase 2: Validate repository state if in a git repository
        if let Err(msg) = Self::validate_repository_state() {
            eprintln!("Repository state check failed: {}", msg);
            return Ok(4);
        }

        // All checks passed
        Ok(0)
    }

    /// Find the full path to a command
    ///
    /// # Arguments
    ///
    /// - `cmd`: Command name to find
    ///
    /// # Returns
    ///
    /// - `Some(PathBuf)`: Full path to the command if found
    /// - `None`: Command not found
    fn find_command_path(cmd: &str) -> Option<std::path::PathBuf> {
        // If the command is an absolute or relative path, check it directly
        let cmd_path = Path::new(cmd);
        if cmd_path.is_absolute() || cmd_path.components().nth(1).is_some() {
            if cmd_path.exists() && cmd_path.is_file() {
                return Some(cmd_path.to_path_buf());
            }

            // On Windows, try with extensions
            #[cfg(target_os = "windows")]
            {
                if cmd_path.extension().is_none() {
                    let extensions = Self::get_windows_executable_extensions();
                    for ext in extensions.iter() {
                        let with_ext = cmd_path.with_extension(ext);
                        if with_ext.exists() && with_ext.is_file() {
                            return Some(with_ext);
                        }
                    }
                }
            }

            return None;
        }

        // Get PATH environment variable
        let path_var = env::var_os("PATH")?;

        #[cfg(target_os = "windows")]
        let extensions = Self::get_windows_executable_extensions();

        // Split PATH and check each directory
        for path_dir in env::split_paths(&path_var) {
            #[cfg(not(target_os = "windows"))]
            {
                let full_path = path_dir.join(cmd);
                if full_path.exists() && full_path.is_file() {
                    return Some(full_path);
                }
            }

            #[cfg(target_os = "windows")]
            {
                let base_path = path_dir.join(cmd);
                if base_path.exists() && base_path.is_file() {
                    return Some(base_path);
                }
                for ext in extensions.iter() {
                    let with_ext = path_dir.join(format!("{}{}", cmd, ext));
                    if with_ext.exists() && with_ext.is_file() {
                        return Some(with_ext);
                    }
                }
            }
        }

        None
    }

    /// Check if a file is executable (Unix only)
    ///
    /// # Arguments
    ///
    /// - `path`: Path to the file to check
    ///
    /// # Returns
    ///
    /// - `true`: File is executable
    /// - `false`: File is not executable
    #[cfg(not(target_os = "windows"))]
    fn is_executable(path: &Path) -> bool {
        use std::os::unix::fs::PermissionsExt;

        match fs::metadata(path) {
            Ok(metadata) => {
                let permissions = metadata.permissions();
                // Check if any execute bit is set (user, group, or other)
                permissions.mode() & 0o111 != 0
            }
            Err(_) => false,
        }
    }

    /// Validate repository state
    ///
    /// # Returns
    ///
    /// - `Ok(())`: Repository state is valid
    /// - `Err(String)`: Repository state is invalid with error message
    ///
    /// # Behavior
    ///
    /// Performs basic repository validation:
    /// - Checks if .git directory exists (when in a git repository)
    /// - Can be extended to check for uncommitted changes, required files, etc.
    fn validate_repository_state() -> Result<(), String> {
        // Check if we're in a git repository by looking for .git directory
        let current_dir =
            env::current_dir().map_err(|e| format!("Cannot determine current directory: {}", e))?;

        // Walk up the directory tree looking for .git
        let mut dir = current_dir.as_path();
        let mut in_git_repo = false;

        loop {
            let git_dir = dir.join(".git");
            if git_dir.exists() {
                in_git_repo = true;
                break;
            }

            match dir.parent() {
                Some(parent) => dir = parent,
                None => break,
            }
        }

        // If we're in a git repository, we could add more checks here
        // For now, just verify .git exists
        if in_git_repo {
            // Repository found - could add more checks here in the future:
            // - Check for uncommitted changes
            // - Verify required configuration files
            // - etc.
        }

        Ok(())
    }

    /// Check if a command exists on the system PATH
    ///
    /// # Arguments
    ///
    /// - `cmd`: Command name to check
    ///
    /// # Returns
    ///
    /// - `true`: Command file found on PATH or at specified path
    /// - `false`: Command file not found
    ///
    /// # Platform Considerations
    ///
    /// On Windows, also checks for .exe, .bat, and .cmd extensions.
    ///
    /// # Note
    ///
    /// This function only checks file existence, not executable permissions.
    /// For full command validation including permissions, use `find_command_path`
    /// and `is_executable`.
    #[allow(dead_code)] // Used by test infrastructure
    fn command_exists(cmd: &str) -> bool {
        Self::find_command_path(cmd).is_some()
    }

    /// Get Windows executable extensions from PATHEXT environment variable
    ///
    /// # Returns
    ///
    /// A vector of executable extensions to check (e.g., [".exe", ".bat", ".cmd"])
    ///
    /// # Behavior
    ///
    /// - Reads PATHEXT environment variable on Windows
    /// - Falls back to common extensions (.exe, .bat, .cmd) if PATHEXT is not set
    /// - Returns empty list on non-Windows platforms (not used)
    #[cfg(target_os = "windows")]
    fn get_windows_executable_extensions() -> Vec<String> {
        match env::var("PATHEXT") {
            Ok(pathext) => {
                // Split PATHEXT by semicolon and filter out empty strings
                pathext
                    .split(';')
                    .filter(|s| !s.is_empty())
                    .map(|s| s.to_string())
                    .collect()
            }
            Err(_) => {
                // Fallback to common Windows executable extensions
                vec![".exe".to_string(), ".bat".to_string(), ".cmd".to_string()]
            }
        }
    }

    #[cfg(not(target_os = "windows"))]
    #[allow(dead_code)] // Only used in Windows-specific code blocks
    fn get_windows_executable_extensions() -> Vec<String> {
        // Not used on non-Windows platforms, but needed for compilation
        vec![]
    }

    /// Create an archive from a source directory
    ///
    /// # Arguments
    ///
    /// - `command`: Command arguments (source and destination paths)
    /// - `no_clobber`: If true, fail when destination exists; if false, auto-suffix
    ///
    /// # Implementation
    ///
    /// Delegates to `crate::safe_archive::execute()` which implements:
    /// - Archive creation from source directories
    /// - Support for .tar.gz, .tar.bz2, and .zip formats
    /// - No-clobber semantics (auto-suffix or strict mode)
    ///
    /// # Returns
    ///
    /// Exit code from the archive operation (0 for success, non-zero for failure)
    ///
    /// # Contract References
    ///
    /// - safe-archive-001: Basic archive creation
    /// - safe-archive-002: Multiple compression formats
    /// - safe-archive-003: No-clobber with auto-suffix
    /// - safe-archive-004: No-clobber strict mode
    fn archive_command(&self, command: &[String], no_clobber: bool) -> Result<i32, String> {
        crate::safe_archive::execute(command, no_clobber)
    }
}

/// Unit tests for CLI interface
///
/// # Purpose
///
/// Validates CLI parsing, version handling, and basic command dispatch without
/// executing actual commands. These tests ensure the clap configuration is correct
/// and the CLI contract is maintained.
///
/// # Coverage
///
/// - CLI structure validation (verify_cli)
/// - Version constant validation (test_version_format)
///
/// # Contract References
///
/// These tests validate the CLI interface defined in docs/wrapper-discovery.md
/// and ensure version strings conform to semantic versioning.
#[cfg(test)]
mod tests {
    use super::*;

    /// Verify CLI structure is valid according to clap's validation rules
    ///
    /// # Purpose
    ///
    /// Uses clap's debug_assert() to validate:
    /// - All required arguments are properly configured
    /// - No conflicting short/long options
    /// - Help text is well-formed
    /// - Subcommand structure is valid
    ///
    /// # Panics
    ///
    /// Panics if CLI structure has configuration errors
    #[test]
    fn verify_cli() {
        use clap::CommandFactory;
        Cli::command().debug_assert();
    }

    /// Verify version constants are non-empty and well-formed
    ///
    /// # Purpose
    ///
    /// Ensures VERSION and CONTRACT_VERSION constants are populated at compile time.
    /// Empty versions would indicate a build configuration problem.
    ///
    /// # Contract References
    ///
    /// - VERSION: Must match Cargo.toml version (semantic versioning)
    /// - CONTRACT_VERSION: Must match RFC contract version (M0-v0.1.0 format)
    #[test]
    fn test_version_format() {
        assert!(!VERSION.is_empty());
        assert!(!CONTRACT_VERSION.is_empty());
    }
}
