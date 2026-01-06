#!/usr/bin/env bash
# Wrapper for Rust bootstrapper (transition period)
#
# This script provides backwards compatibility during the migration
# from the legacy Bash bootstrapper to the new Rust implementation.
#
# Resolution order:
# 1) $BOOTSTRAP_BIN (explicit override)
# 2) $REPO_ROOT/.bootstrap/bin/bootstrap (downloaded/prebuilt)
# 3) $REPO_ROOT/target/release/bootstrap-repo-cli (dev-only)
# 4) legacy Bash bootstrapper
#
# Escape hatch: Set BOOTSTRAP_FORCE_LEGACY=1 to use legacy Bash version

set -euo pipefail

# Find script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Explicit escape hatch to legacy Bash version
if [ "${BOOTSTRAP_FORCE_LEGACY:-0}" = "1" ]; then
    echo "[WARN] BOOTSTRAP_FORCE_LEGACY=1 set; using legacy Bash version" >&2
    
    # Move current script aside and exec the legacy one
    LEGACY_SCRIPT="$SCRIPT_DIR/.legacy/bootstrap-repo-lint-toolchain.sh"
    if [ -f "$LEGACY_SCRIPT" ]; then
        exec "$LEGACY_SCRIPT" "$@"
    else
        echo "[ERROR] Legacy bootstrapper not found at $LEGACY_SCRIPT" >&2
        echo "[ERROR] Cannot honor BOOTSTRAP_FORCE_LEGACY=1" >&2
        exit 1
    fi
fi

# Build list of candidate binaries to try (in order of preference)
CANDIDATES=()

# 1) Explicit override via environment variable
if [ -n "${BOOTSTRAP_BIN:-}" ]; then
    CANDIDATES+=("$BOOTSTRAP_BIN")
fi

# 2) Downloaded/prebuilt binary (standard location)
CANDIDATES+=("$REPO_ROOT/.bootstrap/bin/bootstrap")

# 3) Development build (for local testing)
CANDIDATES+=("$REPO_ROOT/target/release/bootstrap-repo-cli")

# Try each candidate in order
for bin in "${CANDIDATES[@]}"; do
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        # Found a working binary - delegate to it
        # Map legacy flags to Rust binary subcommands
        exec "$bin" install "$@"
    fi
done

# No Rust binary found - fall back to legacy Bash version
echo "[WARN] Rust bootstrapper not found, using legacy Bash version" >&2
echo "[INFO] Searched for binaries at:" >&2
for bin in "${CANDIDATES[@]}"; do
    echo "[INFO]   - $bin (not found or not executable)" >&2
done

# Execute legacy script inline (it's the current script before migration)
# For transition period, we can exec a separate legacy copy or just run inline

# NOTE: During transition, the legacy Bash code should be moved to
# scripts/.legacy/bootstrap-repo-lint-toolchain.sh
LEGACY_SCRIPT="$SCRIPT_DIR/.legacy/bootstrap-repo-lint-toolchain.sh"
if [ -f "$LEGACY_SCRIPT" ]; then
    exec "$LEGACY_SCRIPT" "$@"
else
    echo "[ERROR] Neither Rust binary nor legacy Bash bootstrapper found" >&2
    echo "[ERROR] This script is a wrapper that requires one of the following:" >&2
    echo "[ERROR]   1. Rust binary at one of the candidate locations above" >&2
    echo "[ERROR]   2. Legacy Bash script at $LEGACY_SCRIPT" >&2
    exit 1
fi
