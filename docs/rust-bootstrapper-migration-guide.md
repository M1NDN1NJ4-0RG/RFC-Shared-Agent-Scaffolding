# Rust Bootstrapper Migration Guide

## Overview

This guide helps you migrate from the legacy Bash bootstrapper (`bootstrap-repo-lint-toolchain.sh`) to the new Rust-based bootstrapper (`bootstrap-repo-cli`).

## Why Migrate?

The Rust bootstrapper provides several advantages over the Bash version:

- **30-50% Faster**: Parallel execution where safe (detection, downloads)
- **Better Error Messages**: Clear, actionable error messages with exit codes
- **Rich Progress UI**: Real-time progress bars and status updates
- **Structured Logging**: JSON output mode for CI integration
- **Better Diagnostics**: `doctor` command for troubleshooting
- **Deterministic Behavior**: Fail-fast with clear exit codes
- **Cross-platform**: Single binary, no external dependencies

## Installation

### Option 1: Download Pre-built Binary (Recommended)

1. Download the appropriate binary for your platform from the [releases page](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases):
   - Linux x86_64: `bootstrap-repo-cli-linux-x86_64.tar.gz`
   - Linux ARM64: `bootstrap-repo-cli-linux-arm64.tar.gz`
   - macOS x86_64: `bootstrap-repo-cli-macos-x86_64.tar.gz`
   - macOS ARM64: `bootstrap-repo-cli-macos-arm64.tar.gz`

2. Verify the checksum (optional but recommended):
   ```bash
   sha256sum -c bootstrap-repo-cli-<platform>.tar.gz.sha256
   ```

3. Extract and install:
   ```bash
   tar xzf bootstrap-repo-cli-<platform>.tar.gz
   mkdir -p ~/.bootstrap/bin
   mv bootstrap-repo-cli ~/.bootstrap/bin/
   chmod +x ~/.bootstrap/bin/bootstrap-repo-cli
   ```

4. Add to PATH (if not already):
   ```bash
   echo 'export PATH="$HOME/.bootstrap/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Option 2: Build from Source

If you prefer to build from source or need a custom build:

```bash
cd rust
cargo build --release
sudo cp target/release/bootstrap-repo-cli /usr/local/bin/
```

### Option 3: Use the Wrapper Script (Transition Period)

The repository includes a wrapper script that automatically detects and uses the Rust binary if available, falling back to Bash:

```bash
# This will use Rust if available, otherwise Bash
./scripts/bootstrap-repo-lint-toolchain.sh
```

Set `BOOTSTRAP_BIN` to force a specific binary:
```bash
export BOOTSTRAP_BIN="$HOME/.bootstrap/bin/bootstrap-repo-cli"
./scripts/bootstrap-repo-lint-toolchain.sh
```

## Command Equivalents

### Basic Usage

| Bash | Rust |
|------|------|
| `./scripts/bootstrap-repo-lint-toolchain.sh` | `bootstrap-repo-cli install` |
| `./scripts/bootstrap-repo-lint-toolchain.sh --all` | `bootstrap-repo-cli install --profile full` |
| `./scripts/bootstrap-repo-lint-toolchain.sh --python` | `bootstrap-repo-cli install --profile dev` |
| N/A | `bootstrap-repo-cli doctor` |
| N/A | `bootstrap-repo-cli verify` |

### Advanced Options

| Bash | Rust |
|------|------|
| N/A (always installs) | `--dry-run` (plan without installing) |
| Auto-detected | `--ci` (CI mode: plain output, no TTY) |
| N/A | `--json` (JSON output for automation) |
| N/A | `--verbose` (detailed logging) |
| N/A | `--jobs <N>` (control parallelism) |
| N/A | `--offline` (cache-only mode) |
| N/A | `--allow-downgrade` (permit version downgrades) |

## Parity with Bash Bootstrapper

The Rust bootstrapper achieves complete feature parity with the Bash version:

### repo-lint Installation and Verification

Both bootstrappers:
1. Install `repo-lint` via `pip install -e .` (editable mode from repository root)
2. Verify `repo-lint --help` succeeds before completing
3. Run automatic verification gate (`repo-lint check --ci`) after successful installation
4. Handle verification gate exit codes identically:
   - Exit 0: Clean repository, all tools working ✓
   - Exit 1: Violations found but tools working ✓ (acceptable)
   - Exit 2: Missing tools ✗ (failure)
   - Exit 3+: Other errors ✗ (failure)

### Profile Support

The Rust version uses profiles instead of command-line flags:
- **dev profile**: Equivalent to Bash default (all common tools)
- **ci profile**: Minimal tools for CI environments
- **full profile**: All available tools (equivalent to Bash `--all`)

Both approaches ensure the same tools are installed for equivalent use cases.

### Session Scripts

Both bootstrappers work with session scripts:
- `./scripts/session-start.sh`: Runs bootstrapper and activates environment
- `./scripts/session-end.sh`: Validates all tools still work correctly

The session scripts automatically use the Rust bootstrapper if available, falling back to Bash.

## Configuration

### Legacy Bash: Command-line Flags

The Bash version uses command-line flags to select tools:
```bash
./scripts/bootstrap-repo-lint-toolchain.sh --python --shell --perl
```

### Rust: `.bootstrap.toml` Configuration

The Rust version uses a configuration file for better repeatability:

```toml
# .bootstrap.toml

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
    # All tools
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

[tool.actionlint]
version = "1.7.10"  # Pin specific version

[tool.ripgrep]
min_version = "14.0.0"  # Require minimum version
```

## Exit Codes

Both versions use the same exit codes for compatibility:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage error |
| 10 | Not in repository |
| 11 | Virtual environment activation failed |
| 12 | No install target |
| 13 | repo-lint upgrade failed |
| 14 | repo-lint install failed |
| 15 | Python tools failed |
| 16 | Shell toolchain failed |
| 17 | PowerShell toolchain failed |
| 18 | Perl toolchain failed |
| 19 | Verification failed |
| 20 | actionlint failed |
| 21 | ripgrep failed |

## New Features in Rust

### 1. Doctor Command

Diagnose installation issues:
```bash
bootstrap-repo-cli doctor

# Strict mode (treats warnings as failures)
bootstrap-repo-cli doctor --strict
```

Example output:
```
✓ Repository: Found valid git repository
✓ Package Manager: Homebrew detected
✓ Python: Python 3.12.1 found
⚠ Network: Slow connection detected (>200ms latency)
✓ Disk Space: 45GB available
✓ Permissions: All required permissions granted
```

### 2. Verify-Only Mode

Check installations without re-installing:
```bash
bootstrap-repo-cli verify
```

### 3. JSON Output

For CI integration and automation:
```bash
bootstrap-repo-cli install --json > bootstrap.log
```

Example JSON output:
```json
{
  "type": "BootstrapCompleted",
  "total_duration": 45.2,
  "exit_code": 0,
  "tools_installed": [
    {"name": "ripgrep", "version": "14.1.1"},
    {"name": "black", "version": "24.1.0"}
  ]
}
```

### 4. Parallel Execution

Safe parallelization for faster bootstrapping:
```bash
# Control concurrency (default: CI=2, interactive=4)
bootstrap-repo-cli install --jobs 8
```

### 5. Dry-Run Mode

Preview what would be installed without making changes:
```bash
bootstrap-repo-cli install --dry-run
```

### 6. Offline Mode

Use cached artifacts only (fail if missing):
```bash
bootstrap-repo-cli install --offline
```

## CI Integration

### Legacy Bash in CI

```yaml
- name: Bootstrap tools
  run: ./scripts/bootstrap-repo-lint-toolchain.sh --all
```

### Rust in CI

```yaml
- name: Download Rust bootstrapper
  run: |
    curl -L -o bootstrap.tar.gz \
      https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases/latest/download/bootstrap-repo-cli-linux-x86_64.tar.gz
    tar xzf bootstrap.tar.gz
    chmod +x bootstrap-repo-cli
    mv bootstrap-repo-cli ~/.bootstrap/bin/

- name: Bootstrap tools
  run: bootstrap-repo-cli install --ci --json

- name: Verify installation
  run: bootstrap-repo-cli verify
```

Or use the wrapper for automatic fallback:

```yaml
- name: Bootstrap tools
  run: ./scripts/bootstrap-repo-lint-toolchain.sh
  env:
    # Force Rust version if available
    BOOTSTRAP_BIN: /home/runner/.bootstrap/bin/bootstrap-repo-cli
```

## Troubleshooting

### Issue: "Binary not found"

**Solution**: Ensure the binary is in your PATH or use the full path:
```bash
~/.bootstrap/bin/bootstrap-repo-cli install
```

### Issue: "Missing config in CI mode"

The Rust version requires `.bootstrap.toml` in CI mode.

**Solution**: Create a minimal config:
```toml
[profile.ci]
tools = ["ripgrep", "python-black", "python-ruff"]
```

### Issue: "Permission denied"

**Solution**: Make the binary executable:
```bash
chmod +x ~/.bootstrap/bin/bootstrap-repo-cli
```

### Issue: "Slow execution"

**Solution**: Increase parallelism:
```bash
bootstrap-repo-cli install --jobs 8
```

Or use offline mode if you already have cached artifacts:
```bash
bootstrap-repo-cli install --offline
```

### Issue: "Tools not detected after install"

**Solution**: Run the doctor command for diagnostics:
```bash
bootstrap-repo-cli doctor
```

## Rollback to Bash

If you encounter issues with the Rust version, you can force the legacy Bash version:

### Method 1: Environment Variable
```bash
export BOOTSTRAP_FORCE_LEGACY=1
./scripts/bootstrap-repo-lint-toolchain.sh
```

### Method 2: Direct Invocation
```bash
./scripts/.legacy/bootstrap-repo-lint-toolchain.sh
```

## Migration Checklist

- [ ] Download and install the Rust binary
- [ ] Create `.bootstrap.toml` configuration
- [ ] Test with `--dry-run` mode
- [ ] Run `bootstrap-repo-cli doctor` to verify environment
- [ ] Update CI workflows to use Rust binary
- [ ] Test in CI environment
- [ ] Update documentation and runbooks
- [ ] Train team on new commands
- [ ] Remove Bash-specific flags from scripts

## Getting Help

- Run `bootstrap-repo-cli --help` for command documentation
- Use `bootstrap-repo-cli doctor` for diagnostics
- Check the [GitHub issues](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues) for known problems
- See the [Rust Bootstrapper User Manual](rust-bootstrapper-manual.md) for detailed documentation

## Feedback

We value your feedback! Please report issues or suggestions:
- Open an issue on GitHub
- Use the `doctor` command output to include diagnostic information
- Mention whether you're using the pre-built binary or building from source
