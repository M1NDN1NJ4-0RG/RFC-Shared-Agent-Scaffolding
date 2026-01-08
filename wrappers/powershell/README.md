# PowerShell Agent Ops Tests

This folder contains **Pester** tests for the PowerShell implementations:

- `scripts/safe-run.ps1`
- `scripts/safe-archive.ps1`
- `scripts/safe-check.ps1`
- `scripts/preflight_automerge_ruleset.ps1`

## Requirements

- PowerShell 7+ (`pwsh`)
- Pester 5+ (`Install-Module Pester -Scope CurrentUser`)

## Run

From this bundle root:

```powershell
pwsh -NoProfile -File ./run-tests.ps1
```

## Notes

- Preflight tests use a **fake `gh`** shim injected into `PATH` so no network calls are made.
- Signal/CTRL+C behavior is notoriously hard to simulate portably in CI. The tests cover:
  - success vs failure behavior
  - artifact creation contract
  - tail-snippet behavior
  - large-output behavior (smoke)
  - archive no-clobber + gzip
