# Tests for repo_lint Package

This directory contains unit tests for the `repo_lint` package.

## Running Tests

Run all tests from the repository root:

```bash
python3 tools/repo_lint/tests/test_python_runner.py -v
```

Or if pytest is installed:

```bash
pytest tools/repo_lint/tests/ -v
```

## Test Coverage

### test_python_runner.py

Tests for the Python runner implementation, validating Phase 0 Item 0.9.1 compliance:

- **TestRuffCheckFix**: Tests the split check/fix behavior
  - `test_check_uses_no_fix`: Verifies `_run_ruff_check()` uses `--no-fix` (non-mutating)
  - `test_fix_uses_fix_flag`: Verifies `_run_ruff_fix()` uses `--fix` (safe fixes only)
  - `test_check_handles_violations`: Tests violation parsing in check mode
  - `test_check_handles_unsafe_fixes_warning`: Tests unsafe fixes warning in check context
  - `test_fix_handles_unsafe_fixes_warning`: Tests unsafe fixes warning in fix context
  - `test_fix_command_sequences_black_and_ruff`: Tests that `fix()` calls both formatters

- **TestParseRuffOutput**: Tests the `_parse_ruff_output()` helper method
  - `test_parse_empty_output`: Verifies empty output handling
  - `test_parse_check_context_unsafe_message`: Tests check context message formatting
  - `test_parse_fix_context_unsafe_message`: Tests fix context message formatting
  - `test_parse_filters_found_lines`: Verifies "Found N errors" lines are filtered

## Adding New Tests

When adding new functionality to `repo_lint`, add corresponding tests:

1. Create test class inheriting from `unittest.TestCase`
2. Add descriptive docstrings following repository conventions
3. Use `unittest.mock` to avoid executing actual linters
4. Verify command-line arguments and behavior, not implementation details
5. Run tests to ensure they pass before committing

## Test Philosophy

- Tests use mocking to avoid dependencies on installed tools
- Tests verify **behavior** (what flags are passed, what methods are called)
- Tests do **not** test implementation details (internal variable names, etc.)
- Tests align with EPIC requirements (Phase 0 decisions)
