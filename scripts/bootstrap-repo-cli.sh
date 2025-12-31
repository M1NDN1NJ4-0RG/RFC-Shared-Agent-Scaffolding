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
#    15  repo-lint install failed.
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
	printf "\n[bootstrap][ERROR] %s\n" "$1" >&2
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

	# Add .venv-lint/bin to PATH so Python linting tools are available
	if [[ -d "$REPO_ROOT/.venv-lint/bin" ]]; then
		export PATH="$REPO_ROOT/.venv-lint/bin:$PATH"
		log "Added .venv-lint/bin to PATH for Python linting tools"
	fi
else
	log "repo-lint install not available; skipping."
fi

# Install additional required tools
log "Installing additional required tools..."

# Install shellcheck (if not already installed)
if ! command -v shellcheck >/dev/null 2>&1; then
	log "Installing shellcheck..."
	if command -v apt-get >/dev/null 2>&1; then
		sudo apt-get update -qq && sudo apt-get install -y -qq shellcheck
	else
		warn "shellcheck not found and apt-get not available. Please install manually."
	fi
fi

# Install shfmt (if not already installed)
if ! command -v shfmt >/dev/null 2>&1; then
	log "Installing shfmt..."
	if command -v go >/dev/null 2>&1; then
		go install mvdan.cc/sh/v3/cmd/shfmt@latest
		export PATH="$HOME/go/bin:$PATH"
	else
		warn "shfmt requires Go to be installed. Please install Go first or install shfmt manually."
	fi
fi

# Install rgrep/ripgrep if not already installed
if ! command -v rg >/dev/null 2>&1; then
	log "Installing ripgrep (rg)..."
	if command -v apt-get >/dev/null 2>&1; then
		sudo apt-get install -y -qq ripgrep
	else
		warn "ripgrep not found and apt-get not available. Please install manually."
	fi
fi

# Install PowerShell (pwsh) if not already installed
if ! command -v pwsh >/dev/null 2>&1; then
	log "Installing PowerShell (pwsh)..."
	if command -v apt-get >/dev/null 2>&1; then
		# Install prerequisites
		sudo apt-get install -y -qq wget apt-transport-https software-properties-common
		# Download Microsoft repository GPG keys
		wget -q "https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb" -O /tmp/packages-microsoft-prod.deb
		sudo dpkg -i /tmp/packages-microsoft-prod.deb
		rm /tmp/packages-microsoft-prod.deb
		# Install PowerShell
		sudo apt-get update -qq && sudo apt-get install -y -qq powershell
	else
		warn "PowerShell not found and apt-get not available. Please install manually."
	fi
fi

# Install PSScriptAnalyzer (PowerShell module)
if command -v pwsh >/dev/null 2>&1; then
	log "Installing PSScriptAnalyzer..."
	if ! pwsh -Command "Get-Module -ListAvailable -Name PSScriptAnalyzer" >/dev/null 2>&1; then
		pwsh -Command "Install-Module -Name PSScriptAnalyzer -MinimumVersion 1.23.0 -Scope CurrentUser -Force" || warn "Failed to install PSScriptAnalyzer"
	else
		log "PSScriptAnalyzer already installed"
	fi
else
	warn "PowerShell (pwsh) not available. Skipping PSScriptAnalyzer installation."
fi

# Install Perl::Critic and PPI
if command -v cpan >/dev/null 2>&1; then
	log "Installing Perl::Critic and PPI..."
	# Install cpanminus for faster installation
	if ! command -v cpanm >/dev/null 2>&1; then
		sudo cpan -T App::cpanminus 2>/dev/null || warn "Failed to install cpanminus"
	fi

	if command -v cpanm >/dev/null 2>&1; then
		cpanm --quiet --notest Perl::Critic PPI 2>/dev/null || warn "Failed to install Perl modules via cpanm"
	else
		sudo cpan -T Perl::Critic PPI 2>/dev/null || warn "Failed to install Perl modules via cpan"
	fi
elif command -v apt-get >/dev/null 2>&1; then
	log "Installing Perl::Critic via apt-get..."
	sudo apt-get install -y -qq libperl-critic-perl libppi-perl || warn "Failed to install Perl modules"
else
	warn "Neither cpan nor apt-get available. Cannot install Perl::Critic and PPI."
fi

log "Tool installation complete. Verifying..."
if command -v shellcheck >/dev/null 2>&1; then
	log "✓ shellcheck: $(command -v shellcheck)"
else
	warn "✗ shellcheck not found"
fi
if command -v shfmt >/dev/null 2>&1; then
	log "✓ shfmt: $(command -v shfmt)"
else
	warn "✗ shfmt not found"
fi
if command -v rg >/dev/null 2>&1; then
	log "✓ ripgrep: $(command -v rg)"
else
	warn "✗ ripgrep not found"
fi
if command -v pwsh >/dev/null 2>&1; then
	log "✓ PowerShell: $(command -v pwsh)"
else
	warn "✗ PowerShell not found"
fi
if command -v perl >/dev/null 2>&1 && perl -MPerl::Critic -e 1 2>/dev/null; then
	log "✓ Perl::Critic installed"
else
	warn "✗ Perl::Critic not found"
fi

# Enforcement gate - verify tools are working
log "Running: repo-lint check --ci --only bash"
if repo-lint check --ci --only bash; then
	log "SUCCESS: All tools installed and bash linting works"
else
	warn "Bash linting had issues, but continuing..."
fi

log "SUCCESS: Bootstrap complete!"
log "Tools installed:"
log "  - repo-lint: $(command -v repo-lint)"
log "  - Python tools (black, ruff, pylint, yamllint, pytest) in: .venv-lint/bin"
log "  - shellcheck: $(command -v shellcheck 2>/dev/null || echo 'not found')"
log "  - shfmt: $(command -v shfmt 2>/dev/null || echo 'not found')"
log "  - ripgrep: $(command -v rg 2>/dev/null || echo 'not found')"
log "  - PowerShell: $(command -v pwsh 2>/dev/null || echo 'not found')"
log "  - Perl::Critic: $(perl -MPerl::Critic -e 1 2>/dev/null && echo 'installed' || echo 'not found')"
log ""
log "To use in your shell session:"
log "  source $REPO_ROOT/.venv/bin/activate"
log "  export PATH=\"$REPO_ROOT/.venv-lint/bin:\$HOME/go/bin:\$PATH\""
