#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

ROOT="$(cd ../.. && pwd)"
SAFE_RUN="${ROOT}/scripts/bash/safe-run.sh"

test_success_no_artifacts() {
  local tmp out
  tmp="$(mktemp_dir)"
  ( 
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    out="$(bash "$SAFE_RUN" echo hello 2>&1)"
    [[ "$out" == "hello" ]]
    [[ -z "$(ls -A .agent/FAIL-LOGS 2>/dev/null || true)" ]]
  )
}

test_failure_captures_and_rc() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    bash "$SAFE_RUN" bash -c 'echo OOPS_STDOUT; echo OOPS_STDERR 1>&2; exit 42'
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

test_snippet_lines() {
  local tmp rc err
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    err="$((SAFE_SNIPPET_LINES=2 bash "$SAFE_RUN" bash -c 'printf "L1\nL2\nL3\n"; exit 9') 2>&1 1>/dev/null)"
    rc=$?
    set -e
    [[ "$rc" -eq 9 ]]
    grep -F "failure tail" <<<"$err" >/dev/null
    # With the new event ledger, the tail should show the last lines which include events
    grep -F "EVENTS" <<<"$err" >/dev/null
  )
}

test_safe_log_dir_override() {
  local tmp rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p custom_logs
    set +e
    SAFE_LOG_DIR="custom_logs" bash "$SAFE_RUN" bash -c 'echo nope; exit 7'
    rc=$?
    set -e
    [[ "$rc" -eq 7 ]]
    [[ -n "$(ls custom_logs/*-FAIL.log 2>/dev/null || true)" ]]
  )
}

test_sigint_aborted_log() {
  local tmp rc f pid
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    bash "$SAFE_RUN" bash -c 'echo START; sleep 10; echo END' >/dev/null 2>&1 &
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

test_event_ledger() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    bash "$SAFE_RUN" bash -c 'echo "out1"; echo "err1" 1>&2; echo "out2"; exit 5'
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

test_merged_view() {
  local tmp rc f c
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS
    set +e
    SAFE_RUN_VIEW=merged bash "$SAFE_RUN" bash -c 'echo "line1"; exit 3'
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

t "safe-run: success produces no artifacts" test_success_no_artifacts
t "safe-run: failure captures stderr+stdout, preserves exit code" test_failure_captures_and_rc
t "safe-run: SAFE_SNIPPET_LINES prints tail snippet to stderr on failure" test_snippet_lines
t "safe-run: respects SAFE_LOG_DIR override" test_safe_log_dir_override
t "safe-run: SIGTERM produces ABORTED log and preserves forensic output" test_sigint_aborted_log
t "safe-run: event ledger with sequence numbers" test_event_ledger
t "safe-run: merged view when SAFE_RUN_VIEW=merged" test_merged_view

summary
