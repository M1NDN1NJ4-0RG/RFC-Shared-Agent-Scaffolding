# Problem observed (from latest CI logs)

The probe starts `safe-run.ps1` successfully and calls `GenerateConsoleCtrlEvent(CTRL_C_EVENT, <PID>)` which returns
`True`, but the target process continues running and the probe then force-kills it. This likely happens because
`GenerateConsoleCtrlEvent`’s second parameter is a **process group ID**, not a PID. We are currently passing a PID
(e.g., `7468`), so the call can "succeed" while delivering no useful control event.

# Goal

Make the Windows CI probe actually deliver a console control event to the process tree running `safe-run.ps1` (or
conclusively prove it can’t), and capture evidence such as:

- - - Wrapper exit code - Whether an **ABORTED** log is created - Logs and process snapshots uploaded as artifacts

# Required changes

## 1. Fix signal delivery: use a process group, not PID

Update `RFC-Shared-Agent-Scaffolding-Example/scripts/powershell/tests/phase3-ctrlc-probe.ps1`.

### Option A (preferred): Create a new process group and signal it

- - Launch the target using Win32 `CreateProcess` with `CREATE_NEW_PROCESS_GROUP`. - Capture the process group ID (for
  `CreateProcess`, the group ID is typically the PID of the group leader process). - Call
  `GenerateConsoleCtrlEvent(CTRL_C_EVENT, <groupId>)` (or `CTRL_BREAK_EVENT` if Ctrl-C still doesn’t work). - - Ensure
  the probe ignores Ctrl-C itself: - Call `SetConsoleCtrlHandler(NULL, TRUE)` before sending - Call
  `SetConsoleCtrlHandler(NULL, FALSE)` after sending

You can implement `CreateProcess` via Add-Type C# P/Invoke. You’ll need:

- - `CreateProcessW` - `STARTUPINFO` - `PROCESS_INFORMATION` - Flags: `CREATE_NEW_PROCESS_GROUP` (`0x00000200`) and
  potentially `CREATE_NEW_CONSOLE` (`0x00000010`) depending on attachment strategy.

### Option B: Attach/broadcast to the console’s group

If option A is too complex:

- - Use `AttachConsole(targetPid)` to attach to the child’s console. - Use `GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0)`
  to broadcast to the attached console’s group (`groupId` `0` sends to all processes sharing the console). - This may
  require the child to be started with `CREATE_NEW_CONSOLE`.

Try option A first. Fall back to option B if needed.

## 2. Try both `CTRL_C_EVENT` and `CTRL_BREAK_EVENT`

In the probe logic:

- - - Attempt Ctrl-C first. - If that fails, attempt Ctrl-Break.
