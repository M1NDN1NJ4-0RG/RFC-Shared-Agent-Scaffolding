#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
export SRC_SAFE_RUN="${SRC_SAFE_RUN:-$ROOT/scripts/safe-run.pl}"
export SRC_SAFE_ARCHIVE="${SRC_SAFE_ARCHIVE:-$ROOT/scripts/safe-archive.pl}"
export SRC_SAFE_CHECK="${SRC_SAFE_CHECK:-$ROOT/scripts/safe-check.pl}"
export SRC_PREFLIGHT="${SRC_PREFLIGHT:-$ROOT/scripts/preflight_automerge_ruleset.pl}"

cd "$ROOT"

if command -v prove >/dev/null 2>&1; then
  prove -v -I t/lib t/*.t
else
  for f in t/*.t; do
    perl -I t/lib "$f"
  done
fi
