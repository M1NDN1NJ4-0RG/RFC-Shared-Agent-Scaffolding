#!/usr/bin/env bash
#
# run-tests.sh - Top-level test entry point for Bash bundle
#
# DESCRIPTION:
#   CI-friendly wrapper that orchestrates the Bash test suite. Called by GitHub
#   Actions workflow (test-bash.yml) to run all Bash tests. Ensures scripts are
#   executable and delegates to the actual test runner.
#
# USAGE:
#   ./run-tests.sh
#
# INPUTS:
#   Arguments: None
#
# OUTPUTS:
#   Exit Codes:
#     0  All tests passed
#     Non-zero  Tests failed (delegated from tests/run-all.sh)
#
#   Stdout/Stderr:
#     Delegated to tests/run-all.sh
#
# SIDE EFFECTS:
#   Makes all scripts/*.sh and tests/*.sh executable (chmod +x)
#   Required for CI environments where git doesn't preserve +x bit
#
# PLATFORM COMPATIBILITY:
#   - Linux: Primary CI platform
#   - macOS: Local development
#   - Windows: Git Bash, WSL
#
# CI INTEGRATION:
#   Called by: .github/workflows/test-bash.yml
#   Working directory: RFC-Shared-Agent-Scaffolding-Example/scripts/bash
#   Environment: GitHub Actions Ubuntu runner
#
# EXAMPLES:
#   # Run from bash directory
#   ./run-tests.sh
#
#   # CI usage (GitHub Actions)
#   - name: Run Bash tests
#     working-directory: RFC-Shared-Agent-Scaffolding-Example/scripts/bash
#     run: ./run-tests.sh
#
# SEE ALSO:
#   - tests/run-all.sh: Actual test runner
#   - tests/lib.sh: Test framework
#   - .github/workflows/test-bash.yml: CI workflow
#
# IMPLEMENTATION NOTES:
# - Uses 'set -e' for error handling (exits on any command failure)
# - Changes directory to script location for relative path safety
# - Uses 'exec' to replace shell with test runner (preserves exit code)
#

set -e

# Ensure we're running from the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x scripts/*.sh tests/*.sh tests/run-all.sh

# Run the test suite
exec tests/run-all.sh
