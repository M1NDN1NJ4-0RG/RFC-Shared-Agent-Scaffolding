# Issue Overview: Repo Lint and Docstring Enforcement #327 Failures

**Date:** December 31, 2025 (America/Chicago)
**Purpose:** Durable instruction set for Copilot; do not truncate.

## Current CI Failures

- - **Workflow Run:** Repo Lint and Docstring Enforcement #327 - **Job:** Repo Lint: Python - **Failing Step:** Run
  repo_lint for Python
    - **Root Error:** Ruff linter found 11 violations; first violation at `tools/repo_lint/tests/test_unsafe_fixes.py:28:1` (W293 blank line contains whitespace).
    - **Exit Code:** 1 (VIOLATIONS)
    - **Files Mentioned:** `tools/repo_lint/tests/test_unsafe_fixes.py` and other Python files flagged by Ruff.
    - **Evidence:** See ruff failures table in the job logs ([github.com](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20624035687/job/59231364646)).

  - - **Job:** Repo Lint: Bash - **Failing Step:** Run repo_lint for Bash
    - **Root Error:** `validate_docstrings` plugin found 18 violations in shell scripts. ShellCheck and shfmt passed; docstring validation failed.
- **Exit Code:** 1 (VIOLATIONS) - **Files Mentioned:** Various shell scripts flagged by repo_lint; specific files listed
in the Bash lint results.
    - **Evidence:** Bash linting summary showing 18 docstring violations in validate_docstrings ([github.com](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20624035687/job/59231364646)).

  - - **Job:** Windows: Rich UI Validation - **Failing Step:** Test Rich‑Click Help Output
    - **Root Error:** The help output for the `fix` subcommand did not match the expected snapshot; log shows `Fix help failed` and the process exited with code 1.
    - **Exit Code:** 1
    - **Files Mentioned:** None; error relates to CLI help formatting.
    - **Evidence:** Windows job logs showing “Fix help failed” and exit code 1 ([github.com](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20624035687/job/59231364646)).

## Root Causes (Grouped)

- **Python Lint Failures (Ruff):** Ruff detected style violations across Python sources. The first violation is a blank line containing whitespace in `tools/repo_lint/tests/test_unsafe_fixes.py:28:1` (W293). The repository must be cleaned of all Ruff violations.
- **Bash Docstring Validation Failures:** Repo-lint’s `validate_docstrings` runner failed with 18 violations. These relate to missing or malformed docstrings in bash scripts. ShellCheck and shfmt passed, so the underlying shell syntax/formatting is correct; the failure is purely due to docstring conventions enforced by repo_lint.
- **Rich UI Validation Failure:** On Windows, the test verifying the CLI’s rich-click help text for the `fix` subcommand failed. The expected help output and the actual output differ. This indicates that the CLI help needs to be updated to match the expected snapshot or the snapshot updated to reflect intentional changes. It is likely deterministic rather than environment-specific.

## Non‑Negotiable Human Orders

- - **Fix ALL linting errors across the repository (even if they pre‑exist and are not introduced by the current change
  set).** - **CI output must be ASCII‑safe by default unless UTF‑8 is explicitly confirmed.**
- **Exclude `.venv/` and any other generated environment directories from naming conformance checks.**
- - **No deferrals, no “changed files only”, and no “out of scope” claims. All issues uncovered must be addressed.**

## Step‑by‑Step Fix Plan for Copilot

1. 1. **Investigate Ruff Violations (Python):**
   - Run `repo-cli lint python` locally to reproduce the Ruff failures.
   - For each violation listed (e.g., W293 blank line contains whitespace in `tools/repo_lint/tests/test_unsafe_fixes.py`), open the affected file and fix the issue according to the Ruff rule. Example: remove trailing whitespace on blank lines.
   - Continue fixing all Ruff‑reported issues across the repository until `ruff` reports zero violations.
   - Verify locally by running `repo-cli lint python` and ensuring it exits with code 0.

2. 2. **Fix Bash Docstring Violations:**
   - Run `repo-cli lint bash` locally to produce the validate_docstrings report.
   - - For each violation, open the referenced shell script and add or correct the docstring at the top of the file
     (usually a comment block explaining the script purpose, arguments, and usage). Ensure the docstring follows the
     repository’s docstring guidelines.
   - Exclude generated environment directories such as `.venv/` from scanning by adjusting the lint configuration if necessary, but do not exclude valid project scripts.
   - After correcting all issues, re‑run `repo-cli lint bash` and ensure there are zero violations.

3. 3. **Resolve Rich‑Click Help Output Failure:**
   - Check the CLI implementation for the `fix` subcommand (likely under `src/cli.py` or similar). Run the command `python -m <package> fix --help` locally to view the current help text.
   - - Compare the output against the expected snapshot used in the Windows test. If the CLI output is outdated, update
     the code to produce the correct help text. If the snapshot is outdated but the output is correct, update the
     snapshot used by the test. - Ensure the help text contains only ASCII characters unless UTF‑8 output is
     deliberately required. - Run the Rich UI validation tests locally (on Windows if possible) or run the relevant test
     suite to ensure the help output matches expectations.

4. 4. **General Linting and Cleanup:** - Search the repository for other linting errors (Python, Bash, PowerShell, etc.)
   and fix them proactively, even if they were not flagged in this run.
   - Make sure that no linting tool scans into `.venv/` or other generated directories by updating lint configuration files (e.g., `.repo-lint.yml` or `pyproject.toml`) to exclude those paths.
   - - Ensure all outputs printed during CI are ASCII‑safe unless a command explicitly confirms UTF‑8. Where necessary,
     sanitize output or set environment variables to enforce ASCII.

5. 5. **Commit and Verify:** - Commit all fixes with descriptive messages.
   - Run `repo-cli check --ci` from the repository root. This should run all linting and formatting checks.
   - - Ensure that the command exits with code 0 and that there are no violations. - Push the changes and wait for CI to
     rerun. All jobs, including Repo Lint: Python, Repo Lint: Bash, and Windows: Rich UI Validation, must pass.

## Verification Checklist

- [ ] Run `repo-cli lint python` locally; confirm Ruff reports zero violations.
- [ ] Run `repo-cli lint bash` locally; confirm `validate_docstrings` reports zero violations.
- [ ] Test the CLI `fix` subcommand help output and ensure it matches the expected snapshot; update code or snapshot as needed.
- [ ] Run `repo-cli check --ci`; it must exit with code 0, indicating all lint and formatting checks pass.
- - [ ] After pushing fixes, confirm that all CI jobs on GitHub Actions are green (Repo Lint: Python, Repo Lint: Bash,
  Windows: Rich UI Validation, and all other jobs).
