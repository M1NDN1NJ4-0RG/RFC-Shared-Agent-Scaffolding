//! # Bootstrap Repo CLI Library
//!
//! Library modules for the bootstrap-repo-cli tool.
//! These modules are exposed for integration testing.
//!
//! # Purpose
//!
//! Provides modular toolchain bootstrapping with parallel execution,
//! rich progress UI, and structured error handling.
//!
//! # Examples
//!
//! See integration tests in `tests/` for usage examples.

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
