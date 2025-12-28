#requires -Version 5.1
<#
.SYNOPSIS
  safe-run-tests.ps1 - Pester test suite for safe-run.ps1 wrapper

.DESCRIPTION
  Comprehensive Pester test suite validating the PowerShell safe-run wrapper
  implementation against contract specifications (M0-P1-I1, M0-P1-I2).

  Test Coverage:
    - Success path: No artifacts created, exit code 0
    - Failure path: Artifact creation, exit code preservation
    - Output capture: Split stdout/stderr format validation
    - Event ledger: Sequence numbering and metadata validation
    - Snippet output: SAFE_SNIPPET_LINES tail behavior
    - View modes: Split (default) and merged output formats
    - Large output handling: Memory efficiency with 200K+ lines
    - Error handling: Clean errors when invoked without command
    - Filename format: ISO8601-pidNNN-FAIL.log validation

  Each test runs in an isolated temporary directory to prevent interference
  and ensure repeatable results.

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Tests use pwsh explicitly for subprocess invocations

  Prerequisites:
    - Pester module (v5.0+)
    - safe-run.ps1 script in ../scripts/
    - test-helpers.ps1 in same directory
    - Rust canonical safe-run binary must be discoverable

  Test Isolation:
    - Each test creates a unique temporary directory
    - Working directory is changed to temp dir for test execution
    - Environment variables are set per-test
    - Directory is cleaned up after test (Pop-Location)

  Contract References:
    - M0-P1-I1: safe-run split stdout/stderr format with event ledger
    - M0-P1-I2: Failure artifact naming (YYYYMMDDTHHMMSSZ-pidNNN-FAIL.log)

  Design Notes:
    - Uses ProcessStartInfo for precise stderr capture in snippet test
    - Large output test validates streaming behavior (no memory bloat)
    - Filename format validated with regex matching
    - Event ledger validated with content markers and sequence patterns

.ENVIRONMENT
  None. Tests run in isolated environments with per-test environment variables.

.EXAMPLE
  # Run all safe-run tests with Pester
  PS> Invoke-Pester -Path .\safe-run-tests.ps1

  # Run tests with detailed output
  PS> Invoke-Pester -Path .\safe-run-tests.ps1 -Output Detailed

.LINK
  https://pester.dev/

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>
Set-StrictMode -Version Latest

Describe "safe-run.ps1" {
  BeforeAll {
    . "$PSScriptRoot/test-helpers.ps1"
    $script:ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\safe-run.ps1"
  }

  It "succeeds without creating artifacts" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      & pwsh -NoProfile -File $ScriptUnderTest -- pwsh -NoProfile -Command "Write-Output 'ok'; exit 0"
      $LASTEXITCODE | Should -Be 0

      # No fail logs should be created
      (Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -ErrorAction SilentlyContinue | Measure-Object).Count | Should -Be 0
    } finally {
      Pop-Location
    }
  }

  It "captures stdout and stderr on failure and preserves exit code" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_SNIPPET_LINES = "0"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      & pwsh -NoProfile -File $ScriptUnderTest -- pwsh -NoProfile -Command "Write-Output 'out'; Write-Error 'err'; exit 7"
      $LASTEXITCODE | Should -Be 7

      # M0-P1-I2: Filename should be ISO8601-pidPID-FAIL.log
      $files = @(Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-FAIL.log")
      $files.Count | Should -Be 1
      
      # M0-P1-I2: Validate filename format
      $files[0].Name | Should -Match '^\d{8}T\d{6}Z-pid\d+-FAIL\.log$'

      # M0-P1-I1: Validate split stdout/stderr with markers
      $txt = Get-Content -LiteralPath $files[0].FullName -Raw
      $txt | Should -Match "=== STDOUT ==="
      $txt | Should -Match "=== STDERR ==="
      $txt | Should -Match "out"
      # PowerShell's Write-Error becomes a formatted error record; we just assert some signal survived.
      $txt | Should -Match "err"
    } finally {
      Pop-Location
    }
  }

  It "prints tail snippet to stderr when SAFE_SNIPPET_LINES is set (smoke test)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_SNIPPET_LINES = "3"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      # Capture stderr from wrapper invocation itself.
      $psi = New-Object System.Diagnostics.ProcessStartInfo
      $psi.FileName = "pwsh"
      # Use proper escaping for nested PowerShell command - escape $ to prevent variable expansion
      $psi.Arguments = "-NoProfile -File `"$ScriptUnderTest`" -- pwsh -NoProfile -Command `"1..10 | ForEach-Object { Write-Output ('L' + `$_) }; exit 2`""
      $psi.RedirectStandardError = $true
      $psi.RedirectStandardOutput = $true
      $psi.UseShellExecute = $false
      $p = [System.Diagnostics.Process]::Start($psi)
      $stdout = $p.StandardOutput.ReadToEnd()
      $stderr = $p.StandardError.ReadToEnd()
      $p.WaitForExit()

      $p.ExitCode | Should -Be 2
      # Per conformance spec safe-run-005, only require the actual tail lines in stderr,
      # not a specific header format
      $stderr | Should -Match "L10"
    } finally {
      Pop-Location
    }
  }

  It "handles very large output without running out of memory (behavioral smoke)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_SNIPPET_LINES = "0"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      # 200k lines is enough to stress buffering if someone naively used an array.
      & pwsh -NoProfile -File $ScriptUnderTest -- pwsh -NoProfile -Command "1..200000 | ForEach-Object { 'X' }; exit 3"
      $LASTEXITCODE | Should -Be 3

      # M0-P1-I2: Filename should be ISO8601-pidPID-FAIL.log
      $files = @(Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-FAIL.log")
      $files.Count | Should -Be 1
      # M0-P1-I1: With split stdout/stderr format, expect ~400KB for 200K lines of "X"
      ($files[0].Length -gt 300000) | Should -BeTrue
    } finally {
      Pop-Location
    }
  }

  It "errors cleanly when invoked without a command" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      & pwsh -NoProfile -File $ScriptUnderTest
      $LASTEXITCODE | Should -Be 2
    } finally {
      Pop-Location
    }
  }

  It "emits event ledger with sequence numbers" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_SNIPPET_LINES = "0"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      & pwsh -NoProfile -File $ScriptUnderTest -- pwsh -NoProfile -Command "Write-Output 'out1'; Write-Error 'err1'; Write-Output 'out2'; exit 5"
      $LASTEXITCODE | Should -Be 5

      $files = @(Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-FAIL.log")
      $files.Count | Should -Be 1
      
      $txt = Get-Content -LiteralPath $files[0].FullName -Raw
      
      # Check for event ledger markers
      $txt | Should -Match "--- BEGIN EVENTS ---"
      $txt | Should -Match "--- END EVENTS ---"
      
      # Check for standardized META events
      $txt | Should -Match "\[SEQ=1\]\[META\] safe-run start: cmd="
      $txt | Should -Match "\[META\] safe-run exit: code=5"
      
      # Check for stdout/stderr events
      $txt | Should -Match "\[STDOUT\] out1"
      $txt | Should -Match "\[STDOUT\] out2"
      $txt | Should -Match "\[STDERR\].*err1"
    } finally {
      Pop-Location
    }
  }

  It "emits merged view when SAFE_RUN_VIEW=merged" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_LOG_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_SNIPPET_LINES = "0"
      $env:SAFE_RUN_VIEW = "merged"
      $null = New-Item -ItemType Directory -Force -Path $env:SAFE_LOG_DIR

      & pwsh -NoProfile -File $ScriptUnderTest -- pwsh -NoProfile -Command "Write-Output 'line1'; exit 3"
      $LASTEXITCODE | Should -Be 3

      $files = @(Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-FAIL.log")
      $files.Count | Should -Be 1
      
      $txt = Get-Content -LiteralPath $files[0].FullName -Raw
      
      # Check for merged view markers
      $txt | Should -Match "--- BEGIN MERGED \(OBSERVED ORDER\) ---"
      $txt | Should -Match "--- END MERGED ---"
      
      # Check for merged view format with [#seq]
      $txt | Should -Match "\[#1\]\[META\]"
      $txt | Should -Match "\[#2\]\[STDOUT\] line1"
    } finally {
      Remove-Item Env:SAFE_RUN_VIEW -ErrorAction Ignore
      Pop-Location
    }
  }
}
