// Bootstrap V2 foundational code - comprehensive docs pending (Issue #235 Phase 1)
//! # Retry Strategy
//!
//! Retry policies with exponential backoff and classification.
//! # noqa: SECTION
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.

use std::time::Duration;

/// Retry classification
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RetryClass {
    /// Transient error (safe to retry)
    Transient,

    /// Permanent error (do not retry)
    Permanent,

    /// Security error (checksum/signature mismatch)
    Security,

    /// Unsafe to retry (non-idempotent)
    Unsafe,
}

/// Retry policy
#[derive(Debug, Clone)]
pub struct RetryPolicy {
    /// Maximum retry attempts
    pub max_attempts: u32,

    /// Initial delay
    pub initial_delay: Duration,

    /// Maximum delay
    pub max_delay: Duration,

    /// Maximum total time
    pub max_total_time: Duration,

    /// Add jitter
    pub jitter: bool,
}

impl RetryPolicy {
    /// Default policy for network operations
    pub fn network_default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_secs(1),
            max_delay: Duration::from_secs(30),
            max_total_time: Duration::from_secs(60),
            jitter: true,
        }
    }
}
