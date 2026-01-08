# Rust Migration Plan: Modular Toolchain Bootstrapper

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

**Example CLI:**

```bash
bootstrap install [--profile dev|ci|full] [--shell] [--powershell] [--perl]
bootstrap doctor [--json]
bootstrap verify
```

### 1.2 Exit Code Constants

```rust
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
```

### 1.3 Error Type Hierarchy

```rust
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
```

---

## Phase 2: Installer Registry & Trait

### 2.1 Core Installer Interface

```rust
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
```

### 2.2 Context Object

```rust
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
```

### 2.3 Static Registry

```rust
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
```

---

## Phase 3: Execution Plan & Dependency Graph

### 3.1 Plan Computation

```rust
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
```

### 3.2 Dependency Resolution

```rust
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
```

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

**Implementation:**

```rust
pub async fn execute_phase(
    phase: &Phase,
    ctx: &Context,
    registry: &InstallerRegistry,
) -> Result<Vec<StepResult>> {
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
```

### 4.2 Retry Strategy

```rust
#[derive(Clone)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub initial_delay: Duration,
    pub max_delay: Duration,
    pub jitter: bool,
}

impl RetryPolicy {
    pub fn network_default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_secs(1),
            max_delay: Duration::from_secs(30),
            jitter: true,
        }
    }
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
    
    loop {
        attempts += 1;
        
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts >= policy.max_attempts => {
                return Err(e);
            }
            Err(_) => {
                // Add jitter
                if policy.jitter {
                    let jitter = rand::random::<f64>() * 0.3;
                    delay = Duration::from_secs_f64(
                        delay.as_secs_f64() * (1.0 + jitter)
                    );
                }
                
                tokio::time::sleep(delay).await;
                delay = (delay * 2).min(policy.max_delay);
            }
        }
    }
}
```

**Apply to:**

- Package metadata refresh: YES (idempotent)
- Artifact downloads: YES (idempotent)
- apt/brew install: NO (lock conflicts, partial state)
- Version detection: NO (fast, local)

---

## Phase 5: Progress UI

### 5.1 Multi-Task Progress Display

**Library stack:**

- `indicatif` for progress bars/spinners
- Custom multi-line renderer for concurrent tasks

```rust
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
        bar.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner:.green} [{elapsed_precise}] {msg}")
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
```

### 5.2 TTY vs Non-TTY Behavior

```rust
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
```

### 5.3 JSON Event Stream

```rust
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
```

---

## Phase 6: Configuration & Profiles

### 6.1 Configuration File

**Location:** `<repo>/.bootstrap.toml` (optional)

```toml
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
```

### 6.2 Profile Resolution

```rust
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
```

---

## Phase 7: Dry-Run & Checkpointing

### 7.1 Dry-Run Implementation

```rust
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
```

### 7.2 Checkpoint State

```rust
#[derive(Serialize, Deserialize)]
pub struct Checkpoint {
    pub timestamp: DateTime<Utc>,
    pub plan_hash: String,
    pub completed_steps: Vec<String>,
    pub failed_steps: Vec<String>,
}

impl Checkpoint {
    pub fn save(&self, repo_root: &Path) -> Result<()> {
        let path = repo_root.join(".bootstrap.checkpoint");
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }
    
    pub fn load(repo_root: &Path) -> Result<Option<Self>> {
        let path = repo_root.join(".bootstrap.checkpoint");
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
```

---

## Phase 8: Platform Abstractions

### 8.1 Package Manager Abstraction

```rust
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
        
        if let Some(v) = version {
            cmd.arg(format!("{}@{}", package, v));
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

pub struct AptOps;
// Similar implementation for apt-get
```

### 8.2 OS Detection

```rust
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
```

---

## Phase 9: Self-Diagnostics

### 9.1 Doctor Command

```rust
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
```

---

## Phase 10: Migration Strategy

### 10.1 Bash Wrapper (Transition Period)

**Keep existing `bootstrap-repo-lint-toolchain.sh` as thin wrapper:**

```bash
#!/usr/bin/env bash
# Wrapper for Rust bootstrapper (transition)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if Rust binary exists
BOOTSTRAP_BIN="$REPO_ROOT/target/release/bootstrap"

if [ -f "$BOOTSTRAP_BIN" ]; then
    # Use Rust implementation
    exec "$BOOTSTRAP_BIN" install "$@"
else
    # Fallback to Bash (original script moved to .legacy)
    echo "[WARN] Rust bootstrapper not found, using legacy Bash version"
    exec "$REPO_ROOT/scripts/.legacy/bootstrap-repo-lint-toolchain.sh" "$@"
fi
```

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

```rust
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
```

---

## Phase 11: Build & Distribution

### 11.1 Static Binary Build

```toml
# Cargo.toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true

[dependencies]
# Avoid dynamic linking where possible
openssl = { version = "0.10", features = ["vendored"] }
```

**Build for multiple targets:**

```bash
# Linux (musl for static linking)
cargo build --release --target x86_64-unknown-linux-musl

# macOS
cargo build --release --target x86_64-apple-darwin
cargo build --release --target aarch64-apple-darwin
```

### 11.2 CI Integration

```yaml
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
```

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

---

## Success Metrics

1. **Performance:**
   - 30-50% faster than Bash (via parallelism)
   - Measured in CI over 20 runs

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

```rust
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
```

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

1. Should we support user-defined installer plugins (future)?
2. How to handle version downgrades (disallow? warn?)?
3. Should cache be per-user or per-repo?
4. How aggressive should parallel downloads be (respect bandwidth)?
5. Should we vendor dependencies for fully offline builds?
