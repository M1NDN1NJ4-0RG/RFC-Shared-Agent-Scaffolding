# Issue #160 - Human Decisions Required

**Status:** Phase 1 Complete ✅ | Phase 2 & 3 Awaiting Direction  
**Last Updated:** 2025-12-31  
**Related:** Issue #160, `docs/ai-prompt/160/160-overview.md`

---

## Overview

Phase 1 (Critical Fixes) of Issue #160 is **COMPLETE** and ready for merge. All 6 high-priority items have been implemented, tested (20 tests passing), and code-reviewed.

This document outlines **decisions that require human approval** before proceeding with Phase 2 (Major Enhancements) and Phase 3 (Polish & Minor Improvements).

---

## Phase 1 Status: ✅ COMPLETE

All Phase 1 items are done and do NOT require further decisions:
- ✅ Fix repository root detection
- ✅ Clarify exit codes for unsafe mode
- ✅ Handle partial install failures gracefully
- ✅ Ensure missing docstring validator is detected
- ✅ Validate non-Python unsafe mode behavior
- ✅ Add missing unit tests for error conditions

**Action Required:** Merge the Phase 1 PR, then decide whether to proceed with Phase 2/3.

---

## Phase 2 – Major Enhancements (Awaiting Human Decisions)

### Decision #1: Should we make `repo_lint` an installable package?

**Context:** Future Work (FW-013) calls for packaging the tool.

**Options:**
1. **YES - Proceed with packaging**
   - Create `pyproject.toml` with package metadata
   - Define entry point: `repo-lint` command
   - Update all documentation to use `repo-lint` instead of `python3 -m tools.repo_lint`
   - Allows `pip install -e .` for local development
   - **Scope:** Medium (affects project structure, docs, CI)
   
2. **NO - Keep current invocation method**
   - Continue using `python3 -m tools.repo_lint`
   - Less overhead, no packaging complexity
   - **Scope:** None (no changes needed)
   
3. **DEFER - Revisit later**
   - Mark FW-013 as "planned but not prioritized"
   - Wait for clearer use case or demand
   - **Scope:** None (no changes needed)

**Questions for Human:**
- Is there a specific use case driving the need for `pip install`?
- Are external users expected to install this tool, or is it repo-internal only?
- Should we align with other Python tooling in the repo (if any)?

**Recommended Option:** Need human input to decide.

---

### Decision #2: Should we integrate naming-and-style enforcement into `repo_lint`?

**Context:** Filename conventions (kebab-case, snake_case) are documented in `docs/contributing/naming-and-style.md` but not automatically enforced by `repo_lint`.

**Options:**
1. **YES - Add naming enforcement**
   - Create a new "NamingRunner" or extend existing checks
   - Load rules from `docs/contributing/naming-and-style.md` (or hardcode them)
   - Check all files for compliance with naming conventions
   - Report violations in `repo_lint check` output
   - Optionally suggest fixes (though auto-renaming is complex)
   - **Scope:** Large (new runner, tests, integration with existing checks)
   
2. **NO - Keep naming checks separate**
   - Continue using CI or manual scripts for naming validation
   - `repo_lint` focuses on code quality (linting, formatting, docstrings)
   - **Scope:** None (no changes needed)
   
3. **PARTIAL - Add basic naming checks only**
   - Check only Python files (snake_case for modules)
   - Skip complex cases (kebab-case for scripts, multi-language rules)
   - **Scope:** Medium (simpler than full enforcement)

**Questions for Human:**
- Is naming drift a current problem, or is manual review sufficient?
- Should naming enforcement be blocking (CI fails) or advisory (warnings)?
- Are the rules in `docs/contributing/naming-and-style.md` stable and complete?

**Recommended Option:** Need human input to decide. If naming violations are rare, **Option 2 (keep separate)** may be sufficient.

---

### Decision #3: Should we pin external tool versions in the installer?

**Context:** `install/version_pins.py` exists with desired versions (Black, etc.), but `install_python_tools` currently installs latest via `requirements-dev.txt`.

**Options:**
1. **YES - Pin tool versions**
   - Use version pins from `install/version_pins.py`
   - Change installer to run `pip install black==24.8.0` (etc.) using pinned versions
   - Guarantees deterministic linting behavior across environments
   - **Scope:** Small (modify `install_helpers.py`, update installer logic)
   
2. **NO - Continue using latest versions**
   - Keep current behavior (install latest via `requirements-dev.txt`)
   - Simpler maintenance (no version update burden)
   - Risk: linting behavior may change when tools update
   - **Scope:** None (no changes needed)
   
3. **HYBRID - Pin some tools, float others**
   - Pin critical tools (Black, Ruff) for consistency
   - Float others (pylint, yamllint) for latest features/fixes
   - **Scope:** Small-Medium (selective pinning logic)

**Questions for Human:**
- Have there been issues with tool version drift causing CI failures?
- Who is responsible for keeping version pins up-to-date?
- Is deterministic behavior more important than getting latest fixes?

**Recommended Option:** **Option 1 (pin versions)** if `install/version_pins.py` is already maintained. Otherwise, consider deleting `version_pins.py` if it's not being used.

---

### Decision #4: Should we improve CLI usability?

**Context:** Minor enhancements like better help text, configuration files, etc.

**Options:**
1. **YES - Add usability improvements**
   - Better help text for `--only` and `--yes-i-know` flags
   - Add usage examples to `--help` output
   - Consider configuration file support (`.repo-lint.yaml`)
   - Update documentation with clear usage instructions
   - **Scope:** Small-Medium (depending on features chosen)
   
2. **NO - Keep current CLI as-is**
   - Current help text is adequate
   - Documentation can cover usage examples
   - Avoid feature creep
   - **Scope:** None (no changes needed)
   
3. **PARTIAL - Documentation only**
   - Don't change CLI code
   - Add comprehensive usage guide in `tools/repo_lint/README.md`
   - **Scope:** Small (docs only)

**Questions for Human:**
- Have users reported confusion with the CLI?
- Is configuration file support needed, or are command-line flags sufficient?
- What's the priority of this compared to other work?

**Recommended Option:** **Option 3 (docs only)** unless there's specific user feedback requesting CLI changes.

---

## Phase 3 – Polish & Minor Improvements (Awaiting Human Decisions)

### Decision #5: Should we perform code style clean-up?

**Context:** Minor style issues may exist (unused imports, line lengths, etc.).

**Options:**
1. **YES - Run linters and fix warnings**
   - Run `pylint` and `flake8` on all `tools/repo_lint` code
   - Fix warnings (unused imports, variable names, line lengths)
   - Align formatting with repository norms
   - **Scope:** Small-Medium (depending on number of issues found)
   - **Risk:** May introduce bugs if not carefully tested
   
2. **NO - Leave code as-is**
   - Current code works and is tested
   - Style fixes are low value unless blocking
   - **Scope:** None (no changes needed)
   
3. **CONDITIONAL - Only if linters fail**
   - Run linters as part of Phase 1 validation
   - Only fix if there are actual failures
   - **Scope:** Unknown until linters are run

**Questions for Human:**
- Is there a specific code style standard to enforce?
- Are linter warnings currently blocking CI?
- Is this work worth the testing/validation overhead?

**Recommended Option:** **Option 2 (leave as-is)** unless there's a specific quality issue or CI failure.

---

### Decision #6: Should we add/improve docstrings?

**Context:** Some private methods or CLI helpers may lack docstrings.

**Options:**
1. **YES - Comprehensive docstring audit**
   - Audit all public functions/methods in `repo_lint`
   - Add descriptive docstrings (Purpose, parameters, return values)
   - Align with reST or Google style per repository convention
   - **Scope:** Medium (requires reviewing entire codebase)
   
2. **NO - Current docstrings are sufficient**
   - Public APIs are documented
   - Private helpers don't need extensive docs
   - **Scope:** None (no changes needed)
   
3. **PARTIAL - Public API only**
   - Ensure all public functions/classes have docstrings
   - Skip private/internal helpers
   - **Scope:** Small

**Questions for Human:**
- What's the repository's docstring policy (public only vs. all functions)?
- Is there a specific style guide (Google, NumPy, reST)?
- Are missing docstrings causing issues for maintainers?

**Recommended Option:** **Option 3 (public API only)** if there are gaps. Otherwise **Option 2 (sufficient)**.

---

### Decision #7: Should we update documentation?

**Context:** Once code changes are done, docs should reflect them.

**Options:**
1. **YES - Update all documentation**
   - Mark FW-013 in `docs/future-work.md` (if packaging is done)
   - Add "Tools" section to main README mentioning `repo-lint`
   - Update `CONTRIBUTING.md` with `repo-lint` usage instructions
   - Ensure all doc links are current
   - **Scope:** Small (if only Phase 1), Medium (if Phase 2/3 done)
   
2. **MINIMAL - Update only what changed**
   - Document Phase 1 changes (exit codes, new behaviors)
   - Skip comprehensive doc overhaul
   - **Scope:** Small
   
3. **DEFER - Wait until all phases complete**
   - Don't update docs until Phase 2/3 work is decided
   - Avoid churn from multiple doc updates
   - **Scope:** None (no changes needed now)

**Questions for Human:**
- Should Phase 1 changes be documented immediately?
- Are there specific docs that are out-of-date or incomplete?
- Who reviews/approves documentation changes?

**Recommended Option:** **Option 2 (minimal)** - document Phase 1 changes now, defer comprehensive updates until Phase 2/3 decisions are made.

---

### Decision #8: Should we add integration tests for runners?

**Context:** Current tests are isolated unit tests. Integration tests could catch cross-cutting issues.

**Options:**
1. **YES - Add integration tests**
   - Create test repos with known violations in multiple languages
   - Run `repo_lint check` end-to-end
   - Verify combined output and error handling
   - **Scope:** Medium (requires test fixtures, multi-language setup)
   
2. **NO - Current unit tests are sufficient**
   - Unit tests cover individual runner behavior
   - Integration testing can be manual or via CI
   - **Scope:** None (no changes needed)
   
3. **PARTIAL - Add one integration test as example**
   - Single test covering Python + Bash + Perl
   - Demonstrates pattern without full coverage
   - **Scope:** Small

**Questions for Human:**
- Have there been bugs that unit tests didn't catch?
- Is there value in automated integration tests vs. manual testing?
- What's the maintenance burden of keeping integration tests updated?

**Recommended Option:** **Option 2 (sufficient)** unless there's evidence that unit tests are missing important scenarios.

---

## Summary of Decisions Needed

| # | Decision | Phase | Priority | Recommended |
|---|----------|-------|----------|-------------|
| 1 | Make `repo_lint` installable package | Phase 2 | Medium | Need input |
| 2 | Integrate naming-and-style enforcement | Phase 2 | Medium | Keep separate (unless naming drift is a problem) |
| 3 | Pin external tool versions | Phase 2 | Low | Pin versions (if `version_pins.py` is maintained) |
| 4 | Improve CLI usability | Phase 2 | Low | Docs only (unless user feedback) |
| 5 | Code style clean-up | Phase 3 | Low | Leave as-is (unless CI fails) |
| 6 | Add/improve docstrings | Phase 3 | Low | Public API only (if gaps exist) |
| 7 | Update documentation | Phase 3 | Low | Minimal (document Phase 1 now) |
| 8 | Add integration tests | Phase 3 | Low | Current tests sufficient |

---

## Next Steps

1. **Human reviews this document** and provides decisions for each item
2. **Agent proceeds with approved Phase 2/3 work** in separate PRs
3. **Documentation is updated** to reflect completed work
4. **Issue #160 is closed** when all approved phases are complete

---

## Contact

**For questions or to provide decisions, mention @m1ndn1nj4 in Issue #160.**

---

*This document created per new requirement from human on 2025-12-31.*
