# PR #297 Next Steps

## Current Session (2026-01-08) - Review Comment Addressed

Fixed critical bug in Option B that was mangling nested lists.

### What Was Fixed

1. **Nested list bug** (commit: e76d00e)
   - Reverted conformance/README.md to correct state
   - Fixed `_collect_list_item()` to stop when ANY new list item detected
   - Added `test_version_history_nested_list_structure` regression test
   - All 61 tests pass
   - All Python linting passes (exit 0)

### Remaining Work

Per user instructions, continue with controlled batch processing:

1. **Safety trial on conformance/README.md**
   - Run Option B
   - Verify Version History structure preserved
   - Check other long paragraphs wrapped correctly

2. **Apply MD013 Fixes in Controlled Batches**
   Only proceed if safety trial succeeds:
   - Batch 1: 1-3 files
   - Batch 2: 5-10 files
   - Batch 3: 25 files
   - For each batch:
     - Clean working tree
     - Run Option B on batch
     - Inspect representative diffs
     - Run markdown linting
     - Commit with batch number

3. **Final Verification**
   - Run: `repo-lint check --ci`
   - Ensure PR is clean and resumable

## Files to Work With

- Scripts: `scripts/fix_md013_line_length_option_a.py`, `scripts/fix_md013_line_length_option_b.py`
- Tests: `scripts/tests/test_fix_md013_line_length_option_a.py`, `scripts/tests/test_fix_md013_line_length_option_b.py`
