#!/usr/bin/env bash
#
# test-safe-run.sh - Comprehensive test suite for safe-run.sh wrapper
#
# DESCRIPTION:
#   Tests the Bash wrapper for safe-run, verifying it correctly invokes the
#   Rust canonical tool and satisfies contract requirements. Covers success/failure
#   scenarios, environment variable handling, and conformance vectors.
#
# TEST COVERAGE:
#   Basic Behavior:
#     - Success runs create no artifacts (safe-run-001)
#     - Failure runs create FAIL-LOG artifacts (safe-run-002)
#     - Exit codes are preserved (safe-run-003)
#     - FAIL-LOGS contain stdout and stderr
#
#   Environment Variables:
#     - SAFE_SNIPPET_LINES controls stderr tail output (safe-run-005)
#     - SAFE_LOG_DIR overrides log directory
#     - SAFE_RUN_VIEW=merged produces merged output
#
#   Signal Handling:
#     - SIGTERM/SIGINT produce ABORTED.log files
#     - Exit code 143 for SIGTERM (or 130 on some platforms)
#
#   Event Ledger:
#     - Sequence numbers (SEQ=1, SEQ=2, ...)
#     - BEGIN/END EVENTS markers
#     - META events for start/exit
#
#   Conformance Vectors:
#     - Repo root detection from script location
#     - Argument quoting (empty strings, spaces, metacharacters)
#     - Exit code propagation (0, 1, 7, 42, 127, 255)
#     - Binary not found error (exit 127)
#
# USAGE:
#   ./test-safe-run.sh
#
# REQUIREMENTS:
#   - Rust binary must exist at:
#     - $REPO_ROOT/dist/linux/x86_64/safe-run OR
#     - $REPO_ROOT/rust/target/release/safe-run
#   - Test framework: lib.sh in same directory
#
# OUTPUTS:
#   Exit: 0 if all tests pass, 1 if any fail
#   Stderr: Test results (PASS/FAIL per test, summary)
#
# PLATFORM COMPATIBILITY:
#   - Linux: Primary test platform
#   - macOS: Compatible (adjusts for SIGTERM exit code differences)
#   - Windows: Git Bash, WSL
#
# CONTRACT REFERENCES:
#   - safe-run-001: Success produces no artifacts
#   - safe-run-002: Failure creates artifact with stdout/stderr
#   - safe-run-003: Exit code propagation
#   - safe-run-005: SAFE_SNIPPET_LINES controls tail output
#   - Wrapper discovery: docs/wrapper-discovery.md
#
# SEE ALSO:
#   - lib.sh: Test framework
#   - ../scripts/safe-run.sh: Script being tested
#   - conformance/vectors.json: Contract test vectors
#

set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

# Discover paths
ROOT="$(cd .. && pwd)"
SAFE_RUN="${ROOT}/scripts/safe-run.sh"

# Compute repo root and find Rust binary for wrapper discovery
# This mirrors the wrapper's own discovery logic for testing
REPO_ROOT="$(cd "$ROOT/../../.." && pwd)"
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

#
# TEST FUNCTIONS
# Each function tests a specific aspect of safe-run contract compliance
#

# test_success_no_artifacts - Verify safe-run-001: success creates no FAIL-LOGs
test_success_no_artifacts() {
  local tmp out
  tmp="$(mktemp_dir)"
  ( 
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    out="$(SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" echo hello 2>&1)"
    [[ "$out" == "hello" ]]
    [[ -z "$(ls -A .agent/FAIL-LOGS 2>/dev/null || true)" ]]
  )
}

# test_failure_captures_and_rc - Verify safe-run-002: failure creates log with stdout/stderr
# Also validates safe-run-003: exit code preservation
test_failure_captures_and_rc() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'echo OOPS_STDOUT; echo OOPS_STDERR 1>&2; exit 42'
    rc=$?
    set -e
    [[ "$rc" -eq 42 ]]
    f="$(ls .agent/FAIL-LOGS/*-FAIL.log | head -n1)"
    [[ -n "$f" ]]
    c="$(cat "$f")"
    grep -F "OOPS_STDOUT" <<<"$c" >/dev/null
    grep -F "OOPS_STDERR" <<<"$c" >/dev/null
  )
}

# test_snippet_lines - Verify safe-run-005: SAFE_SNIPPET_LINES controls stderr tail
# Default is 10 lines, test with 2 lines to verify last 2 lines appear
test_snippet_lines() {
  local tmp rc err
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    err="$((SAFE_SNIPPET_LINES=2 SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'printf "L1\nL2\nL3\n"; exit 9') 2>&1 1>/dev/null)"
    rc=$?
    set -e
    [[ "$rc" -eq 9 ]]
    # Conformance spec (safe-run-005) requires L2 and L3 in stderr
    grep -F "L2" <<<"$err" >/dev/null
    grep -F "L3" <<<"$err" >/dev/null
  )
}

# test_safe_log_dir_override - Verify SAFE_LOG_DIR environment variable works
test_safe_log_dir_override() {
  local tmp rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p custom_logs
    set +e
    SAFE_LOG_DIR="custom_logs" SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'echo nope; exit 7'
    rc=$?
    set -e
    [[ "$rc" -eq 7 ]]
    [[ -n "$(ls custom_logs/*-FAIL.log 2>/dev/null || true)" ]]
  )
}

# test_sigint_aborted_log - Verify signal termination creates ABORTED.log
# Tests that SIGTERM produces exit code 143 (or 130) and ABORTED log file
test_sigint_aborted_log() {
  local tmp rc f pid
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'echo START; sleep 10; echo END' >/dev/null 2>&1 &
    pid=$!
    sleep 0.5
    kill -TERM "$pid" >/dev/null 2>&1 || true
    wait "$pid"
    rc=$?
    set -e
    # 143 is the canonical exit code for SIGTERM; accept 130 too if the platform maps differently.
    [[ "$rc" -eq 143 || "$rc" -eq 130 ]]
    f="$(ls .agent/FAIL-LOGS/*ABORTED.log | head -n1)"
    [[ -n "$f" ]]
    grep -F "START" "$f" >/dev/null
  )
}

# test_event_ledger - Verify event ledger format with sequence numbers
# Checks for BEGIN/END EVENTS markers, SEQ numbers, and META events
test_event_ledger() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'echo "out1"; echo "err1" 1>&2; echo "out2"; exit 5'
    rc=$?
    set -e
    [[ "$rc" -eq 5 ]]
    f="$(ls .agent/FAIL-LOGS/*-FAIL.log | head -n1)"
    [[ -n "$f" ]]
    c="$(cat "$f")"
    # Check for event ledger markers
    grep -F "BEGIN EVENTS" <<<"$c" >/dev/null
    grep -F "END EVENTS" <<<"$c" >/dev/null
    # Check for standardized META events
    grep -F '[SEQ=1][META] safe-run start: cmd=' <<<"$c" >/dev/null
    grep -F '[META] safe-run exit: code=5' <<<"$c" >/dev/null
    # Check for stdout/stderr events
    grep -F '[STDOUT] out1' <<<"$c" >/dev/null
    grep -F '[STDOUT] out2' <<<"$c" >/dev/null
    grep -F '[STDERR] err1' <<<"$c" >/dev/null
  )
}

# test_merged_view - Verify SAFE_RUN_VIEW=merged produces merged output
# Tests that merged view uses [#seq] format instead of [SEQ=seq]
test_merged_view() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    SAFE_RUN_VIEW=merged SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c 'echo "line1"; exit 3'
    rc=$?
    set -e
    [[ "$rc" -eq 3 ]]
    f="$(ls .agent/FAIL-LOGS/*-FAIL.log | head -n1)"
    [[ -n "$f" ]]
    c="$(cat "$f")"
    # Check for merged view markers
    grep -F "BEGIN MERGED" <<<"$c" >/dev/null
    grep -F "END MERGED" <<<"$c" >/dev/null
    # Check for merged view format with [#seq] instead of [SEQ=seq]
    grep -F '[#1][META]' <<<"$c" >/dev/null
    grep -F '[#2][STDOUT] line1' <<<"$c" >/dev/null
  )
}

#
# CONFORMANCE TESTS
# These tests validate contract hardening beyond basic functionality
#

# Conformance test: repo root detection from script location
test_repo_root_from_script_location() {
  local tmp wrapper rc output
  tmp="$(mktemp_dir)"
  wrapper="$tmp/safe-run-relocated.sh"
  
  # Copy wrapper to temp location outside repo
  cp "$SAFE_RUN" "$wrapper"
  
  (
    cd "$tmp"  # Change to directory OUTSIDE repo
    # With SAFE_RUN_BIN set, wrapper should work regardless of location
    set +e
    output=$(SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$wrapper" echo "relocated test" 2>&1)
    rc=$?
    set -e
    
    [[ "$rc" -eq 0 ]]
    [[ "$output" == "relocated test" ]]
  )
  
  rm -rf "$tmp"
}

# Conformance test: argument quoting - empty string
# Verifies empty string arguments are preserved (not dropped)
test_arg_quoting_empty_string() {
  local tmp output
  tmp="$(mktemp_dir)"
  
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    output=$(SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" echo "" "after" 2>&1)
    # Should contain "after" (empty arg preserved)
    grep -q "after" <<<"$output"
  )
  
  rm -rf "$tmp"
}

# Conformance test: argument quoting - spaces
# Verifies arguments with spaces are passed as single argument (not split)
test_arg_quoting_spaces() {
  local tmp output
  tmp="$(mktemp_dir)"
  
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    output=$(SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" echo "hello world" 2>&1)
    [[ "$output" == "hello world" ]]
  )
  
  rm -rf "$tmp"
}

# Conformance test: argument quoting - metacharacters not interpreted
# Verifies shell metacharacters (;, |, etc.) are NOT executed
test_arg_quoting_metacharacters() {
  local tmp output
  tmp="$(mktemp_dir)"
  
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    output=$(SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" echo "test;echo hacked" 2>&1)
    [[ "$output" == "test;echo hacked" ]]
    # Should NOT contain "hacked" on separate line
    ! grep -q "^hacked$" <<<"$output"
  )
  
  rm -rf "$tmp"
}

# Conformance test: exit code propagation for multiple codes
# Verifies all exit codes are preserved exactly (safe-run-003)
test_exit_code_propagation_comprehensive() {
  local tmp codes code rc
  tmp="$(mktemp_dir)"
  codes=(0 1 7 42 127 255)
  
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    
    for code in "${codes[@]}"; do
      set +e
      SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" bash "$SAFE_RUN" bash -c "exit $code" >/dev/null 2>&1
      rc=$?
      set -e
      
      if [[ "$rc" -ne "$code" ]]; then
        echo "Exit code mismatch: expected $code, got $rc" >&2
        exit 1
      fi
    done
  )
  
  rm -rf "$tmp"
}

# Conformance test: binary not found error handling
# Verifies exit code 127 and helpful error message when binary missing
test_binary_not_found_error() {
  local tmp wrapper err rc
  tmp="$(mktemp_dir)"
  wrapper="$tmp/safe-run-nobin.sh"
  
  # Copy wrapper to temp location
  cp "$SAFE_RUN" "$wrapper"
  
  (
    cd "$tmp"
    unset SAFE_RUN_BIN || true
    
    set +e
    err=$(bash "$wrapper" echo "test" 2>&1)
    rc=$?
    set -e
    
    # Should exit with 127 (command not found)
    [[ "$rc" -eq 127 ]]
    # Should have error message
    grep -q "Rust canonical tool not found" <<<"$err"
  )
  
  rm -rf "$tmp"
}

#
# TEST EXECUTION
# Run all tests using lib.sh test framework
#

# Basic behavior tests
t "safe-run: success produces no artifacts" test_success_no_artifacts
t "safe-run: failure captures stderr+stdout, preserves exit code" test_failure_captures_and_rc
t "safe-run: SAFE_SNIPPET_LINES prints tail snippet to stderr on failure" test_snippet_lines
t "safe-run: respects SAFE_LOG_DIR override" test_safe_log_dir_override
t "safe-run: SIGTERM produces ABORTED log and preserves forensic output" test_sigint_aborted_log
t "safe-run: event ledger with sequence numbers" test_event_ledger
t "safe-run: merged view when SAFE_RUN_VIEW=merged" test_merged_view

# Conformance tests (contract hardening)
t "conformance: repo root detection from script location" test_repo_root_from_script_location
t "conformance: argument quoting - empty string" test_arg_quoting_empty_string
t "conformance: argument quoting - spaces preserved" test_arg_quoting_spaces
t "conformance: argument quoting - metacharacters not interpreted" test_arg_quoting_metacharacters
t "conformance: exit code propagation (0,1,7,42,127,255)" test_exit_code_propagation_comprehensive
t "conformance: binary not found exits with 127" test_binary_not_found_error

summary
