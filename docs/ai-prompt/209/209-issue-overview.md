# Repo-Lint Toolchain Bootstrapper (Session-Start Compliance Gate)
Last Updated: 2025-12-31
Related: Issue #209

## Progress Tracker
- [x] Read issue overview (209-issue-overview.md)
- [x] Create AI journal (209-next-steps.md)
- [x] Create issue summary (209-summary.md)
- [x] Create detailed implementation plan (209-implementation-plan.md)
- [x] Phase 1: Core Bootstrapper Script Creation
  - [x] Item 1.1: Repository root discovery
  - [x] Item 1.2: Python virtual environment setup
  - [x] Item 1.3: repo-lint package installation
  - [x] Item 1.4: repo-lint verification
- [x] Phase 2: Tool Installation and Verification
  - [x] Item 2.1: Core utility installation (rgrep)
  - [x] Item 2.2: Python toolchain installation
  - [x] Item 2.3: Shell toolchain installation
  - [x] Item 2.4: PowerShell toolchain installation
  - [x] Item 2.5: Perl toolchain installation
- [x] Phase 3: Verification Gate and Error Handling
  - [x] Item 3.1: Final verification gate
  - [x] Item 3.2: Error handling and messages
  - [x] Item 3.3: Idempotency and state management
- [x] Phase 4: Documentation
  - [x] Item 4.1: Inline script documentation
  - [x] Item 4.2: External documentation (`docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md`)
  - [x] Item 4.3: Copilot session-start integration notes
- [x] Phase 5: Testing and Validation
  - [x] Item 5.1: Manual testing (all toolchains verified)
  - [x] Item 5.2: Comprehensive automated test suite (20 tests, all passing)
- [x] Phase 6: CI Integration and Rollout
  - [x] Item 6.1: CI workflow created (`.github/workflows/test-bootstrapper.yml`)
  - [x] Item 6.2: All linting/formatting/docstring checks passing

## Current Status: **COMPLETE** ✅

All phases completed successfully. The repo-lint toolchain bootstrapper is fully functional with:
- Complete Bash script (42,290 bytes) with all toolchains
- Comprehensive test suite (20 tests, 100% passing)
- CI integration via GitHub Actions
- Full documentation
- All compliance checks passing

## Session Notes (newest first)
### 2025-12-31 20:02 - Phase 1 implementation complete
**Summary:**
- Implemented complete Phase 1: Core Bootstrapper Script Creation
- Created `scripts/bootstrap-repo-lint-toolchain.sh` (497 lines, 13,781 bytes)
- All 4 Phase 1 items completed and verified
- Script passes all compliance checks (shellcheck, shfmt, docstring validation)
- Tested: fresh install, idempotency, subdirectory execution, repo-lint functionality

**Deliverables:**
- Bash script with comprehensive docstrings (top-level + 9 functions)
- Naming compliance: kebab-case filename, snake_case functions
- Exit codes: 0, 1, 10, 11, 12, 13, 14 (all documented)
- Idempotent: safe to run multiple times
- Works from any subdirectory in repo

**Phase 1 Features Implemented:**
- ✅ Repository root discovery (walks up looking for .git, pyproject.toml, README.md)
- ✅ Virtual environment creation (.venv/) with validation
- ✅ Virtual environment activation with verification
- ✅ pip/setuptools/wheel upgrade
- ✅ repo-lint package installation in editable mode
- ✅ repo-lint functionality verification (--help test)

**Compliance Evidence:**
- shellcheck: 0 warnings
- shfmt: formatted correctly
- validate_docstrings: all sections present
- repo-lint check --only bash: exit 0

**Next Phase:**
- Phase 2: Tool installation (rgrep, Python/Shell/PowerShell/Perl toolchains)

---

### 2025-12-31 19:47 - Planning phase complete
**Summary:**
- Created all required planning documentation per agent instructions
- Analyzed existing Rust bootstrap implementation as reference
- Developed comprehensive 6-phase implementation plan with detailed sub-items
- Identified that Bash script is specifically requested (Rust impl already exists)
- Ready for implementation pending human approval

**Deliverables Created:**
- `docs/ai-prompt/209/209-next-steps.md` - AI journal for per-commit tracking
- `docs/ai-prompt/209/209-summary.md` - High-level issue summary and requirements
- `docs/ai-prompt/209/209-implementation-plan.md` - Detailed phased plan with checkboxes and TODOs

**Key Decision Points:**
- Plan assumes Bash and Rust implementations will coexist
- Focus on Debian/Ubuntu (apt) as primary platform
- Defer macOS/Windows support unless requested
- Prioritize manual testing over automated tests initially

**Next Steps:**
- Await human approval/feedback on implementation plan
- If approved, begin Phase 1 (core bootstrapper script creation)

---

> **CALL THE TOOL** `copilot_repo_compliance_bootstraper.*`
> USE THE CORRECT NAMING FOR WHATEVER LANGUAGE YOU BUILD THIS BOOTSTRAPPER IN:
> i.e.: Bash = `kebab-case`, Python = `snake_case`, PowerShell = `PascalCase`, etc.

## Problem / Why This Exists
Copilot repeatedly fails the repository’s mandatory “repo-lint before commit” rules due to environment/tooling drift:
- `repo-lint` is not installed / not on PATH
- required linters aren’t installed (black/ruff/pylint/etc.)
- CI failures become non-actionable because the agent can’t reproduce checks locally
- the agent then stalls asking for “exact install commands” instead of fixing issues

This repository already treats tooling compliance as mandatory. The missing piece is a **single, deterministic bootstrapper** that Copilot can run at the **start of every session** to install/verify everything it needs.

## Goal
Add a **Repo-Lint Toolchain Bootstrapper** that Copilot can run at session start to:
1) Ensure required tools are installed/available
2) Install and activate the repo’s `repo-lint` Python package correctly
3) Verify `repo-lint` is on PATH and runnable
4) Verify repo-lint checks can run locally in a predictable way

This is designed specifically to prevent future “missing tools are a blocker” compliance failures.

---

## Requirements

### R1 — Bootstrap script
Create a new script (preferred location):
- `scripts/bootstrap-repo-lint-toolchain.sh`

It must be safe to run repeatedly (idempotent):
- If tools exist, it should verify versions/availability and continue
- If missing, it should install them when possible (or clearly instruct and fail fast)

### R2 — Tools to install/verify
The bootstrapper must install or verify availability of:

**Core utilities**
- `rgrep` (preferred grep tool; if unavailable in environment, fallback to `grep` but warn loudly)

**Python toolchain**
- `black`
- `pylint`
- `pytest`
- `ruff`
- `yamllint`

**Shell toolchain**
- `shellcheck`
- `shfmt`

**PowerShell toolchain**
- `pwsh`
- `PSScriptAnalyzer`

**Perl toolchain**
- `Perl::Critic`
- `PPI`

### R3 — repo-lint / repo-lint activation (MANDATORY)
After tool verification/installation, the bootstrapper must:
- Install `repo-lint` (repo-lint package) into a Python venv owned by the repo (e.g. `.venv/`)
- Activate that venv for the current shell session
- Ensure `repo-lint` (and/or `repo-lint`, depending on canonical naming) is on PATH and runnable:
  - `repo-lint --help` must succeed

If the repo provides a `repo-lint install` command to install dependencies, the bootstrapper must run it.

### R4 — Verification gate (MANDATORY)
At the end, the bootstrapper must run a minimal verification gate and fail non-zero if it doesn’t pass:
- `repo-lint check --ci`  (or a narrower run if needed for speed, but default should be full gate)

If the verification fails due to missing tools, that is treated as bootstrap failure and must clearly list missing tools.

### R5 — Deterministic behavior / no ambiguity
- Must print clear “what I’m doing / what failed / how to fix” messages
- Must have stable exit codes (document them in the script header)
- Must not silently skip required components
- Must be CI-friendly (no interactive prompts unless explicitly required; if unavoidable, detect and error with instructions)

### R6 — Documentation updates
Add a short doc explaining:
- how to run the bootstrapper locally
- that Copilot must run it at session start
- where the venv lives and how PATH is managed

Preferred doc location:
- `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md` (or repository’s existing docs structure)

### R7 — Tests (as applicable)
If feasible, add lightweight tests to validate:
- repo root discovery
- venv creation behavior
- tool detection logic

---

## Implementation Notes / Constraints
- The bootstrapper should prefer common package managers:
  - Linux CI: `apt-get` if available
  - macOS: `brew` if available (optional support is OK)
- If installation is impossible in a given environment (no sudo, no package manager), the script must:
  - Print exact missing tools
  - Provide explicit manual install suggestions
  - Exit non-zero

No “out of scope” behavior. The bootstrapper exists specifically to enforce compliance.

---

## Acceptance Criteria
- [ ] Running `scripts/bootstrap-repo-lint-toolchain.sh` from any subdirectory inside the repo:
  - locates repo root
  - creates/uses `.venv/`
  - installs `repo-lint` package
  - verifies `repo-lint --help` works
  - installs/verifies required tools listed above
  - runs `repo-lint check --ci` successfully (exit 0) on a clean repo
- [ ] Script is idempotent and can be run multiple times without breaking state
- [ ] Clear docs exist and are linked from a relevant README/CONTRIBUTING location
- [ ] Any new dependencies required by the bootstrapper are reflected in CI workflows that depend on them

---

## Deliverables
- [ ] `scripts/bootstrap-repo-lint-toolchain.sh`
- [ ] Documentation file under `docs/` describing usage + expectations
- [ ] (Optional) Basic tests for helper logic if non-trivial

## Priority
P0 / Blocker — This is required to stop recurring compliance failures and CI churn.
