//! # CLI Interface
//!
//! Command-line interface using clap for the bootstrap tool.
//!
//! # Subcommands
//!
//! - `install`: Detect, install, and verify tools
//! - `doctor`: Diagnostic checks
//! - `verify`: Verify-only mode (no installs)

use clap::{Parser, Subcommand};

/// Bootstrap V2 - Modular Toolchain Bootstrapper
#[derive(Parser, Debug)]
#[command(name = "bootstrap")]
#[command(about = "Modular toolchain bootstrapper", long_about = None)]
#[command(version)]
pub struct Cli {
    /// Subcommand to execute
    #[command(subcommand)]
    pub command: Commands,

    /// Enable dry-run mode (no actual changes)
    #[arg(long, global = true)]
    pub dry_run: bool,

    /// Enable CI mode
    #[arg(long, global = true)]
    pub ci: bool,

    /// Output as JSON
    #[arg(long, global = true)]
    pub json: bool,

    /// Verbose output (can be repeated)
    #[arg(short, long, global = true, action = clap::ArgAction::Count)]
    pub verbose: u8,

    /// Number of parallel jobs (default: CI=2, interactive=min(4,num_cpus))
    #[arg(long, global = true, env = "BOOTSTRAP_JOBS")]
    pub jobs: Option<usize>,

    /// Offline mode (no network requests)
    #[arg(long, global = true)]
    pub offline: bool,

    /// Allow downgrades (forbidden in CI by default)
    #[arg(long, global = true)]
    pub allow_downgrade: bool,
}

/// Subcommands
#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Install tools (detect → install → verify)
    Install {
        /// Profile to install (dev, ci, full)
        #[arg(long, default_value = "dev")]
        profile: String,
    },

    /// Run diagnostics
    Doctor {
        /// Treat warnings as failures
        #[arg(long)]
        strict: bool,
    },

    /// Verify installation only (no installs)
    Verify,
}
