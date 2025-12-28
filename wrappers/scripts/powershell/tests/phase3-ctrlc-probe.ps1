#!/usr/bin/env pwsh
<#
.SYNOPSIS
  phase3-ctrlc-probe.ps1 - Windows Ctrl-C signal behavior probe for safe-run.ps1

.DESCRIPTION
  This script programmatically tests how safe-run.ps1 handles Ctrl-C (SIGINT)
  on native Windows by sending console control events to a running process.
  
  Purpose:
    - Validate that Ctrl-C creates an ABORTED log (per contract)
    - Verify exit code is 130 (SIGINT) or 143 (SIGTERM) as expected
    - Gather hard evidence of actual behavior on windows-latest runner
  
  Contract Intent (from RFC):
    - Ctrl-C should trigger signal handler in Rust canonical tool
    - Should create ABORTED log in SAFE_LOG_DIR
    - Should exit with code 130 (SIGINT) or 143 (SIGTERM)
  
  Risk Being Investigated:
    - PowerShell may throw PipelineStoppedException on Ctrl-C
    - Wrapper's catch {} block may convert this to exit 127
    - ABORTED log may not be created if wrapper exits prematurely
  
  Test Methodology:
    1. Create isolated temp directory for logs
    2. Set SAFE_RUN_BIN to built Rust binary (rust/target/release/safe-run.exe)
    3. Set SAFE_LOG_DIR to temp directory
    4. Launch safe-run.ps1 as background job with long-running child command
    5. Wait for child process to start (ensure it's running)
    6. Send Ctrl-C to the process group using GenerateConsoleCtrlEvent
    7. Wait for process to exit
    8. Record exit code
    9. Check for ABORTED log in SAFE_LOG_DIR
    10. Write findings to probe-summary.txt

.OUTPUTS
  Creates probe-summary.txt with findings:
    - Exit code observed
    - Whether ABORTED log was created
    - Log filename (if created)
    - Interpretation of results
  
  Creates temp directory under $env:RUNNER_TEMP with logs (if any)

.NOTES
  Platform: Windows only (uses Windows-specific console control events)
  
  Requires:
    - PowerShell 5.1+ or pwsh 6+
    - Rust canonical tool built at rust/target/release/safe-run.exe
    - safe-run.ps1 wrapper at wrappers/scripts/powershell/scripts/safe-run.ps1
  
  Design Notes:
    - Uses GenerateConsoleCtrlEvent for native Windows Ctrl-C simulation
    - Creates new process group to isolate signal delivery
    - Uses Start-Process with -PassThru to capture process object
    - Waits for process exit to ensure signal was delivered
    - Multiple Ctrl-C send attempts to overcome timing issues
  
  Limitations:
    - Windows-specific implementation (cannot test Unix signal behavior)
    - Timing-dependent (may need retries if process not ready)
    - Process group creation may affect signal delivery

.ENVIRONMENT
  RUNNER_TEMP
    GitHub Actions runner temp directory (used for test workspace).

.EXAMPLE
  # Run phase3 probe (disabled by default in CI)
  PS> .\phase3-ctrlc-probe.ps1

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'  # Don't stop on expected errors

# Helper function to write to both console and summary file
$script:summaryLines = @()
function Write-ProbeLog {
    param([string]$Message)
    Write-Host $Message
    $script:summaryLines += $Message
}

# Main probe logic
function Invoke-CtrlCProbe {
    Write-ProbeLog "=== Phase 3: Windows Ctrl-C Probe ==="
    Write-ProbeLog "Timestamp: $(Get-Date -Format 'o')"
    Write-ProbeLog ""
    
    # Create temp directory for logs
    $tempBase = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
    $probeTempDir = Join-Path $tempBase "phase3-ctrlc-$([guid]::NewGuid())"
    New-Item -ItemType Directory -Force -Path $probeTempDir | Out-Null
    
    Write-ProbeLog "Temp directory: $probeTempDir"
    
    # Locate Rust canonical binary
    $repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
    $rustBinary = Join-Path $repoRoot "rust" "target" "release" "safe-run.exe"
    
    if (-not (Test-Path $rustBinary)) {
        Write-ProbeLog "ERROR: Rust binary not found at: $rustBinary"
        Write-ProbeLog "Build the Rust tool first: cd rust && cargo build --release"
        return $false
    }
    
    Write-ProbeLog "Rust binary: $rustBinary"
    
    # Locate safe-run.ps1 wrapper with detailed debugging
    Write-ProbeLog "=== Path Resolution Debug ==="
    Write-ProbeLog "Current location: $(Get-Location)"
    Write-ProbeLog "`$PSScriptRoot: $PSScriptRoot"
    
    $wrapperScript = Join-Path $PSScriptRoot "..\scripts\safe-run.ps1"
    Write-ProbeLog "Wrapper script (relative): $wrapperScript"
    
    # Test if the path exists before resolving
    if (-not (Test-Path $wrapperScript)) {
        Write-ProbeLog "ERROR: Wrapper script not found at: $wrapperScript"
        Write-ProbeLog ""
        Write-ProbeLog "Directory listing of parent: $PSScriptRoot\.."
        Get-ChildItem "$PSScriptRoot\.." | ForEach-Object {
            Write-ProbeLog "  - $($_.Name)"
        }
        Write-ProbeLog ""
        Write-ProbeLog "Looking for 'scripts' subdirectory..."
        $scriptsDir = Join-Path $PSScriptRoot "..\scripts"
        if (Test-Path $scriptsDir) {
            Write-ProbeLog "Found scripts directory at: $scriptsDir"
            Write-ProbeLog "Contents:"
            Get-ChildItem $scriptsDir | ForEach-Object {
                Write-ProbeLog "  - $($_.Name)"
            }
        } else {
            Write-ProbeLog "Scripts directory not found at: $scriptsDir"
        }
        return $false
    }
    
    Write-ProbeLog "Wrapper script found: $wrapperScript"
    Write-ProbeLog ""
    
    # Set environment variables for the test
    $env:SAFE_RUN_BIN = $rustBinary
    $env:SAFE_LOG_DIR = $probeTempDir
    $env:SAFE_SNIPPET_LINES = "0"
    
    Write-ProbeLog "Environment:"
    Write-ProbeLog "  SAFE_RUN_BIN: $env:SAFE_RUN_BIN"
    Write-ProbeLog "  SAFE_LOG_DIR: $env:SAFE_LOG_DIR"
    Write-ProbeLog ""
    
    # Test strategy: Launch safe-run.ps1 with a long-running command (sleep)
    # Then send Ctrl-C and observe the behavior
    Write-ProbeLog "Launching safe-run.ps1 with long-running command..."
    
    # Define Win32 API structures and functions for process creation with process group
    # This allows us to create a new process group and properly send console control events
    if (-not ([System.Management.Automation.PSTypeName]'Win32Process').Type) {
        Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32Process {
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcessW(
        string lpApplicationName,
        StringBuilder lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GenerateConsoleCtrlEvent(uint dwCtrlEvent, uint dwProcessGroupId);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool SetConsoleCtrlHandler(IntPtr HandlerRoutine, bool Add);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);
    
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO {
        public uint cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public ushort wShowWindow;
        public ushort cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }
    
    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }
    
    public const uint CREATE_NEW_PROCESS_GROUP = 0x00000200;
    public const uint CREATE_NO_WINDOW = 0x08000000;
    public const uint CTRL_C_EVENT = 0;
    public const uint CTRL_BREAK_EVENT = 1;
    public const uint WAIT_TIMEOUT = 0x00000102;
    public const uint WAIT_OBJECT_0 = 0x00000000;
    public const uint STILL_ACTIVE = 259;
}
"@
    }
    
    # Resolve full path to pwsh.exe to avoid PATH lookup issues
    Write-ProbeLog "=== Executable Resolution Debug ==="
    $pwshPath = (Get-Command pwsh).Source
    Write-ProbeLog "Resolved pwsh path: $pwshPath"
    Write-ProbeLog "pwsh exists: $(Test-Path $pwshPath)"
    
    # Resolve and normalize the wrapper script path to avoid relative path issues
    Write-ProbeLog ""
    Write-ProbeLog "=== Wrapper Script Resolution Debug ==="
    try {
        $wrapperScriptResolved = Resolve-Path -LiteralPath $wrapperScript -ErrorAction Stop | Select-Object -ExpandProperty Path
        Write-ProbeLog "Resolved wrapper script path: $wrapperScriptResolved"
        Write-ProbeLog "Resolved wrapper exists: $(Test-Path $wrapperScriptResolved)"
    } catch {
        Write-ProbeLog "ERROR: Failed to resolve wrapper script path"
        Write-ProbeLog "Exception: $($_.Exception.Message)"
        return $false
    }
    
    # Build the command line for the target process
    # Use -File with -- separator for clean argument passing
    # The -- tells safe-run.ps1 that everything after is the child command to execute
    # We pass NULL to lpApplicationName and let Windows parse the command line
    $commandLine = "`"$pwshPath`" -NoProfile -File `"$wrapperScriptResolved`" -- pwsh -NoProfile -Command `"Start-Sleep -Seconds 60`""
    Write-ProbeLog ""
    Write-ProbeLog "=== CreateProcessW Debug ==="
    Write-ProbeLog "Command line: $commandLine"
    Write-ProbeLog "Command line length: $($commandLine.Length) characters"
    Write-ProbeLog "lpApplicationName: NULL (Windows will parse from command line)"
    
    # Create STARTUPINFO structure
    $si = New-Object Win32Process+STARTUPINFO
    $si.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($si)
    
    # Create PROCESS_INFORMATION structure
    $pi = New-Object Win32Process+PROCESS_INFORMATION
    
    # Create the process with CREATE_NEW_PROCESS_GROUP flag
    # Remove CREATE_NO_WINDOW for now to ensure console control events can be delivered
    # StringBuilder needs extra capacity for null terminator (CreateProcessW modifies the buffer)
    $cmdLineBuilder = New-Object System.Text.StringBuilder($commandLine.Length + 100)
    $cmdLineBuilder.Append($commandLine) | Out-Null
    $creationFlags = [Win32Process]::CREATE_NEW_PROCESS_GROUP
    
    Write-ProbeLog ""
    Write-ProbeLog "Creating process with CREATE_NEW_PROCESS_GROUP flag (0x$($creationFlags.ToString('X8')))..."
    Write-ProbeLog "StringBuilder capacity: $($cmdLineBuilder.Capacity)"
    Write-ProbeLog "StringBuilder length: $($cmdLineBuilder.Length)"
    
    $success = [Win32Process]::CreateProcessW(
        $null,                   # lpApplicationName - NULL to parse from command line
        $cmdLineBuilder,          # lpCommandLine
        [IntPtr]::Zero,          # lpProcessAttributes
        [IntPtr]::Zero,          # lpThreadAttributes
        $false,                  # bInheritHandles
        $creationFlags,          # dwCreationFlags
        [IntPtr]::Zero,          # lpEnvironment
        $null,                   # lpCurrentDirectory
        [ref]$si,                # lpStartupInfo
        [ref]$pi                 # lpProcessInformation
    )
    
    if (-not $success) {
        $lastError = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        Write-ProbeLog ""
        Write-ProbeLog "=== CreateProcessW FAILED ==="
        Write-ProbeLog "Error code: $lastError (0x$($lastError.ToString('X8')))"
        Write-ProbeLog "Error description: $([System.ComponentModel.Win32Exception]::new($lastError).Message)"
        Write-ProbeLog ""
        Write-ProbeLog "Parameters used:"
        Write-ProbeLog "  lpApplicationName: NULL (parsed from command line)"
        Write-ProbeLog "  lpCommandLine: $($cmdLineBuilder.ToString())"
        Write-ProbeLog "  dwCreationFlags: 0x$($creationFlags.ToString('X8'))"
        Write-ProbeLog ""
        Write-ProbeLog "File system checks:"
        Write-ProbeLog "  pwsh.exe exists: $(Test-Path $pwshPath)"
        Write-ProbeLog "  Wrapper exists: $(Test-Path $wrapperScriptResolved)"
        return $false
    }
    
    try {
        $targetPid = $pi.dwProcessId
        $processGroupId = $pi.dwProcessId  # For CREATE_NEW_PROCESS_GROUP, the PID is the group ID
        Write-ProbeLog "Process started: PID $targetPid (Process Group ID: $processGroupId)"
        
        # Wait a bit for the child command to actually start
        Start-Sleep -Seconds 2
        
        # Check if process is still running
        $exitCode = 0
        $stillRunning = [Win32Process]::GetExitCodeProcess($pi.hProcess, [ref]$exitCode)
        
        if ($stillRunning -and $exitCode -ne [Win32Process]::STILL_ACTIVE) {
            Write-ProbeLog "WARNING: Process exited immediately (exit code: $exitCode)"
            Write-ProbeLog "This suggests the wrapper or command failed to start properly"
        } else {
            Write-ProbeLog "Process is running, sending console control events..."
            
            try {
                # Ignore Ctrl-C in this process so we don't kill ourselves
                Write-ProbeLog "Setting console control handler to ignore signals in probe process..."
                [Win32Process]::SetConsoleCtrlHandler([IntPtr]::Zero, $true) | Out-Null
                
                # First attempt: Send CTRL_C_EVENT
                Write-ProbeLog "Attempting CTRL_C_EVENT to process group $processGroupId..."
                $resultCtrlC = [Win32Process]::GenerateConsoleCtrlEvent(
                    [Win32Process]::CTRL_C_EVENT,
                    $processGroupId
                )
                Write-ProbeLog "GenerateConsoleCtrlEvent(CTRL_C_EVENT, $processGroupId) result: $resultCtrlC"
                
                # Wait to see if the signal was delivered
                Start-Sleep -Seconds 2
                
                # Check if process exited
                $exitCodeAfterCtrlC = 0
                $stillRunningAfterCtrlC = [Win32Process]::GetExitCodeProcess($pi.hProcess, [ref]$exitCodeAfterCtrlC)
                
                if ($stillRunningAfterCtrlC -and $exitCodeAfterCtrlC -eq [Win32Process]::STILL_ACTIVE) {
                    Write-ProbeLog "Process still running after CTRL_C_EVENT, trying CTRL_BREAK_EVENT..."
                    
                    # Second attempt: Send CTRL_BREAK_EVENT
                    $resultCtrlBreak = [Win32Process]::GenerateConsoleCtrlEvent(
                        [Win32Process]::CTRL_BREAK_EVENT,
                        $processGroupId
                    )
                    Write-ProbeLog "GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, $processGroupId) result: $resultCtrlBreak"
                    
                    # Wait again
                    Start-Sleep -Seconds 2
                    
                    # Check if process exited
                    $exitCodeAfterBreak = 0
                    $stillRunningAfterBreak = [Win32Process]::GetExitCodeProcess($pi.hProcess, [ref]$exitCodeAfterBreak)
                    
                    if ($stillRunningAfterBreak -and $exitCodeAfterBreak -eq [Win32Process]::STILL_ACTIVE) {
                        Write-ProbeLog "Process still running after CTRL_BREAK_EVENT, using TerminateProcess as fallback..."
                        # Force kill as last resort - note we're using Stop-Process since we have the PID
                        Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                    } else {
                        Write-ProbeLog "Process exited after CTRL_BREAK_EVENT"
                    }
                } else {
                    Write-ProbeLog "Process exited after CTRL_C_EVENT"
                }
                
                # Restore normal Ctrl-C handling in this process
                [Win32Process]::SetConsoleCtrlHandler([IntPtr]::Zero, $false) | Out-Null
                
            } catch {
                Write-ProbeLog "Signal attempt failed: $($_.Exception.Message)"
                Write-ProbeLog "Trying Stop-Process instead..."
                Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                
                # Restore normal Ctrl-C handling
                try {
                    [Win32Process]::SetConsoleCtrlHandler([IntPtr]::Zero, $false) | Out-Null
                } catch {
                    # Ignore errors restoring handler
                }
            }
            
            # Wait for process to exit with timeout
            $timeout = 5000  # 5 seconds in milliseconds
            Write-ProbeLog "Waiting up to 5 seconds for process to exit..."
            $waitResult = [Win32Process]::WaitForSingleObject($pi.hProcess, $timeout)
            
            if ($waitResult -eq [Win32Process]::WAIT_TIMEOUT) {
                Write-ProbeLog "WARNING: Process did not exit within timeout, force killing..."
                Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
        }
        
        # Get final exit code
        $finalExitCode = 0
        [Win32Process]::GetExitCodeProcess($pi.hProcess, [ref]$finalExitCode) | Out-Null
        
        Write-ProbeLog ""
        Write-ProbeLog "=== RESULTS ==="
        Write-ProbeLog "Exit code: $finalExitCode"
        
        # Check for ABORTED log
        $logs = @(Get-ChildItem -LiteralPath $probeTempDir -Filter "*-ABORTED.log" -ErrorAction SilentlyContinue)
        $failLogs = @(Get-ChildItem -LiteralPath $probeTempDir -Filter "*-FAIL.log" -ErrorAction SilentlyContinue)
        
        if ($logs.Count -gt 0) {
            Write-ProbeLog "ABORTED log created: YES"
            Write-ProbeLog "  Filename: $($logs[0].Name)"
            
            # Show log content for analysis
            Write-ProbeLog ""
            Write-ProbeLog "Log content preview:"
            $content = Get-Content -LiteralPath $logs[0].FullName -Raw -ErrorAction SilentlyContinue
            if ($content) {
                $preview = $content.Substring(0, [Math]::Min(500, $content.Length))
                Write-ProbeLog $preview
                if ($content.Length -gt 500) {
                    Write-ProbeLog "... (truncated)"
                }
            }
        } else {
            Write-ProbeLog "ABORTED log created: NO"
        }
        
        if ($failLogs.Count -gt 0) {
            Write-ProbeLog "FAIL log created: YES"
            Write-ProbeLog "  Filename: $($failLogs[0].Name)"
        }
        
        Write-ProbeLog ""
        Write-ProbeLog "=== INTERPRETATION ==="
        
        # Interpret results
        if ($finalExitCode -eq 130) {
            Write-ProbeLog "✓ Exit code 130: Correct (SIGINT/Ctrl-C)"
        } elseif ($finalExitCode -eq 143) {
            Write-ProbeLog "✓ Exit code 143: Correct (SIGTERM)"
        } elseif ($finalExitCode -eq 1) {
            Write-ProbeLog "⚠ Exit code 1: Process was killed (expected for Stop-Process)"
        } elseif ($finalExitCode -eq 127) {
            Write-ProbeLog "✗ Exit code 127: Wrapper error (binary not found or execution failed)"
        } else {
            Write-ProbeLog ("? Exit code {0}: Unexpected (investigate further)" -f $finalExitCode)
        }
        
        if ($logs.Count -gt 0) {
            Write-ProbeLog "✓ ABORTED log exists: Signal handling worked"
        } else {
            Write-ProbeLog "✗ ABORTED log missing: Signal may not have been handled properly"
        }
        
        Write-ProbeLog ""
        Write-ProbeLog "=== CONCLUSION ==="
        
        if (($finalExitCode -eq 130 -or $finalExitCode -eq 143) -and $logs.Count -gt 0) {
            Write-ProbeLog "SUCCESS: Ctrl-C behavior matches contract expectations"
            Write-ProbeLog "- Exit code indicates signal handling (130/143)"
            Write-ProbeLog "- ABORTED log was created as specified"
        } elseif ($finalExitCode -eq 1 -and $logs.Count -gt 0) {
            Write-ProbeLog "PARTIAL: Process killed, but ABORTED log created"
            Write-ProbeLog "- Stop-Process was used (not a true Ctrl-C)"
            Write-ProbeLog "- But signal handling still created ABORTED log"
        } else {
            Write-ProbeLog "ISSUE: Behavior does not fully match contract"
            Write-ProbeLog "- Review exit code and log presence above"
            Write-ProbeLog "- May indicate wrapper catch {} converting signal to different exit code"
            Write-ProbeLog "- Or signal not being delivered to Rust tool properly"
        }
        
        Write-ProbeLog ""
        Write-ProbeLog "=== ARTIFACTS ==="
        Write-ProbeLog "Log directory: $probeTempDir"
        Write-ProbeLog "Summary file: probe-summary.txt (in workspace root)"
        
        return $true
        
    } catch {
        Write-ProbeLog "ERROR: Exception during probe: $($_.Exception.Message)"
        Write-ProbeLog "Stack trace: $($_.ScriptStackTrace)"
        return $false
    } finally {
        # Cleanup: close Win32 handles
        if ($pi.hProcess -ne [IntPtr]::Zero) {
            [Win32Process]::CloseHandle($pi.hProcess) | Out-Null
        }
        if ($pi.hThread -ne [IntPtr]::Zero) {
            [Win32Process]::CloseHandle($pi.hThread) | Out-Null
        }
    }
}

# Run the probe
try {
    $success = Invoke-CtrlCProbe
    
    # Write summary to file in workspace root
    $summaryPath = Join-Path $PWD "probe-summary.txt"
    $script:summaryLines | Out-File -FilePath $summaryPath -Encoding UTF8
    
    Write-Host ""
    Write-Host "Summary written to: $summaryPath"
    
    if (-not $success) {
        Write-Host ""
        Write-Host "RESULT: INCONCLUSIVE - Probe encountered errors during execution"
        Write-Host "Review probe-summary.txt for details"
        Write-Host ""
        Write-Host "Exiting with error status to fail the workflow"
        # Exit 1 to fail the workflow when probe is inconclusive
        exit 1
    }
    
    # Exit with success code when probe completes successfully
    exit 0
    
} catch {
    Write-Host ""
    Write-Host "================================================================"
    Write-Host "RESULT: INCONCLUSIVE - FATAL ERROR"
    Write-Host "================================================================"
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Stack trace: $($_.ScriptStackTrace)"
    Write-Host ""
    Write-Host "The probe script threw an unhandled exception."
    Write-Host "This prevents signal behavior validation."
    Write-Host ""
    
    # Still write partial summary
    $summaryPath = Join-Path $PWD "probe-summary.txt"
    $script:summaryLines += ""
    $script:summaryLines += "================================================================"
    $script:summaryLines += "RESULT: INCONCLUSIVE - FATAL ERROR"
    $script:summaryLines += "================================================================"
    $script:summaryLines += "FATAL ERROR: $($_.Exception.Message)"
    $script:summaryLines += "Stack trace: $($_.ScriptStackTrace)"
    $script:summaryLines += ""
    $script:summaryLines += "The probe script threw an unhandled exception."
    $script:summaryLines += "This prevents signal behavior validation."
    $script:summaryLines | Out-File -FilePath $summaryPath -Encoding UTF8
    
    Write-Host "Partial summary written to: $summaryPath"
    Write-Host ""
    Write-Host "Exiting with error status to fail the workflow"
    
    # Exit 1 to fail the workflow when fatal error occurs
    exit 1
}
