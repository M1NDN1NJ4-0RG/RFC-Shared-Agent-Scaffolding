# Agent Ops Python Tests (unittest)

This bundle contains **integration-style** tests for the Python implementation of the Agent Ops scripts:

- `safe_run.py`
- `safe_archive.py`
- `safe_check.py`
- `preflight_automerge_ruleset.py`

## Why integration tests?
These scripts are CLI wrappers and their correctness is mostly about **observable behavior**:
exit codes, artifact creation, no-clobber behavior, and handling signals.

## Requirements
- Python 3 recommended (runs the test runner).
- The tests will attempt to run the scripts using `python3`, then `python`, then `python2`.
  - You can force the interpreter by setting `TEST_PY` (path or command name).

## Run

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Forcing a specific interpreter

```bash
TEST_PY=python2 ./run_tests.sh
# or
TEST_PY=/usr/bin/python2.7 ./run_tests.sh
```

## What’s Covered

### `safe_run.py`
- Success path: no artifacts, exit 0
- Failure path: creates `*-fail.txt`, preserves exit code, captures stdout+stderr
- Snippet behavior (tail snippet on stderr)
- SIGINT handling: creates `*-aborted.txt`, exit code 130

### `safe_archive.py`
- Moves all logs from FAIL-LOGS -> FAIL-ARCHIVE
- No-clobber behavior (does not overwrite existing archive entries)
- gzip compression mode

### `preflight_automerge_ruleset.py`
- Uses a fake `gh` CLI in `PATH` to simulate GitHub API responses
- Passes when required checks match
- Fails when missing checks / ruleset not found

### `safe_check.py`
- Smoke test that `safe_check.py` passes when its sibling scripts exist

## Notes
- The tests create their own temporary `.agent/` directories.
- They do **not** make any real network calls.
