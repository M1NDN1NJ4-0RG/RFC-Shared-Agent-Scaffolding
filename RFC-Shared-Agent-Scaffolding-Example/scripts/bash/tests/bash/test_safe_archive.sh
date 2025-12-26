#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

ROOT="$(cd ../.. && pwd)"
ARCH="${ROOT}/scripts/bash/safe-archive.sh"

test_default_archives_one() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "a\n" > ".agent/FAIL-LOGS/one fail-fail.txt"
    printf "b\n" > ".agent/FAIL-LOGS/two-fail.txt"
    bash "$ARCH" >/dev/null 2>&1
    # By default, it moves ONE file then exits (either one of the two)
    local n
    n="$(ls -1 .agent/FAIL-ARCHIVE/*-fail.txt 2>/dev/null | wc -l | tr -d " ")"
    [[ "$n" -eq 1 ]]
    # And one file remains in FAIL-LOGS
    n="$(ls -1 .agent/FAIL-LOGS/*-fail.txt 2>/dev/null | wc -l | tr -d " ")"
    [[ "$n" -eq 1 ]]
  )
}

test_moves_all_with_spaces() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "a\n" > ".agent/FAIL-LOGS/one fail-fail.txt"
    printf "b\n" > ".agent/FAIL-LOGS/two-fail.txt"
    bash "$ARCH" --all >/dev/null 2>&1
    [[ ! -e ".agent/FAIL-LOGS/one fail-fail.txt" ]]
    [[ ! -e ".agent/FAIL-LOGS/two-fail.txt" ]]
    [[ -f ".agent/FAIL-ARCHIVE/one fail-fail.txt" ]]
    [[ -f ".agent/FAIL-ARCHIVE/two-fail.txt" ]]
  )
}

test_no_clobber() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "OLD\n" > ".agent/FAIL-ARCHIVE/x-fail.txt"
    printf "NEW\n" > ".agent/FAIL-LOGS/x-fail.txt"
    bash "$ARCH" --all >/dev/null 2>&1
    # should skip (exists) and leave original in FAIL-LOGS
    [[ "$(cat .agent/FAIL-ARCHIVE/x-fail.txt)" == "OLD" ]]
    [[ -f ".agent/FAIL-LOGS/x-fail.txt" ]]
  )
}

test_gzip_compression() {
  command -v gzip >/dev/null 2>&1 || return 0
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "Z\n" > ".agent/FAIL-LOGS/z-fail.txt"
    SAFE_ARCHIVE_COMPRESS=gzip bash "$ARCH" --all >/dev/null 2>&1
    [[ -f ".agent/FAIL-ARCHIVE/z-fail.txt.gz" ]]
    gzip -cd ".agent/FAIL-ARCHIVE/z-fail.txt.gz" | grep -F "Z" >/dev/null
  )
}

t "safe-archive: default archives only one file" test_default_archives_one
t "safe-archive: moves all logs (handles spaces in filenames)" test_moves_all_with_spaces
t "safe-archive: no-clobber prevents overwrite" test_no_clobber
t "safe-archive: gzip compression works when gzip is available" test_gzip_compression

summary
