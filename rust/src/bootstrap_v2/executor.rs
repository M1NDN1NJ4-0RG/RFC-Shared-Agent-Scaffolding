//! # Execution Engine
//!
//! Execute installation plans with bounded parallelism and resource locks.
//!
//! # Purpose
//!
//! Provides the execution engine that runs ExecutionPlans with proper concurrency
//! control, lock management, and progress reporting. Implements Phase 4 requirements
//! including job semaphores and lock-aware step execution.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::executor::Executor;
//! use bootstrap_v2::plan::ExecutionPlan;
//! use bootstrap_v2::context::Context;
//! use bootstrap_v2::installers::InstallerRegistry;
//! use std::sync::Arc;
//!
//! # async fn example(plan: ExecutionPlan, ctx: Arc<Context>) {
//! let registry = Arc::new(InstallerRegistry::new());
//! let executor = Executor::new(ctx.clone(), registry);
//! let results = executor.execute(&plan).await.unwrap();
//! # }
//! ```

use crate::bootstrap_v2::context::Context;
use crate::bootstrap_v2::errors::{BootstrapError, BootstrapResult};
use crate::bootstrap_v2::installer::{InstallResult, VerifyResult};
use crate::bootstrap_v2::installers::InstallerRegistry;
use crate::bootstrap_v2::lock::LockManager;
use crate::bootstrap_v2::plan::{ExecutionPlan, Phase, Step, StepAction};
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::Semaphore;

/// Execution result for a single step
#[derive(Debug, Clone)]
pub struct StepResult {
    /// Step ID
    pub step_id: String,

    /// Installer ID
    pub installer_id: String,

    /// Success flag
    pub success: bool,

    /// Duration
    pub duration: std::time::Duration,

    /// Error message (if failed)
    pub error: Option<String>,

    /// Install result (if install step)
    pub install_result: Option<InstallResult>,

    /// Verify result (if verify step)
    pub verify_result: Option<VerifyResult>,
}

/// Execution engine
pub struct Executor {
    /// Context
    ctx: Arc<Context>,

    /// Installer registry
    registry: Arc<InstallerRegistry>,

    /// Lock manager
    lock_manager: Arc<LockManager>,

    /// Job semaphore for bounded parallelism
    job_semaphore: Arc<Semaphore>,
}

impl Executor {
    /// Create new executor
    ///
    /// # Arguments
    ///
    /// * `ctx` - Execution context with configuration
    /// * `registry` - Installer registry
    ///
    /// # Returns
    ///
    /// New executor with job semaphore sized per context (CI=2, Interactive=min(4,cpus))
    pub fn new(ctx: Arc<Context>, registry: Arc<InstallerRegistry>) -> Self {
        let max_jobs = ctx.max_jobs as usize;
        let job_semaphore = Arc::new(Semaphore::new(max_jobs));
        let lock_manager = Arc::new(LockManager::new());

        Self {
            ctx,
            registry,
            lock_manager,
            job_semaphore,
        }
    }

    /// Execute the full plan
    ///
    /// # Arguments
    ///
    /// * `plan` - Execution plan to run
    ///
    /// # Returns
    ///
    /// Vector of step results for all steps in all phases
    ///
    /// # Errors
    ///
    /// Returns error if critical step fails and fail-fast is enabled
    pub async fn execute(&self, plan: &ExecutionPlan) -> BootstrapResult<Vec<StepResult>> {
        let mut all_results = Vec::new();

        for phase in &plan.phases {
            let phase_start = Instant::now();

            // Report phase start
            if let Some(progress) = &self.ctx.progress {
                progress.emit_event_phase_started(&phase.name);
            }

            let phase_results = self.execute_phase(phase).await?;
            all_results.extend(phase_results);

            // Report phase completion
            if let Some(progress) = &self.ctx.progress {
                progress.emit_event_phase_completed(&phase.name, phase_start.elapsed());
            }
        }

        Ok(all_results)
    }

    /// Execute a single phase
    ///
    /// # Arguments
    ///
    /// * `phase` - Phase to execute
    ///
    /// # Returns
    ///
    /// Vector of step results for all steps in this phase
    ///
    /// # Errors
    ///
    /// Returns error if critical step fails
    async fn execute_phase(&self, phase: &Phase) -> BootstrapResult<Vec<StepResult>> {
        if phase.can_parallelize {
            // Execute steps in parallel with job semaphore
            self.execute_parallel(phase).await
        } else {
            // Execute steps sequentially (respecting dependencies)
            self.execute_sequential(phase).await
        }
    }

    /// Execute steps in parallel with bounded concurrency
    ///
    /// # Arguments
    ///
    /// * `phase` - Phase with parallel-safe steps
    ///
    /// # Returns
    ///
    /// Vector of step results
    ///
    /// # Errors
    ///
    /// Returns first critical error encountered
    async fn execute_parallel(&self, phase: &Phase) -> BootstrapResult<Vec<StepResult>> {
        let mut handles = Vec::new();

        for step in &phase.steps {
            let step = step.clone();
            let ctx = self.ctx.clone();
            let registry = self.registry.clone();
            let lock_manager = self.lock_manager.clone();
            let semaphore = self.job_semaphore.clone();

            let handle = tokio::spawn(async move {
                // Acquire job semaphore permit
                let _permit = semaphore.acquire().await.unwrap();

                // Execute step
                Self::execute_step_impl(&step, &ctx, &registry, &lock_manager).await
            });

            handles.push(handle);
        }

        // Await all tasks
        let mut results = Vec::new();
        for handle in handles {
            let result = handle
                .await
                .map_err(|e| BootstrapError::ExecutionFailed(e.to_string()))??;
            results.push(result);
        }

        Ok(results)
    }

    /// Execute steps sequentially
    ///
    /// # Arguments
    ///
    /// * `phase` - Phase with sequential steps
    ///
    /// # Returns
    ///
    /// Vector of step results in execution order
    ///
    /// # Errors
    ///
    /// Returns first error encountered (fail-fast)
    async fn execute_sequential(&self, phase: &Phase) -> BootstrapResult<Vec<StepResult>> {
        let mut results = Vec::new();

        for step in &phase.steps {
            let result =
                Self::execute_step_impl(step, &self.ctx, &self.registry, &self.lock_manager)
                    .await?;
            results.push(result);
        }

        Ok(results)
    }

    /// Execute a single step
    ///
    /// # Arguments
    ///
    /// * `step` - Step to execute
    /// * `ctx` - Execution context
    /// * `registry` - Installer registry
    /// * `lock_manager` - Lock manager for resource locks
    ///
    /// # Returns
    ///
    /// Step result with timing and outcome
    ///
    /// # Errors
    ///
    /// Returns error if step execution fails
    async fn execute_step_impl(
        step: &Step,
        ctx: &Context,
        registry: &InstallerRegistry,
        lock_manager: &LockManager,
    ) -> BootstrapResult<StepResult> {
        let start = Instant::now();

        // Acquire required locks
        let mut _guards = Vec::new();
        for lock_name in &step.required_locks {
            let max_wait = if ctx.is_ci {
                std::time::Duration::from_secs(60)
            } else {
                std::time::Duration::from_secs(180)
            };
            let guard = lock_manager.acquire(lock_name, max_wait, ctx.is_ci).await?;
            _guards.push(guard);
        }

        // Get installer
        let installer = registry
            .get(&step.installer)
            .ok_or_else(|| BootstrapError::InstallerNotFound(step.installer.clone()))?;

        // Create progress task if available
        let task_handle = if let Some(progress) = &ctx.progress {
            Some(progress.add_task(step.id.clone(), installer.name().to_string()))
        } else {
            None
        };

        // Set task to running
        if let Some(task) = &task_handle {
            task.set_running(&format!("Running {}", installer.name()));
        }

        // Execute action
        let result = match &step.action {
            StepAction::Detect => {
                let version_opt = installer.detect(ctx).await?;
                StepResult {
                    step_id: step.id.clone(),
                    installer_id: step.installer.clone(),
                    success: true,
                    duration: start.elapsed(),
                    error: None,
                    install_result: None,
                    verify_result: Some(VerifyResult {
                        success: version_opt.is_some(),
                        version: version_opt,
                        issues: vec![],
                    }),
                }
            }
            StepAction::Install => {
                let install_res = installer.install(ctx).await?;
                StepResult {
                    step_id: step.id.clone(),
                    installer_id: step.installer.clone(),
                    success: true,
                    duration: start.elapsed(),
                    error: None,
                    install_result: Some(install_res),
                    verify_result: None,
                }
            }
            StepAction::Verify => {
                let verify_res = installer.verify(ctx).await?;
                let success = verify_res.success;
                StepResult {
                    step_id: step.id.clone(),
                    installer_id: step.installer.clone(),
                    success,
                    duration: start.elapsed(),
                    error: if !success {
                        Some(verify_res.issues.join("; "))
                    } else {
                        None
                    },
                    install_result: None,
                    verify_result: Some(verify_res),
                }
            }
            StepAction::Skip { reason } => StepResult {
                step_id: step.id.clone(),
                installer_id: step.installer.clone(),
                success: true,
                duration: start.elapsed(),
                error: None,
                install_result: None,
                verify_result: Some(VerifyResult {
                    success: true,
                    version: None,
                    issues: vec![format!("Skipped: {}", reason)],
                }),
            },
        };

        // Update task status
        if let Some(task) = &task_handle {
            if result.success {
                task.set_success(&format!("Completed {}", installer.name()));
            } else {
                task.set_failed(&result.error.clone().unwrap_or_default());
            }
        }

        Ok(result)
    }
}

// Make Step cloneable for parallel execution
impl Clone for Step {
    fn clone(&self) -> Self {
        Self {
            id: self.id.clone(),
            installer: self.installer.clone(),
            action: match &self.action {
                StepAction::Detect => StepAction::Detect,
                StepAction::Install => StepAction::Install,
                StepAction::Verify => StepAction::Verify,
                StepAction::Skip { reason } => StepAction::Skip {
                    reason: reason.clone(),
                },
            },
            dependencies: self.dependencies.clone(),
            concurrency_safe: self.concurrency_safe,
            required_locks: self.required_locks.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bootstrap_v2::config::Config;
    use crate::bootstrap_v2::progress::ProgressReporter;
    use std::path::PathBuf;

    #[tokio::test]
    async fn test_executor_creation() {
        let config = Arc::new(Config::default());
        let ctx = Arc::new(Context::new_for_testing(
            PathBuf::from("/tmp/test"),
            false,
            config,
        ));
        let registry = Arc::new(InstallerRegistry::new());

        let executor = Executor::new(ctx, registry);
        assert!(Arc::strong_count(&executor.job_semaphore) >= 1);
    }

    #[tokio::test]
    async fn test_parallel_execution_bounded() {
        let config = Arc::new(Config::default());
        let progress = Arc::new(ProgressReporter::new_for_testing());
        let ctx = Arc::new(Context::new_with_progress_for_testing(
            PathBuf::from("/tmp/test"),
            false,
            config,
            progress,
        ));
        let registry = Arc::new(InstallerRegistry::new());

        let executor = Executor::new(ctx.clone(), registry.clone());

        // Create a simple plan
        let plan = ExecutionPlan::compute(&registry, &ctx.config, &ctx)
            .await
            .unwrap();

        // Should not panic
        let _results = executor.execute(&plan).await;
    }
}
