#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

ROOT="$(cd .. && pwd)"
CHECK="${ROOT}/scripts/safe-check.sh"

test_safe_check_ok() {
  local tmp
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mkdir -p scripts .agent/FAIL-LOGS .agent/FAIL-ARCHIVE
    cp -f "$ROOT/scripts/"*.sh scripts/
    chmod +x scripts/*.sh
    scripts/safe-check.sh >/dev/null
  )
}

t "safe-check: exits 0 on healthy environment" test_safe_check_ok
summary
