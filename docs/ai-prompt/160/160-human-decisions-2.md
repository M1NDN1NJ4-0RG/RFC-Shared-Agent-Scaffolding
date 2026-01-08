# LOCKED IN HUMAN DECISIONS (ROUND 2)

These decisions are final unless explicitly revised by Ryan. Requirements below are intentionally direct and must be
treated as contracts.

## Decision 1 — Phase 2.5 Windows Validation (Blocking vs Deferred)

**Decision:** **Hybrid approach (CI-first Windows validation).**

**Requirements:**

- - Windows support remains a **Phase 2.5 RELEASE BLOCKER**, per contract. - Implement and require **Windows GitHub
  Actions CI runs** that validate Phase 2.5 behavior. - Manual validation on a physical Windows machine is **explicitly
  deferred** until one is available or a VM is spun up on macOS.

**Notes:**

- - CI must cover: Rich console output, Rich-Click help output, and shell completion behaviors to the extent testable in
  CI.

## Decision 2 — Phase 2.6–2.9 Prioritization and Sequencing

**Decision:** **Sequential approach (complete Phase 2.5 blockers first), then proceed in this order:**

1) **Finish Phase 2.5 blockers** (Windows CI validation + remaining tests/docs) 2) **Phase 2.9** (contracts enforcement)
3) **Phase 2.7** (CLI granularity + reporting surface)
4) **Phase 2.8** (env/activate/which) in the order: `which` → `env` → `activate`
5) **Phase 2.6** (centralized exceptions) after the above
6) **Phase 3** (polish) last

**PR strategy:** Break phases into manageable PRs (small, reviewable units) but preserve the phase ordering above.

## Decision 3 — YAML-First Configuration Scope (Phase 2.9)

**Decision:** **Aggressive YAML-first migration.**

**Requirements:**

- - Migrate **all behavior that can reasonably be configured** into YAML-first configuration, without allowing contract
  violations. - Maintain **multi-file structure** (separate conformance YAML files by concern). - Preserve backward
  compatibility via a **transition period** with **deprecation warnings** (do not hard-break users immediately). - Only
  allow CLI overrides that do **not** violate contracts.

## Decision 4 — Exception System Pragma Policy (Phase 2.6)

**Decision:**

- - **Warn on pragmas by default**, but this warning must be **configurable/disable-able**. - **YAML exceptions have
  strict precedence** over pragmas when both apply. - Provide a migration tool that **prints suggestions** and may
  optionally write a **draft file**; it must not silently rewrite canonical exception files.

## Decision 5 — CLI Granularity vs Complexity (Phase 2.7)

**Decision:** **Implement the full flag set (spec-compliant), with strong UX to prevent overwhelm.**

**Requirements:**

- Implement all Phase 2.7 CLI flags as specified (granular `--lang`, repeatable `--tool`, formats, summaries, reporting, etc.).
- - Mitigate complexity via: - Rich-Click help **panels/sections** (Filtering / Output / Execution / Info) - Excellent
  examples in the help text - Clear error messages and deterministic exit codes

## Decision 6 — Output Format Support (Phase 2.7)

**Decision:** **Support the full structured output suite in-scope for Phase 2.7: `json`, `yaml`, `csv`, `xlsx`.**

**Requirements:**

- - Outputs MUST derive from a **single normalized data model** shared across formats.
- XLSX support is required; if it needs a dependency (e.g., `openpyxl`), handle it as an explicit packaging extra and ensure CI installs it where needed.

## Decision 7 — `repo-lint doctor` Command Scope

**Decision:** **Minimum checks; check-only (no auto-fix).**

**Requirements:**

- `repo-lint doctor` must perform minimum mandatory checks (repo root, venv resolution, config validity, tool registry load, tool availability, PATH sanity).
- `doctor` must be **check-only** (report + suggest fixes; no automatic changes).
- - Help content must be extremely clear, with **exact references** documented in the tool documentation.
- Documentation file reference: `tools/repo_lint/HOW-TO-USE.md` (name may change later, but this is the current canonical path).

## Decision 8 — Environment Commands (`repo-lint env/activate/which`)

**Decision:** **Required. Implement all three in this order:**

1) `repo-lint which`
2) `repo-lint env`
3) `repo-lint activate`

## Decision 9 — Phase 2.9 Timing (Integration + YAML-First Enforcement)

**Decision:** **Phase 2.9 must be implemented before Phase 2.6–2.8 work proceeds (after Phase 2.5 blockers).**

**Requirements:**

- - Perform an audit to identify any existing non-integrated helper scripts. - Enforce Phase 2.9 contracts for all new
  work immediately. - Apply retroactive enforcement as part of the audit findings (prioritize correctness and
  determinism).

## Decision 10 — Testing Strategy for New Phases

**Decision:** **Standard coverage, tests required before review, and Windows CI for relevant phases.**

**Requirements:**

- - Standard test coverage: unit tests + targeted integration tests for major workflows. - Tests MUST be added and
  passing **before** code review. - Windows CI must be included for phases where Windows behavior is relevant (Phase 2.5
  and anything that touches CLI/help/output/shell integration).

---

<--- LOCKED IN HUMAN ANSWERS ABOVE THIS LINE --->

---

# Issue #160 - Human Decisions Required (Round 2)

**Date:** 2025-12-31 **Context:** Consolidation of Phase 2.5-2.9 requirements from external documents **Status:**
PENDING HUMAN REVIEW

---

## Decision 1: Phase 2.5 Windows Validation - Blocking or Deferred

**Issue:** Phase 2.5 (Rich UI) includes a hard requirement: "Windows validation (PowerShell, PowerShell 7+, Windows
Terminal) is a RELEASE BLOCKER."

**Current State:**

- - Phase 2.5 core implementation is complete (PR #180 merged) - Windows validation has NOT been performed - No
  Windows-specific testing infrastructure exists in CI

**Options:**

**A) Treat as BLOCKER - Validate Before Proceeding** ✅ RECOMMENDED

- - Do NOT proceed to Phase 2.6+ until Windows validation is complete - Add Windows CI runners to GitHub Actions -
  Manually validate Rich output, Rich-Click help, and shell completion on Windows - Risk: Delays further progress -
  Benefit: Ensures quality before building on top of Phase 2.5

**B) Defer Windows Validation to Phase 3**

- - Continue to Phase 2.6+ assuming Windows works - Add Windows validation as a Phase 3 item - Risk: May discover
  breaking issues later that require rework - Benefit: Maintains momentum on feature development

**C) Mark as "Best Effort" and Remove BLOCKER Status**

- - Acknowledge Windows support as aspirational, not required - Risk: Undermines cross-platform commitment - Benefit:
  Avoids validation overhead

**Recommendation:** Option A. The spec explicitly states "Windows validation fails, it is a release blocker for Phase
2.5." We should honor this contract.

**Human Decision Required:**

- - [ ] Which option do you choose? (A/B/C or propose alternative) - [ ] If Option A: Do you have access to Windows
  machines for manual validation, or should we rely on CI only? - [ ] Should we add Windows CI runners now, or validate
  manually first?

---

## Decision 2: Phase 2.6-2.9 Prioritization and Sequencing

**Issue:** Four major new phases have been added (2.6, 2.7, 2.8, 2.9). Each is substantial. We need to determine
priority and whether to implement all of them.

**Current State:**

- - Phase 1: ✅ Complete (6/6 items) - Phase 2: ✅ Complete (4/4 items) - Phase 2.5: ✅ Core Complete (6/9 sub-items; 3
  pending including Windows blocker) - Phase 2.6: NOT STARTED (Centralized Exception Rules - YAML exceptions replacing
  pragmas)
- Phase 2.7: NOT STARTED (Extended CLI Granularity - `--lang`, `--tool`, `--format`, `--summary`, etc.)
- Phase 2.8: NOT STARTED (Environment & PATH Management - `repo-lint env/activate/which`)
- - Phase 2.9: NOT STARTED (Mandatory Integration & YAML-First Contracts - cross-cutting requirements) - Phase 3:
  DEFERRED (Polish, nits, docstrings, docs)

**Key Questions:**

1. 1. **Are all of Phase 2.6-2.9 required, or are some optional/nice-to-have?** - Phase 2.6 (Exceptions): Improves
   maintainability, reduces pragma clutter - Phase 2.7 (CLI Granularity): Power-user features, better CI integration -
   Phase 2.8 (env/activate/which): Solves PATH/venv onboarding pain - Phase 2.9 (Integration/YAML-First): Cross-cutting
   quality enforcement

2. 2. **What is the priority order?** - Suggested priority: 2.9 (contracts) → 2.7 (CLI usability) → 2.8 (onboarding) →
   2.6 (exceptions) - Rationale: 2.9 ensures quality for everything else; 2.7 improves daily UX; 2.8 solves onboarding;
   2.6 is long-term maintenance improvement

3. 3. **Should we complete Phase 2.5 blockers first, or proceed to Phase 2.6+ in parallel?** - Proceeding in parallel
   risks building on an incomplete foundation - Completing Phase 2.5 blockers first ensures a stable base

**Options:**

**A) Sequential Approach (Recommended)**

1. 1. Complete Phase 2.5 blockers (Windows validation, tests, docs) 2. Implement Phase 2.9 (contracts enforcement) 3.
   Implement Phase 2.7 (CLI granularity) 4. Implement Phase 2.8 (env/activate/which) 5. Implement Phase 2.6 (centralized
   exceptions) OR defer to future work 6. Revisit Phase 3 (polish) when all features are stable

**B) Parallel Approach**

- - Work on Phase 2.6-2.8 while Windows validation is deferred - Risk: Potential rework if Phase 2.5 issues are
  discovered

**C) Cherry-Pick Approach**

- - Implement only the highest-value items from each phase
- Example: Just `--lang`/`--tool` from Phase 2.7, skip reporting formats
- - Risk: Incomplete features may create inconsistent UX

**Human Decision Required:**

- - [ ] Which overall approach do you prefer? (A/B/C or propose alternative) - [ ] Which phases are REQUIRED vs
  OPTIONAL? - [ ] What is your preferred priority order? - [ ] Should we break any phases into smaller PRs, or tackle
  each phase as a single PR?

---

## Decision 3: YAML-First Configuration Scope (Phase 2.9)

**Issue:** Phase 2.9 includes a mandate: "Any behavior that can reasonably be configured externally MUST be migrated to
the conformance YAML configuration system."

**Current State:**

- - Some configuration is already in YAML (naming rules, docstring rules, linting rules, UI theme) - Some configuration
  is in code (hard-coded constants, CLI-only flags, ad-hoc env vars)

**Questions:**

1. 1. **How aggressive should the YAML-first migration be?** - Conservative: Only migrate obvious candidates (tool
   enable/disable lists, file patterns) - Moderate: Migrate most settings but keep a few CLI-only flags for ergonomics -
   Aggressive: Migrate EVERYTHING configurable to YAML; CLI flags only override

2. 2. **Should we create a single unified config file, or keep the existing multi-file structure?** - Current: Separate
   files (naming rules, docstring rules, linting rules, UI theme, exceptions) - Option A: Keep separate files (clearer
   separation of concerns) - Option B: Add a "master config" that can include/reference other configs
   - Option C: Consolidate into a single `repo-lint-config.yaml` (simpler but larger)

3. 3. **How do we handle backward compatibility?** - Option A: Support both old (CLI-only) and new (YAML + CLI) for a
   transition period - Option B: Hard cut-over; update all docs and examples - Option C: Deprecation warnings for old
   flags

**Human Decision Required:**

- - [ ] How aggressive should the YAML-first migration be? (Conservative/Moderate/Aggressive) - [ ] Single config file
  or multi-file structure? (A/B/C) - [ ] Backward compatibility approach? (A/B/C) - [ ] Are there any behaviors that
  SHOULD remain CLI-only (not configurable via YAML)?

---

## Decision 4: Exception System Pragma Policy (Phase 2.6)

**Issue:** Phase 2.6 proposes a centralized YAML exceptions file, while keeping pragma support for backward
compatibility. The spec suggests "prefer YAML exceptions over pragmas" but leaves the pragma warning policy flexible.

**Questions:**

1. 1. **Should we actively discourage pragmas?** - Option A: Warn on pragmas by default (encourage migration to YAML) -
   Option B: No warnings by default (pragmas are first-class citizens) - Option C: Warn only in CI (nudge toward
   centralized approach)

2. 2. **What happens if both YAML and pragma apply to the same target?** - Current spec: "Prefer YAML exceptions over
   pragmas (deterministic + centralized)" - Should we enforce this strictly, or allow pragmas to override YAML if
   explicitly requested?

3. 3. **Should we provide a migration tool?**
   - The spec proposes `repo-lint pragmas scan` to suggest YAML entries
   - - Should this auto-generate a complete exceptions YAML, or just print suggestions?

**Human Decision Required:**

- - [ ] Pragma warning policy? (A/B/C or propose alternative) - [ ] YAML-always precedence, or allow pragma override?
  (Strict YAML / Configurable) - [ ] Migration tool scope? (Auto-generate YAML / Print suggestions only / Not needed)

---

## Decision 5: CLI Granularity vs Complexity Trade-off (Phase 2.7)

**Issue:** Phase 2.7 proposes extensive CLI flags (`--lang`, `--tool`, `--summary`, `--summary-only`, `--summary-format`, `--format`, `--report`, `--reports-dir`, `--max-violations`, `--show-files`, `--hide-files`, `--show-codes`, `--hide-codes`, `--fail-fast`, `--dry-run`, `--diff`, `--changed-only`, `--list-langs`, `--list-tools`, `--tool-help`, `--explain-tool`, etc.).

**Concern:** This is a LOT of flags. The CLI could become overwhelming for new users.

**Options:**

**A) Implement All Flags (Spec-Compliant)**

- - Pros: Maximum flexibility, power-user friendly - Cons: Overwhelming for beginners, large surface area to maintain -
  Mitigation: Rich-Click help grouping and great documentation

**B) Implement Core Subset First**

- Core: `--lang`, `--tool`, `--summary`, `--format json`
- Defer: `--summary-format`, `--reports-dir`, verbosity controls, `--changed-only`
- - Pros: Incremental approach, easier to test - Cons: Leaves some features incomplete

**C) Use Profiles/Presets Instead of Individual Flags**

- Example: `--profile=ci` (implies `--ci --format=json --summary-only --fail-fast`)
- - Pros: Simplifies common workflows - Cons: Additional abstraction layer, profiles need definition

**D) Lean on YAML Config (Phase 2.9 Integration)**

- - Put most settings in YAML; CLI flags only for overrides - Pros: Less CLI clutter - Cons: Less discoverable for new
  users

**Human Decision Required:**

- - [ ] Which approach do you prefer? (A/B/C/D or hybrid) - [ ] If Option B (subset), which flags are MUST-HAVE vs
  NICE-TO-HAVE? - [ ] Should we implement profiles/presets? (Yes/No/Maybe later)

---

## Decision 6: Output Format Support - Full Suite or Minimal

**Issue:** Phase 2.7 proposes support for: `rich`, `plain`, `json`, `yaml`, `csv`, `xlsx`.

**Questions:**

1. 1. **Is XLSX (Excel) support required?**
   - Requires additional dependency (`openpyxl` or similar)
   - - Use case: Management reports, data analysis - Alternative: Users can convert CSV to XLSX externally

2. 2. **Should we support all formats in the first iteration?** - Option A: All formats (json, yaml, csv, xlsx) -
   complete solution - Option B: Just json and yaml - structured data only - Option C: Just json and csv - most common
   formats

**Human Decision Required:**

- - [ ] XLSX support required? (Yes/No/Future work) - [ ] Which formats are required for first release?
  (All/Subset/Minimal) - [ ] Are you willing to add external dependencies for format support (e.g., openpyxl for XLSX)?

---

## Decision 7: `repo-lint doctor` Command Scope

**Issue:** Phase 2.7 proposes a `repo-lint doctor` command for comprehensive sanity checking.

**Questions:**

1. **What checks should `doctor` perform?**
   - - Minimum: repo root, venv, tool availability, config validity - Extended: git config, python version, disk space,
     network connectivity, proxy settings - Paranoid: hash verification of installed tools, signature checks, etc.

2. **Should `doctor` attempt auto-fix?**
   - - Option A: Check-only (report problems, suggest fixes)
   - Option B: Auto-fix with confirmation (`--fix` flag)
   - Option C: Auto-fix without confirmation (`--fix --yes`)

**Human Decision Required:**

- [ ] What level of checks should `doctor` perform? (Minimum/Extended/Paranoid)
- [ ] Should `doctor` support auto-fix? (Check-only/With confirmation/Auto-fix)

---

## Decision 8: Environment Commands (`repo-lint env/activate/which`) - Required or Optional

**Issue:** Phase 2.8 proposes three new commands for PATH/venv management. These are primarily onboarding/UX
improvements, not core linting functionality.

**Questions:**

1. 1. **Are these commands required, or are they nice-to-have?** - Required: Solves a real pain point for contributors -
   Nice-to-have: Workarounds exist (manual PATH editing, direct venv activation)

2. 2. **Should we implement all three, or a subset?**
   - `repo-lint which` is lowest-effort, highest-value (diagnostic)
   - `repo-lint env` requires careful cross-platform scripting
   - `repo-lint activate` is most complex (subshell handling)

**Human Decision Required:**

- - [ ] Are these commands required? (Yes/No/Nice-to-have)
- [ ] If yes, implement all three, or start with `which` only?
- - [ ] Priority relative to Phase 2.6/2.7/2.9?

---

## Decision 9: Phase 2.9 - Integration Enforcement Timing

**Issue:** Phase 2.9 includes two major contracts:

1. **Internal Integration Contract:** All helper scripts MUST be integrated into `repo-lint` package
2. 2. **External Configuration Contract:** All configuration MUST be YAML-first

**Questions:**

1. 1. **Should Phase 2.9 be implemented FIRST (before 2.6/2.7/2.8)?** - Pros: Ensures quality contracts are in place for
   all new features - Cons: Delays visible feature delivery

2. 2. **Are there existing helper scripts that need integration NOW?** - Need to audit: Do any current runners/commands
   invoke external scripts? - If yes: Phase 2.9 is a prerequisite - If no: Phase 2.9 can be deferred

**Human Decision Required:**

- - [ ] Should Phase 2.9 be implemented first? (Yes/No/Partial) - [ ] Are there existing helper scripts that need
  integration? (Audit required) - [ ] Should we enforce these contracts retroactively on existing code, or only for new
  features?

---

## Decision 10: Testing Strategy for New Phases

**Issue:** Each new phase (2.6-2.9) adds significant complexity. Testing requirements are not fully specified.

**Questions:**

1. 1. **What level of test coverage is required?** - Minimum: Unit tests for new code paths - Standard: Unit tests +
   integration tests for major workflows - Comprehensive: Unit + integration + cross-platform validation + fixture repos

2. 2. **Should we require tests BEFORE code review, or allow iterative test addition?** - Before code review: Ensures
   quality, may slow development - Iterative: Faster initial delivery, risk of incomplete coverage

**Human Decision Required:**

- - [ ] Required test coverage level? (Minimum/Standard/Comprehensive) - [ ] Tests required before code review?
  (Yes/Iterative) - [ ] Should we add cross-platform testing for ALL phases, or just critical ones (2.5, 2.8)?

---

## Summary of Decisions Required

1. 1. **Phase 2.5 Windows Validation:** Blocker vs deferred? (Decision 1) 2. **Phase 2.6-2.9 Prioritization:**
   Sequential vs parallel vs cherry-pick? (Decision 2) 3. **YAML-First Scope:** Conservative vs aggressive migration?
   (Decision 3) 4. **Pragma Policy:** Warn vs allow vs CI-only? (Decision 4) 5. **CLI Complexity:** All flags vs subset
   vs profiles? (Decision 5) 6. **Output Formats:** XLSX required? All formats vs minimal? (Decision 6) 7. **Doctor
   Command:** Check-only vs auto-fix? (Decision 7) 8. **Env Commands:** Required vs nice-to-have? (Decision 8) 9.
   **Phase 2.9 Timing:** First vs later vs partial? (Decision 9) 10. **Testing Strategy:** Coverage level and timing?
   (Decision 10)

---

## Recommendation Summary

**Immediate Actions (Minimal-Change Principle):**

1. 1. ✅ Complete Phase 2.5 blockers first (Windows validation, tests, docs) 2. ✅ Defer Phase 2.6-2.8 until Phase 2.5 is
   fully complete 3. ✅ Get human sign-off on priorities before implementing any new phases

**Suggested Priority (if all phases approved):**

1. 1. Phase 2.5 completion (Windows validation - BLOCKER) 2. Phase 2.9 (contracts) - ensures quality for everything else
3. Phase 2.7 (CLI granularity) - core subset (`--lang`, `--tool`, `--summary`, json format)
4. Phase 2.8 (`repo-lint which`) - minimal diagnostic command
5. 5. Phase 2.6 (centralized exceptions) - long-term maintenance improvement 6. Remaining Phase 2.7 features (csv/xlsx,
   advanced verbosity)
7. Remaining Phase 2.8 features (`env`, `activate`)
8. 8. Phase 3 (polish)

**Conservative Defaults (if in doubt):**

- - Implement features incrementally (smallest viable subset first) - Preserve backward compatibility wherever possible
  - Defer Windows-specific work to CI validation rather than manual testing - Keep CLI simple (core flags only; defer
  advanced features)
- Check-only for `doctor` (no auto-fix)
- - Warn on pragmas by default (encourage YAML exceptions)

---

**Next Steps:**

- @m1ndn1nj4 please review and provide decisions for items marked with `[ ]`
- - Agent will proceed based on human decisions - Agent will NOT implement Phase 2.6-2.9 until decisions are made
