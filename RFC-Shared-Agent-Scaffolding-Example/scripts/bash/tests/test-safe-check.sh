#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

ROOT="$(cd .. && pwd)"
CHECK="${ROOT}/scripts/safe-check.sh"

# Compute repo root and find Rust binary for wrapper discovery
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

test_safe_check_ok() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p scripts .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    cp -f "$ROOT/scripts/"*.sh scripts/
    chmod +x scripts/*.sh
    # Set SAFE_RUN_BIN so the wrapper can find Rust binary in isolated temp dir
    SAFE_RUN_BIN="$SAFE_RUN_BIN_PATH" scripts/safe-check.sh >/dev/null
  )
}

t "safe-check: exits 0 on healthy environment" test_safe_check_ok
summary
