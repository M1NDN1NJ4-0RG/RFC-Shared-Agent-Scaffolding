# PR #297 Next Steps

## Immediate Actions Required

1. **Address unresolved PR review comments** (from PR review #3640238927):
   - scripts/fix_md013_line_length_option_b.py:12 - Docstring mismatch with implementation
   - scripts/fix_md013_line_length_option_b.py:1-394 - Missing test coverage
   - scripts/fix_md013_line_length_option_b.py:219-222 - Magic string "__DO_NOT_TOUCH_LIST_ITEM__" issue
   - scripts/fix_md013_line_length_option_b.py:323-324 - Empty payload wrapping check
   - scripts/fix_md013_line_length_option_a.py:268 - Empty file edge case
   - scripts/fix_md013_line_length_option_a.py:1-309 - Missing test coverage
   - scripts/fix_md013_line_length_option_b.py:353 - Empty file edge case

2. **Fix repo-lint violations** (MANDATORY before commit):
   - pylint R1737: Use 'yield from' in both scripts
   - Add complete module docstrings with Purpose, Environment Variables, Examples, Exit Codes sections
   - Add :param and :returns to all function docstrings

3. **Create comprehensive unit tests** for both scripts

## Detailed Resume Instructions

### Files to open:
- `/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/fix_md013_line_length_option_a.py`
- `/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/fix_md013_line_length_option_b.py`

### Commands to run:
1. Fix violations: `repo-lint check --ci` until exit 0
2. Run tests after creating them: `pytest scripts/tests/test_fix_md013_*.py`
