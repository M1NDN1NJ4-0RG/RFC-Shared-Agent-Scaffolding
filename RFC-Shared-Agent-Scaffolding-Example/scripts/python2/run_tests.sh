#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Optional: export TEST_PY=/path/to/python2 or python3
PY="${TEST_PY:-python3}"

# We run unittest discovery. (No third-party deps like pytest required.)
"$PY" -m unittest discover -s tests -p "test_*.py" -v
