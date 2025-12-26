#!/usr/bin/env pwsh
<#
.SYNOPSIS
  safe-run.ps1 - Run a command verbatim. On failure, capture stdout/stderr to .agent/FAIL-LOGS and preserve exit code.

.ENVIRONMENT
  SAFE_LOG_DIR        Failure log directory (default: .agent/FAIL-LOGS)
  SAFE_SNIPPET_LINES  On failure, print last N lines of output to stderr (default: 0)

.NOTES
  On success, produces no artifacts.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

function Slugify([string]$s) {
  $s = ($s ?? "").ToLowerInvariant()
  $s = [Regex]::Replace($s, '[^a-z0-9._-]+', '-')
  $s = [Regex]::Replace($s, '^-+|-+$', '')
  $s = [Regex]::Replace($s, '-{2,}', '-')
  if ([string]::IsNullOrWhiteSpace($s)) { return "command" }
  return $s
}

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

# Run command, capturing combined output.
$cmd = $argv[0]
$cmdArgs = @()
if ($argv.Count -gt 1) { $cmdArgs = $argv[1..($argv.Count-1)] }

$cmdStr = ($argv -join ' ')
# Use a temp file to capture and tee.
$tmp = [System.IO.Path]::GetTempFileName()

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

try {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $cmd
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute = $false
  $psi.Arguments = [string]::Join(' ', ($cmdArgs | ForEach-Object { '"{0}"' -f ($_ -replace '"','\"') }))
  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()

  # Stream combined output to a temp file to avoid unbounded memory usage.
  $writer = New-Object System.IO.StreamWriter($tmp, $false, [System.Text.Encoding]::UTF8)
  $writer.AutoFlush = $true
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
  [Console]::CancelKeyPress += $cancelHandler

  while (-not $p.HasExited) {
    Start-Sleep -Milliseconds 10
    while (-not $p.StandardOutput.EndOfStream) {
      $line = $p.StandardOutput.ReadLine()
      if ($null -ne $line) {
        Write-Output $line
        $writer.WriteLine($line)
        Add-TailLine -Queue $tail -Max $snippetLines -Line $line
      }
    }
    while (-not $p.StandardError.EndOfStream) {
      $line = $p.StandardError.ReadLine()
      if ($null -ne $line) {
        Write-Output $line
        $writer.WriteLine($line)
        Add-TailLine -Queue $tail -Max $snippetLines -Line $line
      }
    }
  }

  # Flush remaining
  while (-not $p.StandardOutput.EndOfStream) {
    $line = $p.StandardOutput.ReadLine()
    if ($null -ne $line) {
      Write-Output $line
      $writer.WriteLine($line)
      Add-TailLine -Queue $tail -Max $snippetLines -Line $line
    }
  }
  while (-not $p.StandardError.EndOfStream)  {
    $line = $p.StandardError.ReadLine()
    if ($null -ne $line) {
      Write-Output $line
      $writer.WriteLine($line)
      Add-TailLine -Queue $tail -Max $snippetLines -Line $line
    }
  }

  $rc = $p.ExitCode

  # Close writer before we copy the file anywhere.
  $writer.Flush()
  $writer.Close()
  [Console]::CancelKeyPress -= $cancelHandler

  # If we aborted, normalize the exit code to 130 (conventional for SIGINT).
  if ($script:WasAborted) {
    $rc = 130
  }

  if ($rc -eq 0) { exit 0 }

  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $ts = Get-Date -Format "yyyyMMdd-HHmmss"
  $slug = Slugify $cmdStr
  if ($script:WasAborted) {
    $outPath = Join-Path $logDir "$ts-$slug-ABORTED-fail.txt"
  } else {
    $outPath = Join-Path $logDir "$ts-$slug-fail.txt"
  }
  if (Test-Path $outPath) { $outPath = Join-Path $logDir "$ts-$slug-fail-$PID.txt" }

  Copy-Item -Force -Path $tmp -Destination $outPath

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
  try { if ($null -ne $writer) { $writer.Flush(); $writer.Close() } } catch { }
  try { if ($null -ne $cancelHandler) { [Console]::CancelKeyPress -= $cancelHandler } } catch { }

  $rc = 1
  if ($script:WasAborted) { $rc = 130 }

  try {
    # Write the exception to the temp file so it appears in the saved log.
    $msg = $_.Exception.ToString()
    [System.IO.File]::WriteAllText($tmp, $msg + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
  } catch { }

  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $ts = Get-Date -Format "yyyyMMdd-HHmmss"
  $slug = Slugify $cmdStr
  if ($script:WasAborted) {
    $outPath = Join-Path $logDir "$ts-$slug-ABORTED-fail.txt"
  } else {
    $outPath = Join-Path $logDir "$ts-$slug-fail.txt"
  }
  if (Test-Path $outPath) { $outPath = Join-Path $logDir "$ts-$slug-fail-$PID.txt" }

  try { Copy-Item -Force -Path $tmp -Destination $outPath } catch { }

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
  if (Test-Path $tmp) { Remove-Item -Force $tmp -ErrorAction SilentlyContinue }
}
