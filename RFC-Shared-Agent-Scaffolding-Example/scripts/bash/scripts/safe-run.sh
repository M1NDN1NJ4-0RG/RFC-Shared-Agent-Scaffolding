#!/usr/bin/env bash
#
# safe-run.sh - Thin Bash wrapper for Rust canonical safe-run tool
#
# DESCRIPTION:
#   Discovers and invokes the Rust canonical safe-run implementation. This wrapper
#   does NOT reimplement any contract logic - it is a pure invoker that forwards
#   all arguments and environment variables to the Rust binary.
#
#   The safe-run tool captures stdout/stderr of child processes, creates forensic
#   logs on failure, and provides structured event output. See the Rust canonical
#   tool for implementation details.
#
# USAGE:
#   safe-run.sh <command> [args...]
#   safe-run.sh bash -c 'echo hello; exit 1'
#   SAFE_RUN_BIN=/custom/path/safe-run safe-run.sh npm test
#
# INPUTS:
#   Arguments:
#     All arguments are passed through to the Rust binary without modification
#
#   Environment Variables:
#     SAFE_RUN_BIN       Override binary location (highest priority)
#     SAFE_LOG_DIR       Directory for failure logs (default: .agent/FAIL-LOGS)
#     SAFE_SNIPPET_LINES Number of tail lines to show on stderr (default: 0)
#                        The snippet is printed after "command failed ... log:" line
#                        for quick diagnosis. Full output is always in the log file.
#                        Note: Extremely large values may produce noisy stderr.
#     SAFE_RUN_VIEW      Output format: "ledger" (default) or "merged"
#     SAFE_ARCHIVE_DIR   Archive directory (used by safe-archive.sh)
#
# OUTPUTS:
#   Exit Codes:
#     0-255  Child process exit code (forwarded from Rust tool)
#     127    Binary not found (with error message to stderr)
#
#   Stdout/Stderr:
#     Success: Child stdout/stderr passed through
#     Failure: Child stdout/stderr + snippet of captured log to stderr
#
#   Side Effects:
#     Creates forensic log files in SAFE_LOG_DIR on non-zero exit
#     Log format: YYYYMMDDTHHMMSSZ-pid<N>-{FAIL|ABORTED|ERROR}.log
#
# BINARY DISCOVERY ORDER (per docs/wrapper-discovery.md):
#   1. SAFE_RUN_BIN env var (if set)
#   2. ./rust/target/release/safe-run (dev mode, relative to repo root)
#   3. ./dist/<os>/<arch>/safe-run (CI artifacts)
#   4. PATH lookup (system installation)
#   5. Error with actionable instructions (exit 127)
#
# PLATFORM COMPATIBILITY:
#   - Linux: Tested on Ubuntu 20.04+, requires Bash 4.0+
#   - macOS: Compatible with Bash 3.2+ (macOS default)
#   - Windows: Works via Git Bash, WSL, or MSYS2
#
# CONTRACT REFERENCES:
#   - Wrapper discovery: docs/wrapper-discovery.md
#   - Output contract: docs/conformance-contract.md (M0-v0.1.0)
#   - Test vectors: conformance/vectors.json (safe-run-001 through safe-run-005)
#   - Repo root detection: Walks up from script dir looking for .git or RFC marker
#
# EXAMPLES:
#   # Basic usage
#   safe-run.sh echo "Hello, world"
#
#   # Capture failure logs
#   safe-run.sh bash -c 'echo stderr >&2; exit 1'
#   # Creates .agent/FAIL-LOGS/20240115T120000Z-pid1234-FAIL.log
#
#   # Custom log directory
#   SAFE_LOG_DIR=/tmp/logs safe-run.sh npm test
#
#   # Override binary location (testing)
#   SAFE_RUN_BIN=/path/to/dev/safe-run safe-run.sh echo test
#
# SEE ALSO:
#   - safe-archive.sh: Archive failure logs with compression
#   - safe-check.sh: Contract verification tests
#   - docs/rust-canonical-tool.md: Rust implementation details

set -euo pipefail

#
# IMPLEMENTATION NOTES:
# - Uses 'set -euo pipefail' for strict error handling
# - Uses 'exec' to replace shell process, preserving exit codes and signals
# - All functions are helper utilities for binary discovery
# - No argument parsing or interpretation (pure pass-through)
#

# Determine repository root (walk up from script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# find_repo_root - Walk up directory tree to locate repository root
# Looks for RFC-Shared-Agent-Scaffolding-v0.1.0.md or .git directory
# Returns: Absolute path to repo root, or empty string if not found
find_repo_root() {
  local dir="$SCRIPT_DIR"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/RFC-Shared-Agent-Scaffolding-v0.1.0.md" ] || [ -d "$dir/.git" ]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

REPO_ROOT="$(find_repo_root)" || REPO_ROOT=""

# detect_platform - Determine OS and architecture for CI artifact paths
# Returns: String in format "os/arch" (e.g., "linux/x86_64", "macos/aarch64")
# Used for step 3 of binary discovery (./dist/<os>/<arch>/safe-run)
# Also sets IS_WINDOWS=1 for binary name determination (.exe suffix)
detect_platform() {
  local os arch
  case "$(uname -s)" in
    Linux*)  os="linux" ;;
    Darwin*) os="macos" ;;
    CYGWIN*|MINGW*|MSYS*) os="windows"; IS_WINDOWS=1 ;;
    *) os="unknown" ;;
  esac
  
  case "$(uname -m)" in
    x86_64|amd64) arch="x86_64" ;;
    aarch64|arm64) arch="aarch64" ;;
    *) arch="unknown" ;;
  esac
  
  echo "${os}/${arch}"
}

# Initialize IS_WINDOWS before calling detect_platform (function may override to 1)
IS_WINDOWS=0
PLATFORM="$(detect_platform)"

# find_safe_run_binary - Execute binary discovery cascade
# Implements the 5-step discovery order defined in docs/wrapper-discovery.md
# Returns: Absolute path to safe-run binary (prints to stdout)
# Exit: 0 if found, 1 if not found
# Binary discovery cascade
find_safe_run_binary() {
  # 1. Environment override (highest priority)
  if [ -n "${SAFE_RUN_BIN:-}" ]; then
    echo "$SAFE_RUN_BIN"
    return 0
  fi
  
  # 2. Dev mode: ./rust/target/release/safe-run (relative to repo root)
  # On Windows, check for both safe-run and safe-run.exe
  if [ -n "$REPO_ROOT" ]; then
    if [ -x "$REPO_ROOT/rust/target/release/safe-run" ]; then
      echo "$REPO_ROOT/rust/target/release/safe-run"
      return 0
    fi
    if [ "$IS_WINDOWS" -eq 1 ] && [ -x "$REPO_ROOT/rust/target/release/safe-run.exe" ]; then
      echo "$REPO_ROOT/rust/target/release/safe-run.exe"
      return 0
    fi
  fi
  
  # 3. CI artifact: ./dist/<os>/<arch>/safe-run (platform-specific)
  # On Windows, check for both safe-run and safe-run.exe
  if [ -n "$REPO_ROOT" ] && [ "$PLATFORM" != "unknown/unknown" ]; then
    local ci_bin="$REPO_ROOT/dist/$PLATFORM/safe-run"
    if [ -x "$ci_bin" ]; then
      echo "$ci_bin"
      return 0
    fi
    if [ "$IS_WINDOWS" -eq 1 ]; then
      local ci_bin_exe="$REPO_ROOT/dist/$PLATFORM/safe-run.exe"
      if [ -x "$ci_bin_exe" ]; then
        echo "$ci_bin_exe"
        return 0
      fi
    fi
  fi
  
  # 4. PATH lookup (system-wide installation)
  if command -v safe-run >/dev/null 2>&1; then
    command -v safe-run
    return 0
  fi
  
  # 5. Not found - caller will display error
  return 1
}

#
# MAIN EXECUTION
# Finds binary, displays error if not found, then execs Rust tool
# Using 'exec' replaces this shell process, preserving exit codes and signals
#

# Main execution
BINARY="$(find_safe_run_binary)" || {
  # Print actionable error message on binary not found
  # Exit code 127 follows shell convention for "command not found"
  cat >&2 <<'EOF'
ERROR: Rust canonical tool not found.

Searched locations:
  1. SAFE_RUN_BIN env var (not set or invalid)
  2. ./rust/target/release/safe-run (not found)
  3. ./dist/<os>/<arch>/safe-run (not found)
  4. PATH lookup (not found)

To install:
  1. Clone the repository
  2. cd rust/
  3. cargo build --release

Or download a pre-built binary from:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases

For more information, see:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/rust-canonical-tool.md
EOF
  exit 127
}

# Invoke the Rust canonical tool with all arguments passed through
# The 'run' subcommand is required by the Rust CLI structure
exec "$BINARY" run "$@"
