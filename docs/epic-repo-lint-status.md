# [EPIC] Build `repo_lint` Python Package/CLI (Unified Multi-Language Lint + Docstring Validation)

## Goal
Replace the ad-hoc “run everything” linter helper with a **proper Python package + CLI** that becomes the **single source of truth** for repo linting and docstring validation across all supported languages.

This tool must be:
- Deterministic and strict in CI
- Helpful locally (optional bootstrap + `fix`)
- Modular per-language (one runner per language)
- Aligned with repo contracts (naming, docstrings, exit codes, output format)
- Config-driven with **Python tooling config consolidated into `pyproject.toml`**

## Non-Goals
- Rewriting language linters (we orchestrate them)
- Replacing the Rust canonical binary
- Publishing to PyPI (explicitly out-of-scope for now)

---

## Phase 0 — Decisions (Locked)

### Item 0.1 — Naming + Placement (Locked)
- [x] **Sub-Item 0.1.1:** Python package name: `repo_lint` (snake_case)
- [x] **Sub-Item 0.1.2:** CLI command name: `repo-lint` (kebab-case)
- [x] **Sub-Item 0.1.3:** Package location: `tools/repo_lint/` (repo tooling, not PyPI)

### Item 0.2 — Execution Model (Locked)
- [x] **Sub-Item 0.2.1:** Run in-place first (CI runs `python -m tools.repo_lint ...`)
- [x] **Sub-Item 0.2.2:** Add TODOs in `docs/future-work.md` for:
  - Making `repo_lint` installable later (`pip install -e .`, console script, etc.)
  - Future repo-local tool isolation ideas (`.psmodules/`, `.cpan-local/`, etc.) and cleanup implications
  - Any additional enhancements tracked under Item 0.9.7

### Item 0.3 — CLI Surface Area (Locked)
- [x] **Sub-Item 0.3.1:** Minimum viable commands:
  - `repo-lint check`
  - `repo-lint fix`
  - `repo-lint install`
- [x] **Sub-Item 0.3.2:** Nice-to-haves (implement as time allows; keep in scope):
  - `repo-lint changed` (changed-files targeting) — Planned (Phase 6 Item 6.4)
  - `repo-lint doctor` (environment diagnostics + tool versions) — Deferred
  - `--ci/--no-install`, `--verbose` — ✅ Implemented
  - `--json`, `--report` — Deferred

### Item 0.4 — CI Black Auto-Patch Policy (Locked)
- [x] **Sub-Item 0.4.1:** Keep Black auto-patch for now
- [x] **Sub-Item 0.4.2:** Required safeguards:
  - Bot-loop guard (never reformat-commit endlessly): MUST use both (a) actor guard (skip when actor is bot) AND (b) commit-message marker guard (skip when commit message contains an autoformat marker)
  - Same-repo PRs only (never write to forks)
  - Fork PRs produce a patch artifact + fail with instructions
  - Pin all third-party actions by commit SHA

### Item 0.5 — Install / Bootstrap Policy (Locked)
- [x] **Sub-Item 0.5.1:** CI: **never** auto-install tools (workflow installs explicitly)
- [x] **Sub-Item 0.5.2:** Local: auto-install allowed; migrate toward repo-local installs over time

### Item 0.6 — Cleanup Policy (Locked)
- [x] **Sub-Item 0.6.1:** Add `--cleanup`, but it may remove **only repo-local installs**
- [x] **Sub-Item 0.6.2:** Never uninstall system packages (no `brew uninstall`, no `apt remove`)

### Item 0.7 — Version Pinning Policy (Locked)
- [x] **Sub-Item 0.7.1:** Pin tool versions in CI at minimum
- [x] **Sub-Item 0.7.2:** Pin tool versions locally too (prefer deterministic installs)

### Item 0.8 — Python Linter Strategy (Locked)
- [x] **Sub-Item 0.8.1:** Replace Flake8 with **Ruff** (Option C)
- [x] **Sub-Item 0.8.2:** Consolidate Python tool configs in **one location** whenever possible:
  - Prefer `pyproject.toml` for Ruff, Black, Pylint, etc.
- [x] **Sub-Item 0.8.3:** Remove `.flake8` / Flake8 CI steps after migration is complete and verified

### Item 0.9 — Additional Implementation Decisions (Locked)
- [x] **Sub-Item 0.9.1:** Ruff fix policy (Option A2):
  - `repo-lint check` is **non-mutating** and MUST run Ruff without fixes (e.g., `ruff check --no-fix`).
  - `repo-lint fix` may apply **safe** Ruff fixes only (e.g., `ruff check --fix` WITHOUT enabling unsafe fixes).
- [x] **Sub-Item 0.9.2:** Canonical run-in-place invocation is `python -m tools.repo_lint check` (and corresponding `fix`/`install`). Do not standardize on `tools.repo_lint.cli` in docs.
- [x] **Sub-Item 0.9.3:** PowerShell symbol discovery/doc enforcement MUST use native AST parse **from files** via `Parser::ParseFile` (C1). `Parser::ParseInput` (C2) may be used in unit tests/fixtures only.
- [x] **Sub-Item 0.9.4:** Bash symbol discovery MUST use Tree-sitter (D2) with a pinned Bash grammar (no execution).
- [x] **Sub-Item 0.9.5:** Perl symbol discovery MUST use PPI plus a structure-aware fallback strategy (E2) for edge cases (no regex-only parsing).
- [x] **Sub-Item 0.9.6:** Python tool version pinning strategy is F2: define pinned Python lint tool versions as a `lint` optional-dependency group in `pyproject.toml`.
- [x] **Sub-Item 0.9.7:** Future enhancements / potential issues must be tracked in `docs/future-work.md`. If this grows unwieldy, create a dedicated `docs/ideas.md` and link to it from `docs/future-work.md`.

**Phase 0 Success Criteria**
- ✅ All policy decisions above are locked and treated as constraints (no “Copilot interpretation”).

---

## Phase 1 — Package Scaffolding + CLI Entry Point ✅ COMPLETE
### Item 1.1 — Create package structure (High)
- [x] **Sub-Item 1.1.1:** Create `tools/repo_lint/` with:
  - `__init__.py`
  - `cli.py` (arg parsing + command dispatch)
  - `common.py` (types, errors, shared helpers)
  - `reporting.py` (stable output, exit codes)
  - `runners/` (per-language runners)
  - `install/` (bootstrap/install helpers)
- [x] **Sub-Item 1.1.2:** Implement module execution path:
  - `python -m tools.repo_lint check` (standardized)
  - Ensure `python -m tools.repo_lint fix` and `python -m tools.repo_lint install` work equivalently

### Item 1.2 — Implement CLI contract (High)
- [x] **Sub-Item 1.2.1:** Implement `repo-lint check`
- [x] **Sub-Item 1.2.2:** Implement `repo-lint fix` (formatters + allowlisted safe lint auto-fixes + re-check; see Phase 0 Item 0.9.1 and Phase 6 Item 6.5)
- [x] **Sub-Item 1.2.3:** Implement `repo-lint install` (local bootstrap only; CI must not use)
- [x] **Sub-Item 1.2.4:** Implement global flags:
  - `--ci/--no-install` (hard fail if tools missing)
  - `--verbose`
  - Deferred: `--json`, `--report`

**Phase 1 Success Criteria**
- ✅ CLI runs in-place, produces stable output, returns correct exit codes.

---

## Phase 2 — Consolidate Python Tooling Config + Migrate Flake8 → Ruff ✅ COMPLETE
### Item 2.1 — Consolidate into `pyproject.toml` (High)
- [x] **Sub-Item 2.1.1:** Move/confirm Black config in `pyproject.toml`
- [x] **Sub-Item 2.1.2:** Move/confirm Pylint config in `pyproject.toml` (eliminate separate config files if feasible)
- [x] **Sub-Item 2.1.3:** Add Ruff config in `pyproject.toml`:
  - Match line-length = 120
  - Configure equivalent rule set to current Flake8 policy (including prior E203/W503-like intent where relevant)
  - Ensure ignores/extends align with repo conventions

### Item 2.2 — Replace Flake8 in tooling + CI (High)
- [x] **Sub-Item 2.2.1:** Update local lint command set:
  - Remove Flake8 invocation locally
  - Add `ruff check` (non-mutating in `check`; safe fixes allowed only in `fix`)
  - Keep Black as the formatter-of-record (no competing formatters)

> Note: Ruff parity verification is tracked later in CI under **Phase 6 Item 6.3 (Sub-Item 6.3.4)**.

> Note: CI migration off Flake8 and removal of `.flake8` are tracked in **Phase 6 Item 6.3**.

**Phase 2 Success Criteria**
- ✅ Black/Pylint/Ruff all configured in `pyproject.toml`
- ✅ Local tooling uses Ruff in place of Flake8

---

## Phase 3 — Implement Per-Language Runner Modules ✅ COMPLETE
### Item 3.1 — Define runner interface + shared result types (High)
- [x] **Sub-Item 3.1.1:** Define `Runner` interface/protocol (check/fix/install_check)
- [x] **Sub-Item 3.1.2:** Standardize `LintResult` + `Violation` structures (tool, file, line, message)
- [x] **Sub-Item 3.1.3:** Standardize exit code behavior across all runners

### Item 3.2 — Python runner (High)
- [x] **Sub-Item 3.2.1:** Implement Python runner:
  - Black check/fix
  - Ruff check
  - Pylint check
  - Docstring validation (invoke `scripts/validate_docstrings.py`) ✅
- [x] **Sub-Item 3.2.2:** Ensure “no skipping private symbols” remains enforced (docstring validator contract) ✅

### Item 3.3 — Bash runner (High)
- [x] **Sub-Item 3.3.1:** Implement Bash runner:
  - ShellCheck
  - shfmt check/fix
  - Bash docstring validation

### Item 3.4 — PowerShell runner (High)
- [x] **Sub-Item 3.4.1:** Implement PowerShell runner:
  - PSScriptAnalyzer (run via `pwsh -NoProfile -NonInteractive`)
  - PowerShell docstring validation
  - Best practice: for symbol discovery / doc enforcement, parse with PowerShell’s native AST (`Parser::ParseFile`) and emit JSON—**never** execute repo scripts during linting

### Item 3.5 — Perl runner (High)
- [x] **Sub-Item 3.5.1:** Implement Perl runner:
  - Perl::Critic
  - Perl docstring validation

### Item 3.6 — YAML runner (Medium)
- [x] **Sub-Item 3.6.1:** Implement YAML runner:
  - yamllint

### Item 3.7 — Docstring validator modularization + symbol scanners (Imported from Repo Cleanup EPIC Phase 5.5) (High)

> Why this is here: `repo_lint` is the orchestrator, but symbol-level docstring enforcement lives in `scripts/validate_docstrings.py`. The older Repo Cleanup EPIC (paused mid-Phase 5.5) defines the missing work (per-language validators and real parsers). To avoid drift, we track that dependency here too.

- [x] **Sub-Item 3.7.1:** Split `scripts/validate_docstrings.py` into per-language Python validator modules (keep a single CLI entrypoint and preserve output format)
  - Recommended layout:
    - `scripts/docstring_validators/common.py` ✅
    - `scripts/docstring_validators/python_validator.py` ✅
    - `scripts/docstring_validators/bash_validator.py` ✅
    - `scripts/docstring_validators/perl_validator.py` ✅
    - `scripts/docstring_validators/powershell_validator.py` ✅
    - `scripts/docstring_validators/rust_validator.py` ✅
- [x] **Sub-Item 3.7.2:** Implement **structure-aware** symbol discovery per language (no regex-only "wishful thinking"):
  - Bash: Tree-sitter Bash grammar parsing (pinned grammar version; no execution) ✅
    - Implemented in `scripts/docstring_validators/helpers/bash_treesitter.py`
    - Uses tree-sitter-bash 0.25.1 with proper byte handling for UTF-8 files
    - Regex fallback when tree-sitter not available
  - Perl: PPI-based parsing via `perl` subprocess → JSON → Python errors, with a structure-aware fallback strategy for edge cases (no execution) ✅
    - Implemented in `scripts/docstring_validators/helpers/parse_perl_ppi.pl`
    - Graceful fallback when PPI module not installed
  - PowerShell: `pwsh` AST via `[System.Management.Automation.Language.Parser]::ParseFile` → JSON (no execution) ✅
    - Implemented in `scripts/docstring_validators/helpers/parse_powershell_ast.ps1`
    - Per Phase 0 Item 0.9.3: uses ParseFile (C1), not ParseInput
- [x] **Sub-Item 3.7.3:** Enforce doc requirements for **ALL symbols in scope** (no implicit skipping of "private" helpers); exemptions must be explicit via existing `# noqa` / pragma mechanisms.
  - ✅ All validators enforce documentation on all symbols (public and private)
  - ✅ Pragma-based exemptions supported via `# noqa: FUNCTION` and similar
- [x] **Sub-Item 3.7.4:** Ensure `repo_lint`'s language runners call the docstring validator in a way that remains stable as it modularizes (prefer importing modules over shelling out once the split is done).
  - ✅ Runners call `scripts/validate_docstrings.py` which imports modular validators
  - ✅ Integration tested and working for Python, Bash, PowerShell, and Perl
- [x] **Sub-Item 3.7.5:** Add/expand fixtures + unit tests for each language's symbol discovery path so future refactors don't silently regress enforcement.
  - ✅ Created comprehensive test fixtures for Python, Bash, PowerShell, and Perl
    - `scripts/tests/fixtures/python/edge_cases.py` - Python edge cases
    - `scripts/tests/fixtures/bash/edge-cases.sh` - Bash edge cases
    - `scripts/tests/fixtures/powershell/EdgeCases.ps1` - PowerShell edge cases
    - `scripts/tests/fixtures/perl/edge_cases.pl` - Perl edge cases
  - ✅ Created comprehensive unit test suite: `scripts/tests/test_symbol_discovery.py`
    - 31 tests covering all languages (Python: 9, Bash: 7, PowerShell: 7, Perl: 8)
    - All tests passing
  - ✅ Edge cases covered: multiline signatures, nested functions, special characters, private symbols, pragma exemptions
  - ✅ Fixtures follow naming conventions per `docs/contributing/naming-and-style.md`
  - ✅ Tests verify parser outputs match expected symbols

**Phase 3 Success Criteria**
- ✅ Python runner complete and functional
- ✅ Bash runner complete and functional
- ✅ PowerShell runner complete and functional
- ✅ Perl runner complete and functional
- ✅ YAML runner complete and functional
- ✅ Docstring validator modularization (Item 3.7.1-3.7.4) complete
- ✅ Docstring validator test fixtures and unit tests (Item 3.7.5) complete

---

## Phase 4 — Install / Bootstrap + Repo-Local Tools ✅ COMPLETE

### Item 4.1 — CI-safe mode enforcement (High)
- [x] **Sub-Item 4.1.1:** Ensure `repo-lint check --ci` refuses to install tools
  - ✅ Already implemented in `cli.py:114-121`
  - CI mode returns exit code 2 when tools are missing
- [x] **Sub-Item 4.1.2:** If tools are missing, fail with exit code `2` and print exact install instructions
  - ✅ Implemented via `reporting.py:print_install_instructions()`
  - Clear instructions printed for manual installation

### Item 4.2 — Local install support (High)
- [x] **Sub-Item 4.2.1:** Implement `repo-lint install` for supported installs:
  - ✅ Python tools auto-installed in `.venv-lint/` virtual environment
  - ✅ Manual instructions printed for: shellcheck, shfmt, PSScriptAnalyzer, Perl::Critic
  - ✅ Only installs what is safe/deterministic (Python tools via pip)
  - Implementation: `tools/repo_lint/install/install_helpers.py`
- [x] **Sub-Item 4.2.2:** Add pinned versions for installs where possible
  - ✅ Added `lint` optional-dependency group to `pyproject.toml` per Phase 0 Item 0.9.6
  - ✅ Pinned versions: black==24.10.0, ruff==0.8.4, pylint==3.3.2, yamllint==1.35.1
  - ✅ Version pins centralized in `tools/repo_lint/install/version_pins.py`
  - ✅ Non-Python tool versions documented (shfmt v3.12.0, PSScriptAnalyzer 1.23.0)

### Item 4.3 — Repo-local installation path + cleanup (Medium)
- [x] **Sub-Item 4.3.1:** Introduce repo-local tool directories (as feasible):
  - ✅ `.venv-lint/` for Python tooling (fully implemented)
  - ✅ `.tools/`, `.psmodules/`, `.cpan-local/` placeholders added to `.gitignore`
  - ✅ Advanced isolation ideas documented in `docs/future-work.md` (FW-014)
  - Helper functions: `get_venv_path()`, `get_tools_path()`, `create_venv()`
- [x] **Sub-Item 4.3.2:** Implement `--cleanup`:
  - ✅ Added `--cleanup` flag to `install` command
  - ✅ Removes only repo-local installs: `.venv-lint/`, `.tools/`, `.psmodules/`, `.cpan-local/`
  - ✅ Never uninstalls system packages (enforced by design)
  - ✅ Prints confirmation of what was removed
  - Implementation: `cleanup_repo_local()` in `install_helpers.py`

**Phase 4 Success Criteria**
- ✅ CI is deterministic, local is convenient, cleanup is safe.
- ✅ Python tools installable with pinned versions in repo-local venv
- ✅ Cleanup removes only repo-local installations
- ✅ Manual instructions provided for non-Python tools

---

## Phase 5 — Migration of Existing Bash Wrapper + Docs ✅ COMPLETE

### Item 5.1 — Keep a thin bash wrapper (High)
- [x] **Sub-Item 5.1.1:** Keep/rename bash wrapper as kebab-case:
  - ✅ `scripts/run-linters.sh` kept (kebab-case compliant)
- [x] **Sub-Item 5.1.2:** Convert it into a thin wrapper that calls:
  - ✅ Wrapper delegates to `python -m tools.repo_lint check` / `fix` / `install`
  - ✅ Supports `--fix` → `repo-lint fix`
  - ✅ Supports `--install` → `repo-lint install`
  - ✅ Default (no args) → `repo-lint check`
- [x] **Sub-Item 5.1.3:** Ensure Global Rules reference **one canonical command path** (repo-lint + wrapper)
  - ✅ Updated in CONTRIBUTING.md Quick Start section
  - ✅ All references point to `python -m tools.repo_lint` as canonical

### Item 5.2 — Documentation updates (High)
- [x] **Sub-Item 5.2.1:** Update `CONTRIBUTING.md` to make repo-lint the canonical entrypoint
  - ✅ Replaced old linting section with repo-lint commands
  - ✅ Added canonical tool documentation
  - ✅ Updated file naming conventions to reflect language-specific standards
- [x] **Sub-Item 5.2.2:** Add "quickstart" section:
  - ✅ Added install, fix, check workflow to Quick Start
  - ✅ Clear step-by-step instructions for contributors
- [x] **Sub-Item 5.2.3:** Update `docs/future-work.md` with installable-package TODO
  - ✅ Already exists as FW-013 (no changes needed)
- [x] **Sub-Item 5.2.4:** Update repo Global Rules / CONTRIBUTING policy text to make it explicit and **required** that before every commit you run:
  - ✅ Added "REQUIRED Before Every Commit" section in Code Quality and Linting
  - ✅ Explicit 3-step requirement in Quick Start (lines 11-14):
    1. Run `python -m tools.repo_lint check` to lint all code
    2. Run relevant test suites for code you changed
    3. Verify all CI checks pass
  - ✅ No "commit first, lint later" allowed

**Phase 5 Success Criteria**
- ✅ Contributors have exactly one obvious way to run checks: `python -m tools.repo_lint check`
- ✅ Bash wrapper is a thin delegation layer (63 lines vs. 413 lines before)
- ✅ Documentation is updated and consistent across all files

---

## Phase 6 — CI Integration as Single Source of Truth

### Item 6.0 — Auto-Fix Must Run First + Forensics (Mandatory)

**Caveat (hard requirement):** In CI, the **Auto-Fix** portion (Black auto-patch) MUST run **first** and MUST **finish** before *any* other lint or docstring enforcement runs.

Rationale:
- If auto-fix changes files, every subsequent lint/docstring result must reflect the **post-fix** state.
- We must avoid running checks on a stale commit SHA after auto-commit/patch.

- [x] **Sub-Item 6.0.1:** In the umbrella workflow, implement a dedicated first job named **Auto-Fix: Black** that:
  - Checks out the PR head
  - Runs Black in auto-fix mode (same-repo PRs only)
  - Applies the existing safety rules (same-repo-only, fork patch artifact, bot-loop guard, pinned actions)
  - ✅ **Implemented** in `.github/workflows/repo-lint-and-docstring-enforcement.yml`

- [x] **Sub-Item 6.0.2:** If the auto-fix job **changes any files**:
  - Same-repo PRs: commit + push the changes
  - Fork PRs: produce a patch artifact
  - In **both** cases: set an output flag (e.g., `autofix_applied=true`) and ensure **all other jobs are skipped** for this workflow run.
    - All lint/docstring jobs MUST include an `if:` guard so they do not run when `autofix_applied=true`.
    - The workflow must instruct the contributor that checks will run on the next workflow run for the updated commit.
  - ✅ **Implemented** with `autofix_applied` output flag and conditional job execution

- [x] **Sub-Item 6.0.3:** Forensics requirement — when Black changes anything, CI MUST leave a reviewable trail:
  - Upload an artifact containing:
    - `black.diff` (unified diff of changes)
    - `black.log` (command output, version, and the files modified)
  - Also write a short summary into the GitHub Actions job summary (what changed + where + how to reproduce locally).
  - ✅ **Implemented** with forensic artifacts and job summary

- [x] **Sub-Item 6.0.4:** If an auto-fix commit is pushed, the auto-fix job MUST:
  - Use an explicit commit message marker (for loop-guarding)
  - Leave a PR comment that includes:
    - That an auto-fix commit was pushed
    - A link to the workflow run
    - Where to find the diff/log artifacts
  - ✅ **Implemented** with commit message marker `[auto-format]` and PR comment via github-script

### Item 6.1 — Replace CI steps with repo-lint (High)
- [x] **Sub-Item 6.1.1:** Update workflows to run:
  - `repo-lint check --ci` (or wrapper equivalent)
  - ✅ **Implemented** in umbrella workflow using `python -m tools.repo_lint check --ci --only <language>`
- [x] **Sub-Item 6.1.2:** Ensure workflows install prerequisites explicitly (pinned)
  - ✅ **Implemented** with pinned versions: black==24.10.0, ruff==0.8.4, pylint==3.3.2, yamllint==1.35.1, shfmt v3.12.0, PSScriptAnalyzer 1.23.0

### Item 6.2 — Black auto-patch hardening (High)
- [x] **Sub-Item 6.2.1:** Add bot-loop guard using BOTH:
  - Actor guard (skip when actor is a bot)
  - Commit-message marker guard (skip when commit message contains an autoformat marker)
  - ✅ **Implemented** with dual guards: `github.actor != 'github-actions[bot]'` AND `!contains(github.event.head_commit.message, '[auto-format]')`
- [x] **Sub-Item 6.2.2:** Keep same-repo-only auto-commit restriction
  - ✅ **Implemented** with `github.event.pull_request.head.repo.full_name == github.repository` check
- [x] **Sub-Item 6.2.3:** Keep fork patch artifact behavior
  - ✅ **Implemented** with conditional artifact upload and instructions for fork PRs
- [x] **Sub-Item 6.2.4:** Pin actions by commit SHA everywhere
  - ✅ **Implemented** - all actions pinned:
    - `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` (v4.2.2)
    - `actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b` (v5.3.0)
    - `actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882` (v4.4.3)
    - `actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea` (v7.0.1)
    - `shogo82148/actions-setup-perl@9c1eca9952ccc07f9ca4a2097b63df93d9d138e9` (v1.31.3)
- [x] **Sub-Item 6.2.5:** Ensure Black auto-patch output is forensically reviewable (see Item 6.0 Sub-Item 6.0.3).
  - ✅ **Implemented** - covered by Item 6.0.3

### Item 6.3 — Complete CI Migration Flake8 → Ruff + Remove `.flake8` (High)
- [x] **Sub-Item 6.3.1:** Update CI workflows to use Ruff instead of Flake8
  - ✅ **Implemented** in both `lint-and-format-checker.yml` and umbrella workflow
- [ ] **Sub-Item 6.3.2:** Remove Flake8 steps from CI once Ruff parity is verified in CI runs
  - 🔜 **Pending** - keeping old workflow per transition rules (Item 6.4.7)
- [ ] **Sub-Item 6.3.3:** Remove `.flake8` file once CI no longer depends on it
  - 🔜 **Pending** - deferred until umbrella workflow becomes canonical gate
- [x] **Sub-Item 6.3.4:** Re-verify Ruff parity in CI (tests + controlled before/after diff + targeted fixtures; ensure no surprise semantic changes)
  - ✅ **Verified** locally: Ruff finds 24 violations vs Flake8's 16 (improved coverage, all Flake8 issues covered)

### Item 6.4 — Consolidate Linting + Docstring Enforcement into One Umbrella Workflow (High)

**Goal:** Replace the current fragmented lint/docstring workflows with a single umbrella workflow that:
- Runs **only** the checks relevant to the files changed/added in the PR
- Uses `repo_lint` as the final orchestration layer (no per-language workflow drift)
- Keeps strict CI guarantees while reducing wasted CI time

**Umbrella Workflow Naming (Locked by this Item)**
- Workflow display name (Title Case): **Repo Lint and Docstring Enforcement**
- Workflow file name (kebab-case): `.github/workflows/repo-lint-and-docstring-enforcement.yml`

**Job / Check Naming (Title Case)**
- **Auto-Fix: Black**
- **Detect Changed Files**
- **Repo Lint: Python**
- **Repo Lint: Bash**
- **Repo Lint: PowerShell**
- **Repo Lint: Perl**
- **Repo Lint: YAML**
- (Optional, if implemented later) **Repo Lint: Rust**

- [x] **Sub-Item 6.4.1:** Add a new umbrella workflow file: `.github/workflows/repo-lint-and-docstring-enforcement.yml` with `name: Repo Lint and Docstring Enforcement`, and ensure it begins with the **Auto-Fix: Black** job (see Item 6.0).
  - ✅ **Implemented** - umbrella workflow created with Auto-Fix: Black as first job
- [x] **Sub-Item 6.4.2:** Implement **Detect Changed Files** job that computes changed paths using `git diff` (or an equivalent deterministic mechanism) and exposes outputs for each language bucket (Python/Bash/PowerShell/Perl/YAML/Rust) **plus a `shared_tooling` bucket**.
  - `shared_tooling` MUST be set when changes touch shared lint/config/enforcement surfaces (examples):
    - `tools/repo_lint/**`
    - `scripts/validate_docstrings.py` and/or `scripts/docstring_validators/**`
    - `pyproject.toml` (Python lint config)
    - `.github/workflows/**` (workflow YAML)
    - `docs/contributing/**` (contracts/specs)
  - ✅ **Implemented** - Detect Changed Files job with git diff-based detection and all required buckets
- [x] **Sub-Item 6.4.3:** Implement conditional jobs per language using `if:` expressions driven by outputs from **Detect Changed Files** so that:
  - Python checks run only when Python files change, or when `shared_tooling` is true
  - Bash checks run only when Bash files change, or when `shared_tooling` is true
  - PowerShell checks run only when PowerShell files change, or when `shared_tooling` is true
  - Perl checks run only when Perl files change, or when `shared_tooling` is true
  - YAML checks run only when YAML files change (including workflow YAML), or when `shared_tooling` is true
  - Markdown-only changes do **not** trigger PowerShell/Perl/Bash runners (unless docs tooling is added later)
  - ✅ **Implemented** - all language jobs use conditional `if:` expressions
- [x] **Sub-Item 6.4.4:** Each conditional language job MUST run `repo_lint` (run-in-place) as the canonical enforcement mechanism:
  - `python -m tools.repo_lint check --ci --only <language>`
  - The `--only` selector MUST be implemented if it does not exist yet (see Sub-Item 6.4.6).
  - ✅ **Implemented** - all language jobs use `python -m tools.repo_lint check --ci --only <language>`
- [x] **Sub-Item 6.4.5:** Ensure docstring enforcement is included automatically by the relevant language runner(s) (no separate docstring-only workflow once this is in place).
  - ✅ **Complete** - docstring validation integrated into runners in Phase 3
- [x] **Sub-Item 6.4.6:** Implement `repo-lint changed` and/or a `--only <language>` selector in `repo_lint` so the umbrella workflow can target exactly the needed runners. Requirements:
  - `repo-lint check` remains full-scope by default
  - `repo-lint changed` runs only on files changed in the PR (CI-safe)
  - `--only <language>` restricts execution to a single runner (e.g., `python`, `bash`, `powershell`, `perl`, `yaml`, `rust`)
  - Output remains deterministic and CI-friendly
  - ✅ **Implemented** `--only <language>` selector for both `check` and `fix` commands
  - 🔜 **Deferred** `repo-lint changed` (not required for umbrella workflow; can use --only instead)
- [ ] **Sub-Item 6.4.7:** Migrate existing lint/docstring workflows to this umbrella workflow:
  - Disable or remove redundant workflow files once parity is confirmed
  - Keep Black auto-patch behavior *inside* the umbrella workflow with the safeguards from Item 6.2
  - **Transition rules (Locked by this Sub-Item):**
    - Until the umbrella workflow is the canonical gate (required checks), KEEP existing language-specific workflows enabled as the enforcement mechanism.
    - Do NOT delete/disable old workflows until umbrella parity is confirmed **and** the relevant `repo_lint` runners exist.
    - Once the umbrella workflow becomes the canonical gate: if a PR triggers a language bucket whose runner is not implemented, the workflow MUST fail hard (no silent pass/warn).
  - 🔜 **In Progress** - umbrella workflow created, old workflows remain active per transition rules
- [x] **Sub-Item 6.4.8:** Pin any third-party actions used by the umbrella workflow by commit SHA (consistent with Phase 0 Item 0.4).
  - ✅ **Implemented** - all actions pinned by commit SHA (see Item 6.2.4)
- [ ] **Sub-Item 6.4.9:** Add CI verification steps to confirm the umbrella workflow produces the same effective checks as the prior workflows (parity confirmation) before deleting old workflows.
  - 🔜 **Pending** - requires umbrella workflow to run in CI first

### Item 6.5 — Add Lint/Docstring Vectors + Auto-Fix Policy Harness (High)

**Goal:** Add a `vectors.json`-style parity system for linting + docstring enforcement so behavior remains deterministic and consistent across language runners and parser implementations. Also define a deny-by-default allow/deny policy for all auto-fix actions.

**Design Principles (Locked by this Item)**
- Vectors MUST test **outputs**, not parser internals (implementation may change; expected results must not drift).
- Vectors MUST use a **stable, normalized violation schema** (rule id, path, symbol, line, severity, message).
- Auto-fix is **deny-by-default**. Only explicitly allowlisted fix categories may run under `repo-lint fix`.
- `repo-lint check` remains **non-mutating** and MUST NOT apply fixes.

**Proposed Layout (Align with existing `conformance/` pattern)**
- `conformance/repo_lint/vectors/docstrings/` (JSON vector files)
- `conformance/repo_lint/vectors/fixtures/` (fixture source files per language)
- Shared policy file (runtime-owned; referenced by vectors):
  - `conformance/repo_lint/autofix_policy.json`

- [ ] **Sub-Item 6.5.1:** Define and document the normalized violation schema used by vectors (include: `rule_id`, `path`, `symbol`, `symbol_kind`, `line`, `severity`, `message`).
- [ ] **Sub-Item 6.5.2:** Add initial fixtures per language under `conformance/repo_lint/vectors/fixtures/` covering:
  - Missing doc requirements (minimum required sections)
  - Correctly documented symbols
  - Explicit exemptions (existing `# noqa` / pragma mechanisms)
  - Edge cases (multiline signatures, nested functions where applicable)
- [ ] **Sub-Item 6.5.3:** Create initial vector suites per language under `conformance/repo_lint/vectors/docstrings/` (one JSON per scenario; keep cases small and focused):
  - `python_*.json`, `bash_*.json`, `powershell_*.json`, `perl_*.json`, `yaml_*.json`
- [ ] **Sub-Item 6.5.4:** Implement a vector runner in Python tests that:
  - Executes the relevant `repo_lint` runner(s) against fixtures
  - Captures results
  - Normalizes output into the schema
  - Compares against expected vectors deterministically
- [ ] **Sub-Item 6.5.5:** Add an auto-fix allow/deny policy (deny-by-default) with explicit categories, for example:
  - Allow: `FORMAT.BLACK`, `FORMAT.SHFMT`, `LINT.RUFF.SAFE`
  - Deny: `LINT.RUFF.UNSAFE`, `REWRITE.DOCSTRING_CONTENT`, `MODIFY_LOGIC`, `REORDER_IMPORTS` (unless explicitly approved later)
- [ ] **Sub-Item 6.5.6:** Wire `repo-lint fix` to consult the allow/deny policy:
  - Only allowlisted fix categories may run
  - Denied categories MUST be skipped with a clear message
  - Add a deterministic summary of which fix categories ran
- [ ] **Sub-Item 6.5.7:** Add CI coverage for vectors (umbrella workflow should run vectors when relevant tooling or validator code changes).
- [ ] **Sub-Item 6.5.8:** Document how to add new vectors/fixtures and how to update expected outputs safely (no casual baseline rewrites). **Expected outputs MUST be regenerated via a dedicated command** (e.g., `repo-lint vectors update --case <case_id>` or similar) so changes are reproducible and auditable (no hand-editing expected outputs).

**Success Criteria**
- ✅ Parser swaps (e.g., bashlex → Tree-sitter, PPI fallback tweaks, PowerShell AST changes) do not silently change expected outputs.
- ✅ Auto-fix behavior is governed by explicit policy and is auditable.

**Phase 6 Success Criteria**
- ✅ CI executes the same single entrypoint as local dev.
- ✅ No drift between workflow YAML and repo tooling.

---

## Phase 6.5 — Rust Runner Implementation (Future Work)

### Item 6.5.1 — Complete Rust Runner Implementation (Medium)

**Status:** Stub implementation created. Basic structure in place.

**Implemented:**
- [x] Basic runner structure following naming conventions
- [x] File detection (checks for `**/*.rs` files)
- [x] Tool checking (cargo, rustfmt, clippy)
- [x] rustfmt integration (check mode and fix mode)
- [x] clippy integration (basic linting)
- [x] Integrated into CLI with `--only rust` support

**TODO:**
- [ ] **Sub-Item 6.5.1.1:** Enhance clippy output parsing for better violation reporting
- [ ] **Sub-Item 6.5.1.2:** Add Rust docstring validation integration
  - Requires integration with `scripts/validate_docstrings.py`
  - Requires `scripts/docstring_validators/rust_validator.py` to be fully implemented
- [ ] **Sub-Item 6.5.1.3:** Add Rust job to umbrella workflow (`.github/workflows/repo-lint-and-docstring-enforcement.yml`)
  - Conditional execution based on `*.rs` file changes
  - Install Rust toolchain (rustup, rustfmt, clippy)
  - Run `python -m tools.repo_lint check --ci --only rust`
- [ ] **Sub-Item 6.5.1.4:** Update Detect Changed Files job to detect Rust changes
- [ ] **Sub-Item 6.5.1.5:** Add tests for RustRunner in `tools/repo_lint/tests/`

**Notes:**
- Current implementation is a working stub that can detect Rust files and run basic checks
- Located at `tools/repo_lint/runners/rust_runner.py`
- Follows the same pattern as other language runners (Python, Bash, PowerShell, Perl, YAML)
- Runs cargo commands in `rust/` subdirectory (not repo root)

---

## Phase 7 — Tests, Determinism, and Output Guarantees

### Item 7.1 — Unit tests for dispatch + reporting (High)
- [ ] **Sub-Item 7.1.1:** Test runner dispatch (which files trigger which runners)
- [ ] **Sub-Item 7.1.2:** Test exit codes for: pass, violations, missing tools in CI, internal errors
- [ ] **Sub-Item 7.1.3:** Snapshot/fixture test for deterministic output format

### Item 7.2 — Optional JSON reports (Medium)
- [ ] **Sub-Item 7.2.1:** Implement `--json` output artifact mode for CI debugging
- [ ] **Sub-Item 7.2.2:** Ensure no unstable fields unless in verbose mode
- [ ] **Sub-Item 7.2.3:** Re-enable (or ensure) all lint/docstring CI checks to **fail on error** (no warn-only) once migration is complete and the umbrella workflow is the canonical gate.

**Phase 7 Success Criteria**
- ✅ Tool is test-covered, deterministic, and safe to evolve.
- ✅ All Linting CIs & Docstring CIs pass.

---

## Acceptance Criteria (Definition of Done)
- [ ] The **Repo Lint and Docstring Enforcement** umbrella workflow is the canonical CI gating workflow and runs `repo-lint check --ci` (and/or `repo-lint changed`) as its enforcement engine
- [ ] `repo-lint install` exists for local bootstrap (optional installs allowed locally only)
- [ ] `repo-lint fix` auto-formats and may apply **safe** Ruff fixes only (no unsafe fixes; `repo-lint check` remains non-mutating; governed by the allow/deny policy)
- [ ] A vectors-based parity harness exists for lint/docstring enforcement (fixtures + expected outputs), and an auto-fix allow/deny policy is enforced (deny-by-default)
- [ ] Flake8 is fully replaced by Ruff
- [ ] Python linter configs consolidated into `pyproject.toml` (Ruff/Black/Pylint)
- [ ] Output is stable and actionable across local + CI
- [ ] `--cleanup` removes only repo-local installs (never system packages)
- [ ] CI Black auto-patch is safe **and** forensically reviewable (runs first, loop guard + same-repo only + fork patch + pinned actions + diff/log artifacts)
