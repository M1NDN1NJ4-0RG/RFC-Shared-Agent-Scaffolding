# Rust Bootstrapper User Manual

## Table of Contents

1. 1. [Introduction](#introduction) 2. [Installation](#installation) 3. [Quick Start](#quick-start) 4.
   [Commands](#commands) 5. [Configuration](#configuration) 6. [Exit Codes](#exit-codes) 7. [Advanced
   Usage](#advanced-usage) 8. [Troubleshooting](#troubleshooting) 9. [Architecture](#architecture)

## Introduction

The Rust Bootstrapper (`bootstrap-repo-cli`) is a fast, reliable tool for installing and managing development toolchains. It replaces the legacy Bash bootstrapper with better performance, error handling, and user experience.

### Key Features

- - **Parallel Execution**: Safe parallelization for 30-50% faster bootstrapping - **Rich Progress UI**: Real-time
  progress bars and status updates - **Deterministic Behavior**: Fail-fast with clear exit codes - **Cross-platform**:
  Works on macOS and Linux (Windows coming soon) - **Zero Dependencies**: Single static binary, no external runtime
  required
- **Diagnostics**: Built-in `doctor` command for troubleshooting
- - **Flexible Configuration**: TOML-based profiles for different environments - **Parity with Bash**: Full feature
  parity with the Bash bootstrapper

### Parity with Bash Bootstrapper

The Rust bootstrapper achieves complete parity with the Bash bootstrapper:

1. **repo-lint Installation**: Installs repo-lint via `pip install -e .` (editable mode)
2. **Automatic Verification Gate**: Runs `repo-lint check --ci` automatically after successful installation
3. 3. **Exit Code Handling**: Properly handles verification gate exit codes: - Exit 0: Clean repository, all tools
   working - Exit 1: Violations found but tools working (acceptable) - Exit 2+: Missing tools or critical errors
   (failure) 4. **Profile Support**: Supports dev/ci/full profiles for different environments
5. **Session Integration**: Works seamlessly with `session-start.sh` and `session-end.sh` scripts

### Performance

Typical performance improvements over Bash:

- - Detection phase: 40-60% faster (parallel execution) - Installation phase: 20-40% faster (better concurrency) -
  Overall: 30-50% faster on multi-core systems

## Installation

### Pre-built Binaries (Recommended)

Download from the [releases page](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases):

```bash
# Linux x86_64
curl -L -o bootstrap.tar.gz \
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/latest/download/bootstrap-repo-cli-linux-x86_64.tar.gz

# Linux ARM64
curl -L -o bootstrap.tar.gz \
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/latest/download/bootstrap-repo-cli-linux-arm64.tar.gz

# macOS x86_64
curl -L -o bootstrap.tar.gz \
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/latest/download/bootstrap-repo-cli-macos-x86_64.tar.gz

# macOS ARM64
curl -L -o bootstrap.tar.gz \
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/latest/download/bootstrap-repo-cli-macos-arm64.tar.gz

# Extract and install
tar xzf bootstrap.tar.gz
mkdir -p ~/.bootstrap/bin
mv bootstrap-repo-cli ~/.bootstrap/bin/
chmod +x ~/.bootstrap/bin/bootstrap-repo-cli

# Add to PATH
echo 'export PATH="$HOME/.bootstrap/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Build from Source

Requirements:

- - Rust 1.70+ - Cargo

```bash
cd rust
cargo build --release
sudo cp target/release/bootstrap-repo-cli /usr/local/bin/
```

### Verify Installation

```bash
bootstrap-repo-cli --version
bootstrap-repo-cli --help
```

## Quick Start

### Basic Usage

Install all tools for the CI profile:

```bash
bootstrap-repo-cli install --profile ci
```

Install all tools for development:

```bash
bootstrap-repo-cli install --profile dev
```

Check your environment:

```bash
bootstrap-repo-cli doctor
```

Verify installations:

```bash
bootstrap-repo-cli verify
```

## Commands

### `install`

Install and verify tools.

**Usage:**

```bash
bootstrap-repo-cli install [OPTIONS]
```

**Options:**

- `--profile <NAME>`: Profile to install (dev, ci, full)
- `--dry-run`: Preview without installing
- `--ci`: CI mode (plain output, no TTY)
- `--json`: JSON output for automation
- `--verbose`: Detailed logging
- `--jobs <N>`: Control parallelism (default: CI=2, interactive=4)
- `--offline`: Use cache only, fail if missing
- `--allow-downgrade`: Permit version downgrades
- `--checkpoint`: Enable checkpoint/resume
- `--resume`: Resume from checkpoint

**Examples:**

```bash
# Basic install
bootstrap-repo-cli install

# CI environment
bootstrap-repo-cli install --profile ci --ci

# Preview what would be installed
bootstrap-repo-cli install --dry-run

# High parallelism
bootstrap-repo-cli install --jobs 8

# Offline mode (cache only)
bootstrap-repo-cli install --offline
```

**Behavior:**

- - Always runs: detect → install → verify - Fail-fast: stops on first error - Idempotent: safe to run multiple times -
  Exit codes: see [Exit Codes](#exit-codes)

### `doctor`

Diagnose environment and configuration.

**Usage:**

```bash
bootstrap-repo-cli doctor [OPTIONS]
```

**Options:**

- `--strict`: Treat warnings as failures
- `--json`: JSON output

**Examples:**

```bash
# Basic diagnostics
bootstrap-repo-cli doctor

# Strict mode (CI)
bootstrap-repo-cli doctor --strict

# JSON output
bootstrap-repo-cli doctor --json
```

**Checks:**

- - Repository: Valid git repository - Package Manager: Homebrew, apt, or snap detected - Python: Version and location -
  Network: Connectivity and latency - Disk Space: Available space - Permissions: Write permissions for installation
  paths

**Exit Codes:**

- - 0: All checks passed - 19: One or more checks failed - 19: Warnings present in strict mode

### `verify`

Verify installations without re-installing.

**Usage:**

```bash
bootstrap-repo-cli verify [OPTIONS]
```

**Options:**

- `--json`: JSON output
- `--verbose`: Detailed output

**Examples:**

```bash
# Basic verification
bootstrap-repo-cli verify

# Verbose output
bootstrap-repo-cli verify --verbose
```

**Behavior:**

- - Does not install or download anything - Checks each tool is present and functional - Reports version mismatches -
  Exit code 19 if any tool is missing or broken

## Configuration

### Configuration File: `.bootstrap.toml`

**Location:** Repository root

**Format:**

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
    # All available tools
    "python-black",
    "python-ruff",
    "python-pylint",
    "yamllint",
    "pytest",
    "actionlint",
    "ripgrep",
    "shellcheck",
    "shfmt",
    "perlcritic",
    "ppi",
    "pwsh",
    "psscriptanalyzer",
]

# Pin specific versions
[tool.actionlint]
version = "1.7.10"

# Require minimum version
[tool.ripgrep]
min_version = "14.0.0"

# Custom install args
[tool.python-black]
install_args = ["--upgrade"]
```

### Environment Variables

| Variable | Description | Default |
| ---------- | ------------- | --------- |
| `BOOTSTRAP_BIN` | Force specific binary | Auto-detect |
| `BOOTSTRAP_JOBS` | Override parallelism | CI=2, interactive=4 |
| `BOOTSTRAP_FORCE_LEGACY` | Use legacy Bash | 0 |

### Default Behavior

If `.bootstrap.toml` is missing:

- - Interactive mode: uses default dev profile - CI mode: **requires config** (exits with error)

## Exit Codes

All exit codes match the legacy Bash bootstrapper for compatibility.

| Code | Constant | Meaning |
| ------ | ---------- | --------- |
| 0 | Success | All operations completed successfully |
| 1 | UsageError | Invalid arguments or missing config |
| 10 | NotInRepo | Not in a git repository |
| 11 | VenvActivationFailed | Python virtual environment activation failed |
| 12 | NoInstallTarget | No tools to install |
| 13 | RepoLintUpgradeFailed | repo-lint upgrade failed |
| 14 | RepoLintInstallFailed | repo-lint install failed |
| 15 | PythonToolsFailed | Python tools installation failed |
| 16 | ShellToolchainFailed | Shell tools installation failed |
| 17 | PowerShellToolchainFailed | PowerShell tools installation failed |
| 18 | PerlToolchainFailed | Perl tools installation failed |
| 19 | VerificationFailed | One or more tools failed verification |
| 20 | ActionlintFailed | actionlint installation failed |
| 21 | RipgrepFailed | ripgrep installation failed (REQUIRED) |

## Advanced Usage

### Parallel Execution

Control concurrency with `--jobs`:

```bash
# Default (CI=2, interactive=4)
bootstrap-repo-cli install

# High parallelism
bootstrap-repo-cli install --jobs 16

# Sequential (debugging)
bootstrap-repo-cli install --jobs 1
```

**Safety:**

- - Detection phase: always parallel-safe - Download phase: limited by HTTP concurrency (2 per host) - Install phase:
  respects package manager locks - Verify phase: parallel-safe

### Checkpoint and Resume

For long-running installations:

```bash
# First run (creates checkpoint)
bootstrap-repo-cli install --checkpoint

# Resume from checkpoint (if interrupted)
bootstrap-repo-cli install --resume
```

**Checkpoint location:** `~/.cache/bootstrap-repo-cli/checkpoints/`

**Note:** Checkpoints are disabled by default. Enable with `--checkpoint`.

### Offline Mode

Use cached artifacts only:

```bash
# Download everything first
bootstrap-repo-cli install

# Later, use cache only
bootstrap-repo-cli install --offline
```

**Cache location:**

- Linux: `~/.cache/bootstrap-repo-cli/`
- macOS: `~/Library/Caches/bootstrap-repo-cli/`

**Cache keys:** tool + version + platform + arch + checksum

### JSON Output

For CI integration:

```bash
bootstrap-repo-cli install --json > bootstrap.log
```

**Event types:**

- `PlanComputed`: Execution plan with phases and steps
- `PhaseStarted`: Phase beginning
- `TaskStarted`: Individual task start
- `TaskProgress`: Progress update
- `TaskCompleted`: Task finished with status
- `PhaseCompleted`: Phase finished
- `BootstrapCompleted`: Final summary with exit code

### Dry-Run Mode

Preview without making changes:

```bash
bootstrap-repo-cli install --dry-run
```

**Output:**

- - Shows execution plan - Lists all steps that would be executed - Does not install or download anything - Always exits
  with code 0

### Version Downgrades

By default, downgrades are disallowed.

**Allow downgrades:**

```bash
bootstrap-repo-cli install --allow-downgrade
```

**CI policy:** Downgrades are forbidden in CI unless explicitly passed.

## Troubleshooting

### Common Issues

#### Issue: "Binary not found"

**Symptom:**

```
bash: bootstrap-repo-cli: command not found
```

**Solution:**

```bash
# Check PATH
echo $PATH

# Add to PATH if missing
export PATH="$HOME/.bootstrap/bin:$PATH"

# Or use full path
~/.bootstrap/bin/bootstrap-repo-cli install
```

#### Issue: "Missing config in CI mode"

**Symptom:**

```
Error: .bootstrap.toml required in CI mode but not found
Exit code: 1
```

**Solution:**
Create `.bootstrap.toml`:

```toml
[profile.ci]
tools = ["ripgrep", "python-black", "python-ruff"]
```

#### Issue: "Permission denied"

**Symptom:**

```
bash: ./bootstrap-repo-cli: Permission denied
```

**Solution:**

```bash
chmod +x ~/.bootstrap/bin/bootstrap-repo-cli
```

#### Issue: "ripgrep failed (exit code 21)"

**Symptom:**

```
Error: ripgrep installation failed
Exit code: 21
```

**Explanation:** ripgrep is a **required** tool and cannot be skipped.

**Solution:**

```bash
# Check package manager
bootstrap-repo-cli doctor

# Try manual install
brew install ripgrep  # macOS
sudo apt-get install ripgrep  # Linux

# Verify
rg --version
```

#### Issue: "Slow execution"

**Symptom:**
Installation takes longer than expected.

**Solution:**

```bash
# Increase parallelism
bootstrap-repo-cli install --jobs 8

# Use offline mode if cached
bootstrap-repo-cli install --offline

# Check network
bootstrap-repo-cli doctor
```

### Diagnostics

Always run `doctor` first:

```bash
bootstrap-repo-cli doctor
```

Example output:

```
✓ Repository: /path/to/repo (valid git repository)
✓ Package Manager: Homebrew 4.2.0
✓ Python: Python 3.12.1 (/usr/bin/python3)
⚠ Network: High latency detected (350ms)
✓ Disk Space: 45GB available
✓ Permissions: All paths writable
```

### Debug Logging

Enable verbose output:

```bash
bootstrap-repo-cli install --verbose
```

### Getting Help

- `bootstrap-repo-cli --help`: Command documentation
- `bootstrap-repo-cli <command> --help`: Command-specific help
- `bootstrap-repo-cli doctor`: Environment diagnostics
- [GitHub Issues](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues): Bug reports and feature requests

## Architecture

### Design Principles

1. 1. **Determinism over convenience**: Exit codes are deterministic 2. **Fail-fast, always**: No silent failures 3.
   **Idempotency governs retries**: Only safe operations are retried 4. **Concurrency only where safe**: Parallelism
   respects locks 5. **Progress UI must be honest**: Clear communication 6. **No repo pollution**: Caches live outside
   the repo

### Components

- - **CLI**: Command-line interface (clap) - **Installer Registry**: Tool definitions and dependencies - **Execution
  Planner**: Dependency resolution and phase planning - **Package Managers**: Homebrew, apt, snap abstractions -
  **Progress Reporter**: Multi-task progress UI (indicatif) - **Lock Manager**: Resource locking for safe concurrency -
  **Retry Policy**: Exponential backoff with classification - **Doctor**: Diagnostics and environment checks

### Installer Architecture

Each tool implements the `Installer` trait:

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

### Execution Flow

1. 1. **Parse CLI**: Arguments and flags
2. **Load Config**: `.bootstrap.toml` or defaults
3. 3. **Build Plan**: Dependency resolution and phase planning 4. **Execute Phases**: - Phase 1: Detection (parallel) -
   Phase 2: Installation (respects concurrency) - Phase 3: Verification (parallel) 5. **Report Results**: Exit with
   appropriate code

### Concurrency Model

- **Global Semaphore**: `--jobs <N>` limits total concurrency
- - **Resource Locks**: Named locks (brew_lock, apt_lock, etc.) - **HTTP Limiting**: 2 concurrent requests per host -
  **Retry Classification**: Only transient failures are retried

### Supported Tools

**Python:**

- - black (formatter) - ruff (linter) - pylint (linter) - yamllint (YAML linter) - pytest (test framework)

**Shell:**

- - shellcheck (linter) - shfmt (formatter)

**PowerShell:**

- - pwsh (interpreter) - PSScriptAnalyzer (linter)

**Perl:**

- - perlcritic (linter) - PPI (parser)

**Other:**

- - actionlint (GitHub Actions linter) - ripgrep (search tool, REQUIRED)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

### Adding a New Tool

1. Implement the `Installer` trait
2. Register in `InstallerRegistry`
3. 3. Add tests 4. Update documentation

## License

See [LICENSE](../LICENSE) for details.
