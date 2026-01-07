//! # Progress Reporting
//!
//! Progress UI using indicatif with TTY/non-TTY support.
//!
//! # Purpose
//!
//! Provides multi-task progress reporting with TTY detection and mode selection.
//! Supports interactive mode (with progress bars), CI mode (plain text), and JSON output.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::progress::{ProgressReporter, ProgressMode};
//!
//! let reporter = ProgressReporter::new_auto();
//! let task = reporter.add_task("install-ripgrep".to_string(), "Installing ripgrep".to_string());
//! task.set_running("Downloading...");
//! task.set_success("Installed");
//! ```

use chrono;
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use serde::Serialize;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;

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

/// Task status
#[derive(Debug, Clone, Serialize)]
pub enum TaskStatus {
    /// Task is pending
    Pending,
    /// Task is running
    Running,
    /// Task completed successfully
    Success,
    /// Task failed
    Failed { error: String },
    /// Task was skipped
    Skipped { reason: String },
}

/// Progress task
pub struct ProgressTask {
    bar: Option<ProgressBar>,
    status: Arc<Mutex<TaskStatus>>,
    elapsed: Instant,
    mode: ProgressMode,
    id: String,
    name: String,
}

impl ProgressTask {
    /// Set task to running status
    pub fn set_running(&self, msg: &str) {
        *self.status.lock().unwrap() = TaskStatus::Running;

        match self.mode {
            ProgressMode::Interactive => {
                if let Some(bar) = &self.bar {
                    bar.set_message(format!("{}: {}", self.name, msg));
                }
            }
            ProgressMode::Ci => {
                println!(
                    "[{}] {}: {}",
                    chrono::Utc::now().format("%H:%M:%S"),
                    self.name,
                    msg
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "TaskProgress",
                    "task_id": self.id,
                    "name": self.name,
                    "status": "running",
                    "message": msg,
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Set task to success status
    pub fn set_success(&self, msg: &str) {
        *self.status.lock().unwrap() = TaskStatus::Success;
        let duration = self.elapsed.elapsed();

        match self.mode {
            ProgressMode::Interactive => {
                if let Some(bar) = &self.bar {
                    bar.finish_with_message(format!("✓ {}: {} ({:?})", self.name, msg, duration));
                }
            }
            ProgressMode::Ci => {
                println!(
                    "[{}] ✓ {}: {} ({:?})",
                    chrono::Utc::now().format("%H:%M:%S"),
                    self.name,
                    msg,
                    duration
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "TaskCompleted",
                    "task_id": self.id,
                    "name": self.name,
                    "status": "success",
                    "message": msg,
                    "duration_ms": duration.as_millis(),
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Set task to failed status
    pub fn set_failed(&self, error: &str) {
        *self.status.lock().unwrap() = TaskStatus::Failed {
            error: error.to_string(),
        };
        let duration = self.elapsed.elapsed();

        match self.mode {
            ProgressMode::Interactive => {
                if let Some(bar) = &self.bar {
                    bar.finish_with_message(format!("✗ {}: {} ({:?})", self.name, error, duration));
                }
            }
            ProgressMode::Ci => {
                println!(
                    "[{}] ✗ {}: {} ({:?})",
                    chrono::Utc::now().format("%H:%M:%S"),
                    self.name,
                    error,
                    duration
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "TaskCompleted",
                    "task_id": self.id,
                    "name": self.name,
                    "status": "failed",
                    "error": error,
                    "duration_ms": duration.as_millis(),
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Set task to skipped status
    pub fn set_skipped(&self, reason: &str) {
        *self.status.lock().unwrap() = TaskStatus::Skipped {
            reason: reason.to_string(),
        };

        match self.mode {
            ProgressMode::Interactive => {
                if let Some(bar) = &self.bar {
                    bar.finish_with_message(format!("⊘ {}: {}", self.name, reason));
                }
            }
            ProgressMode::Ci => {
                println!(
                    "[{}] ⊘ {}: {}",
                    chrono::Utc::now().format("%H:%M:%S"),
                    self.name,
                    reason
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "TaskSkipped",
                    "task_id": self.id,
                    "name": self.name,
                    "reason": reason,
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }
}

/// Progress reporter
pub struct ProgressReporter {
    multi: MultiProgress,
    mode: ProgressMode,
    tasks: Arc<Mutex<HashMap<String, Arc<ProgressTask>>>>,
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
            tasks: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Add a new task
    pub fn add_task(&self, id: String, name: String) -> Arc<ProgressTask> {
        let bar = match self.mode {
            ProgressMode::Interactive => {
                let bar = self.multi.add(ProgressBar::new_spinner());
                bar.set_style(
                    ProgressStyle::default_spinner()
                        .template("{spinner} [{elapsed_precise}] {msg}")
                        .unwrap(),
                );
                bar.set_message(format!("{}: Pending", name));
                Some(bar)
            }
            _ => None,
        };

        let task = Arc::new(ProgressTask {
            bar,
            status: Arc::new(Mutex::new(TaskStatus::Pending)),
            elapsed: Instant::now(),
            mode: self.mode,
            id: id.clone(),
            name,
        });

        self.tasks.lock().unwrap().insert(id, Arc::clone(&task));
        task
    }

    /// Get current mode
    pub fn mode(&self) -> ProgressMode {
        self.mode
    }

    /// Emit phase started event
    pub fn emit_event_phase_started(&self, phase_name: &str) {
        match self.mode {
            ProgressMode::Interactive | ProgressMode::Ci => {
                println!(
                    "[{}] Phase: {}",
                    chrono::Utc::now().format("%H:%M:%S"),
                    phase_name
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "PhaseStarted",
                    "phase": phase_name,
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Emit phase completed event
    pub fn emit_event_phase_completed(&self, phase_name: &str, duration: std::time::Duration) {
        match self.mode {
            ProgressMode::Interactive | ProgressMode::Ci => {
                println!(
                    "[{}] Phase {} completed in {:?}",
                    chrono::Utc::now().format("%H:%M:%S"),
                    phase_name,
                    duration
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "PhaseCompleted",
                    "phase": phase_name,
                    "duration_ms": duration.as_millis(),
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Emit plan computed event
    pub fn emit_event_plan_computed(&self) {
        match self.mode {
            ProgressMode::Interactive | ProgressMode::Ci => {
                println!(
                    "[{}] Execution plan computed",
                    chrono::Utc::now().format("%H:%M:%S")
                );
            }
            ProgressMode::Json => {
                let event = serde_json::json!({
                    "type": "PlanComputed",
                });
                println!("{}", serde_json::to_string(&event).unwrap());
            }
        }
    }

    /// Create reporter for testing
    #[cfg(test)]
    pub fn new_for_testing() -> Self {
        Self::new(ProgressMode::Ci)
    }
}
