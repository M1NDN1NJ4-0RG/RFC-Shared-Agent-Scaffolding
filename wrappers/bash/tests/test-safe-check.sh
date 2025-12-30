#!/usr/bin/env bash
#
# test-safe-check.sh - Tests for safe-check.sh contract verification script
#
# DESCRIPTION:
#   Validates that safe-check.sh correctly verifies the safe-run contract.
#   The safe-check script is a smoke test that validates success/failure
#   artifact creation and archiving behavior.
#
# TEST COVERAGE:
#   - safe-check.sh exits 0 when all contract checks pass
#   - Tests run in isolated temp directory
#   - Verifies Rust binary discovery works
#
# USAGE:
#   ./test-safe-check.sh
#
# INPUTS:
#   Arguments:
#     None (test script runs all tests)
#
#   Environment Variables:
#     None (discovers Rust binary automatically)
#
# OUTPUTS:
#   Exit Codes:
#     0    All tests passed
#     1    One or more tests failed
#     127  Rust binary not found
#
#   Stderr:
#     Test results (PASS/FAIL per test, summary)
#
# EXAMPLES:
#   # Run all safe-check tests
#   ./test-safe-check.sh
#
# CONTRACT REFERENCES:
#   - safe-check.sh tests: success artifacts, failure artifacts, archiving
#   - Related: safe-run.sh, safe-archive.sh
#
# SEE ALSO:
#   - lib.sh: Test framework
#   - ../scripts/safe-check.sh: Script being tested
#

set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

# Discover paths
ROOT="$(cd .. && pwd)"

# Compute repo root and find Rust binary for wrapper discovery
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
if [ -x "$REPO_ROOT/dist/linux/x86_64/safe-run" ]; then
	SAFE_RUN_BIN_PATH="$REPO_ROOT/dist/linux/x86_64/safe-run"
elif [ -x "$REPO_ROOT/rust/target/release/safe-run" ]; then
	SAFE_RUN_BIN_PATH="$REPO_ROOT/rust/target/release/safe-run"
else
	echo "ERROR: Rust binary not found for tests" >&2
	echo "  Searched: $REPO_ROOT/dist/linux/x86_64/safe-run" >&2
	echo "  Searched: $REPO_ROOT/rust/target/release/safe-run" >&2
	exit 127
fi

# test_safe_check_ok - Verify safe-check passes in healthy environment
# Creates temp dir, copies scripts, runs safe-check with binary override
test_safe_check_ok() {
	local tmp
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mkdir -p scripts .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
		cp -f "$ROOT/scripts/"*.sh scripts/
		chmod +x scripts/*.sh
		# Set SAFE_RUN_BIN so the wrapper can find Rust binary in isolated temp dir
		SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" scripts/safe-check.sh >/dev/null
	)
}

t "safe-check: exits 0 on healthy environment" test_safe_check_ok
summary
