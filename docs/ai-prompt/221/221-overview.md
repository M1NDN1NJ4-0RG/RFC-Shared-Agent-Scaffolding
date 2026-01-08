# Issue 221 Overview

Last Updated: 2026-01-01
Related: Issue #221, PR #222

## Original Issue

## General Guidelines

- This PR is strictly limited to setting up the canonical fixtures/test vectors and their supporting infrastructure. Do not change any unrelated code.
- The existing rule "DO NOT COMMIT WITH VIOLATIONS" is temporarily suspended only for files under `tests/fixtures/**` in this PR. You may commit these intentionally bad files; no other files may contain violations.
- Use explicit imperative language in code comments and commit messages; no ambiguity is allowed.
- Each step below must be completed in sequence; do not skip steps.

### Phase&nbsp;1 – Create Fixture Directory Structure

1. Create a new directory `tests/fixtures` at the repository root.
2. For each supported language (python, bash, powershell, perl, yaml, rust):
   1. Create a subdirectory named after the language.
   2. Under that language directory, create tool‑specific violation files named `<tool>-violations.<ext>` for every linting tool used for that language. Each file must include many distinct violations that trigger multiple rules/codes for its tool.
   3. Under that language directory, create a single `all-docstring-violations.<ext>` file that intentionally violates every module-level docstring rule and every docstring contract category (functions, classes, methods, etc.) for that language.

### Phase&nbsp;2 – Exclude Fixtures From Normal Runs and Add Vector Mode

1. Modify repo‑lint's file selection logic so that paths under `tests/fixtures/**` are excluded by default for both check and fix operations.
2. Add a new command‑line flag or configuration option to enable vector mode (for example, `--include-fixtures`). When this flag is supplied, repo‑lint must include the fixture files in its scans.

### Phase&nbsp;3 – Add Vector Integration Tests

1. Write integration tests that copy the fixture files into a temporary working directory.
2. In vector mode, run repo‑lint against the temporary copies and assert that all violations are detected and the `File` and `Line` fields are populated correctly for every violation.
3. In normal mode, run repo‑lint against the temporary copies and assert that no violations are reported because fixtures are ignored.
4. Verify that fix mode modifies only the temporary copies and never the fixtures themselves.

### Phase&nbsp;4 – Add Module‑Specific Unit Tests

1. For every runner module (e.g., `python_runner.py`, `bash_runner.py`, `powershell_runner.py`, etc.), create a matching unit test file under `tests/runners/` using the naming pattern `test_<module>.py`.
2. In each unit test, mock out external tool calls and assert that violation objects have the correct `file` (basename only), `line` (exact integer or "-" when unavailable), and `message` fields.

### Phase&nbsp;5 – Verification and CI Integration

1. Confirm that a default `repo-lint check` run on the repository (excluding fixtures) reports zero violations.
2. Confirm that running repo‑lint in vector mode reports the expected violations from the fixtures.
3. Add a CI job that runs the vector integration tests.
4. Ensure that existing CI jobs remain green after these changes.

### Acceptance Criteria

- A `tests/fixtures/**` hierarchy exists with tool‑specific violation files and docstring violation files for each language.
- repo‑lint ignores fixture files by default and only scans them in vector mode.
- Integration tests demonstrate correct detection of violations and correct exclusion behavior.
- Unit tests cover each runner module.
- The override on committing violations applies only to fixture files for this PR.

This plan is non‑negotiable; follow each directive exactly.

## Progress Tracker

- [x] Phase 1: Create Fixture Directory Structure
  - [x] Create `tests/fixtures` directory
  - [x] Create Python fixtures (black, ruff, pylint, docstrings)
  - [x] Create Bash fixtures (shellcheck, shfmt, docstrings)
  - [x] Create PowerShell fixtures (PSScriptAnalyzer, docstrings)
  - [x] Create Perl fixtures (perlcritic, docstrings)
  - [x] Create YAML fixtures (yamllint, actionlint, docstrings)
  - [x] Create Rust fixtures (rustfmt, clippy, docstrings)
- [x] Phase 2: Exclude Fixtures From Normal Runs and Add Vector Mode (PARTIAL)
  - [x] Modify file selection logic to exclude `tests/fixtures/**`
  - [x] Add `--include-fixtures` flag
  - [x] Fix exclusion duplication - single source of truth
  - [ ] Complete docstring validator integration
- [ ] Phase 3: Add Vector Integration Tests
  - [ ] Write integration tests for vector mode
  - [ ] Test normal mode exclusion
  - [ ] Test fix mode behavior
- [ ] Phase 4: Add Module-Specific Unit Tests
  - [ ] Create unit tests for all runner modules
- [ ] Phase 5: Verification and CI Integration
  - [ ] Verify repo-lint check passes without fixtures
  - [ ] Verify vector mode detects violations
  - [ ] Add CI job for vector tests
  - [ ] Ensure existing CI passes

## Session Notes (newest first)

### 2026-01-01 07:30 - Session Start

- Completed session start requirements
- Bootstrapper completed successfully (exit code 0)
- repo-lint health check passed (exit code 0)
- Created issue journals for issue #221
- Ready to begin work
