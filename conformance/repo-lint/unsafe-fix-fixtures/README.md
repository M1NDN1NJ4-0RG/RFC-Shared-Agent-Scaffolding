# Unsafe Fix Test Fixtures

This directory contains test fixtures for testing `repo_lint`'s unsafe fix mode.

## Purpose

These fixtures are **intentionally non-conformant** with repo standards. They are designed to test unsafe fixers that modify code behavior or semantics.

## Do NOT Fix Manually

These files should remain in their non-conformant state. They are test fixtures, not real code.

## Fixtures by Language

### Python

- `python/google_style_docstrings.py`: Google-style docstrings (violates Sphinx format requirement)
  - Tests: `unsafe_docstring_rewrite` fixer
  - Expected change: Convert `Args:` and `Returns:` to `:param:` and `:returns:`

### Bash

- (Placeholder for future unsafe Bash fixers)

### PowerShell

- (Placeholder for future unsafe PowerShell fixers)

### Perl

- (Placeholder for future unsafe Perl fixers)

### YAML

- (Placeholder for future unsafe YAML fixers)

### Rust

- (Placeholder for future unsafe Rust fixers)

## Testing Usage

These fixtures are used by tests in `tools/repo_lint/tests/test_unsafe_fixes.py`.

**AUTHORIZED USAGE (PR #148 ONLY):**
During PR #148, these fixtures may be processed by:

```bash
# Copy fixture to temporary workspace
cp conformance/repo-lint/unsafe-fix-fixtures/python/google_style_docstrings.py /tmp/test_unsafe.py

# Run unsafe fixer
python3 -m tools.repo_lint fix --unsafe --yes-i-know /tmp/test_unsafe.py

# Review generated patch and log in logs/unsafe-fixes/
```

Outside PR #148, unsafe mode is human-only and AI-prohibited.
