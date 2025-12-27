#!/usr/bin/env bash
# safe-run.sh - Thin invoker for Rust canonical safe-run tool
#
# This wrapper discovers and invokes the Rust canonical implementation.
# It does NOT reimplement any contract logic.
#
# Binary Discovery Order (per docs/wrapper-discovery.md):
#   1. SAFE_RUN_BIN env var (if set)
#   2. ./target/release/safe-run (dev mode, relative to repo root)
#   3. ./dist/<os>/<arch>/safe-run (CI artifacts)
#   4. PATH lookup (system installation)
#   5. Error with actionable instructions (exit 127)

set -euo pipefail

# Determine repository root (walk up from script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

# Detect OS and architecture for CI artifact path
detect_platform() {
  local os arch
  case "$(uname -s)" in
    Linux*)  os="linux" ;;
    Darwin*) os="macos" ;;
    CYGWIN*|MINGW*|MSYS*) os="windows" ;;
    *) os="unknown" ;;
  esac
  
  case "$(uname -m)" in
    x86_64|amd64) arch="x86_64" ;;
    aarch64|arm64) arch="aarch64" ;;
    *) arch="unknown" ;;
  esac
  
  echo "${os}/${arch}"
}

PLATFORM="$(detect_platform)"

# Binary discovery cascade
find_safe_run_binary() {
  # 1. Environment override
  if [ -n "${SAFE_RUN_BIN:-}" ]; then
    echo "$SAFE_RUN_BIN"
    return 0
  fi
  
  # 2. Dev mode: ./target/release/safe-run (relative to repo root)
  if [ -n "$REPO_ROOT" ] && [ -x "$REPO_ROOT/rust/target/release/safe-run" ]; then
    echo "$REPO_ROOT/rust/target/release/safe-run"
    return 0
  fi
  
  # 3. CI artifact: ./dist/<os>/<arch>/safe-run
  if [ -n "$REPO_ROOT" ] && [ "$PLATFORM" != "unknown/unknown" ]; then
    local ci_bin="$REPO_ROOT/dist/$PLATFORM/safe-run"
    if [ -x "$ci_bin" ]; then
      echo "$ci_bin"
      return 0
    fi
  fi
  
  # 4. PATH lookup
  if command -v safe-run >/dev/null 2>&1; then
    command -v safe-run
    return 0
  fi
  
  # 5. Not found
  return 1
}

# Main execution
BINARY="$(find_safe_run_binary)" || {
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
