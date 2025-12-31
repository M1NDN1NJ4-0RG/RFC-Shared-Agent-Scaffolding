# Issue 327 Overview
Last Updated: 2025-12-31
Related: Issue #327, PRs TBD

## Original Issue
# Issue Overview: Repo Lint and Docstring Enforcement M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding#327 Failures  
**Date:** December 31, 2025 (America/Chicago)  
**Purpose:** Durable instruction set for Copilot; do not truncate.

## Current CI Failures  
- **Workflow Run:** Repo Lint and Docstring Enforcement M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding#327  
  - **Job:** Repo Lint: Python  
    - **Failing Step:** Run repo_lint for Python  
    - **Root Error:** Ruff linter found 11 violations; first violation at `tools/repo_lint/tests/test_unsafe_fixes.py:28:1` (W293 blank line contains whitespace).  
    - **Exit Code:** 1 (VIOLATIONS)  
    - **Files Mentioned:** `tools/repo_lint/tests/test_unsafe_fixes.py` and other Python files flagged by Ruff.  
    - **Evidence:** See ruff failures table in the job logs.

  - **Job:** Repo Lint: Bash  
    - **Failing Step:** Run repo_lint for Bash  
    - **Root Error:** `validate_docstrings` plugin found 18 violations in shell scripts. ShellCheck and shfmt passed; docstring validation failed.  
    - **Exit Code:** 1 (VIOLATIONS)  
    - **Files Mentioned:** Various shell scripts flagged by repo_lint; specific files listed in the Bash lint results.  
    - **Evidence:** Bash linting summary showing 18 docstring violations in validate_docstrings.

  - **Job:** Windows: Rich UI Validation  
    - **Failing Step:** Test Rich‑Click Help Output  
    - **Root Error:** The help output for the `fix` subcommand did not match the expected snapshot; log shows `Fix help failed` and the process exited with code 1.  
    - **Exit Code:** 1  
    - **Files Mentioned:** None; error relates to CLI help formatting.  
    - **Evidence:** Windows job logs showing "Fix help failed" and exit code 1.

## Root Causes (Grouped)  
- **Python Lint Failures (Ruff):** Ruff detected style violations across Python sources. The first violation is a blank line containing whitespace in `tools/repo_lint/tests/test_unsafe_fixes.py:28:1` (W293). The repository must be cleaned of all Ruff violations.  
- **Bash Docstring Validation Failures:** Repo-lint's `validate_docstrings` runner failed with 18 violations. These relate to missing or malformed docstrings in bash scripts. ShellCheck and shfmt passed, so the underlying shell syntax/formatting is correct; the failure is purely due to docstring conventions enforced by repo_lint.  
- **Rich UI Validation Failure:** On Windows, the test verifying the CLI's rich-click help text for the `fix` subcommand failed. The expected help output and the actual output differ. This indicates that the CLI help needs to be updated to match the expected snapshot or the snapshot updated to reflect intentional changes. It is likely deterministic rather than environment-specific.

## Non‑Negotiable Human Orders  
- **Fix ALL linting errors across the repository (even if they pre‑exist and are not introduced by the current change set).**  
- **CI output must be ASCII‑safe by default unless UTF‑8 is explicitly confirmed.**  
- **Exclude `.venv/` and any other generated environment directories from naming conformance checks.**  
- **No deferrals, no "changed files only", and no "out of scope" claims. All issues uncovered must be addressed.**

## Progress Tracker
- [x] Set up environment and install required tools (repo-cli, linters, formatters)
- [x] Run repo-cli check --ci locally to reproduce all failures
- [x] Fix Ruff violations in Python files (1 violation: W293 in test_unsafe_fixes.py)
- [x] Verify Bash docstring violations (0 violations found - already fixed)
- [x] Fix Rich UI help output test failure (replaced emoji with ASCII text)
- [x] Run repo-cli check --ci again to verify all fixes
- [x] Run code review (no comments)
- [x] Run CodeQL checker (0 alerts)
- [x] Commit and push fixes
- [x] Verify all checks passing locally

## Session Notes (newest first)
### 2025-12-31 Session Complete - All Fixes Applied
- Fixed Ruff W293 violation in tools/repo_lint/tests/test_unsafe_fixes.py
- Fixed Windows encoding issue by replacing warning emoji with ASCII text
- All linting checks passing: Python (4/4), Bash (3/3)
- All help commands working with ASCII-safe output
- Code review passed with no comments
- CodeQL scan passed with 0 alerts
- Ready for CI validation

### 2025-12-31 Session Start
- Initialized issue journal directory
- Reviewing repository structure and understanding the problem
