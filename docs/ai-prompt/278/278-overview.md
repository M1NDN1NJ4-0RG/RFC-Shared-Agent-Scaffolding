# [EPIC] [BLOCKER TO ISSUE #160] Issue: Enforce Python Type Annotations + reST Docstring Return Types (PEP 526 + function annotations)

## Goal

Bring the repo’s Python code into a **single, enforceable standard** for:

- **PEP 526 variable annotations** (`x: T = ...`) repo-wide
- **Function annotations** everywhere (`def f(x: T) -> R:`) including explicit `-> None`
- **reST docstring completeness**: if a function returns a value, its docstring MUST include `:rtype:`

This issue is intentionally phased to avoid a “big-bang” PR and to keep CI usable.

## Locked Decisions (Human Approved)

These decisions are **locked in** for this issue and should be treated as requirements unless explicitly changed later.

1. **PEP 526 scope (baseline):** enforce variable annotations for **module-level assignments** and **class attributes** as the mandatory baseline.
   Local-variable annotations are **optional** for now and may be enabled later behind `--strict-typing` and/or “new/changed code only”.

2. **Function annotations:** enforce annotations for **every parameter** and **every return type** repo-wide, including explicit `-> None`.

3. **Unknown types:** prefer **real types** where possible; when unknown, `Any` is allowed **with an explicit tightening tag**:
   `# typing: Any (TODO: tighten)`

4. **Optional / union syntax (max compatibility):** allow PEP 604 `T | None`, but it is **allowed-not-preferred**.
   Prefer `Optional[T]` for broad compatibility, and avoid churn: only update syntax when touching code for another reason.

5. **`*args`/`**kwargs` policy:** use `*args: Any, **kwargs: Any` as the default (advanced `Unpack[...]` is optional later).

6. **Docstring `:rtype:` policy:** require `:rtype:` **only** when a function/method returns a **non-None** value. Do **not** require `:rtype:` for `None`.

7. **Rollout strategy (initial):** start with **maximum compatibility** and **measurement-first** enforcement
   (report-only / baseline) so we can see how bad the churn would be, then tighten gradually.

8. **Markdown tooling:** use **markdownlint-cli2**.

9. **TOML tooling:** use **Taplo**.

10. **Progress UI:** optional. If added, use **Rich** (not tqdm) and keep it **off by default**; enable only when
    attached to a TTY to avoid CI log spam.

---

---

## Phase 0 — Preflight: establish current state (MANDATORY)

### 0.1 Snapshot repo + tooling

- [x] From repo root, run the standard gate(s) used in this repo (CI/pre-commit equivalents).
- [x] Capture current Python toolchain versions used by CI (ruff/black/pylint/etc.).
- [x] Identify where Python lint/docstring/naming contracts are documented:
  - [ ] Search docs for “Python”, “docstring”, “naming”, “contracts”, “repo-lint”.
  - [x] Record canonical doc(s) that define “correct” Python behavior.

### 0.2 Inventory all Python files (MANDATORY)

- [x] Enumerate all `*.py` files and classify them:
  - [x] Product/library code
  - [x] CLI/utility scripts
  - [x] Tests/fixtures
  - [x] Generated or third-party vendored code (if any)
- [x] Identify any “excluded” directories/patterns already in use (and why).

**Deliverable:** `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-python-annotation-inventory.md`

- paths + counts
- existing exclusions
- current lint/docstring rules referenced by the repo

---

## Phase 1 — Evaluate existing Python contracts (naming/docstrings/symbols/linting)

### 1.1 Collect “contracts” that already exist

- [x] Identify current enforcement mechanisms:
  - [x] `repo-lint` Python runner rules
  - [x] any standalone docstring validation scripts
  - [x] CI workflows that run Python checks
- [x] List *exactly* what is already enforced today:
  - [x] naming conventions (files/classes/functions/constants)
  - [x] docstring requirements (format + required fields)
  - [x] linting tools and rulesets (ruff/black/pylint/etc.)
  - [x] symbol export expectations (if any)

### 1.2 Current-violations baseline

- [x] Run the current Python checks and collect a baseline of failures/warnings.
- [x] Identify the most common failure categories and which are “autofixable”.

**Deliverable:** A short “baseline report” section inside `{ISSUE_NUMBER}-summary.md`:

- top failure categories
- approximate counts
- which ones are safe to auto-fix

---

## Phase 2 — Define the policy: what “Enforce PEP 526 repo-wide” means

### 2.1 Policy specification (MANDATORY)

Write a concrete policy in a doc so the tooling can implement it deterministically.

- [x] Define which scopes require PEP 526 annotations:
  - [x] module-level assignments (**MANDATORY baseline**)
  - [x] class attributes (**MANDATORY baseline**)
  - [x] local variables (**OPTIONAL for now**; later gated by `--strict-typing` and/or “new/changed code only”)
- [x] Define which patterns **MUST** be annotated (recommended minimum set):
  - [x] empty literals (ambiguous inference): `{}`, `[]`, `set()`, `dict()`, `list()`, `tuple()`
  - [x] `None` initializations intended to be later replaced (common bug factory)
  - [x] public “configuration” variables/constants
- [x] Define allowed fallback types when exact type is unknown:
  - [x] Prefer **real types** where possible (custom types/modules/classes are encouraged when they clarify intent)
  - [x] `Any` is **allowed** but MUST be explicitly tagged for future tightening:
    - [ ] `# typing: Any (TODO: tighten)`
  - [x] `object` is allowed only when you truly mean “unknown opaque thing” and `Any` would be misleading
- [x] Decide policy on these edge cases:
  - [x] comprehensions
  - [x] unpacking assignment
  - [x] `global`/`nonlocal`
  - [x] dynamic attribute injection patterns

**Deliverable:** `docs/contributing/python-typing-policy.md` (or repo-equivalent canonical location)

### 2.2 Function annotations policy (MANDATORY)

- [x] All functions MUST have:
  - [x] annotations for every parameter (including keyword-only)
  - [x] annotation for return type
- [x] Functions returning nothing MUST be explicitly `-> None`
- [x] For `*args` and `**kwargs`, define allowed forms (LOCKED):
  - [x] `*args: Any, **kwargs: Any` (**default**)
  - [x] typed tuples / `Unpack[...]` (advanced; optional later)

### 2.3 Docstring return type policy (MANDATORY)

- [x] reST docstrings MUST include `:rtype:` when the function returns a value
- [x] If return is `None`:
  - [x] Do **NOT** require `:rtype:`
  - [x] Do **NOT** add `:rtype: None`
- [x] Define how generators/iterators should be documented (`Iterator[T]`, `Generator[T, None, None]`, etc.)

---

## Phase 3 — Tooling design: can `repo_lint` enforce this

### 3.1 Evaluate existing `repo_lint` Python runner

- [x] Locate where Python rules run (runner + config).
- [x] Determine whether the existing pipeline can host a new checker stage:
  - [x] “type annotations checker” stage in `check --ci`
  - [x] optional “fix” mode support (later)

### 3.2 Prefer existing linters where possible (reduce custom code)

- [x] Use Ruff rules for function annotations if feasible:
  - [x] enable annotation rules (e.g., flake8-annotations / `ANN*`) via ruff config
  - [x] explicitly require return annotations, including `-> None`
  - [x] Optional type syntax policy (max compatibility):
    - [x] `Optional[T]` is preferred
    - [x] `T | None` is allowed but not preferred (avoid churn unless touching code)
- [x] Evaluate docstring tooling for `:rtype:`:
  - [x] if ruff cannot enforce it: introduce a dedicated checker (custom or a docstring tool)
  - [x] ensure it can run in CI and locally consistently

### 3.3 Implement missing enforcement in `repo_lint` (if needed)

**Status:** DEFERRED - Will implement after 3.4, 3.5, 3.6 complete

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

**Note:** Investigation complete - Ruff ANN* handles function annotations but NOT module-level/class attribute
annotations. Custom checker needed for PEP 526 scope.

---

### 3.4 Docstring validation consolidation (MANDATORY)

We currently have a docstring validation system implemented via `scripts/validate_docstrings.py` and its related modules. This issue MUST evaluate how `repo_lint` uses that script today, then migrate that logic into the `repo_lint` package so that docstring enforcement is **first-class and internal**, not an external script dependency.

#### 3.4.1 Current state analysis (MANDATORY)

- [x] Locate and review:
  - [x] `scripts/validate_docstrings.py`
  - [x] any Python modules it imports from / depends on (submodules/packages dedicated to docstring validation)
- [x] Identify and document how `repo_lint` uses this functionality today:
  - [x] Is it invoked as a subprocess? Imported as a module? Reimplemented partially?
  - [x] Which runner(s) call it (Python runner only, or shared docstring checks across languages)?
  - [x] Where configuration lives (CLI args, config files, hard-coded defaults)
- [x] Produce a concise mapping in the issue journal:
  - [x] “Current entrypoints” → “What rules are enforced” → “Where results are reported”

#### 3.4.2 Design: internalize docstring validation into `repo_lint` (MANDATORY)

- [x] Create an internal `repo_lint` module that owns docstring validation logic (example location):
  - [x] `tools/repo_lint/docstrings/` (or equivalent)
- [x] Refactor the existing validator implementation so `repo_lint` can call it directly (no subprocess).
- [x] Ensure the internal API supports:
  - [x] running checks during `repo-lint check --ci`
  - [x] stable machine-readable results (suitable for CI failure reports)
  - [x] future extensibility to enforce additional fields (like `:rtype:`)

#### 3.4.3 Migration plan (NO BREAKAGE)

- [x] Update `repo_lint` to use the new internal module.
- [x] Keep `scripts/validate_docstrings.py` as a thin compatibility wrapper initially (optional but recommended):
  - [x] it should import/call the internal `repo_lint` implementation
  - [x] it must remain behaviorally equivalent (same exit codes, same core checks)
- [x] Remove any `repo_lint` runtime dependency on `scripts/validate_docstrings.py`.
- [x] If legacy modules exist solely to support the old script (and are no longer needed after migration), remove them.

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

**Status:** Core migration COMPLETE (3.4.1-3.4.3 done). All 6 language runners use internal module. Comprehensive unit tests (3.4.4) deferred as future work - basic integration testing complete via `repo-lint check --ci`.

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

### 3.7 Reduce overly-broad exception handling (MANDATORY)

We need to identify and reduce occurrences of overly-broad exception handling (especially `except Exception as e:`) to improve correctness, debuggability, and avoid swallowing real failures.

#### 3.7.1 Repo-wide inventory (MANDATORY)

- [ ] Use `rg` (ripgrep) to locate broad exception handlers across the repo:
  - [ ] `except Exception as e:`
  - [ ] `except Exception:`
  - [ ] bare `except:` (if any)
- [ ] Produce counts by category and a list of exact file paths.
- [ ] Classify each finding by context:
  - [ ] CLI boundary / user-facing error handling
  - [ ] tooling wrappers calling subprocesses
  - [ ] library code paths
  - [ ] tests/fixtures

**Deliverable:** Add a section to `{ISSUE_NUMBER}-summary.md` with counts + a table of findings (path, category, reason).

#### 3.7.2 Define the policy (MANDATORY)

- [ ] Define acceptable vs unacceptable broad exception usage:
  - [ ] Acceptable: CLI boundary where we convert exceptions into a clean error message + non-zero exit
  - [ ] Unacceptable: library code swallowing exceptions without re-raising or without narrowing the exception type
- [ ] Define minimum required behavior when catching exceptions:
  - [ ] replace broad `Exception` with built-in exception classes where possible
  - [ ] create custom exception types where a domain-specific error improves clarity
  - [ ] always include actionable context in the error message (file/tool/action)
  - [ ] preserve the original exception via exception chaining (`raise ... from e`) when re-raising

**Deliverable:** Add this policy to `docs/contributing/python-typing-policy.md` or a new canonical doc if more appropriate (must be linked from contributing docs).

#### 3.7.3 Implementation plan (MANDATORY)

- [ ] For each broad exception site, decide one of:
  - [ ] Narrow to an appropriate built-in exception type(s)
  - [ ] Introduce a custom exception class (add to a canonical module, e.g. `tools/repo_lint/exceptions.py` or equivalent)
  - [ ] Keep broad catch ONLY if it’s a CLI boundary, and document why
- [ ] Update code to:
  - [ ] narrow exceptions
  - [ ] add `raise ... from e` where re-raising
  - [ ] ensure exit codes remain correct and consistent

#### 3.7.4 EXTREMELY COMPREHENSIVE tests (MANDATORY, NO SHORTCUTS)

- [ ] Unit tests that validate exception behavior:
  - [ ] expected exception types are raised for library code
  - [ ] CLI boundary catches produce correct user message + non-zero exit
  - [ ] exception chaining is preserved when intended
- [ ] Regression tests:
  - [ ] add a regression test for every bug found while tightening exception handling

**Deliverable:** Broad exception handling is reduced repo-wide and remaining uses are intentional, documented, and
tested.

### 3.8 Rich-powered logging (MANDATORY)

We want consistent, high-signal logging across the repo with Rich formatting where it makes sense, without breaking CI
logs or artifact readability.

#### 3.8.1 Current state assessment (MANDATORY)

- [ ] Inventory current logging patterns in Python code:
  - [ ] direct `print()` usage
  - [ ] `logging` module usage
  - [ ] Rich console output usage (if any)
- [ ] Identify where structured logging is most valuable:
  - [ ] repo-lint runner orchestration
  - [ ] subprocess execution wrappers
  - [ ] CI failure report generation

**Deliverable:** Add a section to `{ISSUE_NUMBER}-summary.md` describing current logging patterns and where to standardize.

#### 3.8.2 Implement a shared logger wrapper (MANDATORY)

- [ ] Create a shared logger utility that integrates Rich with Python `logging`:
  - [ ] Use RichHandler for pretty logs when attached to a TTY
  - [ ] Automatically fall back to plain logging in CI / non-TTY contexts
  - [ ] Provide consistent log levels and formatting
  - [ ] Support a `--verbose` / `--quiet` style toggle where applicable
- [ ] Ensure logs do NOT inject ANSI escape sequences into persisted artifacts unless explicitly intended.

**Deliverable:** A canonical logging module (e.g., `tools/repo_lint/logging_utils.py` or repo-equivalent) used by repo-lint and other Python tooling.

#### 3.8.3 Adopt the logger across repo-lint (MANDATORY)

- [ ] Replace ad-hoc `print()` statements with logger calls where appropriate.
- [ ] Ensure parallel execution (if enabled) still produces deterministic, readable output.
- [ ] Ensure CI output remains readable and artifact files remain ANSI-clean.

#### 3.8.4 EXTREMELY COMPREHENSIVE tests (MANDATORY, NO SHORTCUTS)

- [ ] Unit tests for logging behavior:
  - [ ] TTY vs non-TTY formatting differences
  - [ ] log level filtering (quiet/verbose)
  - [ ] no ANSI codes in failure report artifacts
- [ ] Integration tests:
  - [ ] repo-lint check --ci produces stable logs + stable artifact outputs

**Deliverable:** Logging is “fancy” interactively, stable in CI, and consistent repo-wide.

## Phase 4 — Autofix strategy (COMPLETE ✅)

### 4.1 Add non-destructive autofix where safe

- [x] Autofix candidates (safe-ish):
  - [x] add `-> None` where function has no return statements
  - [x] add missing return annotation where trivially inferrable (optional)
  - [x] add `:rtype:` for obvious simple returns (optional)
- [x] Any non-trivial type inference should be **suggested**, not auto-applied.

### 4.2 “Bulk migration” PR plan

- [x] Create a dedicated PR that:
  - [x] applies mechanical changes repo-wide
  - [x] keeps commits small (per directory / per module)
  - [x] keeps CI green after each commit

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

---

## Notes / Guardrails

- Enforce in **check** mode first; keep **fix** mode conservative.
- Avoid “clever inference” in automated tooling; prefer deterministic rules and human review for complex typing.
- Keep tests/fixtures policy explicit (some fixtures intentionally violate rules; they must be scoped and documented).

- Optional: If progress reporting is added for long-running checks, use **Rich progress** (not tqdm).
  - Keep it **off by default**; enable only when running interactively (TTY).
  - In CI, prefer stable summaries over progress bars to avoid log spam.

---
