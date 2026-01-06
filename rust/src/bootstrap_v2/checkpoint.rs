//! # Checkpointing Module
//!
//! Save and restore execution state for resume capability.
//!
//! # Purpose
//!
//! Provides checkpoint save/load functionality for resuming interrupted installations.
//! State is stored outside the repository by default (XDG/macOS cache dirs).
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::checkpoint::Checkpoint;
//! use bootstrap_v2::plan::ExecutionPlan;
//! use std::path::Path;
//!
//! # async fn example(plan: &ExecutionPlan) -> Result<(), Box<dyn std::error::Error>> {
//! let checkpoint = Checkpoint::new(plan);
//! checkpoint.save(Path::new("/repo"))?;
//!
//! let loaded = Checkpoint::load(Path::new("/repo"))?;
//! if let Some(cp) = loaded {
//!     if cp.is_valid(plan) {
//!         // Resume from checkpoint
//!     }
//! }
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::plan::ExecutionPlan;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

/// Checkpoint state for resume capability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Checkpoint {
    /// Timestamp when checkpoint was created
    pub timestamp: DateTime<Utc>,

    /// Hash of the execution plan
    pub plan_hash: String,

    /// Steps completed successfully
    pub completed_steps: Vec<String>,

    /// Steps that failed
    pub failed_steps: Vec<String>,
}

impl Checkpoint {
    /// Create new checkpoint from plan
    ///
    /// # Arguments
    ///
    /// * `plan` - Execution plan to checkpoint
    ///
    /// # Returns
    ///
    /// New checkpoint with current timestamp and plan hash
    pub fn new(plan: &ExecutionPlan) -> Self {
        Self {
            timestamp: Utc::now(),
            plan_hash: plan.compute_hash(),
            completed_steps: vec![],
            failed_steps: vec![],
        }
    }

    /// Save checkpoint to disk
    ///
    /// # Arguments
    ///
    /// * `repo_root` - Repository root path
    ///
    /// # Returns
    ///
    /// Ok on success, error on I/O failure
    ///
    /// # Policy
    ///
    /// State files live outside the repo by default (cache dirs) to avoid dirty working trees.
    /// Uses XDG cache on Linux and macOS caches on macOS.
    pub fn save(&self, repo_root: &Path) -> BootstrapResult<()> {
        let path = default_checkpoint_path(repo_root)?;

        // Create parent directory if needed
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| {
                BootstrapError::ConfigError(format!("Failed to create checkpoint directory: {}", e))
            })?;
        }

        let json = serde_json::to_string_pretty(self).map_err(|e| {
            BootstrapError::ConfigError(format!("Failed to serialize checkpoint: {}", e))
        })?;

        fs::write(&path, json).map_err(|e| {
            BootstrapError::ConfigError(format!(
                "Failed to write checkpoint to {}: {}",
                path.display(),
                e
            ))
        })?;

        Ok(())
    }

    /// Load checkpoint from disk
    ///
    /// # Arguments
    ///
    /// * `repo_root` - Repository root path
    ///
    /// # Returns
    ///
    /// Some(checkpoint) if found and valid, None if not found
    ///
    /// # Errors
    ///
    /// Returns error if checkpoint file exists but is corrupt
    pub fn load(repo_root: &Path) -> BootstrapResult<Option<Self>> {
        let path = default_checkpoint_path(repo_root)?;

        if !path.exists() {
            return Ok(None);
        }

        let json = fs::read_to_string(&path).map_err(|e| {
            BootstrapError::ConfigError(format!(
                "Failed to read checkpoint from {}: {}",
                path.display(),
                e
            ))
        })?;

        let checkpoint: Checkpoint = serde_json::from_str(&json).map_err(|e| {
            BootstrapError::ConfigError(format!("Failed to parse checkpoint: {}", e))
        })?;

        Ok(Some(checkpoint))
    }

    /// Check if checkpoint is valid for current plan
    ///
    /// # Arguments
    ///
    /// * `current_plan` - Current execution plan
    ///
    /// # Returns
    ///
    /// true if plan hash matches (checkpoint is compatible)
    pub fn is_valid(&self, current_plan: &ExecutionPlan) -> bool {
        self.plan_hash == current_plan.compute_hash()
    }

    /// Mark a step as completed
    ///
    /// # Arguments
    ///
    /// * `step_id` - Step identifier to mark as complete
    pub fn mark_completed(&mut self, step_id: String) {
        if !self.completed_steps.contains(&step_id) {
            self.completed_steps.push(step_id);
        }
    }

    /// Mark a step as failed
    ///
    /// # Arguments
    ///
    /// * `step_id` - Step identifier to mark as failed
    pub fn mark_failed(&mut self, step_id: String) {
        if !self.failed_steps.contains(&step_id) {
            self.failed_steps.push(step_id);
        }
    }

    /// Check if a step was completed
    ///
    /// # Arguments
    ///
    /// * `step_id` - Step identifier to check
    ///
    /// # Returns
    ///
    /// true if step is in completed list
    pub fn is_completed(&self, step_id: &str) -> bool {
        self.completed_steps.contains(&step_id.to_string())
    }
}

/// Get default checkpoint path
///
/// # Arguments
///
/// * `repo_root` - Repository root directory
///
/// # Returns
///
/// Path to checkpoint file in cache directory
///
/// # Errors
///
/// Returns error if cache directory cannot be determined (no XDG/macOS cache available)
///
/// # Platform Behavior
///
/// - Linux: Uses XDG_CACHE_HOME or ~/.cache
/// - macOS: Uses ~/Library/Caches
/// - No fallback to repo root (policy: checkpoints must be outside repo)
fn default_checkpoint_path(repo_root: &Path) -> BootstrapResult<PathBuf> {
    // Try to get cache directory
    if let Some(cache_dir) = dirs::cache_dir() {
        // Use cache_dir/bootstrap-repo-lint/checkpoints/<repo-name>.json
        let repo_name = repo_root
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        Ok(cache_dir
            .join("bootstrap-repo-lint")
            .join("checkpoints")
            .join(format!("{}.json", repo_name)))
    } else {
        // No fallback to repo root per policy - return error
        Err(BootstrapError::ConfigError(
            "Cannot determine cache directory for checkpoint storage. \
             XDG_CACHE_HOME or platform cache directory is required."
                .to_string(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bootstrap_v2::config::Config;
    use crate::bootstrap_v2::context::Context;
    use crate::bootstrap_v2::installers::InstallerRegistry;
    use std::sync::Arc;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_checkpoint_new() {
        let registry = InstallerRegistry::new();
        let config = Arc::new(Config::default());
        let ctx = Context::new_for_testing(PathBuf::from("/tmp/test"), false, config.clone());
        let plan = ExecutionPlan::compute(&registry, &config, &ctx)
            .await
            .unwrap();

        let checkpoint = Checkpoint::new(&plan);
        assert_eq!(checkpoint.plan_hash, plan.compute_hash());
        assert!(checkpoint.completed_steps.is_empty());
        assert!(checkpoint.failed_steps.is_empty());
    }

    #[tokio::test]
    async fn test_checkpoint_save_load() {
        let temp_dir = TempDir::new().unwrap();
        let registry = InstallerRegistry::new();
        let config = Arc::new(Config::default());
        let ctx = Context::new_for_testing(temp_dir.path().to_path_buf(), false, config.clone());
        let plan = ExecutionPlan::compute(&registry, &config, &ctx)
            .await
            .unwrap();

        let mut checkpoint = Checkpoint::new(&plan);
        checkpoint.mark_completed("step1".to_string());
        checkpoint.mark_failed("step2".to_string());

        checkpoint.save(temp_dir.path()).unwrap();

        let loaded = Checkpoint::load(temp_dir.path()).unwrap();
        assert!(loaded.is_some());

        let loaded = loaded.unwrap();
        assert_eq!(loaded.plan_hash, checkpoint.plan_hash);
        assert_eq!(loaded.completed_steps.len(), 1);
        assert_eq!(loaded.failed_steps.len(), 1);
        assert!(loaded.is_completed("step1"));
    }

    #[tokio::test]
    async fn test_checkpoint_validity() {
        let registry = InstallerRegistry::new();
        let config = Arc::new(Config::default());
        let ctx = Context::new_for_testing(PathBuf::from("/tmp/test"), false, config.clone());
        let plan = ExecutionPlan::compute(&registry, &config, &ctx)
            .await
            .unwrap();

        let checkpoint = Checkpoint::new(&plan);
        assert!(checkpoint.is_valid(&plan));
    }

    #[test]
    fn test_checkpoint_load_missing() {
        let temp_dir = TempDir::new().unwrap();
        let result = Checkpoint::load(temp_dir.path()).unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn test_default_checkpoint_path() {
        let temp_dir = TempDir::new().unwrap();
        let path = default_checkpoint_path(temp_dir.path()).unwrap();
        // Path should be in the cache dir and include the bootstrap-repo-lint subdir
        assert!(path.to_string_lossy().contains("bootstrap-repo-lint"));
    }
}
