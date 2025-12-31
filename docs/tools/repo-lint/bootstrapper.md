# Repo-Lint Toolchain Bootstrapper

## Overview

The `bootstrap-repo-lint-toolchain.sh` script automates the setup of all development tools required for contributing to this repository. It is designed to be run at the start of every Copilot agent session to ensure a consistent, compliant development environment.

## Quick Start

### For Copilot Agents (MANDATORY)

**Run at session start:**
```bash
./scripts/bootstrap-repo-lint-toolchain.sh
```

**After bootstrap completes, activate the environment:**
```bash
source .venv/bin/activate
```

**Now you can use repo-lint:**
```bash
repo-lint --help
repo-lint check --ci
```

### For Human Developers

```bash
# Install all required tools
./scripts/bootstrap-repo-lint-toolchain.sh

# Install optional toolchains as needed
./scripts/bootstrap-repo-lint-toolchain.sh --shell --perl

# Install everything
./scripts/bootstrap-repo-lint-toolchain.sh --all
```

## What Gets Installed

### Required Toolchains (Always Installed)

- **Python Virtual Environment** (`.venv/`): Isolated Python environment at repository root
- **repo-lint Package**: Installed in editable mode from `tools/repo_lint/`
- **Python Development Tools**:
  - `black` - Code formatter
  - `ruff` - Fast Python linter
  - `pylint` - Python static analyzer
  - `yamllint` - YAML linter
  - `pytest` - Testing framework
- **rgrep**: Recursive grep utility (falls back to `grep` with warnings if unavailable)

### Optional Toolchains (Install with Flags)

- **Shell Toolchain** (`--shell`):
  - `shellcheck` - Shell script linter
  - `shfmt` - Shell script formatter

- **PowerShell Toolchain** (`--powershell`):
  - `pwsh` - PowerShell Core
  - `PSScriptAnalyzer` - PowerShell script analyzer

- **Perl Toolchain** (`--perl`):
  - `Perl::Critic` - Perl script linter
  - `PPI` - Perl parsing library

## Command-Line Options

```
Usage: ./scripts/bootstrap-repo-lint-toolchain.sh [OPTIONS]

Options:
  --verbose, -v      Verbose output (default, required during implementation)
  --quiet, -q        Quiet mode (reserved for future, currently disabled)
  --shell            Install shell toolchain (shellcheck, shfmt)
  --powershell       Install PowerShell toolchain (pwsh, PSScriptAnalyzer)
  --perl             Install Perl toolchain (Perl::Critic, PPI)
  --all              Install all optional toolchains
  --help, -h         Show help message
```

## Environment Setup

### Virtual Environment Location

The script creates a Python virtual environment at:
```
<repo-root>/.venv/
```

### PATH Management

**CRITICAL:** The bootstrapper activates the virtual environment within the script context, but **your shell session needs manual activation**.

After running the bootstrapper, you **MUST** activate the environment:

```bash
source .venv/bin/activate
```

This ensures:
- `repo-lint` is on PATH
- All Python tools are accessible
- The correct Python interpreter is used

### Verifying Setup

After activation, verify the tools:

```bash
# Verify repo-lint
repo-lint --version
which repo-lint  # Should show: <repo-root>/.venv/bin/repo-lint

# Verify Python tools
pytest --version
black --version
ruff --version

# Verify shell tools (if --shell was used)
shellcheck --version
shfmt --version
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success - all operations completed |
| 1    | Generic failure |
| 10   | Repository root not found |
| 11   | Virtual environment creation failed |
| 12   | No valid install target (missing pyproject.toml) |
| 13   | repo-lint not found on PATH after installation |
| 14   | repo-lint --help command failed |
| 15   | Python toolchain installation failed |
| 16   | Shell toolchain installation failed |
| 17   | PowerShell toolchain installation failed |
| 18   | Perl toolchain installation failed |
| 19   | Verification gate failed (repo-lint check --ci) |

## Idempotency

The script is **idempotent** - safe to run multiple times:
- Existing virtual environment is reused
- Already-installed packages are skipped
- Verification ensures everything is functional

## Troubleshooting

### "repo-lint: command not found" after bootstrap

**Solution:** Activate the virtual environment:
```bash
source .venv/bin/activate
```

### Python tools not found

**Solution:** Ensure virtual environment is activated:
```bash
which python3  # Should show: <repo-root>/.venv/bin/python3
```

### Permission denied errors

**Solution:** Ensure script is executable:
```bash
chmod +x scripts/bootstrap-repo-lint-toolchain.sh
```

### apt-get/brew installation failures

**Solution:** The script will attempt installation but gracefully degrade:
- `rgrep` → falls back to `grep`
- Optional toolchains → clear error messages with manual install instructions

## For Copilot Agents: Pre-Commit Requirements

**BEFORE EVERY COMMIT**, Copilot agents **MUST**:

1. **Run linting on shell scripts:**
   ```bash
   shellcheck <file>
   shfmt -d <file>
   python3 scripts/validate_docstrings.py --file <file> --language bash
   ```

2. **Run linting on Python files:**
   ```bash
   black --check <file>
   ruff check <file>
   pylint <file>
   python3 scripts/validate_docstrings.py --file <file> --language python
   ```

3. **Fix ALL violations before committing** - no exceptions.

This includes fixing violations in files created earlier in the PR.

## Platform Compatibility

- **Linux**: Fully supported (tested on Ubuntu/Debian)
- **macOS**: Should work (uses `brew` when available)
- **Windows**: Not supported (WSL recommended)

### Requirements

- `bash` (version 4.0+)
- `python3` (version 3.8+)
- `python3-venv` module
- `git` (for repository detection)

## Architecture

### Script Phases

1. **Phase 1: Core Setup**
   - Repository root discovery
   - Virtual environment creation/activation
   - repo-lint package installation
   - Verification that repo-lint is functional

2. **Phase 2: Toolchain Installation**
   - rgrep utility (required)
   - Python toolchain (required)
   - Shell toolchain (optional)
   - PowerShell toolchain (optional)
   - Perl toolchain (optional)

3. **Phase 3: Verification Gate**
   - Run `repo-lint check --ci` to validate all tools
   - Ensure repo-lint is using the correct PATH

### Design Decisions

**Why direct pip install instead of `repo-lint install`?**
- `repo-lint install` creates a separate `.venv-lint/` environment
- Direct installation into main `.venv/` ensures all tools are immediately available
- Simplifies PATH management for users and Copilot agents

**Why non-interactive Perl installation?**
- `Perl::Critic` installation can prompt for user input
- Uses `PERL_MM_USE_DEFAULT=1` and `--notest --force` to avoid blocking
- Enables automated/CI usage

## Implementation Status

- ✅ Phase 1: Core bootstrapper (complete)
- ✅ Phase 2: Toolchain installation (complete)
- ✅ Phase 3: Verification gate (complete)
- ✅ Phase 4: Documentation (this document)
- ⏳ Phase 5: Testing and validation (in progress)
- ⏳ Phase 6: CI integration (planned)

## See Also

- [Copilot Instructions](/.github/copilot-instructions.md) - Repository agent guidelines
- [Docstring Contracts](/docs/contributing/docstring-contracts/) - Documentation standards
- [repo-lint Documentation](/tools/repo_lint/README.md) - Tool usage and configuration
