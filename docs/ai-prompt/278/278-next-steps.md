# Issue #278 - Next Steps

## NEXT

**Phase 3.7.3 COMPLETE - Ready for Code Review**

All 38 broad exception handlers have been systematically narrowed or documented with policy references.

### Completed in This Session

**Phase 3.7.3: Exception Handler Narrowing Implementation**

- ✅ Priority 1: Library Code (6 instances) - All fixed
- ✅ Priority 2: Tooling Wrappers (11 instances) - All fixed
- ✅ Priority 3: CLI Boundaries (17 instances) - All documented

**Details:**
- Narrowed 21 broad exception handlers to specific exception types
- Added policy reference comments to 17 CLI boundary handlers
- All changes tested and passing: `repo-lint check --ci --only python` (exit 0)

### Next Session Actions

After code review approval:

**Option A: Phase 3.8 - Rich-powered logging (MANDATORY)**
- Assess current logging patterns
- Create shared logger wrapper with Rich integration
- Adopt across repo-lint
- Add comprehensive tests

**Option B: Continue with remaining phases**
- Phase 3.5.5: Comprehensive tests for Markdown runner (deferred)
- Phase 3.6.5: Already complete ✅
- Phase 4: Autofix strategy
- Phase 5: CI enforcement rollout

### Session Summary

**Work Completed:**
- ✅ Phase 3.7.3 implementation complete
- ✅ 11 files modified
- ✅ 38 exception handlers addressed
- ✅ All Python checks passing
- ✅ Ready for code review

**Files Modified:**
1. tools/repo_lint/runners/base.py
2. tools/repo_lint/docstrings/validator.py
3. tools/repo_lint/docstrings/helpers/bash_treesitter.py
4. scripts/docstring_validators/helpers/bash_treesitter.py
5. scripts/add_future_annotations.py
6. wrappers/python3/run_tests.py
7. wrappers/python3/scripts/preflight_automerge_ruleset.py
8. tools/repo_lint/install/install_helpers.py
9. tools/repo_lint/cli.py
10. tools/repo_lint/cli_argparse.py
11. scripts/bootstrap_watch.py

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
