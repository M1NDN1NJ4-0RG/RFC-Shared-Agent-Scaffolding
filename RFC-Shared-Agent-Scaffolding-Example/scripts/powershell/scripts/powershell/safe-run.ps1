#!/usr/bin/env pwsh
<#
.SYNOPSIS
  safe-run.ps1 - Run a command verbatim. On failure, capture stdout/stderr to .agent/FAIL-LOGS and preserve exit code.

.ENVIRONMENT
  SAFE_LOG_DIR        Failure log directory (default: .agent/FAIL-LOGS)
  SAFE_SNIPPET_LINES  On failure, print last N lines of output to stderr (default: 0)
  SAFE_RUN_VIEW       Set to "merged" to enable optional merged view output

.NOTES
  On success, produces no artifacts.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

if ($args.Count -eq 0 -or $args[0] -in @('-h','--help')) {
  Write-Err "Usage: scripts/powershell/safe-run.ps1 [--] <command> [args...]"
  exit 2
}

# Optional "--"
$argv = @($args)
if ($argv[0] -eq '--') { $argv = $argv[1..($argv.Count-1)] }
if ($argv.Count -eq 0) { exit 2 }

$logDir = $env:SAFE_LOG_DIR
if ([string]::IsNullOrWhiteSpace($logDir)) { $logDir = ".agent/FAIL-LOGS" }

$snippetRaw = $env:SAFE_SNIPPET_LINES
if ([string]::IsNullOrWhiteSpace($snippetRaw)) { $snippetRaw = "0" }
if (-not ($snippetRaw -match '^\d+$')) { Write-Err "ERROR: SAFE_SNIPPET_LINES must be a non-negative integer"; exit 1 }
$snippetLines = [int]$snippetRaw

$viewMode = $env:SAFE_RUN_VIEW
if ([string]::IsNullOrWhiteSpace($viewMode)) { $viewMode = "" }

# Run command, capturing stdout and stderr separately (M0-P1-I1).
$cmd = $argv[0]
$cmdArgs = @()
if ($argv.Count -gt 1) { $cmdArgs = $argv[1..($argv.Count-1)] }

# Build properly quoted command string for META event (POSIX shell-style quoting)
function Quote-ShellArg {
  param([string]$Arg)
  # Simple args don't need quoting
  if ($Arg -match '^[a-zA-Z0-9_\-\.\/=]+$') {
    return $Arg
  }
  # Quote using single quotes, escape embedded single quotes
  $escaped = $Arg -replace "'", "'\''"
  return "'$escaped'"
}

$cmdStr = ($argv | ForEach-Object { Quote-ShellArg $_ }) -join ' '

# Use temp files to capture stdout and stderr separately.
$tmpStdout = [System.IO.Path]::GetTempFileName()
$tmpStderr = [System.IO.Path]::GetTempFileName()

# Event ledger: track observed-order events with sequence numbers
$script:EventLedger = New-Object System.Collections.Generic.List[PSCustomObject]
$script:SeqNum = 0

function Emit-Event {
  param(
    [string]$Stream,
    [string]$Text
  )
  $script:SeqNum++
  $script:EventLedger.Add([PSCustomObject]@{
    Seq = $script:SeqNum
    Stream = $Stream
    Text = $Text
  })
}

# Track aborts (Ctrl+C / termination) so we can still persist partial logs.
$script:WasAborted = $false
$script:AbortReason = ""

# Tail buffer for optional snippets (keeps last N lines only).
function Add-TailLine {
  param(
    [System.Collections.Generic.Queue[string]]$Queue,
    [int]$Max,
    [string]$Line
  )
  if ($Max -le 0) { return }
  if ($Queue.Count -ge $Max) { [void]$Queue.Dequeue() }
  $Queue.Enqueue($Line)
}

# Helper function to format log content with event ledger and optional merged view
function Format-LogContent {
  param(
    [string]$StdoutPath,
    [string]$StderrPath
  )
  
  $stdout_content = (Get-Content -LiteralPath $StdoutPath -Raw -ErrorAction SilentlyContinue) ?? ""
  $stderr_content = (Get-Content -LiteralPath $StderrPath -Raw -ErrorAction SilentlyContinue) ?? ""
  
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append("=== STDOUT ===$([Environment]::NewLine)")
  [void]$sb.Append($stdout_content)
  [void]$sb.Append("=== STDERR ===$([Environment]::NewLine)")
  [void]$sb.Append($stderr_content)
  
  # Event ledger
  [void]$sb.Append("$([Environment]::NewLine)--- BEGIN EVENTS ---$([Environment]::NewLine)")
  foreach ($evt in $script:EventLedger) {
    [void]$sb.Append("[SEQ=$($evt.Seq)][$($evt.Stream)] $($evt.Text)$([Environment]::NewLine)")
  }
  [void]$sb.Append("--- END EVENTS ---$([Environment]::NewLine)")
  
  # Optional merged view
  if ($viewMode -eq 'merged') {
    [void]$sb.Append("$([Environment]::NewLine)--- BEGIN MERGED (OBSERVED ORDER) ---$([Environment]::NewLine)")
    foreach ($evt in $script:EventLedger) {
      [void]$sb.Append("[#$($evt.Seq)][$($evt.Stream)] $($evt.Text)$([Environment]::NewLine)")
    }
    [void]$sb.Append("--- END MERGED ---$([Environment]::NewLine)")
  }
  
  return $sb.ToString()
}

try {
  # Emit start event
  Emit-Event 'META' "safe-run start: cmd=`"$cmdStr`""
  
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $cmd
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute = $false
  $psi.Arguments = [string]::Join(' ', ($cmdArgs | ForEach-Object { '"{0}"' -f ($_ -replace '"','\"') }))
  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()

  # Stream stdout and stderr separately to temp files (M0-P1-I1).
  $writerStdout = New-Object System.IO.StreamWriter($tmpStdout, $false, [System.Text.Encoding]::UTF8)
  $writerStdout.AutoFlush = $true
  $writerStderr = New-Object System.IO.StreamWriter($tmpStderr, $false, [System.Text.Encoding]::UTF8)
  $writerStderr.AutoFlush = $true
  $tail = New-Object System.Collections.Generic.Queue[string]

  # Handle Ctrl+C so we can stop the child process and still write an ABORTED log.
  $cancelHandler = {
    param($sender, $e)
    $script:WasAborted = $true
    $script:AbortReason = "SIGINT"
    # Prevent PowerShell from terminating immediately; we'll clean up ourselves.
    $e.Cancel = $true
    try {
      if ($null -ne $p -and -not $p.HasExited) {
        try { $p.Kill($true) } catch { try { $p.Kill() } catch { } }
      }
    } catch { }
  }
  # Register cancel handler (may not be available in all environments)
  try { [Console]::CancelKeyPress += $cancelHandler } catch { }

  while (-not $p.HasExited) {
    Start-Sleep -Milliseconds 10
    while (-not $p.StandardOutput.EndOfStream) {
      $line = $p.StandardOutput.ReadLine()
      if ($null -ne $line) {
        Write-Output $line
        $writerStdout.WriteLine($line)
        Emit-Event 'STDOUT' $line
        Add-TailLine -Queue $tail -Max $snippetLines -Line $line
      }
    }
    while (-not $p.StandardError.EndOfStream) {
      $line = $p.StandardError.ReadLine()
      if ($null -ne $line) {
        [Console]::Error.WriteLine($line)
        $writerStderr.WriteLine($line)
        Emit-Event 'STDERR' $line
        Add-TailLine -Queue $tail -Max $snippetLines -Line $line
      }
    }
  }

  # Flush remaining
  while (-not $p.StandardOutput.EndOfStream) {
    $line = $p.StandardOutput.ReadLine()
    if ($null -ne $line) {
      Write-Output $line
      $writerStdout.WriteLine($line)
      Emit-Event 'STDOUT' $line
      Add-TailLine -Queue $tail -Max $snippetLines -Line $line
    }
  }
  while (-not $p.StandardError.EndOfStream)  {
    $line = $p.StandardError.ReadLine()
    if ($null -ne $line) {
      [Console]::Error.WriteLine($line)
      $writerStderr.WriteLine($line)
      Emit-Event 'STDERR' $line
      Add-TailLine -Queue $tail -Max $snippetLines -Line $line
    }
  }

  $rc = $p.ExitCode
  
  # Emit exit event
  Emit-Event 'META' "safe-run exit: code=$rc"

  # Close writers before we copy files.
  $writerStdout.Flush()
  $writerStdout.Close()
  $writerStderr.Flush()
  $writerStderr.Close()
  # Unregister cancel handler (may not be available in all environments)
  try { [Console]::CancelKeyPress -= $cancelHandler } catch { }

  # If we aborted, normalize the exit code to 130 (conventional for SIGINT).
  if ($script:WasAborted) {
    $rc = 130
  }

  if ($rc -eq 0) { exit 0 }

  # On failure, create log file with M0-P1-I1 format (split stdout/stderr with markers) + event ledger
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  
  # M0-P1-I2: Use ISO8601-pidPID-STATUS.log format
  $ts = Get-Date -AsUtc -Format "yyyyMMdd\THHmmss\Z"
  $processId = $PID
  if ($script:WasAborted) {
    $status = "ABORTED"
  } else {
    $status = "FAIL"
  }
  $outPath = Join-Path $logDir "${ts}-pid${processId}-${status}.log"
  
  # Write M0-P1-I1 format: split streams with markers + event ledger + optional merged view
  $logContent = Format-LogContent -StdoutPath $tmpStdout -StderrPath $tmpStderr
  [System.IO.File]::WriteAllText($outPath, $logContent, [System.Text.Encoding]::UTF8)

  Write-Err ""
  if ($script:WasAborted) {
    $why = $script:AbortReason
    if ([string]::IsNullOrWhiteSpace($why)) { $why = "ABORTED" }
    Write-Err ("SAFE-RUN: command aborted ({0})" -f $why)
  } else {
    Write-Err ("SAFE-RUN: command failed (exit={0})" -f $rc)
  }
  Write-Err ("SAFE-RUN: failure log saved to: {0}" -f $outPath)

  if ($snippetLines -gt 0) {
    Write-Err ""
    Write-Err ("SAFE-RUN: last {0} lines of output:" -f $snippetLines)
    foreach ($l in $tail) { Write-Err $l }
  }

  exit $rc
}
catch {
  # Ensure we still persist something useful when the wrapper itself errors
  # (e.g., executable not found) or if PowerShell stops the pipeline.
  $script:AbortReason = $script:AbortReason

  # Best-effort cleanup of open resources.
  try { if ($null -ne $writerStdout) { $writerStdout.Flush(); $writerStdout.Close() } } catch { }
  try { if ($null -ne $writerStderr) { $writerStderr.Flush(); $writerStderr.Close() } } catch { }
  try { if ($null -ne $cancelHandler) { [Console]::CancelKeyPress -= $cancelHandler } } catch { }

  $rc = 1
  if ($script:WasAborted) { $rc = 130 }

  try {
    # Write the exception to the stderr temp file so it appears in the saved log.
    $msg = $_.Exception.ToString()
    [System.IO.File]::WriteAllText($tmpStderr, $msg + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
  } catch { }

  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  
  # M0-P1-I2: Use ISO8601-pidPID-STATUS.log format
  $ts = Get-Date -AsUtc -Format "yyyyMMdd\THHmmss\Z"
  $processId = $PID
  if ($script:WasAborted) {
    $status = "ABORTED"
  } else {
    $status = "ERROR"
  }
  $outPath = Join-Path $logDir "${ts}-pid${processId}-${status}.log"

  # Write M0-P1-I1 format: split streams with markers + event ledger + optional merged view
  $logContent = Format-LogContent -StdoutPath $tmpStdout -StderrPath $tmpStderr
  try { [System.IO.File]::WriteAllText($outPath, $logContent, [System.Text.Encoding]::UTF8) } catch { }

  Write-Err ""
  if ($script:WasAborted) {
    $why = $script:AbortReason
    if ([string]::IsNullOrWhiteSpace($why)) { $why = "ABORTED" }
    Write-Err ("SAFE-RUN: wrapper aborted ({0})" -f $why)
  } else {
    Write-Err "SAFE-RUN: wrapper error"
  }
  Write-Err ("SAFE-RUN: failure log saved to: {0}" -f $outPath)
  exit $rc
}
finally {
  if (Test-Path $tmpStdout) { Remove-Item -Force $tmpStdout -ErrorAction SilentlyContinue }
  if (Test-Path $tmpStderr) { Remove-Item -Force $tmpStderr -ErrorAction SilentlyContinue }
}
