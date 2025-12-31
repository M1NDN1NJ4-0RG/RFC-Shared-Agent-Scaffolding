# Repo-Lint Toolchain Bootstrapper (Session-Start Compliance Gate)

## Problem / Why This Exists
Copilot repeatedly fails the repository’s mandatory “repo-lint before commit” rules due to environment/tooling drift:
- `repo-cli` (repo-lint) is not installed / not on PATH
- required linters aren’t installed (black/ruff/pylint/etc.)
- CI failures become non-actionable because the agent can’t reproduce checks locally
- the agent then stalls asking for “exact install commands” instead of fixing issues

This repository already treats tooling compliance as mandatory. The missing piece is a **single, deterministic bootstrapper** that Copilot can run at the **start of every session** to install/verify everything it needs.

## Goal
Add a **Repo-Lint Toolchain Bootstrapper** that Copilot can run at session start to:
1) Ensure required tools are installed/available
2) Install and activate the repo’s `repo-cli`/repo-lint Python package correctly
3) Verify `repo-cli` is on PATH and runnable
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

### R3 — repo-cli / repo-lint activation (MANDATORY)
After tool verification/installation, the bootstrapper must:
- Install `repo-cli` (repo-lint package) into a Python venv owned by the repo (e.g. `.venv/`)
- Activate that venv for the current shell session
- Ensure `repo-cli` (and/or `repo-lint`, depending on canonical naming) is on PATH and runnable:
  - `repo-cli --help` must succeed

If the repo provides a `repo-cli install` command to install dependencies, the bootstrapper must run it.

### R4 — Verification gate (MANDATORY)
At the end, the bootstrapper must run a minimal verification gate and fail non-zero if it doesn’t pass:
- `repo-cli check --ci`  (or a narrower run if needed for speed, but default should be full gate)

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
- `docs/tools/repo-cli/bootstrapper.md` (or repository’s existing docs structure)

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
  - installs `repo-cli`/repo-lint package
  - verifies `repo-cli --help` works
  - installs/verifies required tools listed above
  - runs `repo-cli check --ci` successfully (exit 0) on a clean repo
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
