//! # Bootstrap V2 - Modular Toolchain Bootstrapper
//!
//! This module implements the next-generation modular bootstrapper with:
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.
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

pub mod activate;
pub mod checkpoint;
pub mod cli;
pub mod config;
pub mod context;
pub mod doctor;
pub mod errors;
pub mod executor;
pub mod exit_codes;
pub mod installer;
pub mod installers;
pub mod lock;
pub mod package_manager;
pub mod plan;
pub mod platform;
pub mod progress;
pub mod retry;
