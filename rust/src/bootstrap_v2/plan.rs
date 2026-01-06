//! # Execution Plan
//!
//! Build and execute dependency-ordered installation plans.
//!
//! # Purpose
//!
//! Constructs execution plans with phases for parallel and sequential execution.
//! Handles dependency resolution, step ordering, and lock requirements.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::plan::ExecutionPlan;
//! use bootstrap_v2::installers::InstallerRegistry;
//! use bootstrap_v2::context::Context;
//! use bootstrap_v2::config::Config;
//! use std::sync::Arc;
//!
//! # async fn example(ctx: &Context) {
//! let registry = InstallerRegistry::new();
//! let config = Arc::new(Config::default());
//! let plan = ExecutionPlan::compute(&registry, &config, ctx).await.unwrap();
//! plan.print_human();
//! # }
//! ```

use crate::bootstrap_v2::config::Config;
use crate::bootstrap_v2::context::Context;
use crate::bootstrap_v2::errors::BootstrapResult;
use crate::bootstrap_v2::installers::InstallerRegistry;

/// Execution plan
#[derive(Debug)]
pub struct ExecutionPlan {
    /// Phases to execute
    pub phases: Vec<Phase>,

    /// Total steps
    pub total_steps: usize,
}

impl ExecutionPlan {
    /// Compute execution plan from registry and config
    pub async fn compute(
        registry: &InstallerRegistry,
        config: &Config,
        _ctx: &Context,
        profile: &str,
    ) -> BootstrapResult<Self> {
        // Get required tools from config for the given profile
        let required_tools = config.get_tools_for_profile(profile);

        // Resolve dependencies
        let installers = registry.resolve_dependencies(&required_tools)?;

        let mut phases = Vec::new();
        let mut total_steps = 0;

        // Phase 1: Detection (parallel safe)
        let mut detect_steps = Vec::new();
        for installer in &installers {
            detect_steps.push(Step {
                id: format!("detect-{}", installer.id()),
                installer: installer.id().to_string(),
                action: StepAction::Detect,
                dependencies: vec![],
                concurrency_safe: true, // Detection is read-only
                required_locks: vec![],
            });
            total_steps += 1;
        }

        phases.push(Phase {
            name: "Detection".to_string(),
            steps: detect_steps,
            can_parallelize: true,
        });

        // Phase 2: Installation (respects concurrency_safe)
        let mut install_steps = Vec::new();
        for installer in &installers {
            let deps: Vec<String> = installer
                .dependencies()
                .iter()
                .map(|d| format!("install-{}", d))
                .collect();

            let required_locks = if installer.concurrency_safe() {
                vec![]
            } else {
                // Non-concurrent installers need package manager lock
                vec!["package_manager_lock".to_string()]
            };

            install_steps.push(Step {
                id: format!("install-{}", installer.id()),
                installer: installer.id().to_string(),
                action: StepAction::Install,
                dependencies: deps,
                concurrency_safe: installer.concurrency_safe(),
                required_locks,
            });
            total_steps += 1;
        }

        phases.push(Phase {
            name: "Installation".to_string(),
            steps: install_steps,
            can_parallelize: false, // Installation must respect dependencies
        });

        // Phase 3: Verification (parallel safe)
        let mut verify_steps = Vec::new();
        for installer in &installers {
            verify_steps.push(Step {
                id: format!("verify-{}", installer.id()),
                installer: installer.id().to_string(),
                action: StepAction::Verify,
                dependencies: vec![format!("install-{}", installer.id())],
                concurrency_safe: true,
                required_locks: vec![],
            });
            total_steps += 1;
        }

        phases.push(Phase {
            name: "Verification".to_string(),
            steps: verify_steps,
            can_parallelize: true,
        });

        Ok(Self {
            phases,
            total_steps,
        })
    }

    /// Print human-readable plan
    pub fn print_human(&self) {
        println!("Execution Plan:");
        println!("  Total steps: {}", self.total_steps);
        println!();
        for phase in &self.phases {
            println!("  Phase: {}", phase.name);
            println!(
                "    Parallel: {}",
                if phase.can_parallelize { "yes" } else { "no" }
            );
            for step in &phase.steps {
                let concurrent = if step.concurrency_safe {
                    "concurrent"
                } else {
                    "sequential"
                };
                println!("    - {} ({})", step.id, concurrent);
                if !step.dependencies.is_empty() {
                    println!("      Depends on: {:?}", step.dependencies);
                }
                if !step.required_locks.is_empty() {
                    println!("      Locks: {:?}", step.required_locks);
                }
            }
            println!();
        }
    }

    /// Convert to JSON representation
    pub fn to_json(&self) -> serde_json::Value {
        serde_json::json!({
            "total_steps": self.total_steps,
            "phases": self.phases.iter().map(|p| {
                serde_json::json!({
                    "name": p.name,
                    "can_parallelize": p.can_parallelize,
                    "steps": p.steps.iter().map(|s| {
                        serde_json::json!({
                            "id": s.id,
                            "installer": s.installer,
                            "action": format!("{:?}", s.action),
                            "dependencies": s.dependencies,
                            "concurrency_safe": s.concurrency_safe,
                            "required_locks": s.required_locks,
                        })
                    }).collect::<Vec<_>>()
                })
            }).collect::<Vec<_>>()
        })
    }

    /// Compute hash of plan for checkpointing
    pub fn compute_hash(&self) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        self.total_steps.hash(&mut hasher);
        for phase in &self.phases {
            phase.name.hash(&mut hasher);
            for step in &phase.steps {
                step.id.hash(&mut hasher);
            }
        }
        format!("{:x}", hasher.finish())
    }
}

/// Installation phase
#[derive(Debug)]
pub struct Phase {
    /// Phase name
    pub name: String,

    /// Steps in this phase
    pub steps: Vec<Step>,

    /// Can parallelize
    pub can_parallelize: bool,
}

/// Installation step
#[derive(Debug)]
pub struct Step {
    /// Step ID
    pub id: String,

    /// Installer ID
    pub installer: String,

    /// Action to perform
    pub action: StepAction,

    /// Dependencies
    pub dependencies: Vec<String>,

    /// Concurrency safe
    pub concurrency_safe: bool,

    /// Required locks
    pub required_locks: Vec<String>,
}

/// Step action
#[derive(Debug)]
pub enum StepAction {
    /// Detect if installed
    Detect,

    /// Install tool
    Install,

    /// Verify installation
    Verify,

    /// Skip (with reason)
    Skip { reason: String },
}
