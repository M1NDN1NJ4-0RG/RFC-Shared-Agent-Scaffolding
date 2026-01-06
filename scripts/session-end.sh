#!/usr/bin/env bash
# session-end.sh - Session completion workflow script
#
# DESCRIPTION:
#   Automated session completion workflow that:
#   - Resolves repository root robustly
#   - Runs bootstrap toolchain setup
#   - Activates Python virtual environment
#   - Sets up Perl environment variables
#   - Executes repo-lint in CI mode for final validation
#
# USAGE:
#   ./scripts/session-end.sh
#
# EXIT CODES:
#   0: Success - all checks passed
#   1: Failure - bootstrap missing/failed, venv missing, or repo-lint failed
#
# INPUTS:
#   None (uses repository state)
#
# OUTPUTS:
#   Exit Codes:
#     0: Success - all checks passed
#     1: Failure - bootstrap missing/failed, venv missing, or repo-lint failed
#
#   Stdout/Stderr:
#     Stdout: Status messages during execution
#     Stderr: Error messages if failures occur
#
# EXAMPLES:
#   # Run session-end workflow
#   ./scripts/session-end.sh
#
#   # Run from subdirectory
#   cd rust && ../scripts/session-end.sh

set -euo pipefail

# Resolve repository root using git or fallback to Python
REPO_ROOT="$(
	git rev-parse --show-toplevel 2>/dev/null ||
		python3 - <<'PY'
import os, sys
p=os.getcwd()
while True:
    if os.path.isdir(os.path.join(p, ".git")):
        print(p); sys.exit(0)
    parent=os.path.dirname(p)
    if parent==p:
        print("ERROR: Not in a git repository", file=sys.stderr)
        sys.exit(1)
    p=parent
PY
)"

cd "$REPO_ROOT"

# Verify bootstrap script exists and is executable
if [[ ! -x "./scripts/bootstrap-repo-lint-toolchain.sh" ]]; then
	echo "ERROR: Bootstrap script not found or not executable: ./scripts/bootstrap-repo-lint-toolchain.sh" >&2
	exit 1
fi

# Run bootstrap script (allowed to fail without stopping)
echo "[session-end] Running bootstrap toolchain setup..."
./scripts/bootstrap-repo-lint-toolchain.sh || true

# Verify venv exists, run bootstrap_watch.py if not
if [[ ! -f ".venv/bin/activate" ]]; then
	echo "[session-end] Virtual environment not found at .venv/bin/activate" >&2
	echo "[session-end] Running bootstrap_watch.py to create it..." >&2
	if ! ./scripts/bootstrap_watch.py; then
		echo "ERROR: bootstrap_watch.py failed with exit code $?" >&2
		exit 1
	fi
fi

# Run repo-lint check in subshell with activated environment
echo "[session-end] Running repo-lint check in CI mode..."
(
	# Activate venv
	# shellcheck disable=SC1091
	source .venv/bin/activate

	# Set Perl environment variables
	PERL_HOME="$HOME/perl5"
	export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}"
	export PERL_MB_OPT="--install_base \"${PERL_HOME}\""
	export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}"
	export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}"
	export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}"

	# Execute repo-lint check
	repo-lint check --ci
)

echo "[session-end] Session completion workflow finished successfully."
