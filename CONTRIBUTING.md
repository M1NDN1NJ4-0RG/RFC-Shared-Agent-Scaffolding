# Contributing to RFC-Shared-Agent-Scaffolding

Thank you for your interest in contributing! This repository implements the RFC-Shared-Agent-Scaffolding contract
(v0.1.0) - a restartable, failure-resilient operating model for AI coding agents.

## Quick Start

1. 1. 1. 1. **Read the documentation** - Start with [docs/README.md](./docs/README.md) for an overview 2. **Review the
   RFC** - [rfc-shared-agent-scaffolding-v0.1.0.md](./rfc-shared-agent-scaffolding-v0.1.0.md) defines the contract
3. **Check the roadmap** - [EPIC #33](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33) tracks the Rust canonical tool implementation
4. 4. 4. **Install linting tools** - Run `python3 -m tools.repo_lint install` (or `./scripts/run-linters.sh --install`)
   5. 5. **Before every commit:** - Run `python3 -m tools.repo_lint check` to lint all code - - Run relevant test suites
   for code you changed - Verify all CI checks pass 6. **Follow the guidelines** - See detailed contributing guide below

## Essential Documentation

### For Contributors

🛠️ **[Bootstrapper Toolchain User Manual](./docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md)** -
Session-start compliance and toolchain setup

- - - - Bootstrapping repo-lint and all development tools - Virtual environment setup - Platform-specific installation
  (macOS/Linux) - Troubleshooting and verification

📝 **[Contributing Guide](./docs/contributing/contributing-guide.md)** - Complete guide to contributing

- - - - Workflow and PR process - Code style and conventions - Testing requirements - Review process

📋 **[Docstring Contracts](./docs/contributing/docstring-contracts/README.md)** - Required documentation standards

- - - - Language-specific templates - Required sections and format - Examples and validation - **All scripts must follow
  their language contract**

🤖 **[AI Agent Constraints](./docs/contributing/ai-constraints.md)** - Safety rules for AI agents

- - - - Prohibited dangerous commands (unsafe fixes, destructive operations) - Required escalation procedures -
  Human-only vs AI-allowed operations - **AI agents must follow these constraints**

### For Testing

🧪 **[Testing Documentation](./docs/testing/)** - How to run and write tests

- - - - Rust canonical tool tests - Wrapper tests (Bash, Perl, Python, PowerShell) - Conformance testing - CI/CD
  pipeline

### For Architecture Understanding

🏗️ **[Architecture Documentation](./docs/architecture/)** - System design and structure

- - - - Canonical directory structure - Rust canonical tool design - Wrapper discovery algorithm - Cross-platform
  considerations

## Key Contribution Rules

### File Naming Conventions

**Language-specific script files follow their ecosystem conventions:**

```bash
# Python scripts (snake_case)
✅ Good: safe_run.py, test_helpers.py, validate_docstrings.py
❌ Bad: safe-run.py, SafeRun.py

# PowerShell scripts (PascalCase)
✅ Good: SafeRun.ps1, TestHelpers.ps1
❌ Bad: safe-run.ps1, safe_run.ps1

# Bash scripts (kebab-case)
✅ Good: safe-run.sh, test-helpers.sh, run-linters.sh
❌ Bad: safe_run.sh, SafeRun.sh

# Perl scripts (snake_case)
✅ Good: safe_run.pl, test_helpers.pl, run_tests.pl
❌ Bad: safe-run.pl, SafeRun.pl

# Non-script files (kebab-case)
✅ Good: contributing-guide.md, vectors.json
❌ Bad: contributing_guide.md, ContributingGuide.md
```

See [docs/contributing/naming-and-style.md](./docs/contributing/naming-and-style.md) for complete naming standards.

Enforced by CI via `.github/workflows/naming-enforcement.yml`

### Docstring Contracts (CRITICAL)

**Every script must include proper documentation headers:**

- - - **Bash** (`.sh`, `.bash`, `.zsh`) - See
  [bash-contract.md](./docs/contributing/docstring-contracts/bash-contract.md) - **PowerShell** (`.ps1`) - See
  [powershell-contract.md](./docs/contributing/docstring-contracts/powershell-contract.md) - **Python** (`.py`) - See
  [python-contract.md](./docs/contributing/docstring-contracts/python-contract.md) - **Perl** (`.pl`, `.pm`) - See
  [perl-contract.md](./docs/contributing/docstring-contracts/perl-contract.md) - **Rust** (`.rs`) - See
  [rust-contract.md](./docs/contributing/docstring-contracts/rust-contract.md)

Enforced by CI via `.github/workflows/docstring-contract.yml`

### Git Workflow

1. 1. 1. **Use `git mv` for renames** - Preserves file history 2. 2. **Keep commits focused** - One logical change per
   commit 3. **Write clear commit messages** - Describe what and why 4. **Reference issues** - Link commits to GitHub
   issues when applicable

### Testing Requirements

Before submitting a PR:

1. 1. 1. **Run linters** - `python3 -m tools.repo_lint check` (or `./scripts/run-linters.sh`) 2. 2. **Run tests** -
   Language-specific test suites must pass 3. **Run conformance** - For wrapper changes: `make conformance` 4. **Verify
   structure** - `scripts/validate-structure.sh` 5. **Check docstrings** - Automatically included in `repo-lint check`

### Code Quality and Linting

**Code Standards:**

All code must adhere to language-specific standards:

- - - - **Python**: 120-character lines, Black formatting, Ruff + Pylint compliance - **Bash**: ShellCheck warnings
  addressed, shfmt formatting - **PowerShell**: PSScriptAnalyzer error-level compliance - **Perl**: Perl::Critic
  severity 5 compliance - **YAML**: yamllint compliance

**Canonical Linting Tool: `repo-lint`**

This repository uses `repo-lint` as the **single source of truth** for all linting and docstring validation:

```bash
# Quick start - Check all code (recommended before every commit)
python3 -m tools.repo_lint check

# Auto-format code and apply safe fixes
python3 -m tools.repo_lint fix

# Install/bootstrap required linting tools locally
python3 -m tools.repo_lint install

# Thin wrapper alternative (delegates to repo-lint)
./scripts/run-linters.sh          # Runs: python3 -m tools.repo_lint check
./scripts/run-linters.sh --fix     # Runs: python3 -m tools.repo_lint fix
./scripts/run-linters.sh --install # Runs: python3 -m tools.repo_lint install
```

**REQUIRED Before Every Commit:**

1. 1. 1. Run `python3 -m tools.repo_lint check` (or `./scripts/run-linters.sh`) 2. 2. Run the full relevant test
   suite(s) for impacted code 3. Ensure CI remains green (no "commit first, lint later")

**Configuration files:**

- - - Python tools (Black, Ruff, Pylint): `pyproject.toml` - YAML: `.yamllint` - Perl: `.perlcriticrc`

All Python tools are configured for 120-character line length and compatible rule sets.

**CI behavior:**

- - - - Black formatting is **automatically applied** for same-repo PRs - For fork PRs, a patch artifact is provided if
  formatting is needed - All other linters must pass without errors

**Tool installation:**

- - - `python3 -m tools.repo_lint install` installs Python tools in a local virtual environment (`.venv-lint/`) - -
  Manual installation instructions are provided for non-Python tools (shellcheck, shfmt, PSScriptAnalyzer, Perl::Critic)
  - CI installs all tools explicitly (no auto-install in CI mode)

### Pull Request Guidelines

- - - - **Small, focused PRs** - Easier to review and merge - **Clear description** - Explain what changed and why -
  **All checks must pass** - CI validates naming, docstrings, tests, conformance - **Address review feedback** - Engage
  constructively with reviewers

## Development Setup

### Build the Rust Canonical Tool

```bash
cd rust/
cargo build --release
```

The binary will be at `rust/target/release/safe-run`

### Run Wrapper Tests

Each language wrapper has its own test suite:

```bash
# Bash
cd wrappers/bash && bash run-tests.sh

# Perl
cd wrappers/perl && bash run-tests.sh

# Python
cd wrappers/python3 && bash run-tests.sh

# PowerShell
cd wrappers/powershell && pwsh run-tests.ps1
```

### Run Conformance Tests

Validates behavioral parity across all language wrappers:

```bash
# From repository root
make conformance
```

## Repository Structure

```
.
├── rust/                 # Rust canonical tool (primary implementation)
├── wrappers/            # Language-specific wrapper scripts
│   └── scripts/
│       ├── bash/        # Bash wrappers
│       ├── perl/        # Perl wrappers
│       ├── python3/     # Python 3 wrappers
│       └── powershell/  # PowerShell wrappers
├── conformance/         # Cross-language conformance test vectors
├── docs/               # Documentation
│   ├── architecture/   # System design
│   ├── contributing/   # Contribution guidelines
│   ├── testing/        # Testing documentation
│   ├── usage/          # User guides
│   └── history/        # Historical decisions and milestones
├── scripts/            # Development and validation scripts
└── dist/               # Build artifacts (CI-generated, not committed)
```

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/discussions)
- **Bug reports?** Open a [GitHub Issue](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues)
- - - - **Security concerns?** See [SECURITY.md](./SECURITY.md) if it exists, or open a private security advisory

## Code of Conduct

Be respectful, constructive, and collaborative. We welcome contributions from everyone.

## License

This repository is licensed under the [Unlicense](./LICENSE) - it is dedicated to the public domain.

---

Thank you for contributing to RFC-Shared-Agent-Scaffolding! 🚀
