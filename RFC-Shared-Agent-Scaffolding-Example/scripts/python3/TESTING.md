# Python 3 Agent Ops Script Tests

These tests validate the Python 3 implementations in `scripts/`:

- `safe_run.py`
- `safe_archive.py`
- `safe_check.py`
- `preflight_automerge_ruleset.py`

## How to run

```bash
./run_tests.sh
```

Or directly:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Notes

- Tests run fully offline; GitHub API calls are mocked.
- SIGINT/abort behavior is tested by spawning a long-running child process and sending Ctrl+C to the wrapper.
- Compression tests cover `gzip` because it is implemented natively in Python.
