# Issue #278 - Next Steps

## NEXT

**Phase 3.6.5: Comprehensive Tests for TOML Runner (NEXT TASK)**

Create comprehensive unit tests for the TOML runner following the pattern established by test_markdown_runner.py (15 tests, 100% pass rate).

**Required Tests:**

1. `test_has_files_detects_toml` - Verify .toml file detection
2. `test_has_files_returns_false_when_no_files` - Empty file list handling
3. `test_check_tools_detects_missing_tool` - Missing Taplo detection
4. `test_check_tools_returns_empty_when_installed` - Tool available check
5. `test_run_taplo_with_config_file` - Config file usage verification
6. `test_run_taplo_fix_mode` - Verify fix mode uses `taplo fmt` (not --check)
7. `test_run_taplo_check_mode_uses_check_flag` - Verify check mode uses `--check`
8. `test_parse_taplo_output_single_violation` - Single violation parsing
9. `test_parse_taplo_output_multiple_violations` - Multiple violations
10. `test_parse_taplo_output_skips_info_lines` - Skip INFO/WARN lines
11. `test_parse_taplo_output_handles_stderr` - stderr output parsing
12. `test_parse_taplo_output_empty_output` - Empty output handling
13. `test_run_taplo_empty_file_list` - Empty file list returns success
14. `test_check_returns_violations` - Check mode integration test
15. `test_fix_applies_fixes` - Fix mode integration test

**Implementation Steps:**
1. Create `tools/repo_lint/tests/test_toml_runner.py`
2. Follow test_markdown_runner.py structure exactly
3. Use `side_effect` for multiple subprocess calls (git + taplo)
4. Mock `command_exists` for tool detection tests
5. Mock `subprocess.run` for Taplo execution
6. Run tests: `python3 -m pytest tools/repo_lint/tests/test_toml_runner.py -v`
7. Ensure 100% pass rate (15/15 tests)

**After Phase 3.6.5:**
- Phase 3.6 will be COMPLETE
- Move to Phase 3.7 (Reduce overly-broad exception handling) or Phase 3.8 (Rich logging)

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
