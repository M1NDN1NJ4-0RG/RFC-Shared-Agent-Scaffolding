#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
source "./lib.sh"

# Run each test file in a fresh bash to avoid state leakage.
status=0
for tf in ./test_*.sh; do
  [[ -f "$tf" ]] || continue
  echo "==> Running $tf" >&2
  if ! bash "$tf"; then
    status=1
  fi
done

# Each test file prints its own summary; this is a belt-and-suspenders exit.
exit "$status"
