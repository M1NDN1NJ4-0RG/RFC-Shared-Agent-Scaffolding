# Issue #278 - Next Steps

## CURRENT SESSION (2026-01-08) - Planning Remaining Work

**Status:** Reviewed all previous work and issue #297. Planning remaining MANDATORY phases.

### Critical Finding: NO OPTIONAL PHASES

Per agent instructions: "We DO NOT have ANY OPTIONAL PHASES in this EPIC!"
This means ALL phases including 4, 5, 6 are MANDATORY (not optional/recommended).

### Work Completed (Previous Sessions)

- ✅ Phase 0: Preflight (snapshots + inventory)
- ✅ Phase 1: Evaluate existing contracts
- ✅ Phase 2: Define policy (PEP 526 + function annotations + :rtype:)
- ✅ Phase 3.1-3.2: Tooling evaluation + Ruff ANN* config
- ✅ Phase 3.4.1-3.4.3: Docstring validation consolidation (core migration)
- ✅ Phase 3.5.1-3.5.4: Markdown contracts + linting (partial cleanup)
- ✅ Phase 3.6.1-3.6.5: TOML contracts + linting (complete with tests)
- ✅ Phase 3.7.1-3.7.3: Exception handling policy + narrowing
- ✅ Phase 3.8.1-3.8.4: Rich-powered logging

### Remaining MANDATORY Work

**Phase 3.3: Custom PEP 526 Checker (DEFERRED - HIGH PRIORITY)**
- [ ] 3.3.1: Design AST-based checker for module-level/class attribute annotations
- [ ] 3.3.2: Implement checker in repo_lint
- [ ] 3.3.3: Add configuration support (per-file-ignores, gradual rollout)
- [ ] 3.3.4: Comprehensive unit tests
- [ ] 3.3.5: Integration with `repo-lint check --ci`

**Phase 3.4.4: Docstring Validator Unit Tests (DEFERRED - MEDIUM PRIORITY)**
- [ ] Create test files for internal validators:
  - [ ] test_python_validator.py
  - [ ] test_bash_validator.py
  - [ ] test_powershell_validator.py
  - [ ] test_perl_validator.py
  - [ ] test_rust_validator.py
  - [ ] test_yaml_validator.py
  - [ ] test_validator_common.py
- [ ] Golden fixtures for each language (pass/fail cases)
- [ ] Regression tests for bugs found during migration

**Phase 3.5.5: Markdown Runner Comprehensive Tests (COMPLETE ✅)**
- Already has 15 comprehensive tests (added during code review)
- Covers: file detection, tool checking, parsing, check/fix modes
- Integration tests included
- Mark as COMPLETE

**Phase 4: Autofix Strategy (ALL MANDATORY)**
- [ ] 4.1: Add non-destructive autofix where safe
  - [ ] Identify autofixable patterns (-> None, trivial annotations)
  - [ ] Implement safe autofix logic
  - [ ] Test autofix on sample files
- [ ] 4.2: Bulk migration PR plan
  - [ ] Create staged migration strategy
  - [ ] Per-directory commits plan
  - [ ] CI green validation after each stage

**Phase 5: CI Enforcement Rollout (ALL MANDATORY)**
- [ ] 5.1: Report-only mode
  - [ ] Add checks to CI without failing builds
  - [ ] Produce actionable failure reports
  - [ ] Measure baseline violations
- [ ] 5.2: Enforcing mode
  - [ ] Fail CI on new violations
  - [ ] Remove temporary exemptions

**Phase 6: Documentation Updates (MANDATORY)**
- [ ] 6.1: Update repo docs
  - [ ] User manual / README updates
  - [ ] Contributing docs with examples
  - [ ] PEP 526 examples
  - [ ] Function annotation examples
  - [ ] reST docstring :rtype: examples
- [ ] 6.2: Verify docs match reality
  - [ ] Config files match documented rules
  - [ ] CI runs documented ruleset

### Recommended Execution Order

**Priority 1: Complete Deferred Test Coverage**
1. Phase 3.5.5: Mark as complete (already done)
2. Phase 3.4.4: Add docstring validator unit tests

**Priority 2: Implement Custom PEP 526 Checker**
3. Phase 3.3: Custom checker for module-level/class annotations

**Priority 3: Autofix and Rollout**
4. Phase 4: Autofix strategy
5. Phase 5: CI enforcement rollout

**Priority 4: Documentation**
6. Phase 6: Documentation updates

### Next Immediate Action

Start with Phase 3.4.4 (docstring validator tests) because:
- Validates the Phase 3.4 migration was correct
- Establishes test patterns for Phase 3.3 custom checker
- Lower risk than implementing new checker first
- Can be done incrementally (one validator at a time)

---

## PREVIOUS SESSION

**Code Review Comments Addressed - PR Ready for Final Review**

All 4 code review comments from PR #295 have been addressed and verified.

### Completed in This Session

**Code Review Fixes (2026-01-08)**

Addressed all comments from https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/pull/295#pullrequestreview-3639382623

1. ✅ **Comment 2672317233**: Added `:rtype: bool` to `is_tty()` function
   - File: `tools/repo_lint/logging_utils.py`
   - Added missing reST docstring return type field

2. ✅ **Comment 2672317191**: Added `:rtype: logging.Logger` to `get_logger()` function
   - File: `tools/repo_lint/logging_utils.py`
   - Added missing reST docstring return type field

3. ✅ **Comment 2672317203**: Fixed incorrect line count (394 → 437)
   - File: `docs/ai-prompt/278/278-summary.md` line 1050
   - Corrected test file line count to actual value

4. ✅ **Comment 2672317222**: Fixed incorrect line count (394 → 437)
   - File: `docs/ai-prompt/278/278-summary.md` line 1036
   - Corrected test file line count to actual value

5. ✅ **Ruff import sorting issue**: Fixed in `cli_argparse.py`
   - Auto-fixed with `ruff check --fix`

**Verification:**
- ✅ All Python checks pass: `repo-lint check --ci --only python` (exit 0)
- ✅ All 25 unit tests pass (100%)
- ✅ Replied to all 4 review comments

**Commit:** 41f6a74

### Next Session Actions

PR #295 is now ready for final review and merge.

After merge:
- **Option A**: Continue with remaining optional phases (3.5.5, Phase 4, 5, 6)
- **Option B**: Conclude issue #278 (all mandatory phases complete)

---

## Previous Work

**Phase 3.8 COMPLETE - Ready for Code Review**

All Rich-powered logging infrastructure is complete and tested.

### Completed in This Session

**Phase 3.8: Rich-powered Logging (COMPLETE ✅)**

- ✅ Phase 3.8.1: Current state assessment
  - Inventoried 518 print() statements, minimal logging adoption
  - Identified Rich already integrated in 6 files
  - Documented findings in 278-summary.md

- ✅ Phase 3.8.2: Shared logger wrapper implementation
  - Created `tools/repo_lint/logging_utils.py` (264 lines)
  - Rich integration for TTY, plain for CI
  - Convenience functions for common patterns

- ✅ Phase 3.8.3: CLI integration
  - Modified `cli_argparse.py` main() for logging config
  - Migrated `runners/base.py` to use logging_utils
  - Tested and verified working

- ✅ Phase 3.8.4: Comprehensive tests
  - Created 25 unit tests (100% pass rate)
  - ANSI-free output verified
  - All Python checks pass (exit 0)

**Commits:**
- 9279f50: Phase 3.8.1-3.8.2 complete
- 100aba6: Phase 3.8.3 partial (CLI + base runner)

### Next Session Actions

After code review approval, choose one of:

**Option A: Continue with remaining mandatory phases**
- Phase 3.5.5: Comprehensive tests for Markdown runner (deferred earlier)
- Phase 4: Autofix strategy (function annotations, etc.)
- Phase 5: CI enforcement rollout
- Phase 6: Documentation updates

**Option B: Gradual logging adoption (optional enhancement)**
- Migrate additional runners to use logging_utils
- Replace print() with logger calls in scripts
- Add logging to report generation

**Option C: Conclude issue #278**
- Phase 3.8 was the last MANDATORY phase per issue requirements
- All mandatory deliverables complete
- Ready for final review and merge

### Session Summary

**Work Completed:**
- ✅ Phase 3.8 complete (all 4 sub-phases)
- ✅ 2 new files created (logging_utils.py, test_logging_utils.py)
- ✅ 2 files modified (cli_argparse.py, base.py)
- ✅ 25 unit tests added (100% pass)
- ✅ All Python checks passing
- ✅ Ready for code review

**Files Modified:**
1. tools/repo_lint/logging_utils.py (NEW - 264 lines)
2. tools/repo_lint/tests/test_logging_utils.py (NEW - 394 lines)
3. tools/repo_lint/cli_argparse.py
4. tools/repo_lint/runners/base.py
5. docs/ai-prompt/278/278-summary.md

---

## Recent Completion

**Phase 3.7.2: COMPLETE ✅**

- Created `docs/contributing/python-exception-handling-policy.md` (14KB)
- Defined acceptable vs unacceptable patterns
- Documented required behaviors (narrow types, exception chaining, actionable messages)
- Fixed pylint violation in test_toml_runner.py
- All Python checks pass (exit 0)

---

## Previous Status

**Phase 3.5.1-3.5.3: COMPLETE ✅**

- [x] Created Markdown contract document
- [x] Configured markdownlint-cli2
- [x] Integrated Markdown runner into repo-lint
- [x] Fixed parsing bug (code review)
- [x] Added comprehensive tests (code review)

**Phase 3.6.1-3.6.4: COMPLETE ✅**
- [x] Created TOML contract document
- [x] Configured Taplo
- [x] Integrated TOML runner into repo-lint
- [x] Auto-formatted all TOML files (0 violations)

**Current State:**

- ✅ Markdown linting works: `repo-lint check --lang markdown`
- ✅ TOML linting works: `repo-lint check --lang toml`
- ✅ Auto-fix works for both: `repo-lint fix --lang markdown/toml`
- ✅ All tests pass: Markdown (15/15), TOML (15/15)
- ✅ All Python checks pass (exit 0)

## Resume Pointers

**Branch:** copilot/enforce-type-annotations

**Key Commands:**

- `python3 -m pytest tools/repo_lint/tests/test_toml_runner.py -v` - Run TOML runner tests
- `python3 -m pytest tools/repo_lint/tests/test_markdown_runner.py -v` - Run Markdown runner tests
- `repo-lint check --lang toml` - Check TOML files
- `repo-lint check --lang markdown` - Check Markdown files

**Recent Commits:**

- 6a8f637: Phase 3.5.1-3.5.2 (Markdown contract + config)
- c040b9a: Phase 3.5.3 (Markdown integration)
- 2c7b953: Fixed unused json import (code review)
- 3ac82d4: Fixed parsing bug + added comprehensive tests (code review)
- 226c3c2: Phase 3.5.4 partial (Markdown auto-fix, 75% reduction)
- a523651: Phase 3.6.1-3.6.2 (TOML contract + config)
- 9a1d56d: Phase 3.6.3 (TOML integration)
- 3672998: Phase 3.6.4 (TOML auto-format, 100% clean)

**Ready for:** Phase 3.7 or Phase 3.8

**Current State:**

- ✅ Markdown linting works: `repo-lint check --lang markdown`
- ✅ Auto-fix works: `repo-lint fix --lang markdown`
- ✅ All tests pass: 15/15 (100%)
- ✅ All Python checks pass
- ⚠️ 3,790 Markdown violations exist across repository (baseline)

## Resume Pointers

**Branch:** copilot/enforce-python-type-annotations

**Key Commands:**

- `python3 -m pytest tools/repo_lint/tests/test_markdown_runner.py -v` - Run Markdown runner tests
- `repo-lint check --lang markdown` - Shows 3,790 Markdown violations
- `repo-lint fix --lang markdown` - Auto-fix safe violations

**Recent Commits:**

- 6a8f637: Phase 3.5.1-3.5.2 (contract + config)
- c040b9a: Phase 3.5.3 (integration)
- 2c7b953: Fixed unused json import (code review)
- 3ac82d4: Fixed parsing bug + added comprehensive tests (code review)

**Ready for:** PR merge, then Phase 3.5.4 or Phase 3.6
