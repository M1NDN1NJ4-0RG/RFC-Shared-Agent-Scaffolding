#!/usr/bin/env bash
#
# test-safe-archive.sh - Tests for safe-archive.sh log archiving script
#
# DESCRIPTION:
#   Validates safe-archive.sh correctly moves failure logs from FAIL-LOGS
#   to FAIL-ARCHIVE with no-clobber safety and optional compression.
#
# TEST COVERAGE:
#   - Default behavior: archives one file
#   - --all flag: archives all files
#   - Handles filenames with spaces
#   - No-clobber: doesn't overwrite existing archives
#   - Compression: gzip compression when available
#
# USAGE:
#   ./test-safe-archive.sh
#
# INPUTS:
#   Arguments:
#     None (test script runs all tests)
#
#   Environment Variables:
#     None (uses isolated temp directories for testing)
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
#   # Run all safe-archive tests
#   ./test-safe-archive.sh
#
# CONTRACT REFERENCES:
#   - M0-P1-I2: Log lifecycle and naming
#   - No-clobber guarantee for archive safety
#
# SEE ALSO:
#   - lib.sh: Test framework
#   - ../scripts/safe-archive.sh: Script being tested
#

set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

# Discover paths
ROOT="$(cd .. && pwd)"
ARCH="${ROOT}/scripts/safe-archive.sh"

# test_default_archives_one - Verify default (no --all) archives only one file
test_default_archives_one() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "a\n" > ".agent/FAIL-LOGS/one fail-FAIL.log"
    printf "b\n" > ".agent/FAIL-LOGS/two-FAIL.log"
    bash "$ARCH" >/dev/null 2>&1
    # By default, it moves ONE file then exits (either one of the two)
    local n
    n="$(ls -1 .agent/FAIL-ARCHIVE/*-FAIL.log 2>/dev/null | wc -l | tr -d " ")"
    [[ "$n" -eq 1 ]]
    # And one file remains in FAIL-LOGS
    n="$(ls -1 .agent/FAIL-LOGS/*-FAIL.log 2>/dev/null | wc -l | tr -d " ")"
    [[ "$n" -eq 1 ]]
  )
}

# test_moves_all_with_spaces - Verify --all flag and space handling
# Tests that filenames with spaces are handled correctly (no word splitting)
test_moves_all_with_spaces() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "a\n" > ".agent/FAIL-LOGS/one fail-FAIL.log"
    printf "b\n" > ".agent/FAIL-LOGS/two-FAIL.log"
    bash "$ARCH" --all >/dev/null 2>&1
    [[ ! -e ".agent/FAIL-LOGS/one fail-FAIL.log" ]]
    [[ ! -e ".agent/FAIL-LOGS/two-FAIL.log" ]]
    [[ -f ".agent/FAIL-ARCHIVE/one fail-FAIL.log" ]]
    [[ -f ".agent/FAIL-ARCHIVE/two-FAIL.log" ]]
  )
}

# test_no_clobber - Verify existing archive files are not overwritten
test_no_clobber() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "OLD\n" > ".agent/FAIL-ARCHIVE/x-FAIL.log"
    printf "NEW\n" > ".agent/FAIL-LOGS/x-FAIL.log"
    bash "$ARCH" --all >/dev/null 2>&1
    # should skip (exists) and leave original in FAIL-LOGS
    [[ "$(cat .agent/FAIL-ARCHIVE/x-FAIL.log)" == "OLD" ]]
    [[ -f ".agent/FAIL-LOGS/x-FAIL.log" ]]
  )
}

# test_gzip_compression - Verify gzip compression works when gzip available
# Skips gracefully if gzip not installed (returns 0)
test_gzip_compression() {
  command -v gzip >/dev/null 2>&1 || return 0
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    printf "Z\n" > ".agent/FAIL-LOGS/z-FAIL.log"
    SAFE_ARCHIVE_COMPRESS=gzip bash "$ARCH" --all >/dev/null 2>&1
    [[ -f ".agent/FAIL-ARCHIVE/z-FAIL.log.gz" ]]
    gzip -cd ".agent/FAIL-ARCHIVE/z-FAIL.log.gz" | grep -F "Z" >/dev/null
  )
}

t "safe-archive: default archives only one file" test_default_archives_one
t "safe-archive: moves all logs (handles spaces in filenames)" test_moves_all_with_spaces
t "safe-archive: no-clobber prevents overwrite" test_no_clobber
t "safe-archive: gzip compression works when gzip is available" test_gzip_compression

summary
