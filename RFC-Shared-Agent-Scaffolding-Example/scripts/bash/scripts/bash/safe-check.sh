#!/usr/bin/env bash
# safe-check.sh
# Lightweight contract verification for the Bash implementation.

set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL_DIR="$ROOT_DIR/.agent/FAIL-LOGS"
ARCH_DIR="$ROOT_DIR/.agent/FAIL-ARCHIVE"

mkdir -p "$FAIL_DIR" "$ARCH_DIR"

# 1) Success run: should create no FAIL-LOG artifacts
before_count=$(find "$FAIL_DIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
"$ROOT_DIR/scripts/bash/safe-run.sh" bash -c 'echo ok; exit 0' >/dev/null
after_count=$(find "$FAIL_DIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$after_count" -ne "$before_count" ]; then
  echo "FAIL: safe-run created artifacts on success" >&2
  exit 1
fi

# 2) Failure run: must create a FAIL-LOG file
"$ROOT_DIR/scripts/bash/safe-run.sh" bash -c 'echo out; echo err 1>&2; exit 42' >/dev/null || true
newest=$(ls -1t "$FAIL_DIR" 2>/dev/null | head -n 1 || true)
if [ -z "$newest" ]; then
  echo "FAIL: safe-run did not create failure log" >&2
  exit 1
fi

# 3) Archive should move it, no clobber
"$ROOT_DIR/scripts/bash/safe-archive.sh" --all >/dev/null
if [ -e "$FAIL_DIR/$newest" ]; then
  echo "FAIL: safe-archive did not move log" >&2
  exit 1
fi
if [ ! -e "$ARCH_DIR/$newest" ] && [ ! -e "$ARCH_DIR/${newest}.gz" ] && [ ! -e "$ARCH_DIR/${newest}.xz" ] && [ ! -e "$ARCH_DIR/${newest}.zst" ]; then
  echo "FAIL: safe-archive did not create archived file" >&2
  exit 1
fi

echo "OK: Bash safe-run/safe-archive contract looks sane."
