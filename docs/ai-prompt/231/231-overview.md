MUST READ: `.github/copilot-instructions.md` FIRST!
<!-- DO NOT EDIT OR REMOVE THE LINE ABOVE -->
# Issue 231 Overview

Last Updated: 2026-01-06
Related: Issue 231, PR copilot/add-actionlint-to-bootstrapper

## Original Issue

# Title

Add `actionlint` to `bootstrap-repo-lint-toolchain.sh` (GitHub Actions workflow linting)

## Summary

We currently bootstrap Python tooling (black/ruff/pylint/yamllint/pytest) and optional toolchains
(shell/powershell/perl). We need to add **actionlint** to the bootstrapper so GitHub Actions workflow YAML is linted
consistently in CI and in Copilot agent sessions.

## Background / Why

- The repo bootstrapper is intended to be run at the start of every Copilot agent session and then verified via `repo-lint check --ci`.
- - GitHub Actions workflows are part of the repository surface area. Without actionlint in the toolchain, workflow YAML
  can drift into "looks fine" but fails at runtime.

## Goals

- Install `actionlint` automatically as part of the bootstrap flow (with sensible OS-specific behavior).
- - Ensure the install is **idempotent** (safe to run repeatedly). - Update documentation so humans and agents know
  actionlint is included and how to verify it.
- Ensure the verification gate (`repo-lint check --ci`) continues to be the final "everything works" check.

## Non-Goals

- - Do not redesign CI workflows here. - Do not add new repo-lint rules beyond wiring in actionlint availability (unless
  a minimal hook is already planned/exists).

---

## Phase 1 — Script changes (`scripts/bootstrap-repo-lint-toolchain.sh`)

- [ ] Add an `install_actionlint` helper that:
  - [ ] No-ops if `actionlint` is already available on PATH
  - [ ] Installs on **macOS** using Homebrew when available (`brew install actionlint`)
  - - [ ] Installs on **Linux** using a deterministic method:
    - Prefer `go install github.com/rhysd/actionlint/cmd/actionlint@<PINNED_VERSION>` when Go is available
    - If Go is **not** available, install Go via the platform package manager (Debian/Ubuntu: `apt-get install -y golang-go`) and then run the same `go install ...`
  - [ ] Ensures the installed binary is on PATH for the remainder of the bootstrap run (e.g., `export PATH="$HOME/go/bin:$PATH"` after install)
  - [ ] Emits `actionlint -version` (or equivalent) in verbose mode for debugging
- - [ ] Decide where to call it: - [ ] Recommended: include it in **Required Toolchains (Always Installed)** so it's
  present for all agents by default
  - [ ] Alternative: include it under `--shell` (but then CI/agents might miss it unless `--shell` is always used)
- [ ] Update `show_usage` output to mention actionlint if it's required, or add a new flag if you decide to gate it behind an option.
- - [ ] Ensure failure behavior is consistent with existing exit codes: - [ ] If actionlint is required and cannot be
  installed, fail with a clear message and a stable exit code (either reuse "Shell toolchain installation failed"
  semantics or introduce a new specific exit code if that's consistent with the doc contract).

## Phase 2 — Documentation updates (`bootstrapper-toolchain-user-manual.md`)

- - [ ] Update "What Gets Installed":
  - [ ] Add `actionlint` to the appropriate section (required vs optional) and describe it as "GitHub Actions workflow linter".
- - [ ] Update "Verifying Setup" section to include:
  - [ ] `actionlint -version`
- - [ ] If a new flag is introduced, update "Command-Line Options" and all examples accordingly.

## Phase 3 — Verification / Tests

- - [ ] Run the bootstrapper end-to-end on at least one Linux environment and one macOS environment (where feasible):
  - [ ] `./scripts/bootstrap-repo-lint-toolchain.sh`
  - [ ] `source .venv/bin/activate`
  - [ ] `actionlint -version`
  - [ ] `repo-lint check --ci`
- - [ ] If this repo has fixture-based tests for toolchain parsing/availability: - [ ] Add or update fixtures to cover
  actionlint presence and failure modes.

---

## Acceptance Criteria

- [ ] `./scripts/bootstrap-repo-lint-toolchain.sh` installs (or confirms) `actionlint` and the command is available on PATH by the end of the run.
- [ ] `bootstrapper-toolchain-user-manual.md` accurately documents actionlint as installed and provides a verification command.
- - [ ] The bootstrapper remains idempotent.
- [ ] `repo-lint check --ci` passes after bootstrap in a clean environment.

## Notes / Implementation Guidance

- Prefer **version pinning** for reproducibility (either a pinned `@vX.Y.Z` for `go install`, or a pinned Homebrew formula version strategy if that's already a repo pattern).
- - Keep output consistent with current verbose/quiet conventions and existing tool install patterns.

## Progress Tracker

- - [x] Phase 1: Script changes - [x] Added install_actionlint function - [x] Integrated as required toolchain (Phase
  2.3) - [x] Updated show_usage - [x] Added exit code 20 for failures - [x] Added has_sudo helper (Rule of Three) - [x]
  Phase 2: Documentation updates - [x] Updated bootstrapper-toolchain-user-manual.md with actionlint - [x] Added
  verification command - [x] Documented exit code 20 - [x] Removed old Rust binary docs - [x] Phase 3: Verification and
  Tests - [x] Added comprehensive test suite (5 tests) - [x] End-to-end testing completed - [x] All tests passing
  (25/25) - [x] Code Review Feedback - [x] Fixed Go version requirement (1.18+ not 1.24+) - [x] Fixed failing test
  pattern - [x] All PR review comments addressed

## Session Notes (newest first)

### 2026-01-06 00:40 - New Session: Fail-Fast Hardening Plan Implementation

- - Read session compliance requirements document
- Ran bootstrapper successfully: `./scripts/bootstrap-repo-lint-toolchain.sh --all` (exit 0)
- - Activated environment and verified repo-lint functional
- Health check passed: `repo-lint check --ci` (exit 0)
- Read fail-fast hardening plan from `docs/ai-prompt/231/231-fail-fast-hardening-plan.md`
- - Created comprehensive execution checklist covering all 6 phases - Current status: actionlint already added in
  previous work; now implementing full fail-fast hardening - **Work completed in this session:**
  - Phase 0: Renamed bootstrapper manual to `bootstrapper-toolchain-user-manual.md`, updated all references, added CONTRIBUTING.md link
  - - Phase 1: Added 3 fail-fast helper functions (run_or_die, try_run, safe_version) - Phase 2.1-2.2: Made venv
    activation fatal, wrapped pip upgrade with deterministic exit codes - Code review: Addressed all 3 feedback items
    (exit code docs, security warnings, rationale notes) - All changes verified: shellcheck, shfmt, repo-lint check --ci
    all pass (exit 0) - **Remaining work:** Phases 2.3-6 cover extensive refactoring (PowerShell, Perl, shell tools,
    ripgrep enforcement, verification hardening, tests, documentation, analysis, Rust migration plan)

### 2026-01-06 00:16 - Journal Creation

- - Created issue journals for Issue 231 - All implementation work already completed in previous sessions - 7 commits
  total in PR - All tests passing, all acceptance criteria met
