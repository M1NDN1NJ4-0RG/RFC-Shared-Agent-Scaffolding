#!/usr/bin/env bash
#
# run-all.sh - Test suite runner for Bash scripts
#
# DESCRIPTION:
#   Discovers and runs all test-*.sh files in the current directory.
#   Each test file runs in a fresh Bash process to avoid state leakage.
#   Collects results and exits with failure if any test fails.
#
# USAGE:
#   ./run-all.sh
#
# INPUTS:
#   Arguments: None
#   Files: All test-*.sh files in current directory
#
# OUTPUTS:
#   Exit Codes:
#     0  All tests passed
#     1  One or more test files failed
#
#   Stdout:
#     (delegated to test files)
#
#   Stderr:
#     "==> Running <file>" - progress indicator per test file
#     (test output from individual files)
#
# DISCOVERY:
#   Runs all files matching pattern: ./test-*.sh
#   Each test file must be executable (chmod +x) or run via bash
#
# ISOLATION:
#   Each test file runs in a separate Bash process (via bash <file>)
#   Prevents environment variable pollution between tests
#   Prevents function/variable collisions
#
# PLATFORM COMPATIBILITY:
#   - Linux: Bash 4.0+
#   - macOS: Bash 3.2+
#   - Windows: Git Bash, WSL
#
# EXAMPLES:
#   # Run all tests
#   ./run-all.sh
#
#   # Run from parent directory
#   bash tests/run-all.sh
#
#   # CI usage
#   cd tests && ./run-all.sh || exit 1
#
# SEE ALSO:
#   - lib.sh: Test harness library
#   - test-*.sh: Individual test files
#   - ../run-tests.sh: Top-level CI entry point
#
# IMPLEMENTATION NOTES:
# - Uses 'set -euo pipefail' for strict error handling
# - Tracks cumulative exit status across test files
# - Sources lib.sh for test framework (in test files, not here)
#

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
# shellcheck disable=SC1091  # lib.sh is sourced at runtime
source "./lib.sh"

# Run each test file in a fresh bash to avoid state leakage.
# Accumulate failures in status variable
status=0
for tf in ./test-*.sh; do
	[[ -f "$tf" ]] || continue # Skip if no test files match pattern
	echo "==> Running $tf" >&2
	if ! bash "$tf"; then
		status=1 # Mark failure but continue running other tests
	fi
done

# Each test file prints its own summary; this is a belt-and-suspenders exit.
exit "$status"
