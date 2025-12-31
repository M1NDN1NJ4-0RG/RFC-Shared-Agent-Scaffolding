#!/usr/bin/env bash
# DESCRIPTION:
#   Bootstrap the repo-lint toolchain in a local Python virtual environment.
#   This script locates the repository root, creates a .venv if needed,
#   installs repo-lint into that environment, verifies it is on PATH,
#   and then runs repo-lint install (if supported) followed by
#   repo-lint check --ci.
#
# USAGE:
#   From anywhere inside the repository:
#     scripts/bootstrap-repo-cli.sh
#     ./scripts/bootstrap-repo-cli.sh
#
# INPUTS:
#   Arguments:
#     None.
#   Environment variables:
#     None.
#
# OUTPUTS:
#   Stdout:
#     Human-readable progress logs prefixed with "[bootstrap]".
#   Stderr:
#     Warnings and errors prefixed with "[bootstrap][WARN]" or
#     "[bootstrap][ERROR]".
#   Exit codes:
#     0  Success.
#     1  Generic failure.
#    10  Repository root could not be located.
#    11  Could not determine install target (no packaging metadata found).
#    12  pip install -e failed.
#    13  repo-lint is not runnable after install.
#    14  repo-lint exists but failed to run --help.
#    20  repo-lint check --ci FAILED.
#
# EXAMPLES:
#   # Run from any subdirectory within the repository
#   scripts/bootstrap-repo-cli.sh
#
#   # Run from the repository root
#   ./scripts/bootstrap-repo-cli.sh
#
# ---------------------------------------------------------------------------

set -Eeuo pipefail

VENV_DIR=".venv"

# Print log message to stdout
#
# Arguments:
#   $* - Log message
#
# Returns:
#   0 (always succeeds)
log() { printf "\n[bootstrap] %s\n" "$*"; }

# Print warning message to stderr
#
# Arguments:
#   $* - Warning message
#
# Returns:
#   0 (always succeeds)
warn() { printf "\n[bootstrap][WARN] %s\n" "$*" >&2; }

# Print error message and exit
#
# Arguments:
#   $1 - Error message
#   $2 - Exit code (default: 1)
#
# Returns:
#   Never returns (exits process)
die() {
	printf "\n[bootstrap][ERROR] %s\n" "$*" >&2
	exit "${2:-1}"
}

# Find repo root by walking up until we hit .git or pyproject.toml or README.md
find_repo_root() {
	local d
	d="$(pwd)"
	while true; do
		if [[ -d "$d/.git" || -f "$d/pyproject.toml" || -f "$d/README.md" ]]; then
			printf "%s" "$d"
			return 0
		fi
		[[ "$d" == "/" ]] && return 1
		d="$(cd "$d/.." && pwd)"
	done
}

REPO_ROOT="$(find_repo_root || true)"
[[ -n "$REPO_ROOT" ]] || die "Could not find repo root. Run from inside the repo." 10
cd "$REPO_ROOT"
log "Repo root: $REPO_ROOT"

# Create venv if needed
if [[ ! -d "$VENV_DIR" ]]; then
	log "Creating venv: $VENV_DIR"
	python3 -m venv "$VENV_DIR"
fi

# Activate venv
log "Activating venv"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "Upgrading pip tooling"
python3 -m pip install -U pip setuptools wheel

# Decide install target:
# - Prefer repo root if it looks like a Python package
# - Prefer tools/repo_cli if it has its own packaging metadata
#   (and log when it overrides repo-root selection for clarity)
INSTALL_TARGET=""
ROOT_PKG_FOUND=0
TOOLS_PKG_FOUND=0

# Heuristic A: repo root appears to be a Python package (pyproject/setup.py/setup.cfg)
if [[ -f "$REPO_ROOT/pyproject.toml" || -f "$REPO_ROOT/setup.py" || -f "$REPO_ROOT/setup.cfg" ]]; then
	ROOT_PKG_FOUND=1
fi

# Heuristic B: explicit tools/repo_cli packaging (prefer if it exists)
if [[ -d "$REPO_ROOT/tools/repo_cli" ]]; then
	if [[ -f "$REPO_ROOT/tools/repo_cli/pyproject.toml" || -f "$REPO_ROOT/tools/repo_cli/setup.py" || -f "$REPO_ROOT/tools/repo_cli/setup.cfg" ]]; then
		TOOLS_PKG_FOUND=1
	fi
fi

# Apply precedence rules based on detected packaging metadata.
if [[ "$ROOT_PKG_FOUND" -eq 1 && "$TOOLS_PKG_FOUND" -eq 1 ]]; then
	log "Found packaging metadata in repo root and tools/repo_cli; preferring tools/repo_cli as install target."
	INSTALL_TARGET="$REPO_ROOT/tools/repo_cli"
elif [[ "$TOOLS_PKG_FOUND" -eq 1 ]]; then
	INSTALL_TARGET="$REPO_ROOT/tools/repo_cli"
elif [[ "$ROOT_PKG_FOUND" -eq 1 ]]; then
	INSTALL_TARGET="$REPO_ROOT"
fi

[[ -n "$INSTALL_TARGET" ]] || die "Could not determine where to install repo-lint (no packaging metadata found)." 11

log "Installing repo-lint (editable) from: $INSTALL_TARGET"
python3 -m pip install -e "$INSTALL_TARGET" || die "pip install -e failed for: $INSTALL_TARGET" 12

log "Verifying repo-lint is on PATH"
if ! command -v repo-lint >/dev/null 2>&1; then
	warn "repo-lint not found on PATH after install."
	warn "Diagnostics:"
	echo "  python: $(python3 -c 'import sys; print(sys.executable)')" >&2
	echo "  pip:    $(python3 -m pip --version)" >&2
	echo "  PATH:   $PATH" >&2
	if python3 -m pip show repo-lint >/dev/null 2>&1; then
		python3 -m pip show repo-lint >&2
	fi
	if python3 -m pip show repo_lint >/dev/null 2>&1; then
		python3 -m pip show repo_lint >&2
	fi
	die "repo-lint is not runnable. Fix packaging/venv/PATH first." 13
fi

repo-lint --help >/dev/null 2>&1 || die "repo-lint exists but failed to run: repo-lint --help" 14
log "repo-lint OK: $(command -v repo-lint)"

# If repo-lint has an install command, run it
if repo-lint install --help >/dev/null 2>&1; then
	log "Running: repo-lint install"
	if ! repo-lint install; then
		die "repo-lint install failed. Missing tools are BLOCKER. Install missing tools and rerun." 15
	fi
else
	log "repo-lint install not available; skipping."
fi

# Enforcement gate
log "Running: repo-lint check --ci"
repo-lint check --ci || die "repo-lint check --ci FAILED. Fix issues and rerun until PASS." 20

log "SUCCESS: repo-lint installed + repo-lint check --ci PASS"
