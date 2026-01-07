# [EPIC] [BLOCKER TO ISSUE #160] Issue: Enforce Python Type Annotations + reST Docstring Return Types (PEP 526 + function annotations)

## Goal

Bring the repo’s Python code into a **single, enforceable standard** for:

- **PEP 526 variable annotations** (`x: T = ...`) repo-wide
- **Function annotations** everywhere (`def f(x: T) -> R:`) including explicit `-> None`
- **reST docstring completeness**: if a function returns a value, its docstring MUST include `:rtype:`

This issue is intentionally phased to avoid a “big-bang” PR and to keep CI usable.

---

## Phase 0 — Preflight: establish current state (MANDATORY)

### 0.1 Snapshot repo + tooling

- [ ] From repo root, run the standard gate(s) used in this repo (CI/pre-commit equivalents).
- [ ] Capture current Python toolchain versions used by CI (ruff/black/pylint/etc.).
- [ ] Identify where Python lint/docstring/naming contracts are documented:
  - [ ] Search docs for “Python”, “docstring”, “naming”, “contracts”, “repo-lint”.
  - [ ] Record canonical doc(s) that define “correct” Python behavior.

### 0.2 Inventory all Python files (MANDATORY)

- [ ] Enumerate all `*.py` files and classify them:
  - [ ] Product/library code
  - [ ] CLI/utility scripts
  - [ ] Tests/fixtures
  - [ ] Generated or third-party vendored code (if any)
- [ ] Identify any “excluded” directories/patterns already in use (and why).

**Deliverable:** `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-python-annotation-inventory.md`

- paths + counts
- existing exclusions
- current lint/docstring rules referenced by the repo

---

## Phase 1 — Evaluate existing Python contracts (naming/docstrings/symbols/linting)

### 1.1 Collect “contracts” that already exist

- [ ] Identify current enforcement mechanisms:
  - [ ] `repo-lint` Python runner rules
  - [ ] any standalone docstring validation scripts
  - [ ] CI workflows that run Python checks
- [ ] List *exactly* what is already enforced today:
  - [ ] naming conventions (files/classes/functions/constants)
  - [ ] docstring requirements (format + required fields)
  - [ ] linting tools and rulesets (ruff/black/pylint/etc.)
  - [ ] symbol export expectations (if any)

### 1.2 Current-violations baseline

- [ ] Run the current Python checks and collect a baseline of failures/warnings.
- [ ] Identify the most common failure categories and which are “autofixable”.

**Deliverable:** A short “baseline report” section inside `{ISSUE_NUMBER}-summary.md`:

- top failure categories
- approximate counts
- which ones are safe to auto-fix

---

## Phase 2 — Define the policy: what “Enforce PEP 526 repo-wide” means

### 2.1 Policy specification (MANDATORY)

Write a concrete policy in a doc so the tooling can implement it deterministically.

- [ ] Define which scopes require PEP 526 annotations:
  - [ ] module-level assignments
  - [ ] class attributes
  - [ ] local variables
- [ ] Define which patterns **MUST** be annotated (recommended minimum set):
  - [ ] empty literals (ambiguous inference): `{}`, `[]`, `set()`, `dict()`, `list()`, `tuple()`
  - [ ] `None` initializations intended to be later replaced (common bug factory)
  - [ ] public “configuration” variables/constants
- [ ] Define allowed fallback types when exact type is unknown:
  - [ ] `Any` vs `object` vs `Unknown`-style patterns
- [ ] Decide policy on these edge cases:
  - [ ] comprehensions
  - [ ] unpacking assignment
  - [ ] `global`/`nonlocal`
  - [ ] dynamic attribute injection patterns

**Deliverable:** `docs/contributing/python-typing-policy.md` (or repo-equivalent canonical location)

### 2.2 Function annotations policy (MANDATORY)

- [ ] All functions MUST have:
  - [ ] annotations for every parameter (including keyword-only)
  - [ ] annotation for return type
- [ ] Functions returning nothing MUST be explicitly `-> None`
- [ ] For `*args` and `**kwargs`, define allowed forms (pick one):
  - [ ] `*args: Any, **kwargs: Any`
  - [ ] `*args: object, **kwargs: object`
  - [ ] typed tuples / `Unpack[...]` (advanced; optional later)

### 2.3 Docstring return type policy (MANDATORY)

- [ ] reST docstrings MUST include `:rtype:` when the function returns a value
- [ ] If return is `None`, allow:
  - [ ] no `:rtype:` (recommended), OR
  - [ ] `:rtype: None` (allowed if you prefer symmetry)
- [ ] Define how generators/iterators should be documented (`Iterator[T]`, `Generator[T, None, None]`, etc.)

---

## Phase 3 — Tooling design: can `repo_lint` enforce this?

### 3.1 Evaluate existing `repo_lint` Python runner

- [ ] Locate where Python rules run (runner + config).
- [ ] Determine whether the existing pipeline can host a new checker stage:
  - [ ] “type annotations checker” stage in `check --ci`
  - [ ] optional “fix” mode support (later)

### 3.2 Prefer existing linters where possible (reduce custom code)

- [ ] Use Ruff rules for function annotations if feasible:
  - [ ] enable annotation rules (e.g., flake8-annotations / `ANN*`) via ruff config
  - [ ] explicitly require return annotations, including `-> None`
- [ ] Evaluate docstring tooling for `:rtype:`:
  - [ ] if ruff cannot enforce it: introduce a dedicated checker (custom or a docstring tool)
  - [ ] ensure it can run in CI and locally consistently

### 3.3 Implement missing enforcement in `repo_lint` (if needed)

If `repo_lint` cannot fully enforce PEP 526 + `:rtype:`:

- [ ] Add a **Python AST-based checker** (safe, deterministic) that:
  - [ ] parses Python files with `ast`
  - [ ] flags assignments that violate the PEP 526 policy
  - [ ] flags function defs missing parameter/return annotations
  - [ ] flags functions returning non-None that lack `:rtype:` in reST docstring
- [ ] Add config knobs for exclusions / gradual rollout:
  - [ ] per-path ignore list
  - [ ] per-rule disable switches (temporary, but must be documented)

**Deliverable:** new repo-lint rule(s) with unit tests + integration in `repo-lint check --ci`

### 3.4 Docstring validation consolidation (MANDATORY)

We currently have a docstring validation system implemented via `scripts/validate_docstrings.py` and its related modules. This issue MUST evaluate how `repo_lint` uses that script today, then migrate that logic into the `repo_lint` package so that docstring enforcement is **first-class and internal**, not an external script dependency.

#### 3.4.1 Current state analysis (MANDATORY)

- [ ] Locate and review:
  - [ ] `scripts/validate_docstrings.py`
  - [ ] any Python modules it imports from / depends on (submodules/packages dedicated to docstring validation)
- [ ] Identify and document how `repo_lint` uses this functionality today:
  - [ ] Is it invoked as a subprocess? Imported as a module? Reimplemented partially?
  - [ ] Which runner(s) call it (Python runner only, or shared docstring checks across languages)?
  - [ ] Where configuration lives (CLI args, config files, hard-coded defaults)
- [ ] Produce a concise mapping in the issue journal:
  - [ ] “Current entrypoints” → “What rules are enforced” → “Where results are reported”

#### 3.4.2 Design: internalize docstring validation into `repo_lint` (MANDATORY)

- [ ] Create an internal `repo_lint` module that owns docstring validation logic (example location):
  - [ ] `tools/repo_lint/docstrings/` (or equivalent)
- [ ] Refactor the existing validator implementation so `repo_lint` can call it directly (no subprocess).
- [ ] Ensure the internal API supports:
  - [ ] running checks during `repo-lint check --ci`
  - [ ] stable machine-readable results (suitable for CI failure reports)
  - [ ] future extensibility to enforce additional fields (like `:rtype:`)

#### 3.4.3 Migration plan (NO BREAKAGE)

- [ ] Update `repo_lint` to use the new internal module.
- [ ] Keep `scripts/validate_docstrings.py` as a thin compatibility wrapper initially (optional but recommended):
  - [ ] it should import/call the internal `repo_lint` implementation
  - [ ] it must remain behaviorally equivalent (same exit codes, same core checks)
- [ ] Remove any `repo_lint` runtime dependency on `scripts/validate_docstrings.py`.
- [ ] If legacy modules exist solely to support the old script (and are no longer needed after migration), remove them.

#### 3.4.4 EXTREMELY COMPREHENSIVE unit tests (MANDATORY, NO SHORTCUTS)

This migration MUST include exhaustive test coverage for the new internal docstring validator.

- [ ] Unit tests for:
  - [ ] parsing / discovery of docstrings
  - [ ] rule evaluation (each rule has multiple failing cases and at least one passing case)
  - [ ] error classification / message formatting (stable and deterministic)
  - [ ] exit code behavior and “fail-fast vs aggregate” behavior (as designed)
- [ ] Integration tests that run through `repo-lint check --ci` end-to-end and validate:
  - [ ] expected failures are reported in the correct report artifact format
  - [ ] results do not depend on terminal capabilities (no ANSI garbage in saved artifacts)
- [ ] “Golden” fixtures:
  - [ ] include multiple fixtures that intentionally violate docstring rules
  - [ ] include fixtures that pass (to prevent false positives)
- [ ] Regression tests:
  - [ ] add a test for every bug found during migration so it cannot reoccur

**Deliverable:** Docstring validation runs fully inside `repo_lint`, and test coverage proves parity with the old script.

### 3.5 Markdown contracts + linting support in `repo_lint` (MANDATORY)

Because Copilot sessions now start with Markdown formatting/linting available, we MUST add first-class Markdown linting support into the `repo_lint` package.

This includes:

- defining **repo-wide Markdown contracts** (what “valid” Markdown means here),
- enforcing them consistently via `repo-lint check --ci`, and
- fixing the current repo to conform to the contract.

#### 3.5.1 Define the Markdown contract (MANDATORY)

- [ ] Create a canonical Markdown rules document:
  - [ ] `docs/contributing/markdown-contracts.md` (or repo-equivalent canonical location)
- [ ] Define the contract scope:
  - [ ] Which directories/files are enforced (default: all `*.md`)
  - [ ] Explicit exclusions (generated docs, vendored content, etc.)
- [ ] Define the ruleset explicitly (NO VAGUE RULES). Examples to decide and document:
  - [ ] heading structure (H1 rules, incremental headings)
  - [ ] line length policy (if any) and exceptions
  - [ ] code fence requirements (language tags, consistent fence style)
  - [ ] trailing whitespace policy
  - [ ] required blank lines around lists/headings
  - [ ] link style + link checking expectations (if enforced)
  - [ ] allowed HTML in Markdown (if any)

**Deliverable:** `docs/contributing/markdown-contracts.md` merged and treated as the canonical source of truth.

#### 3.5.2 Choose enforcement mechanism (MANDATORY)

- [ ] Evaluate options and pick ONE default enforcement path:
  - [ ] Use a standard Markdown linter (preferred) and call it from `repo_lint`:
    - [ ] `markdownlint-cli2` (Node) **or**
    - [ ] `markdownlint` (Node) **or**
    - [ ] a Python-based markdown linter (only if Node is not acceptable)
  - [ ] If a standard linter cannot support a contract rule, implement a small deterministic checker inside `repo_lint` to cover the missing rule(s).
- [ ] Decide how configuration is stored:
  - [ ] `.markdownlint.yaml` / `.markdownlint-cli2.jsonc` / repo-equivalent config
  - [ ] mapping from `docs/contributing/markdown-contracts.md` → linter configuration must be explicit

**Deliverable:** Selected linter + config committed, with a clear mapping to the documented contract.

#### 3.5.3 Integrate Markdown checks into `repo_lint` (MANDATORY)

- [ ] Add a Markdown runner to `repo_lint` (or extend an existing runner architecture) that:
  - [ ] discovers Markdown files (`*.md`) respecting exclusions
  - [ ] runs the chosen linter deterministically
  - [ ] produces stable machine-readable results compatible with existing CI failure report artifacts
  - [ ] supports `repo-lint check --ci`
- [ ] Decide fix behavior:
  - [ ] `repo-lint fix` may include Markdown auto-fix ONLY if the chosen tool supports safe deterministic fixes.
  - [ ] If fixes are risky, keep Markdown in check-only mode initially.

**Deliverable:** Markdown linting runs under `repo-lint check --ci` and produces CI-friendly failure artifacts.

#### 3.5.4 Repo baseline cleanup (MANDATORY)

- [ ] Run Markdown linting across the repo.
- [ ] Fix all Markdown files to conform to the new contract (or add explicit, documented exclusions).
- [ ] Ensure `repo-lint check --ci` is green after cleanup.

**Deliverable:** Repo-wide Markdown conformance achieved (or tracked via explicit exclusions).

#### 3.5.5 EXTREMELY COMPREHENSIVE tests (MANDATORY, NO SHORTCUTS)

- [ ] Unit tests for:
  - [ ] Markdown file discovery + exclusion logic
  - [ ] config loading and contract-to-config mapping
  - [ ] result parsing / normalization into repo-lint report format
  - [ ] exit code and failure aggregation behavior
- [ ] Golden fixtures:
  - [ ] multiple `*.md` fixtures with multiple distinct violations
  - [ ] at least one fully compliant fixture
- [ ] Integration tests:
  - [ ] `repo-lint check --ci` end-to-end validation including Markdown failures
  - [ ] failure report artifact contents (stable and ANSI-clean)
- [ ] Regression tests:
  - [ ] add a regression test for every bug found in Markdown integration so it cannot reoccur

**Deliverable:** Markdown linting in `repo_lint` is heavily tested and stable.

### 3.6 TOML contracts + linting support in `repo_lint` (MANDATORY)

Because Copilot sessions now start with TOML linting available, we MUST add first-class TOML linting support into the `repo_lint` package.

This includes:

- defining **repo-wide TOML contracts** (what “valid” TOML means here),
- enforcing them consistently via `repo-lint check --ci`, and
- fixing the current repo to conform to the contract.

#### 3.6.1 Define the TOML contract (MANDATORY)

- [ ] Create a canonical TOML rules document:
  - [ ] `docs/contributing/toml-contracts.md` (or repo-equivalent canonical location)
- [ ] Define the contract scope:
  - [ ] Which files are enforced (default: all `*.toml`)
  - [ ] Explicit exclusions (vendored/generated TOML, tool-managed lockfiles if applicable, etc.)
- [ ] Define the ruleset explicitly (NO VAGUE RULES). Examples to decide and document:
  - [ ] formatting/indentation conventions (spaces vs tabs, indentation width)
  - [ ] key ordering expectations (if any) and whether ordering is enforced
  - [ ] whitespace rules (around `=` and inline tables)
  - [ ] quoting rules (single vs double quotes, when required)
  - [ ] trailing commas policy in inline tables/arrays (if applicable)
  - [ ] allowed multi-line strings conventions
  - [ ] comment style expectations

**Deliverable:** `docs/contributing/toml-contracts.md` merged and treated as the canonical source of truth.

#### 3.6.2 Choose enforcement mechanism (MANDATORY)

- [ ] Evaluate options and pick ONE default enforcement path:
  - [ ] Use a standard TOML linter/formatter (preferred) and call it from `repo_lint`:
    - [ ] **Taplo** (`taplo fmt` / `taplo check`) (recommended)
    - [ ] OR another TOML linter/formatter already used in this repo (if any)
  - [ ] If a standard tool cannot support a contract rule, implement a small deterministic checker inside `repo_lint` to cover the missing rule(s).
- [ ] Decide how configuration is stored:
  - [ ] `taplo.toml` (recommended) or repo-equivalent config
  - [ ] mapping from `docs/contributing/toml-contracts.md` → tool configuration must be explicit

**Deliverable:** Selected tool + config committed, with a clear mapping to the documented contract.

#### 3.6.3 Integrate TOML checks into `repo_lint` (MANDATORY)

- [ ] Add a TOML runner to `repo_lint` (or extend an existing runner architecture) that:
  - [ ] discovers TOML files (`*.toml`) respecting exclusions
  - [ ] runs the chosen tool deterministically
  - [ ] produces stable machine-readable results compatible with existing CI failure report artifacts
  - [ ] supports `repo-lint check --ci`
- [ ] Decide fix behavior:
  - [ ] `repo-lint fix` may include TOML auto-format ONLY if the chosen tool supports safe deterministic formatting.
  - [ ] If fixes are risky, keep TOML in check-only mode initially.

**Deliverable:** TOML linting/formatting runs under `repo-lint check --ci` and produces CI-friendly failure artifacts.

#### 3.6.4 Repo baseline cleanup (MANDATORY)

- [ ] Run TOML linting/formatting across the repo.
- [ ] Fix all TOML files to conform to the new contract (or add explicit, documented exclusions).
- [ ] Ensure `repo-lint check --ci` is green after cleanup.

**Deliverable:** Repo-wide TOML conformance achieved (or tracked via explicit exclusions).

#### 3.6.5 EXTREMELY COMPREHENSIVE tests (MANDATORY, NO SHORTCUTS)

- [ ] Unit tests for:
  - [ ] TOML file discovery + exclusion logic
  - [ ] config loading and contract-to-config mapping
  - [ ] result parsing / normalization into repo-lint report format
  - [ ] exit code and failure aggregation behavior
- [ ] Golden fixtures:
  - [ ] multiple `*.toml` fixtures with multiple distinct violations
  - [ ] at least one fully compliant fixture
- [ ] Integration tests:
  - [ ] `repo-lint check --ci` end-to-end validation including TOML failures
  - [ ] failure report artifact contents (stable and ANSI-clean)
- [ ] Regression tests:
  - [ ] add a regression test for every bug found in TOML integration so it cannot reoccur

**Deliverable:** TOML linting in `repo_lint` is heavily tested and stable.

---

## Phase 4 — Autofix strategy (recommended: staged, not all-at-once)

### 4.1 Add non-destructive autofix where safe

- [ ] Autofix candidates (safe-ish):
  - [ ] add `-> None` where function has no return statements
  - [ ] add missing return annotation where trivially inferrable (optional)
  - [ ] add `:rtype:` for obvious simple returns (optional)
- [ ] Any non-trivial type inference should be **suggested**, not auto-applied.

### 4.2 “Bulk migration” PR plan

- [ ] Create a dedicated PR that:
  - [ ] applies mechanical changes repo-wide
  - [ ] keeps commits small (per directory / per module)
  - [ ] keeps CI green after each commit

---

## Phase 5 — CI enforcement rollout (avoid breaking everyone instantly)

### 5.1 Introduce checks in “report-only” mode

- [ ] Add the checks to CI but do not fail builds for the first pass
- [ ] Produce actionable failure reports (paths + rule + snippet)

### 5.2 Flip to “enforcing” mode

- [ ] Fail CI if:
  - [ ] new violations are introduced, OR
  - [ ] the baseline is fully fixed
- [ ] Remove temporary exemptions once baseline is resolved

---

## Phase 6 — Documentation updates (MANDATORY)

### 6.1 Update repo docs to reflect new contracts

- [ ] Update any user manual / README / contributing docs referencing Python standards.
- [ ] Add “Examples” section:
  - [ ] variable annotations examples (PEP 526)
  - [ ] function annotations examples including `-> None`
  - [ ] reST docstring examples showing `:rtype:`

### 6.2 Verify docs match reality

- [ ] Confirm config files (ruff, pylint, repo-lint configs) match the documented rules.
- [ ] Confirm CI runs the same ruleset described in docs.

---

## Acceptance Criteria (Definition of Done)

- [ ] Policy is written and merged (PEP 526 + function annotations + `:rtype:` rules).
- [ ] `repo-lint check --ci` enforces:
  - [ ] PEP 526 policy (as defined)
  - [ ] function annotations everywhere (including explicit `-> None`)
  - [ ] `:rtype:` required when return is non-None
- [ ] Baseline issues are fixed or tracked via explicit, documented, time-bounded exceptions.
- [ ] CI fails on new violations.
- [ ] Documentation is updated and verified against the repo configuration.
- [ ] `repo-lint check --ci` no longer depends on calling `scripts/validate_docstrings.py` as an external script.
- [ ] The docstring validation implementation is internal to `repo_lint` and covered by extremely comprehensive unit + integration tests.
- [ ] If `scripts/validate_docstrings.py` remains, it is a thin compatibility wrapper over the internal `repo_lint` implementation (no duplicated logic).
- [ ] Markdown contracts are documented in a canonical doc and mapped to a concrete linter configuration.
- [ ] `repo-lint check --ci` enforces Markdown linting repo-wide (with explicit exclusions if needed).
- [ ] Markdown linting integration includes extremely comprehensive unit + integration tests and produces stable CI failure artifacts.
- [ ] TOML contracts are documented in a canonical doc and mapped to a concrete linter/formatter configuration.
- [ ] `repo-lint check --ci` enforces TOML linting/formatting repo-wide (with explicit exclusions if needed).
- [ ] TOML linting integration includes extremely comprehensive unit + integration tests and produces stable CI failure artifacts.

---

## Notes / Guardrails

- Enforce in **check** mode first; keep **fix** mode conservative.
- Avoid “clever inference” in automated tooling; prefer deterministic rules and human review for complex typing.
- Keep tests/fixtures policy explicit (some fixtures intentionally violate rules; they must be scoped and documented).

---
