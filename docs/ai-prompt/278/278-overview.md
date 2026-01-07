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

---

## Notes / Guardrails

- Enforce in **check** mode first; keep **fix** mode conservative.
- Avoid “clever inference” in automated tooling; prefer deterministic rules and human review for complex typing.
- Keep tests/fixtures policy explicit (some fixtures intentionally violate rules; they must be scoped and documented).
