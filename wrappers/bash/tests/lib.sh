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

# _color - Apply ANSI color codes if output is a TTY
# Args: $1 = color code, $2+ = text
# Returns: Colored text if TTY, plain text otherwise
_color() {
  local code="$1"; shift
  if [[ -t 1 ]]; then printf "\033[%sm%s\033[0m" "$code" "$*"; else printf "%s" "$*"; fi
}

# Logging helpers
log() { printf "%s\n" "$*" >&2; }  # Print to stderr

# Print PASS message with green color
# Args: $* = pass message
pass() { log "$(_color '32' 'PASS') $*"; }  # Green PASS

# Print FAIL message with red color
# Args: $* = fail message
fail() { log "$(_color '31' 'FAIL') $*"; }  # Red FAIL

# t - Run a test and track results
# Args: $1 = test name/description, $2+ = test command
# Returns: 0 if test passes, 1 if test fails (non-blocking)
# Side effect: Increments __TESTS_TOTAL and __TESTS_FAIL counters
t() {
  __TESTS_TOTAL=$((__TESTS_TOTAL+1))
  local name="$1"; shift
  if "$@"; then
    pass "$name"
    return 0
  else
    __TESTS_FAIL=$((__TESTS_FAIL+1))
    fail "$name"
    return 1
  fi
}

#
# ASSERTION HELPERS
# All return 0 on success, 1 on failure (compatible with t() wrapper)
#

# assert_eq - Assert two values are equal
# Args: $1 = got, $2 = want, $3 = optional message
assert_eq() {
  local got="$1" want="$2" msg="${3:-}"
  [[ "$got" == "$want" ]] || { log "assert_eq failed: got=<$got> want=<$want> $msg"; return 1; }
}

# assert_ne - Assert two values are not equal
# Args: $1 = got, $2 = bad (value that should NOT match), $3 = optional message
assert_ne() {
  local got="$1" bad="$2" msg="${3:-}"
  [[ "$got" != "$bad" ]] || { log "assert_ne failed: got=<$got> bad=<$bad> $msg"; return 1; }
}

# File existence assertions

# Assert directory exists
# Args: $1 = directory path
assert_dir_exists() { [[ -d "$1" ]] || { log "expected dir to exist: $1"; return 1; }; }

# Assert file does not exist
# Args: $1 = file path
assert_file_not_exists() { [[ ! -e "$1" ]] || { log "expected file to NOT exist: $1"; return 1; }; }

# String containment assertions
assert_contains() {
  local hay="$1" needle="$2" msg="${3:-}"
  grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 || { log "expected output to contain: $needle $msg"; return 1; }
}

# Assert string not in content
# Args: $1 = haystack, $2 = needle, $3 = optional message
assert_not_contains() {
  local hay="$1" needle="$2" msg="${3:-}"
  grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 && { log "expected output NOT to contain: $needle $msg"; return 1; }
}

#
# UTILITY FUNCTIONS
#

# mktemp_dir - Create temporary directory (cross-platform)
# Returns: Absolute path to temp directory
# Compatible with macOS (BSD mktemp) and Linux (GNU mktemp)
mktemp_dir() {
  local d
  d="$(mktemp -d 2>/dev/null || mktemp -d -t agentops_tests)"
  printf "%s" "$d"
}

#
# TEST SUMMARY
#

# summary - Print final test results and exit
# Prints pass/fail counts and exits with appropriate code
# Exit: 0 if all tests passed, 1 if any failed
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
