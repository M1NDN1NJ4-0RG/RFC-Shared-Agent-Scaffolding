#!/usr/bin/env bash
# tests/bash/lib.sh - tiny test harness (no external deps)

set -u

__TESTS_TOTAL=0
__TESTS_FAIL=0

_color() {
  local code="$1"; shift
  if [[ -t 1 ]]; then printf "\033[%sm%s\033[0m" "$code" "$*"; else printf "%s" "$*"; fi
}

log() { printf "%s\n" "$*" >&2; }
pass() { log "$(_color '32' 'PASS') $*"; }
fail() { log "$(_color '31' 'FAIL') $*"; }

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

assert_eq() {
  local got="$1" want="$2" msg="${3:-}"
  [[ "$got" == "$want" ]] || { log "assert_eq failed: got=<$got> want=<$want> $msg"; return 1; }
}
assert_ne() {
  local got="$1" bad="$2" msg="${3:-}"
  [[ "$got" != "$bad" ]] || { log "assert_ne failed: got=<$got> bad=<$bad> $msg"; return 1; }
}
assert_file_exists() { [[ -f "$1" ]] || { log "expected file to exist: $1"; return 1; }; }
assert_dir_exists() { [[ -d "$1" ]] || { log "expected dir to exist: $1"; return 1; }; }
assert_file_not_exists() { [[ ! -e "$1" ]] || { log "expected file to NOT exist: $1"; return 1; }; }
assert_contains() {
  local hay="$1" needle="$2" msg="${3:-}"
  grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 || { log "expected output to contain: $needle $msg"; return 1; }
}
assert_not_contains() {
  local hay="$1" needle="$2" msg="${3:-}"
  grep -F -- "$needle" <<<"$hay" >/dev/null 2>&1 && { log "expected output NOT to contain: $needle $msg"; return 1; }
}

mktemp_dir() {
  local d
  d="$(mktemp -d 2>/dev/null || mktemp -d -t agentops_tests)"
  printf "%s" "$d"
}

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
