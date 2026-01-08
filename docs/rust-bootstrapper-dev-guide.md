# Rust Bootstrapper Developer Documentation

## Overview

This document provides technical details for developers working on the Rust bootstrapper codebase.

## Project Structure

```
rust/
├── Cargo.toml              # Project manifest and dependencies
├── Cargo.lock              # Dependency lockfile
├── src/
│   ├── main.rs             # CLI entry point
│   └── bootstrap_v2/       # Core implementation
│       ├── mod.rs          # Module exports
│       ├── cli.rs          # Command-line interface (clap)
│       ├── exit_codes.rs   # Exit code constants
│       ├── errors.rs       # Error type hierarchy
│       ├── context.rs      # Execution context
│       ├── config.rs       # Configuration (.bootstrap.toml)
│       ├── installer.rs    # Installer trait and registry
│       ├── plan.rs         # Execution planning
│       ├── executor.rs     # Phase execution
│       ├── progress.rs     # Progress UI (indicatif)
│       ├── retry.rs        # Retry policy and backoff
│       ├── lock.rs         # Resource locking
│       ├── checkpoint.rs   # Checkpoint/resume
│       ├── doctor.rs       # Diagnostics
│       ├── platform.rs     # OS and package manager detection
│       ├── package_manager.rs  # Package manager abstractions
│       └── installers/     # Tool-specific installers
│           ├── mod.rs
│           ├── python_tools.rs
│           ├── shell_tools.rs
│           ├── perl_tools.rs
│           ├── powershell_tools.rs
│           ├── actionlint.rs
│           ├── ripgrep.rs
│           └── shellcheck.rs
├── tests/
│   └── integration_tests.rs  # Integration test suite
└── target/                # Build output
    ├── debug/
    └── release/
```

## Architecture

### Design Principles

1. **Determinism over convenience**: Exit codes are deterministic and match the Bash contract
2. **Fail-fast, always**: No silent failures or "warn and continue" for required components
3. **Idempotency governs retries**: Only safe operations are retried
4. **Concurrency only where safe**: Parallelism respects resource locks
5. **Progress UI must be honest**: Clear, real-time communication
6. **No repo pollution by default**: Caches live outside the repo
7. **Parity + tests are mandatory**: Behavior must match Bash version
8. **Rule of Three**: Abstract shared logic after 3 instances

### Core Components

#### 1. Exit Codes (`exit_codes.rs`)

All exit codes match the Bash bootstrapper:

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
```

#### 2. Error Hierarchy (`errors.rs`)

Typed errors with `thiserror`:

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

#### 3. Installer Trait (`installer.rs`)

Core abstraction for tools:

```rust
#[async_trait]
pub trait Installer: Send + Sync {
    fn id(&self) -> &'static str;
    fn name(&self) -> &'static str;
    fn description(&self) -> &'static str;
    fn dependencies(&self) -> Vec<&'static str>;
    fn concurrency_safe(&self) -> bool;

    async fn detect(&self, ctx: &Context) -> Result<Option<Version>>;
    async fn install(&self, ctx: &Context) -> Result<InstallResult>;
    async fn verify(&self, ctx: &Context) -> Result<VerifyResult>;
}
```

#### 4. Installer Registry (`installer.rs`)

Static registry with dependency resolution:

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
        registry.register(Box::new(RipgrepInstaller));
        registry.register(Box::new(PythonBlackInstaller));
        // ... all tools

        registry
    }

    pub fn resolve_dependencies(&self, ids: &[&str])
        -> Result<Vec<&dyn Installer>>
    {
        // Topological sort using petgraph
    }
}
```

#### 5. Execution Planning (`plan.rs`)

Builds execution plan with phases:

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
    pub required_locks: Vec<String>,
}
```

#### 6. Concurrency and Locking (`executor.rs`, `lock.rs`)

Safe parallel execution:

```rust
pub async fn execute_phase(
    phase: &Phase,
    ctx: &Context,
    registry: &InstallerRegistry,
) -> Result<Vec<StepResult>> {
    if phase.can_parallelize {
        // Parallel execution with semaphore and locks
        let semaphore = Arc::new(Semaphore::new(ctx.jobs));
        let mut tasks = vec![];

        for step in &phase.steps {
            let permit = semaphore.clone().acquire_owned().await?;
            let lock = acquire_locks(&step.required_locks).await?;

            tasks.push(tokio::spawn(async move {
                let _permit = permit;
                let _lock = lock;
                execute_step(&step, &ctx).await
            }));
        }

        futures::future::join_all(tasks).await
    } else {
        // Sequential execution
        // ...
    }
}
```

#### 7. Retry Policy (`retry.rs`)

Exponential backoff with error classification:

```rust
#[derive(Clone, Copy, Debug)]
pub enum RetryClass {
    Transient,   // timeouts, 429, 5xx
    Permanent,   // 404, auth failures
    Security,    // checksum mismatch (never retry)
    Unsafe,      // partial-state (never retry)
}

pub async fn retry_with_backoff<F, Fut, T>(
    policy: &RetryPolicy,
    operation: F,
) -> Result<T>
where
    F: Fn() -> Fut,
    Fut: Future<Output = Result<T>>,
{
    // Only retry Transient errors
    // Respect HTTP Retry-After headers
    // Enforce total retry budget
}
```

## Development Workflow

### Building

```bash
# Debug build (bootstrap-repo-cli)
cd rust
cargo build -p bootstrap-repo-cli

# Release build (optimized)
cargo build --release -p bootstrap-repo-cli

# Build safe-run package
cargo build -p safe-run

# Check without building
cargo check
```

### Testing

```bash
# Run all tests for bootstrap-repo-cli
cargo test -p bootstrap-repo-cli

# Run with output
cargo test -p bootstrap-repo-cli -- --nocapture

# Run specific test
cargo test -p bootstrap-repo-cli test_full_install_flow

# Integration tests only
cargo test -p bootstrap-repo-cli --test integration_tests
```

### Linting

```bash
# Clippy (lint)
cargo clippy --all-targets --all-features

# Format check
cargo fmt --check

# Format apply
cargo fmt
```

### Documentation

```bash
# Generate documentation
cargo doc --no-deps --open

# Document private items
cargo doc --no-deps --document-private-items
```

## Adding a New Installer

### 1. Create Installer Module

Create `src/bootstrap_v2/installers/my_tool.rs`:

```rust
use async_trait::async_trait;
use crate::bootstrap_v2::{
    installer::{Installer, InstallResult, VerifyResult},
    context::Context,
    errors::BootstrapError,
};
use semver::Version;
use std::process::Command;

pub struct MyToolInstaller;

#[async_trait]
impl Installer for MyToolInstaller {
    fn id(&self) -> &'static str {
        "my-tool"
    }

    fn name(&self) -> &'static str {
        "MyTool"
    }

    fn description(&self) -> &'static str {
        "Description of my tool"
    }

    fn dependencies(&self) -> Vec<&'static str> {
        vec![] // Or list dependency IDs
    }

    fn concurrency_safe(&self) -> bool {
        true // Or false if requires exclusive access
    }

    async fn detect(&self, _ctx: &Context) -> Result<Option<Version>, BootstrapError> {
        // Check if tool is installed
        let output = Command::new("my-tool")
            .arg("--version")
            .output()?;

        if output.status.success() {
            let version_str = String::from_utf8_lossy(&output.stdout);
            let version = parse_version(&version_str)?;
            Ok(Some(version))
        } else {
            Ok(None)
        }
    }

    async fn install(&self, ctx: &Context) -> Result<InstallResult, BootstrapError> {
        // Install using package manager
        match &ctx.package_manager {
            PackageManager::Homebrew => {
                Command::new("brew")
                    .arg("install")
                    .arg("my-tool")
                    .status()?;
            }
            PackageManager::Apt => {
                Command::new("sudo")
                    .args(&["apt-get", "install", "-y", "my-tool"])
                    .status()?;
            }
            _ => return Err(BootstrapError::UnsupportedPackageManager),
        }

        // Verify installation
        let version = self.detect(ctx).await?
            .ok_or(BootstrapError::InstallVerificationFailed)?;

        Ok(InstallResult {
            version,
            installed_new: true,
            log_messages: vec![],
        })
    }

    async fn verify(&self, ctx: &Context) -> Result<VerifyResult, BootstrapError> {
        match self.detect(ctx).await? {
            Some(version) => Ok(VerifyResult {
                success: true,
                version: Some(version),
                issues: vec![],
            }),
            None => Ok(VerifyResult {
                success: false,
                version: None,
                issues: vec!["my-tool not found".to_string()],
            }),
        }
    }
}
```

### 2. Register Installer

In `src/bootstrap_v2/installers/mod.rs`:

```rust
mod my_tool;
pub use my_tool::MyToolInstaller;
```

In `src/bootstrap_v2/installer.rs`:

```rust
impl InstallerRegistry {
    pub fn new() -> Self {
        let mut registry = Self {
            installers: HashMap::new(),
        };

        // ... existing installers
        registry.register(Box::new(MyToolInstaller));

        registry
    }
}
```

### 3. Add Tests

In `tests/integration_tests.rs`:

```rust
#[tokio::test]
async fn test_my_tool_installer() {
    let ctx = create_test_context();
    let installer = MyToolInstaller;

    // Test detection
    let detected = installer.detect(&ctx).await;
    assert!(detected.is_ok());

    // Test installation (dry-run)
    let result = installer.install(&ctx).await;
    assert!(result.is_ok());

    // Test verification
    let verify = installer.verify(&ctx).await;
    assert!(verify.is_ok());
}
```

### 4. Update Documentation

Add to `.bootstrap.toml` examples and user manual.

## Testing Strategy

### Unit Tests

Located in each module:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exit_code_mapping() {
        let error = BootstrapError::NotInRepo;
        assert_eq!(error.exit_code(), ExitCode::NotInRepo);
    }
}
```

### Integration Tests

Located in `tests/integration_tests.rs`:

```rust
#[tokio::test]
async fn test_full_install_flow_dry_run() {
    let temp_dir = tempfile::tempdir().unwrap();
    let ctx = create_test_context_in(&temp_dir);

    // Test full flow
    let result = run_install(&ctx).await;
    assert!(result.is_ok());
}
```

### Parity Tests

Compare Rust vs Bash behavior:

```rust
#[tokio::test]
async fn test_parity_with_bash() {
    let bash_output = run_bash_bootstrap().await;
    let rust_output = run_rust_bootstrap().await;

    assert_eq!(bash_output.exit_code, rust_output.exit_code);
    assert_eq!(bash_output.installed_tools, rust_output.installed_tools);
}
```

## Debugging

### Enable Verbose Logging

```bash
RUST_LOG=debug cargo run -- install --verbose
```

### Use `dbg!` Macro

```rust
dbg!(&execution_plan);
```

### Tokio Console (Advanced)

```toml
[dependencies]
console-subscriber = "0.1"
tokio = { version = "1", features = ["tracing"] }
```

```rust
console_subscriber::init();
```

```bash
tokio-console
```

## Performance Profiling

### Flamegraph

```bash
cargo install flamegraph
cargo flamegraph --bin bootstrap-repo-cli -- install --dry-run
```

### Benchmarking

```bash
./scripts/benchmark-bootstrap.sh --iterations 10
```

## Release Process

### 1. Version Bump

Update version in `Cargo.toml`:

```toml
[package]
version = "0.2.0"
```

### 2. Update Changelog

Document changes in `CHANGELOG.md`.

### 3. Tag Release

```bash
git tag bootstrap-v0.2.0
git push origin bootstrap-v0.2.0
```

### 4. CI Build

GitHub Actions will automatically:

- Build binaries for all platforms
- Run tests
- Create GitHub Release
- Upload artifacts

### 5. Verify Release

```bash
# Download and test
curl -L -o bootstrap.tar.gz \
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/download/bootstrap-v0.2.0/bootstrap-repo-cli-linux-x86_64.tar.gz

tar xzf bootstrap.tar.gz
./bootstrap-repo-cli --version
./bootstrap-repo-cli doctor
```

## Common Patterns

### Adding a New Exit Code

1. Add variant to `ExitCode` enum
2. Add mapping in `BootstrapError::exit_code()`
3. Update documentation
4. Add test case

### Adding a New Error Type

1. Add variant to `BootstrapError` enum
2. Implement `exit_code()` mapping
3. Add test case
4. Update error handling

### Adding a New CLI Flag

1. Add field to `Cli` struct in `cli.rs`
2. Use in execution logic
3. Add test case
4. Update documentation

## Dependencies

Key dependencies and their roles:

- **clap**: CLI argument parsing (derive API)
- **tokio**: Async runtime (required)
- **async-trait**: Async trait support
- **reqwest**: HTTP client (rustls backend)
- **indicatif**: Progress bars and spinners
- **serde**: Serialization (JSON, TOML)
- **toml**: Configuration file parsing
- **thiserror**: Error derive macro
- **anyhow**: Error handling utilities
- **semver**: Version parsing and comparison
- **petgraph**: Dependency graph resolution
- **atty**: TTY detection
- **chrono**: Timestamp formatting

## Code Style

### Formatting

```bash
cargo fmt
```

### Linting

```bash
cargo clippy -- -D warnings
```

### Documentation

All public items must have doc comments:

```rust
/// Install and verify tools based on configuration.
///
/// # Arguments
///
/// * `ctx` - Execution context with configuration
///
/// # Returns
///
/// Result containing installation summary or error
///
/// # Errors
///
/// Returns error if installation or verification fails
pub async fn install(ctx: &Context) -> Result<InstallSummary> {
    // ...
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `cargo fmt` and `cargo clippy` for the package you changed
5. Run `cargo test -p <package>` (e.g., `cargo test -p bootstrap-repo-cli`)
6. Submit pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## Resources

- [Rust Book](https://doc.rust-lang.org/book/)
- [Async Book](https://rust-lang.github.io/async-book/)
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial)
- [clap Documentation](https://docs.rs/clap/)
- [thiserror Documentation](https://docs.rs/thiserror/)
