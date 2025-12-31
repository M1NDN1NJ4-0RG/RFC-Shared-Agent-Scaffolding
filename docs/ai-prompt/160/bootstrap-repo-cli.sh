#!/usr/bin/env bash
set -Eeuo pipefail

# bootstrap-repo-cli.sh
# Minimal bootstrap for Copilot VM:
# - Create/activate .venv
# - Install repo-cli (editable) from repo root or tools/repo_cli
# - Verify repo-cli on PATH
# - Run repo-cli install (if supported)
# - Run repo-cli check --ci

VENV_DIR=".venv"

log()  { printf "\n[bootstrap] %s\n" "$*"; }
warn() { printf "\n[bootstrap][WARN] %s\n" "$*" >&2; }
die()  { printf "\n[bootstrap][ERROR] %s\n" "$*" >&2; exit "${2:-1}"; }

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

# Decide install target: prefer repo root, else tools/repo_cli
INSTALL_TARGET=""

# Heuristic A: repo root appears to be a Python package (pyproject/setup.py/setup.cfg)
if [[ -f "$REPO_ROOT/pyproject.toml" || -f "$REPO_ROOT/setup.py" || -f "$REPO_ROOT/setup.cfg" ]]; then
  INSTALL_TARGET="$REPO_ROOT"
fi

# Heuristic B: explicit tools/repo_cli packaging (prefer if it exists)
if [[ -d "$REPO_ROOT/tools/repo_cli" ]]; then
  if [[ -f "$REPO_ROOT/tools/repo_cli/pyproject.toml" || -f "$REPO_ROOT/tools/repo_cli/setup.py" || -f "$REPO_ROOT/tools/repo_cli/setup.cfg" ]]; then
    INSTALL_TARGET="$REPO_ROOT/tools/repo_cli"
  fi
fi

[[ -n "$INSTALL_TARGET" ]] || die "Could not determine where to install repo-cli (no packaging metadata found)." 11

log "Installing repo-cli (editable) from: $INSTALL_TARGET"
python3 -m pip install -e "$INSTALL_TARGET" || die "pip install -e failed for: $INSTALL_TARGET" 12

log "Verifying repo-cli is on PATH"
if ! command -v repo-cli >/dev/null 2>&1; then
  warn "repo-cli not found on PATH after install."
  warn "Diagnostics:"
  echo "  python: $(python3 -c 'import sys; print(sys.executable)')" >&2
  echo "  pip:    $(python3 -m pip --version)" >&2
  echo "  PATH:   $PATH" >&2
  python3 -m pip show repo-cli >/dev/null 2>&1 && python3 -m pip show repo-cli >&2 || true
  python3 -m pip show repo_cli >/dev/null 2>&1 && python3 -m pip show repo_cli >&2 || true
  die "repo-cli is not runnable. Fix packaging/venv/PATH first." 13
fi

repo-cli --help >/dev/null 2>&1 || die "repo-cli exists but failed to run: repo-cli --help" 14
log "repo-cli OK: $(command -v repo-cli)"

# If repo-cli has an install command, run it
if repo-cli install --help >/dev/null 2>&1; then
  log "Running: repo-cli install"
  if ! repo-cli install; then
    warn "repo-cli install failed. You may need to install missing external tools manually."
    # Do not exit here; repo-cli check will be the enforcement gate.
  fi
else
  log "repo-cli install not available; skipping."
fi

# Enforcement gate
log "Running: repo-cli check --ci"
repo-cli check --ci || die "repo-cli check --ci FAILED. Fix issues and rerun until PASS." 20

log "SUCCESS: repo-cli installed + repo-cli check --ci PASS"
