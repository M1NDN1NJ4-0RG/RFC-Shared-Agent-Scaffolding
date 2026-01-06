# [EPIC] Rust Migration Plan: Modular Toolchain Bootstrapper

## General Rules (MUST FOLLOW)

These rules are **non-negotiable** and must be treated as part of the contract for the Rust rewrite.

1) **Determinism over convenience**
   - Exit codes must remain deterministic and map to the existing contract.
   - Do not “best-effort” your way into ambiguous success states.

2) **Fail-fast, always**
   - If a required prerequisite is missing or a critical step fails, stop immediately with the correct exit code.
   - No silent fall-through, no “warn and continue” for required components.

3) **Idempotency governs retries**
   - Retries + exponential backoff are allowed **only** for operations that are proven safe to retry.
   - Unsafe/non-idempotent operations must not be blindly retried.

4) **Concurrency only where safe**
   - Parallelism must be bounded and must respect resource locks (package manager locks, shared caches, filesystem paths).
   - Concurrency must not reduce log clarity or determinism.

5) **Progress UI must be honest**
   - The CLI must always communicate what it is doing.
   - In non-TTY/CI, output must degrade gracefully (no ANSI garbage), and still provide clear status.

6) **No repo pollution by default**
   - Checkpoints/state/caches must live outside the repo by default (XDG/macOS cache dirs), unless explicitly overridden.

7) **Parity + tests are mandatory**
   - Changes must preserve behavior relative to the Bash script.
   - Parity tests and integration tests must be used to prove correctness.

8) **Rule of Three is a HARD REQUIREMENT**
   - Any repeated logic, command construction, or installer behavior must be abstracted/shared once it appears three times.
   - Do not allow copy/paste divergence across installers; centralize shared helpers (download, verify, checksum, version parsing, command execution, logging).
   - If a third instance appears during development, refactor immediately as part of the same change.

9) **Session execution + journaling is mandatory**
   - Each session must implement **as much as possible** within the scoped phase(s) before stopping.
   - At the start of the work, create the journal file if it does not exist:
     - `docs/ai-prompt/<ISSUE#>/<ISSUE_NUMBER>-next-steps.md`
   - At the end of **every** session, update that file with **exact, resumable notes**, including:
     - What was changed (files + brief intent)
     - What remains (as checkboxes)
     - Any required follow-ups, edge cases, or hazards (clearly called out)
   - If token/context limits or other constraints are hit:
     - Stop starting new work
     - Commit/persist completed work
     - Leave the repo and the journal in a clean, resumable state

---

## Human Decisions Locked In (NO DISCRETION)

These items are explicitly decided. Implementation may vary, but behavior must match.

- **CLI semantics are fixed:**
  - `install` always performs `detect → install → verify` (fail-fast). No `--no-verify` flag.
  - `verify` is **verify-only** (no installs, no downloads).
  - `doctor` is diagnostics; `doctor --strict` treats WARN as FAIL.
- **Config policy:**
  - The binary supports defaults when `.bootstrap.toml` is absent.
  - **For this repo in CI:** `.bootstrap.toml` is **required**. Missing config in CI exits with **UsageError (1)** and a clear message.
- **Concurrency policy:**
  - Default jobs: **CI = 2**; Interactive = `min(4, num_cpus)`.
  - Support override via `--jobs <N>` and `BOOTSTRAP_JOBS`.
  - Add per-host HTTP concurrency limit: **2 requests per host**.
- **Locking policy:**
  - A lock manager is **mandatory**.
  - Standard lock names are fixed constants: `brew_lock`, `apt_lock`, `cache_lock`, `venv_lock`.
- **Retry policy:**
  - Retries are allowed **only** for `RetryClass::Transient`.
  - Respect HTTP `Retry-After` when present (e.g., 429/503).
  - `RetryClass::Security` (checksum/signature mismatch) fails immediately.
  - Total retry budget is enforced (`max_total_time`).
- **Package manager lock contention:**
  - Do **not** retry installs.
  - Use lock-wait with backoff only.
  - Max lock-wait time: **CI = 60s**; Interactive = **180s**.
- **Checkpointing:**
  - Checkpoint/resume is **OFF by default**.
  - Enable only via `--checkpoint` / `--resume`.
- **Progress UI:**
  - v1 uses **indicatif only** (no ratatui/full-screen TUI).
  - Avoid ANSI styling in CI/non-TTY.
- **Runtime:**
  - Use **tokio** (required).
- **HTTP/TLS:**
  - Use `reqwest` with **rustls** (no OpenSSL-vendored requirement in the plan).
- **Wrapper binary resolution order:**
  1) `$BOOTSTRAP_BIN` if set
  2) `$REPO_ROOT/.bootstrap/bin/bootstrap`
  3) `$REPO_ROOT/target/release/bootstrap` (dev-only fallback)
  4) legacy Bash
- **Downgrades:**
  - Disallowed by default.
  - Allowed only with explicit `--allow-downgrade` (and forbidden in CI unless explicitly passed).
- **Caching:**
  - Per-user cache, keyed by tool/version/platform/arch and protected by checksums.
- **Offline mode:**
  - Support `--offline`: use cache only; if required artifacts missing, fail-fast.
- **Supply-chain hardening:**
  - Any direct-download installer requires checksum verification (hard requirement).
  - Signature verification is optional when upstream provides it.
- **Scope constraints:**
  - No Windows support in v1.
  - No plugin system in v1.
- **Performance metric:**
  - 30–50% speedup is a **goal**, not a release gate.

---


## Executive Summary

This plan outlines a phased migration from `bootstrap-repo-lint-toolchain.sh` (Bash) to a modular Rust binary that preserves deterministic behavior while adding:
- Parallel execution (where safe)
- Rich progress UI
- Structured logging
- Better error handling
- Easier tool addition/removal

**Target:** Self-contained binary with no external Bash dependency, backwards-compatible during transition.

---

## Phase 1: Core Infrastructure

### 1.1 Project Setup

**CLI Framework:**
- Use `clap` (derive API) for argument parsing
- Subcommands: `install`, `doctor`, `verify`
- Flags: `--dry-run`, `--ci`, `--json`, `--verbose`
- Semantics (HARD REQUIREMENTS):
  - `install` always runs `detect → install → verify` and fails fast.
  - `verify` is verify-only (no installs, no downloads).
  - `doctor` is diagnostics; `doctor --strict` treats WARN as FAIL.
- Concurrency flag: `--jobs <N>` (default CI=2; Interactive=min(4,num_cpus)); env override `BOOTSTRAP_JOBS`.
- Add flags: `--offline`, `--allow-downgrade`, `--strict` (doctor).


**Example CLI:**
~~~bash
bootstrap install [--profile dev|ci|full] [--jobs N] [--dry-run] [--offline] [--allow-downgrade] [--ci] [--json] [--verbose]
bootstrap doctor [--strict] [--json]
bootstrap verify [--json] [--verbose]
~~~

### 1.2 Exit Code Constants

~~~rust
pub enum ExitCode {
    Success = 0,
    UsageError = 1,
    NotInRepo = 10,
    VenvActivationFailed = 11,
    NoInstallTarget = 12,
    RepoLintUpgradeFailed = 13,
    RepoLintInstallFailed = 14,
    PythonToolsFailed = 15,
    ShellToolchainFailed = 16,
    PowerShellToolchainFailed = 17,
    PerlToolchainFailed = 18,
    VerificationFailed = 19,
    ActionlintFailed = 20,
    RipgrepFailed = 21,
}

impl ExitCode {
    pub fn as_i32(&self) -> i32 {
        *self as i32
    }
}
~~~

**Locked requirement:** `ripgrep` is REQUIRED (hard fail with `RipgrepFailed = 21` if not present after install).


### 1.3 Error Type Hierarchy

~~~rust
#[derive(Debug, thiserror::Error)]
pub enum BootstrapError {
    #[error("Not in git repository")]
    NotInRepo,
    
    #[error("Virtual environment activation failed: {0}")]
    VenvActivation(String),
    
    #[error("Installation failed: {tool} ({exit_code})")]
    InstallFailed {
        tool: String,
        exit_code: i32,
        stderr: String,
    },
    
    // ... more variants
}

impl BootstrapError {
    pub fn exit_code(&self) -> ExitCode {
        match self {
            Self::NotInRepo => ExitCode::NotInRepo,
            Self::VenvActivation(_) => ExitCode::VenvActivationFailed,
            // ...
        }
    }
}
~~~

---

## Phase 2: Installer Registry & Trait

### 2.1 Core Installer Interface

~~~rust
#[async_trait]
pub trait Installer: Send + Sync {
    /// Unique identifier
    fn id(&self) -> &'static str;
    
    /// Human-readable name
    fn name(&self) -> &'static str;
    
    /// Description for help text
    fn description(&self) -> &'static str;
    
    /// Tools this installer depends on
    fn dependencies(&self) -> Vec<&'static str> {
        vec![]
    }
    
    /// Can this run concurrently with others?
    fn concurrency_safe(&self) -> bool {
        false  // Conservative default
    }
    
    /// Detect if already installed
    async fn detect(&self, ctx: &Context) -> Result<Option<Version>>;
    
    /// Perform installation
    async fn install(&self, ctx: &Context) -> Result<InstallResult>;
    
    /// Verify installation succeeded
    async fn verify(&self, ctx: &Context) -> Result<VerifyResult>;
}

pub struct InstallResult {
    pub version: Version,
    pub installed_new: bool,
    pub log_messages: Vec<String>,
}

pub struct VerifyResult {
    pub success: bool,
    pub version: Option<Version>,
    pub issues: Vec<String>,
}
~~~

### 2.2 Context Object

~~~rust
pub struct Context {
    pub repo_root: PathBuf,
    pub venv_path: PathBuf,
    pub os: OsType,
    pub package_manager: PackageManager,
    pub dry_run: bool,
    pub verbosity: Verbosity,
    pub progress: Arc<ProgressReporter>,
    pub config: Arc<Config>,
}

pub enum OsType {
    MacOS,
    Linux,
    Windows,  // Future
}

pub enum PackageManager {
    Homebrew,
    Apt,
    Snap,
    None,
}
~~~

### 2.3 Static Registry

~~~rust
pub struct InstallerRegistry {
    installers: HashMap<&'static str, Box<dyn Installer>>,
}

impl InstallerRegistry {
    pub fn new() -> Self {
        let mut registry = Self {
            installers: HashMap::new(),
        };
        
        // Register all installers
        registry.register(Box::new(PythonBlackInstaller));
        registry.register(Box::new(PythonRuffInstaller));
        registry.register(Box::new(ActionlintInstaller));
        registry.register(Box::new(RipgrepInstaller));
        registry.register(Box::new(ShellcheckInstaller));
        // ... all tools
        
        registry
    }
    
    pub fn register(&mut self, installer: Box<dyn Installer>) {
        self.installers.insert(installer.id(), installer);
    }
    
    pub fn get(&self, id: &str) -> Option<&dyn Installer> {
        self.installers.get(id).map(|b| &**b)
    }
    
    pub fn resolve_dependencies(&self, ids: &[&str]) 
        -> Result<Vec<&dyn Installer>> 
    {
        // Topological sort with dependency resolution
        // ...
    }
}
~~~

---

## Phase 3: Execution Plan & Dependency Graph

### 3.1 Plan Computation

~~~rust
pub struct ExecutionPlan {
    pub phases: Vec<Phase>,
    pub total_steps: usize,
    pub estimated_duration: Option<Duration>,
}

pub struct Phase {
    pub name: String,
    pub steps: Vec<Step>,
    pub can_parallelize: bool,
}

pub struct Step {
    pub id: String,
    pub installer: &'static str,
    pub action: StepAction,
    pub dependencies: Vec<String>,
    pub concurrency_safe: bool,
    pub required_locks: Vec<String>,
}

pub enum StepAction {
    Detect,
    Install,
    Verify,
    Skip { reason: String },
}

impl ExecutionPlan {
    pub async fn compute(
        registry: &InstallerRegistry,
        config: &Config,
        ctx: &Context,
    ) -> Result<Self> {
        let required_tools = config.resolve_tools()?;
        let installers = registry.resolve_dependencies(&required_tools)?;
        
        let mut plan = ExecutionPlan {
            phases: vec![],
            total_steps: 0,
            estimated_duration: None,
        };
        
        // Phase 1: Detection (parallel safe)
        let detect_steps = installers.iter()
            .map(|i| Step {
                id: format!("detect-{}", i.id()),
                installer: i.id(),
                action: StepAction::Detect,
                dependencies: vec![],
                concurrency_safe: true,
                required_locks: vec![],
            })
            .collect();
        
        plan.phases.push(Phase {
            name: "Detection".into(),
            steps: detect_steps,
            can_parallelize: true,
        });
        
        // Phase 2: Installation (respects concurrency_safe)
        // ...
        
        Ok(plan)
    }
    
    pub fn print_human(&self) {
        println!("Execution Plan:");
        for phase in &self.phases {
            println!("  Phase: {}", phase.name);
            for step in &phase.steps {
                println!("    - {} ({})", step.id, 
                    if step.concurrency_safe { "parallel" } else { "sequential" });
            }
        }
    }
    
    pub fn to_json(&self) -> serde_json::Value {
        // Machine-readable output
        // ...
    }
}
~~~

### 3.2 Dependency Resolution

~~~rust
pub fn build_dependency_graph(
    installers: &[&dyn Installer]
) -> Result<DependencyGraph> {
    let mut graph = DiGraph::new();
    let mut node_map = HashMap::new();
    
    // Add nodes
    for installer in installers {
        let node = graph.add_node(installer.id());
        node_map.insert(installer.id(), node);
    }
    
    // Add edges (dependencies)
    for installer in installers {
        let from_node = node_map[installer.id()];
        for dep_id in installer.dependencies() {
            if let Some(&to_node) = node_map.get(dep_id) {
                graph.add_edge(from_node, to_node, ());
            }
        }
    }
    
    // Detect cycles
    if petgraph::algo::is_cyclic_directed(&graph) {
        return Err(BootstrapError::CyclicDependency);
    }
    
    Ok(DependencyGraph { graph, node_map })
}
~~~

---

## Phase 4: Concurrency & Parallelism

### 4.1 Safe Parallelization Strategy

**Parallel-safe operations:**
- Detection phase (read-only checks)
- Independent tool downloads (different artifacts)
- Version parsing (no side effects)

**Sequential-only operations:**
- Virtual environment creation (filesystem race)
- Package manager lock (apt/brew single-instance)
- PATH mutations (shell environment ordering)
- Installations with shared dependencies

**Additional concurrency requirements (MUST):**
- Use a **global concurrency limit** (e.g., `--jobs <N>`; default to a conservative value) to prevent saturating CI/network.
- Introduce **resource locks** so steps can declare shared resources they require (examples: `apt_lock`, `brew_lock`, `cache_lock`, `venv_lock`).
  - Even “parallel-safe” steps must not run concurrently if they require the same lock.


**Locked defaults:**
- Default `--jobs`:
  - CI mode: **2**
  - Interactive: `min(4, num_cpus)`
- Environment override: `BOOTSTRAP_JOBS=<N>`
- HTTP per-host concurrency limit: **2** concurrent requests per host


**Implementation:**
~~~rust
pub async fn execute_phase(
    phase: &Phase,
    ctx: &Context,
    registry: &InstallerRegistry,
) -> Result<Vec<StepResult>> {
    // MUST: also apply a global semaphore limit (jobs) and a lock manager for required_locks
    if phase.can_parallelize {
        // Use tokio::spawn for each concurrent-safe step
        let mut tasks = vec![];
        
        for step in &phase.steps {
            if step.concurrency_safe {
                let step = step.clone();
                let ctx = ctx.clone();
                tasks.push(tokio::spawn(async move {
                    execute_step(&step, &ctx).await
                }));
            }
        }
        
        // Await all parallel tasks
        let results = futures::future::join_all(tasks).await;
        // ...
    } else {
        // Sequential execution
        let mut results = vec![];
        for step in &phase.steps {
            results.push(execute_step(step, ctx).await?);
        }
        Ok(results)
    }
}
~~~

### 4.2 Retry Strategy

~~~rust
#[derive(Clone)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub initial_delay: Duration,
    pub max_delay: Duration,
    pub max_total_time: Duration,
    pub jitter: bool,
}

impl RetryPolicy {
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

// Retry classification is REQUIRED so we do not waste time retrying permanent failures.
#[derive(Clone, Copy, Debug)]
pub enum RetryClass {
    Transient,   // timeouts, 429, 5xx, connection reset
    Permanent,   // 404, invalid URL, auth failures
    Security,    // checksum/signature mismatch -> fail immediately
    Unsafe,      // partial-state detected -> do not blindly retry
}


// HARD REQUIREMENT: errors must be classified so only transient failures are retried.
fn classify_error(e: &anyhow::Error) -> RetryClass {
    // Examples:
    // - timeouts, connection reset, DNS temporary failure -> Transient
    // - HTTP 429/5xx -> Transient (respect Retry-After when present)
    // - HTTP 400/401/403/404, invalid URL, unsupported platform -> Permanent
    // - checksum/signature mismatch -> Security
    // - detected partial-state / non-idempotent hazard -> Unsafe
    // ...
    RetryClass::Transient
}

pub async fn retry_with_backoff<F, Fut, T>(
    policy: &RetryPolicy,
    operation: F,
) -> Result<T>
where
    F: Fn() -> Fut,
    Fut: Future<Output = Result<T>>,
{
    let mut attempts = 0;
    let mut delay = policy.initial_delay;
    let started = Instant::now();
    
    loop {
        attempts += 1;
        
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts >= policy.max_attempts => {
                return Err(e);
            }
            Err(e) => {
                match classify_error(&e.into()) {
                    RetryClass::Transient => { /* continue */ }
                    RetryClass::Permanent | RetryClass::Security | RetryClass::Unsafe => {
                        return Err(e);
                    }
                }

                // Add jitter
                if policy.jitter {
                    let jitter = rand::random::<f64>() * 0.3;
                    delay = Duration::from_secs_f64(
                        delay.as_secs_f64() * (1.0 + jitter)
                    );
                }
                
                // Enforce total retry budget to avoid infinite/long stalls.
                if started.elapsed() >= policy.max_total_time {
                    return Err(e);
                }
                tokio::time::sleep(delay).await;
                delay = (delay * 2).min(policy.max_delay);
            }
        }
    }
}
~~~

**Apply to:**
- Package metadata refresh: YES (idempotent)
- Artifact downloads: YES (idempotent)
- apt/brew install: NO (lock conflicts, partial state)
- Version detection: NO (fast, local)

**Additional retry rules (MUST):**
- Implement a classifier that maps failures to `RetryClass`.
  - Only `RetryClass::Transient` may be retried.
- Respect HTTP `Retry-After` headers when present (429/503), bounded by the retry budget.
  - `RetryClass::Security` must fail immediately.
- For package-manager lock contention (apt/brew):
  - Do **not** retry the install itself.
  - Instead, implement an explicit **lock-wait with backoff** (sequential) and then proceed once the lock clears.
  - Max lock-wait time: CI=60s; Interactive=180s.

---

## Phase 5: Progress UI

**Policy (LOCKED):**
- v1 uses `indicatif` only (no ratatui/full-screen TUI).
- CI/non-TTY output must be clean and parseable (no ANSI styling).

### 5.1 Multi-Task Progress Display

**Library stack:**
- `indicatif` for progress bars/spinners
- Custom multi-line renderer for concurrent tasks

~~~rust
pub struct ProgressReporter {
    multi: MultiProgress,
    tasks: Arc<Mutex<HashMap<String, ProgressTask>>>,
    mode: ProgressMode,
}

pub enum ProgressMode {
    Interactive,  // TTY with fancy UI
    Ci,           // Plain text, periodic updates
    Json,         // Structured events
}

pub struct ProgressTask {
    bar: ProgressBar,
    status: TaskStatus,
    elapsed: Instant,
}

pub enum TaskStatus {
    Pending,
    Running,
    Success,
    Failed { error: String },
    Skipped { reason: String },
}

impl ProgressReporter {
    pub fn new(mode: ProgressMode) -> Self {
        let multi = MultiProgress::new();
        Self {
            multi,
            tasks: Arc::new(Mutex::new(HashMap::new())),
            mode,
        }
    }
    
    pub fn add_task(&self, id: String, name: String) -> TaskHandle {
        let bar = self.multi.add(ProgressBar::new_spinner());
        // NOTE: Avoid hard-coded ANSI styling; style only in Interactive mode and degrade cleanly in CI/non-TTY.
        bar.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner} [{elapsed_precise}] {msg}")
                .unwrap()
        );
        bar.set_message(format!("{}: Pending", name));
        
        let task = ProgressTask {
            bar,
            status: TaskStatus::Pending,
            elapsed: Instant::now(),
        };
        
        self.tasks.lock().unwrap().insert(id.clone(), task);
        
        TaskHandle {
            id,
            reporter: self.clone(),
        }
    }
}

pub struct TaskHandle {
    id: String,
    reporter: ProgressReporter,
}

impl TaskHandle {
    pub fn set_running(&self, msg: &str) {
        // Update task status and UI
    }
    
    pub fn set_success(&self, msg: &str) {
        // Mark complete with checkmark
    }
    
    pub fn set_failed(&self, error: &str) {
        // Mark failed with X
    }
}
~~~

### 5.2 TTY vs Non-TTY Behavior

~~~rust
impl ProgressMode {
    pub fn auto_detect() -> Self {
        if atty::is(atty::Stream::Stdout) {
            ProgressMode::Interactive
        } else {
            ProgressMode::Ci
        }
    }
}

// In CI mode:
impl ProgressReporter {
    fn ci_print(&self, msg: String) {
        // Periodic plain-text updates
        println!("[{}] {}", chrono::Utc::now().format("%H:%M:%S"), msg);
    }
}
~~~

### 5.3 JSON Event Stream

~~~rust
#[derive(Serialize)]
#[serde(tag = "type")]
pub enum ProgressEvent {
    PlanComputed {
        plan: ExecutionPlan,
    },
    PhaseStarted {
        phase: String,
    },
    TaskStarted {
        task_id: String,
        name: String,
    },
    TaskProgress {
        task_id: String,
        progress: f32,
        message: Option<String>,
    },
    TaskCompleted {
        task_id: String,
        status: TaskStatus,
        duration: Duration,
    },
    PhaseCompleted {
        phase: String,
        duration: Duration,
    },
    BootstrapCompleted {
        total_duration: Duration,
        exit_code: i32,
    },
}

// Emit to stdout in --json mode
~~~

---

## Phase 6: Configuration & Profiles

### 6.1 Configuration File

**Location:** `<repo>/.bootstrap.toml`

**Policy (LOCKED):**
- The binary supports defaults when `.bootstrap.toml` is absent.
- **For this repo in CI:** `.bootstrap.toml` is **required**. If missing in CI mode, exit with `UsageError (1)` and a clear message.

~~~toml
[profile.dev]
tools = [
    "python-black",
    "python-ruff",
    "python-pylint",
    "yamllint",
    "pytest",
    "actionlint",
    "ripgrep",
    "shellcheck",
    "shfmt",
]

[profile.ci]
tools = [
    "python-black",
    "python-ruff",
    "python-pylint",
    "yamllint",
    "actionlint",
    "ripgrep",
]

[profile.full]
tools = [
    # all tools
]

[tool.actionlint]
version = "1.7.10"  # Pin specific version

[tool.ripgrep]
min_version = "14.0.0"
~~~

### 6.2 Profile Resolution

~~~rust
pub struct Config {
    profiles: HashMap<String, Profile>,
    tool_configs: HashMap<String, ToolConfig>,
}

pub struct Profile {
    pub name: String,
    pub tools: Vec<String>,
}

pub struct ToolConfig {
    pub version: Option<Version>,
    pub min_version: Option<Version>,
    pub install_args: Vec<String>,
}

impl Config {
    pub fn load(repo_root: &Path) -> Result<Self> {
        let config_path = repo_root.join(".bootstrap.toml");
        if config_path.exists() {
            // Parse TOML
        } else {
            // Return default config
            Self::default()
        }
    }
    
    pub fn resolve_tools(&self, profile: &str, overrides: &[String]) 
        -> Result<Vec<String>> 
    {
        let mut tools = self.profiles.get(profile)
            .map(|p| p.tools.clone())
            .unwrap_or_default();
        
        tools.extend_from_slice(overrides);
        Ok(tools)
    }
}
~~~

---

## Phase 7: Dry-Run & Checkpointing

**Policy (LOCKED):**
- Checkpointing/resume is **OFF by default**.
- Enable only via `--checkpoint` (write state) and `--resume` (resume from state).
- State files live outside the repo by default (cache dirs), unless explicitly overridden.

### 7.1 Dry-Run Implementation

~~~rust
impl Context {
    pub async fn execute_command(&self, cmd: &Command) -> Result<Output> {
        if self.dry_run {
            println!("[DRY-RUN] Would execute: {:?}", cmd);
            return Ok(Output {
                status: ExitStatus::from_raw(0),
                stdout: vec![],
                stderr: vec![],
            });
        }
        
        // Real execution
        cmd.output().await
            .map_err(|e| BootstrapError::CommandFailed(e))
    }
}
~~~

### 7.2 Checkpoint State

~~~rust
#[derive(Serialize, Deserialize)]
pub struct Checkpoint {
    pub timestamp: DateTime<Utc>,
    pub plan_hash: String,
    pub completed_steps: Vec<String>,
    pub failed_steps: Vec<String>,
}

impl Checkpoint {
    pub fn save(&self, repo_root: &Path) -> Result<()> {
        // Default: store state outside the repo to avoid dirty working trees.
        // Prefer XDG cache on Linux and macOS caches on macOS.
        // Allow override via a CLI flag like `--checkpoint-file`.
        let path = default_checkpoint_path(repo_root)?;
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }
    
    pub fn load(repo_root: &Path) -> Result<Option<Self>> {
        let path = default_checkpoint_path(repo_root)?;
        if !path.exists() {
            return Ok(None);
        }
        
        let json = std::fs::read_to_string(path)?;
        let checkpoint = serde_json::from_str(&json)?;
        Ok(Some(checkpoint))
    }
    
    pub fn is_valid(&self, current_plan: &ExecutionPlan) -> bool {
        // Check if plan hash matches
        self.plan_hash == current_plan.compute_hash()
    }
}
~~~

---

## Phase 8: Platform Abstractions

### 8.1 Package Manager Abstraction

~~~rust
#[async_trait]
pub trait PackageManagerOps: Send + Sync {
    async fn refresh(&self) -> Result<()>;
    async fn install(&self, package: &str, version: Option<&str>) -> Result<()>;
    async fn is_installed(&self, package: &str) -> Result<bool>;
}

pub struct HomebrewOps;

#[async_trait]
impl PackageManagerOps for HomebrewOps {
    async fn install(&self, package: &str, version: Option<&str>) -> Result<()> {
        let mut cmd = Command::new("brew");
        cmd.arg("install").arg(package);
        
        // NOTE: Homebrew does not support arbitrary `package@<version>` for all formulae.
        // Only use a versioned formula when it exists (e.g., `python@3.12`).
        // If an exact pin is required and no versioned formula exists, prefer a direct-download installer
        // with checksum verification (see supply-chain hardening rules).
        if let Some(_v) = version {
            // Intentionally not implemented as `package@version` by default.
            // A real implementation must detect whether a versioned formula exists.
        }
        
        let output = cmd.output().await?;
        if !output.status.success() {
            return Err(BootstrapError::InstallFailed {
                tool: package.to_string(),
                exit_code: output.status.code().unwrap_or(-1),
                stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            });
        }
        Ok(())
    }
}

pub struct AptOps; // MUST: use non-interactive apt-get flags and deterministic behavior in CI
// Similar implementation for apt-get
~~~


**Apt requirements (MUST):**
- Use non-interactive mode (e.g., `DEBIAN_FRONTEND=noninteractive`) and deterministic flags.
- In CI, use `sudo -n` (or equivalent) so privilege prompts fail fast instead of hanging.
- Do not retry installs; only lock-wait/backoff is allowed for lock contention.


### 8.2 OS Detection

~~~rust
pub fn detect_os() -> Result<OsType> {
    #[cfg(target_os = "macos")]
    return Ok(OsType::MacOS);
    
    #[cfg(target_os = "linux")]
    return Ok(OsType::Linux);
    
    #[cfg(target_os = "windows")]
    return Ok(OsType::Windows);
    
    #[cfg(not(any(
        target_os = "macos",
        target_os = "linux",
        target_os = "windows"
    )))]
    Err(BootstrapError::UnsupportedOs)
}

pub fn detect_package_manager(os: &OsType) -> PackageManager {
    match os {
        OsType::MacOS => {
            if Command::new("brew").arg("--version").output().is_ok() {
                PackageManager::Homebrew
            } else {
                PackageManager::None
            }
        }
        OsType::Linux => {
            if Command::new("apt-get").arg("--version").output().is_ok() {
                PackageManager::Apt
            } else if Command::new("snap").arg("version").output().is_ok() {
                PackageManager::Snap
            } else {
                PackageManager::None
            }
        }
        _ => PackageManager::None,
    }
}
~~~

---

## Phase 9: Self-Diagnostics

**Locked behavior:**
- Default: WARN does not fail the command.
- `doctor --strict` (and CI when configured) treats WARN as FAIL.

### 9.1 Doctor Command

~~~rust
pub async fn doctor(ctx: &Context) -> Result<DiagnosticReport> {
    let mut report = DiagnosticReport::default();
    
    // Check repo root
    report.add_check("Repository", check_repo(&ctx.repo_root).await);
    
    // Check package manager
    report.add_check("Package Manager", 
        check_package_manager(&ctx.package_manager).await);
    
    // Check Python
    report.add_check("Python", check_python().await);
    
    // Check network
    report.add_check("Network", check_network().await);
    
    // Check disk space
    report.add_check("Disk Space", check_disk_space(&ctx.repo_root).await);
    
    // Check permissions
    report.add_check("Permissions", check_permissions().await);
    
    Ok(report)
}

pub struct DiagnosticReport {
    pub checks: Vec<DiagnosticCheck>,
}

pub struct DiagnosticCheck {
    pub name: String,
    pub status: CheckStatus,
    pub message: String,
    pub remediation: Option<String>,
}

pub enum CheckStatus {
    Pass,
    Warn,
    Fail,
}

impl DiagnosticReport {
    pub fn print(&self) {
        for check in &self.checks {
            let icon = match check.status {
                CheckStatus::Pass => "✓",
                CheckStatus::Warn => "⚠",
                CheckStatus::Fail => "✗",
            };
            println!("{} {}: {}", icon, check.name, check.message);
            if let Some(remediation) = &check.remediation {
                println!("  → {}", remediation);
            }
        }
    }
    
    pub fn exit_code(&self) -> ExitCode {
        if self.checks.iter().any(|c| matches!(c.status, CheckStatus::Fail)) {
            ExitCode::VerificationFailed
        } else {
            ExitCode::Success
        }
    }
}
~~~

---

## Phase 10: Migration Strategy

### 10.1 Bash Wrapper (Transition Period)

**Keep existing `bootstrap-repo-lint-toolchain.sh` as thin wrapper (with an explicit legacy escape hatch):**

~~~bash
#!/usr/bin/env bash
# Wrapper for Rust bootstrapper (transition)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Explicit escape hatch
if [ "${BOOTSTRAP_FORCE_LEGACY:-0}" = "1" ]; then
    echo "[WARN] BOOTSTRAP_FORCE_LEGACY=1 set; using legacy Bash version"
    exec "$REPO_ROOT/scripts/.legacy/bootstrap-repo-lint-toolchain.sh" "$@"
fi

# Resolution order:
# 1) $BOOTSTRAP_BIN (explicit)
# 2) $REPO_ROOT/.bootstrap/bin/bootstrap (downloaded/prebuilt)
# 3) $REPO_ROOT/target/release/bootstrap (dev-only)
# 4) legacy bash

CANDIDATES=()
if [ -n "${BOOTSTRAP_BIN:-}" ]; then
    CANDIDATES+=("$BOOTSTRAP_BIN")
fi
CANDIDATES+=("$REPO_ROOT/.bootstrap/bin/bootstrap")
CANDIDATES+=("$REPO_ROOT/target/release/bootstrap")

for bin in "${CANDIDATES[@]}"; do
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        exec "$bin" install "$@"
    fi
done

echo "[WARN] Rust bootstrapper not found, using legacy Bash version"
exec "$REPO_ROOT/scripts/.legacy/bootstrap-repo-lint-toolchain.sh" "$@"
~~~

### 10.2 Phased Rollout

**Phase 1: Parallel development**
- Develop Rust version with feature parity
- Run both in CI for comparison
- Fix behavioral differences

**Phase 2: Opt-in**
- Make Rust version available
- Document how to use it
- Gather feedback

**Phase 3: Default**
- Rust becomes default
- Bash available as fallback
- Monitor for issues

**Phase 4: Deprecation**
- Remove Bash fallback
- Archive legacy script
- Update all documentation

### 10.3 Behavioral Parity Testing

~~~rust
// Integration test comparing Rust vs Bash output
#[tokio::test]
async fn test_parity_with_bash() {
    let temp_repo = create_test_repo();
    
    // Run Bash version
    let bash_output = run_bash_bootstrap(&temp_repo).await;
    
    // Run Rust version
    let rust_output = run_rust_bootstrap(&temp_repo).await;
    
    // Compare:
    assert_eq!(bash_output.exit_code, rust_output.exit_code);
    assert_eq!(bash_output.installed_tools, rust_output.installed_tools);
    assert!(rust_output.duration <= bash_output.duration * 1.5);
}
~~~

---

## Phase 11: Build & Distribution

### 11.1 Static Binary Build

~~~toml
# Cargo.toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true

[dependencies]
# Avoid dynamic linking where possible
reqwest = { version = "0.11", default-features = false, features = ["rustls-tls", "gzip", "brotli"] }
# Async runtime (required)
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
~~~

**Locked decision:** prefer `rustls` over OpenSSL to reduce cross-platform build pain.


**Build for multiple targets:**
~~~bash
# Linux (musl for static linking)
cargo build --release --target x86_64-unknown-linux-musl

# macOS
cargo build --release --target x86_64-apple-darwin
cargo build --release --target aarch64-apple-darwin
~~~

### 11.2 CI Integration

~~~yaml
# .github/workflows/bootstrap-test.yml
jobs:
  build-rust-bootstrapper:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rust-lang/setup-rust-toolchain@v1
      - run: cargo build --release
      - run: ./target/release/bootstrap install --profile ci --dry-run
      - run: ./target/release/bootstrap doctor
~~~

---

## Non-Goals & Constraints

### Explicit Non-Goals

1. **Windows support in v1**
   - Focus on macOS/Linux first
   - Windows support is additive later

2. **Plugin system**
   - Static registry only
   - No dynamic loading
   - Simplifies distribution

3. **GUI interface**
   - CLI only
   - Rich TUI is acceptable
   - No graphical desktop app

4. **Parallel package manager calls**
   - Too risky (lock conflicts)
   - Keep package manager operations sequential

### Constraints

1. **Zero external runtime dependencies**
   - Must work on fresh macOS/Linux
   - No Ruby, Python, or Node required to run bootstrapper itself

2. **Backwards compatibility**
   - Must preserve all exit codes
   - Must preserve CLI interface during transition

3. **CI headless mode**
   - Must work without TTY
   - Must produce parseable logs

4. **Downgrades are disallowed by default**
   - Downgrades require explicit `--allow-downgrade`.
   - CI must not perform downgrades unless explicitly configured.

5. **Caching is per-user and checksum-protected**
   - Cache keys must include tool/version/platform/arch.
   - Direct downloads must be checksum verified before entering cache.

6. **Offline mode is supported**
   - `--offline` uses cache only; if required artifacts are missing, fail fast.

7. **Supply-chain hardening is mandatory for direct downloads**
   - Checksums are required for any direct-download installer.
   - Signature verification is optional when upstream provides it.


---

## Success Metrics

1. **Performance:**
   - Performance is a **goal**, not a release gate.
   - Target 30–50% faster than Bash where safe parallelism applies (measured across CI runs).

2. **Reliability:**
   - Zero flaky failures in CI
   - All exit codes deterministic

3. **Maintainability:**
   - Adding new tool takes < 50 LOC
   - No platform-specific bugs for 6 months

4. **User Experience:**
   - Live progress UI rated "clear" by 5+ users
   - Doctor command resolves 80%+ of issues

---

## Risk Mitigation

### Risk: Behavioral Divergence

**Mitigation:**
- Comprehensive parity tests
- Run both versions in CI
- Document all intentional differences

### Risk: Performance Regression

**Mitigation:**
- Benchmark every PR
- Profile to find bottlenecks
- Have "fast" CI profile for quick feedback

### Risk: Platform-Specific Bugs

**Mitigation:**
- Test matrix: macOS x Linux x (Homebrew|apt|snap)
- Virtualized test environments
- User beta testing program

### Risk: Maintenance Burden During Transition

**Mitigation:**
- Minimize changes to Bash during Rust development
- Feature freeze Bash once Rust reaches parity
- Time-boxed transition (6 months max)

---

## Timeline Estimate

**Optimistic (1 developer, full-time):**
- Phase 1-2 (Core): 2 weeks
- Phase 3-4 (Concurrency): 1 week
- Phase 5 (UI): 1 week
- Phase 6-7 (Config/Features): 1 week
- Phase 8-9 (Platform/Diagnostics): 1 week
- Phase 10 (Migration): 2 weeks
- Testing/Polish: 2 weeks

**Total: ~10 weeks**

**Realistic (1 developer, part-time):**
- 20-24 weeks

**Conservative (accounting for unknowns):**
- 6 months to production-ready

---

## Appendices

### Appendix A: Example Installers

**RipgrepInstaller:**
~~~rust
pub struct RipgrepInstaller;

#[async_trait]
impl Installer for RipgrepInstaller {
    fn id(&self) -> &'static str { "ripgrep" }
    fn name(&self) -> &'static str { "ripgrep" }
    fn description(&self) -> &'static str { 
        "Fast recursive search tool (REQUIRED)"
    }
    
    fn concurrency_safe(&self) -> bool { true }
    
    async fn detect(&self, _ctx: &Context) -> Result<Option<Version>> {
        let output = Command::new("rg").arg("--version").output().await?;
        if output.status.success() {
            let version = parse_version(&output.stdout)?;
            Ok(Some(version))
        } else {
            Ok(None)
        }
    }
    
    async fn install(&self, ctx: &Context) -> Result<InstallResult> {
        match ctx.package_manager {
            PackageManager::Homebrew => {
                ctx.run_command(Command::new("brew")
                    .arg("install")
                    .arg("ripgrep")).await?;
            }
            PackageManager::Apt => {
                ctx.run_command(Command::new("sudo")
                    .arg("apt-get")
                    .arg("install")
                    .arg("-y")
                    .arg("ripgrep")).await?;
            }
            _ => return Err(BootstrapError::NoPackageManager),
        }
        
        let version = self.detect(ctx).await?
            .ok_or(BootstrapError::InstallVerificationFailed)?;
        
        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec![],
        })
    }
    
    async fn verify(&self, ctx: &Context) -> Result<VerifyResult> {
        match self.detect(ctx).await? {
            Some(version) => Ok(VerifyResult {
                success: true,
                version: Some(version),
                issues: vec![],
            }),
            None => Ok(VerifyResult {
                success: false,
                version: None,
                issues: vec!["ripgrep not found on PATH".to_string()],
            }),
        }
    }
}
~~~

### Appendix B: Recommended Crates

- **CLI:** `clap` (argument parsing)
- **Async:** `tokio` (runtime)
- **Progress:** `indicatif` (progress bars)
- **Config:** `serde`, `toml` (configuration)
- **Error:** `thiserror`, `anyhow` (error handling)
- **Graph:** `petgraph` (dependency resolution)
- **Version:** `semver` (version comparison)
- **Logging:** `tracing` (structured logging)
- **HTTP:** `reqwest` (downloads)
- **TTY:** `atty` (terminal detection)

### Appendix C: Open Questions

1. Plugin system: **NO** (v1 uses static registry only).
2. Windows support: **NO** (v1 is macOS/Linux only).
3. Version downgrades: **DISALLOWED by default**; require `--allow-downgrade`.
4. Cache scope: **per-user**, keyed by tool/version/platform/arch and checksum-protected.
5. Parallel downloads: bounded by `--jobs` plus per-host concurrency limit (2).
6. Offline mode: **SUPPORTED** via `--offline` (cache-only; fail if missing).

---
