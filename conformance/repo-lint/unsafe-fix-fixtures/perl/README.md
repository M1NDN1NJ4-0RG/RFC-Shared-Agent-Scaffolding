# Perl Unsafe Fix Fixtures

## Purpose

This directory contains **intentionally non-conforming** Perl scripts used for testing unsafe fix mode in `repo_lint`.

## Important Notes

- **These files violate repository docstring contracts intentionally**
- **Do NOT manually fix these files** - they are test fixtures
- **These files are excluded from CI lint/docstring checks**
- These files are used ONLY for testing unsafe mode transformations

## Usage

These fixtures are used by:
- Unit tests for unsafe fix mode (`tools/repo_lint/tests/test_unsafe_fixes.py`)
- Manual testing of unsafe fixers (ONLY with explicit human authorization per PR)

## Current Status

**TODO:** Unsafe fixers for Perl are not yet implemented.

When Perl unsafe fixers are added, this directory will contain fixtures that demonstrate:
- Non-conforming POD documentation formats that can be auto-fixed unsafely
- Edge cases that unsafe fixers must handle correctly

## Authorization

Per `docs/contributing/ai-constraints.md`, AI agents are PROHIBITED from running unsafe fixes on these files without explicit human permission in a specific PR/issue thread.
