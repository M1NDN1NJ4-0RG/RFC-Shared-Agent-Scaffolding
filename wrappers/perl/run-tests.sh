#!/usr/bin/env bash
#
# run-tests.sh - Perl test suite runner
#
# DESCRIPTION:
#   Executes all Perl tests for the safe-run/safe-check/safe-archive wrapper
#   implementations. Uses prove (if available) or falls back to direct perl
#   execution of test files.
#
# USAGE:
#   ./run-tests.sh
#
# INPUTS:
#   Arguments:
#     None
#
#   Environment Variables:
#     SAFE_RUN_BIN  Path to Rust canonical binary (default: auto-detected)
#     SRC_SAFE_RUN  Path to safe_run.pl (default: scripts/safe_run.pl)
#
# OUTPUTS:
#   Exit Codes:
#     0  All tests passed
#     1  One or more tests failed
#
#   Stdout:
#     Test results from prove or perl
#
# EXAMPLES:
#   # Run all Perl tests
#   ./run-tests.sh
#
#   # Run with custom binary path
#   SAFE_RUN_BIN=/path/to/safe-run ./run-tests.sh
#
# NOTES:
#   - Prefers prove (TAP harness) if available
#   - Falls back to direct perl execution if prove not found
#   - Requires Rust canonical binary to be built
#   - Sets environment variables for test scripts

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
export SRC_SAFE_RUN="${SRC_SAFE_RUN:-$ROOT/scripts/safe_run.pl}"
export SRC_SAFE_ARCHIVE="${SRC_SAFE_ARCHIVE:-$ROOT/scripts/safe_archive.pl}"
export SRC_SAFE_CHECK="${SRC_SAFE_CHECK:-$ROOT/scripts/safe_check.pl}"
export SRC_PREFLIGHT="${SRC_PREFLIGHT:-$ROOT/scripts/preflight_automerge_ruleset.pl}"

# For thin wrapper tests: point to Rust canonical binary
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
export SAFE_RUN_BIN="${SAFE_RUN_BIN:-$REPO_ROOT/rust/target/release/safe-run}"

cd "$ROOT"

if command -v prove >/dev/null 2>&1; then
  prove -v -I tests/lib tests/*.t
else
  for f in tests/*.t; do
    perl -I tests/lib "$f"
  done
fi
