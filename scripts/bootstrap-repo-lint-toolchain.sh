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
#   ./scripts/bootstrap-repo-lint-toolchain.sh [OPTIONS]
#   bash scripts/bootstrap-repo-lint-toolchain.sh [OPTIONS]
#
# INPUTS:
#   Arguments:
#     --verbose, -v    Enable verbose output (DEFAULT, REQUIRED during implementation)
#     --quiet, -q      Enable quiet mode (DISABLED - reserved for future use)
#     --shell          Install shell toolchain (shellcheck, shfmt)
#     --powershell     Install PowerShell toolchain (pwsh, PSScriptAnalyzer)
#     --perl           Install Perl toolchain (Perl::Critic, PPI)
#     --all            Install all optional toolchains
#     --help, -h       Show this help message
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
#     16  Shell toolchain installation failed (shellcheck/shfmt)
#     17  PowerShell toolchain installation failed (pwsh/PSScriptAnalyzer)
#     18  Perl toolchain installation failed (Perl::Critic/PPI)
#     19  Verification gate failed (repo-lint check --ci)
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
#   # Run from repository root (verbose mode - default)
#   ./scripts/bootstrap-repo-lint-toolchain.sh
#
#   # Install all toolchains
#   ./scripts/bootstrap-repo-lint-toolchain.sh --all
#
#   # Install specific toolchains
#   ./scripts/bootstrap-repo-lint-toolchain.sh --shell --perl
#
#   # Verbose mode (explicit)
#   ./scripts/bootstrap-repo-lint-toolchain.sh --verbose
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
#   - Phase 1 + Phase 2 + Phase 3 implementation (core + all toolchains + verification)
#
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ ⚠️  PRE-COMMIT COMPLIANCE REMINDER FOR COPILOT AGENTS ⚠️              ┃
# ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
# ┃ BEFORE EVERY COMMIT, YOU **MUST** RUN AND PASS ALL OF THE FOLLOWING:  ┃
# ┃                                                                        ┃
# ┃ Shell Scripts (Bash/sh):                                              ┃
# ┃   • shellcheck <file>                                                 ┃
# ┃   • shfmt -d <file>                                                   ┃
# ┃   • python3 scripts/validate_docstrings.py --file <file> --lang bash ┃
# ┃                                                                        ┃
# ┃ Python Scripts (.py):                                                 ┃
# ┃   • black --check <file>                                              ┃
# ┃   • ruff check <file>                                                 ┃
# ┃   • pylint <file>                                                     ┃
# ┃   • python3 scripts/validate_docstrings.py --file <file> --lang py   ┃
# ┃                                                                        ┃
# ┃ FIX ALL VIOLATIONS BEFORE COMMITTING - NO EXCEPTIONS!                 ┃
# ┃                                                                        ┃
# ┃ This includes fixing violations in files you created earlier in the   ┃
# ┃ PR, even if the current changes don't directly touch those files.     ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
#
# PLATFORM COMPATIBILITY:
#   - Linux (tested on Ubuntu/Debian)
#   - macOS (should work, not extensively tested)
#   - Requires: bash, python3, python3-venv

set -euo pipefail

# Constants
readonly VENV_DIR=".venv"

# Global flags (set by parse_arguments)
VERBOSE_MODE=true # Default to verbose during implementation
QUIET_MODE=false  # Reserved for future use
INSTALL_SHELL=false
INSTALL_POWERSHELL=false
INSTALL_PERL=false

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

# show_banner - Display a prominent banner message
#
# DESCRIPTION:
#   Prints a visually prominent banner with a message to help users
#   identify important information during bootstrap process.
#
# INPUTS:
#   $1 - Banner title/message
#   $2 - Optional subtitle (default: none)
#
# OUTPUTS:
#   Stdout: Formatted banner with borders
#
# EXAMPLES:
#   show_banner "INSTALLATION IN PROGRESS" "This may take several minutes"
show_banner() {
	local title="$1"
	local subtitle="${2:-}"

	echo ""
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	echo "  $title"
	if [[ -n "$subtitle" ]]; then
		echo "  $subtitle"
	fi
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	echo ""
}

# show_usage - Display help message
#
# DESCRIPTION:
#   Prints usage information and available command-line options.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Stdout: Help message
#
# EXAMPLES:
#   show_usage
show_usage() {
	cat <<-'EOF'
		Usage: bootstrap-repo-lint-toolchain.sh [OPTIONS]

		Bootstrap the repo-lint toolchain and development environment.

		OPTIONS:
		  --verbose, -v      Enable verbose output (DEFAULT - required during implementation)
		  --quiet, -q        Enable quiet mode (DISABLED - reserved for future use)
		  --shell            Install shell toolchain (shellcheck, shfmt)
		  --powershell       Install PowerShell toolchain (pwsh, PSScriptAnalyzer)
		  --perl             Install Perl toolchain (Perl::Critic, PPI)
		  --all              Install all optional toolchains
		  --help, -h         Show this help message

		DEFAULT TOOLCHAINS (always installed):
		  - Python toolchain (black, ruff, pylint, yamllint, pytest)
		  - rgrep (or grep fallback)

		EXAMPLES:
		  # Basic install (Python + rgrep only)
		  ./scripts/bootstrap-repo-lint-toolchain.sh

		  # Install all toolchains
		  ./scripts/bootstrap-repo-lint-toolchain.sh --all

		  # Install specific optional toolchains
		  ./scripts/bootstrap-repo-lint-toolchain.sh --shell --perl

		NOTE: Verbose mode is currently the ONLY supported output mode during
		      implementation for troubleshooting purposes. The --quiet flag is
		      reserved for future use and will display a warning if used.

	EOF
}

# parse_arguments - Parse command-line arguments
#
# DESCRIPTION:
#   Parses command-line arguments and sets global flags accordingly.
#   Handles --verbose, --quiet, --shell, --powershell, --perl, --all, --help.
#
# INPUTS:
#   $@ - All command-line arguments
#
# OUTPUTS:
#   Exit Code:
#     0   Arguments parsed successfully
#     0   Help displayed (exits after showing help)
#
#   Side Effects:
#     Sets global variables: VERBOSE_MODE, QUIET_MODE, INSTALL_SHELL,
#     INSTALL_POWERSHELL, INSTALL_PERL
#
# EXAMPLES:
#   parse_arguments "$@"
parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-h | --help)
			show_usage
			exit 0
			;;
		-v | --verbose)
			VERBOSE_MODE=true
			shift
			;;
		-q | --quiet)
			warn "The --quiet flag is reserved for future use and currently disabled."
			warn "During implementation, verbose output is REQUIRED for troubleshooting."
			warn "Continuing in verbose mode..."
			# shellcheck disable=SC2034  # QUIET_MODE reserved for future use
			QUIET_MODE=false
			VERBOSE_MODE=true
			shift
			;;
		--shell)
			INSTALL_SHELL=true
			shift
			;;
		--powershell)
			INSTALL_POWERSHELL=true
			shift
			;;
		--perl)
			INSTALL_PERL=true
			shift
			;;
		--all)
			INSTALL_SHELL=true
			INSTALL_POWERSHELL=true
			INSTALL_PERL=true
			shift
			;;
		*)
			die "Unknown option: $1. Use --help for usage information." 1
			;;
		esac
	done
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
	python3 -m pip install --upgrade pip setuptools wheel

	local install_target
	install_target=$(determine_install_target "$repo_root")

	log "Installing repo-lint from: $install_target"

	if ! python3 -m pip install -e "$install_target"; then
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
		if python3 -m pip install "$tool"; then
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
# Core Utilities Installation (Phase 2.1)
# ============================================================================

# install_rgrep - Install or verify ripgrep (rgrep) utility
#
# DESCRIPTION:
#   Attempts to install ripgrep (provides rgrep command) using available
#   package managers (apt-get on Debian/Ubuntu). If ripgrep is not available,
#   warns the user and falls back to grep. This is a required utility.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   rgrep available or fallback to grep configured
#
#   Stdout:
#     Installation progress and warnings about grep fallback if needed
#
#   Side Effects:
#     May install ripgrep system package if sudo is available
#
# EXAMPLES:
#   install_rgrep
install_rgrep() {
	log "Checking for ripgrep (rgrep)..."

	# Check if ripgrep (rg) is already installed
	if command -v rg >/dev/null 2>&1; then
		local version
		version=$(rg --version | head -n1)
		log "  ✓ ripgrep is already installed: $version"
		return 0
	fi

	# Attempt to install ripgrep
	log "ripgrep not found. Attempting to install..."

	# Detect package manager and install
	if command -v apt-get >/dev/null 2>&1; then
		log "Detected apt-get package manager"
		if [ "$(id -u)" -eq 0 ] || sudo -n true 2>/dev/null; then
			log "Installing ripgrep via apt-get..."
			if sudo apt-get update -qq && sudo apt-get install -y ripgrep; then
				log "  ✓ ripgrep installed successfully"
				return 0
			else
				warn "  ✗ Failed to install ripgrep via apt-get"
			fi
		else
			warn "  ✗ Cannot install ripgrep: sudo access required"
		fi
	elif command -v brew >/dev/null 2>&1; then
		log "Detected Homebrew package manager"
		log "Installing ripgrep via brew..."
		if brew install ripgrep; then
			log "  ✓ ripgrep installed successfully"
			return 0
		else
			warn "  ✗ Failed to install ripgrep via brew"
		fi
	else
		warn "  ✗ No supported package manager found (apt-get/brew)"
	fi

	# Fallback warning
	warn "ripgrep (rg/rgrep) could not be installed"
	warn "repo-lint will fall back to 'grep' but performance may be degraded"
	warn "To install manually:"
	warn "  - Debian/Ubuntu: sudo apt-get install ripgrep"
	warn "  - macOS: brew install ripgrep"
	warn "  - Or download from: https://github.com/BurntSushi/ripgrep/releases"

	return 0
}

# ============================================================================
# Shell Toolchain Installation (Phase 2.3)
# ============================================================================

# install_shell_tools - Install shell linting and formatting tools
#
# DESCRIPTION:
#   Installs shellcheck (shell script linter) and shfmt (shell script formatter)
#   using available package managers. These tools are required for bash/shell
#   script compliance checks.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   All shell tools installed successfully
#     16  One or more shell tools failed to install
#
#   Stdout:
#     Installation progress and version information for each tool
#
#   Side Effects:
#     May install system packages if sudo is available
#
# EXAMPLES:
#   install_shell_tools
install_shell_tools() {
	log "Installing shell toolchain (shellcheck, shfmt)"

	local failed_tools=()

	# Install shellcheck
	log "Installing shellcheck..."
	if command -v shellcheck >/dev/null 2>&1; then
		local version
		version=$(shellcheck --version | grep "^version:" | awk '{print $2}')
		log "  ✓ shellcheck already installed: version $version"
	else
		# Attempt to install shellcheck
		if command -v apt-get >/dev/null 2>&1; then
			if [ "$(id -u)" -eq 0 ] || sudo -n true 2>/dev/null; then
				log "Installing shellcheck via apt-get..."
				if sudo apt-get update -qq && sudo apt-get install -y shellcheck; then
					local version
					version=$(shellcheck --version | grep "^version:" | awk '{print $2}')
					log "  ✓ shellcheck installed: version $version"
				else
					warn "  ✗ Failed to install shellcheck via apt-get"
					failed_tools+=("shellcheck")
				fi
			else
				warn "  ✗ Cannot install shellcheck: sudo access required"
				failed_tools+=("shellcheck")
			fi
		elif command -v brew >/dev/null 2>&1; then
			log "Installing shellcheck via brew..."
			if brew install shellcheck; then
				local version
				version=$(shellcheck --version | grep "^version:" | awk '{print $2}')
				log "  ✓ shellcheck installed: version $version"
			else
				warn "  ✗ Failed to install shellcheck via brew"
				failed_tools+=("shellcheck")
			fi
		else
			warn "  ✗ No supported package manager found for shellcheck"
			failed_tools+=("shellcheck")
		fi
	fi

	# Install shfmt
	log "Installing shfmt..."
	if command -v shfmt >/dev/null 2>&1; then
		local version
		version=$(shfmt --version 2>&1)
		log "  ✓ shfmt already installed: version $version"
	else
		# Attempt to install shfmt
		if command -v apt-get >/dev/null 2>&1; then
			if [ "$(id -u)" -eq 0 ] || sudo -n true 2>/dev/null; then
				log "Installing shfmt via apt-get..."
				if sudo apt-get update -qq && sudo apt-get install -y shfmt; then
					local version
					version=$(shfmt --version 2>&1)
					log "  ✓ shfmt installed: version $version"
				else
					warn "  ✗ Failed to install shfmt via apt-get"
					warn "  → shfmt may not be in default apt repos, trying alternative method..."
					# Try installing via snap as fallback
					if command -v snap >/dev/null 2>&1; then
						log "Attempting to install shfmt via snap..."
						if sudo snap install shfmt; then
							local version
							version=$(shfmt --version 2>&1)
							log "  ✓ shfmt installed via snap: version $version"
						else
							warn "  ✗ Failed to install shfmt via snap"
							failed_tools+=("shfmt")
						fi
					else
						failed_tools+=("shfmt")
					fi
				fi
			else
				warn "  ✗ Cannot install shfmt: sudo access required"
				failed_tools+=("shfmt")
			fi
		elif command -v brew >/dev/null 2>&1; then
			log "Installing shfmt via brew..."
			if brew install shfmt; then
				local version
				version=$(shfmt --version 2>&1)
				log "  ✓ shfmt installed: version $version"
			else
				warn "  ✗ Failed to install shfmt via brew"
				failed_tools+=("shfmt")
			fi
		else
			warn "  ✗ No supported package manager found for shfmt"
			failed_tools+=("shfmt")
		fi
	fi

	# Check if any tools failed
	if [ ${#failed_tools[@]} -gt 0 ]; then
		warn "Failed to install shell tools: ${failed_tools[*]}"
		warn "Manual installation required:"
		for tool in "${failed_tools[@]}"; do
			case "$tool" in
			shellcheck)
				warn "  - shellcheck: https://github.com/koalaman/shellcheck#installing"
				;;
			shfmt)
				warn "  - shfmt: https://github.com/mvdan/sh#shfmt or 'go install mvdan.cc/sh/v3/cmd/shfmt@latest'"
				;;
			esac
		done
		die "Shell toolchain installation incomplete" 16
	fi

	log "Shell toolchain installed successfully"
}

# install_powershell_tools - Install PowerShell development toolchain
#
# DESCRIPTION:
#   Installs PowerShell (pwsh) and PowerShell linting/analysis tools required
#   for PowerShell script development. Only runs if --powershell flag provided.
#
# INPUTS:
#   None (uses package managers: apt-get, brew, snap)
#
# OUTPUTS:
#   Exit Code:
#     0   Tools installed or verified successfully
#     17  PowerShell toolchain installation failed
#
#   Stdout:
#     Installation progress and verification messages
#
# EXAMPLES:
#   install_powershell_tools
install_powershell_tools() {
	log ""
	log "Installing PowerShell toolchain (pwsh, PSScriptAnalyzer)"
	log "This may take several minutes..."

	local failed_tools=()

	# Install pwsh (PowerShell)
	if command -v pwsh >/dev/null 2>&1; then
		local pwsh_version
		pwsh_version=$(pwsh --version 2>&1 | head -n1)
		log "  ✓ pwsh already installed: $pwsh_version"
	else
		log "Installing pwsh..."
		if command -v apt-get >/dev/null 2>&1; then
			if command -v sudo >/dev/null 2>&1; then
				# Install PowerShell via Microsoft package repository
				sudo apt-get update
				sudo apt-get install -y wget apt-transport-https software-properties-common
				wget -q "https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb"
				sudo dpkg -i packages-microsoft-prod.deb
				rm packages-microsoft-prod.deb
				sudo apt-get update
				sudo apt-get install -y powershell

				if command -v pwsh >/dev/null 2>&1; then
					local pwsh_version
					pwsh_version=$(pwsh --version 2>&1 | head -n1)
					log "  ✓ pwsh installed: $pwsh_version"
				else
					failed_tools+=("pwsh")
				fi
			else
				warn "  ✗ sudo not available, cannot install pwsh via apt-get"
				failed_tools+=("pwsh")
			fi
		elif command -v brew >/dev/null 2>&1; then
			brew install --cask powershell
			if command -v pwsh >/dev/null 2>&1; then
				local pwsh_version
				pwsh_version=$(pwsh --version 2>&1 | head -n1)
				log "  ✓ pwsh installed: $pwsh_version"
			else
				failed_tools+=("pwsh")
			fi
		else
			warn "  ✗ No supported package manager found for pwsh"
			failed_tools+=("pwsh")
		fi
	fi

	# Install PSScriptAnalyzer (PowerShell linter)
	if command -v pwsh >/dev/null 2>&1; then
		log "Installing PSScriptAnalyzer..."
		if pwsh -Command "Get-Module -ListAvailable -Name PSScriptAnalyzer" | grep -q PSScriptAnalyzer; then
			log "  ✓ PSScriptAnalyzer already installed"
		else
			pwsh -Command "Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser"
			if pwsh -Command "Get-Module -ListAvailable -Name PSScriptAnalyzer" | grep -q PSScriptAnalyzer; then
				log "  ✓ PSScriptAnalyzer installed"
			else
				failed_tools+=("PSScriptAnalyzer")
			fi
		fi
	else
		warn "  ✗ pwsh not available, cannot install PSScriptAnalyzer"
		failed_tools+=("PSScriptAnalyzer")
	fi

	# Check if any tools failed
	if [ ${#failed_tools[@]} -gt 0 ]; then
		warn "Failed to install PowerShell tools: ${failed_tools[*]}"
		warn "Manual installation required:"
		for tool in "${failed_tools[@]}"; do
			case "$tool" in
			pwsh)
				warn "  - pwsh: https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell"
				;;
			PSScriptAnalyzer)
				warn "  - PSScriptAnalyzer: Install-Module -Name PSScriptAnalyzer -Force"
				;;
			esac
		done
		die "PowerShell toolchain installation incomplete" 17
	fi

	log "PowerShell toolchain installed successfully"
}

# install_perl_tools - Install Perl development toolchain (non-interactive)
#
# DESCRIPTION:
#   Installs Perl linting/analysis tools (Perl::Critic, PPI) required for
#   Perl script development. Uses non-interactive installation to avoid prompts.
#   Only runs if --perl flag provided.
#
# INPUTS:
#   None (uses cpanm with PERL_MM_USE_DEFAULT=1 for non-interactive install)
#
# OUTPUTS:
#   Exit Code:
#     0   Tools installed or verified successfully
#     18  Perl toolchain installation failed
#
#   Stdout:
#     Installation progress and verification messages
#
# EXAMPLES:
#   install_perl_tools
install_perl_tools() {
	log ""
	log "Installing Perl toolchain (Perl::Critic, PPI)"
	log "This may take several minutes..."
	log "NOTE: Using non-interactive installation (PERL_MM_USE_DEFAULT=1)"

	local failed_tools=()

	# Ensure cpanm (cpanminus) is installed
	if ! command -v cpanm >/dev/null 2>&1; then
		log "Installing cpanminus..."
		if command -v apt-get >/dev/null 2>&1; then
			if command -v sudo >/dev/null 2>&1; then
				sudo apt-get update
				sudo apt-get install -y cpanminus
			else
				warn "  ✗ sudo not available, cannot install cpanminus via apt-get"
				die "Perl toolchain installation incomplete (cpanminus required)" 18
			fi
		elif command -v brew >/dev/null 2>&1; then
			brew install cpanminus
		else
			warn "  ✗ No supported package manager found for cpanminus"
			die "Perl toolchain installation incomplete (cpanminus required)" 18
		fi
	fi

	if command -v cpanm >/dev/null 2>&1; then
		log "  ✓ cpanm available"
	else
		die "cpanminus installation failed" 18
	fi

	# Install Perl::Critic (non-interactive)
	log "Installing Perl::Critic..."
	if perl -MPerlCritic -e 1 2>/dev/null; then
		log "  ✓ Perl::Critic already installed"
	else
		# Non-interactive installation with default answers
		PERL_MM_USE_DEFAULT=1 cpanm --notest --force Perl::Critic
		if perl -MPerl::Critic -e 1 2>/dev/null; then
			log "  ✓ Perl::Critic installed"
		else
			failed_tools+=("Perl::Critic")
		fi
	fi

	# Install PPI (Perl parsing library)
	log "Installing PPI..."
	if perl -MPPI -e 1 2>/dev/null; then
		log "  ✓ PPI already installed"
	else
		PERL_MM_USE_DEFAULT=1 cpanm --notest --force PPI
		if perl -MPPI -e 1 2>/dev/null; then
			log "  ✓ PPI installed"
		else
			failed_tools+=("PPI")
		fi
	fi

	# Check if any tools failed
	if [ ${#failed_tools[@]} -gt 0 ]; then
		warn "Failed to install Perl tools: ${failed_tools[*]}"
		warn "Manual installation required:"
		for tool in "${failed_tools[@]}"; do
			case "$tool" in
			Perl::Critic)
				warn "  - Perl::Critic: cpanm Perl::Critic"
				;;
			PPI)
				warn "  - PPI: cpanm PPI"
				;;
			esac
		done
		die "Perl toolchain installation incomplete" 18
	fi

	log "Perl toolchain installed successfully"
}

# run_verification_gate - Run repo-lint verification gate
#
# DESCRIPTION:
#   Runs repo-lint check --ci to verify that all required tools are properly
#   installed and functional. This is the final compliance gate.
#
# INPUTS:
#   None (assumes repo-lint is on PATH in activated venv)
#
# OUTPUTS:
#   Exit Code:
#     0   Verification passed
#     19  Verification gate failed
#
#   Stdout:
#     Verification progress and results
#
# EXAMPLES:
#   run_verification_gate
run_verification_gate() {
	log ""
	log "Running verification gate (repo-lint check --ci)..."
	log "This validates that all required tools are functional"

	# Ensure we're using the venv repo-lint
	local repo_lint_path
	repo_lint_path=$(command -v repo-lint)

	if [[ ! "$repo_lint_path" =~ \.venv ]]; then
		warn "repo-lint is not from .venv: $repo_lint_path"
		warn "This may indicate PATH activation issues"
	fi

	# Run verification gate with full output
	log "Running: repo-lint check --ci"
	if repo-lint check --ci; then
		log "  ✓ Verification gate passed"
		return 0
	else
		warn "  ✗ Verification gate failed"
		warn "Some tools may be missing or non-functional"
		warn "Review the output above for specific failures"
		die "Verification gate failed" 19
	fi
}

# ============================================================================
# Main Execution
# ============================================================================

# main - Main bootstrap execution flow
#
# DESCRIPTION:
#   Executes the bootstrap sequence: parse arguments, find repo root,
#   create/activate venv, install repo-lint, install toolchains based on flags,
#   and verify installation. Prints success summary with PATH instructions.
#
# INPUTS:
#   $@ - Command-line arguments (parsed by parse_arguments)
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
#   main "$@"
main() {
	# Parse command-line arguments
	parse_arguments "$@"

	show_banner "REPO-LINT TOOLCHAIN BOOTSTRAP" "Setting up development environment..."

	log "Starting repo-lint toolchain bootstrap"
	log ""

	# Display configuration
	log "Configuration:"
	log "  Verbose mode: $VERBOSE_MODE"
	log "  Install shell toolchain: $INSTALL_SHELL"
	log "  Install PowerShell toolchain: $INSTALL_POWERSHELL"
	log "  Install Perl toolchain: $INSTALL_PERL"
	log ""

	# Phase 1.1: Find repository root
	local repo_root
	repo_root=$(find_repo_root)
	log "Repository root: $repo_root"
	log ""

	# Change to repository root
	cd "$repo_root"

	# Phase 1.2: Ensure virtual environment exists
	show_banner "PHASE 1: CORE SETUP" "Creating Python virtual environment..."
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

	# Phase 2: Install toolchains
	show_banner "PHASE 2: TOOLCHAIN INSTALLATION" "This may take several minutes. Please wait..."

	# Phase 2.1: Install rgrep (always installed - required)
	install_rgrep
	log ""

	# Phase 2.2: Install Python toolchain (always installed - required)
	install_python_tools
	log ""

	# Phase 2.3: Install shell toolchain (if requested)
	if [ "$INSTALL_SHELL" = true ]; then
		install_shell_tools
		log ""
	fi

	# Phase 2.4: Install PowerShell toolchain (if requested)
	if [ "$INSTALL_POWERSHELL" = true ]; then
		install_powershell_tools
		log ""
	fi

	# Phase 2.5: Install Perl toolchain (if requested)
	if [ "$INSTALL_PERL" = true ]; then
		install_perl_tools
		log ""
	fi

	# Phase 3: Run verification gate
	show_banner "PHASE 3: VERIFICATION GATE" "Validating installation..."
	run_verification_gate
	log ""

	# Success summary
	show_banner "BOOTSTRAP COMPLETE" "All requested components installed successfully"

	log "Summary:"
	log "  - Repository root: $repo_root"
	log "  - Virtual environment: $repo_root/$VENV_DIR"
	log "  - repo-lint: $(command -v repo-lint)"
	log "  - Python tools: black, ruff, pylint, yamllint, pytest"
	if command -v rg >/dev/null 2>&1; then
		log "  - ripgrep: $(command -v rg)"
	else
		log "  - ripgrep: NOT INSTALLED (fallback to grep)"
	fi
	if [ "$INSTALL_SHELL" = true ]; then
		log "  - Shell tools: shellcheck, shfmt"
	fi
	if [ "$INSTALL_POWERSHELL" = true ]; then
		log "  - PowerShell tools: pwsh, PSScriptAnalyzer"
	fi
	if [ "$INSTALL_PERL" = true ]; then
		log "  - Perl tools: Perl::Critic, PPI"
	fi
	log ""

	# PATH activation banner
	show_banner "IMPORTANT: PATH ACTIVATION REQUIRED"
	log "To use repo-lint and installed tools, you MUST activate the virtual environment:"
	log ""
	log "  source .venv/bin/activate"
	log ""
	log "OR run repo-lint with explicit path:"
	log ""
	log "  .venv/bin/repo-lint --help"
	log ""
	log "The virtual environment is activated for THIS shell session only."
	log "You will need to activate it again in new terminal sessions."
	log ""
}

# Entry point
main "$@"
