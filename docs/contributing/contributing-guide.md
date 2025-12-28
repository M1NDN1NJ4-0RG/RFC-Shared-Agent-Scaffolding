# Contributing Guide

**Last Updated:** 2025-12-28

This guide explains how to contribute to the RFC-Shared-Agent-Scaffolding repository, including conventions, required checks, and workflow standards.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Naming Conventions](#naming-conventions)
3. [Directory Structure](#directory-structure)
4. [Required Checks](#required-checks)
5. [Adding New Language Wrappers](#adding-new-language-wrappers)
6. [Testing Standards](#testing-standards)
7. [Documentation Requirements](#documentation-requirements)
8. [Pull Request Process](#pull-request-process)

---

## Getting Started

### Prerequisites

- **Rust** (1.70 or higher) - for the canonical tool
- **Python 3** (3.8 or higher) - for validation scripts
- **Git** - with history preservation via `git mv`

### Building the Project

```bash
# Build Rust canonical tool
cd rust/
cargo build --release

# Run tests
cargo test

# Run conformance tests
cargo test --test conformance
```

### Running Validation Scripts

```bash
# Validate docstrings
python3 scripts/validate-docstrings.py

# Validate structure
./scripts/validate-structure.sh

# Verify references
./scripts/verify-repo-references.sh
```

---

## Naming Conventions

**All files and directories in this repository MUST follow kebab-case naming conventions.**

### Rules

1. **Use kebab-case** (lowercase with hyphens)
   - ✅ `safe-run.sh`
   - ✅ `contributing-guide.md`
   - ❌ `Safe_Run.sh`
   - ❌ `ContributingGuide.md`

2. **Exceptions** (standard/tool-mandated names):
   - `README.md` - GitHub standard
   - `LICENSE` - Standard license file
   - `Cargo.toml`, `Cargo.lock` - Rust standard
   - `.github/`, `.gitignore`, `.flake8`, `.perlcriticrc` - Tool configs

3. **Language-specific extensions**:
   - Bash: `.sh`
   - Perl: `.pl`
   - Python: `.py`
   - PowerShell: `.ps1`
   - Rust: `.rs`

### Enforcement

Naming conventions are enforced by CI via `.github/workflows/naming-kebab-case.yml`.

---

## Directory Structure

### Canonical Structure

```
.
├── .github/          # GitHub workflows and configuration
├── conformance/      # Conformance test vectors
├── docs/             # All documentation
│   ├── architecture/ # Design documents
│   ├── contributing/ # Contributor guides
│   ├── docstrings/   # Docstring contract templates
│   ├── history/      # Historical records (EPICs, PRs, milestones)
│   ├── overview/     # High-level summaries
│   └── testing/      # Test documentation
├── rust/             # Rust canonical tool implementation
│   ├── src/          # Source code
│   └── tests/        # Rust tests
├── scripts/          # Validation and helper scripts
└── wrappers/         # Language-specific wrapper scripts
    └── scripts/      # Per-language implementations
        ├── bash/
        ├── perl/
        ├── powershell/
        └── python3/
```

### Adding Files

- **Documentation**: Add to appropriate `docs/` subdirectory
- **Scripts**: Add to `scripts/` (repo-wide) or `wrappers/scripts/<language>/scripts/` (language-specific)
- **Tests**: Add to `rust/tests/` (Rust) or `wrappers/scripts/<language>/tests/` (wrapper tests)

---

## Required Checks

Before submitting a PR, ensure all checks pass:

### 1. Naming Conventions

```bash
# Automated check - runs in CI
# Manual verification:
find . -type f -name "*" | grep -E "[A-Z_]" | grep -v -E "(README|LICENSE|Cargo|\.git)"
```

### 2. Docstring Contracts

**ALL scripts MUST conform to their language-specific docstring contract.**

```bash
# Validate all docstrings
python3 scripts/validate-docstrings.py
```

See [Docstring Contracts](#docstring-contracts) for details.

### 3. Structure Validation

```bash
# Validate directory structure
./scripts/validate-structure.sh
```

### 4. Conformance Tests

```bash
# Run Rust conformance tests
cd rust/
cargo test --test conformance
```

### 5. Wrapper Tests

```bash
# Test all wrappers
cd wrappers/scripts/bash/
./run-tests.sh

cd ../perl/
./run-tests.sh

cd ../powershell/
./run-tests.ps1

cd ../python3/
./run-tests.sh
```

### 6. Drift Detection

Strict parity is enforced across all implementations. See [allowed-drift.md](./allowed-drift.md) for policy.

---

## Adding New Language Wrappers

To add a new language wrapper:

### 1. Create Language Directory

```bash
mkdir -p wrappers/scripts/<language>/scripts
mkdir -p wrappers/scripts/<language>/tests
```

### 2. Follow Canonical Structure

See [docs/architecture/canonical-structure.md](../architecture/canonical-structure.md) for required layout:

```
wrappers/scripts/<language>/
  ├── scripts/          # Implementation scripts
  │   ├── safe-run.*
  │   ├── safe-check.*
  │   ├── safe-archive.*
  │   └── preflight-automerge-ruleset.*
  ├── tests/            # Test files
  ├── run-tests.*       # Test runner
  └── README.md         # Language-specific documentation
```

### 3. Implement Wrapper Behavior

Wrappers MUST:
- Discover the Rust canonical tool binary (see [wrapper-discovery.md](../wrapper-discovery.md))
- Pass through all arguments unchanged
- Forward exit codes exactly
- Provide actionable error messages if Rust binary is missing

### 4. Add Docstring Contract

Create a docstring contract template in `docs/contributing/docstring-contracts/<language>.md` following existing examples.

### 5. Add Conformance Tests

Wrappers must pass all conformance vectors in `conformance/vectors.json`.

### 6. Add CI Workflow

Create `.github/workflows/test-<language>.yml` following existing wrapper test workflows.

---

## Testing Standards

### Test Coverage Requirements

1. **Rust canonical tool**: Unit tests + integration tests + conformance tests
2. **Wrappers**: Conformance tests (via wrapper invocation)
3. **Validation scripts**: Test scripts in `scripts/tests/`

### Conformance Tests

Conformance tests validate behavior against the RFC contract using vectors defined in `conformance/vectors.json`.

See [docs/testing/conformance-tests.md](../testing/conformance-tests.md) for details.

### Running Tests

```bash
# Run all Rust tests (unit + integration + conformance)
cd rust/
cargo test

# Run only conformance tests
cargo test --test conformance

# Run wrapper tests
cd wrappers/scripts/bash/
./run-tests.sh
```

---

## Documentation Requirements

### Docstring Contracts

**EVERY script file in the repository MUST conform to its language-specific docstring contract.**

Contracts are defined in `docs/contributing/docstring-contracts/` and enforced by CI via `scripts/validate-docstrings.py`.

#### Required Sections

All scripts must include:

1. **Purpose** - What the script does
2. **Usage** - How to invoke it
3. **Arguments/Parameters** - What inputs it accepts
4. **Exit Codes** - What each exit code means (see [exit-codes-contract.md](../docstrings/exit-codes-contract.md))
5. **Examples** - Concrete usage examples
6. **Environment Variables** (if applicable)
7. **Error Conditions** - What can go wrong

#### Language-Specific Templates

See templates in:
- [docs/contributing/docstring-contracts/bash.md](../docstrings/bash.md) - Bash/Shell scripts
- [docs/contributing/docstring-contracts/python.md](../docstrings/python.md) - Python scripts
- [docs/contributing/docstring-contracts/perl.md](../docstrings/perl.md) - Perl scripts
- [docs/contributing/docstring-contracts/powershell.md](../docstrings/powershell.md) - PowerShell scripts
- [docs/contributing/docstring-contracts/rust.md](../docstrings/rust.md) - Rust code
- [docs/contributing/docstring-contracts/yaml.md](../docstrings/yaml.md) - YAML workflows

### Documentation Standards

1. **Use kebab-case** for all doc filenames
2. **Add to docs index** - Update `docs/README.md` when adding new docs
3. **Cross-reference appropriately** - Link to related docs
4. **Keep docs in sync** - Update docs when changing behavior

---

## Pull Request Process

### Before Submitting

1. **Run all checks locally**:
   ```bash
   # Naming, docstrings, structure
   python3 scripts/validate-docstrings.py
   ./scripts/validate-structure.sh
   ./scripts/verify-repo-references.sh
   
   # Tests
   cd rust/ && cargo test
   cd ../wrappers/scripts/bash/ && ./run-tests.sh
   ```

2. **Use `git mv` for renames** - Preserve history
3. **Update references** - Search for old paths when moving files
4. **Update documentation** - Keep docs in sync with changes

### PR Guidelines

1. **Small, focused PRs** - One concern per PR
2. **Clear descriptions** - Explain what and why
3. **CI must pass** - All checks green before merge
4. **Tests included** - Add tests for new functionality
5. **Docs updated** - Document new features/changes

### Commit Messages

Follow conventional commit format:

```
<type>: <description>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Examples:
- `feat: Add safe-check subcommand`
- `fix: Correct exit code forwarding in Bash wrapper`
- `docs: Update contributing guide with naming conventions`
- `test: Add conformance tests for safe-archive`

---

## Additional Resources

- [RFC v0.1.0](../../rfc-shared-agent-scaffolding-v0.1.0.md) - Contract specification
- [Canonical Structure](../architecture/canonical-structure.md) - Directory layout
- [Conformance Contract](../conformance-contract.md) - Testing contract
- [Wrapper Discovery](../wrapper-discovery.md) - How wrappers find the Rust binary
- [Allowed Drift](./allowed-drift.md) - Behavioral difference policy

---

## Getting Help

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `docs/` for detailed guides

---

**Last Updated:** 2025-12-28
