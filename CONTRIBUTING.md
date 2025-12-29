# Contributing to RFC-Shared-Agent-Scaffolding

Thank you for your interest in contributing! This repository implements the RFC-Shared-Agent-Scaffolding contract (v0.1.0) - a restartable, failure-resilient operating model for AI coding agents.

## Quick Start

1. **Read the documentation** - Start with [docs/README.md](./docs/README.md) for an overview
2. **Review the RFC** - [rfc-shared-agent-scaffolding-v0.1.0.md](./rfc-shared-agent-scaffolding-v0.1.0.md) defines the contract
3. **Check the roadmap** - [EPIC #33](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33) tracks the Rust canonical tool implementation
4. **Follow the guidelines** - See detailed contributing guide below

## Essential Documentation

### For Contributors

📝 **[Contributing Guide](./docs/contributing/contributing-guide.md)** - Complete guide to contributing
- Workflow and PR process
- Code style and conventions
- Testing requirements
- Review process

📋 **[Docstring Contracts](./docs/contributing/docstring-contracts/README.md)** - Required documentation standards
- Language-specific templates
- Required sections and format
- Examples and validation
- **All scripts must follow their language contract**

### For Testing

🧪 **[Testing Documentation](./docs/testing/)** - How to run and write tests
- Rust canonical tool tests
- Wrapper tests (Bash, Perl, Python, PowerShell)
- Conformance testing
- CI/CD pipeline

### For Architecture Understanding

🏗️ **[Architecture Documentation](./docs/architecture/)** - System design and structure
- Canonical directory structure
- Rust canonical tool design
- Wrapper discovery algorithm
- Cross-platform considerations

## Key Contribution Rules

### File Naming Conventions

**ALL files in this repository must follow kebab-case naming:**

```bash
✅ Good: safe-run.sh, test-helpers.py, my-script.pl
❌ Bad: SafeRun.sh, test_helpers.py, MyScript.pl
```

Enforced by CI via `.github/workflows/naming-kebab-case.yml`

### Docstring Contracts (CRITICAL)

**Every script must include proper documentation headers:**

- **Bash** (`.sh`, `.bash`, `.zsh`) - See [bash-contract.md](./docs/contributing/docstring-contracts/bash-contract.md)
- **PowerShell** (`.ps1`) - See [powershell-contract.md](./docs/contributing/docstring-contracts/powershell-contract.md)
- **Python** (`.py`) - See [python-contract.md](./docs/contributing/docstring-contracts/python-contract.md)
- **Perl** (`.pl`, `.pm`) - See [perl-contract.md](./docs/contributing/docstring-contracts/perl-contract.md)
- **Rust** (`.rs`) - See [rust-contract.md](./docs/contributing/docstring-contracts/rust-contract.md)

Enforced by CI via `.github/workflows/docstring-contract.yml`

### Git Workflow

1. **Use `git mv` for renames** - Preserves file history
2. **Keep commits focused** - One logical change per commit
3. **Write clear commit messages** - Describe what and why
4. **Reference issues** - Link commits to GitHub issues when applicable

### Testing Requirements

Before submitting a PR:

1. **Run linters** - See "Code Quality and Linting" section below
2. **Run tests** - Language-specific test suites must pass
3. **Run conformance** - For wrapper changes: `make conformance`
4. **Verify structure** - `scripts/validate-structure.sh`
5. **Check docstrings** - `scripts/validate_docstrings.py`

### Code Quality and Linting

**Code Standards:**

All code must adhere to language-specific standards:
- **Python**: 120-character lines, Black formatting, Flake8 + Pylint compliance
- **Bash**: ShellCheck warnings addressed, shfmt formatting
- **PowerShell**: PSScriptAnalyzer error-level compliance
- **Perl**: Perl::Critic severity 5 compliance
- **YAML**: yamllint compliance

**Quick linting commands:**

```bash
# Run all linters (Python, Bash, PowerShell, Perl, YAML)
./scripts/run-linters.sh

# Auto-format code where possible (Python, Bash)
./scripts/run-linters.sh --fix

# Or run tools individually by language:

# Python
black .                    # Auto-format
flake8 .                   # Style check
pylint **/*.py             # Static analysis

# Bash
shellcheck **/*.sh         # Shell script analysis
shfmt -d -i 2 -ci **/*.sh  # Format check

# PowerShell
pwsh -Command "Invoke-ScriptAnalyzer -Path script.ps1 -Severity Error"

# Perl
perlcritic --severity 5 **/*.pl

# YAML
yamllint .                 # Linting

# All languages
python3 scripts/validate_docstrings.py  # Docstring validation
```

**Configuration files:**
- Python Black: `pyproject.toml` (`[tool.black]`)
- Python Flake8: `.flake8`
- Python Pylint: `pyproject.toml` (`[tool.pylint.*]`)
- YAML: `.yamllint`

All Python tools are configured for 120-character line length and compatible rule sets.

**CI behavior:**
- Black formatting is **automatically applied** for same-repo PRs
- For fork PRs, a patch artifact is provided if formatting is needed
- All other linters must pass without errors

**Automatic linter installation:**
The `./scripts/run-linters.sh` script automatically installs missing linters:
- Python: black, flake8, pylint (via pip)
- Bash: shellcheck (via apt/brew), shfmt (via go install)
- PowerShell: pwsh, PSScriptAnalyzer (via apt/brew + PowerShell Gallery)
- Perl: perlcritic (via cpanm)
- YAML: yamllint (via pip)

### Pull Request Guidelines

- **Small, focused PRs** - Easier to review and merge
- **Clear description** - Explain what changed and why
- **All checks must pass** - CI validates naming, docstrings, tests, conformance
- **Address review feedback** - Engage constructively with reviewers

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
- **Security concerns?** See [SECURITY.md](./SECURITY.md) if it exists, or open a private security advisory

## Code of Conduct

Be respectful, constructive, and collaborative. We welcome contributions from everyone.

## License

This repository is licensed under the [Unlicense](./LICENSE) - it is dedicated to the public domain.

---

Thank you for contributing to RFC-Shared-Agent-Scaffolding! 🚀
