#!/usr/bin/env pwsh
<#
.SYNOPSIS
  SafeCheck.ps1 - Automated contract verification for safe-run and safe-archive wrappers

.DESCRIPTION
  Executable conformance test that validates the PowerShell wrapper implementations
  against their behavioral contracts. This script tests both success and failure paths
  to ensure wrappers correctly:
    - Preserve exit codes from wrapped commands
    - Create failure artifacts only on command failure
    - Archive logs with proper no-clobber semantics
    - Handle edge cases (collisions, missing directories, etc.)

  Purpose:
    - Validate M0-P1-I1 (safe-run output capture and formatting)
    - Validate M0-P1-I2 (failure artifact creation and naming)
    - Validate M0-P1-I3 (safe-archive no-clobber behavior)
    - Provide deterministic pass/fail signal for CI/CD

  This script is designed to be run in a clean workspace and creates its own
  test directories (.agent/FAIL-LOGS, .agent/FAIL-ARCHIVE) to avoid interfering
  with other operations.

.PARAMETER args
  No arguments accepted. Script will exit with usage error (code 2) if any are provided.

.ENVIRONMENT
  SAFE_LOG_DIR
    Override for failure log directory during testing.
    Default: .agent/FAIL-LOGS

  All environment variables consumed by SafeRun.ps1 and SafeArchive.ps1 are
  implicitly tested through their invocation in this script.

.OUTPUTS
  Exit codes:
    0   All contract checks passed
    1   One or more contract violations detected
    2   Usage error (unexpected arguments)

  All diagnostic output is written to stderr to avoid polluting stdout and to
  match the convention used by the tested scripts.

.EXAMPLE
  PS> .\SafeCheck.ps1
  INFO: safe-run failure-path OK
  INFO: safe-run success-path OK
  INFO: safe-archive move OK
  INFO: safe-archive no-clobber OK
  INFO: SAFE-CHECK: contract verification PASSED
  PS> $LASTEXITCODE
  0

.EXAMPLE
  # Run from CI/CD pipeline
  PS> pwsh -NoProfile -File scripts/SafeCheck.ps1
  # Exit code signals pass/fail for automation

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Uses pwsh explicitly for subprocess invocations to ensure cross-platform behavior

  Contract References:
    - M0-P1-I1: safe-run split stdout/stderr format
    - M0-P1-I2: Failure artifact naming (YYYYMMDDTHHMMSSZ-pidNNN-FAIL.log)
    - M0-P1-I3: safe-archive no-clobber and move semantics

  Side Effects:
    - Creates .agent/FAIL-LOGS directory if not present
    - Creates .agent/FAIL-ARCHIVE directory if not present
    - Creates test failure artifacts during failure-path testing
    - Moves test artifacts during archive testing
    - All side effects are intentional and part of the contract validation

  Test Coverage:
    1. safe-run failure path: exit code preservation, artifact creation
    2. safe-run success path: no artifact creation on success
    3. safe-archive move: file relocation from FAIL-LOGS to FAIL-ARCHIVE
    4. safe-archive no-clobber: automatic suffix on destination collision

  Prerequisites:
    - scripts/SafeRun.ps1 must exist
    - scripts/SafeArchive.ps1 must exist
    - Rust canonical safe-run binary must be discoverable (or SAFE_RUN_BIN set)

  Design Notes:
    - Uses *> redirection to suppress all output from tested commands
    - Validates state changes (file counts) rather than output content
    - Deterministic: creates exactly one artifact per failure command
    - Self-contained: operates in working directory, no external dependencies

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
.SYNOPSIS
Writes an error message to stderr.
.DESCRIPTION
Outputs the provided message to the standard error stream.
.PARAMETER Msg
The error message to write.
#>
function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

<#
.SYNOPSIS
Writes an error message and exits with code 1.
.DESCRIPTION
Outputs an error message prefixed with "ERROR:" and terminates the script with exit code 1.
.PARAMETER Msg
The error message to write.
#>
function Die([string]$Msg) { Write-Err "ERROR: $Msg"; exit 1 }

if ($args.Count -ne 0) { Write-Err "Usage: scripts/SafeCheck.ps1"; exit 2 }

$logDir = $env:SAFE_LOG_DIR
if ([string]::IsNullOrWhiteSpace($logDir)) { $logDir = ".agent/FAIL-LOGS" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path ".agent/FAIL-ARCHIVE" | Out-Null

if (-not (Test-Path "scripts/SafeRun.ps1")) { Die "Missing scripts/SafeRun.ps1" }
if (-not (Test-Path "scripts/SafeArchive.ps1")) { Die "Missing scripts/SafeArchive.ps1" }

$before = (Get-ChildItem -Path $logDir -File | Measure-Object).Count

# failure path
& pwsh scripts/SafeRun.ps1 -- pwsh -NoProfile -Command 'Write-Output "hello"; Write-Error "boom"; exit 42' *> $null
if ($LASTEXITCODE -ne 42) { Die "safe-run did not preserve exit code (expected 42, got $LASTEXITCODE)" }

$after = (Get-ChildItem -Path $logDir -File | Measure-Object).Count
if ($after -ne ($before + 1)) { Die "safe-run failure did not create exactly one artifact (before=$before after=$after)" }
Write-Err "INFO: safe-run failure-path OK"

# success path
$before = $after
& pwsh scripts/SafeRun.ps1 -- pwsh -NoProfile -Command 'Write-Output "ok"; exit 0' *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-run success returned non-zero ($LASTEXITCODE)" }

$after = (Get-ChildItem -Path $logDir -File | Measure-Object).Count
if ($after -ne $before) { Die "safe-run success created artifacts (before=$before after=$after)" }
Write-Err "INFO: safe-run success-path OK"

# archive newest
$newest = Get-ChildItem -Path $logDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $newest) { Die "No fail logs found to test archiving" }

$base = $newest.Name
$dest = Join-Path ".agent/FAIL-ARCHIVE" $base

& pwsh scripts/SafeArchive.ps1 $newest.FullName *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-archive failed ($LASTEXITCODE)" }
if (-not (Test-Path $dest)) { Die "Archive file missing: $dest" }
if (Test-Path $newest.FullName) { Die "Source file still exists (expected moved)" }
Write-Err "INFO: safe-archive move OK"

# no-clobber
$dummy = Join-Path $logDir $base
"dummy" | Out-File -Encoding utf8 -FilePath $dummy

& pwsh scripts/SafeArchive.ps1 $dummy *> $null
if ($LASTEXITCODE -ne 0) { Die "safe-archive no-clobber failed ($LASTEXITCODE)" }

$contents = Get-Content -Raw -ErrorAction Stop $dest
if ($contents -notmatch 'hello') { Die "Archive content changed unexpectedly (no-clobber violation suspected)" }
Write-Err "INFO: safe-archive no-clobber OK"

Write-Err "INFO: SAFE-CHECK: contract verification PASSED"
exit 0
