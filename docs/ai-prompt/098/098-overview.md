# EPIC: Repo Cleanup Follow‑Ups — Phased Fix Plan (Post-Restructure)

This issue tracks the remaining callouts, recommendations, and nits identified after the initial repo restructure. The work is intentionally phased to keep risk low and ensure CI remains green throughout.

## Global Rules (Apply to every Phase)
- Use `git mv` for renames/moves to preserve history.
- Install and use `rg` (ripgrep) for repo searches **instead of** `grep`/`rgrep`.
  - Treat `rg` as the default search tool in all instructions, scripts, and debugging steps.
  - Only use `grep` if a specific environment cannot install ripgrep; document the reason when you do.
- Before **every commit**, run **all** repo linters locally and ensure they pass:
  - Python linters
  - Bash linters
  - Perl linters
  - PowerShell linters
  - Rust linters
  - YAML/Markdown/workflow linters (where configured)
- Before **every commit**, run `scripts/validate_docstrings.py` (or the repo’s docstring validator entrypoint) and ensure **all docstring validations pass**.
- Before **every commit**, run the **smallest relevant test suites** for the files you changed (unit tests + wrapper tests + conformance where impacted) and ensure they pass.
- Do not commit until all required linters and test runners are installed locally and all checks pass.
  - If a linter/test runner is missing, install it (using the repo’s documented setup steps) before proceeding.
- Install/build the Rust binary before running wrapper/conformance test suites, since they depend on it.
  - Use the repo’s documented build/install command for the Rust tool (or `cargo build`/`cargo install` as appropriate).
- After each **Item**:
  - Search for old paths/names and update references.
  - Run the smallest relevant test set.
- After each **Phase**:
  - Run **full test matrix** (Rust + wrappers + conformance).
  - Ensure **CI is green** before proceeding.
- Prefer multiple small PRs per Phase if it improves reviewability.

---

## Phase 0 — Preflight & Guardrails (Stabilize the ground you’re standing on)

### Item 0.1 — Create tracking + baseline
- [x] **Sub‑Item 0.1.1:** Create branch `refactor/followups-post-restructure`
- [x] **Sub‑Item 0.1.2:** Record current CI run links + status in the PR/issue description
- [x] **Sub‑Item 0.1.3:** Tag baseline (optional): `post-restructure-baseline-YYYYMMDD`

### Item 0.2 — Add/confirm reference auditing helpers
- [x] **Sub‑Item 0.2.1:** Ensure `scripts/verify-repo-references.sh` exists and runs locally
- [x] **Sub‑Item 0.2.2:** Add “obsolete path tokens” list to the helper script (or a config file), including:
  - `documents/`
  - `RFC-Shared-Agent-Scaffolding-Example/`
  - any known pre-move doc paths
- [x] **Sub‑Item 0.2.3:** Add a CI job (or reuse existing) to run the reference checker on PRs

**Phase 0 Success Criteria**
- ✅ Reference helper exists and runs
- ✅ Baseline CI known and documented
- ✅ No structure changes yet

---

## Phase 1 — Documentation Hygiene & Entry Points (Reduce confusion, improve discoverability)

### Item 1.1 — Fix `wrappers/README.md` mismatch (High)
**Problem:** `wrappers/README.md` currently reads like AI-agent methodology instructions (sharding CLAUDE / `.docs/agent`) instead of documenting wrappers.
- [x] **Sub‑Item 1.1.1:** Decide: **Move** vs **Rewrite**
  - Move the AI-agent content under `docs/history/ai-agent-guidelines/` (preferred)
  - Or rewrite `wrappers/README.md` to be wrappers-focused and relocate the old content
- [x] **Sub‑Item 1.1.2:** If moving: `git mv wrappers/README.md docs/history/ai-agent-guidelines/wrappers-readme-legacy.md`
- [x] **Sub‑Item 1.1.3:** Create/replace `wrappers/README.md` with:
  - what wrappers are
  - how they map to `safe-run` / `safe-check` / `safe-archive`
  - how to run wrapper tests
  - how wrappers locate the Rust binary (if applicable)
- [x] **Sub‑Item 1.1.4:** Update any links in docs pointing to wrappers README

### Item 1.2 — Standardize wrapper test docs naming (Medium)
**Problem:** inconsistent naming (`readme-tests.md` vs `README.md` vs `testing.md`).
- [x] **Sub‑Item 1.2.1:** Pick one convention:
  - Option A (recommended): `README.md` inside each wrapper language folder
  - Option B: `testing.md` across languages
- [x] **Sub‑Item 1.2.2:** Apply consistently via `git mv` and merge content as needed
- [x] **Sub‑Item 1.2.3:** Update internal references + docs index links
- [x] **Sub‑Item 1.2.4:** Verify GitHub folder rendering is clean and consistent

### Item 1.3 — Add root-level contributor entry point (Medium)
**Problem:** GitHub surfaces root `CONTRIBUTING.md` automatically; currently guidelines live under docs.
- [x] **Sub‑Item 1.3.1:** Add `CONTRIBUTING.md` at repository root
- [x] **Sub‑Item 1.3.2:** Make it an entry point that links to:
  - `docs/contributing/contributing-guide.md`
  - `docs/contributing/docstring-contracts/`
  - `docs/testing/` and CI guidance
- [x] **Sub‑Item 1.3.3:** Ensure docs index and root README link to it

### Item 1.4 — Clarify `docs/history/` sprawl (Low/Medium)
**Problem:** history is huge; readers may drown.
- [x] **Sub‑Item 1.4.1:** Add `docs/history/README.md` as an index of major history clusters (epics, PRs, milestones)
- [x] **Sub‑Item 1.4.2:** Update `docs/README.md` to link to history index instead of listing every file
- [x] **Sub‑Item 1.4.3:** Optionally group history into subfolders (e.g., `docs/history/epics/`, `docs/history/prs/`, `docs/history/milestones/`) using `git mv`

**Phase 1 Success Criteria**
- ✅ Wrappers README accurately describes wrappers
- ✅ Wrapper test docs are consistent and discoverable
- ✅ CONTRIBUTING entry point exists at root
- ✅ Docs navigation improved without breaking links

---

## Phase 2 — Wrappers Path Simplification (Kill redundant nesting, keep behavior identical)

### Item 2.1 — Remove redundant `wrappers/scripts/<lang>/scripts/` nesting (High)
**Problem:** current wrappers paths are overly nested and confusing.
- [x] **Sub‑Item 2.1.1:** Define target layout (recommended):
  - `wrappers/<lang>/`  
    - scripts at top-level **OR** in `scripts/`
    - tests in `tests/`
- [x] **Sub‑Item 2.1.2:** Move language folders up one level:
  - `git mv wrappers/scripts/bash wrappers/bash` (repeat for perl/powershell/python3)
- [x] **Sub‑Item 2.1.3:** If double `scripts/` remains inside each language folder, flatten it:
  - `git mv wrappers/bash/scripts/* wrappers/bash/`
  - keep `wrappers/bash/tests/` (or `test/`) as-is
- [x] **Sub‑Item 2.1.4:** Update all references:
  - GitHub workflows
  - conformance harness calls
  - docs links
  - any helper scripts that enumerate wrapper paths
- [x] **Sub‑Item 2.1.5:** Run wrapper test suites per language locally

### Item 2.2 — Ensure conformance tooling still finds wrappers (High)
- [x] **Sub‑Item 2.2.1:** Update any wrapper discovery logic docs (`docs/architecture/wrapper-discovery.md` if present)
- [x] **Sub‑Item 2.2.2:** Update conformance driver scripts to new locations
- [x] **Sub‑Item 2.2.3:** Run full conformance against `conformance/vectors.json`

### Item 2.3 — Keep CI path expectations accurate (High)
- [x] **Sub‑Item 2.3.1:** Update `.github/workflows/*` to point at new wrapper paths
- [x] **Sub‑Item 2.3.2:** Update any repository structure validation scripts
- [x] **Sub‑Item 2.3.3:** CI must pass: lint + tests + conformance

**Phase 2 Success Criteria**
- ✅ Wrapper paths are simplified
- ✅ No behavior changes
- ✅ CI and conformance remain green

---

## Phase 3 — Clarify/Document Build Artifact Directory (`dist/`) (Low/Medium)

### Item 3.1 — Decide whether `dist/` is a committed directory (Medium)
**Problem:** empty or unclear `dist/` can confuse contributors.
- [x] **Sub‑Item 3.1.1:** Determine usage:
  - CI artifact staging only (recommended: do not commit artifacts)
  - Committed release bundles (not recommended for most repos)
- [x] **Sub‑Item 3.1.2:** If CI-only:
  - add `.gitignore` rules if necessary
  - ensure workflows create required dist paths during builds
- [x] **Sub‑Item 3.1.3:** Add `dist/README.md` explaining:
  - what goes there (if anything)
  - who/what creates it (CI/local)
  - whether it should be committed

**Phase 3 Success Criteria**
- ✅ `dist/` has a clearly documented purpose (or is removed if truly unnecessary)
- ✅ CI does not rely on committed build outputs

---

## Phase 4 — Script & Code Casing Standardization (Dedicated Phase, High Risk / High Coordination)

> This phase intentionally stands alone because it touches:
> - file names
> - symbols inside scripts (functions/variables)
> - docs + examples
> - GitHub Actions enforcement policy
> - end-to-end tests and conformance

### Phase 4 Decisions (Locked)
- **File naming policy**
  - Script files follow their respective language naming standards (not a single repo-wide filename rule).
  - Non-script files (docs, configs, general repo files) use **kebab-case** by default.
- **Python**
  - Filenames/modules: `snake_case.py`
  - Functions/variables: `snake_case`
- **PowerShell**
  - Script filenames: `PascalCase.ps1` (Option A)
  - Functions: `PascalCase`
  - Variables: allow current conventions; add an eventual TODO to enforce variable-case. For now: **warnings** only.
- **Bash**
  - Constants/env/exported vars: `UPPER_SNAKE_CASE`
  - Local vars: `lower_snake_case`
  - Enforce obvious violations only.
- **CI enforcement rollout**
  - Use a warn/gradual rollout in Phase 4.
  - Add **Phase 4.5** to convert warnings to passing enforcement, one language per item.
- **Source of truth**
  - Maintain a single canonical doc: `docs/contributing/naming-and-style.md`

### Item 4.1 — Define the standards (High)
- [x] **Sub‑Item 4.1.1:** Create/confirm a single standards doc:
  - `docs/contributing/naming-and-style.md`
- [x] **Sub‑Item 4.1.2:** Lock the rules (examples below; adjust to repo needs):
  - **Non-script files (docs/config/general):** kebab-case by default
  - **Python scripts/modules:** `snake_case.py`; functions/vars `snake_case`
  - **PowerShell scripts:** `PascalCase.ps1`; functions `PascalCase` (variables: warn-only for now)
  - **Bash scripts:** script filenames follow shell conventions; vars: `UPPER_SNAKE_CASE` for constants/env, `lower_snake_case` for locals
  - **Perl scripts:** consistent Perl conventions; choose and document (warn-first, then enforce)
  - **Rust:** standard Rust naming (snake_case for fns/modules; CamelCase for types)
- [x] **Sub‑Item 4.1.3:** Decide how strict enforcement will be (lint vs “warn-only” vs “fail CI”)

### Item 4.2 — Inventory current casing deviations (High)
- [x] **Sub‑Item 4.2.1:** Generate a report of file names that violate the chosen policy
- [x] **Sub‑Item 4.2.2:** Generate a report of internal symbol deviations (where feasible)
  - Python: `ruff`/`flake8` naming plugins (if desired)
  - PowerShell: PSScriptAnalyzer rules
  - Bash: shellcheck + optional custom grep rules
- [x] **Sub‑Item 4.2.3:** Attach the reports to the PR (or store in `docs/history/`)

### Item 4.3 — Rename files (High)
- [x] **Sub‑Item 4.3.1:** Apply file renames via `git mv` in small batches per language
- [x] **Sub‑Item 4.3.2:** After each batch:
  - update references in code/docs/workflows
  - run the relevant wrapper tests
- [x] **Sub‑Item 4.3.3:** Update any “structure validation” scripts with the new naming rules

### Item 4.4 — Update internal symbol casing (Medium/High)
- [x] **Sub‑Item 4.4.1:** Python:
  - rename functions/vars to snake_case
  - update imports and call sites
  - run unit tests + wrapper tests
- [x] **Sub‑Item 4.4.2:** PowerShell:
  - rename functions to PascalCase
  - update references across scripts/tests
  - run PSScriptAnalyzer + tests
- [x] **Sub‑Item 4.4.3:** Bash:
  - apply chosen convention consistently
  - run shellcheck + tests
- [x] **Sub‑Item 4.4.4:** Perl:
  - normalize as feasible without unnecessary churn
  - run Perl tests + critic if enforced

### Item 4.5 — Update documentation and examples (High)
- [x] **Sub‑Item 4.5.1:** Update any code blocks in docs that reference renamed scripts/functions
- [x] **Sub‑Item 4.5.2:** Update README and docs indexes if any paths changed

### Item 4.6 — Update CI enforcement policy (High)
- [x] **Sub‑Item 4.6.1:** Modify GitHub Actions workflows to enforce the *new* policy (not the old one)
- [x] **Sub‑Item 4.6.2:** Ensure the enforcement is consistent across languages:
  - use linters where available
  - use custom scripts only where necessary
- [x] **Sub‑Item 4.6.3:** Add a “naming validation” job that fails fast with actionable output
- [x] **Sub‑Item 4.6.4:** Set enforcement to warn/no-new-violations during Phase 4; defer strict pass/fail conversion to Phase 4.5.

### Item 4.7 — Full verification (High)
- [x] **Sub‑Item 4.7.1:** Run full Rust test suite
- [x] **Sub‑Item 4.7.2:** Run all wrapper tests (bash/perl/powershell/python3)
- [x] **Sub‑Item 4.7.3:** Run conformance suite against vectors
- [x] **Sub‑Item 4.7.4:** CI must pass on PR

**Phase 4 Success Criteria**
- ✅ All casing rules documented and enforced
- ✅ All file names and internal symbols comply
- ✅ All references updated (docs, scripts, workflows)
- ✅ CI green + conformance green

## Phase 4.5 — CI Enforcement Conversion (One language per item)

> Goal: Convert Phase 4’s warning/rollout state into fully passing enforcement, one language at a time, without breaking CI.

### Item 4.5.3 — Python enforcement pass (High)
- [x] **Sub‑Item 4.5.3.1:** Turn Python naming checks from warn/no-new to hard fail.
- [x] **Sub‑Item 4.5.3.2:** Fix all remaining Python naming violations (files + symbols) until CI passes.

### Item 4.5.4 — PowerShell enforcement pass (High)
- [x] **Sub‑Item 4.5.4.1:** Turn PowerShell naming checks from warn/no-new to hard fail (functions + filenames).
- [x] **Sub‑Item 4.5.4.2:** Keep variable-case as warnings for now; track a follow-up to enforce later.
- [x] **Sub‑Item 4.5.4.3:** Fix all remaining PowerShell naming violations until CI passes.

### Item 4.5.5 — Bash enforcement pass (High)
- [x] **Sub‑Item 4.5.5.1:** Turn Bash naming checks from warn/no-new to hard fail for obvious violations.
- [x] **Sub‑Item 4.5.5.2:** Fix any remaining obvious violations until CI passes.

### Item 4.5.6 — Perl enforcement pass (High)
- [x] **Sub‑Item 4.5.6.1:** Choose and document Perl naming conventions in `docs/contributing/naming-and-style.md`.
- [x] **Sub‑Item 4.5.6.2:** Implement CI checks as warn/no-new first, then convert to hard fail once clean.
- [x] **Sub‑Item 4.5.6.3:** Fix Perl naming violations until CI passes.

**Phase 4.5 Success Criteria**
- ✅ Each language is converted from warn/rollout to passing enforcement without breaking CI
- ✅ Python/PowerShell/Bash naming enforcement is fully passing
- ✅ PowerShell variable-case remains warn-only with a tracked TODO
- ✅ Perl conventions are documented and enforced once clean

---

## Phase 5 — Wrapper Test Runner Parity Across Languages (Add language-native run-tests equivalents)

> Goal: Each wrapper language directory gets a first-class, language-native test runner that is functionally equivalent to the existing Bash `run-tests.sh` used for wrappers. These are **in addition to** the current Bash `run-tests.sh` scripts.

### Phase 5 Decisions (Locked)
- **Equivalence contract:** Strict parity with `run-tests.sh` (behavior, exit codes, stdout/stderr conventions, and CLI flags or a documented 1:1 mapping).
- **Implementation approach:** Start with language-native runners as thin wrappers around the existing Bash `run-tests.sh` to minimize drift.
  - Add a TODO to optionally migrate to fully native implementations later if there is a strong reason.
- **Runner placement:** Place language-native runners at `wrappers/<lang>/` (top-level) to match the flattened wrapper layout.
- **Invocation requirements:** Each runner must work when executed from:
  - its wrapper directory, and
  - repo root (no required `cd`).
- **CI strategy:** Run both Bash `run-tests.sh` and the language-native runner initially.
  - Add a TODO to optionally downgrade the duplicate Bash runner to scheduled/nightly if CI runtime becomes excessive.

### Item 5.1 — Define the contract for “equivalent” (High)
- [x] **Sub-Item 5.1.1:** Document what `run-tests.sh` does today (inputs, outputs, exit codes, required tools, environment variables).
- [x] **Sub-Item 5.1.2:** Define parity requirements for all runners:
  - same default behavior
  - same CLI flags (or documented mapping)
  - same exit codes for pass/fail/error
  - same stdout/stderr conventions (so CI logs remain consistent)
  - same working-directory assumptions
- [x] **Sub-Item 5.1.3:** Decide naming conventions (recommended):
  - Python: `run_tests.py`
  - PowerShell: `RunTests.ps1`
  - Perl: `run_tests.pl`
    - Perl runner filenames must be `snake_case`; update any existing kebab-case Perl runner references in docs/scripts to match.

- [x] **Sub-Item 5.1.4:** Add a `future-work.md` entry: consider migrating thin wrappers to fully native test logic later (only if needed).

### Item 5.2 — Implement language-native runners (High)
- [x] **Sub-Item 5.2.1:** Python wrapper: add `wrappers/python3/run_tests.py` as the functional equivalent of `wrappers/python3/run-tests.sh`.
- [x] **Sub-Item 5.2.2:** PowerShell wrapper: add `wrappers/powershell/RunTests.ps1` as the functional equivalent of `wrappers/powershell/run-tests.sh`.
- [x] **Sub-Item 5.2.3:** Perl wrapper: add `wrappers/perl/run_tests.pl` as the functional equivalent of `wrappers/perl/run-tests.sh` (snake_case Perl runner).
- [x] **Sub-Item 5.2.4:** Ensure each runner can be executed directly from its wrapper directory and from repo root via documented commands.

### Item 5.3 — Lint, test, and CI integration (High)
- [x] **Sub-Item 5.3.1:** Add/confirm lint rules for each new runner file type in CI (Python, PowerShell, Perl).
- [x] **Sub-Item 5.3.2:** Update wrapper docs to include language-native runner usage examples.
- [x] **Sub-Item 5.3.3:** Update CI workflows to run each language-native runner (in addition to existing Bash runner) where appropriate.
- [x] **Sub-Item 5.3.4:** Verify end-to-end wrapper parity by running all wrapper test suites (bash/perl/powershell/python3) and conformance.

- [x] **Sub-Item 5.3.5:** Add a `future-work.md` entry: if CI becomes too slow, move the duplicate Bash-runner execution to scheduled/nightly workflows while keeping language-native runners on PR CI.

**Phase 5 Success Criteria**
- ✅ Each wrapper directory contains a language-native runner (Python/PowerShell/Perl) that matches `run-tests.sh` behavior
- ✅ All new runner files pass their respective lint workflows
- ✅ Wrapper tests + conformance remain green in CI

---

## Phase 5.5 — Docstring/Documentation Contract Expansion (All languages, all symbols)

### Item 5.5.0 — Preflight: Perl filename + reference normalization (High)

> Goal: Ensure all Perl script filenames follow `snake_case` and that all documentation and references point at the correct names **before** expanding docstring enforcement.

- [ ] **Sub-Item 5.5.0.1:** Inventory Perl files and identify any that are not `snake_case` (e.g., kebab-case, mixedCase).
- [ ] **Sub-Item 5.5.0.2:** Rename non-conforming Perl files to `snake_case` using `git mv`.
- [ ] **Sub-Item 5.5.0.3:** Update all references to renamed Perl files across the repo (scripts, CI workflows, and docs).
  - Use `rg` to find kebab-case references (e.g., `run-tests.pl`) and update them to snake_case (e.g., `run_tests.pl`).
- [ ] **Sub-Item 5.5.0.4:** Re-run the smallest relevant Perl test/lint set (and wrapper/conformance suites if impacted) to ensure nothing broke.

> Goal: Expand the existing docstring validation tooling so it enforces documentation standards not only at the file/module level, but also for key **symbols** (classes, functions, methods, and language equivalents) across **Python, Bash, Perl, PowerShell, and Rust**. Then run the expanded validator across the repository and fix all violations until CI is green.

### Item 5.5.1 — Define the cross-language symbol documentation contract (High)
- [x] **Sub-Item 5.5.1.1:** Update/extend the canonical standard in `docs/contributing/naming-and-style.md` (or create `docs/contributing/docstring-symbol-contracts.md` if you want separation) to explicitly define required doc blocks for:
  - Classes
  - Functions
  - Methods
  - (Language equivalents)
- [x] **Sub-Item 5.5.1.2:** For each language, define **what counts as a docstring/docblock**, and where it must appear.
  - **Python:** class/function/method docstrings (`"""..."""`) with required sections/keywords per repo contract.
  - **Bash:** function docblocks as comment blocks immediately above function definitions; define minimum required fields.
  - **Perl:** POD (`=head1`, `=head2`, etc.) or comment-based doc blocks (choose one and standardize); define requirements for subs/packages.
  - **PowerShell:** comment-based help (`<# .SYNOPSIS ... #>`) for functions and scripts; define requirements for functions and exported commands.
  - **Rust:** `///` (outer) and `//!` (module) docs; define requirements for structs/enums/traits/functions/public items.
- [x] **Sub-Item 5.5.1.3:** Decide scope of enforcement:
  - Minimum: public/exposed entrypoints only
  - Recommended: all exported/public symbols + all wrapper entrypoints
  - Optional: enforce everything (including private helpers) after initial cleanup
- [x] **Sub-Item 5.5.1.4:** Document severity levels and CI behavior:
  - Phase 5.5 can start with warn/no-new-violations if needed
  - End of Phase 5.5 must be hard-fail enforced and passing

### Item 5.5.2 — Expand the validator implementation (High)
- [x] **Sub-Item 5.5.2.1:** Identify the current validator script location (the existing docstring validation script) and add a clear architecture section to its header comment/docstring explaining:
  - how it discovers files
  - how it classifies languages
  - how it detects doc blocks
  - how it reports failures

- [ ] **Sub-Item 5.5.2.2:** Split the docstring validator into per-language Python validators (High)
  - **Goal:** Keep each language’s logic isolated and testable (Python-only validator module, Bash-only validator module, etc.), while retaining a single CLI entrypoint for CI.
  - **Approach:**
    - Keep `scripts/validate_docstrings.py` as the CLI entrypoint (argument parsing, file discovery, and unified reporting).
    - Move language-specific validation logic into separate Python modules (one module per language), and keep shared utilities in a small common module.
    - Recommended layout (adjust if the repo already has a preferred structure):
      - `scripts/docstring_validators/common.py` (shared helpers, `ValidationError`, base interfaces)
      - `scripts/docstring_validators/python_validator.py`
      - `scripts/docstring_validators/bash_validator.py`
      - `scripts/docstring_validators/perl_validator.py`
      - `scripts/docstring_validators/powershell_validator.py`
      - `scripts/docstring_validators/rust_validator.py`
      - `scripts/docstring_validators/__init__.py`
    - Ensure the entrypoint imports and dispatches to these modules without changing existing output formatting.
  - **Copilot Work Packet (Paste into Copilot as-is):**

```text
You are working in scripts/validate_docstrings.py and related validator modules.

Context:
- PythonValidator uses Python AST for symbol-level validation.
- BashValidator currently uses regex for function discovery.
- PerlValidator currently validates only file-level POD sections (no sub discovery).
- PowerShellValidator currently validates only a file-level comment-based help block (no function discovery).
- The module docstring currently CLAIMS Perl/PowerShell symbol discovery exists; that is currently untrue.

Core policy update (IMPORTANT):
- We do NOT skip private/internal symbols anymore.
  - Do NOT skip functions/classes/subs just because they start with "_" (Python/Bash) or any similar convention.
  - Enforce symbol-level doc requirements for ALL symbols in scope, with a minimal implementation aligned with the docstring contracts.
  - Exceptions must be explicit via existing pragma mechanisms (e.g., # noqa: D102/D103/D101 for Python, # noqa: FUNCTION for Bash, etc.), not implicit based on naming.

Task A — Modularize validators (required before adding new parsers):
1) Keep scripts/validate_docstrings.py as the single CLI entrypoint and reporter (no behavior/output changes).
2) Split language-specific logic into separate Python modules (one per language) and move shared helpers into a common module.
   - Use a package like scripts/docstring_validators/ with:
     - common.py (shared helpers, ValidationError, base interfaces)
     - python_validator.py
     - bash_validator.py
     - perl_validator.py
     - powershell_validator.py
     - rust_validator.py
   - Update imports/dispatch so validate_docstrings.py calls the correct validator module per file type.
   - Add/adjust unit tests to cover dispatch and ensure output format is unchanged.

Task B — Reconcile documentation vs behavior:
- Update the module-level docstring to accurately describe current behavior OR implement the missing behavior so the docstring is true.
- Prefer making behavior match the stated architecture if consistent with repository goals.

Task C — Implement structure-aware parsing for symbol discovery where appropriate:

Python:
- Keep using Python AST for symbol discovery.
- Update Python symbol validation so that private functions/classes are NOT auto-exempt.
- Enforce minimal requirements per our docstring contracts:
  - All functions/methods require a docstring unless explicitly exempted via pragma (# noqa: D102/D103).
  - All classes require a docstring unless explicitly exempted via pragma (# noqa: D101).
  - Keep the existing “require :param only when parameters exist (excluding self/cls)” logic.
  - Keep the existing “require :returns only when a return-with-value exists” logic.
- Do not change validation output formatting.

Bash:
- Replace regex-based function detection with bashlex AST parsing (no execution).
- Preserve the rule: every function must have a preceding comment docblock with a description (no skipping underscore-prefixed functions).
- Maintain pragma behavior (# noqa: FUNCTION) on the function definition line.

Perl:
- Add symbol-level validation for subroutines using PPI (Perl module).
- Because the validator is Python, invoke perl via subprocess and run a small embedded Perl script that uses PPI to parse the target file and output JSON listing subs and their line numbers.
- In Python, convert that JSON into ValidationError objects using the existing format.
- Enforce the repo’s Perl symbol doc contract for ALL subs.
- Do not execute any Perl code.

PowerShell:
- Add symbol-level validation for functions using PowerShell’s built-in AST parser.
- Invoke pwsh via subprocess; inside PowerShell use [System.Management.Automation.Language.Parser]::ParseInput to build the AST and output JSON of discovered functions and their line numbers.
- Enforce comment-based help presence for ALL functions per repo contract (or define the minimal rule consistent with our docs if the contract is currently only file-level).
- Do not execute functions; parse only.

Keep changes minimal and safe:
- Do NOT remove any existing functions/classes/methods.
- Do NOT change runtime behavior of scripts; validation-only.
- Do NOT change validation output format.
- Add unit tests for each new language parser path (at least one pass and one fail case).

CI readiness:
- If new dependencies are required (bashlex, pwsh availability, Perl PPI), update the workflow or docs accordingly.
- Keep CI deterministic.

Deliverables:
- Modular per-language validator modules + common helpers.
- Updated docs reflecting the actual mechanisms.
- New tests verifying symbol discovery paths and the “no skipping private symbols” policy.
```

- [ ] **Sub-Item 5.5.2.3:** Add language-specific symbol scanners:
  - **Python:** use `ast` parsing to detect module/class/function/method nodes and their docstrings; enforce required fields.
  - **Bash:** implement a conservative parser (regex + indentation/brace heuristics) that maps function names to immediate preceding comment blocks.
  - **Perl:** detect `package` / `sub` and associated POD/comment blocks using a conservative parser; prefer POD if present.
  - **PowerShell:** detect `function` blocks and comment-based help blocks immediately preceding; optionally use PSScriptAnalyzer outputs as supporting signals.
  - **Rust:** detect public items (`pub`) and rustdoc comments (`///`, `//!`); enforce minimum required text/sections.
- [ ] **Sub-Item 5.5.2.4:** Ensure the validator produces deterministic, CI-friendly output:
  - file path
  - symbol name (and kind: class/function/method/etc.)
  - rule violated
  - suggested fix format
- [ ] **Sub-Item 5.5.2.5:** Add a `--check` mode (fail on violations) and an optional `--report` mode (human-readable summary).
- [ ] **Sub-Item 5.5.2.6:** Add test coverage for the validator itself (fixtures per language) so future refactors don’t break it.

### Item 5.5.3 — CI integration (High)
- [ ] **Sub-Item 5.5.3.1:** Add/extend CI workflows so the expanded validator runs in the appropriate jobs (and in the correct order relative to lint).
- [ ] **Sub-Item 5.5.3.2:** Ensure failures link back to the canonical contract docs (print the path to the standard document in the failure output).
- [ ] **Sub-Item 5.5.3.3:** Confirm the validator respects repo-wide search rules (use `rg` for supporting searches where applicable) and ignores vendored/build directories.

### Item 5.5.4 — Repository-wide remediation pass (High)
- [ ] **Sub-Item 5.5.4.1:** Run the expanded validator across the entire repo and generate a baseline report.
- [ ] **Sub-Item 5.5.4.2:** Fix violations in a controlled order to keep PRs reviewable:
  - Rust (public APIs and modules)
  - Wrappers (Python/PowerShell/Perl/Bash)
  - Remaining scripts/tools
  - Docs/config examples that reference required doc formats
- [ ] **Sub-Item 5.5.4.3:** After each language batch, run:
  - that language’s lints
  - wrapper/conformance tests (after Rust binary is built)
  - full CI before moving on
- [ ] **Sub-Item 5.5.4.4:** Ensure every fix uses the repo’s documented docstring templates/contracts and does not invent new formats.

**Phase 5.5 Success Criteria**
- ✅ Docstring/symbol documentation requirements are explicitly documented for all supported languages
- ✅ The validator enforces module/file docs **and** symbol-level docs (classes/functions/methods/etc.) across Python/Bash/Perl/PowerShell/Rust
- ✅ The validator runs in CI and fails with actionable output
- ✅ All repository violations are fixed and CI remains green (lint + tests + conformance)

---

## Phase 6 — Final Polish & Long-Term Maintenance (Nits that prevent future drift)

### Item 6.1 — Rename “scripts/” (dev utilities) if desired (Low/Optional)
- [ ] **Sub‑Item 6.1.1:** Decide whether `scripts/` is ambiguous enough to justify churn; if yes, prefer renaming to `tools/` (unless the folder is truly CI-only, in which case consider `ci-scripts/`).
- [ ] **Sub‑Item 6.1.2:** `git mv scripts tools` (if chosen)
- [ ] **Sub‑Item 6.1.3:** Update workflows and docs accordingly

### Item 6.2 — Make docs index “start-here” clearer (Low)
- [ ] **Sub‑Item 6.2.1:** Add a short “Start Here” section to `docs/README.md`
- [ ] **Sub‑Item 6.2.2:** Ensure README links:
  - users → usage docs
  - contributors → CONTRIBUTING + docstring contracts
  - maintainers → architecture + testing

### Item 6.3 — Add “structure map” to root README (Low)
- [ ] **Sub‑Item 6.3.1:** Add a short tree + explanation:
  - `rust/` canonical tool
  - `wrappers/` language wrappers
  - `conformance/` test vectors
  - `docs/` documentation
  - `scripts/` or `tools/` dev utilities

- [ ] **Sub‑Item 6.3.2:** Add a `future-work.md` entry: consider adding a docs “Start Here” section organized by persona (User / Contributor / Maintainer) if navigation remains confusing.

**Phase 6 Success Criteria**
- ✅ Repo is self-explanatory to newcomers
- ✅ Maintenance burden reduced
- ✅ Less chance of future drift

---

## Reference Verification Checklist (Run after every Phase)
- [ ] `rg "documents/"` returns 0
- [ ] `rg "RFC-Shared-Agent-Scaffolding-Example"` returns 0
- [ ] `rg` for any old file names you renamed returns 0
- [ ] All Markdown links work (run link checker if available)
- [ ] All workflows updated for any moved/renamed paths
- [ ] Rust tests pass
- [ ] Wrapper tests pass (bash/perl/powershell/python3)
- [ ] Conformance tests pass
