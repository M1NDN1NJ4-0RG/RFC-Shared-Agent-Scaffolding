# Issue #278 - Next Steps

## NEXT

**Phase 3.5.4: PARTIALLY COMPLETE - Moving to Phase 3.6**

Markdown auto-fix completed:
- ✅ Reduced from 7,501 to 1,888 violations (75% reduction, 5,613 auto-fixed)
- ⚠️ Remaining 1,888 violations are mostly MD013/line-length requiring manual review
- Decision: Defer remaining line-length fixes to future cleanup sessions (not blocking)

**Phase 3.6: TOML Contracts + Linting Support (START NOW)**

Following the same pattern as Markdown (Phase 3.5), implement TOML linting:

1. **Phase 3.6.1:** Define TOML contract (docs/contributing/toml-contracts.md)
   - Document formatting/indentation conventions
   - Define key ordering, whitespace rules, quoting policy
   - Set scope (all `*.toml` files, exclusions if any)

2. **Phase 3.6.2:** Configure Taplo (taplo.toml)
   - Map contract rules to Taplo configuration
   - Test baseline violations

3. **Phase 3.6.3:** Integrate TOML runner into repo-lint
   - Create tools/repo_lint/runners/toml_runner.py
   - Add to CLI (--lang toml, --only toml)
   - Support check and fix modes

4. **Phase 3.6.4:** Repo baseline cleanup
   - Run auto-fix where safe
   - Manual fixes if needed

5. **Phase 3.6.5:** Comprehensive tests
   - Create test_toml_runner.py
   - Follow same pattern as test_markdown_runner.py

**Locked Decision:** Use **Taplo** for TOML linting/formatting (from issue #278)

---

## Previous Status

**Phase 3.5.1-3.5.3: COMPLETE ✅**

- [x] Created Markdown contract document
- [x] Configured markdownlint-cli2
- [x] Integrated Markdown runner into repo-lint
- [x] Fixed parsing bug (code review)
- [x] Added comprehensive tests (code review)

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
