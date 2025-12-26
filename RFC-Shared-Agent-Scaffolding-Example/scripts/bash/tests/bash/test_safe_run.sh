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
    f="$(ls .agent/FAIL-LOGS/*-fail.txt | head -n1)"
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
    grep -F "Failure tail" <<<"$err" >/dev/null
    grep -F "L2" <<<"$err" >/dev/null
    grep -F "L3" <<<"$err" >/dev/null
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
    [[ -n "$(ls custom_logs/*-fail.txt 2>/dev/null || true)" ]]
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
    f="$(ls .agent/FAIL-LOGS/*ABORTED-fail.txt | head -n1)"
    [[ -n "$f" ]]
    grep -F "START" "$f" >/dev/null
  )
}

t "safe-run: success produces no artifacts" test_success_no_artifacts
t "safe-run: failure captures stderr+stdout, preserves exit code" test_failure_captures_and_rc
t "safe-run: SAFE_SNIPPET_LINES prints tail snippet to stderr on failure" test_snippet_lines
t "safe-run: respects SAFE_LOG_DIR override" test_safe_log_dir_override
t "safe-run: SIGTERM produces ABORTED log and preserves forensic output" test_sigint_aborted_log

summary
