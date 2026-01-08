# How to Use repo-lint

This guide covers installation, common commands, shell completion, and troubleshooting for the `repo-lint` tool.

## Table of Contents

- - - [Installation](#installation) - [Basic Usage](#basic-usage) - [Common Commands](#common-commands) - [Tool
  Discovery and Help](#6-tool-discovery-and-help) - [Environment Diagnostics](#7-environment-diagnostics) - [Environment
  and PATH Management](#8-environment-and-path-management) - [Test Fixtures and Vector
  Mode](#test-fixtures-and-vector-mode) - [What Are Fixture Files?](#what-are-fixture-files) - [Where Fixture Files
  Live](#where-fixture-files-live) - [Vector Mode (--include-fixtures)](#vector-mode---include-fixtures) - [Fixture
  Immutability Guarantees](#fixture-immutability-guarantees) - [Per-Language Fixture
  Breakdown](#per-language-fixture-breakdown) - [Common Mistakes and Warnings](#common-mistakes-and-warnings) - [Shell
  Completion](#shell-completion) - [Bash, Zsh, Fish](#bash-completion) - [PowerShell
  (Windows)](#powershell-completion-windows) - [Troubleshooting](#troubleshooting) - [Windows-Specific
  Issues](#windows-specific-issues) - [Advanced Usage](#advanced-usage) - [Output Modes: Interactive vs
  CI](#output-modes-interactive-vs-ci) - [Theme Customization](#theme-customization) - [Custom
  Configuration](#custom-configuration) - [Viewing Current Configuration](#viewing-current-configuration) - [Validating
  Configuration Files](#validating-configuration-files) - [Configuration Precedence](#configuration-precedence) -
  [Pre-Commit Hooks](#integrating-with-pre-commit-hooks) - [CI/CD Integration](#cicd-integration) - [Getting
  Help](#getting-help)

---

## Installation

### Prerequisites

- - - Python 3.8 or higher - pip (Python package manager) - Git (recommended)

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

- - - Install Python tools (black, ruff, pylint, yamllint) in a local virtual environment - Provide instructions for
  installing language-specific tools (shellcheck, perltidy, etc.)

### Option 3: Automated Bootstrapping (Recommended for Contributors)

For a complete, automated setup of all development tools, use the bootstrapper scripts:

#### Using Bash Bootstrapper (Traditional)

```bash
cd RFC-Shared-Agent-Scaffolding
./scripts/session-start.sh
```

This script:

- - Creates a Python virtual environment (`.venv/`) - Installs `repo-lint` in editable mode (`pip install -e .`) - -
  Installs all required linting tools (Python, Shell, PowerShell, Perl) - Runs verification gate (`repo-lint check
  --ci`)

#### Using Rust Bootstrapper (Faster, Parallel)

The repository includes a Rust-based bootstrapper that provides:

- - - Parallel tool installation for faster setup - Profile-based installation (dev/ci/full) - Rich progress UI with
  real-time status updates - Deterministic exit codes

**Pre-built binaries** are available for:

- - - Linux x86_64 (musl) - Linux ARM64 (musl) - macOS x86_64 - macOS ARM64

Download from [GitHub Releases](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases) or use the session scripts (which automatically use the Rust bootstrapper if available).

**Usage:**

```bash
# Install for development (dev profile)
bootstrap-repo-cli install --profile dev

# Check installation
bootstrap-repo-cli doctor

# Verify all tools
bootstrap-repo-cli verify
```

**Profiles:**

- - `dev`: Development tools (repo-lint, ripgrep, Python tools, shell tools, actionlint) - `ci`: Minimal tools for CI
  environments (subset of dev) - `full`: All available tools including Perl and PowerShell

**Parity with Bash:**
The Rust bootstrapper achieves parity with the Bash bootstrapper by:

- - Installing `repo-lint` via `pip install -e .` (editable mode) - Running automatic verification gate (`repo-lint
  check --ci`) after installation - Ensuring `repo-lint --help` succeeds before completing

#### Session Scripts

For consistent workflow management, use these scripts:

```bash
# Start a session (runs bootstrapper + activates environment)
./scripts/session-start.sh

# End a session (runs verification gate)
./scripts/session-end.sh
```

**Session workflow:**

1. 1. `session-start.sh` runs the bootstrapper and sets up the environment 2. 2. You make code changes 3.
   `session-end.sh` validates that all tools still work correctly

Both scripts **MUST** exit 0 for a successful session.

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
repo-lint check --lang python
repo-lint check --lang bash
repo-lint check --lang yaml
```

### CI Mode

Run checks in CI mode (fails if tools are missing instead of prompting to install):

```bash
repo-lint check --ci
```

### Parallel Execution (Default)

**`repo-lint check` runs in parallel by default** using automatic worker calculation based on CPU count.

#### Default Behavior (AUTO)

By default, `repo-lint check` and `repo-lint check --ci` use parallel execution with:

- - **AUTO worker calculation**: `min(max((os.cpu_count() or 1) - 1, 1), 8)` - - This selects a conservative number of
  workers (1-8) based on available CPUs - Leaves 1 CPU core available for OS/overhead - Hard capped at 8 workers to
  prevent resource exhaustion

#### Controlling Parallelism

Override the number of parallel workers:

```bash
# Use AUTO (default - recommended)
repo-lint check

# Explicitly set worker count
repo-lint check --jobs 4
repo-lint check -j 4

# Use environment variable
REPO_LINT_JOBS=4 repo-lint check

# Disable parallelism (sequential execution)
repo-lint check --jobs 1
# OR
REPO_LINT_DISABLE_CONCURRENCY=1 repo-lint check
```

**Precedence**: CLI `--jobs` > `REPO_LINT_JOBS` env var > AUTO

#### Safety Controls

When you request more workers than the AUTO maximum, `repo-lint` shows a warning banner but **honors your explicit
request**:

```bash
repo-lint check --jobs 50
# ⚠️  Requested 50 workers exceeds safe AUTO max 3
# ⚠️  Proceeding with 50 workers as explicitly requested via --jobs=50
# ⚠️  High worker counts may cause resource exhaustion and flaky CI
```

**Optional hard cap** (disabled by default):

```bash
# Enforce AUTO maximum even for explicit requests
REPO_LINT_HARD_CAP_JOBS=1 repo-lint check --jobs 50
# Will cap to AUTO maximum with warning
```

#### Debug and Diagnostics

```bash
# Show per-runner timing information
REPO_LINT_DEBUG_TIMING=1 repo-lint check

# Enable tool-level parallelism within each runner (experimental)
REPO_LINT_TOOL_PARALLELISM=1 repo-lint check
```

#### Progress Bar

Show a Rich progress bar during parallel execution:

```bash
repo-lint check --progress
```

**Note**: Progress bars are auto-disabled in CI environments and non-TTY contexts unless explicitly enabled with
`--progress`.

#### Deterministic Output

Parallel execution maintains deterministic, stable output:

- - - Final violation results are buffered and reported in runner registration order - Exit codes and violation counts
  are identical to sequential execution - Same violations reported regardless of `--jobs` value - - Aggregated summary
  output is deterministic

#### Performance Impact

Example on a 4-CPU system:

- - **Sequential** (`--jobs 1`): ~45s - - **Parallel** (AUTO, 3 workers): ~27s (**40% faster**) - With tool-level
  parallelism: ~26s (**43% faster**)

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
repo-lint check --lang python

# Check only Bash scripts
repo-lint check --lang bash

# Check only YAML files
repo-lint check --lang yaml

# Check only PowerShell scripts
repo-lint check --lang powershell

# Check only Perl scripts
repo-lint check --lang perl

# Check only Rust files
repo-lint check --lang rust
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

### 6. Tool Discovery and Help

Discover what languages and tools are supported:

```bash
# List all supported languages
repo-lint list-langs

# List all available linting tools
repo-lint list-tools

# List tools for a specific language
repo-lint list-tools --lang python
repo-lint list-tools --lang bash

# Get detailed help for a specific tool
repo-lint tool-help black
repo-lint tool-help shellcheck
```

Example output from `tool-help`:

```
$ repo-lint tool-help ruff
Tool: ruff
Language: python
Description: Fast Python linter (replaces flake8, isort)
Fix capable: Yes
Version: 0.8.4
Config: pyproject.toml
```

### 7. Environment Diagnostics

Check your repo-lint installation and environment:

```bash
# Run comprehensive diagnostics
repo-lint doctor

# Output in different formats
repo-lint doctor --format json
repo-lint doctor --format yaml

# Save diagnostics to a file
repo-lint doctor --report diagnostics.txt

# CI mode (exit 0 if all checks pass, 1 if any fail)
repo-lint doctor --ci
```

The `doctor` command checks:

- - - Repository root detection - Virtual environment configuration - Tool registry loading - Config file validity -
  Tool availability (black, ruff, shellcheck, etc.) - PATH configuration

---

### 8. Environment and PATH Management

`repo-lint` provides three commands to help manage your virtual environment and make `repo-lint` available in your
shell.

#### Show Environment Information (`which`)

Displays diagnostic information about your repo-lint installation:

```bash
# Show human-readable environment info
repo-lint which

# Get JSON output for scripting
repo-lint which --json
```

Output includes:

- - - Repository root directory - Resolved virtual environment path - Bin/Scripts directory (where executables live) -
  Activation script path - repo-lint executable location - Python executable location - sys.prefix and sys.base_prefix
  (venv detection) - Detected shell (for completion setup)

**Use cases:**

- - - Debug PATH or venv configuration issues - Verify repo-lint installation location - Check which Python is being
  used - Identify current shell for completion setup

#### Generate Shell Integration (`env`)

Generates shell snippets to add repo-lint to your PATH:

```bash
# Show instructions for current shell
repo-lint env

# Generate PowerShell snippet
repo-lint env --shell powershell

# Save snippet to config directory (Linux/macOS: ~/.config/repo-lint/shell/)
repo-lint env --install --shell bash

# Get just the PATH line for scripting (automation-friendly)
repo-lint env --path-only
```

**Important:** The `env` command does NOT automatically edit your shell rc files (by design). You must manually add the
snippet to make it permanent.

**Manual RC editing:**

- - **Bash:** Add to `~/.bashrc` - **Zsh:** Add to `~/.zshrc` - **Fish:** Add to `~/.config/fish/config.fish` -
  **PowerShell:** Add to `$PROFILE`

Example workflow:

```bash
# 1. Generate and save snippet
repo-lint env --install --shell bash

# 2. Follow printed instructions to add to ~/.bashrc
source ~/.config/repo-lint/shell/repo-lint.bash

# 3. Reload shell
source ~/.bashrc
```

#### Launch Subshell with Venv (`activate`)

Spawns a new shell with the repo-lint virtual environment activated:

```bash
# Launch interactive bash with venv activated
repo-lint activate

# Run single command in venv (non-interactive)
repo-lint activate --command "repo-lint check --ci"

# Launch PowerShell with venv activated
repo-lint activate --shell powershell

# CI mode: run command without interactive shell
repo-lint activate --ci --command "pytest"

# Print command without executing
repo-lint activate --print
```

**Use cases:**

- - - Quickly activate venv without manual source command - Run single command in venv context (use `--command`) - -
  Test venv activation in different shells - CI/CD automation (use `--ci --command`)

**Options:**

- - `--venv <path>`: Use explicit venv path (overrides auto-detection) - `--shell <shell>`: Launch specific shell (bash,
  zsh, fish, powershell, cmd) - `--command "<cmd>"`: Run single command, exit when done - `--no-rc`: Start shell without
  loading user rc files - `--print`: Show command without executing - `--ci`: CI mode - requires `--command`, blocks
  interactive shells

**Virtual Environment Resolution:**

All three commands (`which`, `env`, `activate`) use the same venv resolution precedence:

1. 1. Explicit `--venv` flag (highest priority) 2. `.venv/` directory under repository root 3. 3. Currently active
   Python virtual environment (sys.prefix) 4. Error if none found (lowest priority)

---

## Test Fixtures and Vector Mode

### What Are Fixture Files

**Fixture files** in `repo-lint` are **intentionally broken** code files that serve as **canonical test vectors** for
validating that the linting infrastructure correctly detects violations.

#### Purpose

These files exist to:

- - **Test the linters themselves**: Ensure `repo-lint` runners correctly invoke tools like `black`, `ruff`,
  `shellcheck`, `clippy`, etc. - - **Validate violation detection**: Confirm that violation messages, file names, and
  line numbers are accurately reported - **Provide conformance testing**: Enable "vector mode" testing where the tool
  scans intentionally bad code - **Document expected behavior**: Serve as living examples of what each linter should
  catch

#### Critical Understanding

⚠️ **FIXTURES ARE NOT PRODUCTION CODE** ⚠️

- - - Fixtures contain **intentional violations** (unused variables, missing docstrings, bad formatting, etc.) - Every
  violation is **deliberate** and **required** for testing - These files should **NEVER** be "fixed" or reviewed as if
  they were production code - Running formatters or linters directly on fixtures would destroy their purpose

#### Why CI Excludes Fixtures by Default

In normal operation (including `--ci` mode), `repo-lint` **automatically excludes** all fixture files from scanning.
This prevents:

- - - False positive violations in CI builds - Confusion about code quality ("Why are there 40 violations in the repo?")
  - Accidental "fixes" that would break the test suite - Performance overhead from scanning test artifacts

Fixtures are **only** scanned when explicitly requested via `--include-fixtures` (vector mode).

---

### Where Fixture Files Live

All fixture files are located within the `repo-lint` package itself:

```
tools/repo_lint/tests/fixtures/
├── bash/
│   ├── all-docstring-violations.sh
│   ├── shellcheck-violations.sh
│   ├── shfmt-violations.sh
│   └── naming_violations.sh          # Intentionally violates Bash naming (snake_case)
├── perl/
│   ├── all_docstring_violations.pl
│   ├── perlcritic_violations.pl
│   └── naming-violations.pl          # Intentionally violates Perl naming (kebab-case)
├── powershell/
│   ├── AllDocstringViolations.ps1
│   ├── PsScriptAnalyzerViolations.ps1
│   └── naming-violations.ps1         # Intentionally violates PowerShell naming (kebab-case)
├── python/
│   ├── all_docstring_violations.py
│   ├── black_violations.py
│   ├── pylint_violations.py
│   ├── ruff_violations.py
│   ├── naming-violations.py          # Intentionally violates Python naming (kebab-case)
│   ├── *.RESET.diff                  # Audit trail diffs (see below)
├── rust/
│   ├── all-docstring-violations.rs
│   ├── clippy-violations.rs
│   └── rustfmt-violations.rs
└── yaml/
    ├── all-docstring-violations.yaml
    ├── actionlint-violations.yaml
    └── yamllint-violations.yaml
```

#### Why Fixtures Are Colocated with Tests

Fixtures live in `tools/repo_lint/tests/fixtures/` (not in a top-level `examples/` or `samples/` directory) because:

- - - They are **test artifacts**, not user-facing examples - They are tightly coupled to the integration tests in
  `tools/repo_lint/tests/test_fixture_vector_mode.py` - - They must be excluded from normal repository scans - They are
  part of the `repo-lint` package's internal test infrastructure

This location makes it clear these are **testing tools**, not documentation or samples.

---

### Vector Mode (`--include-fixtures`)

**Vector mode** is a special operating mode where `repo-lint` includes fixture files in its scans. This mode exists
exclusively for **testing and validating** the linting infrastructure itself.

#### What Vector Mode Is

When you run `repo-lint` with the `--include-fixtures` flag:

- - All fixture files under `tools/repo_lint/tests/fixtures/` are **included** in the scan - - The tool runs all
  configured linters against these intentionally broken files - Violations are detected and reported just like they
  would be for normal code - This validates that the linting infrastructure is working correctly

#### Why Vector Mode Exists

Vector mode enables:

1. 1. **Conformance testing**: Verify that `repo-lint` correctly detects all expected violations 2. 2. **Regression
   testing**: Ensure linter integration doesn't break over time 3. **CI validation**: Automated tests can verify the
   fixture system works as expected 4. **Development debugging**: When adding new linters, test against known bad code

#### When to Use `--include-fixtures`

Use vector mode when:

- - Running integration tests (`pytest tools/repo_lint/tests/test_fixture_vector_mode.py`) - - Debugging linter
  integration issues - Validating that a new linter correctly detects violations - Testing changes to runner code

**DO NOT** use vector mode for:

- - - Normal development workflows - Pre-commit hooks - CI builds (unless explicitly testing the fixture system) - Code
  quality checks

#### How Vector Mode Changes Behavior

| Mode | Fixtures Scanned? | Use Case |
| ------ | ------------------- | ---------- |
| **Normal** (`repo-lint check`) | ❌ No | Daily development |
| **CI Mode** (`repo-lint check --ci`) | ❌ No | CI/CD pipelines |
| **Vector Mode** (`repo-lint check --include-fixtures`) | ✅ **Yes** | Testing linting infrastructure |

---

### Concrete CLI Examples

#### Normal Mode (Fixtures Excluded)

```bash
# Standard development check - fixtures are automatically excluded
$ repo-lint check
🔍 Running repository linters and formatters...
✅ All checks passed! (0 violations)
```

Fixtures are **not scanned**. Only production code is checked.

#### CI Mode (Fixtures Excluded)

```bash
# CI pipeline check - fixtures are automatically excluded
$ repo-lint check --ci
🔍 Running repository linters and formatters...
✅ All checks passed! (0 violations)
```

Same as normal mode - fixtures remain excluded. This is the **correct** behavior for CI.

If you see fixture violations in CI output, that indicates a **bug** in the exclusion logic.

#### Vector Mode (Fixtures Included)

```bash
# Test mode - explicitly include fixtures to validate linting infrastructure
$ repo-lint check --include-fixtures --lang python
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Python Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Runner                Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────────
  black                 ✅ PASS      20            0       0.2s
  ruff                  ❌ FAIL      20           45       0.3s
  pylint                ❌ FAIL      20           67       1.2s
  validate_docstrings   ❌ FAIL      20           23       0.1s

❌ Found 135 violations across 4 runners
```

Fixtures **are scanned**, and violations **are expected**. This validates that the linters are working correctly.

#### Vector Mode for All Languages

```bash
# Scan all fixture files across all languages
$ repo-lint check --include-fixtures

# Expected output: hundreds of intentional violations detected
# This is CORRECT - it proves the linters are working
```

#### Vector Mode with Specific Languages

```bash
# Test only Bash fixtures
$ repo-lint check --include-fixtures --lang bash

# Test only Rust fixtures
$ repo-lint check --include-fixtures --lang rust

# Test multiple languages (use --lang multiple times)
$ repo-lint check --include-fixtures --lang python --lang yaml
```

---

### Fixture Immutability Guarantees

Fixture files are considered **canonical test vectors** and must **never** be modified by automated tools.

#### Why Fixtures Are Canonical

- - - Each violation in a fixture file is **deliberate** and **documented** - Changing a fixture could break integration
  tests - Fixtures serve as the "source of truth" for what violations should be detected - Auto-fixing a fixture would
  destroy its value as a test vector

#### How CI Enforces Immutability

The repository has **multiple safeguards** to prevent fixtures from being modified:

1. 1. 1. **Black Auto-Fix Workflow**: Hardcoded regex exclusion

   ```yaml

 --exclude='(tools/repo_lint/tests/fixtures/ | conformance/repo-lint/fixtures/ | ...)'

   ```

   Black's auto-formatter will **never** touch fixture files, even if they violate formatting rules.

2. 2. 2. **Naming Enforcement Workflow**: Explicit file exclusions

   ```python
   if any(part in path for part in ['naming-violations.py', 'naming-violations.pl', ...]):
       continue  # Skip naming violation test files
   ```

   The naming enforcer skips dedicated `naming-violations.*` test files (which intentionally use wrong naming conventions).

1. 1. 1. **Default Exclusion in repo-lint**: Built-in protection - All runners have `include_fixtures=False` by default
   - Fixtures are excluded unless `--include-fixtures` is explicitly provided - - This prevents accidental scanning or
   fixing

#### What Are `*.RESET.diff` Files

In the Python fixtures directory, you'll find files like:

- - `all-docstring-violations.py.RESET.diff` - `black-violations.py.RESET.diff` - `pylint-violations.py.RESET.diff` -
  `ruff-violations.py.RESET.diff`

These are **audit trail artifacts** that document the complete history of changes to fixture files:

- - - They show the diff from the original fixture state to the current state - They serve as a record of intentional
  modifications (e.g., adding disclaimers, renaming files) - They help maintainers understand what changed and why -
  They are regenerated whenever fixtures are intentionally updated

**These diff files are for reference only** - they are not executed or parsed by the tool.

---

### Per-Language Fixture Breakdown

This section details **exactly** what fixture files exist for each language, what they test, and why.

#### Python Fixtures

**Location**: `tools/repo_lint/tests/fixtures/python/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `python_all_docstring_violations.py` | `validate_docstrings` | Missing module docstring, missing function docstrings, missing class docstrings, missing method docstrings | Validates docstring enforcement across all Python construct types (module, function, class, method) |
| `python_black_violations.py` | `black` | Line length violations, inconsistent quotes, missing whitespace, wrong number of blank lines | Tests Black formatter detection across various formatting issues |
| `python_pylint_violations.py` | `pylint` | Unused variables, unused imports, too many local variables, redefined builtins, too few public methods | Validates pylint's detection of code quality issues and style violations |
| `python_ruff_violations.py` | `ruff` | Unused imports (F401), unused local variables (F841), line too long (E501), redefinition of unused name (F811), mutable default argument (B006) | Tests ruff's comprehensive linting rules including Pyflakes, pycodestyle, and flake8-bugbear rules |
| `python-naming-violations.py` | Naming enforcement | Uses kebab-case filename instead of snake_case, classes not in PascalCase, functions not in snake_case, constants not in UPPER_CASE | **Intentionally** violates Python naming conventions to test that naming enforcement correctly identifies violations |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file (e.g.,
`python_black_violations.py.RESET.diff`) that can restore the fixture to its canonical "bad" state after auto-fixing
tools have been run on it.

**Key Violations Tested**:

- - **Unused imports**: `import os` when `os` is never used - **Bad comparisons**: `list = [1, 2, 3]` (redefining
  builtin) - - **Missing docstrings**: Functions/classes without documentation - **Formatting**: Lines that are too
  long, inconsistent indentation, etc.

**Why These Violations**: These are the most common Python code quality issues that linters should catch. By testing
against these specific patterns, we ensure the runners correctly invoke and parse tool output.

#### Bash Fixtures

**Location**: `tools/repo_lint/tests/fixtures/bash/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `bash-docstring-violations.sh` | `validate_docstrings` | Missing file-level comments, missing function documentation | Validates Bash docstring enforcement for scripts and functions |
| `bash-shellcheck-violations.sh` | `shellcheck` | SC2086 (unquoted variable expansion), SC2155 (declare and assign separately), SC2034 (unused variable), SC2164 (cd without error checking) | Tests shellcheck's detection of common Bash scripting pitfalls and best practice violations |
| `bash-shfmt-violations.sh` | `shfmt` | Inconsistent indentation (tabs vs spaces), missing space in if statement, bad case statement formatting | Validates shfmt's formatting checks for Bash scripts |
| `bash_naming_violations.sh` | Naming enforcement | camelCase and PascalCase function names instead of snake_case, kebab-case function names | **Intentionally** violates Bash naming conventions to test naming enforcement |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file that can restore the fixture to its canonical
"bad" state after auto-fixing tools have been run on it.

**Key Violations Tested**:

- - **Unquoted variables**: `echo $my_var` instead of `echo "$my_var"` (can cause word splitting/globbing issues) - -
  **Unused variables**: Variables declared but never referenced - **Improper cd usage**: `cd /tmp` without error
  handling

**Why These Violations**: Shellcheck catches critical bugs that can cause scripts to fail in production. These test
cases ensure the Bash runner correctly identifies these issues.

#### Perl Fixtures

**Location**: `tools/repo_lint/tests/fixtures/perl/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `perl_docstring_violations.pl` | `validate_docstrings` | Missing POD documentation, missing subroutine documentation | Validates Perl docstring enforcement using POD (Plain Old Documentation) format |
| `perl-perlcritic_violations.pl` | `perlcritic` | Excessive complexity, using @_ directly, using punctuation variables | Tests perlcritic's "Perl Best Practices" policy enforcement |
| `perl-perlNamingViolations.pl` | Naming enforcement | camelCase, ALLUPPERCASE, and mixedCase function names; PascalCase variable names | **Intentionally** violates Perl naming conventions to test naming enforcement |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file that can restore the fixture to its canonical
"bad" state.

**Key Violations Tested**:

- - - **Excessive complexity**: Functions with too many branches - **Using @_ directly**: `print $_[0]` instead of
  unpacking arguments - **Punctuation variables**: Using `$_` without clear context

**Why These Violations**: Perlcritic enforces best practices that make Perl code more maintainable and less error-prone.
These fixtures test that the Perl runner correctly applies these policies.

#### PowerShell Fixtures

**Location**: `tools/repo_lint/tests/fixtures/powershell/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `PowershellAllDocstringViolations.ps1` | `validate_docstrings` | Missing function comments, missing `.SYNOPSIS`, incomplete help blocks | Validates PowerShell docstring enforcement using comment-based help |
| `PowershellPsScriptAnalyzerViolations.ps1` | `PSScriptAnalyzer` | Unused variables, using aliases instead of full cmdlet names, positional parameters, missing ShouldProcess support | Tests PSScriptAnalyzer's PowerShell best practices and cmdlet development standards |
| `Powershell-naming-violations.ps1` | Naming enforcement | Functions without Verb-Noun naming, unapproved verbs, missing verbs, snake_case variables instead of PascalCase | **Intentionally** violates PowerShell naming conventions to test naming enforcement |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file that can restore the fixture to its canonical
"bad" state.

**Key Violations Tested**:

- - **Unused variables**: `$UnusedVariable = "never used"` - **Aliases**: Using `gci` instead of `Get-ChildItem` - -
  **Positional parameters**: Not using named parameters - **Missing ShouldProcess**: Remove-* functions without
  -WhatIf/-Confirm support

**Why These Violations**: PowerShell has strict conventions for module and cmdlet development. These fixtures ensure the
PowerShell runner enforces these standards.

#### YAML Fixtures

**Location**: `tools/repo_lint/tests/fixtures/yaml/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `yaml-all-docstring-violations.yaml` | `validate_docstrings` | Missing file-level comments, missing section documentation | Validates YAML docstring enforcement (expecting top-of-file comments) |
| `yaml-actionlint-violations.yaml` | `actionlint` | Using deprecated set-output command, missing shell specification, deprecated action versions | Tests actionlint's validation of GitHub Actions workflow files |
| `yaml-yamllint-violations.yaml` | `yamllint` | Line too long, trailing spaces, inconsistent indentation, missing document start marker | Validates yamllint's YAML formatting and style enforcement |
| `yaml_naming_violations.yaml` | Naming enforcement | camelCase, PascalCase, and ALL_CAPS keys with inconsistent naming styles | **Intentionally** violates YAML naming conventions to test naming enforcement |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file that can restore the fixture to its canonical
"bad" state.

**Key Violations Tested**:

- - - **Line too long**: Lines exceeding configured maximum - **Trailing whitespace**: Spaces at end of lines -
  **Inconsistent indentation**: Wrong indentation levels - **Deprecated Actions syntax**: Old workflow commands

**Why These Violations**: YAML is whitespace-sensitive and easy to break. These fixtures test that the YAML runner
catches common formatting and syntax errors.

#### Rust Fixtures

**Location**: `tools/repo_lint/tests/fixtures/rust/`

| File | Tool(s) Tested | Violation Categories | Purpose |
| ------ | ---------------- | --------------------- | --------- |
| `rust-all-docstring.violations.rs` | `validate_docstrings` | Missing module docs (`//!`), missing function docs, missing struct docs, missing impl docs, missing method docs | Validates Rust docstring enforcement for modules, functions, structs, and public APIs |
| `rust-clippy-violations.rs` | `clippy` | Needless return, unnecessary clone, manual string formatting, comparison to bool | Tests clippy's lint suggestions for idiomatic Rust code |
| `rust-rustfmt-violations.rs` | `rustfmt` | Bad spacing in function signatures, inconsistent indentation, bad brace placement | Validates rustfmt's formatting checks for Rust code |
| `rustNamingViolations.rs` | Naming enforcement | bad_struct_name (should be PascalCase), BadFunctionName (should be snake_case), badConstant (should be SCREAMING_SNAKE_CASE) | **Intentionally** violates Rust naming conventions to test naming enforcement |

**RESET.diff Files**: Each fixture has a corresponding `.RESET.diff` file that can restore the fixture to its canonical
"bad" state after auto-fixing tools have been run on it.

**Key Violations Tested**:

- - **Missing docs**: Public functions without `///` doc comments, modules without `//!` - **Clippy lints**: `return x +
  1` instead of `x + 1`, unnecessary `.clone()` calls - **Formatting**: Bad spacing like `fn bad_formatting(
  x:i32,y:i32  )->i32{`

**Why These Violations**: Rust has strong conventions for documentation and idiomatic code. These fixtures ensure the
Rust runner enforces these standards and correctly integrates with `clippy` and `rustfmt`.

---

### Using RESET.diff Files

Each fixture file has a corresponding `.RESET.diff` file that can restore the fixture to its original "bad" (violating)
state after auto-fixing tools have been run on it.

#### What are RESET.diff files

RESET.diff files are git-format patch files that contain the difference between the "fixed" state (after running
auto-formatters) and the "bad" state (with intentional violations). They allow you to restore fixtures to their
canonical violating state.

#### When to use RESET.diff files

Use RESET.diff files when:

- - You've accidentally run an auto-fixer (like `black`, `rustfmt`, `shfmt`) on fixture files - - You want to verify
  that fixtures still contain their intended violations - You need to reset fixtures to a known state for testing

#### How to apply a RESET.diff file

To restore a single fixture:

```bash
# Example: Restore Python black violations fixture
git apply --whitespace=nowarn tools/repo_lint/tests/fixtures/python/python_black_violations.py.RESET.diff
```

To restore all fixtures in a language:

```bash
# Example: Restore all Python fixtures
for diff in tools/repo_lint/tests/fixtures/python/*.RESET.diff; do
    git apply --whitespace=nowarn "$diff"
done
```

To restore ALL fixtures:

```bash
# Restore all fixtures across all languages
find tools/repo_lint/tests/fixtures -name "*.RESET.diff" -exec git apply --whitespace=nowarn {} \;
```

#### Verifying fixture integrity

After applying RESET.diff files, verify that fixtures contain violations:

```bash
# Check that fixtures trigger violations when scanned
repo-lint check --include-fixtures --ci
```

You should see violations detected in the fixture files.

---

### Common Mistakes and Warnings

#### ⚠️ DO NOT Submit PRs to "Fix" Fixture Violations

**WRONG**:

```bash
# DO NOT DO THIS
$ repo-lint fix
# Sees fixture violations and "fixes" them
$ git add tools/repo_lint/tests/fixtures/
$ git commit -m "fix: resolve linting violations in test fixtures"
```

**This would break the test suite!** Fixtures are **intentionally broken**. "Fixing" them destroys their purpose.

#### ⚠️ Fixtures Are NOT Examples

Do **NOT** use fixture files as examples of how to write code. They demonstrate **anti-patterns** and **bad practices**.

**For examples**, see:

- - Repository's actual source code (`tools/repo_lint/`) - Documentation in `docs/` - Test files in `tests/` (excluding
  `fixtures/`)

Fixtures show **what NOT to do**, not best practices.

#### ⚠️ DO NOT Run Formatters Directly on Fixture Paths

**WRONG**:

```bash
# DO NOT DO THIS
$ black tools/repo_lint/tests/fixtures/python/
$ ruff check --fix tools/repo_lint/tests/fixtures/python/
$ shellcheck --fix tools/repo_lint/tests/fixtures/bash/*.sh
```

Running formatters or auto-fixers directly on fixture files will destroy their intentional violations.

**CORRECT**:

```bash
# Use repo-lint in normal mode (fixtures are automatically excluded)
$ repo-lint check
$ repo-lint fix

# Or explicitly exclude fixtures when using tools directly
$ black --exclude='tests/fixtures' .
```

#### ⚠️ If You See Fixture Violations in CI, That's a Bug

**CORRECT CI OUTPUT**:

```bash
$ repo-lint check --ci
✅ All checks passed! (0 violations)
```

**INCORRECT CI OUTPUT (BUG)**:

```bash
$ repo-lint check --ci
❌ Found 135 violations
  - tools/repo_lint/tests/fixtures/python/ruff_violations.py: 45 violations
  - tools/repo_lint/tests/fixtures/python/pylint_violations.py: 67 violations
  - ...
```

If you see fixture violations in CI logs (without `--include-fixtures`), this indicates:

- - - A bug in the exclusion logic - A regression in the `include_fixtures` parameter handling - - An incorrect workflow
  configuration

**Report this immediately** - it violates the fixture immutability contract.

#### ⚠️ DO NOT Modify Fixtures Without Updating Tests

If you need to modify a fixture file (e.g., to add a new violation category):

1. 1. 1. Update the fixture file 2. Update integration tests in `tools/repo_lint/tests/test_fixture_vector_mode.py` 3.
   Regenerate `*.RESET.diff` files for audit trail 4. 4. Document the change in the commit message

**Never** modify fixtures casually - they are part of the test infrastructure.

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

# Should show: --ci, --json, --lang, --verbose, --help
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

- - Remove `--unsafe` flag in CI environments - Use `--yes-i-know` with `--unsafe` in local environments - - Read
  docs/contributing/ai-constraints.md before using unsafe mode

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

- - `conformance/repo-lint/repo-lint-naming-rules.yaml` - Filename conventions -
  `conformance/repo-lint/repo-lint-docstring-rules.yaml` - Docstring requirements -
  `conformance/repo-lint/repo-lint-linting-rules.yaml` - Linter configurations -
  `conformance/repo-lint/repo-lint-file-patterns.yaml` - File discovery patterns

Edit these files to customize rules for your repository.

#### Viewing Current Configuration

To see the complete resolved configuration:

```bash
# View in YAML format (human-readable)
repo-lint dump-config

# View in JSON format (machine-readable)
repo-lint dump-config --format json

# View configuration from a custom directory
repo-lint dump-config --config /path/to/custom/configs
```

The `dump-config` command shows:

- - - All configuration files merged together - The source of the configuration (default, environment variable, or
  custom path) - Current values for all tools, rules, and settings

#### Validating Configuration Files

Before committing configuration changes, validate them:

```bash
# Validate a specific config file
repo-lint validate-config conformance/repo-lint/repo-lint-linting-rules.yaml

# Validate returns exit 0 if valid, exit 1 if invalid
# Perfect for CI/CD validation gates:
repo-lint validate-config my-config.yaml && echo "Config valid!"
```

The `validate-config` command checks:

- - YAML document markers (`---` and `...`) - Required fields (`config_type`, `version`, `languages`) - - Unknown or
  misspelled keys (strict validation) - Semantic version format - Config-type-specific schema requirements

#### Configuration Precedence

repo-lint loads configuration in this order (highest priority first):

1. 1. **Custom directory** via `--config <PATH>` flag 2. **Environment variable** `REPO_LINT_CONFIG_DIR` 3. **Default
   location** `conformance/repo-lint/` in repository root

Example using custom configuration:

```bash
# Use configs from a different location via environment variable
export REPO_LINT_CONFIG_DIR=/path/to/custom/configs
repo-lint check

# The --config flag is available only for dump-config command
repo-lint dump-config --config /path/to/custom/configs
```

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

      - name: Run repo-lint (uses AUTO parallelism by default)
        run: repo-lint check --ci --json
        # Parallel execution is enabled by default
        # AUTO will use min(max(cpu_count-1, 1), 8) workers

      # Optional: Explicit worker count for deterministic CI performance
      - name: Run repo-lint with explicit worker count
        run: repo-lint check --ci --jobs 4
        # OR use environment variable:
        # env:
        #   REPO_LINT_JOBS: 4
```

#### CI Parallelism Recommendations

**For stable CI performance**, consider setting an explicit worker count:

```yaml
env:
  REPO_LINT_JOBS: 4  # Explicit count for reproducible CI timing
```

**For maximum speed with variable runners**, rely on AUTO:

```yaml
# No --jobs flag - uses AUTO based on runner CPU count
run: repo-lint check --ci
```

**To disable parallelism** (if needed for troubleshooting):

```yaml
env:
  REPO_LINT_DISABLE_CONCURRENCY: 1
```

### Environment Variables

repo-lint supports environment variable configuration:

```bash
# Parallelism controls
export REPO_LINT_JOBS=4                      # Override worker count
export REPO_LINT_DISABLE_CONCURRENCY=1       # Force sequential execution
export REPO_LINT_HARD_CAP_JOBS=1             # Enforce AUTO cap on explicit values
export REPO_LINT_DEBUG_TIMING=1              # Show per-runner timing
export REPO_LINT_TOOL_PARALLELISM=1          # Enable tool-level parallelism (experimental)

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

- - - **Rich formatting** with colors, tables, and panels - **Icons** for status indicators (✓, ✗, ⚠️) - **Progress
  indicators** and spinners for long operations - **Styled help** output with syntax highlighting

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

- - - **Plain text** output without colors or formatting - **No icons** or progress indicators - **Stable,
  deterministic** output for log parsing - **Greppable** format for automated analysis

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

- - - GitHub Actions, GitLab CI, Jenkins, or other CI/CD - Redirecting output to files: `repo-lint check > results.txt`
  - - Scripting and automation where stable output is needed - Windows Command Prompt (if Rich rendering has issues)

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

1. 1. `--theme` flag 2. `REPO_LINT_UI_THEME` environment variable 3. User theme:
   `~/.config/repo-lint/repo-lint-ui-theme.yaml` 4. Repository theme: `conformance/repo-lint/repo-lint-ui-theme.yaml` 5.
   5. Built-in default theme

#### Available Color Names

- - Standard: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` - Bright: `bright_black`,
  `bright_red`, `bright_green`, `bright_yellow`, `bright_blue`, `bright_magenta`, `bright_cyan`, `bright_white` -
  Special: `dim` (dimmed text), `bold` (bold text)

#### Available Border Styles

- - `ascii` - Simple ASCII characters (`+`, `-`, ` | `) - `rounded` - Rounded corners (╭, ╮, ╰, ╯) - `heavy` - Heavy
  borders (┏, ┓, ┗, ┛) - `double` - Double-line borders (╔, ╗, ╚, ╝)

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

- - - Colored text and panels - Tables for command lists - Syntax highlighting for examples

### Documentation

- - **Contributing Guide:** `docs/contributing/README.md` - **AI Constraints:** `docs/contributing/ai-constraints.md` -
  **Naming Conventions:** `docs/contributing/naming-and-style.md` - **Configuration:** `conformance/repo-lint/README.md`

### Reporting Issues

If you encounter bugs or have feature requests:

1. Check existing issues: <https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues>
2. 2. 2. Create a new issue with: - Command that failed - Full error message - Python version (`python --version`) -
   repo-lint version (`repo-lint --version`) - - Operating system

---

## Summary of Exit Codes

| Code | Meaning | Action |
| ------ | --------- | -------- |
| 0 | Success | All checks passed |
| 1 | Violations found | Fix issues and re-run |
| 2 | Missing tools (CI) | Install required tools |
| 3 | Internal error | Check error message and logs |
| 4 | Unsafe violation | Review unsafe mode requirements |

---

**Version:** 0.1.0
**Last Updated:** 2025-12-31
**Maintained by:** Ryan Bell
