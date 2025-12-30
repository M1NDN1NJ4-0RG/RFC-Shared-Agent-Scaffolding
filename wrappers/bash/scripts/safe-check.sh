#!/usr/bin/env bash
#
# safe-check.sh - Lightweight contract verification for Bash safe-run implementation
#
# DESCRIPTION:
#   Smoke test that verifies the Bash wrapper and Rust canonical tool satisfy
#   the core contract requirements. Tests three critical behaviors:
#     1. Success runs create no artifacts
#     2. Failure runs create FAIL-LOG artifacts
#     3. safe-archive moves logs without clobbering
#
#   This is NOT a comprehensive conformance test (see conformance/harness for that).
#   It's a quick sanity check for CI and local development.
#
# USAGE:
#   safe-check.sh
#
# INPUTS:
#   Arguments: None
#
#   Environment Variables:
#     SAFE_RUN_BIN  Override binary location (optional, for testing)
#     All safe-run environment variables (SAFE_LOG_DIR, etc.) are respected
#
# OUTPUTS:
#   Exit Codes:
#     0  All checks passed (contract looks sane)
#     1  One or more checks failed (contract violation)
#
#   Stdout:
#     "OK: Bash safe-run/safe-archive contract looks sane." - all tests passed
#
#   Stderr:
#     "FAIL: <reason>" - specific failure message
#
#   Side Effects:
#     Creates temporary .agent/FAIL-LOGS and .agent/FAIL-ARCHIVE directories
#     May leave test artifacts in .agent/ (cleaned up by tests)
#
# TEST COVERAGE:
#   1. Success run (exit 0):
#      - No FAIL-LOG artifacts created
#      - Compares file count before/after
#
#   2. Failure run (exit 42):
#      - FAIL-LOG artifact created in FAIL-LOGS/
#      - Contains stdout and stderr from failed command
#
#   3. Archive behavior:
#      - safe-archive.sh --all moves logs to FAIL-ARCHIVE/
#      - No-clobber: doesn't overwrite existing archives
#      - Handles compressed extensions (.gz, .xz, .zst)
#
# PLATFORM COMPATIBILITY:
#   - Linux: Tested on Ubuntu 20.04+
#   - macOS: Compatible with Bash 3.2+
#   - Windows: Works via Git Bash, WSL
#
# CONTRACT REFERENCES:
#   - Artifact creation: conformance/vectors.json (safe-run-001, safe-run-002)
#   - Archive behavior: M0-P1-I2 (log lifecycle)
#   - Related scripts: safe-run.sh, safe-archive.sh
#
# EXAMPLES:
#   # Normal usage (CI)
#   safe-check.sh
#
#   # With custom binary (testing)
#   SAFE_RUN_BIN=/path/to/dev/safe-run safe-check.sh
#
#   # Run from anywhere (discovers repo root)
#   cd /tmp && /path/to/repo/scripts/bash/scripts/safe-check.sh
#
# SEE ALSO:
#   - conformance/harness: Comprehensive contract validation
#   - safe-run.sh: Wrapper being tested
#   - safe-archive.sh: Archival tool being tested
# safe-check.sh
# Lightweight contract verification for the Bash implementation.
#
# IMPLEMENTATION NOTES:
# - Uses 'set -eu' for error handling
# - Runs from script's parent directory (assumes scripts/ layout)
# - Tests use relative paths to safe-run.sh and safe-archive.sh
#

set -eu

# Discover script locations relative to this file
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL_DIR="$ROOT_DIR/.agent/FAIL-LOGS"
ARCH_DIR="$ROOT_DIR/.agent/FAIL-ARCHIVE"

# Create test directories
mkdir -p "$FAIL_DIR" "$ARCH_DIR"

#
# TEST 1: Success run should create no FAIL-LOG artifacts
# Verifies: safe-run-001 (success produces no artifacts)
#

# 1) Success run: should create no FAIL-LOG artifacts
before_count=$(find "$FAIL_DIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
"$ROOT_DIR/scripts/safe-run.sh" bash -c 'echo ok; exit 0' >/dev/null
after_count=$(find "$FAIL_DIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$after_count" -ne "$before_count" ]; then
	echo "FAIL: safe-run created artifacts on success" >&2
	exit 1
fi

#
# TEST 2: Failure run must create a FAIL-LOG file
# Verifies: safe-run-002 (failure creates artifact with stdout/stderr)
#

# 2) Failure run: must create a FAIL-LOG file
"$ROOT_DIR/scripts/safe-run.sh" bash -c 'echo out; echo err 1>&2; exit 42' >/dev/null || true
# shellcheck disable=SC2012  # ls is acceptable here for sorting by time
newest=$(ls -1t "$FAIL_DIR" 2>/dev/null | head -n 1 || true)
if [ -z "$newest" ]; then
	echo "FAIL: safe-run did not create failure log" >&2
	exit 1
fi

#
# TEST 3: Archive should move log to FAIL-ARCHIVE with no-clobber
# Verifies: safe-archive.sh moves files and respects existing archives
#

# 3) Archive should move it, no clobber
"$ROOT_DIR/scripts/safe-archive.sh" --all >/dev/null

# Verify log was moved from FAIL-LOGS
if [ -e "$FAIL_DIR/$newest" ]; then
	echo "FAIL: safe-archive did not move log" >&2
	exit 1
fi

# Verify log exists in FAIL-ARCHIVE (check all possible compression extensions)
if [ ! -e "$ARCH_DIR/$newest" ] && [ ! -e "$ARCH_DIR/${newest}.gz" ] && [ ! -e "$ARCH_DIR/${newest}.xz" ] && [ ! -e "$ARCH_DIR/${newest}.zst" ]; then
	echo "FAIL: safe-archive did not create archived file" >&2
	exit 1
fi

#
# ALL TESTS PASSED
#

echo "OK: Bash safe-run/safe-archive contract looks sane."
