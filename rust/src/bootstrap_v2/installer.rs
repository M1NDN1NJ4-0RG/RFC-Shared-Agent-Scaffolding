//! # Installer Trait and Registry
//!
//! Core installer abstraction and registry pattern.
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.

use crate::bootstrap_v2::context::Context;
use crate::bootstrap_v2::errors::BootstrapResult;
use async_trait::async_trait;
use semver::Version;

/// Installation result
#[derive(Debug)]
pub struct InstallResult {
    /// Version installed
    pub version: Version,

    /// Whether new install (vs already present)
    pub installed_new: bool,

    /// Log messages
    pub log_messages: Vec<String>,
}

/// Verification result
#[derive(Debug)]
pub struct VerifyResult {
    /// Success status
    pub success: bool,

    /// Version if detected
    pub version: Option<Version>,

    /// Issues found
    pub issues: Vec<String>,
}

/// Core installer trait
#[async_trait]
pub trait Installer: Send + Sync {
    /// Unique identifier
    fn id(&self) -> &'static str;

    /// Human-readable name
    fn name(&self) -> &'static str;

    /// Description for help text
    fn description(&self) -> &'static str;

    /// Dependencies (other installer IDs)
    fn dependencies(&self) -> Vec<&'static str> {
        vec![]
    }

    /// Can run concurrently with others
    fn concurrency_safe(&self) -> bool {
        false
    }

    /// Detect if already installed
    async fn detect(&self, ctx: &Context) -> BootstrapResult<Option<Version>>;

    /// Perform installation
    async fn install(&self, ctx: &Context) -> BootstrapResult<InstallResult>;

    /// Verify installation
    async fn verify(&self, ctx: &Context) -> BootstrapResult<VerifyResult>;
}
