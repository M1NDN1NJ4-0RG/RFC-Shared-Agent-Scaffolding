# How to Use repo-lint

This guide covers installation, common commands, shell completion, and troubleshooting for the `repo-lint` tool.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Common Commands](#common-commands)
- [Shell Completion](#shell-completion)
  - [Bash, Zsh, Fish](#bash-completion)
  - [PowerShell (Windows)](#powershell-completion-windows)
- [Troubleshooting](#troubleshooting)
  - [Windows-Specific Issues](#windows-specific-issues)
- [Advanced Usage](#advanced-usage)
  - [Output Modes: Interactive vs CI](#output-modes-interactive-vs-ci)
  - [Theme Customization](#theme-customization)
  - [Custom Configuration](#custom-configuration)
  - [Pre-Commit Hooks](#integrating-with-pre-commit-hooks)
  - [CI/CD Integration](#cicd-integration)
- [Getting Help](#getting-help)

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (recommended)

### Option 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding.git
cd RFC-Shared-Agent-Scaffolding

# Install in editable mode (includes all dependencies)
pip install -e .

# Verify installation
repo-lint --help
```

### Option 2: Install Linting Tools Only

If you just want to set up the linting environment:

```bash
cd RFC-Shared-Agent-Scaffolding
repo-lint install
```

This will:
- Install Python tools (black, ruff, pylint, yamllint) in a local virtual environment
- Provide instructions for installing language-specific tools (shellcheck, perltidy, etc.)

---

## Basic Usage

### Check Code Quality

Run all linting checks without modifying files:

```bash
repo-lint check
```

### Fix Code Style Issues

Apply automatic formatting fixes:

```bash
repo-lint fix
```

### Check Specific Language

Lint only files for a specific language:

```bash
repo-lint check --only python
repo-lint check --only bash
repo-lint check --only yaml
```

### CI Mode

Run checks in CI mode (fails if tools are missing instead of prompting to install):

```bash
repo-lint check --ci
```

### Verbose Output

Show detailed output including passed checks:

```bash
repo-lint check --verbose
repo-lint fix --verbose
```

---

## Common Commands

### 1. Pre-Commit Check (Local Development)

Before committing changes, run:

```bash
repo-lint check
```

If there are issues, fix them with:

```bash
repo-lint fix
```

Then run check again to verify:

```bash
repo-lint check
```

### 2. Check Specific File Types

```bash
# Check only Python files
repo-lint check --only python

# Check only Bash scripts
repo-lint check --only bash

# Check only YAML files
repo-lint check --only yaml

# Check only PowerShell scripts
repo-lint check --only powershell

# Check only Perl scripts
repo-lint check --only perl

# Check only Rust files
repo-lint check --only rust
```

### 3. JSON Output for CI Integration

Get machine-readable output:

```bash
repo-lint check --json
repo-lint fix --json
```

### 4. Install/Update Linting Tools

Install all auto-installable tools:

```bash
repo-lint install
```

Clean up local tool installations:

```bash
repo-lint install --cleanup
```

### 5. Unsafe Mode (⚠️ Advanced Users Only)

Enable experimental fixers that may change code behavior:

```bash
# WARNING: This is FORBIDDEN in CI and requires explicit confirmation
repo-lint fix --unsafe --yes-i-know

# Always review the generated patch before committing:
# - Check logs/unsafe-fix-forensics/ for detailed logs
# - Review the .patch file carefully
```

---

## Shell Completion

repo-lint supports shell completion for bash, zsh, and fish.

### Bash Completion

```bash
# Generate completion script
_REPO_LINT_COMPLETE=bash_source repo-lint > ~/.repo-lint-complete.bash

# Add to ~/.bashrc
echo 'source ~/.repo-lint-complete.bash' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

### Zsh Completion

```bash
# Generate completion script
_REPO_LINT_COMPLETE=zsh_source repo-lint > ~/.repo-lint-complete.zsh

# Add to ~/.zshrc
echo 'source ~/.repo-lint-complete.zsh' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

### Fish Completion

```bash
# Generate completion script
_REPO_LINT_COMPLETE=fish_source repo-lint > ~/.config/fish/completions/repo-lint.fish

# Reload shell
source ~/.config/fish/config.fish
```

### PowerShell Completion (Windows)

**For PowerShell 5.x (Built-in on Windows):**

```powershell
# Generate completion script
$env:_REPO_LINT_COMPLETE = "powershell_source"
repo-lint | Out-File -FilePath "$HOME\Documents\WindowsPowerShell\repo-lint-complete.ps1" -Encoding UTF8

# Add to PowerShell profile
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
}
Add-Content $PROFILE ". `"$HOME\Documents\WindowsPowerShell\repo-lint-complete.ps1`""

# Reload profile
. $PROFILE
```

**For PowerShell 7+ (Cross-Platform):**

```powershell
# Generate completion script
$env:_REPO_LINT_COMPLETE = "powershell_source"
repo-lint | Out-File -FilePath "$HOME\.config\powershell\repo-lint-complete.ps1" -Encoding UTF8

# Add to PowerShell 7+ profile
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
}
Add-Content $PROFILE ". `"$HOME\.config\powershell\repo-lint-complete.ps1`""

# Reload profile
. $PROFILE
```

### Testing Completion

After setting up completion, test it:

```bash
# Type and press TAB
repo-lint <TAB>

# Should show: check, fix, install

# Type and press TAB
repo-lint check --<TAB>

# Should show: --ci, --json, --only, --verbose, --help
```

---

## Troubleshooting

### Issue: "repo-lint: command not found"

**Cause:** The tool is not installed or not in PATH.

**Solution:**

```bash
# Verify installation
pip list | grep repo-lint

# If not found, install it
pip install -e .

# Verify entry point
which repo-lint

# Alternative: Use module invocation
python3 -m tools.repo_lint check
```

### Issue: "ModuleNotFoundError: No module named 'yaml'"

**Cause:** PyYAML dependency is missing.

**Solution:**

```bash
# Install dependencies
pip install -e .

# Or install PyYAML directly
pip install PyYAML>=6.0
```

### Issue: "Missing tools: black, ruff, pylint"

**Cause:** Python linting tools are not installed.

**Solution:**

```bash
# Run the installer
repo-lint install

# Or install tools manually
pip install black==24.10.0 ruff==0.8.4 pylint==3.3.2 yamllint==1.35.1
```

### Issue: "shellcheck: command not found" (Bash linting)

**Cause:** ShellCheck is not installed.

**Solution:**

```bash
# Ubuntu/Debian
sudo apt-get install shellcheck

# macOS
brew install shellcheck

# Fedora/RHEL
sudo dnf install ShellCheck
```

### Issue: "shfmt: command not found" (Bash formatting)

**Cause:** shfmt is not installed.

**Solution:**

```bash
# Install via Go
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Or download binary from releases
# https://github.com/mvdan/sh/releases
```

### Issue: "Auto-fix policy file not found"

**Cause:** The auto-fix policy configuration file is missing.

**Solution:**

```bash
# Ensure you're in the repository root
cd RFC-Shared-Agent-Scaffolding

# Verify policy file exists
ls -l conformance/repo-lint/autofix-policy.json

# If missing, the repository may be incomplete
git pull origin main
```

### Issue: Unsafe mode is blocked

**Cause:** Safety checks prevent unsafe fixers from running.

**Solution:**

```bash
# Unsafe mode requires BOTH flags:
repo-lint fix --unsafe --yes-i-know

# Unsafe mode is FORBIDDEN in CI environments
# If CI is detected, unsafe mode will fail with exit code 4

# To run locally (after reading warnings):
# 1. Review docs/contributing/ai-constraints.md
# 2. Use both --unsafe and --yes-i-know flags
# 3. Review generated patch before committing
```

### Issue: Exit code 2 (Missing tools in CI)

**Cause:** Required tools are not installed and CI mode is active.

**Solution:**

In CI workflows, ensure tools are installed before running repo-lint:

```yaml
- name: Install dependencies
  run: |
    python3 -m pip install --upgrade pip
    python3 -m pip install black==24.10.0 ruff==0.8.4 pylint==3.3.2 yamllint==1.35.1 PyYAML>=6.0

- name: Run repo-lint
  run: repo-lint check --ci
```

### Issue: Exit code 4 (Unsafe violation)

**Cause:** Unsafe mode used in CI or without confirmation.

**Solution:**

- Remove `--unsafe` flag in CI environments
- Use `--yes-i-know` with `--unsafe` in local environments
- Read docs/contributing/ai-constraints.md before using unsafe mode

### Windows-Specific Issues

#### Issue: Rich output not displaying correctly in Command Prompt

**Cause:** Windows Command Prompt has limited Unicode and color support.

**Solution:**

```powershell
# Option 1: Use Windows Terminal (recommended)
# Download from Microsoft Store or GitHub

# Option 2: Use PowerShell instead of cmd.exe
# PowerShell has better Unicode support

# Option 3: Force CI mode for plain text output
repo-lint check --ci
```

#### Issue: PowerShell completion not working

**Cause:** Execution policy may block the completion script.

**Solution:**

```powershell
# Check current execution policy
Get-ExecutionPolicy

# If Restricted, change to RemoteSigned (allows local scripts)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then regenerate and load completion script
$env:_REPO_LINT_COMPLETE = "powershell_source"
repo-lint | Out-File -FilePath "$HOME\.config\powershell\repo-lint-complete.ps1" -Encoding UTF8
. $PROFILE
```

#### Issue: "python: command not found" on Windows

**Cause:** Python may be installed as `python3` or `py` instead of `python`.

**Solution:**

```powershell
# Try different Python commands
py -3 -m tools.repo_lint check
python3 -m tools.repo_lint check

# Or create an alias in PowerShell profile
Set-Alias -Name python -Value py

# Verify Python is in PATH
$env:PATH -split ';' | Select-String python
```

#### Issue: Line ending differences (CRLF vs LF)

**Cause:** Windows uses CRLF, Unix/Linux/Mac use LF. Git auto-conversion may conflict with linters.

**Solution:**

```bash
# Configure Git to handle line endings correctly
git config --global core.autocrlf true

# For repo-lint to work correctly, ensure consistent line endings
# Edit .gitattributes:
* text=auto
*.py text eol=lf
*.sh text eol=lf
*.ps1 text eol=crlf
```

#### Issue: Theme colors not appearing in PowerShell

**Cause:** PowerShell may need color support enabled.

**Solution:**

```powershell
# Enable ANSI color support in PowerShell (Windows 10+)
# This is usually automatic, but if not:
$env:TERM = "xterm-256color"

# For PowerShell 7+, colors should work by default
# For PowerShell 5.x, use Windows Terminal for best results

# Alternative: Force CI mode for plain output
repo-lint check --ci
```

---

## Advanced Usage

### Custom Configuration

repo-lint uses external YAML configuration files for naming rules, docstring rules, and linting rules:

- `conformance/repo-lint/repo-lint-naming-rules.yaml` - Filename conventions
- `conformance/repo-lint/repo-lint-docstring-rules.yaml` - Docstring requirements
- `conformance/repo-lint/repo-lint-linting-rules.yaml` - Linter configurations

Edit these files to customize rules for your repository.

### Integrating with Pre-Commit Hooks

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "Running repo-lint checks..."
repo-lint check

if [ $? -ne 0 ]; then
    echo "❌ Linting checks failed. Fix issues and try again."
    exit 1
fi

echo "✅ All checks passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
      
      - name: Run repo-lint
        run: repo-lint check --ci --json
```

### Environment Variables

repo-lint supports environment variable configuration:

```bash
# Set default values for Click commands
export REPO_LINT_VERBOSE=1
export REPO_LINT_CI=1

# Run with environment defaults
repo-lint check
```

### Output Modes: Interactive vs CI

repo-lint provides two output modes optimized for different environments:

#### Interactive Mode (Default)

Used when running in a terminal (TTY). Features:
- **Rich formatting** with colors, tables, and panels
- **Icons** for status indicators (✓, ✗, ⚠️)
- **Progress indicators** and spinners for long operations
- **Styled help** output with syntax highlighting

```bash
# Interactive mode (automatic when running in terminal)
repo-lint check

# Example output:
# ╭───────────────────── Linting Results ─────────────────────╮
# │ Runner │ Status │ Files │ Violations │ Duration        │
# ├────────┼────────┼───────┼────────────┼─────────────────┤
# │ black  │ ✓ PASS │   142 │          0 │ 1.23s          │
# │ ruff   │ ✗ FAIL │   142 │          3 │ 0.87s          │
# ╰────────────────────────────────────────────────────────────╯
```

#### CI Mode

Used in CI/CD environments. Features:
- **Plain text** output without colors or formatting
- **No icons** or progress indicators
- **Stable, deterministic** output for log parsing
- **Greppable** format for automated analysis

```bash
# Enable CI mode explicitly
repo-lint check --ci

# CI mode is also automatically detected when:
# - CI environment variable is set (e.g., GitHub Actions, GitLab CI)
# - STDOUT is not a TTY (output is redirected to file/pipe)

# Example output:
# Runner: black    Status: PASS   Files: 142   Violations: 0   Duration: 1.23s
# Runner: ruff     Status: FAIL   Files: 142   Violations: 3   Duration: 0.87s
```

**When to use CI mode:**
- GitHub Actions, GitLab CI, Jenkins, or other CI/CD
- Redirecting output to files: `repo-lint check > results.txt`
- Scripting and automation where stable output is needed
- Windows Command Prompt (if Rich rendering has issues)

### Theme Customization

repo-lint uses a YAML-based theme system for customizing UI appearance.

#### Default Theme

The default theme is defined in `conformance/repo-lint/repo-lint-ui-theme.yaml`:

```yaml
---
config_type: repo-lint-ui-theme
version: 1.0.0

interactive:
  colors:
    primary: "cyan"
    success: "green"
    failure: "red"
    warning: "yellow"
    info: "blue"
    metadata: "dim"
  
  icons:
    pass: "✓"
    fail: "✗"
    warn: "⚠️"
    skip: "○"
    running: "▶"
  
  borders:
    style: "rounded"  # Options: ascii, rounded, heavy, double
    color: "cyan"

ci:
  icons_enabled: false  # No icons in CI mode
  colors_enabled: false  # No colors in CI mode
...
```

#### Custom Theme

Create a custom theme file anywhere in your repository:

```bash
# Create custom theme
mkdir -p ~/.config/repo-lint
cat > ~/.config/repo-lint/my-theme.yaml << 'EOF'
---
config_type: repo-lint-ui-theme
version: 1.0.0

interactive:
  colors:
    primary: "magenta"
    success: "bright_green"
    failure: "bright_red"
    warning: "bright_yellow"
    info: "bright_blue"
  
  icons:
    pass: "✅"
    fail: "❌"
    warn: "⚠️"
  
  borders:
    style: "heavy"
    color: "magenta"

ci:
  icons_enabled: false
  colors_enabled: false
...
EOF
```

#### Using Custom Themes

**Method 1: Command-line flag**

```bash
repo-lint --theme ~/.config/repo-lint/my-theme.yaml check
```

**Method 2: Environment variable**

```bash
export REPO_LINT_UI_THEME=~/.config/repo-lint/my-theme.yaml
repo-lint check
```

**Method 3: Per-command override**

```bash
# Use custom theme for this command only
REPO_LINT_UI_THEME=/path/to/theme.yaml repo-lint check
```

**Theme Precedence (highest to lowest):**
1. `--theme` flag
2. `REPO_LINT_UI_THEME` environment variable
3. User theme: `~/.config/repo-lint/repo-lint-ui-theme.yaml`
4. Repository theme: `conformance/repo-lint/repo-lint-ui-theme.yaml`
5. Built-in default theme

#### Available Color Names

- Standard: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- Bright: `bright_black`, `bright_red`, `bright_green`, `bright_yellow`, `bright_blue`, `bright_magenta`, `bright_cyan`, `bright_white`
- Special: `dim` (dimmed text), `bold` (bold text)

#### Available Border Styles

- `ascii` - Simple ASCII characters (`+`, `-`, `|`)
- `rounded` - Rounded corners (╭, ╮, ╰, ╯)
- `heavy` - Heavy borders (┏, ┓, ┗, ┛)
- `double` - Double-line borders (╔, ╗, ╚, ╝)

### Forensics and Debugging

When unsafe fixes are applied, forensic files are generated:

```bash
# After running unsafe mode:
repo-lint fix --unsafe --yes-i-know

# Check forensics directory:
ls -l logs/unsafe-fix-forensics/

# Files include:
# - unsafe-fixes-TIMESTAMP.patch  (changes made)
# - unsafe-fixes-TIMESTAMP.log    (detailed execution log)
```

---

## Getting Help

### Command-Line Help

```bash
# General help
repo-lint --help

# Command-specific help
repo-lint check --help
repo-lint fix --help
repo-lint install --help
```

### Rich Help Output

repo-lint uses Rich for formatted help output with:
- Colored text and panels
- Tables for command lists
- Syntax highlighting for examples

### Documentation

- **Contributing Guide:** `docs/contributing/README.md`
- **AI Constraints:** `docs/contributing/ai-constraints.md`
- **Naming Conventions:** `docs/contributing/naming-and-style.md`
- **Configuration:** `conformance/repo-lint/README.md`

### Reporting Issues

If you encounter bugs or have feature requests:
1. Check existing issues: https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues
2. Create a new issue with:
   - Command that failed
   - Full error message
   - Python version (`python --version`)
   - repo-lint version (`repo-lint --version`)
   - Operating system

---

## Summary of Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | All checks passed |
| 1 | Violations found | Fix issues and re-run |
| 2 | Missing tools (CI) | Install required tools |
| 3 | Internal error | Check error message and logs |
| 4 | Unsafe violation | Review unsafe mode requirements |

---

**Version:** 0.1.0  
**Last Updated:** 2025-12-31  
**Maintained by:** M1NDN1NJ4-0RG
