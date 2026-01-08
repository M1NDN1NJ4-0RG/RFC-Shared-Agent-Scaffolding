# Issue #209 - Repo-Lint Toolchain Bootstrapper - Summary

## Issue Overview

**Title:** [EPIC] Repo-Lint Toolchain Bootstrapper (Session-Start Compliance Gate)
**Priority:** P0 / Blocker
**Status:** Planning Phase

## Problem Statement

Copilot agents repeatedly fail the repository's mandatory "repo-lint before commit" rules due to environment/tooling
drift:

- `repo-lint` is not installed or not on PATH
- Required linters aren't installed (black/ruff/pylint/shellcheck/shfmt/etc.)
- CI failures become non-actionable because agents can't reproduce checks locally
- Agents stall asking for "exact install commands" instead of fixing issues

## Goal

Create a single, deterministic bootstrapper script that Copilot can run at the start of every session to:

1. Ensure required tools are installed/available
2. Install and activate the repo's `repo-lint` Python package correctly
3. Verify `repo-lint` is on PATH and runnable
4. Verify repo-lint checks can run locally in a predictable way

## Key Deliverables

1. **Bash Script**: `scripts/bootstrap-repo-lint-toolchain.sh`
   - Idempotent (safe to run multiple times)
   - Locates repo root from any subdirectory
   - Creates/uses `.venv/` for repo-lint installation
   - Installs/verifies all required tools
   - Runs final verification gate (`repo-lint check --ci`)

2. **Documentation**: `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md` (or similar)
   - How to run the bootstrapper locally
   - Session-start requirements for Copilot
   - Where venv lives and how PATH is managed

3. **Tests** (optional, as applicable):
   - Repo root discovery logic
   - Venv creation behavior
   - Tool detection logic

## Current State

- **Existing**: Rust-based bootstrap implementation exists (`rust/src/bootstrap.rs` [**REMOVED in Issue #265** - replaced by `rust/src/bootstrap_v2/`], `rust/src/bootstrap_main.rs` [**UPDATED in Issue #265** - now uses bootstrap_v2])
- **Existing**: Documentation at `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md` (for Bash script implementation)
- **Completed**: Bash script at `scripts/bootstrap-repo-lint-toolchain.sh`
- **Completed**: Documentation specific to Bash script approach
- **Completed**: Session-start integration guidance

## Required Tools Checklist

The bootstrapper must install or verify:

**Core utilities:**

- [ ] `rgrep` (preferred grep; fallback to `grep` with warning)

**Python toolchain:**

- [ ] `black`
- [ ] `pylint`
- [ ] `pytest`
- [ ] `ruff`
- [ ] `yamllint`

**Shell toolchain:**

- [ ] `shellcheck`
- [ ] `shfmt`

**PowerShell toolchain:**

- [ ] `pwsh`
- [ ] `PSScriptAnalyzer`

**Perl toolchain:**

- [ ] `Perl::Critic`
- [ ] `PPI`

**repo-lint:**

- [ ] Install `repo-lint` package into `.venv/`
- [ ] Activate venv for current shell session
- [ ] Verify `repo-lint --help` works
- [ ] Run `repo-lint install` to install additional dependencies
- [ ] Run `repo-lint check --ci` as verification gate

## Exit Code Requirements

The bootstrapper must use stable, documented exit codes:

- `0`: Success - all operations completed
- `1`: Generic failure
- `2`: Missing tools (CI mode - tools not installable)
- Other codes TBD based on specific failure modes

## Acceptance Criteria

- [ ] Running `scripts/bootstrap-repo-lint-toolchain.sh` from any subdirectory:
  - [ ] Locates repo root
  - [ ] Creates/uses `.venv/`
  - [ ] Installs `repo-lint` package
  - [ ] Verifies `repo-lint --help` works
  - [ ] Installs/verifies all required tools
  - [ ] Runs `repo-lint check --ci` successfully (exit 0) on clean repo
- [ ] Script is idempotent
- [ ] Clear documentation exists
- [ ] New dependencies reflected in CI workflows

## Notes

- The Rust implementation already exists and is functional
- The requirement is for a **Bash script** as specified in the issue
- The Bash script should follow the same patterns as the Rust version
- Both implementations can coexist; Bash may be preferred for simpler shell-based workflows
- Follow repository's "Rule of Three" for any code duplication
