#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# For thin wrapper tests: point to Rust canonical binary
REPO_ROOT="$(cd "$ROOT_DIR/../../.." && pwd)"
export SAFE_RUN_BIN="${SAFE_RUN_BIN:-$REPO_ROOT/rust/target/release/safe-run}"

# Ensure we run from repo root for relative paths
cd "$ROOT_DIR"

echo "Python: $(python3 -V 2>&1 || true)"

echo "Running unit tests..."
# Python module imports require valid identifiers (no hyphens allowed)
# Standard unittest discovery can find test-*.py files, but cannot import them as modules
# Use custom importlib loader to work around this constraint
python3 - <<'PYEOF'
import sys
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

test_dir = Path("tests")
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Load each test file explicitly (hyphens don't work with standard discovery)
for test_file in sorted(test_dir.glob("test-*.py")):
    module_name = test_file.stem.replace("-", "_")
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


