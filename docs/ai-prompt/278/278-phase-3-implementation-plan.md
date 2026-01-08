# Issue #278 - Phase 3 Implementation Plan

**Created:** 2026-01-07
**Purpose:** Detailed implementation plan for Phase 3 remaining work

## Context

Phase 3 has three MANDATORY large-scope items that involve:

- Creating new internal `repo_lint` modules
- Writing comprehensive test coverage (MANDATORY, NO SHORTCUTS per issue)
- Migrating/consolidating existing functionality
- Creating canonical contract documentation

Each item is substantial and requires focused implementation.

---

## Phase 3.3: PEP 526 Enforcement (Evaluate Need)

### Current Status

- **Ruff ANN* rules enabled** for function annotations (Phase 3.2 complete)
- **Question:** Does Ruff enforce PEP 526 for module-level and class attribute annotations?

### Investigation Needed

1. Test if Ruff ANN* rules cover module-level variable annotations
2. Test if Ruff ANN* rules cover class attribute annotations
3. If gaps exist, evaluate:
   - Option A: Custom AST-based checker in `repo_lint`
   - Option B: Extend existing Ruff rules (upstream contribution)
   - Option C: Use mypy for full static type checking

### Decision Criteria

- If Ruff covers module-level + class attributes: NO custom checker needed (preferred)
- If Ruff has gaps: Implement minimal custom checker for the gaps only
- Avoid reinventing functionality that standard tools provide

### Estimated Scope

- **If Ruff covers it:** 0 hours (already done in Phase 3.2)
- **If custom checker needed:** ~4-6 hours (AST parsing + tests + integration)

---

## Phase 3.4: Docstring Validation Consolidation (MANDATORY)

### Goal

Move `scripts/validate_docstrings.py` functionality into `tools/repo_lint/docstrings/` as a first-class internal module.

### Current State

- **Docstring validation:** External script at `scripts/validate_docstrings.py`
- **Called by:** `tools/repo_lint/runners/python_runner.py` (subprocess)
- **Modules:** `scripts/docstring_validators/*.py` (9 files)
- **Problem:** Subprocess dependency, not first-class repo_lint feature

### Implementation Plan

#### 3.4.1: Current State Analysis (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [x] Locate `scripts/validate_docstrings.py` (DONE - already viewed)
- [ ] Map all imports and dependencies
- [ ] Document current entrypoints in `repo_lint`
- [ ] Map where config lives (CLI args, config files, hardcoded)
- [ ] Create concise mapping in issue journal

**Deliverable:** Section in `278-summary.md` documenting current docstring validation architecture

#### 3.4.2: Design Internal Module (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Create `tools/repo_lint/docstrings/` package structure
- [ ] Design internal API for `repo_lint` to call directly (no subprocess)
- [ ] Ensure stable machine-readable results for CI
- [ ] Support future extensibility for `:rtype:` checking (Phase 3.4 overlap with Python typing policy)

**Deliverable:** Architecture doc or design comments in `278-next-steps.md`

#### 3.4.3: Migration Plan (NO BREAKAGE)

**Status:** NOT STARTED

**Tasks:**

- [ ] Refactor validator implementation into `tools/repo_lint/docstrings/`
- [ ] Update `tools/repo_lint/runners/*_runner.py` to use internal module
- [ ] Keep `scripts/validate_docstrings.py` as thin compatibility wrapper (optional)
- [ ] Remove `repo_lint` subprocess dependency

**Deliverable:** Migrated code, backwards-compatible behavior

#### 3.4.4: EXTREMELY COMPREHENSIVE Tests (MANDATORY, NO SHORTCUTS)

**Status:** NOT STARTED

**Requirements (per issue):**

- [ ] Unit tests for:
  - [ ] Docstring parsing/discovery
  - [ ] Each rule with multiple failing + passing cases
  - [ ] Error classification/message formatting
  - [ ] Exit code behavior (fail-fast vs aggregate)
- [ ] Integration tests via `repo-lint check --ci` end-to-end
  - [ ] Expected failures in correct report artifact format
  - [ ] No ANSI garbage in saved artifacts
- [ ] "Golden" fixtures:
  - [ ] Fixtures with intentional violations
  - [ ] Passing fixtures (prevent false positives)
- [ ] Regression tests:
  - [ ] Test for every bug found during migration

**Estimated Scope:** 8-12 hours (migration + comprehensive tests)

---

## Phase 3.5: Markdown Contracts + Linting Support (MANDATORY)

### Goal

Add first-class Markdown linting support to `repo_lint` with canonical contract documentation.

### Current State

- **Markdown linting:** NOT enforced
- **Copilot sessions:** Start with Markdown formatting/linting available
- **Decision (Locked):** Use **markdownlint-cli2** per issue

### Implementation Plan

#### 3.5.1: Define Markdown Contract (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Create `docs/contributing/markdown-contracts.md` (canonical)
- [ ] Define contract scope (which files enforced, exclusions)
- [ ] Define explicit ruleset (NO VAGUE RULES):
  - [ ] Heading structure (H1 rules, incremental headings)
  - [ ] Line length policy + exceptions
  - [ ] Code fence requirements (language tags, fence style)
  - [ ] Trailing whitespace policy
  - [ ] Blank lines around lists/headings
  - [ ] Link style + link checking
  - [ ] Allowed HTML in Markdown

**Deliverable:** `docs/contributing/markdown-contracts.md` merged

#### 3.5.2: Choose Enforcement Mechanism (MANDATORY)

**Status:** NOT STARTED (but decision locked: markdownlint-cli2)

**Tasks:**

- [ ] Install/configure `markdownlint-cli2` (Node dependency)
- [ ] Create `.markdownlint-cli2.jsonc` config
- [ ] Map contract rules to linter config explicitly
- [ ] Test on sample files

**Deliverable:** markdownlint-cli2 config committed with mapping to contract

#### 3.5.3: Integrate Markdown Checks into `repo_lint` (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Add Markdown runner to `repo_lint` (or extend existing runner architecture)
- [ ] Discover Markdown files (`*.md`) respecting exclusions
- [ ] Run linter deterministically
- [ ] Produce stable machine-readable results (CI-friendly)
- [ ] Support `repo-lint check --ci`
- [ ] Decide fix behavior (auto-fix if safe, else check-only)

**Deliverable:** Markdown linting runs under `repo-lint check --ci`

#### 3.5.4: Repo Baseline Cleanup (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Run Markdown linting across repo
- [ ] Fix all Markdown files to conform (or add documented exclusions)
- [ ] Ensure `repo-lint check --ci` is green after cleanup

**Deliverable:** Repo-wide Markdown conformance achieved

#### 3.5.5: EXTREMELY COMPREHENSIVE Tests (MANDATORY, NO SHORTCUTS)

**Status:** NOT STARTED

**Requirements (per issue):**

- [ ] Unit tests for:
  - [ ] Markdown file discovery + exclusion logic
  - [ ] Config loading and contract-to-config mapping
  - [ ] Result parsing into repo-lint report format
  - [ ] Exit code and failure aggregation
- [ ] Golden fixtures:
  - [ ] Multiple `*.md` with distinct violations
  - [ ] At least one fully compliant fixture
- [ ] Integration tests:
  - [ ] `repo-lint check --ci` end-to-end with Markdown failures
  - [ ] Failure report artifact contents (ANSI-clean)
- [ ] Regression tests for bugs found during integration

**Estimated Scope:** 10-15 hours (contract + integration + tests)

---

## Phase 3.6: TOML Contracts + Linting Support (MANDATORY)

### Goal

Add first-class TOML linting support to `repo_lint` with canonical contract documentation.

### Current State

- **TOML linting:** NOT enforced
- **Copilot sessions:** Start with TOML linting available
- **Decision (Locked):** Use **Taplo** per issue

### Implementation Plan

#### 3.6.1: Define TOML Contract (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Create `docs/contributing/toml-contracts.md` (canonical)
- [ ] Define contract scope (which files enforced, exclusions)
- [ ] Define explicit ruleset (NO VAGUE RULES):
  - [ ] Formatting/indentation (spaces vs tabs, width)
  - [ ] Key ordering expectations + enforcement
  - [ ] Whitespace rules (around `=`, inline tables)
  - [ ] Quoting rules (single vs double, when required)
  - [ ] Trailing commas in inline tables/arrays
  - [ ] Multi-line string conventions
  - [ ] Comment style expectations

**Deliverable:** `docs/contributing/toml-contracts.md` merged

#### 3.6.2: Choose Enforcement Mechanism (MANDATORY)

**Status:** NOT STARTED (but decision locked: Taplo)

**Tasks:**

- [ ] Install/configure **Taplo** (`taplo fmt` / `taplo check`)
- [ ] Create `taplo.toml` config
- [ ] Map contract rules to tool config explicitly
- [ ] Test on sample files (e.g., `pyproject.toml`)

**Deliverable:** Taplo config committed with mapping to contract

#### 3.6.3: Integrate TOML Checks into `repo_lint` (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Add TOML runner to `repo_lint` (or extend existing architecture)
- [ ] Discover TOML files (`*.toml`) respecting exclusions
- [ ] Run Taplo deterministically
- [ ] Produce stable machine-readable results (CI-friendly)
- [ ] Support `repo-lint check --ci`
- [ ] Decide fix behavior (auto-format if safe, else check-only)

**Deliverable:** TOML linting runs under `repo-lint check --ci`

#### 3.6.4: Repo Baseline Cleanup (MANDATORY)

**Status:** NOT STARTED

**Tasks:**

- [ ] Run TOML linting/formatting across repo
- [ ] Fix all TOML files to conform (or add documented exclusions)
- [ ] Ensure `repo-lint check --ci` is green after cleanup

**Deliverable:** Repo-wide TOML conformance achieved

#### 3.6.5: EXTREMELY COMPREHENSIVE Tests (MANDATORY, NO SHORTCUTS)

**Status:** NOT STARTED

**Requirements (per issue):**

- [ ] Unit tests for:
  - [ ] TOML file discovery + exclusion logic
  - [ ] Config loading and contract-to-config mapping
  - [ ] Result parsing into repo-lint report format
  - [ ] Exit code and failure aggregation
- [ ] Golden fixtures:
  - [ ] Multiple `*.toml` with distinct violations
  - [ ] At least one fully compliant fixture
- [ ] Integration tests:
  - [ ] `repo-lint check --ci` end-to-end with TOML failures
  - [ ] Failure report artifact contents (ANSI-clean)
- [ ] Regression tests for bugs found during integration

**Estimated Scope:** 10-15 hours (contract + integration + tests)

---

## Total Estimated Scope for Remaining Phase 3

- **3.3 (PEP 526):** 0-6 hours (depends on Ruff coverage)
- **3.4 (Docstring consolidation):** 8-12 hours
- **3.5 (Markdown):** 10-15 hours
- **3.6 (TOML):** 10-15 hours

**Total:** 28-48 hours of focused implementation work

---

## Recommended Next Session Strategy

Given the scope, the next session should:

1. **Complete Phase 3.3 investigation** (quick - 30 min)
   - Test Ruff ANN coverage for module-level + class attributes
   - Decide if custom checker needed

2. **Pick ONE of 3.4, 3.5, or 3.6** and complete it fully
   - Rationale: Each is independent and can be completed in isolation
   - Order recommendation: 3.4 first (Python-focused, aligns with issue theme)

3. **Alternative: Start with "quick wins"**
   - If 3.4/3.5/3.6 are too large for one session, break them into sub-phases
   - Example: Complete 3.5.1 + 3.5.2 (contract + config) in one session
   - Then 3.5.3 + 3.5.4 + 3.5.5 (integration + tests) in next session

---

## Session Handoff Notes

**Current branch:** `copilot/enforce-python-type-annotations`

**What's done:**

- Phase 0: Preflight (complete)
- Phase 1: Current contracts + baseline (complete)
- Phase 2: Policy documentation (complete)
- Phase 3.2: Ruff ANN* rules enabled with per-file-ignores (complete)

**What's next:**

- Phase 3.3: Quick investigation (30 min)
- Phase 3.4, 3.5, 3.6: Choose one and implement fully

**Key files to review:**

- `docs/ai-prompt/278/278-python-annotation-inventory.md` - Inventory
- `docs/contributing/python-typing-policy.md` - Policy
- `pyproject.toml` - Ruff ANN* configuration
- `tools/repo_lint/runners/python_runner.py` - Current docstring validation entrypoint

**Pre-commit gate reminder:**

- If changing any `*.py`, `*.sh`, `*.pl`, `*.ps1`, `*.rs` in `tools/` or `scripts/`: run `repo-lint check --ci` until exit 0 before committing
