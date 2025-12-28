# Phase 3 Windows Ctrl-C Probe - Implementation Summary

## Overview

This implementation adds a GitHub Actions workflow and probe script to investigate the real Ctrl-C behavior of `safe-run.ps1` on native Windows without requiring a human Windows machine.

## Files Added

1. **`.github/workflows/phase3-windows-ctrlc-probe.yml`**
   - GitHub Actions workflow that runs on `windows-latest`
   - Triggers: Manual dispatch (`workflow_dispatch`), pull requests, and pushes to main
   - Builds Rust canonical tool
   - Executes the probe script
   - Uploads artifacts (logs + summary)

2. **`RFC-Shared-Agent-Scaffolding-Example/scripts/powershell/tests/phase3-ctrlc-probe.ps1`**
   - PowerShell probe script that tests Ctrl-C behavior
   - Creates isolated temp directory for logs
   - Sets environment variables (SAFE_RUN_BIN, SAFE_LOG_DIR)
   - Launches safe-run.ps1 with long-running command (60-second sleep)
   - Sends Ctrl-C signal using Windows `GenerateConsoleCtrlEvent` API
   - Records exit code and checks for ABORTED log
   - Writes detailed summary to `probe-summary.txt`

## How to Use

### Manual Trigger

1. Navigate to the repository on GitHub
2. Go to **Actions** → **Phase 3 Windows Ctrl-C Probe**
3. Click **Run workflow** → **Run workflow**
4. Wait for completion
5. Download artifacts: `phase3-ctrlc-probe-results`
6. Review `probe-summary.txt` for findings

### Automatic Trigger

The workflow runs automatically on:
- Pull requests that modify PowerShell scripts or the workflow itself
- Pushes to main branch with same path filters

## Expected Outcomes

### Success Case (Contract Compliance)
- Exit code: 130 (SIGINT) or 143 (SIGTERM)
- ABORTED log created in temp directory
- Log filename format: `YYYYMMDDTHHMMSSZ-pidNNN-ABORTED.log`

### Issue Case (Contract Violation)
- Exit code: 127 (wrapper error) or other unexpected code
- No ABORTED log created
- Indicates PowerShell exception handling may be interfering

## What the Probe Tests

The probe investigates whether:

1. **Signal delivery works**: Does Ctrl-C reach the Rust canonical tool?
2. **Exit code is correct**: Is it 130/143 as specified in the contract?
3. **ABORTED log is created**: Does the signal handler create the expected log?
4. **PowerShell wrapper preserves behavior**: Does the catch {} block interfere?

## Interpretation Guide

The probe script provides detailed interpretation in `probe-summary.txt`:

- **✓ Exit code 130/143 + ABORTED log**: Full contract compliance
- **⚠ Exit code 1 + ABORTED log**: Process killed but log created (partial success)
- **✗ Exit code 127 or missing log**: Wrapper issue (requires investigation)

## Limitations

- **Windows-specific**: Uses Windows console control events (not portable to Unix)
- **Timing-dependent**: May need adjustments if process startup is slow
- **Console group restrictions**: GenerateConsoleCtrlEvent may fail cross-console
- **Fallback to Stop-Process**: If signal delivery fails, forcefully kills process

## Technical Details

### Signal Delivery Approach

The probe uses Win32 APIs to properly create a process group and deliver console control events:

1. **Process Creation**: `CreateProcessW` with `CREATE_NEW_PROCESS_GROUP` flag
   - Creates the target process in its own process group
   - The process leader's PID becomes the process group ID
   - Ensures proper signal isolation and delivery

2. **Signal Protection**: `SetConsoleCtrlHandler(NULL, TRUE)`
   - Prevents the probe process from terminating itself
   - Must be called before sending console control events

3. **Primary Signal**: `GenerateConsoleCtrlEvent(CTRL_C_EVENT, processGroupId)`
   - Sends Ctrl-C to the target process group
   - Uses process group ID (not PID) as required by Windows API
   - Waits 2 seconds to check if process exited

4. **Secondary Signal**: `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, processGroupId)`
   - If CTRL_C_EVENT fails, attempts Ctrl-Break
   - Some applications handle Ctrl-Break differently than Ctrl-C
   - Waits 2 seconds to check if process exited

5. **Signal Restoration**: `SetConsoleCtrlHandler(NULL, FALSE)`
   - Restores normal Ctrl-C handling in probe process
   - Called after signal attempts complete

6. **Fallback**: `Stop-Process` (TerminateProcess)
   - If both console control events fail, forcefully terminates the process
   - Used as last resort to ensure probe completes
   - Less representative of actual Ctrl-C behavior

### Win32 APIs Used

- `CreateProcessW`: Process creation with process group control
- `GenerateConsoleCtrlEvent`: Console control event delivery
- `SetConsoleCtrlHandler`: Signal handler management
- `WaitForSingleObject`: Process synchronization
- `GetExitCodeProcess`: Exit code retrieval
- `CloseHandle`: Resource cleanup

### Environment Setup

```powershell
$env:SAFE_RUN_BIN = "rust/target/release/safe-run.exe"
$env:SAFE_LOG_DIR = "$env:RUNNER_TEMP/phase3-ctrlc-<guid>"
$env:SAFE_SNIPPET_LINES = "0"
```

### Process Launch

```
CreateProcessW(
    applicationName: NULL,
    commandLine: "pwsh -NoProfile -File safe-run.ps1 -- pwsh -NoProfile -Command Start-Sleep -Seconds 60",
    creationFlags: CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
    ...
)
```

## Next Steps

After running the probe:

1. **Review artifacts**: Download and examine `probe-summary.txt`
2. **Check ABORTED log**: If created, inspect content for signal metadata
3. **Analyze exit code**: Verify it matches contract expectations
4. **Address issues**: If contract violations found, fix wrapper signal handling
5. **Document findings**: Update issue with probe results

## Contract References

- **M0-P1-I2**: Failure artifact naming and ABORTED status
- **Signal handling**: SIGINT → 130, SIGTERM → 143
- **ABORTED log**: Created on signal interruption with "safe-run interrupted by signal" message

## Related Files

- `rust/src/safe_run.rs`: Signal handling implementation in canonical tool
- `RFC-Shared-Agent-Scaffolding-Example/scripts/powershell/scripts/safe-run.ps1`: Wrapper being tested
- `.github/workflows/test-powershell.yml`: Related PowerShell test workflow
