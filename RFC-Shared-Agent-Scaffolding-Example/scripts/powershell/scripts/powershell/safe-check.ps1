#!/usr/bin/env pwsh
<#
.SYNOPSIS
  safe-check.ps1 - Contract verification for PowerShell scripts.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }
function Die([string]$Msg) { Write-Err "ERROR: $Msg"; exit 1 }

if ($args.Count -ne 0) { Write-Err "Usage: scripts/powershell/safe-check.ps1"; exit 2 }

$logDir = $env:SAFE_LOG_DIR
if ([string]::IsNullOrWhiteSpace($logDir)) { $logDir = ".agent/FAIL-LOGS" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path ".agent/FAIL-ARCHIVE" | Out-Null

if (-not (Test-Path "scripts/powershell/safe-run.ps1")) { Die "Missing scripts/powershell/safe-run.ps1" }
if (-not (Test-Path "scripts/powershell/safe-archive.ps1")) { Die "Missing scripts/powershell/safe-archive.ps1" }

$before = (Get-ChildItem -Path $logDir -File | Measure-Object).Count

# failure path
& pwsh scripts/powershell/safe-run.ps1 -- pwsh -NoProfile -Command 'Write-Output "hello"; Write-Error "boom"; exit 42' *> $null
if ($LASTEXITCODE -ne 42) { Die "safe-run did not preserve exit code (expected 42, got $LASTEXITCODE)" }

$after = (Get-ChildItem -Path $logDir -File | Measure-Object).Count
if ($after -ne ($before + 1)) { Die "safe-run failure did not create exactly one artifact (before=$before after=$after)" }
Write-Err "INFO: safe-run failure-path OK"

# success path
$before = $after
& pwsh scripts/powershell/safe-run.ps1 -- pwsh -NoProfile -Command 'Write-Output "ok"; exit 0' *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-run success returned non-zero ($LASTEXITCODE)" }

$after = (Get-ChildItem -Path $logDir -File | Measure-Object).Count
if ($after -ne $before) { Die "safe-run success created artifacts (before=$before after=$after)" }
Write-Err "INFO: safe-run success-path OK"

# archive newest
$newest = Get-ChildItem -Path $logDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $newest) { Die "No fail logs found to test archiving" }

$base = $newest.Name
$dest = Join-Path ".agent/FAIL-ARCHIVE" $base

& pwsh scripts/powershell/safe-archive.ps1 $newest.FullName *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-archive failed ($LASTEXITCODE)" }
if (-not (Test-Path $dest)) { Die "Archive file missing: $dest" }
if (Test-Path $newest.FullName) { Die "Source file still exists (expected moved)" }
Write-Err "INFO: safe-archive move OK"

# no-clobber
$dummy = Join-Path $logDir $base
"dummy" | Out-File -Encoding utf8 -FilePath $dummy

& pwsh scripts/powershell/safe-archive.ps1 $dummy *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-archive no-clobber failed ($LASTEXITCODE)" }

$contents = Get-Content -Raw -ErrorAction Stop $dest
if ($contents -notmatch 'hello') { Die "Archive content changed unexpectedly (no-clobber violation suspected)" }
Write-Err "INFO: safe-archive no-clobber OK"

Write-Err "INFO: SAFE-CHECK: contract verification PASSED"
exit 0
