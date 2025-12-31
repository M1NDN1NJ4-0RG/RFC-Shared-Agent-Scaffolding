# Issue 090 Overview
Last Updated: 2025-12-31
Related: Issue #90, PR (TBD)

## Original Issue

# EPIC: Repository Restructure & Documentation Reorganization (RFC-Shared-Agent-Scaffolding)

**Goal:** Refactor the repository layout to a clean, scalable structure with consistent naming, consolidated documentation, and updated references (docs links, scripts, workflows, tests) — **without breaking behavior** at any point.

**Non negotiables:**
- Use `git mv` for all renames/moves to preserve history.
- After **every Phase**: all tests pass locally, and CI is green.
- After **every Item**: verify references (Markdown links, script paths, workflow paths, config includes) are updated.
- No "big bang" move. This must be incremental, verifiable, and rollback-friendly.

---

## Progress Checklist

- [x] **M0 — Preflight & Safety Nets (No structural changes yet)**
- [x] **M1 — Documentation Consolidation (No code path changes yet)**
- [x] **M2 — Wrapper Directory Refactor (Path changes, but behavior unchanged)**
- [x] **M3 — Naming & Consistency Sweep (Repo-wide standardization)**
- [x] **M4 — Documentation Merges & De-duplication (Reduce maintenance burden)**
- [x] **M5 — Final Verification & "No Regrets" Pass**

---

[Full issue text continues in 090-summary.md for detailed checklist]

## Progress Tracker

- [x] M0 — Preflight & Safety Nets
  - [x] P0 — Baseline & Repo Snapshot
  - [x] P1 — Add Reference Validation Helpers
- [x] M1 — Documentation Consolidation
  - [x] P1 — Create docs/ taxonomy and migrate documents/
  - [x] P2 — Relocate root-level historical/progress Markdown
  - [x] P3 — Update documentation references
- [x] M2 — Wrapper Directory Refactor
  - [x] P1 — Rename RFC-Shared-Agent-Scaffolding-Example/ → wrappers/
  - [x] P2 — Extract agent-methodology docs
  - [x] P3 — Fix CI workflows & test harness paths
- [x] M3 — Naming & Consistency Sweep
  - [x] P1 — Repo-wide kebab-case normalization
  - [x] P2 — Add/update "Contributing" and standards docs
- [x] M4 — Documentation Merges & De-duplication
  - [x] P1 — Consolidate overlapping docs
- [x] M5 — Final Verification & "No Regrets" Pass
  - [x] P1 — Full repo integrity checks
    - [x] Item 1.1 — Reference verification (✅ PASSED)
    - [x] Item 1.2 — Behavior verification (✅ PASSED - 120+ tests)
    - [x] Item 1.3 — CI validation (✅ PASSED)
  - [x] P2 — Documentation navigation verification
    - [x] Item 2.1 — Docs index & README navigation (✅ PASSED)

## Session Notes (newest first)

### 2025-12-31 00:40 - M5 Final Verification Complete
- Completed all M5 verification items
- Reference verification: No obsolete paths in active codebase
- Behavior verification: All tests pass (Bash: 23, Python: 20, Perl: 46, Rust: 31)
- CI validation: All linting checks pass
- Documentation navigation: All paths verified
- **EPIC #90 Repository Restructure is COMPLETE**

### 2025-12-31 00:33 - Session initialization
- Initialized issue journal directory
- Created overview and next-steps files
- Assessed current repository state
- Identified M5 as the remaining milestone to complete
