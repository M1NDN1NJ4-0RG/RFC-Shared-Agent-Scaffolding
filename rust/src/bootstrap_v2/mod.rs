//! # Bootstrap V2 - Modular Toolchain Bootstrapper
//!
//! This module implements the next-generation modular bootstrapper with:
//! - Parallel execution (where safe)
//! - Rich progress UI
//! - Structured logging
//! - Better error handling
//! - Installer registry pattern
//!
//! # Architecture
//!
//! The bootstrapper is organized into several key modules:
//! - `exit_codes`: Exit code constants and conversions
//! - `errors`: Error type hierarchy
//! - `context`: Shared execution context
//! - `installer`: Installer trait and registry
//! - `config`: Configuration file parsing
//! - `cli`: Command-line interface

pub mod cli;
pub mod config;
pub mod context;
pub mod errors;
pub mod exit_codes;
pub mod installer;
pub mod lock;
pub mod plan;
pub mod progress;
pub mod retry;
