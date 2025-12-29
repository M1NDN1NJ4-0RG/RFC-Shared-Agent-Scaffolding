#!/usr/bin/env bash
# DESCRIPTION:
#   Thin wrapper for repo-lint tool - delegates to Python implementation
#   Run all repository linters and formatters locally
#   Supports Python, Bash, PowerShell, Perl, and YAML files
#
# USAGE:
#   ./scripts/run-linters.sh [--fix]
#   ./scripts/run-linters.sh [--install]
#
# INPUTS:
#   --fix       Apply automatic fixes where possible (black formatting, shfmt, safe ruff fixes)
#   --install   Install/bootstrap required linting tools locally
#
# OUTPUTS:
#   Lint results printed to stdout/stderr
#   Exit code 0 if all checks pass, 1 if any fail, 2 if tools missing in CI mode
#
# EXAMPLES:
#   # Check code without modifying
#   ./scripts/run-linters.sh
#
#   # Auto-format and check
#   ./scripts/run-linters.sh --fix
#
#   # Install missing tools
#   ./scripts/run-linters.sh --install

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Parse arguments and map to repo-lint commands
COMMAND="check"
if [[ "${1:-}" == "--fix" ]]; then
  COMMAND="fix"
elif [[ "${1:-}" == "--install" ]]; then
  COMMAND="install"
elif [[ -n "${1:-}" ]]; then
  echo "Error: Unknown argument '${1}'"
  echo ""
  echo "Usage: $0 [--fix|--install]"
  echo "  (no args)   Run linting checks without modifying files"
  echo "  --fix       Apply automatic fixes where possible"
  echo "  --install   Install/bootstrap required linting tools"
  exit 1
fi

# Delegate to repo_lint Python module
exec python -m tools.repo_lint "$COMMAND"
