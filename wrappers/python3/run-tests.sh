#!/usr/bin/env bash
#
# run-tests.sh - Python3 test suite runner
#
# DESCRIPTION:
#   Executes all Python3 unit tests for the safe-run/safe-check/safe-archive
#   wrapper implementations. Uses unittest framework with custom loader to
#   handle test files with hyphens in their names.
#
# USAGE:
#   ./run-tests.sh
#
# INPUTS:
#   Arguments:
#     None
#
#   Environment Variables:
#     SAFE_RUN_BIN  Path to Rust canonical binary (default: auto-detected)
#
# OUTPUTS:
#   Exit Codes:
#     0  All tests passed
#     1  One or more tests failed
#
#   Stdout:
#     Test results and summary
#
# EXAMPLES:
#   # Run all Python3 tests
#   ./run-tests.sh
#
#   # Run with custom binary path
#   SAFE_RUN_BIN=/path/to/safe-run ./run-tests.sh
#
# NOTES:
#   - Requires Python 3.8+
#   - Requires Rust canonical binary to be built
#   - Uses custom importlib loader for test_*.py files
#   - Sets SAFE_RUN_BIN environment variable for tests

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# For thin wrapper tests: point to Rust canonical binary
REPO_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"
export SAFE_RUN_BIN="${SAFE_RUN_BIN:-$REPO_ROOT/rust/target/release/safe-run}"

# Ensure we run from repo root for relative paths
cd "$ROOT_DIR"

echo "Python: $(python3 -V 2>&1 || true)"

echo "Running unit tests..."
# Python module imports require valid identifiers (no hyphens allowed)
# Standard unittest discovery can find test_*.py files and import them as modules
# Use custom importlib loader for explicit control over test discovery
python3 - <<'PYEOF'
import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

test_dir = Path("tests")
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Load each test file explicitly (snake_case pattern per Phase 4)
for test_file in sorted(test_dir.glob("test_*.py")):
    module_name = test_file.stem
    spec = spec_from_file_location(module_name, test_file)
    if spec and spec.loader:
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    sys.exit(1)
PYEOF
