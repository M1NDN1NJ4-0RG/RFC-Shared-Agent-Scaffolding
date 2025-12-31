//! # Bootstrap Repo-CLI Binary Entry Point
//!
//! # Purpose
//!
//! This binary implements the bootstrap-repo-cli functionality for setting up
//! the repo-lint toolchain in a local Python virtual environment.
//!
//! # Examples
//!
//! Run the bootstrap to set up repo-lint:
//!
//! ```bash
//! bootstrap-repo-cli
//! ```
//!
//! The binary can be run from anywhere inside the repository and will:
//! 1. Find the repository root
//! 2. Create a Python virtual environment
//! 3. Install repo-lint and dependencies
//! 4. Install system tools (shellcheck, shfmt, ripgrep, PowerShell, Perl modules)
//! 5. Verify installations

mod bootstrap;

use std::process::ExitCode;

fn main() -> ExitCode {
    bootstrap::run()
}
