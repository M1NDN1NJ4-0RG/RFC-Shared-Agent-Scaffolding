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
#   - Shell toolchain installation (shellcheck, shfmt) - INSTALLED BY DEFAULT
#   - PowerShell toolchain installation (pwsh, PSScriptAnalyzer) - INSTALLED BY DEFAULT
#   - Perl toolchain installation (Perl::Critic, PPI) - INSTALLED BY DEFAULT
#   - Final verification gate (repo-lint check --ci)
#
# USAGE:
#   ./scripts/bootstrap-repo-lint-toolchain.sh [OPTIONS]
#   bash scripts/bootstrap-repo-lint-toolchain.sh [OPTIONS]
#
# INPUTS:
#   Arguments:
#     --verbose, -v    Enable verbose output (DEFAULT, REQUIRED during implementation)
#     --quiet, -q      Enable quiet mode (DISABLED - reserved for future use)
#     --shell          Install shell toolchain (shellcheck, shfmt) - DEFAULT: enabled
#     --powershell     Install PowerShell toolchain (pwsh, PSScriptAnalyzer) - DEFAULT: enabled
#     --perl           Install Perl toolchain (Perl::Critic, PPI) - DEFAULT: enabled
#     --all            Install all toolchains (DEFAULT BEHAVIOR - this flag is redundant)
#     --help, -h       Show this help message
#
#   Environment Variables:
#     None (uses auto-detected repo root)
#
#   Note: All toolchains are installed by default. Individual flags are kept
#         for backwards compatibility and explicit specification but have no
#         effect since --all is the default behavior.
# OUTPUTS:
#   Exit Codes:
#     0   Success - all operations completed
#     1   Generic failure
#     10  Repository root could not be located
#     11  Virtual environment creation or activation failed
#     12  No valid install target found (missing pyproject.toml at repo root)
#     13  repo-lint not found on PATH after installation
#     14  repo-lint exists but --help command failed
#     15  Python toolchain installation failed
#     16  Shell toolchain installation failed (shellcheck/shfmt)
#     17  PowerShell toolchain installation failed (pwsh/PSScriptAnalyzer)
#     18  Perl toolchain installation failed (Perl::Critic/PPI)
#     19  Verification gate failed (repo-lint check --ci)
#     20  actionlint installation failed
#     21  ripgrep installation failed (required tool)
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

# Trap to ensure progress cleanup on exit
trap progress_cleanup EXIT INT TERM

# Constants
readonly VENV_DIR=".venv"

# Global flags (set by parse_arguments)
VERBOSE_MODE=true       # Default to verbose during implementation
QUIET_MODE=false        # Reserved for future use
INSTALL_SHELL=true      # Default to true - all toolchains installed by default
INSTALL_POWERSHELL=true # Default to true - all toolchains installed by default
INSTALL_PERL=true       # Default to true - all toolchains installed by default

# Progress UI globals
PROGRESS_ENABLED=false
PROGRESS_TTY=false
PROGRESS_TOTAL_STEPS=0
PROGRESS_CURRENT_STEP=0
PROGRESS_CURRENT_STEP_NAME=""
PROGRESS_STEP_START_TIME=0

# ============================================================================
# Progress UI Functions
# ============================================================================

# is_tty - Check if stdout is a TTY
#
# DESCRIPTION:
#   Determines if the script is running in an interactive terminal.
#
# OUTPUTS:
#   Exit Code:
#     0   stdout is a TTY
#     1   stdout is not a TTY
is_tty() {
	[[ -t 1 ]]
}

# progress_init - Initialize progress tracking
#
# DESCRIPTION:
#   Sets up progress tracking system. Automatically detects TTY mode and
#   respects CI/NO_COLOR environment variables.
#
# INPUTS:
#   $1 - Total number of steps
#
# OUTPUTS:
#   Sets global progress variables
progress_init() {
	local total_steps="$1"
	PROGRESS_TOTAL_STEPS="$total_steps"
	PROGRESS_CURRENT_STEP=0

	# Detect if we should enable progress UI
	if is_tty && [[ -z "${CI:-}" ]] && [[ -z "${NO_COLOR:-}" ]]; then
		PROGRESS_ENABLED=true
		PROGRESS_TTY=true
		# Hide cursor
		printf '\033[?25l'
	elif [[ -n "${CI:-}" ]] || ! is_tty; then
		PROGRESS_ENABLED=true
		PROGRESS_TTY=false
	fi
}

# progress_cleanup - Cleanup progress UI state
#
# DESCRIPTION:
#   Restores terminal state. Must be called on exit.
#
# OUTPUTS:
#   Restores cursor visibility if in TTY mode
progress_cleanup() {
	if [[ "$PROGRESS_TTY" = true ]]; then
		# Clear current line and show cursor
		printf '\r\033[K\033[?25h'
	fi
}

# step_start - Mark start of a step
#
# DESCRIPTION:
#   Records the start of a step and displays progress.
#
# INPUTS:
#   $1 - Step name
#
# OUTPUTS:
#   Progress indicator (TTY or CI format)
step_start() {
	local step_name="$1"
	PROGRESS_CURRENT_STEP=$((PROGRESS_CURRENT_STEP + 1))
	PROGRESS_CURRENT_STEP_NAME="$step_name"
	PROGRESS_STEP_START_TIME="$SECONDS"

	if [[ "$PROGRESS_ENABLED" = false ]]; then
		return
	fi

	if [[ "$PROGRESS_TTY" = true ]]; then
		# TTY mode: in-place updating progress
		printf '\r\033[K[%d/%d] %s...' \
			"$PROGRESS_CURRENT_STEP" \
			"$PROGRESS_TOTAL_STEPS" \
			"$step_name"
	else
		# CI mode: clean line-oriented output
		echo "[bootstrap] [$PROGRESS_CURRENT_STEP/$PROGRESS_TOTAL_STEPS] $step_name..."
	fi
}

# step_ok - Mark step as successful
#
# DESCRIPTION:
#   Records successful completion of current step.
#
# OUTPUTS:
#   Success indicator with duration
step_ok() {
	if [[ "$PROGRESS_ENABLED" = false ]]; then
		return
	fi

	local duration=$((SECONDS - PROGRESS_STEP_START_TIME))

	if [[ "$PROGRESS_TTY" = true ]]; then
		# TTY mode: update in place with checkmark
		printf '\r\033[K✓ [%d/%d] %s (%ds)\n' \
			"$PROGRESS_CURRENT_STEP" \
			"$PROGRESS_TOTAL_STEPS" \
			"$PROGRESS_CURRENT_STEP_NAME" \
			"$duration"
	else
		# CI mode: clean success line
		echo "[bootstrap] ✓ [$PROGRESS_CURRENT_STEP/$PROGRESS_TOTAL_STEPS] $PROGRESS_CURRENT_STEP_NAME (${duration}s)"
	fi
}

# step_fail - Mark step as failed
#
# DESCRIPTION:
#   Records failure of current step.
#
# INPUTS:
#   $1 - Error message (optional)
#
# OUTPUTS:
#   Failure indicator with duration and error
step_fail() {
	local error_msg="${1:-failed}"

	if [[ "$PROGRESS_ENABLED" = false ]]; then
		return
	fi

	local duration=$((SECONDS - PROGRESS_STEP_START_TIME))

	if [[ "$PROGRESS_TTY" = true ]]; then
		# TTY mode: update in place with X
		printf '\r\033[K✗ [%d/%d] %s (%ds) - %s\n' \
			"$PROGRESS_CURRENT_STEP" \
			"$PROGRESS_TOTAL_STEPS" \
			"$PROGRESS_CURRENT_STEP_NAME" \
			"$duration" \
			"$error_msg"
	else
		# CI mode: clean failure line
		echo "[bootstrap] ✗ [$PROGRESS_CURRENT_STEP/$PROGRESS_TOTAL_STEPS] $PROGRESS_CURRENT_STEP_NAME (${duration}s) - $error_msg"
	fi
}

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

# has_sudo - Check if sudo access is available
#
# DESCRIPTION:
#   Checks if the current user is root or has passwordless sudo access.
#   Used before attempting system package installations.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   User is root or has passwordless sudo access
#     1   No sudo access available
#
# EXAMPLES:
#   if has_sudo; then
#       sudo apt-get install package
#   fi
has_sudo() {
	[ "$(id -u)" -eq 0 ] || sudo -n true 2>/dev/null
}

# run_or_die - Execute command and exit via die() on failure
#
# DESCRIPTION:
#   Runs a command and if it fails, exits the script via die() with
#   a specified exit code and error message. This enforces deterministic
#   exit codes for all critical external commands.
#
# INPUTS:
#   $1 - Exit code to use on failure
#   $2 - Error message for die()
#   $@ (3+) - Command and arguments to execute
#
# OUTPUTS:
#   Exit Code:
#     0   Command succeeded
#     <specified>  Command failed, exits via die()
#
# EXAMPLES:
#   run_or_die 17 "PowerShell installation failed" sudo apt-get install -y powershell
#   run_or_die 13 "pip upgrade failed" python3 -m pip install --upgrade pip
run_or_die() {
	local exit_code="$1"
	local error_msg="$2"
	shift 2

	if ! "$@"; then
		die "$error_msg (command: $*)" "$exit_code"
	fi
}

# try_run - Execute command and return its exit code without dying
#
# DESCRIPTION:
#   Runs a command and returns its exit code without terminating the script.
#   Used for truly optional operations where failure is acceptable.
#   Suppresses pipefail/-e behavior for this command only.
#
# INPUTS:
#   $@ - Command and arguments to execute
#
# OUTPUTS:
#   Exit Code:
#     Returns the exit code of the command (0 on success, non-zero on failure)
#
# EXAMPLES:
#   if try_run brew install actionlint; then
#       log "Homebrew install succeeded"
#   else
#       log "Homebrew install failed, trying alternative"
#   fi
try_run() {
	"$@" || return $?
}

# safe_version - Extract version string without terminating on failure
#
# DESCRIPTION:
#   Safely attempts to extract a version string from a command's output.
#   Uses pipefail-safe patterns to prevent version parsing failures from
#   terminating the bootstrap process. Returns empty string on failure.
#
#   SECURITY: This function executes the command passed as $1. Only use with
#   trusted tool version commands (e.g., "shellcheck --version"). Do NOT pass
#   untrusted input or user-controlled command strings.
#
# INPUTS:
#   $1 - Command to run (e.g., "shellcheck --version") - MUST BE TRUSTED
#   $2 - Optional grep pattern (e.g., "^version:")
#   $3 - Optional awk field number (default: 2)
#
# OUTPUTS:
#   Stdout: Version string or empty string
#   Exit Code: Always 0 (never fails)
#
# EXAMPLES:
#   version=$(safe_version "shellcheck --version" "^version:" 2)
#   version=$(safe_version "actionlint -version")
safe_version() {
	local cmd="$1"
	local pattern="${2:-}"
	local field="${3:-2}"

	# Execute command in subshell with error suppression
	# WARNING: $cmd is executed directly - only call with trusted tool commands
	local output
	output=$($cmd 2>/dev/null || true)

	if [[ -n "$pattern" ]]; then
		echo "$output" | awk -v pat="$pattern" -v fld="$field" \
			'$0 ~ pat {print $fld; found=1} END {exit 0}' || true
	else
		echo "$output" || true
	fi
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
		By default, ALL toolchains are installed (equivalent to --all flag).

		OPTIONS:
		  --verbose, -v      Enable verbose output (DEFAULT - required during implementation)
		  --quiet, -q        Enable quiet mode (DISABLED - reserved for future use)
		  --shell            Install shell toolchain (shellcheck, shfmt) - DEFAULT: enabled
		  --powershell       Install PowerShell toolchain (pwsh, PSScriptAnalyzer) - DEFAULT: enabled
		  --perl             Install Perl toolchain (Perl::Critic, PPI) - DEFAULT: enabled
		  --all              Install all toolchains (DEFAULT BEHAVIOR - redundant)
		  --help, -h         Show this help message

		DEFAULT TOOLCHAINS (always installed):
		  - Python toolchain (black, ruff, pylint, yamllint, pytest)
		  - Shell toolchain (shellcheck, shfmt)
		  - PowerShell toolchain (pwsh, PSScriptAnalyzer)
		  - Perl toolchain (Perl::Critic, PPI)
		  - actionlint (GitHub Actions workflow linter)
		  - ripgrep (or grep fallback)

		EXAMPLES:
		  # Install all toolchains (default behavior)
		  ./scripts/bootstrap-repo-lint-toolchain.sh

		  # Explicit --all flag (same as default)
		  ./scripts/bootstrap-repo-lint-toolchain.sh --all

		  # Any individual flag still works (but all are installed anyway)
		  ./scripts/bootstrap-repo-lint-toolchain.sh --shell

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
		die "Virtual environment activation failed (python3 does not point to venv). Expected: $venv_path/bin/python3, Got: $active_python" 11
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
	# NOTE: Uses exit code 13 (repo-lint installation failure) for pip upgrade failures
	# because pip upgrade is part of the repo-lint installation process. The error message
	# clearly indicates what failed, so a separate exit code is not necessary.
	run_or_die 13 "Failed to upgrade pip/setuptools/wheel" python3 -m pip install --upgrade pip setuptools wheel

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
				black)
					version=$(safe_version "black --version")
					;;
				ruff)
					version=$(safe_version "ruff --version")
					;;
				pylint)
					version=$(safe_version "pylint --version")
					;;
				yamllint)
					version=$(safe_version "yamllint --version")
					;;
				pytest)
					version=$(safe_version "pytest --version")
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

# install_rgrep - Install ripgrep (REQUIRED)
#
# DESCRIPTION:
#   Attempts to install ripgrep (rg) using available package managers
#   (Homebrew on macOS, apt-get on Debian/Ubuntu). Ripgrep is REQUIRED
#   for this repository's tooling. If installation fails, the script
#   exits with error code 21.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   ripgrep available
#     21  ripgrep installation failed (fatal)
#
#   Stdout:
#     Installation progress and clear error messages
#
#   Side Effects:
#     May install ripgrep system package if sudo is available
#
# EXAMPLES:
#   install_rgrep
install_rgrep() {
	log "Checking for ripgrep (rgrep) - REQUIRED..."

	# Check if ripgrep (rg) is already installed
	if command -v rg >/dev/null 2>&1; then
		local version
		version=$(safe_version "rg --version")
		log "  ✓ ripgrep is already installed: $version"
		return 0
	fi

	# Attempt to install ripgrep
	log "ripgrep not found. Attempting to install (REQUIRED)..."

	# Detect package manager and install
	if command -v apt-get >/dev/null 2>&1; then
		log "Detected apt-get package manager"
		if has_sudo; then
			log "Installing ripgrep via apt-get..."
			run_or_die 21 "Failed to update apt repositories for ripgrep" sudo apt-get update -qq
			run_or_die 21 "Failed to install ripgrep via apt-get" sudo apt-get install -y ripgrep
			log "  ✓ ripgrep installed successfully"
			return 0
		else
			die "Cannot install ripgrep: sudo access required. Manual install: sudo apt-get install ripgrep" 21
		fi
	elif command -v brew >/dev/null 2>&1; then
		log "Detected Homebrew package manager"
		log "Installing ripgrep via brew..."
		run_or_die 21 "Failed to install ripgrep via Homebrew" brew install ripgrep
		log "  ✓ ripgrep installed successfully"
		return 0
	else
		die "No supported package manager found for ripgrep (tried apt-get/brew). Manual install required: https://github.com/BurntSushi/ripgrep/releases" 21
	fi
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
		version=$(safe_version "shellcheck --version" "^version:" 2)
		log "  ✓ shellcheck already installed: version $version"
	else
		# Attempt to install shellcheck
		if command -v apt-get >/dev/null 2>&1; then
			if has_sudo; then
				log "Installing shellcheck via apt-get..."
				if sudo apt-get update -qq && sudo apt-get install -y shellcheck; then
					local version
					version=$(safe_version "shellcheck --version" "^version:" 2)
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
				version=$(safe_version "shellcheck --version" "^version:" 2)
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
			if has_sudo; then
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
		pwsh_version=$(safe_version "pwsh --version")
		log "  ✓ pwsh already installed: $pwsh_version"
	else
		log "Installing pwsh..."
		if command -v apt-get >/dev/null 2>&1; then
			if command -v sudo >/dev/null 2>&1; then
				# Install PowerShell via Microsoft package repository
				# Set up trap to clean up downloaded deb file on exit/failure
				local deb_file="packages-microsoft-prod.deb"
				trap 'rm -f "$deb_file"' EXIT

				run_or_die 17 "Failed to update apt repositories for PowerShell prerequisites" sudo apt-get update
				run_or_die 17 "Failed to install PowerShell prerequisites (wget, apt-transport-https, software-properties-common)" sudo apt-get install -y wget apt-transport-https software-properties-common

				local ms_repo_url
				ms_repo_url="https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb"
				log "Downloading Microsoft repository package from: $ms_repo_url"
				run_or_die 17 "Failed to download Microsoft repository package from $ms_repo_url" wget -q "$ms_repo_url" -O "$deb_file"

				run_or_die 17 "Failed to install Microsoft repository package via dpkg" sudo dpkg -i "$deb_file"
				run_or_die 17 "Failed to update apt repositories after adding Microsoft repo" sudo apt-get update
				run_or_die 17 "Failed to install PowerShell package" sudo apt-get install -y powershell

				# Clean up deb file (trap will also handle this)
				rm -f "$deb_file"
				trap - EXIT

				if command -v pwsh >/dev/null 2>&1; then
					local pwsh_version
					pwsh_version=$(safe_version "pwsh --version")
					log "  ✓ pwsh installed: $pwsh_version"
				else
					failed_tools+=("pwsh")
				fi
			else
				warn "  ✗ sudo not available, cannot install pwsh via apt-get"
				failed_tools+=("pwsh")
			fi
		elif command -v brew >/dev/null 2>&1; then
			run_or_die 17 "Failed to install PowerShell via Homebrew" brew install --cask powershell
			if command -v pwsh >/dev/null 2>&1; then
				local pwsh_version
				pwsh_version=$(safe_version "pwsh --version")
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

# setup_perl_environment - Set up Perl local::lib environment variables
#
# DESCRIPTION:
#   Exports environment variables required for Perl modules installed to ~/perl5
#   via cpanm local::lib. This function is called by install_perl_tools during
#   installation and by run_verification_gate before running repo-lint.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   Environment variables exported
#
#   Environment:
#     Exports PERL_LOCAL_LIB_ROOT, PERL_MB_OPT, PERL_MM_OPT, PERL5LIB, PATH
#
# EXAMPLES:
#   setup_perl_environment
setup_perl_environment() {
	export PERL_LOCAL_LIB_ROOT="$HOME/perl5${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}"
	export PERL_MB_OPT="--install_base \"$HOME/perl5\""
	export PERL_MM_OPT="INSTALL_BASE=$HOME/perl5"
	export PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"
	export PATH="$HOME/perl5/bin${PATH:+:${PATH}}"
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

	# Set up local::lib environment for Perl module installation
	# cpanm will install to ~/perl5 when it can't write to system directories. These environment variables ensure modules and executables are discoverable both during installation and when running repo-lint verification.
	setup_perl_environment

	# Install Perl::Critic (non-interactive)
	log "Installing Perl::Critic..."
	if perl -MPerl::Critic -e 1 2>/dev/null; then
		log "  ✓ Perl::Critic already installed"
	else
		# Non-interactive installation with default answers
		# Wrap cpanm to prevent set -e from short-circuiting error collection
		if PERL_MM_USE_DEFAULT=1 cpanm --notest --force Perl::Critic; then
			log "  ✓ Perl::Critic installed"
		else
			warn "  ✗ Failed to install Perl::Critic"
			failed_tools+=("Perl::Critic")
		fi
	fi

	# Install PPI (Perl parsing library)
	log "Installing PPI..."
	if perl -MPPI -e 1 2>/dev/null; then
		log "  ✓ PPI already installed"
	else
		# Wrap cpanm to prevent set -e from short-circuiting error collection
		if PERL_MM_USE_DEFAULT=1 cpanm --notest --force PPI; then
			log "  ✓ PPI installed"
		else
			warn "  ✗ Failed to install PPI"
			failed_tools+=("PPI")
		fi
	fi

	# Verify perlcritic executable is available
	if ! command -v perlcritic >/dev/null 2>&1; then
		warn "  ✗ perlcritic executable not found in PATH"
		failed_tools+=("perlcritic-executable")
	else
		log "  ✓ perlcritic executable found: $(command -v perlcritic)"
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
			perlcritic-executable)
				warn "  - perlcritic not in PATH. Add ~/perl5/bin to PATH:"
				warn "    export PATH=\"\$HOME/perl5/bin:\$PATH\""
				;;
			esac
		done
		die "Perl toolchain installation incomplete" 18
	fi

	log "Perl toolchain installed successfully"
	log "NOTE: Perl tools installed to ~/perl5/bin - ensure this is in your PATH"
}

# install_actionlint - Install actionlint (GitHub Actions workflow linter)
#
# DESCRIPTION:
#   Installs actionlint to lint GitHub Actions workflow YAML files.
#   This tool is required for workflow compliance checks in CI and Copilot sessions.
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Code:
#     0   actionlint installed successfully or already present
#     20  actionlint installation failed
#
#   Stdout:
#     Installation progress and version information
#
#   Side Effects:
#     May install Go via package manager if not present
#     Adds $HOME/go/bin to PATH for current session
#
# EXAMPLES:
#   install_actionlint
install_actionlint() {
	log "Installing actionlint (GitHub Actions workflow linter)"

	# Check if actionlint is already installed
	if command -v actionlint >/dev/null 2>&1; then
		local version
		version=$(safe_version "actionlint -version")
		log "  ✓ actionlint already installed: $version"
		return 0
	fi

	# Determine installation method based on platform
	if command -v brew >/dev/null 2>&1; then
		# macOS: Use Homebrew
		log "Installing actionlint via Homebrew..."
		run_or_die 20 "Failed to install actionlint via Homebrew" brew install actionlint
		local version
		version=$(safe_version "actionlint -version")
		log "  ✓ actionlint installed: $version"
		return 0
	else
		# Linux: Use go install
		log "Installing actionlint via go install..."

		# Check if Go is available
		if ! command -v go >/dev/null 2>&1; then
			log "Go not found, attempting to install..."
			if command -v apt-get >/dev/null 2>&1; then
				if has_sudo; then
					# NOTE: golang-go from apt may install an older Go version on some distributions.
					# actionlint v1.7.10 requires Go 1.18+. If installation fails due to Go version,
					# consider using snap (sudo snap install go --classic) or direct binary download.
					log "Installing golang-go via apt-get..."
					run_or_die 20 "Failed to update apt repositories for Go installation" sudo apt-get update -qq
					run_or_die 20 "Failed to install golang-go via apt-get" sudo apt-get install -y golang-go
					log "  ✓ Go installed successfully"
				else
					warn "  ✗ Cannot install Go: sudo access required"
					die "Go installation required for actionlint (needs sudo)" 20
				fi
			else
				warn "  ✗ No supported package manager found for Go"
				die "Go installation required for actionlint" 20
			fi
		fi

		# Ensure GOPATH/bin is in PATH for this session
		export PATH="$HOME/go/bin:$PATH"

		# Install actionlint using go install (pinned to v1.7.10 for reproducibility)
		log "Running: go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.10"
		run_or_die 20 "Failed to install actionlint via go install" go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.10

		# Verify installation
		if command -v actionlint >/dev/null 2>&1; then
			local version
			version=$(safe_version "actionlint -version")
			log "  ✓ actionlint installed: $version"
			log "  ✓ actionlint binary: $(command -v actionlint)"
			return 0
		else
			warn "  ✗ actionlint installed but not found on PATH"
			warn "  → Expected location: \$HOME/go/bin/actionlint"
			warn "  → PATH was updated for this session: export PATH=\"\$HOME/go/bin:\$PATH\""
			warn "  → Manually verify: actionlint -version"
			die "actionlint not accessible after installation (check PATH)" 20
		fi
	fi
}

# run_verification_gate - Run repo-lint verification gate
#
# DESCRIPTION:
#   Runs repo-lint check --ci to verify that all required tools are properly
#   installed and functional. This is the final compliance gate.
#   Accepts exit code 1 (VIOLATIONS) as success since it means tools work.
#   Only fails on exit code 2 (MISSING_TOOLS) or other errors.
#
# INPUTS:
#   None (assumes repo-lint is on PATH in activated venv)
#   Globals: INSTALL_PERL (to set Perl PATH if needed)
#
# OUTPUTS:
#   Exit Code:
#     0   Verification passed (tools functional)
#     19  Verification gate failed (missing tools)
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

	# Set up Perl environment if Perl toolchain was installed
	if [ "$INSTALL_PERL" = true ]; then
		setup_perl_environment
	fi

	# Ensure we're using the venv repo-lint
	local repo_lint_path
	repo_lint_path=$(command -v repo-lint)

	if [[ ! "$repo_lint_path" =~ \.venv ]]; then
		warn "repo-lint is not from .venv: $repo_lint_path"
		warn "This may indicate PATH activation issues"
	fi

	# First run repo-lint doctor to verify toolchain availability
	log "Running: repo-lint doctor (toolchain self-test)"
	local doctor_exit=0
	repo-lint doctor || doctor_exit=$?

	# Exit code 0: Perfect health
	# Exit code 1: Config/path issues but tools are functional (acceptable for bootstrap)
	# Exit code 2+: Critical toolchain failures
	if [ $doctor_exit -eq 0 ]; then
		log "  ✓ repo-lint doctor passed (toolchain operational)"
	elif [ $doctor_exit -eq 1 ]; then
		log "  ⚠ repo-lint doctor reports config issues (exit 1) but tools are functional"
		log "  This is acceptable for bootstrap verification"
	else
		warn "  ✗ repo-lint doctor failed with exit code $doctor_exit"
		warn "Critical toolchain errors detected"
		die "Verification gate failed: toolchain errors detected by repo-lint doctor" 19
	fi

	# Run full verification gate with repo-lint check --ci
	log "Running: repo-lint check --ci"

	# Capture exit code
	local exit_code=0
	repo-lint check --ci || exit_code=$?

	# Exit code 0: All checks passed
	# Exit code 1: Violations found (tools work, but repo has lint issues - THIS IS OK for verification)
	# Exit code 2: Missing tools (THIS IS FAILURE)
	# Exit code 3+: Other errors (THIS IS FAILURE)

	if [ $exit_code -eq 0 ]; then
		log "  ✓ Verification gate passed (no violations)"
		return 0
	elif [ $exit_code -eq 1 ]; then
		log "  ✓ Verification gate passed (tools functional, violations found)"
		log "  Note: Repository has lint violations but all tools are working"
		return 0
	elif [ $exit_code -eq 2 ]; then
		warn "  ✗ Verification gate failed: Missing tools"
		warn "Some required tools are not installed or not on PATH"
		warn "Review the output above for specific missing tools"
		die "Verification gate failed: missing tools" 19
	else
		warn "  ✗ Verification gate failed with exit code $exit_code"
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
	# Calculate total steps (dynamically based on configuration)
	local total_steps=9 # Base steps: args, repo_root, venv, activate, repo-lint install, repo-lint verify, ripgrep, python, actionlint, verification
	[[ "$INSTALL_SHELL" = true ]] && total_steps=$((total_steps + 1))
	[[ "$INSTALL_POWERSHELL" = true ]] && total_steps=$((total_steps + 1))
	[[ "$INSTALL_PERL" = true ]] && total_steps=$((total_steps + 1))
	total_steps=$((total_steps + 1)) # verification gate

	# Initialize progress tracking
	progress_init "$total_steps"

	# Step 1: Parse command-line arguments
	step_start "Parsing arguments"
	parse_arguments "$@"
	step_ok

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

	# Step 2: Find repository root
	step_start "Finding repository root"
	local repo_root
	repo_root=$(find_repo_root)
	log "Repository root: $repo_root"
	step_ok
	log ""

	# Change to repository root
	cd "$repo_root"

	# Step 3: Ensure virtual environment exists
	show_banner "PHASE 1: CORE SETUP" "Creating Python virtual environment..."
	step_start "Creating virtual environment"
	ensure_venv "$repo_root"
	step_ok
	log ""

	# Step 4: Activate virtual environment
	step_start "Activating virtual environment"
	activate_venv "$repo_root"
	step_ok
	log ""

	# Step 5: Install repo-lint package
	step_start "Installing repo-lint package"
	install_repo_lint "$repo_root"
	step_ok
	log ""

	# Step 6: Verify repo-lint installation
	step_start "Verifying repo-lint installation"
	verify_repo_lint
	step_ok
	log ""

	# Phase 2: Install toolchains
	show_banner "PHASE 2: TOOLCHAIN INSTALLATION" "This may take several minutes. Please wait..."

	# Step 7: Install ripgrep (always installed - required)
	step_start "Installing ripgrep"
	install_rgrep
	step_ok
	log ""

	# Step 8: Install Python toolchain (always installed - required)
	step_start "Installing Python toolchain"
	install_python_tools
	step_ok
	log ""

	# Step 9: Install actionlint (always installed - required)
	step_start "Installing actionlint"
	install_actionlint
	step_ok
	log ""

	# Step 10+: Install shell toolchain (if requested)
	if [ "$INSTALL_SHELL" = true ]; then
		step_start "Installing shell toolchain"
		install_shell_tools
		step_ok
		log ""
	fi

	# Step 11+: Install PowerShell toolchain (if requested)
	if [ "$INSTALL_POWERSHELL" = true ]; then
		step_start "Installing PowerShell toolchain"
		install_powershell_tools
		step_ok
		log ""
	fi

	# Step 12+: Install Perl toolchain (if requested)
	if [ "$INSTALL_PERL" = true ]; then
		step_start "Installing Perl toolchain"
		install_perl_tools
		step_ok
		log ""
	fi

	# Step Final: Run verification gate
	show_banner "PHASE 3: VERIFICATION GATE" "Validating installation..."
	step_start "Running verification gate"
	run_verification_gate
	step_ok
	log ""

	# Success summary
	show_banner "BOOTSTRAP COMPLETE" "All requested components installed successfully"

	log "Summary:"
	log "  - Repository root: $repo_root"
	log "  - Virtual environment: $repo_root/$VENV_DIR"
	log "  - repo-lint: $(command -v repo-lint)"
	log "  - Python tools: black, ruff, pylint, yamllint, pytest"
	if command -v actionlint >/dev/null 2>&1; then
		log "  - actionlint: $(command -v actionlint)"
	else
		log "  - actionlint: NOT INSTALLED"
	fi
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
	if [ "$INSTALL_PERL" = true ]; then
		log "For Perl tools (Perl::Critic, PPI), this script has configured a local::lib-style"
		log "environment for the CURRENT shell, including:"
		log "  PATH, PERL5LIB, PERL_LOCAL_LIB_ROOT, PERL_MB_OPT, PERL_MM_OPT"
		log ""
		log "In a NEW shell, the recommended way to restore the full Perl environment is to re-run:"
		log ""
		log "  scripts/bootstrap-repo-lint-toolchain.sh --install-perl"
		log ""
		log "If you prefer to configure Perl manually, you must at least:"
		log "  - add \$HOME/perl5/bin to PATH, and"
		log "  - set PERL5LIB (and any additional local::lib variables) consistently"
		log ""
	fi
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
