#!/usr/bin/env bash
# safe-run.sh
# Runs a command verbatim. If it fails, capture combined stdout+stderr to a FAIL-LOG file.
# If it succeeds, create no artifacts.
#
# Env:
#   SAFE_LOG_DIR       default: .agent/FAIL-LOGS
#   SAFE_SNIPPET_LINES default: 0  (if >0, prints tail snippet to stderr on failure)

set -u

SAFE_LOG_DIR="${SAFE_LOG_DIR:-.agent/FAIL-LOGS}"
SAFE_SNIPPET_LINES="${SAFE_SNIPPET_LINES:-0}"

if [ "$#" -lt 1 ]; then
  echo "usage: safe-run.sh <command> [args...]" >&2
  exit 2
fi

mkdir -p "$SAFE_LOG_DIR" 2>/dev/null || true

# Temp file for streaming + later save-on-failure.
# mktemp exists on macOS + Linux.
TMP="$(mktemp -t safe-run.XXXXXX)" || exit 1

# Build a stable-ish name (timestamp + pid).
TS="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || date +%Y%m%dT%H%M%SZ)"
PID="$$"
BASE="$TS-pid$PID"

ABORTED="0"

cleanup_tmp() {
  [ -f "$TMP" ] && rm -f "$TMP" 2>/dev/null || true
}

save_abort_log() {
  # If we have any buffered output, preserve it.
  local out="$SAFE_LOG_DIR/${BASE}-ABORTED-fail.txt"
  if [ -f "$TMP" ]; then
    # no-clobber safety: if name exists, append counter.
    local n=0
    local cand="$out"
    while [ -e "$cand" ]; do
      n=$((n+1))
      cand="$SAFE_LOG_DIR/${BASE}-ABORTED-fail-$n.txt"
    done
    mv "$TMP" "$cand" 2>/dev/null || cp "$TMP" "$cand" || true
  fi
}

on_int() {
  ABORTED="1"
  # Don't echo extra junk unless we must.
  save_abort_log
  cleanup_tmp
  exit 130
}

on_term() {
  ABORTED="1"
  save_abort_log
  cleanup_tmp
  exit 143
}

trap on_int INT
trap on_term TERM

# Stream combined output to stdout AND to temp.
# Need exit code of the command, not tee.
# IMPORTANT: do NOT wrap this pipeline in a subshell, or PIPESTATUS will be lost.
"$@" 2>&1 | tee "$TMP"
CMD_RC=${PIPESTATUS[0]}

if [ "$CMD_RC" -eq 0 ]; then
  cleanup_tmp
  exit 0
fi

# Failure: move temp into FAIL-LOGS.
OUT="$SAFE_LOG_DIR/${BASE}-fail.txt"
# no-clobber
n=0
cand="$OUT"
while [ -e "$cand" ]; do
  n=$((n+1))
  cand="$SAFE_LOG_DIR/${BASE}-fail-$n.txt"
done
mv "$TMP" "$cand" 2>/dev/null || cp "$TMP" "$cand" || true

# Optional tail snippet to stderr (useful for CI without opening the file).
if [ "$SAFE_SNIPPET_LINES" -gt 0 ] 2>/dev/null; then
  echo "--- safe-run failure tail ($SAFE_SNIPPET_LINES lines) ---" >&2
  tail -n "$SAFE_SNIPPET_LINES" "$cand" >&2 || true
  echo "--- end tail ---" >&2
fi

echo "safe-run: command failed (rc=$CMD_RC). log: $cand" >&2
exit "$CMD_RC"
