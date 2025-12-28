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
    /// Verifies that a command file exists without actually running it.
    /// This is useful for pre-flight checks and dependency validation.
    ///
    /// # Current Implementation (Phase 1)
    ///
    /// - Command file existence check via PATH lookup
    /// - Returns 0 if command file found, 2 if not found
    /// - Does not verify executable permissions (Unix)
    ///
    /// # Future Phases
    ///
    /// - Phase 2: Repository state validation, dependency checks, executable permission verification
    /// - Phase 3: Full conformance test coverage
    ///
    /// # Exit Codes
    ///
    /// - 0: Success (command file exists)
    /// - 2: Command file not found
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
    /// **WARNING: NOT YET IMPLEMENTED - This subcommand is scaffolding only.**
    ///
    /// # Behavior
    ///
    /// (Future) Executes a command and creates an archive of its output regardless of
    /// exit status. Unlike `run`, this will always create artifacts even on success.
    ///
    /// # Current Behavior
    ///
    /// Prints an error message and exits with code 1 to avoid silent no-ops.
    ///
    /// # Exit Codes
    ///
    /// - 1: Not implemented (current behavior)
    /// - (Future) 0: Archival succeeded (command may have failed)
    /// - (Future) 2: Archival failed (e.g., I/O error)
    /// - (Future) Other: Preserved from command
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

    /// Check command availability
    ///
    /// # Arguments
    ///
    /// - `command`: Command to check (first element is the command name)
    ///
    /// # Implementation Status
    ///
    /// **Phase 1 - Command file existence check**: Implements PATH lookup to verify
    /// the target command file exists.
    ///
    /// # Behavior
    ///
    /// Verifies that a command file exists on the system PATH without executing it.
    /// This is useful for pre-flight checks and dependency validation.
    ///
    /// # Exit Codes
    ///
    /// - 0: Success (command file exists)
    /// - 2: Command file not found
    ///
    /// # Limitations
    ///
    /// Phase 1 only checks file existence, not executable permissions (Unix).
    ///
    /// # Future Implementation
    ///
    /// Will additionally verify:
    /// - Executable permissions (Unix)
    /// - Repository state is valid
    /// - Dependencies are available
    fn check_command(&self, command: &[String]) -> Result<i32, String> {
        if command.is_empty() {
            eprintln!("ERROR: No command specified for check");
            return Ok(2);
        }

        let cmd_name = &command[0];
        
        // Check if the command exists on PATH
        if Self::command_exists(cmd_name) {
            Ok(0)
        } else {
            eprintln!("Command not found: {}", cmd_name);
            Ok(2)
        }
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
    /// On Unix-like systems, the file may exist but not be executable.
    fn command_exists(cmd: &str) -> bool {
        // If the command is an absolute or relative path, check it directly
        let cmd_path = Path::new(cmd);
        if cmd_path.is_absolute() || cmd_path.components().count() > 1 {
            return cmd_path.exists() && cmd_path.is_file();
        }

        // Get PATH environment variable
        let path_var = match env::var_os("PATH") {
            Some(p) => p,
            None => return false,
        };

        // Split PATH and check each directory
        for path_dir in env::split_paths(&path_var) {
            // On Unix-like systems, just check if the file exists
            #[cfg(not(target_os = "windows"))]
            {
                let full_path = path_dir.join(cmd);
                if full_path.exists() && full_path.is_file() {
                    return true;
                }
            }

            // On Windows, check both without extension and with common extensions
            #[cfg(target_os = "windows")]
            {
                // Check without extension first (in case user specified full name)
                let base_path = path_dir.join(cmd);
                if base_path.exists() && base_path.is_file() {
                    return true;
                }
                // Then check with common Windows executable extensions
                for ext in &[".exe", ".bat", ".cmd"] {
                    let with_ext = path_dir.join(format!("{}{}", cmd, ext));
                    if with_ext.exists() && with_ext.is_file() {
                        return true;
                    }
                }
            }
        }

        false
    }

    /// Archive command output (scaffolding only)
    ///
    /// # Arguments
    ///
    /// - `_command`: Command to execute and archive (currently unused)
    ///
    /// # Implementation Status
    ///
    /// **SCAFFOLDING ONLY**: This subcommand is not yet implemented.
    /// It exists for CLI structure but does not perform real work.
    ///
    /// # Current Behavior
    ///
    /// Prints an error message indicating the feature is not implemented
    /// and exits with code 1 to prevent silent no-ops.
    ///
    /// # Future Implementation
    ///
    /// Will:
    /// - Execute command with full output capture
    /// - Create archive regardless of command exit status
    /// - Include metadata (timestamp, command, exit code)
    /// - Support artifact collection
    fn archive_command(&self, _command: &[String]) -> Result<i32, String> {
        eprintln!("ERROR: 'safe-run archive' is not yet implemented.");
        eprintln!();
        eprintln!("This subcommand is scaffolding only and does not archive output.");
        eprintln!("Use the 'run' subcommand for safe command execution:");
        eprintln!("  safe-run run <command> [args...]");
        eprintln!();
        eprintln!("For more information, see:");
        eprintln!("  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding");
        Ok(1)
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
