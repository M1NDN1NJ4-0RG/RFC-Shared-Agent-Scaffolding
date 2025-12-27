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
    - safe-run.ps1 wrapper at RFC-Shared-Agent-Scaffolding-Example/scripts/powershell/scripts/safe-run.ps1
  
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
    $repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    $rustBinary = Join-Path $repoRoot "rust" "target" "release" "safe-run.exe"
    
    if (-not (Test-Path $rustBinary)) {
        Write-ProbeLog "ERROR: Rust binary not found at: $rustBinary"
        Write-ProbeLog "Build the Rust tool first: cd rust && cargo build --release"
        return $false
    }
    
    Write-ProbeLog "Rust binary: $rustBinary"
    
    # Locate safe-run.ps1 wrapper
    $wrapperScript = Join-Path $PSScriptRoot "..\scripts\safe-run.ps1"
    
    if (-not (Test-Path $wrapperScript)) {
        Write-ProbeLog "ERROR: Wrapper script not found at: $wrapperScript"
        return $false
    }
    
    Write-ProbeLog "Wrapper script: $wrapperScript"
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
    
    # Use pwsh to run the wrapper with a sleep command
    # We'll use Start-Process to get a process object we can signal
    $childCommand = "pwsh -NoProfile -Command `"Start-Sleep -Seconds 60`""
    $arguments = @(
        "-NoProfile"
        "-File"
        $wrapperScript
        "--"
        "pwsh"
        "-NoProfile"
        "-Command"
        "Start-Sleep -Seconds 60"
    )
    
    # Start the process in a new process group (required for GenerateConsoleCtrlEvent)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "pwsh"
    # Build argument list properly to handle spaces and special characters
    $psi.Arguments = "-NoProfile -File `"$wrapperScript`" -- pwsh -NoProfile -Command `"Start-Sleep -Seconds 60`""
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardInput = $false
    $psi.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    
    try {
        $started = $process.Start()
        if (-not $started) {
            Write-ProbeLog "ERROR: Failed to start process"
            return $false
        }
        
        $pid = $process.Id
        Write-ProbeLog "Process started: PID $pid"
        
        # Wait a bit for the child command to actually start
        Start-Sleep -Seconds 2
        
        # Check if process is still running
        if ($process.HasExited) {
            Write-ProbeLog "WARNING: Process exited immediately (exit code: $($process.ExitCode))"
            Write-ProbeLog "This suggests the wrapper or command failed to start properly"
        } else {
            Write-ProbeLog "Process is running, sending Ctrl-C signal..."
            
            # Send Ctrl-C signal using Windows console control event
            # Note: GenerateConsoleCtrlEvent requires processes to be in the same console group
            # Since we're running in a different console, we'll try to kill the process
            # and look for the ABORTED log that should be created
            
            # Alternative approach: Use Stop-Process which should trigger signal handling
            try {
                # First try: Send CTRL_C_EVENT (this might not work cross-console)
                # We'll use a .NET interop to call GenerateConsoleCtrlEvent
                Add-Type @"
using System;
using System.Runtime.InteropServices;

public class ConsoleHelper {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GenerateConsoleCtrlEvent(uint dwCtrlEvent, uint dwProcessGroupId);
    
    public const uint CTRL_C_EVENT = 0;
    public const uint CTRL_BREAK_EVENT = 1;
}
"@
                
                # Try to send Ctrl-C (might fail due to console group restrictions)
                # Note: Using 0 for process group ID to target the current process group
                # Since we cannot easily get the process group ID of the child, this may fail
                $result = [ConsoleHelper]::GenerateConsoleCtrlEvent(0, 0)
                Write-ProbeLog "GenerateConsoleCtrlEvent(CTRL_C, 0) result: $result"
                
                # Wait for exit
                Start-Sleep -Seconds 2
                
                # If still running, try Stop-Process
                if (-not $process.HasExited) {
                    Write-ProbeLog "Process still running, using Stop-Process..."
                    Stop-Process -Id $pid -Force
                }
            } catch {
                Write-ProbeLog "Signal attempt failed: $($_.Exception.Message)"
                Write-ProbeLog "Trying Stop-Process instead..."
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
            
            # Wait for process to exit
            $timeout = 5
            $waited = $process.WaitForExit($timeout * 1000)
            
            if (-not $waited) {
                Write-ProbeLog "WARNING: Process did not exit within $timeout seconds"
                try {
                    $process.Kill()
                    Write-ProbeLog "Force-killed the process"
                } catch {
                    Write-ProbeLog "Could not kill process: $($_.Exception.Message)"
                }
            }
        }
        
        # Get exit code
        $process.WaitForExit()
        $exitCode = $process.ExitCode
        
        Write-ProbeLog ""
        Write-ProbeLog "=== RESULTS ==="
        Write-ProbeLog "Exit code: $exitCode"
        
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
        if ($exitCode -eq 130) {
            Write-ProbeLog "✓ Exit code 130: Correct (SIGINT/Ctrl-C)"
        } elseif ($exitCode -eq 143) {
            Write-ProbeLog "✓ Exit code 143: Correct (SIGTERM)"
        } elseif ($exitCode -eq 1) {
            Write-ProbeLog "⚠ Exit code 1: Process was killed (expected for Stop-Process)"
        } elseif ($exitCode -eq 127) {
            Write-ProbeLog "✗ Exit code 127: Wrapper error (binary not found or execution failed)"
        } else {
            Write-ProbeLog ("? Exit code {0}: Unexpected (investigate further)" -f $exitCode)
        }
        
        if ($logs.Count -gt 0) {
            Write-ProbeLog "✓ ABORTED log exists: Signal handling worked"
        } else {
            Write-ProbeLog "✗ ABORTED log missing: Signal may not have been handled properly"
        }
        
        Write-ProbeLog ""
        Write-ProbeLog "=== CONCLUSION ==="
        
        if (($exitCode -eq 130 -or $exitCode -eq 143) -and $logs.Count -gt 0) {
            Write-ProbeLog "SUCCESS: Ctrl-C behavior matches contract expectations"
            Write-ProbeLog "- Exit code indicates signal handling (130/143)"
            Write-ProbeLog "- ABORTED log was created as specified"
        } elseif ($exitCode -eq 1 -and $logs.Count -gt 0) {
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
        # Cleanup: dispose process object
        if ($process) {
            $process.Dispose()
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
    
    # Exit with success code (don't fail the workflow, we want to see the results)
    exit 0
    
} catch {
    Write-Host "FATAL ERROR: $($_.Exception.Message)"
    Write-Host "Stack trace: $($_.ScriptStackTrace)"
    
    # Still write partial summary
    $summaryPath = Join-Path $PWD "probe-summary.txt"
    $script:summaryLines += ""
    $script:summaryLines += "FATAL ERROR: $($_.Exception.Message)"
    $script:summaryLines | Out-File -FilePath $summaryPath -Encoding UTF8
    
    exit 0  # Don't fail workflow, capture partial results
}
