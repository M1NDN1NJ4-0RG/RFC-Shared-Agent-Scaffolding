# repo_lint - Unified Multi-Language Linting Tool

**Status:** Canonical linting and docstring validation tool for this repository
**Version:** Phase 7 (Unsafe Fix Mode implemented)
**Last Updated:** 2025-12-30

## Overview

`repo_lint` is the single source of truth for linting, formatting, and docstring validation across all supported languages in this repository. It orchestrates language-specific linters and enforces repo-wide coding standards.

## Supported Languages

- **Python**: Black, Ruff, Pylint, docstring validation
- **Bash**: ShellCheck, shfmt, docstring validation
- **PowerShell**: PSScriptAnalyzer, docstring validation
- **Perl**: Perl::Critic, PPI, docstring validation
- **YAML**: yamllint
- **Rust**: (stub, future implementation)

## Quick Start

### Check (Read-Only)

Run all linters without modifying files:

```bash
python3 -m tools.repo_lint check
```

### Fix (Safe Auto-Fixes)

Apply safe automatic fixes (formatters + approved lint fixes):

```bash
python3 -m tools.repo_lint fix
```

### Install Tools

Install required linting tools locally:

```bash
python3 -m tools.repo_lint install
```

## Command Reference

### `check` - Run Linting Checks

Run all linters in read-only mode (no file modifications):

```bash
python3 -m tools.repo_lint check [OPTIONS]
```

**Options:**

- `--ci`, `--no-install`: CI mode - fail if tools are missing (exit code 2)
- `--verbose`, `-v`: Show verbose output including passed checks
- `--only <language>`: Run checks for only the specified language (python, bash, powershell, perl, yaml, rust)
- `--json`: Output results in JSON format for CI debugging

**Exit Codes:**

- `0`: All checks passed
- `1`: Linting violations found
- `2`: Required tools missing (CI mode)
- `3`: Internal error

**Examples:**

```bash
# Check all languages
python3 -m tools.repo_lint check

# Check only Python files
python3 -m tools.repo_lint check --only python

# CI mode (fail on missing tools)
python3 -m tools.repo_lint check --ci

# Verbose output
python3 -m tools.repo_lint check --verbose

# JSON output for CI
python3 -m tools.repo_lint check --json
```

### `fix` - Apply Automatic Fixes

Apply safe automatic fixes (formatters + approved lint auto-fixes):

```bash
python3 -m tools.repo_lint fix [OPTIONS]
```

**Safe Fixes Include:**

- Black (Python formatter)
- shfmt (Bash formatter)
- Ruff safe auto-fixes (Python linter)

**Options:**

- `--ci`, `--no-install`: CI mode - fail if tools are missing
- `--verbose`, `-v`: Show verbose output
- `--only <language>`: Run fixes for only the specified language
- `--json`: Output results in JSON format

**Exit Codes:**

- `0`: All fixes applied successfully, no violations remain
- `1`: Violations remain after fixes
- `2`: Required tools missing (CI mode)
- `3`: Internal error

**Examples:**

```bash
# Apply safe fixes to all files
python3 -m tools.repo_lint fix

# Fix only Python files
python3 -m tools.repo_lint fix --only python

# CI mode (fail on missing tools)
python3 -m tools.repo_lint fix --ci
```

### `fix --unsafe` - DANGER: Unsafe Fixes

> **DANGER:** `python3 -m tools.repo_lint fix --unsafe --yes-i-know` is intentionally dangerous. It may change behavior. It is forbidden in CI. Only run it locally when you accept risk, and ALWAYS review the generated patch/log before committing.

Apply **unsafe** fixes that can modify code behavior or semantics:

```bash
python3 -m tools.repo_lint fix --unsafe --yes-i-know [OPTIONS]
```

**⚠️ CRITICAL WARNINGS:**

1. **HUMAN-ONLY COMMAND**: AI agents are **PROHIBITED** from running this command without explicit human permission. See [AI Constraints](../../docs/contributing/ai-constraints.md).

2. **BEHAVIOR CHANGES**: Unsafe fixes can change code semantics, refactor structure, or modify documentation in ways that alter meaning.

3. **FORBIDDEN IN CI**: This mode is **hard-blocked** in CI environments. Exit code 2 if attempted.

4. **REQUIRES DUAL FLAGS**: `--unsafe` alone will fail. You MUST also provide `--yes-i-know` to confirm.

5. **REVIEW REQUIRED**: Always review the generated patch and log files in `logs/unsafe-fixes/` before committing.

**Unsafe Fixers:**

- `unsafe_docstring_rewrite`: Converts Google-style docstrings to Sphinx format (may alter documentation semantics)
- *(More fixers may be added in the future)*

**Guard Rails:**

- `--unsafe` without `--yes-i-know` → Exit code 2 with error message
- Any unsafe flag in CI environment → Exit code 2 with error message
- CI detection via `--ci` flag or `CI` environment variable

**Forensics:**
All unsafe fix operations generate mandatory forensic artifacts in `logs/unsafe-fixes/`:

- `unsafe-fix-TIMESTAMP.patch` - Unified diff of all changes
- `unsafe-fix-TIMESTAMP.log` - Detailed log of what changed, why, and when

**Examples:**

```bash
# WRONG: This will fail (missing --yes-i-know)
python3 -m tools.repo_lint fix --unsafe
# ERROR: UNSAFE MODE BLOCKED FOR SAFETY

# CORRECT: Run unsafe fixes locally (after reading warnings)
python3 -m tools.repo_lint fix --unsafe --yes-i-know

# Review forensics before committing
ls -la logs/unsafe-fixes/
cat logs/unsafe-fixes/unsafe-fix-*.log
git diff  # Check actual changes

# FORBIDDEN: This will fail (CI mode)
python3 -m tools.repo_lint fix --unsafe --yes-i-know --ci
# ERROR: UNSAFE MODE FORBIDDEN IN CI
```

**See Also:**

- [AI Constraints Documentation](../../docs/contributing/ai-constraints.md) - AI agent safety rules
- [Phase 7 Requirements](../../docs/ai-prompt/110/new-requirement-phase-7.md) - Unsafe mode specification

### `install` - Install/Bootstrap Tools

Install required linting tools locally:

```bash
python3 -m tools.repo_lint install [OPTIONS]
```

**Options:**

- `--verbose`, `-v`: Show verbose output
- `--cleanup`: Remove repo-local tool installations (safe, only removes `.venv-lint/`, `.tools/`, etc.)

**Behavior:**

- **Python tools**: Auto-installed in `.venv-lint/` virtual environment
- **Other tools**: Manual installation instructions printed

**Examples:**

```bash
# Install tools
python3 -m tools.repo_lint install

# Clean up repo-local installations
python3 -m tools.repo_lint install --cleanup
```

## CI Integration

`repo_lint` is the canonical gate for all CI linting. The umbrella workflow (`.github/workflows/repo-lint-and-docstring-enforcement.yml`) uses `repo_lint` exclusively.

### CI Usage

```yaml
- name: Run repo_lint
  run: python3 -m tools.repo_lint check --ci --only python
```

### CI Exit Codes

- `0`: Pass (merge allowed)
- `1`: Violations found (merge blocked)
- `2`: Missing tools (workflow misconfigured)
- `3`: Internal error (workflow issue)

## Configuration

### Auto-Fix Policy

Safe auto-fixes are controlled by `conformance/repo-lint/autofix-policy.json`:

```json
{
  "version": "1.0",
  "categories": {
    "safe-formatter": {
      "allowed": true,
      "tools": ["black", "shfmt"]
    },
    "safe-lint-autofix": {
      "allowed": true,
      "tools": ["ruff"]
    }
  }
}
```

### Python Tool Configuration

All Python tools are configured in `pyproject.toml`:

- Black: `[tool.black]`
- Ruff: `[tool.ruff]`
- Pylint: `[tool.pylint]`

### Version Pinning

Tool versions are pinned in `pyproject.toml` under `[project.optional-dependencies.lint]`:

```toml
[project.optional-dependencies]
lint = [
    "black==24.10.0",
    "ruff==0.8.4",
    "pylint==3.3.2",
    "yamllint==1.35.1",
]
```

## Development

### Running Tests

```bash
# Run all repo_lint tests
python3 -m pytest tools/repo_lint/tests/ -v

# Run specific test file
python3 -m pytest tools/repo_lint/tests/test_unsafe_fixes.py -v

# Run with coverage
python3 -m pytest tools/repo_lint/tests/ --cov=tools.repo_lint
```

### Adding a New Language

1. Create runner in `tools/repo_lint/runners/<language>_runner.py`
2. Implement `Runner` protocol (check/fix/install_check methods)
3. Add to `cli.py` runner list
4. Add test fixtures in `conformance/repo-lint/`
5. Update this README

### Adding an Unsafe Fixer

**⚠️ REQUIRES CAREFUL REVIEW**

1. Create fixer class in `tools/repo_lint/unsafe_fixers.py`
2. Implement `can_fix()` and `fix()` methods
3. Document why the fixer is unsafe
4. Add to `UNSAFE_FIXERS` registry
5. Create test fixtures in `conformance/repo-lint/unsafe-fix-fixtures/`
6. Add tests in `tools/repo_lint/tests/test_unsafe_fixes.py`
7. Update this README and AI constraints doc

## Troubleshooting

### "Missing tools" error

```bash
# Install tools locally
python3 -m tools.repo_lint install

# Or in CI, ensure tools are installed in workflow
```

### "Auto-fix policy validation failed"

Check that `conformance/repo-lint/autofix-policy.json` exists and is valid JSON.

### Unsafe mode fails with "BLOCKED FOR SAFETY"

This is intentional. You must use BOTH `--unsafe` and `--yes-i-know` flags:

```bash
python3 -m tools.repo_lint fix --unsafe --yes-i-know
```

### Unsafe mode fails with "FORBIDDEN IN CI"

Unsafe mode is hard-blocked in CI. This is a safety feature. Run unsafe fixes locally only.

## See Also

- [Contributing Guide](../../CONTRIBUTING.md) - General contribution guidelines
- [AI Constraints](../../docs/contributing/ai-constraints.md) - AI agent safety rules
- [Docstring Contracts](../../docs/contributing/docstring-contracts/) - Per-language docstring requirements
- [Epic Status](../../docs/epic-repo-lint-status.md) - Implementation status and roadmap
