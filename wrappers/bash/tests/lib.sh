#!/usr/bin/env bash
#
# lib.sh - Lightweight test harness for Bash script testing
#
# DESCRIPTION:
#   Minimal test framework with no external dependencies. Provides test runner
#   functions, assertions, and colored output for test results. Used by all
#   Bash test files in this directory.
#
#   Design: Simple, self-contained, works on macOS Bash 3.2+ and Linux Bash 4+.
#
# USAGE:
#   # In test file
#   source "./lib.sh"
#
#   test_something() {
#     # test logic
#     return 0  # pass
#   }
#
#   t "description" test_something
#   summary  # prints final results and exits
#
# FUNCTIONS:
#   t <name> <command...>        Run a test, track pass/fail
#   assert_eq <got> <want> [msg] Assert equality
#   assert_ne <got> <bad> [msg]  Assert inequality
#   assert_file_exists <path>    Assert file exists
#   assert_dir_exists <path>     Assert directory exists
#   assert_file_not_exists <path> Assert file doesn't exist
#   assert_contains <hay> <needle> [msg] Assert substring
#   assert_not_contains <hay> <needle> [msg] Assert no substring
#   mktemp_dir                   Create temp directory (cross-platform)
#   summary                      Print test summary and exit
#   pass <msg>                   Print green PASS message
#   fail <msg>                   Print red FAIL message
#   log <msg>                    Print to stderr
#
# INPUTS:
#   Arguments:
#     None (library is sourced, not executed)
#
#   Environment Variables:
#     None (self-contained test framework)
#
# OUTPUTS:
#   Exit Codes (via summary):
#     0  All tests passed
#     1  One or more tests failed
#
#   Stdout:
#     (silent)
#
#   Stderr:
#     PASS <description> - test passed (green if TTY)
#     FAIL <description> - test failed (red if TTY)
#     ALL TESTS PASSED total=N - summary (green if TTY)
#     SOME TESTS FAILED total=N failed=M - summary (red if TTY)
#
# STATE:
#   __TESTS_TOTAL  Global counter for total tests run
#   __TESTS_FAIL   Global counter for failed tests
#
# PLATFORM COMPATIBILITY:
#   - Linux: Bash 4.0+
#   - macOS: Bash 3.2+ (default macOS shell)
#   - Windows: Git Bash, WSL
#   - Colors: Auto-detected via -t 1 (TTY check)
#
# EXAMPLES:
#   # Basic test
#   my_test() {
#     local result=$(echo "hello")
#     assert_eq "$result" "hello" "echo should work"
#   }
#   t "echo returns hello" my_test
#
#   # File assertions
#   test_file_created() {
#     touch /tmp/test.txt
#     assert_file_exists /tmp/test.txt
#     rm /tmp/test.txt
#   }
#   t "creates temp file" test_file_created
#
#   # Temp directory
#   test_with_tmpdir() {
#     local tmp=$(mktemp_dir)
#     cd "$tmp"
#     # ... test logic ...
#     rm -rf "$tmp"
#   }
#   t "uses temp dir" test_with_tmpdir
#
# SEE ALSO:
#   - run-all.sh: Runs all test-*.sh files
#   - test-safe-run.sh, test-safe-archive.sh: Example usage
# tests/bash/lib.sh - tiny test harness (no external deps)
#
# IMPLEMENTATION NOTES:
# - Uses 'set -u' to catch undefined variable errors
# - No pipefail needed (no critical pipes)
# - _color helper detects TTY for colored output
# - All output goes to stderr (stdout reserved for test data)
#

set -u

# Global test counters
__TESTS_TOTAL=0
__TESTS_FAIL=0

# Apply ANSI color codes if output is a TTY
#
# Arguments:
#   $1 - Color code (e.g., 32 for green, 31 for red)
#   $2+ - Text to color
#
# Returns:
#   0 (always succeeds)
#
# Globals:
#   None
#
# Outputs:
#   Colored text if stdout is TTY, plain text otherwise
_color() {
	local code="$1"
	shift
	if [[ -t 1 ]]; then printf "\033[%sm%s\033[0m" "$code" "$*"; else printf "%s" "$*"; fi
}

# Print message to stderr
#
# Arguments:
#   $* - Message to print
#
# Returns:
#   0 (always succeeds)
#
# Globals:
#   None
#
# Outputs:
#   Message to stderr
log() { printf "%s\n" "$*" >&2; }

# Print PASS message with green color
#
# Arguments:
#   $* - Pass message
#
# Returns:
#   0 (always succeeds)
#
# Globals:
#   None
#
# Outputs:
#   "PASS <message>" to stderr in green if TTY
pass() { log "$(_color '32' 'PASS') $*"; }

# Print FAIL message with red color
#
# Arguments:
#   $* - Fail message
#
# Returns:
#   0 (always succeeds)
#
# Globals:
#   None
#
# Outputs:
#   "FAIL <message>" to stderr in red if TTY
fail() { log "$(_color '31' 'FAIL') $*"; }

# Run a test and track results
#
# Arguments:
#   $1 - Test name/description
#   $2+ - Test command to execute
#
# Returns:
#   0 if test passes
#   1 if test fails (non-blocking)
#
# Globals:
#   __TESTS_TOTAL - Incremented for each test
#   __TESTS_FAIL - Incremented for each failure
#
# Outputs:
#   PASS or FAIL message to stderr
t() {
	__TESTS_TOTAL=$((__TESTS_TOTAL + 1))
	local name="$1"
	shift
	if "$@"; then
		pass "$name"
		return 0
	else
		__TESTS_FAIL=$((__TESTS_FAIL + 1))
		fail "$name"
		return 1
	fi
}

#
# ASSERTION HELPERS
# All return 0 on success, 1 on failure (compatible with t() wrapper)
#

# Assert two values are equal
#
# Arguments:
#   $1 - Got (actual value)
#   $2 - Want (expected value)
#   $3 - Optional message
#
# Returns:
#   0 if values are equal
#   1 if values differ
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_eq() {
	local got="$1" want="$2" msg="${3:-}"
	[[ "$got" == "$want" ]] || {
		log "assert_eq failed: got=<$got> want=<$want> $msg"
		return 1
	}
}

# Assert two values are not equal
#
# Arguments:
#   $1 - Got (actual value)
#   $2 - Bad (value that should NOT match)
#   $3 - Optional message
#
# Returns:
#   0 if values are different
#   1 if values are equal
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_ne() {
	local got="$1" bad="$2" msg="${3:-}"
	[[ "$got" != "$bad" ]] || {
		log "assert_ne failed: got=<$got> bad=<$bad> $msg"
		return 1
	}
}

# File existence assertions

# Assert file exists
#
# Arguments:
#   $1 - File path
#
# Returns:
#   0 if file exists
#   1 if file does not exist
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_file_exists() { [[ -e "$1" ]] || {
	log "expected file to exist: $1"
	return 1
}; }

# Assert directory exists
#
# Arguments:
#   $1 - Directory path
#
# Returns:
#   0 if directory exists
#   1 if directory does not exist
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_dir_exists() { [[ -d "$1" ]] || {
	log "expected dir to exist: $1"
	return 1
}; }

# Assert file does not exist
#
# Arguments:
#   $1 - File path
#
# Returns:
#   0 if file does not exist
#   1 if file exists
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_file_not_exists() { [[ ! -e "$1" ]] || {
	log "expected file to NOT exist: $1"
	return 1
}; }

# String containment assertions
# Assert string contains substring
#
# Arguments:
#   $1 - Haystack (string to search in)
#   $2 - Needle (substring to find)
#   $3 - Optional message
#
# Returns:
#   0 if substring found
#   1 if substring not found
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_contains() {
	local hay="$1" needle="$2" msg="${3:-}"
	grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 || {
		log "expected output to contain: $needle $msg"
		return 1
	}
}

# Assert string does not contain substring
#
# Arguments:
#   $1 - Haystack (string to search in)
#   $2 - Needle (substring that should not be found)
#   $3 - Optional message
#
# Returns:
#   0 if substring not found
#   1 if substring found
#
# Globals:
#   None
#
# Outputs:
#   Error message to stderr on failure
assert_not_contains() {
	local hay="$1" needle="$2" msg="${3:-}"
	grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 && {
		log "expected output NOT to contain: $needle $msg"
		return 1
	}
}

#
# UTILITY FUNCTIONS
#

# Create temporary directory (cross-platform)
#
# Arguments:
#   None
#
# Returns:
#   0 on success
#   Non-zero on failure
#
# Globals:
#   None
#
# Outputs:
#   Absolute path to temp directory to stdout
#
# Compatibility:
#   Works with macOS (BSD mktemp) and Linux (GNU mktemp)
mktemp_dir() {
	local d
	d="$(mktemp -d 2>/dev/null || mktemp -d -t agentops_tests)"
	printf "%s" "$d"
}

#
# TEST SUMMARY
#

# Print final test results and exit
#
# Arguments:
#   None
#
# Returns:
#   0 if all tests passed
#   1 if any test failed
#
# Globals:
#   __TESTS_TOTAL - Total number of tests run
#   __TESTS_FAIL - Number of failed tests
#
# Outputs:
#   Test summary to stderr with colored pass/fail status
summary() {
	if [[ "$__TESTS_FAIL" -ne 0 ]]; then
		log ""
		log "$(_color '31' 'SOME TESTS FAILED')  total=$__TESTS_TOTAL failed=$__TESTS_FAIL"
		return 1
	fi
	log ""
	log "$(_color '32' 'ALL TESTS PASSED') total=$__TESTS_TOTAL"
	return 0
}
