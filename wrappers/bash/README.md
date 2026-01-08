# Bash Agent Ops Script Tests

This folder contains a **self-contained** test harness for the Bash implementations:

- `scripts/bash/safe-run.sh`
- `scripts/bash/safe-archive.sh`
- `scripts/bash/safe-check.sh`
- `scripts/bash/preflight_automerge_ruleset.sh`

## Requirements

- `bash` (3.2+ is fine for running these tests)
- `jq` (required by `preflight_automerge_ruleset.sh`)
- `gzip` (optional; only needed for the gzip compression test)

## Run

From the bundle root:

```bash
chmod +x scripts/bash/*.sh tests/bash/*.sh tests/bash/run_all.sh
tests/bash/run_all.sh
```

The runner prints PASS/FAIL for each case and exits non-zero if anything fails.

## What gets tested

### safe-run.sh

- Success: no artifacts created
- Failure: stdout+stderr captured, exit code preserved
- `SAFE_SNIPPET_LINES` tail snippet printing
- `SAFE_LOG_DIR` override
- SIGINT (Ctrl+C): creates `*ABORTED-fail.txt` and preserves forensic output

### safe-archive.sh

- `--all` moves logs and handles filenames with spaces
- No-clobber behavior (duplicate archive name causes failure and preserves originals)
- Gzip compression when available
- `--file` archives one file

### preflight_automerge_ruleset.sh

- Happy path (success)
- Missing required contexts
- Enforcement not active
- Does not target `~DEFAULT_BRANCH`
- Auth error classification (exit 2)

### safe-check.sh

- Sanity check end-to-end in a temp workspace
