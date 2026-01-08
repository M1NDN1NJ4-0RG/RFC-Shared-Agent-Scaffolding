# EPIC: Repository Restructure & Documentation Reorganization (RFC-Shared-Agent-Scaffolding)

**Goal:** Refactor the repository layout to a clean, scalable structure with consistent naming, consolidated
documentation, and updated references (docs links, scripts, workflows, tests) — **without breaking behavior** at any
point.

**Non negotiables:**

- Use `git mv` for all renames/moves to preserve history.
- After **every Phase**: all tests pass locally, and CI is green.
- After **every Item**: verify references (Markdown links, script paths, workflow paths, config includes) are updated.
- No “big bang” move. This must be incremental, verifiable, and rollback-friendly.

---

## Progress Checklist

- [x] **M0 — Preflight & Safety Nets (No structural changes yet)**
- [x] **M1 — Documentation Consolidation (No code path changes yet)**
- [x] **M2 — Wrapper Directory Refactor (Path changes, but behavior unchanged)**
- [x] **M3 — Naming & Consistency Sweep (Repo-wide standardization)**
- [x] **M4 — Documentation Merges & De-duplication (Reduce maintenance burden)**
- [ ] **M5 — Final Verification & “No Regrets” Pass**

---

## Scope Summary (What’s Changing)

### High-level structural changes

- Consolidate `documents/` into `docs/` (single documentation root).
- Move root-level historical/progress Markdown files (EPIC/PR/M#) into `docs/history/`.
- Rename `RFC-Shared-Agent-Scaffolding-Example/` to a clearer name (recommended: `wrappers/`), and separate **agent-methodology docs** out of the wrappers code tree into `docs/history/ai-agent-guidelines/` (or similarly named).
- Standardize naming:
  - lower-case
  - kebab-case
  - no underscores (unless a tool demands it)
- Add a documentation index and make `README.md` the canonical entry point with stable links.

### Key acceptance properties

- Same behavior of `safe-run` and `safe-archive`.
- Wrapper scripts still find and invoke the Rust binaries correctly.
- Conformance tests still run and validate behavior.
- CI workflows still find all scripts/tests after path changes.

---

## Definitions

- **Milestone**: a top-level delivery checkpoint (must be CI-green).
- **Phase**: a bounded set of changes in a Milestone (must be CI-green).
- **Item**: a specific change within a Phase (must be verifiable on its own).
- **Sub-Item**: discrete steps with explicit checks.

---

## Preflight Tooling Requirements (Before any moves)

> These items prevent “move files, forget references, break CI” chaos.

### M0 — Preflight & Safety Nets (No structural changes yet)

#### P0 — Baseline & Repo Snapshot

- [x] **Item 0.1 — Create a baseline branch**
  - [x] Sub-Item 0.1.1: Create new branch `refactor/repo-structure-v1`.
  - [x] Sub-Item 0.1.2: Tag current state (optional) `pre-restructure-<date>`.
  - [x] **Verify:** No uncommitted changes.

- [x] **Item 0.2 — Capture baseline CI status**
  - [x] Sub-Item 0.2.1: Run full CI locally if possible (or trigger CI run).
  - [x] Sub-Item 0.2.2: Save baseline results (link in PR description or an internal note).
  - [x] **Verify:** Current CI status is known (green or known red with documented reason).

#### P1 — Add Reference Validation Helpers (Optional but highly recommended)

- [x] **Item 1.1 — Add “Link Integrity” check (optional)**
  - [x] Sub-Item 1.1.1: Add a CI job that runs a markdown link checker (or a lightweight script).
  - [x] Sub-Item 1.1.2: Allowlist known external links if needed.
  - [x] **Verify:** The job passes on baseline.

- [x] **Item 1.2 — Add “Path Reference Search” helper script**
  - [x] Sub-Item 1.2.1: Create a script (e.g., `scripts/verify-repo-references.sh`) that:
    - [x] searches for old paths (e.g. `documents/`, `RFC-Shared-Agent-Scaffolding-Example/`)
    - [x] reports occurrences
  - [x] Sub-Item 1.2.2: Script exits non-zero if forbidden/obsolete paths exist after milestones.
  - [x] **Verify:** Script runs and reports expected baseline matches.

**Milestone M0 Exit Criteria**

- [x] CI still green
- [x] Baseline captured
- [x] Optional helper checks added (if implemented)

---

## M1 — Documentation Consolidation (No code path changes yet)

> Objective: move/rename docs safely and update links, without touching code/wrapper paths.

### P1 — Create `docs/` taxonomy and migrate `documents/`

- [x] **Item 1.1 — Create new docs structure**
  - [x] Sub-Item 1.1.1: Create:
    - [x] `docs/overview/`
    - [x] `docs/architecture/`
    - [x] `docs/usage/`
    - [x] `docs/testing/`
    - [x] `docs/contributing/`
    - [x] `docs/history/`
  - [x] Sub-Item 1.1.2: Add `docs/README.md` as an index (table of contents).

- [x] **Item 1.2 — Move `documents/*` into `docs/*`**
  - [x] Sub-Item 1.2.1: Identify each file’s category:
    - [x] Architecture/spec/requirements → `docs/architecture/`
    - [x] Test plans/evidence → `docs/testing/`
    - [x] Final summary/overview → `docs/overview/`
    - [x] Checklists → `docs/testing/` or `docs/contributing/` (depending on audience)
  - [x] Sub-Item 1.2.2: `git mv documents/... docs/<category>/...`
  - [x] Sub-Item 1.2.3: Delete `documents/` directory once empty.
  - [x] **Verify:** `rg "documents/"` returns **0** in repo after updates.

### P2 — Relocate root-level historical/progress Markdown into `docs/history/`

- [x] **Item 2.1 — Move EPIC/PR/M# logs**
  - [x] Sub-Item 2.1.1: `git mv EPIC-*.md docs/history/`
  - [x] Sub-Item 2.1.2: `git mv PR*.md docs/history/`
  - [x] Sub-Item 2.1.3: `git mv M*.md docs/history/` (or subset)
  - [x] Sub-Item 2.1.4: Keep only **canonical** docs at root (README, LICENSE, etc.)
  - [x] **Verify:** Root directory is clean; historical docs are in `docs/history/`.

- [x] **Item 2.2 — Standardize file naming (docs only, in this milestone)**
  - [x] Sub-Item 2.2.1: Convert moved historical doc filenames to lower kebab-case
    - [x] Example: `EPIC-33-VERIFICATION-SUMMARY.md` → `epic-33-verification-summary.md`
  - [x] Sub-Item 2.2.2: Convert “policy” docs too:
    - [x] `KNOWN-ISSUES.md` → `known-issues.md`
    - [x] `ALLOWED_DRIFT.md` → `allowed-drift.md`
  - [x] **Verify:** No duplicate names introduced; all links updated.

### P3 — Update documentation references

- [x] **Item 3.1 — Update README and doc links**
  - [x] Sub-Item 3.1.1: Update root `README.md` links to new docs paths.
  - [x] Sub-Item 3.1.2: Update internal Markdown links across `docs/`:
    - [x] run a link checker or scripted validation
  - [x] **Verify:** No broken relative links.

- [x] **Item 3.2 — Create stable entrypoints**
  - [x] Sub-Item 3.2.1: Ensure `docs/README.md` links to the main sections.
  - [x] Sub-Item 3.2.2: Ensure `docs/overview/` contains the high-level “start here” docs.
  - [x] **Verify:** All docs index pages link properly to the main sections.

**Milestone M1 Exit Criteria**

- [x] CI green
- [x] `documents/` removed
- [x] Root no longer contains “log spam” docs
- [x] All Markdown links updated and validated

---

## M2 — Wrapper Directory Refactor (Path changes, but behavior unchanged)

> Objective: rename and reshape wrapper folder, keep wrappers working, update tests and CI paths.

### P1 — Rename `RFC-Shared-Agent-Scaffolding-Example/` → `wrappers/`

- [x] **Item 1.1 — Move/rename folder**
  - [x] Sub-Item 1.1.1: `git mv RFC-Shared-Agent-Scaffolding-Example wrappers`
  - [x] Sub-Item 1.1.2: Ensure per-language subfolders remain intact (`bash/`, `perl/`, etc.)
  - [x] **Verify:** `rg "RFC-Shared-Agent-Scaffolding-Example"` returns **0** in repo.

- [x] **Item 1.2 — Update any hard-coded paths**
  - [x] Sub-Item 1.2.1: Search & update:
    - [x] scripts referencing old path
    - [x] tests referencing old path
    - [x] workflows referencing old path
    - [x] docs referencing old path
  - [x] **Verify:** Grep/ripgrep shows no old references.

### P2 — Extract agent-methodology docs out of wrapper code tree

- [x] **Item 2.1 — Move `.docs/` and `CLAUDE.md`**
  - [x] Sub-Item 2.1.1: `git mv wrappers/.docs docs/history/ai-agent-guidelines`
  - [x] Sub-Item 2.1.2: `git mv wrappers/CLAUDE.md docs/history/ai-agent-guidelines/claude.md`
  - [x] Sub-Item 2.1.3: Add a short README in `docs/history/ai-agent-guidelines/` explaining why it’s archived.
  - [x] **Verify:** No `.docs` remains inside `wrappers/`.

### P3 — Fix CI workflows & test harness paths

- [x] **Item 3.1 — Update GitHub Actions workflows**
  - [x] Sub-Item 3.1.1: Update any workflow steps that reference the old wrappers directory.
  - [x] Sub-Item 3.1.2: Ensure test invocation paths point at `wrappers/...`
  - [x] **Verify:** Workflows run successfully in CI.

- [x] **Item 3.2 — Update conformance harness and any path-aware scripts**
  - [x] Sub-Item 3.2.1: Search for assumptions about wrapper directory name.
  - [x] Sub-Item 3.2.2: Update accordingly.
  - [x] **Verify:** Conformance tests pass.

**Milestone M2 Exit Criteria**

- [x] CI green
- [x] Wrapper scripts still locate and run the Rust binaries
- [x] All tests (unit + conformance) pass

---

## M3 — Naming & Consistency Sweep (Repo-wide standardization)

> Objective: apply consistent naming conventions across remaining files/directories with controlled blast radius.

### P1 — Repo-wide kebab-case normalization (careful: CI + scripts)

- [x] **Item 1.1 — Identify remaining non-conforming names**
  - [x] Sub-Item 1.1.1: Enumerate files with uppercase, spaces, underscores.
  - [x] Sub-Item 1.1.2: Classify by risk:
    - [x] Low risk: docs
    - [x] Medium: tests
    - [x] High: scripts invoked by CI or referenced by name
  - [x] **Verify:** A list exists and is attached to PR description.

- [x] **Item 1.2 — Rename low-risk files first**
  - [x] Sub-Item 1.2.1: `git mv` docs and misc text files to kebab-case.
  - [x] Sub-Item 1.2.2: Update links.
  - [x] **Verify:** Link checks pass.

- [x] **Item 1.3 — Rename medium/high-risk files with explicit reference audits**
  - [x] Sub-Item 1.3.1: For each rename:
    - [x] Update all references in scripts, tests, workflows
    - [x] Run targeted test set
  - [x] Sub-Item 1.3.2: Run full CI per batch.
  - [x] **Verify:** No dangling references.

### P2 — Add/update “Contributing” and standards docs

- [x] **Item 2.1 — Add `docs/contributing/contributing-guide.md`**
  - [x] Sub-Item 2.1.1: Document:
    - [x] naming conventions (kebab-case)
    - [x] required checks
    - [x] how to run tests
    - [x] how to add new language wrappers
  - [x] **Verify:** README points to it.

- [x] **Item 2.2 — Relocate docstring contracts**
  - [x] Sub-Item 2.2.1: Ensure docstring contracts live under:
    - [x] `docs/contributing/docstring-contracts/`
  - [x] Sub-Item 2.2.2: Update any references from README and validation scripts.
  - [x] **Verify:** Docstring validation still finds contracts and passes.

**Milestone M3 Exit Criteria**

- [x] CI green
- [x] Naming consistent repo-wide
- [x] Contributing docs clearly describe conventions

---

## M4 — Documentation Merges & De-duplication (Reduce maintenance burden)

> Objective: reduce duplicated docs by consolidating into single sources of truth.

### P1 — Consolidate overlapping docs

- [x] **Item 1.1 — Future work + verification**
  - [x] Sub-Item 1.1.1: Merge verification content into `docs/contributing/future-work.md` (or `docs/overview/roadmap.md`)
  - [x] Sub-Item 1.1.2: Archive the old verification doc in `docs/history/`
  - [x] **Verify:** The “future work” document is authoritative and current.

- [x] **Item 1.2 — Epic 33/Rust docs**
  - [x] Sub-Item 1.2.1: Ensure `docs/architecture/rust-canonical-tool.md` is the canonical Rust design doc.
  - [x] Sub-Item 1.2.2: Move old checklists/summaries to `docs/history/epic-33/`
  - [x] **Verify:** README and docs index link to the canonical doc.

- [x] **Item 1.3 — Testing docs consolidation (optional)**
  - [x] Sub-Item 1.3.1: Combine conformance overview + vectors schema into one guide (if it reduces confusion).
  - [x] **Verify:** Conformance docs still reflect real behavior and test harness structure.

**Milestone M4 Exit Criteria**

- [x] CI green
- [x] Canonical docs exist per topic; duplicates archived

---

## M5 — Final Verification & “No Regrets” Pass

> Objective: prove that everything still works and that references are fully correct.

### P1 — Full repo integrity checks

- [x] **Item 1.1 — Reference verification**
  - [x] Sub-Item 1.1.1: `rg` search for obsolete paths:
    - [x] `documents/`
    - [x] `RFC-Shared-Agent-Scaffolding-Example/`
    - [x] old docs filenames
  - [x] Sub-Item 1.1.2: Ensure zero matches.
  - [x] **Verify:** 0 results for all obsolete tokens (only historical docs contain references, as expected).

- [x] **Item 1.2 — Behavior verification**
  - [x] Sub-Item 1.2.1: Run:
    - [x] Rust unit/integration tests (31 passed, 4 ignored)
    - [x] wrapper tests (bash: 23, perl: 46, python: 20): 89 tests passed
    - [x] conformance harness (passed)
  - [x] Sub-Item 1.2.2: Confirm wrapper scripts still invoke Rust binaries with expected behavior.
  - [x] **Verify:** All test suites pass (120+ tests total).

- [x] **Item 1.3 — CI validation**
  - [x] Sub-Item 1.3.1: Confirm all workflows still run.
  - [x] Sub-Item 1.3.2: Confirm any path-based actions still function (linting, docstring checks, naming checks).
  - [x] **Verify:** All linting checks passed via `python3 -m tools.repo_lint check --ci`.

### P2 — Documentation navigation verification

- [x] **Item 2.1 — Docs index & README navigation**
  - [x] Sub-Item 2.1.1: Confirm README → docs index → main sections all valid.
  - [x] Sub-Item 2.1.2: Confirm “start here” is obvious for:
    - [x] users (usage)
    - [x] contributors (contributing)
    - [x] maintainers (architecture/testing)
  - [x] **Verify:** A human can follow links without dead ends.

**Milestone M5 Exit Criteria**

- [x] CI green
- [x] All integrity checks pass
- [x] Docs navigation verified

---

## Reference Audit Checklist (Run after each Phase)

### A) Path references

- [ ] `rg "documents/"` returns 0 (after M1)
- [ ] `rg "RFC-Shared-Agent-Scaffolding-Example"` returns 0 (after M2)
- [ ] `rg` for any old filenames you renamed returns 0

### B) Scripts

- [ ] Any script with hard-coded relative paths updated
- [ ] Any script invoked by CI still exists at referenced location
- [ ] Wrapper binary discovery logic still works

### C) Workflows / CI

- [ ] `.github/workflows/*` updated for moved paths
- [ ] CI jobs still find the correct test directories
- [ ] Linting / docstring / naming workflows still pass

### D) Documentation links

- [ ] README links valid
- [ ] `docs/README.md` index links valid
- [ ] Cross-links inside docs valid

### E) Tests

- [ ] Rust tests pass
- [ ] Wrapper tests pass
- [ ] Conformance tests pass

---

## Deliverables

- One or more PRs implementing these milestones incrementally.
- Final merged PR results in:
  - Clean repository root
  - Organized `docs/` taxonomy
  - `wrappers/` replacing the confusing “Example” name
  - Standardized naming
  - Updated references everywhere
  - CI green at every step

---

## Notes for Copilot (Directive Language)

- Do not perform wide moves without simultaneously updating every reference.
- Every time you move/rename files:
  - search the repo for the old path/name
  - update references
  - run targeted tests
  - run full CI at milestone boundaries
- Prefer multiple smaller PRs if needed, but each must be independently green and reviewable.
- If any unexpected failures appear:
  - stop, diagnose, fix, and re-run checks before continuing to the next Item.
