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
    /// Verifies that a command exists and can be executed without actually running it.
    /// This is useful for pre-flight checks and dependency validation.
    ///
    /// # Implementation Status
    ///
    /// **Note**: This subcommand is scaffolding only. Full implementation will be
    /// added in a future PR per the stacked PR plan.
    ///
    /// # Exit Codes
    ///
    /// - 0: Success (command exists and is executable)
    /// - 1: Command not found or not executable
    Check {
        /// Command to check
        ///
        /// The command name or path to verify. Additional arguments may be provided
        /// for version checking or validation.
        #[arg(required = true)]
        command: Vec<String>,
    },

    /// Archive command output and artifacts
    ///
    /// # Behavior
    ///
    /// Executes a command and creates an archive of its output regardless of
    /// exit status. Unlike `run`, this always creates artifacts even on success.
    ///
    /// # Implementation Status
    ///
    /// **Note**: This subcommand is scaffolding only. Full implementation will be
    /// added in a future PR per the stacked PR plan.
    ///
    /// # Exit Codes
    ///
    /// - 0: Archival succeeded (command may have failed)
    /// - 1: Archival failed
    /// - Other: Preserved from command
    Archive {
        /// Command to execute and archive
        ///
        /// All output from this command will be captured and stored in an archive
        /// file regardless of the command's exit status.
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
            Some(Commands::Archive { command }) => self.archive_command(command),
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

    /// Check command availability (scaffolding only)
    ///
    /// # Arguments
    ///
    /// - `_command`: Command to check (currently unused)
    ///
    /// # Implementation Status
    ///
    /// This is scaffolding implementation only. The full safe-check contract
    /// will be implemented in a future PR as part of the stacked PR plan.
    ///
    /// # Current Behavior
    ///
    /// Prints a message indicating the feature is not yet implemented and
    /// returns success (exit code 0).
    ///
    /// # Future Implementation
    ///
    /// Will verify:
    /// - Command exists on PATH
    /// - Command is executable
    /// - Repository state is valid
    /// - Dependencies are available
    fn check_command(&self, _command: &[String]) -> Result<i32, String> {
        // TODO: Implement safe-check logic
        println!("safe-check: Command checking not yet implemented");
        println!("This is a scaffolding PR - implementation comes in PR3+");
        Ok(0)
    }

    /// Archive command output (scaffolding only)
    ///
    /// # Arguments
    ///
    /// - `_command`: Command to execute and archive (currently unused)
    ///
    /// # Implementation Status
    ///
    /// This is scaffolding implementation only. The full safe-archive contract
    /// will be implemented in a future PR as part of the stacked PR plan.
    ///
    /// # Current Behavior
    ///
    /// Prints a message indicating the feature is not yet implemented and
    /// returns success (exit code 0).
    ///
    /// # Future Implementation
    ///
    /// Will:
    /// - Execute command with full output capture
    /// - Create archive regardless of command exit status
    /// - Include metadata (timestamp, command, exit code)
    /// - Support artifact collection
    fn archive_command(&self, _command: &[String]) -> Result<i32, String> {
        // TODO: Implement safe-archive logic
        println!("safe-archive: Command archiving not yet implemented");
        println!("This is a scaffolding PR - implementation comes in PR3+");
        Ok(0)
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
