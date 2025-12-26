#!/usr/bin/env bash
#
# Wrapper script to run Bash bundle tests
# This script is called by CI (test-bash.yml) and delegates to the actual test runner

set -e

# Ensure we're running from the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x scripts/*.sh tests/*.sh tests/run_all.sh

# Run the test suite
exec tests/run_all.sh
