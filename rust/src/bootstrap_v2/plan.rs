//! # Execution Plan
//!
//! Build and execute dependency-ordered installation plans.

/// Execution plan
#[derive(Debug)]
pub struct ExecutionPlan {
    /// Phases to execute
    pub phases: Vec<Phase>,

    /// Total steps
    pub total_steps: usize,
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
