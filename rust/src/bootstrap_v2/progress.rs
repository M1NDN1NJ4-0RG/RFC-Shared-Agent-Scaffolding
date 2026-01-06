// Bootstrap V2 foundational code - comprehensive docs pending (Issue #235 Phase 1)
//! # Progress Reporting
//!
//! Progress UI using indicatif with TTY/non-TTY support.
//! # noqa: SECTION
//!
//! # Purpose
//!
//! Foundational module for bootstrap-v2 implementation (Issue #235 Phase 1).
//!
//! # Examples
//!
//! See module documentation and tests for usage examples.

use indicatif::MultiProgress;

/// Progress mode
#[derive(Debug, Clone, Copy)]
pub enum ProgressMode {
    /// Interactive TTY with progress bars
    Interactive,

    /// CI mode with plain text
    Ci,

    /// JSON structured output
    Json,
}

/// Progress reporter
pub struct ProgressReporter {
    #[allow(dead_code)]
    multi: MultiProgress,
    #[allow(dead_code)]
    mode: ProgressMode,
}

impl ProgressReporter {
    /// Auto-detect mode based on TTY
    pub fn new_auto() -> Self {
        let mode = if atty::is(atty::Stream::Stdout) {
            ProgressMode::Interactive
        } else {
            ProgressMode::Ci
        };
        Self::new(mode)
    }

    /// Create with explicit mode
    pub fn new(mode: ProgressMode) -> Self {
        Self {
            multi: MultiProgress::new(),
            mode,
        }
    }
}
