//! # Safe-Run and Bootstrap Library
//!
//! This library provides:
//! # noqa: SECTION
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.
//! - safe-run: Command execution with timeouts and resource limits
//! - bootstrap: Toolchain bootstrapping utilities

pub mod bootstrap;
pub mod bootstrap_v2;
pub mod cli;
pub mod safe_archive;
pub mod safe_run;
