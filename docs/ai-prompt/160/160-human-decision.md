# ✅ Locked-In Human Decisions (Authoritative)

**Decision Owner:** Human (Ryan)
**Decision Date:** 2025-12-31
**Applies To:** Issue #160 (Phase 2 & Phase 3)

This section is the **single source of truth** for the decisions below. The remainder of this document must be
interpreted in accordance with these locked-in decisions.

## Phase 2 Decisions

### Decision 1 — Package `repo_lint` as an installable tool (APPROVED)

**Decision:** **YES — Proceed with packaging.**

**Non-negotiable requirements:**

- Provide a standard install + entrypoint so contributors can run `repo-lint ...` directly (while keeping `python3 -m tools.repo_lint ...` working as a compatibility path during transition).
- - The packaged tool must be as **self-contained** as reasonably possible (ship the Python code + required Python
  dependencies).
- Repository-local workflows/docs must standardize on the preferred invocation (`repo-lint`) once packaging lands.

**Expected deliverables:**

- Packaging metadata (`pyproject.toml` preferred) and a console entrypoint.
- - Updated docs to reflect the canonical invocation.

---

### Decision 2 — Add naming/style enforcement to `repo_lint` as a CHECK (APPROVED; NO AUTO-RENAMES)

**Decision:** **YES — Add naming/style checks to `repo_lint check` output.**

**Explicit constraints:**

- - **NO automatic renaming** of files (no “auto-change” behavior). Naming enforcement is **check-only**. - Naming rules
  MUST be defined externally via a **YAML rules/vectors file** (per-language rules). This is intentionally
  user-configurable. - This approach is not limited to naming: **all user-tunable rulesets** (linting rules, docstring
  rules/contracts, naming standards) should be configurable via **external config files**, rather than hardcoded.
  - Config files MUST live under: `conformance/repo-lint/`.
  - - We will use **exactly three** top-level rules files:
    - `conformance/repo-lint/repo-lint-naming-rules.yaml`
    - `conformance/repo-lint/repo-lint-docstring-rules.yaml`
    - `conformance/repo-lint/repo-lint-linting-rules.yaml`
  - Per-language rule organization MUST follow **Option A** (single file per category with a `languages:` mapping).
- The design MUST also support **Option B** in the future (ability to “include”/compose per-language fragments) for very
large rulesets, but Option B is **not** required for the initial implementation.
  - Every rules YAML file MUST include a **type marker** and a **version** at the top-level (e.g. `config_type:` and `version:`) to prevent accidental file swaps and to enable strict validation.
  - - YAML formatting MUST follow best practices and MUST be strictly enforced by the config validator:
    - YAML document start marker `---` is **REQUIRED**.
    - YAML document end marker `...` is **REQUIRED**.

**Configuration safety requirements (STRICT):**

- - Implement a **configuration validator** that runs **before** ingesting any rules:
  - Validate that the YAML is a single-document file and that it contains the required `---` start marker and `...` end marker before ingesting any content.
  - - Validate YAML structure against a strict schema/contract. - Reject unknown keys. - Provide actionable error
    messages (file + path + what is wrong). - Fail fast and loudly (do not limp forward with partial config). - If
    config validation fails, the tool must “scream”: exit non-zero with a clear failure summary.

**Expected deliverables:**

- Three external YAML rules/vectors files located under `conformance/repo-lint/`:
  - `repo-lint-naming-rules.yaml`
  - `repo-lint-docstring-rules.yaml`
  - `repo-lint-linting-rules.yaml`
- - A strict config validation step that runs before rule ingestion and enforces:
  - Required YAML document markers (`---` and `...`) and single-document structure
  - Required top-level fields (`config_type`, `version`, and the expected schema for that file type)
  - - Rejection of unknown keys and malformed structures
- Naming/docstring/linting rule violations reported as part of the normal `repo_lint check` output (check-only; no auto-renames).

---

### Decision 3 — Pin external tool versions (APPROVED)

**Decision:** **YES — Pin tool versions to ensure deterministic behavior.**

**Implementation expectation:**

- Resolve the current mismatch between `install/version_pins.py` and `requirements-dev.txt` so there is **one canonical source of truth** for tool versions.
- - The installer must reliably install the pinned versions so CI and local runs match.

---

### Decision 4 — CLI usability: Adopt Click + Rich help menus + shell autocomplete (APPROVED)

**Decision:** **YES — Integrate Click.**

**Non-negotiable requirements:**

- - Implement the CLI using **Click**. - Provide **rich help output** (e.g., Rich-Click / rich formatting) and **CLI
  auto-complete**.
- Provide a dedicated doc file: **`HOW-TO-USE-THIS-TOOL.md`** covering:
  - - Installation - Common commands and examples - Enabling shell completions (per shell) - Troubleshooting and common
    failure modes

---

## Phase 3 Decisions

### Decision 5 — Code style clean-up in `tools/repo_lint` (APPROVED: Do it, but safely)

**Decision:** Proceed with code style clean-up.

**Guardrails:**

- - No “style-only refactor” that changes behavior without tests. - Prefer small, reviewable commits. - If changes are
  non-trivial, increase test coverage first.

---

### Decision 6 — Docstrings: Comprehensive audit (APPROVED)

**Decision:** **Option A — Comprehensive docstring audit.**

**Scope:**

- - Audit and document **all** public surfaces and any internal helpers that are non-trivial. - Align docstrings with
  the repo’s chosen conventions and the broader “contracts” ethos.

---

### Decision 7 — Documentation updates (APPROVED)

**Decision:** **Option A — Update all documentation.**

**Scope expectations:**

- - Ensure docs reflect packaging + Click CLI + new naming/config rules. - Verify links and cross-references. -
  Eliminate ambiguity: docs should clearly state the canonical commands, required steps, and expected outputs.

---

### Decision 8 — Integration tests for runners (APPROVED)

**Decision:** **Option A — Add integration tests.**

**Scope expectations:**

- Add end-to-end tests that execute `repo_lint check` across multiple language fixtures.
- - Validate combined output, exit codes, and error handling. - Keep fixtures minimal but representative.

---

--- PUT MY DECISIONS ABOVE HERE ---

# Issue #160 - Human Decisions Required

 **Status:** Phase 1 Complete ✅ | Phase 2 & 3 Awaiting Direction
**Last Updated:** 2025-12-31
**Related:** Issue #160, `docs/ai-prompt/160/160-overview.md`

---

## Overview

Phase 1 (Critical Fixes) of Issue #160 is **COMPLETE** and ready for merge. All 6 high-priority items have been
implemented, tested (20 tests passing), and code-reviewed.

This document outlines **decisions that require human approval** before proceeding with Phase 2 (Major Enhancements) and
Phase 3 (Polish & Minor Improvements).

---

## Phase 1 Status: ✅ COMPLETE

All Phase 1 items are done and do NOT require further decisions:

- - ✅ Fix repository root detection - ✅ Clarify exit codes for unsafe mode - ✅ Handle partial install failures
  gracefully - ✅ Ensure missing docstring validator is detected - ✅ Validate non-Python unsafe mode behavior - ✅ Add
  missing unit tests for error conditions

**Action Required:** Merge the Phase 1 PR, then decide whether to proceed with Phase 2/3.

---

## Phase 2 – Major Enhancements (Awaiting Human Decisions)

### Decision #1: Should we make `repo_lint` an installable package

**Context:** Future Work (FW-013) calls for packaging the tool.

**Options:**

1. 1. **YES - Proceed with packaging**
   - Create `pyproject.toml` with package metadata
   - Define entry point: `repo-lint` command
   - Update all documentation to use `repo-lint` instead of `python3 -m tools.repo_lint`
   - Allows `pip install -e .` for local development
   - - **Scope:** Medium (affects project structure, docs, CI)

2. 2. **NO - Keep current invocation method**
   - Continue using `python3 -m tools.repo_lint`
   - - Less overhead, no packaging complexity - **Scope:** None (no changes needed)

3. 3. **DEFER - Revisit later** - Mark FW-013 as "planned but not prioritized" - Wait for clearer use case or demand -
   **Scope:** None (no changes needed)

**Questions for Human:**

- Is there a specific use case driving the need for `pip install`?
- - Are external users expected to install this tool, or is it repo-internal only? - Should we align with other Python
  tooling in the repo (if any)?

**Recommended Option:** **Option 1 (YES — Proceed with packaging)** (APPROVED — locked in).

---

### Decision #2: Should we integrate naming-and-style enforcement into `repo_lint`

**Context:** Filename conventions (kebab-case, snake_case) are documented in `docs/contributing/naming-and-style.md` but not automatically enforced by `repo_lint`.

**Options:**

1. 1. **YES - Add naming enforcement** - Create a new "NamingRunner" or extend existing checks
   - Load rules from external YAML vectors in `conformance/repo-lint/` (no hardcoding)
   - Check all files for compliance with naming conventions defined per-language under a `languages:` mapping (Option A)
   - Report violations in `repo_lint check` output
   - - Optionally suggest fixes (though auto-renaming is complex). Auto-renaming is explicitly forbidden. - **Scope:**
     Large (new runner, tests, integration with existing checks)

2. 2. **NO - Keep naming checks separate** - Continue using CI or manual scripts for naming validation
   - `repo_lint` focuses on code quality (linting, formatting, docstrings)
   - - **Scope:** None (no changes needed)

3. 3. **PARTIAL - Add basic naming checks only** - Check only Python files (snake_case for modules) - Skip complex cases
   (kebab-case for scripts, multi-language rules) - **Scope:** Medium (simpler than full enforcement)

**Locked decision detail:** Naming rules (and other user-tunable rulesets) MUST be defined in external YAML config under `conformance/repo-lint/` with strict schema validation. Each YAML file MUST include `---` and `...`, plus `config_type` and `version`. Per-language rules MUST be represented via a `languages:` mapping (Option A) with future support for include/composition (Option B) if rulesets become massive.

**Questions for Human:**

- - Is naming drift a current problem, or is manual review sufficient? - Should naming enforcement be blocking (CI
  fails) or advisory (warnings)?
- Are the rules in `docs/contributing/naming-and-style.md` stable and complete?

**Recommended Option:** **Option 1 (YES — Add naming enforcement)** as **CHECK-ONLY** with **external YAML rules** +
**strict pre-ingest config validation** (APPROVED — locked in).

---

### Decision #3: Should we pin external tool versions in the installer

**Context:** `install/version_pins.py` exists with desired versions (Black, etc.), but `install_python_tools` currently installs latest via `requirements-dev.txt`.

**Options:**

1. 1. **YES - Pin tool versions**
   - Use version pins from `install/version_pins.py`
   - Change installer to run `pip install black==24.8.0` (etc.) using pinned versions
   - - Guarantees deterministic linting behavior across environments
   - **Scope:** Small (modify `install_helpers.py`, update installer logic)

2. 2. **NO - Continue using latest versions**
   - Keep current behavior (install latest via `requirements-dev.txt`)
   - - Simpler maintenance (no version update burden) - Risk: linting behavior may change when tools update - **Scope:**
     None (no changes needed)

3. 3. **HYBRID - Pin some tools, float others** - Pin critical tools (Black, Ruff) for consistency - Float others
   (pylint, yamllint) for latest features/fixes - **Scope:** Small-Medium (selective pinning logic)

**Questions for Human:**

- - Have there been issues with tool version drift causing CI failures? - Who is responsible for keeping version pins
  up-to-date? - Is deterministic behavior more important than getting latest fixes?

**Recommended Option:** **Option 1 (pin versions)** (APPROVED — locked in).

---

### Decision #4: Should we improve CLI usability

**Context:** Minor enhancements like better help text, configuration files, etc.

**Options:**

1. 1. **YES - Add usability improvements**
   - Better help text for `--only` and `--yes-i-know` flags
   - Add usage examples to `--help` output
   - Consider configuration file support (`.repo-lint.yaml`)
   - - Update documentation with clear usage instructions - **Scope:** Small-Medium (depending on features chosen)

2. 2. **NO - Keep current CLI as-is** - Current help text is adequate - Documentation can cover usage examples - Avoid
   feature creep - **Scope:** None (no changes needed)

3. 3. **PARTIAL - Documentation only** - Don't change CLI code
   - Add comprehensive usage guide in `tools/repo_lint/README.md`
   - - **Scope:** Small (docs only)

**Questions for Human:**

- - Have users reported confusion with the CLI? - Is configuration file support needed, or are command-line flags
  sufficient? - What's the priority of this compared to other work?

**Recommended Option:** **Option 1 (YES — Add usability improvements)** via **Click + Rich help + shell autocomplete** + dedicated `HOW-TO-USE-THIS-TOOL.md` (APPROVED — locked in).

---

## Phase 3 – Polish & Minor Improvements (Awaiting Human Decisions)

### Decision #5: Should we perform code style clean-up

**Context:** Minor style issues may exist (unused imports, line lengths, etc.).

**Options:**

1. 1. **YES - Run linters and fix warnings**
   - Run `pylint` and `flake8` on all `tools/repo_lint` code
   - - Fix warnings (unused imports, variable names, line lengths) - Align formatting with repository norms - **Scope:**
     Small-Medium (depending on number of issues found) - **Risk:** May introduce bugs if not carefully tested

2. 2. **NO - Leave code as-is** - Current code works and is tested - Style fixes are low value unless blocking -
   **Scope:** None (no changes needed)

3. 3. **CONDITIONAL - Only if linters fail** - Run linters as part of Phase 1 validation - Only fix if there are actual
   failures - **Scope:** Unknown until linters are run

**Questions for Human:**

- - Is there a specific code style standard to enforce? - Are linter warnings currently blocking CI? - Is this work
  worth the testing/validation overhead?

**Recommended Option:** **Option 1 (YES — run linters and fix warnings)** with guardrails (APPROVED — locked in).

---

### Decision #6: Should we add/improve docstrings

**Context:** Some private methods or CLI helpers may lack docstrings.

**Options:**

1. 1. **YES - Comprehensive docstring audit**
   - Audit all public functions/methods in `repo_lint`
   - - Add descriptive docstrings (Purpose, parameters, return values) - Align with reST or Google style per repository
     convention - **Scope:** Medium (requires reviewing entire codebase)

2. 2. **NO - Current docstrings are sufficient** - Public APIs are documented - Private helpers don't need extensive
   docs - **Scope:** None (no changes needed)

3. 3. **PARTIAL - Public API only** - Ensure all public functions/classes have docstrings - Skip private/internal
   helpers - **Scope:** Small

**Questions for Human:**

- - What's the repository's docstring policy (public only vs. all functions)? - Is there a specific style guide (Google,
  NumPy, reST)? - Are missing docstrings causing issues for maintainers?

**Recommended Option:** **Option 1 (YES — comprehensive docstring audit)** (APPROVED — locked in).

---

### Decision #7: Should we update documentation

**Context:** Once code changes are done, docs should reflect them.

**Options:**

1. 1. **YES - Update all documentation**
   - Mark FW-013 in `docs/future-work.md` (if packaging is done)
   - Add "Tools" section to main README mentioning `repo-lint`
   - Update `CONTRIBUTING.md` with `repo-lint` usage instructions
   - - Ensure all doc links are current - **Scope:** Small (if only Phase 1), Medium (if Phase 2/3 done)

2. 2. **MINIMAL - Update only what changed** - Document Phase 1 changes (exit codes, new behaviors) - Skip comprehensive
   doc overhaul - **Scope:** Small

3. 3. **DEFER - Wait until all phases complete** - Don't update docs until Phase 2/3 work is decided - Avoid churn from
   multiple doc updates - **Scope:** None (no changes needed now)

**Questions for Human:**

- - Should Phase 1 changes be documented immediately? - Are there specific docs that are out-of-date or incomplete? -
  Who reviews/approves documentation changes?

**Recommended Option:** **Option 1 (YES — update all documentation)** (APPROVED — locked in).

---

### Decision #8: Should we add integration tests for runners

**Context:** Current tests are isolated unit tests. Integration tests could catch cross-cutting issues.

**Options:**

1. 1. **YES - Add integration tests** - Create test repos with known violations in multiple languages
   - Run `repo_lint check` end-to-end
   - - Verify combined output and error handling - **Scope:** Medium (requires test fixtures, multi-language setup)

2. 2. **NO - Current unit tests are sufficient** - Unit tests cover individual runner behavior - Integration testing can
   be manual or via CI - **Scope:** None (no changes needed)

3. 3. **PARTIAL - Add one integration test as example** - Single test covering Python + Bash + Perl - Demonstrates
   pattern without full coverage - **Scope:** Small

**Questions for Human:**

- - Have there been bugs that unit tests didn't catch? - Is there value in automated integration tests vs. manual
  testing? - What's the maintenance burden of keeping integration tests updated?

**Recommended Option:** **Option 1 (YES — add integration tests)** (APPROVED — locked in).

---

## Summary of Decisions Needed

| # | Decision | Phase | Priority | Recommended |
| --- | ---------- | ------- | ---------- | ------------- |
| 1 | Make `repo_lint` installable package | Phase 2 | Medium | Yes — package repo_lint |
| 2 | Integrate naming-and-style enforcement | Phase 2 | Medium | Yes — check-only naming via external YAML + strict validation |
| 3 | Pin external tool versions | Phase 2 | Low | Yes — pin versions (single source of truth) |
| 4 | Improve CLI usability | Phase 2 | Low | Yes — Click + Rich help + autocomplete + HOW-TO doc |
| 5 | Code style clean-up | Phase 3 | Low | Yes — style cleanup (guardrailed) |
| 6 | Add/improve docstrings | Phase 3 | Low | Yes — comprehensive docstring audit |
| 7 | Update documentation | Phase 3 | Low | Yes — update all documentation |
| 8 | Add integration tests | Phase 3 | Low | Yes — add integration tests |

---

## Next Steps

1. 1. **Merge Phase 1 PR** (already complete and ready). 2. **Proceed with Phase 2 & Phase 3 implementation** exactly as
   specified in **Locked-In Human Decisions (Authoritative)** above. 3. Implement the new features behind clear
   contracts/config validation so the packaged tool remains deterministic and safe. 4. Update and verify documentation
   and references as part of the same overall workstream. 5. Close Issue #160 once all approved deliverables are
   complete and CI is green.

---

## Contact

**For questions or to provide decisions, mention @m1ndn1nj4 in Issue #160.**

---

*This document created per new requirement from human on 2025-12-31.*
