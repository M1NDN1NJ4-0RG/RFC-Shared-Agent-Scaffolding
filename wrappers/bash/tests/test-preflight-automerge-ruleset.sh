#!/usr/bin/env bash
#
# test-preflight-automerge-ruleset.sh - Tests for preflight-automerge-ruleset.sh
#
# DESCRIPTION:
#   Tests the GitHub Ruleset verification script using a mock gh API.
#   Validates exit codes for success, failure, and auth error scenarios.
#
# TEST COVERAGE:
#   - Precheck OK (exit 0): Ruleset active, targets default, has contexts
#   - Missing contexts (exit 1): Required contexts not in ruleset
#   - Enforcement inactive (exit 1): Ruleset not active
#   - No default branch (exit 1): Ruleset doesn't target ~DEFAULT_BRANCH
#   - Auth error (exit 2): GitHub API auth/permission failure
#
# USAGE:
#   ./test-preflight-automerge-ruleset.sh
#
# INPUTS:
#   Arguments:
#     None (test script runs all tests)
#
#   Environment Variables:
#     GH_SCENARIO (internal) Used by mock gh to return specific JSON responses
#
# OUTPUTS:
#   Exit Codes:
#     0  All tests passed
#     1  One or more tests failed
#
#   Stderr:
#     Test results (PASS/FAIL per test, summary)
#
# EXAMPLES:
#   # Run all preflight tests
#   ./test-preflight-automerge-ruleset.sh
#
# TEST STRATEGY:
#   - Creates mock gh command that returns canned JSON responses
#   - Uses GH_SCENARIO env var to control mock behavior
#   - Tests all exit code paths (0, 1, 2)
#
# SEE ALSO:
#   - lib.sh: Test framework
#   - ../scripts/preflight-automerge-ruleset.sh: Script being tested
#

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091  # lib.sh is sourced at runtime
source "./lib.sh"

# Discover paths
ROOT="$(cd .. && pwd)"
PREF="${ROOT}/scripts/preflight-automerge-ruleset.sh"

# Create mock gh command for testing
#
# Arguments:
#   $1 - Directory to place mock binary
#
# Returns:
#   0 on success
#
# Globals:
#   None
#
# Outputs:
#   Creates executable mock gh script in specified directory
#
# Side Effects:
#   Creates file ${dir}/gh with execute permissions
#
# Purpose:
#   Mock responds based on GH_SCENARIO env var for test isolation
make_mock_gh() {
	local dir="$1"
	cat >"${dir}/gh" <<'GH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "api" ]]; then
  echo "unsupported gh subcommand" >&2
  exit 99
fi
endpoint="${@: -1}"
scenario="${GH_SCENARIO:-ok}"

if [[ "$endpoint" =~ /rulesets$ ]]; then
  case "$scenario" in
    auth_error) printf '{"message":"Bad credentials","status":"401"}\n' ;;
    *) printf '[{"id":123,"name":"Main - PR Only + Green CI"}]\n' ;;
  esac
  exit 0
fi

if [[ "$endpoint" =~ /rulesets/123$ ]]; then
  case "$scenario" in
    auth_error) printf '{"message":"Forbidden","status":"403"}\n' ;;
    inactive) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"disabled","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
    no_default) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["refs/heads/main"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
    missing_ctx) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"}]}}]}\n' ;;
    *) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
  esac
  exit 0
fi

printf '{"message":"Not Found","status":"404"}\n'
exit 0
GH
	chmod +x "${dir}/gh"
}

# Verify exit 0 when ruleset is properly configured
#
# Arguments:
#   None
#
# Returns:
#   0 if test passes
#   Non-zero if test fails
#
# Globals:
#   PREF - Path to preflight script
#
# Outputs:
#   None (test output suppressed)
#
# Test Scenario:
#   Ruleset active, targets default branch, all contexts present
test_preflight_ok() {
	local tmp mockbin
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mockbin="$tmp/mockbin"
		mkdir -p "$mockbin"
		make_mock_gh "$mockbin"
		PATH="$mockbin:$PATH" GH_SCENARIO=ok bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null
	)
}

# Verify exit 1 when required contexts missing
#
# Arguments:
#   None
#
# Returns:
#   0 if test passes (script correctly exits with 1)
#   Non-zero if test fails
#
# Globals:
#   PREF - Path to preflight script
#
# Outputs:
#   None (test output suppressed)
#
# Test Scenario:
#   Ruleset missing required status check contexts
test_preflight_missing_ctx() {
	local tmp mockbin rc
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mockbin="$tmp/mockbin"
		mkdir -p "$mockbin"
		make_mock_gh "$mockbin"
		set +e
		PATH="$mockbin:$PATH" GH_SCENARIO=missing_ctx bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
		rc=$?
		set -e
		[[ "$rc" -eq 1 ]]
	)
}

# Verify exit 1 when ruleset enforcement is inactive
#
# Arguments:
#   None
#
# Returns:
#   0 if test passes (script correctly exits with 1)
#   Non-zero if test fails
#
# Globals:
#   PREF - Path to preflight script
#
# Outputs:
#   None (test output suppressed)
#
# Test Scenario:
#   Ruleset has enforcement=disabled
test_preflight_inactive() {
	local tmp mockbin rc
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mockbin="$tmp/mockbin"
		mkdir -p "$mockbin"
		make_mock_gh "$mockbin"
		set +e
		PATH="$mockbin:$PATH" GH_SCENARIO=inactive bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
		rc=$?
		set -e
		[[ "$rc" -eq 1 ]]
	)
}

# Verify exit 1 when ruleset doesn't target default branch
#
# Arguments:
#   None
#
# Returns:
#   0 if test passes (script correctly exits with 1)
#   Non-zero if test fails
#
# Globals:
#   PREF - Path to preflight script
#
# Outputs:
#   None (test output suppressed)
#
# Test Scenario:
#   Ruleset targets specific branch instead of ~DEFAULT_BRANCH
test_preflight_no_default() {
	local tmp mockbin rc
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mockbin="$tmp/mockbin"
		mkdir -p "$mockbin"
		make_mock_gh "$mockbin"
		set +e
		PATH="$mockbin:$PATH" GH_SCENARIO=no_default bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
		rc=$?
		set -e
		[[ "$rc" -eq 1 ]]
	)
}

# Verify exit 2 when authentication fails
#
# Arguments:
#   None
#
# Returns:
#   0 if test passes (script correctly exits with 2)
#   Non-zero if test fails
#
# Globals:
#   PREF - Path to preflight script
#
# Outputs:
#   None (test output suppressed)
#
# Test Scenario:
#   GitHub API returns auth error (Bad credentials/Forbidden)
test_preflight_auth_error() {
	local tmp mockbin rc
	tmp="$(mktemp_dir)"
	(
		cd "$tmp"
		mockbin="$tmp/mockbin"
		mkdir -p "$mockbin"
		make_mock_gh "$mockbin"
		set +e
		PATH="$mockbin:$PATH" GH_SCENARIO=auth_error bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
		rc=$?
		set -e
		[[ "$rc" -eq 2 ]]
	)
}

t "preflight: ok returns 0" test_preflight_ok
t "preflight: missing contexts returns 1" test_preflight_missing_ctx
t "preflight: enforcement inactive returns 1" test_preflight_inactive
t "preflight: does not target default branch returns 1" test_preflight_no_default
t "preflight: auth error returns 2" test_preflight_auth_error

summary
