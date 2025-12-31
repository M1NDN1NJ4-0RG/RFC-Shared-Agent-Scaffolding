#!/usr/bin/env bash
#
# bootstrap-repo-lint-toolchain.sh - Session-start compliance gate for repo-lint toolchain
#
# DESCRIPTION:
#   Automates the setup of the repo-lint toolchain and all required development
#   tools for contributing to this repository. Designed to be run at the start
#   of every Copilot agent session to ensure a consistent, compliant environment.
#
#   This script handles:
#   - Python virtual environment (.venv) creation and activation
#   - repo-lint package installation in editable mode
#   - Verification that repo-lint is functional and on PATH
#   - Python toolchain installation (black, ruff, pylint, yamllint, pytest)
#
#   Future phases will add installation of system tools (shellcheck, shfmt,
#   ripgrep, PowerShell, Perl modules) and final verification gate.
#
# USAGE:
#   ./scripts/bootstrap-repo-lint-toolchain.sh
#   bash scripts/bootstrap-repo-lint-toolchain.sh
#
# INPUTS:
#   Arguments:
#     None (planned: --force, --skip-verify)
#
#   Environment Variables:
#     None (uses auto-detected repo root)
#
# OUTPUTS:
#   Exit Codes:
#     0   Success - all operations completed
#     1   Generic failure
#     10  Repository root could not be located
#     11  Virtual environment creation failed
#     12  No valid install target found (missing pyproject.toml at repo root)
#     13  repo-lint not found on PATH after installation
#     14  repo-lint exists but --help command failed
#     15  Python toolchain installation failed
#
#   Stdout:
#     Progress messages prefixed with [bootstrap]
#     Success summary with paths to installed components
#
#   Stderr:
#     Error messages prefixed with [bootstrap][ERROR]
#     Warning messages prefixed with [bootstrap][WARN]
#
#   Side Effects:
#     Creates .venv/ directory at repository root
#     Installs repo-lint package in editable mode
#     Modifies current shell's PATH (via venv activation)
#
# EXAMPLES:
#   # Run from repository root
#   ./scripts/bootstrap-repo-lint-toolchain.sh
#
#   # Run from any subdirectory
#   bash scripts/bootstrap-repo-lint-toolchain.sh
#
#   # Check exit code
#   if ./scripts/bootstrap-repo-lint-toolchain.sh; then
#       echo "Bootstrap successful"
#   fi
#
# NOTES:
#   - Script is idempotent: safe to run multiple times
#   - Requires Python 3 with venv module
#   - Must be run from within the repository
#   - Phase 1 + Phase 2 implementation (core + Python toolchain)
#
# PLATFORM COMPATIBILITY:
#   - Linux (tested on Ubuntu/Debian)
#   - macOS (should work, not extensively tested)
#   - Requires: bash, python3, python3-venv

set -euo pipefail

# Constants
readonly VENV_DIR=".venv"

# ============================================================================
# Logging Functions
# ============================================================================

# log - Print informational message to stdout
#
# DESCRIPTION:
#   Prints a progress message prefixed with [bootstrap] to stdout.
#
# INPUTS:
#   $1 - Message string to print
#
# OUTPUTS:
#   Stdout: Formatted log message
#
# EXAMPLES:
#   log "Creating virtual environment"
log() {
	echo "[bootstrap] $1"
}

# warn - Print warning message to stderr
#
# DESCRIPTION:
#   Prints a warning message prefixed with [bootstrap][WARN] to stderr.
#
# INPUTS:
#   $1 - Warning message string
#
# OUTPUTS:
#   Stderr: Formatted warning message
#
# EXAMPLES:
#   warn "Tool not found, using fallback"
warn() {
	echo "[bootstrap][WARN] $1" >&2
}

# die - Print error message and exit with code
#
# DESCRIPTION:
#   Prints an error message prefixed with [bootstrap][ERROR] to stderr
#   and exits the script with the specified exit code.
#
# INPUTS:
#   $1 - Error message string
#   $2 - Exit code (integer)
#
# OUTPUTS:
#   Stderr: Formatted error message
#   Exits with specified code
#
# EXAMPLES:
#   die "Repository root not found" 10
die() {
	local msg="$1"
	local code="${2:-1}"
	echo "[bootstrap][ERROR] $msg" >&2
	exit "$code"
}

# ============================================================================
# Repository Discovery
# ============================================================================

# find_repo_root - Locate repository root directory
#
# DESCRIPTION:
#   Walks up the directory tree from current directory to find the repository
#   root. Looks for .git directory, pyproject.toml, or README.md as markers.
#   Returns the absolute path to the repository root.
#
# INPUTS:
#   None (uses current working directory as starting point)
#
# OUTPUTS:
#   Exit Code:
#     0   Repository root found
#     10  Repository root not found (reached filesystem root)
#
#   Stdout:
#     Absolute path to repository root
#
#   Stderr:
#     Error message if root not found
#
# EXAMPLES:
#   repo_root=$(find_repo_root)
#   cd "$repo_root"
find_repo_root() {
	local current_dir
	current_dir="$(pwd)"

	while true; do
		# Check for repository markers
		if [[ -d "$current_dir/.git" ]] ||
			[[ -f "$current_dir/pyproject.toml" ]] ||
			[[ -f "$current_dir/README.md" ]]; then
			echo "$current_dir"
			return 0
		fi

		# Check if we've reached filesystem root
		if [[ "$current_dir" == "/" ]]; then
			die "Could not find repository root (no .git, pyproject.toml, or README.md found)" 10
		fi

		# Move up one directory
		current_dir="$(dirname "$current_dir")"
	done
}

# ============================================================================
# Virtual Environment Management
# ============================================================================

# ensure_venv - Create virtual environment if it doesn't exist
#
# DESCRIPTION:
#   Creates a Python virtual environment at .venv/ in the repository root
#   if it doesn't already exist. Verifies that the venv contains a functional
#   Python executable. Skips creation if venv already exists and is valid.
#
# INPUTS:
#   $1 - Repository root path
#
# OUTPUTS:
#   Exit Code:
#     0   Virtual environment exists or was created successfully
#     11  Virtual environment creation failed
#
#   Stdout:
#     Progress messages about venv creation/verification
#
#   Side Effects:
#     Creates .venv/ directory with Python virtual environment
#
# EXAMPLES:
#   ensure_venv "$repo_root"
ensure_venv() {
	local repo_root="$1"
	local venv_path="$repo_root/$VENV_DIR"

	if [[ -d "$venv_path" ]] && [[ -x "$venv_path/bin/python3" ]]; then
		log "Virtual environment already exists: $venv_path"
		return 0
	fi

	log "Creating virtual environment: $venv_path"

	if ! python3 -m venv "$venv_path"; then
		die "Failed to create virtual environment at $venv_path" 11
	fi

	if [[ ! -x "$venv_path/bin/python3" ]]; then
		die "Virtual environment created but python3 not executable: $venv_path/bin/python3" 11
	fi

	log "Virtual environment created successfully"
}

# activate_venv - Activate virtual environment for current shell
#
# DESCRIPTION:
#   Activates the Python virtual environment by sourcing the activate script
#   and updating PATH. Verifies that activation succeeded by checking that
#   python3 now points to the venv's python3.
#
# INPUTS:
#   $1 - Repository root path
#
# OUTPUTS:
#   Exit Code:
#     0   Virtual environment activated successfully
#     11  Virtual environment activation failed
#
#   Stdout:
#     Confirmation message with venv path
#
#   Environment:
#     Updates PATH, VIRTUAL_ENV, and other venv-related variables
#
# EXAMPLES:
#   activate_venv "$repo_root"
#   which python3  # Should point to .venv/bin/python3
activate_venv() {
	local repo_root="$1"
	local venv_path="$repo_root/$VENV_DIR"
	local activate_script="$venv_path/bin/activate"

	if [[ ! -f "$activate_script" ]]; then
		die "Activate script not found: $activate_script" 11
	fi

	log "Activating virtual environment"

	# shellcheck disable=SC1090
	# shellcheck source=/dev/null
	source "$activate_script"

	# Verify activation by checking which python3 is in use
	local active_python
	active_python="$(command -v python3)"

	if [[ "$active_python" != "$venv_path/bin/python3" ]]; then
		warn "Virtual environment may not be properly activated"
		warn "Expected: $venv_path/bin/python3"
		warn "Got: $active_python"
	else
		log "Virtual environment activated: $active_python"
	fi
}

# ============================================================================
# repo-lint Installation
# ============================================================================

# determine_install_target - Find repo-lint package location
#
# DESCRIPTION:
#   Determines where to install repo-lint from by checking for pyproject.toml
#   in the repository root. The repo-lint package is defined in the root-level
#   pyproject.toml with tools.repo_lint as a package.
#
# INPUTS:
#   $1 - Repository root path
#
# OUTPUTS:
#   Exit Code:
#     0   Valid install target found
#     12  No valid install target found
#
#   Stdout:
#     Path to install target (repo root)
#
# EXAMPLES:
#   install_target=$(determine_install_target "$repo_root")
#   pip install -e "$install_target"
determine_install_target() {
	local repo_root="$1"

	# Check for pyproject.toml at repo root
	if [[ -f "$repo_root/pyproject.toml" ]]; then
		echo "$repo_root"
		return 0
	fi

	die "No valid install target found (no pyproject.toml at repo root)" 12
}

# install_repo_lint - Install repo-lint package in editable mode
#
# DESCRIPTION:
#   Upgrades pip/setuptools/wheel and installs the repo-lint package in
#   editable mode using pip install -e. Determines the install target
#   automatically and handles installation failures.
#
# INPUTS:
#   $1 - Repository root path
#
# OUTPUTS:
#   Exit Code:
#     0   repo-lint installed successfully
#     12  No valid install target found
#     13  Installation succeeded but repo-lint command not found
#
#   Stdout:
#     Progress messages about installation
#
#   Side Effects:
#     Installs packages in active virtual environment
#
# EXAMPLES:
#   install_repo_lint "$repo_root"
install_repo_lint() {
	local repo_root="$1"

	log "Upgrading pip, setuptools, and wheel"
	python3 -m pip install --upgrade pip setuptools wheel --quiet

	local install_target
	install_target=$(determine_install_target "$repo_root")

	log "Installing repo-lint from: $install_target"

	if ! python3 -m pip install -e "$install_target" --quiet; then
		die "Failed to install repo-lint package" 13
	fi

	log "repo-lint package installed successfully"

	# Verify installation
	if ! command -v repo-lint >/dev/null 2>&1; then
		die "repo-lint installed but command not found on PATH" 13
	fi
}

# ============================================================================
# repo-lint Verification
# ============================================================================

# verify_repo_lint - Verify repo-lint is functional
#
# DESCRIPTION:
#   Verifies that the repo-lint command exists and is functional by running
#   repo-lint --help. Prints the path to the repo-lint executable.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   repo-lint is functional
#     13  repo-lint command not found
#     14  repo-lint found but --help failed
#
#   Stdout:
#     Path to repo-lint executable
#     Confirmation message
#
# EXAMPLES:
#   verify_repo_lint
verify_repo_lint() {
	local repo_lint_path

	if ! repo_lint_path="$(command -v repo-lint)"; then
		die "repo-lint command not found on PATH" 13
	fi

	log "Found repo-lint: $repo_lint_path"

	if ! repo-lint --help >/dev/null 2>&1; then
		die "repo-lint found but --help command failed" 14
	fi

	log "repo-lint is functional"
}

# ============================================================================
# Python Toolchain Installation (Phase 2)
# ============================================================================

# install_python_tools - Install Python linting and testing tools
#
# DESCRIPTION:
#   Installs required Python development tools (black, ruff, pylint, yamllint,
#   pytest) into the active virtual environment. Installs tools directly to
#   ensure they're available in the main .venv environment.
#
# INPUTS:
#   None (uses active venv)
#
# OUTPUTS:
#   Exit Code:
#     0   All Python tools installed successfully
#     15  One or more Python tools failed to install
#
#   Stdout:
#     Installation progress and version information for each tool
#
#   Side Effects:
#     Installs packages in active virtual environment
#
# EXAMPLES:
#   install_python_tools
install_python_tools() {
	log "Installing Python toolchain (black, ruff, pylint, yamllint, pytest)"

	# Install tools directly into the main venv
	log "Installing Python tools via pip"

	# Install tools
	local tools=("black" "ruff" "pylint" "yamllint" "pytest")
	local failed_tools=()

	for tool in "${tools[@]}"; do
		log "Installing $tool..."
		if python3 -m pip install "$tool" --quiet; then
			# Verify installation
			if command -v "$tool" >/dev/null 2>&1; then
				local version
				case "$tool" in
				black | ruff | pylint | yamllint)
					version=$($tool --version 2>&1 | head -n1)
					;;
				pytest)
					version=$(pytest --version 2>&1 | head -n1)
					;;
				esac
				log "  ✓ $tool installed: $version"
			else
				warn "  ✗ $tool installed but not found on PATH"
				failed_tools+=("$tool")
			fi
		else
			warn "  ✗ Failed to install $tool"
			failed_tools+=("$tool")
		fi
	done

	# Check if any tools failed
	if [ ${#failed_tools[@]} -gt 0 ]; then
		die "Failed to install Python tools: ${failed_tools[*]}" 15
	fi

	log "Python toolchain installed successfully"
}

# ============================================================================
# Main Execution
# ============================================================================

# main - Main bootstrap execution flow
#
# DESCRIPTION:
#   Executes the bootstrap sequence: find repo root, create/activate venv,
#   install repo-lint, and verify installation. Prints success summary.
#
# INPUTS:
#   None (command-line arguments will be added in future phases)
#
# OUTPUTS:
#   Exit Code:
#     0   Bootstrap completed successfully
#     Non-zero: Error occurred (see exit codes above)
#
#   Stdout:
#     Progress messages and success summary
#
# EXAMPLES:
#   main
main() {
	log "Starting repo-lint toolchain bootstrap"
	log ""

	# Phase 1.1: Find repository root
	local repo_root
	repo_root=$(find_repo_root)
	log "Repository root: $repo_root"
	log ""

	# Change to repository root
	cd "$repo_root"

	# Phase 1.2: Ensure virtual environment exists
	ensure_venv "$repo_root"
	log ""

	# Phase 1.2 (continued): Activate virtual environment
	activate_venv "$repo_root"
	log ""

	# Phase 1.3: Install repo-lint package
	install_repo_lint "$repo_root"
	log ""

	# Phase 1.4: Verify repo-lint installation
	verify_repo_lint
	log ""

	# Phase 2.2: Install Python toolchain
	install_python_tools
	log ""

	# Success summary
	log "SUCCESS: Bootstrap complete!"
	log ""
	log "Summary:"
	log "  - Repository root: $repo_root"
	log "  - Virtual environment: $repo_root/$VENV_DIR"
	log "  - repo-lint: $(command -v repo-lint)"
	log "  - Python tools: black, ruff, pylint, yamllint, pytest"
	log ""
	log "Next steps:"
	log "  - Virtual environment is activated for this shell session"
	log "  - Run 'repo-lint --help' to see available commands"
	log "  - Phase 3 (verification gate) will be implemented in future commits"
}

# Entry point
main "$@"
