# Issue #278 - Next Steps

## NEXT

**All Copilot Code Review Comments Addressed**

All 3 code review comments from PR #293 have been fixed and tested. The PR is ready for review approval and merge.

### Session Summary

**Completed:**
- ✅ Fixed all 3 Copilot Code Review comments
- ✅ Comment 1: Fixed NameError risk in exception handling example 1
- ✅ Comment 2: Added explanatory comment for deferred version check
- ✅ Comment 3: Fixed NameError risk in exception handling example 3
- ✅ Auto-formatted markdown policy document
- ✅ Verified all changes with pre-commit gate

**Status:**
- All Python checks passing (black, ruff, pylint, docstrings)
- Only Markdown baseline violations remain (not in scope per user requirement)
- PR #293 ready for review and merge

### Next Session Actions

After PR #293 is merged:

**Phase 3.7.3: Implementation Plan for Exception Handler Narrowing**

Based on the Phase 3.7.1 inventory, we identified 38 broad exception handlers requiring attention. We need to create an implementation plan and then execute the fixes.

### Execution Strategy

**Priority 1: Library Code (6 instances) - MUST FIX**

These are the highest priority because they can hide bugs and make debugging difficult:

1. `tools/repo_lint/runners/base.py:302` - Tool method execution
2. `tools/repo_lint/docstrings/validator.py:55` - File read error
3. `tools/repo_lint/docstrings/helpers/bash_treesitter.py:128` - Bash parsing
4. `scripts/docstring_validators/helpers/bash_treesitter.py:128` - Duplicate (mark for removal)
5. `scripts/add_future_annotations.py:258` - File processing
6. `wrappers/python3/run_tests.py:162` - Actually CLI boundary (add comment)

**Priority 2: Tooling Wrappers (11 instances) - SHOULD FIX**

Excluding doctor.py (5 instances which are acceptable), we have:

7-14. `wrappers/python3/scripts/preflight_automerge_ruleset.py` (8 instances) - JSON parsing + HTTP
15. `tools/repo_lint/install/install_helpers.py:282` - Directory removal

**Priority 3: Documentation (17 instances) - DOCUMENT PATTERN**

CLI boundary handlers are acceptable per policy, but should have inline comments referencing the policy.

### Implementation Steps

1. **Create exceptions module** (if needed):
   - [ ] Create `tools/repo_lint/exceptions.py` with base exceptions
   - [ ] Define `RepoLintError`, `MissingToolError`, `ConfigurationError`

2. **Fix library code** (Priority 1):
   - [ ] Fix base.py:302 (narrow to subprocess + file errors)
   - [ ] Fix validator.py:55 (narrow to OSError + UnicodeDecodeError)
   - [ ] Fix bash_treesitter.py:128 (narrow to tree-sitter exceptions)
   - [ ] Remove duplicate bash_treesitter.py in scripts/
   - [ ] Fix add_future_annotations.py:258 (narrow to file + syntax errors)
   - [ ] Add comment to run_tests.py:162 (acceptable CLI boundary)

3. **Fix tooling wrappers** (Priority 2):
   - [ ] Fix preflight_automerge_ruleset.py (narrow JSON to JSONDecodeError)
   - [ ] Fix install_helpers.py:282 (narrow to OSError)

4. **Document CLI boundaries** (Priority 3):
   - [ ] Add policy reference comments to cli.py handlers
   - [ ] Add policy reference comments to cli_argparse.py handlers

### Testing Requirements

For each fix:
- [ ] Verify existing tests still pass
- [ ] Add new test cases if exception behavior changed
- [ ] Run `repo-lint check --ci` to ensure no regressions

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
