# Perl Agent Ops Tests

These are TAP-style tests for the Perl implementations:

- - `safe_run.pl` - `safe_archive.pl` - `safe_check.pl` - `preflight_automerge_ruleset.pl`

## Run

From this directory:

```bash
./run-tests.sh
```

Uses `prove` if present, otherwise runs each `.t` file directly.

## What gets tested

- - `safe_run.pl`: success/no artifacts, failure log creation + exit code preservation, snippet tail emission, large
  output capture, SIGINT abort logging (`ABORTED` suffix). - `safe_archive.pl`: `--all` move behavior, spaces in
  filenames, no-clobber collision handling (auto-suffix). - `safe_check.pl`: runs contract checks in a clean sandbox. -
  `preflight_automerge_ruleset.pl`: mocked `gh` CLI responses for both success and failure paths; token secrecy check.
