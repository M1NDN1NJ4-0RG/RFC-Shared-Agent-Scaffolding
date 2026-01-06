#!/usr/bin/env bash
#
# session-start.sh - Bootstrap Progress Watcher (Bash Implementation)
#
# DESCRIPTION:
#   Runs the bootstrap script and filters output to show a condensed view
#   of progress steps and final results. This reduces noise while preserving
#   visibility into step-by-step progress and any final output or errors.
#
#   Functionally equivalent to bootstrap_watch.py but implemented in Bash
#   for environments where Python may not be available yet.
#
# USAGE:
#   ./scripts/session-start.sh
#
# INPUTS:
#   Arguments:
#     None
#
#   Environment Variables:
#     None
#
# OUTPUTS:
#   Exit Codes:
#     0    Bootstrap script succeeded
#     1    Bootstrap script failed or file not found
#
#   Stdout/Stderr:
#     Filtered bootstrap output showing progress lines and final summary
#
#   Side Effects:
#     Executes bootstrap-repo-lint-toolchain.sh
#
# EXAMPLES:
#   # Run from repository root
#   ./scripts/session-start.sh
#   [bootstrap] [1/13] Parsing arguments...
#   [bootstrap] ✓ [1/13] Parsing arguments (0s)
#   ...
#   [bootstrap] [13/13] Running verification gate...
#   [bootstrap] ✓ [13/13] Running verification gate (43s)
#
# NOTES:
#   - Filters out tar extended header warnings (macOS metadata noise)
#   - Filters out Go module download messages (go: downloading ...)
#   - Shows all progress lines with step indicators ([N/M])
#   - Shows all output from the last progress step onward
#   - Exit code matches the bootstrap script's exit code

set -euo pipefail

# Main function - Run bootstrap script and filter output
#
# Executes the bootstrap script, captures output, and filters it to show
# only progress lines and final results.
#
# Arguments:
#   None
#
# Returns:
#   0 on success (bootstrap script succeeded)
#   1 on failure (bootstrap script failed or not found)
#
# Globals:
#   None
#
# Outputs:
#   Filtered bootstrap output to stdout/stderr
main() {
	local script_path="./scripts/bootstrap-repo-lint-toolchain.sh"
	local temp_output

	# Check if bootstrap script exists
	if [[ ! -f "$script_path" ]]; then
		echo "Error: Could not find $script_path" >&2
		echo "Make sure you're running from the repository root." >&2
		return 1
	fi

	# Create temporary file for output
	temp_output=$(mktemp -t session-start.XXXXXX)
	# shellcheck disable=SC2064
	trap "rm -f '$temp_output'" EXIT

	# Run bootstrap script and capture all output (stdout + stderr)
	local exit_code=0
	if ! "$script_path" &>"$temp_output"; then
		exit_code=$?
	fi

	# Read output into array, filtering noise
	local -a lines=()
	local -a progress_indices=()
	local idx=0

	while IFS= read -r line; do
		# Filter out tar extended header warnings (macOS metadata noise)
		if [[ "$line" =~ ^(/usr/bin/)?tar:\ Ignoring\ unknown\ extended\ header\ keyword\ \'LIBARCHIVE\.xattr\..* ]]; then
			continue
		fi

		# Filter out Go module download noise
		if [[ "$line" =~ ^go:\ downloading\  ]]; then
			continue
		fi

		# Store line
		lines+=("$line")

		# Check if line matches progress pattern: [bootstrap] ... [N/M] ...
		if [[ "$line" =~ ^\[bootstrap\].*\[[0-9]+/[0-9]+\] ]]; then
			progress_indices+=("$idx")
		fi

		idx=$((idx + 1))
	done <"$temp_output"

	# Output filtered results
	if [[ ${#progress_indices[@]} -eq 0 ]]; then
		# No progress lines found, print everything
		printf '%s\n' "${lines[@]}"
	else
		# Print all progress lines except the last one
		local last_idx=$((${#progress_indices[@]} - 1))
		for ((i = 0; i < last_idx; i++)); do
			printf '%s\n' "${lines[${progress_indices[$i]}]}"
		done

		# Print everything from the last progress line onward
		local last_progress_idx=${progress_indices[$last_idx]}
		for ((i = last_progress_idx; i < ${#lines[@]}; i++)); do
			printf '%s\n' "${lines[$i]}"
		done
	fi

	return "$exit_code"
}

# Execute main function
main "$@"
