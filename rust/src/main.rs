//! # Rust Canonical Tool for RFC Shared Agent Scaffolding
//!
//! This is the canonical implementation of the RFC-Shared-Agent-Scaffolding contract,
//! providing structured logging and artifact generation for command execution.
//!
//! # Purpose
//!
//! This tool serves as the single source of truth for the safe-run/safe-check/safe-archive
//! contract behaviors. Language-specific wrappers (Bash, Perl, Python3, PowerShell) are
//! thin invokers that discover and execute this Rust binary rather than reimplementing
//! the contract logic.
//!
//! # Architecture
//!
//! - **Entry point**: This module (`main.rs`) initializes the CLI and delegates to subcommands
//! - **CLI interface**: The `cli` module defines the command-line interface using clap
//! - **Implementation**: The `safe_run` module implements the core contract behaviors
//!
//! # Exit Behavior
//!
//! - Exit code 0: Successfully parsed arguments and executed command (command may have failed)
//! - Exit code 1: Error during tool execution (not command failure)
//! - Exit code 2: Invalid usage or missing required arguments
//! - Exit codes 3-255: Preserved from executed command
//!
//! # Contract References
//!
//! This implementation conforms to:
//! - RFC-Shared-Agent-Scaffolding-v0.1.0.md (M0 contract)
//! - Conformance vectors in `conformance/vectors.json`
//! - Wrapper discovery rules in `docs/wrapper-discovery.md`
//!
//! # Examples
//!
//! ```bash
//! # Execute a command with safe-run semantics
//! safe-run run echo "Hello, world!"
//!
//! # Check command availability
//! safe-run check git --version
//!
//! # Archive command output
//! safe-run archive make test
//! ```

mod cli;
mod safe_archive;
mod safe_run;

use clap::Parser;
use std::process;

/// Main entry point for the Rust canonical tool.
///
/// # Behavior
///
/// 1. Parses command-line arguments using clap
/// 2. Delegates execution to the appropriate subcommand handler in the `cli` module
/// 3. Exits with the appropriate status code based on command execution result
///
/// # Exit Codes
///
/// - 0: Success (command completed, even if command itself failed)
/// - 1: Tool error (invalid arguments, internal error)
/// - Other: Preserved from executed command
///
/// # Error Handling
///
/// Errors from subcommand execution are printed to stderr with "Error: " prefix
/// before exiting with code 1. This distinguishes tool errors from command failures.
fn main() {
    let args = cli::Cli::parse();

    match args.run() {
        Ok(exit_code) => process::exit(exit_code),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}
