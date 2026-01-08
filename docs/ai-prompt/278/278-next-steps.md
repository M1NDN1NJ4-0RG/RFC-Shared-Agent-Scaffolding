# Issue #278 - Next Steps

## NEXT

**Phase 3.5.4: Repo Baseline Cleanup (Markdown)**

The Markdown runner is integrated and working, but there are 3,790 violations to fix. Options:

1. **Gradual rollout approach (RECOMMENDED):**
   - Add per-file-ignores to exclude all current violations
   - Enforce on new/changed files only
   - Fix violations incrementally in dedicated cleanup sessions

2. **Auto-fix what's safe:**
   - Run `repo-lint fix --lang markdown` to auto-fix deterministic violations
   - Manually fix remaining violations (line length, language tags, etc.)

**Decision needed:** How to handle the 3,790 existing violations?

**After 3.5.4, continue with:**

1. Phase 3.5.5: Comprehensive tests for Markdown runner
2. Phase 3.6: TOML contracts + linting support (similar to Markdown)
3. Phase 3.7: Reduce overly-broad exception handling
4. Phase 3.8: Rich-powered logging
5. Phase 3.3: Implement PEP 526 checker (deferred until after 3.5-3.8)

---

## Previous Status

**Phase 3.5.1-3.5.3: COMPLETE ✅**
- [x] Created Markdown contract document
- [x] Configured markdownlint-cli2
- [x] Integrated Markdown runner into repo-lint
- [x] All tests passing

**Current State:**
- ✅ Markdown linting works: `repo-lint check --lang markdown`
- ✅ Auto-fix works: `repo-lint fix --lang markdown`
- ⚠️ 3,790 violations exist across repository (baseline)
- ✅ New requirements addressed (Markdown Best Practices, 120 char line length)

## Resume Pointers

**Branch:** copilot/enforce-python-type-annotations

**Key Commands:**
- `repo-lint check --ci` - All checks pass except Markdown violations
- `repo-lint check --lang markdown` - Shows 3,790 Markdown violations
- `repo-lint fix --lang markdown` - Auto-fix safe violations

**Recent Commits:**
- 6a8f637: Phase 3.5.1-3.5.2 (contract + config)
- c040b9a: Phase 3.5.3 (integration)

**Ready for:** Phase 3.5.4 decision + implementation, or Phase 3.5.5 (tests), or move to Phase 3.6 (TOML)
