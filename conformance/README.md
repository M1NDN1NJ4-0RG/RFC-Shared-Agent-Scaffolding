# Conformance Test Vectors

**Purpose:** Single source of truth for expected behavior across all language implementations.

**Status:** v1.0 (M2-P1-I1)

---

## Overview

This directory contains canonical test vectors that define the expected behavior of all scripts in the RFC Shared Agent Scaffolding system. All language bundles (Bash, Python 3, Perl, PowerShell) **MUST** pass these conformance tests to ensure behavioral parity.

---

## Vector Schema

### `vectors.json` Structure

```json
{
  "version": "1.0",
  "m0_contract_version": "v0.1.0",
  "vectors": {
    "safe_run": [...],
    "safe_archive": [...],
    "preflight_automerge_ruleset": [...]
  }
}
```

### Vector Fields

Each test vector contains:

- **`id`** (string, required): Unique stable identifier (e.g., `safe-run-001`)
- **`name`** (string, required): Human-readable test name
- **`m0_spec`** (string[], optional): M0 contract items this vector validates (e.g., `["M0-P1-I1", "M0-P1-I2"]`)
- **`command`** (object, required for safe_run): Command execution details
  - **`args`** (string[]): Command arguments
  - **`stdin`** (string, optional): Standard input data
  - **`env`** (object, optional): Environment variables
- **`expected`** (object, required): Expected outcomes
  - **`exit_code`** (number): Expected exit code
  - **`stdout_contains`** (string[], optional): Required stdout substrings
  - **`stderr_contains`** (string[], optional): Required stderr substrings
  - **`log_file_pattern`** (string, optional): Regex for log filename (M0-P1-I2)
  - **`log_content_markers`** (string[], optional): Required log content markers (M0-P1-I1)
  - **`artifacts_created`** (boolean): Whether artifacts should be created
  - **`file_exists`** (string[], optional): Files that must exist after execution
  - **`file_not_exists`** (string[], optional): Files that must not exist

---

## M0 Contract Coverage

### M0-P1-I1: safe-run Logging Semantics
- Split stdout/stderr with `=== STDOUT ===` and `=== STDERR ===` markers
- **Vectors:** `safe-run-002`, `safe-run-005`

### M0-P1-I2: Failure Log File Naming
- Format: `{ISO8601}-pid{PID}-{STATUS}.log`
- **Vectors:** `safe-run-002`, `safe-run-003`, `safe-run-005`

### M0-P1-I3: safe-archive No-Clobber Semantics
- Default: auto-suffix on collision
- Opt-in strict: fail on collision
- **Vectors:** `safe-archive-003`, `safe-archive-004`

### M0-P2-I1: Auth Method & Header Semantics
- `Authorization: Bearer <token>` header format
- Auth precedence: CLI > env > config > gh auth
- **Vectors:** `preflight-001`, `preflight-002`

### M0-P2-I2: Exit Code Taxonomy
- Stable exit code ranges for error classes
- **Vectors:** All vectors validate exit codes

---

## Usage

### For Test Implementers

1. Load `vectors.json` in your test framework
2. For each vector in the relevant category (`safe_run`, `safe_archive`, etc.):
   - Set up the test environment (temp directory, env vars)
   - Execute the command with specified inputs
   - Assert all `expected` conditions
3. Report pass/fail per vector ID

### For CI/CD

Conformance tests **MUST** pass for all supported language bundles:
- Bash
- Python 3
- Perl
- PowerShell

A failing conformance test indicates implementation drift and blocks merge.

---

## Adding New Vectors

When adding a new vector:

1. Assign a unique, stable `id` in the format `{category}-{number}` (e.g., `safe-run-010`)
2. Link to relevant M0 spec items in `m0_spec` field
3. Provide clear `name` describing what is tested
4. Define complete `expected` outcomes
5. Test the vector against at least one reference implementation
6. Update this README with M0 coverage information

---

## Allowed Implementation Differences

Certain platform-specific differences are **permitted**:

- **Path separators:** `/` vs `\` (normalize in tests)
- **Line endings:** LF vs CRLF (normalize in tests)
- **Process IDs:** Different PID values (test pattern, not exact value)
- **Timestamps:** Different execution times (test format, not exact value)
- **Absolute paths:** Different base paths (normalize or use relative paths)

All **functional behavior** must be identical.

---

## Version History

- **v1.0** (2025-12-26): Initial conformance vectors for M2-P1-I1
  - safe_run: 5 vectors (success, failure, SIGINT, custom log dir, snippet)
  - preflight_automerge_ruleset: 4 vectors (success, auth fail, ruleset not found, missing context)
  - safe_archive: 4 vectors (success, compression, no-clobber default, no-clobber strict)

---

**Refs:** Epic #3, M2-P1-I1
