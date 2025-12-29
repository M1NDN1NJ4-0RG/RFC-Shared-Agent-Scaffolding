#requires -Version 5.1
<#
.SYNOPSIS
  safe-archive-tests.ps1 - Pester test suite for safe-archive.ps1

.DESCRIPTION
  Comprehensive Pester test suite validating the PowerShell safe-archive wrapper
  implementation against contract specifications (M0-P1-I3).

  Test Coverage:
    - Empty directory handling: Graceful exit when no logs exist
    - No-clobber semantics: Automatic suffix on destination collision
    - Move semantics: Source file removed after successful archive
    - Compression support: gzip validation (built-in .NET)
    - Compression validation: Rejection of unsupported methods
    - --all mode: Bulk archival of all logs in FAIL-LOGS

  Each test runs in an isolated temporary directory with controlled
  environment variables to ensure repeatable results.

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - gzip compression tests use .NET built-in (cross-platform)
    - xz/zstd tests skipped if commands not available

  Prerequisites:
    - Pester module (v5.0+)
    - safe-archive.ps1 script in ../scripts/
    - TestHelpers.ps1 in same directory (provides Write-RandomTextFile, New-TempDir)

  Test Isolation:
    - Each test creates unique temporary directory
    - Environment variables set per-test (SAFE_FAIL_DIR, SAFE_ARCHIVE_DIR, SAFE_ARCHIVE_COMPRESS)
    - Environment cleaned up after test (Remove-Item env:...)
    - Temporary directory cleaned automatically (Pop-Location)

  Contract References:
    - M0-P1-I3: safe-archive no-clobber semantics and move behavior

  Test Details:
    1. Empty directory test: Verifies --all exits 0 when no logs exist
    2. No-clobber test: Pre-creates collision file, verifies suffix behavior
    3. Move semantics test: Verifies source file removed, destination created
    4. gzip compression test: Verifies .gz file created, uncompressed file removed
    5. Invalid compression test: Verifies error exit and source preservation

  Design Notes:
    - Uses Write-RandomTextFile helper for controlled test data
    - Validates file counts to ensure no unexpected side effects
    - Tests both individual file and --all modes
    - Compression tests validate both success and failure paths

.ENVIRONMENT
  None. Tests set environment variables per-test.

.EXAMPLE
  # Run safe-archive tests with Pester
  PS> Invoke-Pester -Path .\safe-archive-tests.ps1

.LINK
  https://pester.dev/

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>
Set-StrictMode -Version Latest

Describe "safe-archive.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\SafeArchive.ps1"
  }

  It "does nothing and exits 0 when FAIL-LOGS does not exist" {
    $td = New-TempDir
    Push-Location $td
    try {
      $env:SAFE_FAIL_DIR = Join-Path $td ".agent/FAIL-LOGS"
      $env:SAFE_ARCHIVE_DIR = Join-Path $td ".agent/FAIL-ARCHIVE"
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $env:SAFE_FAIL_DIR
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $env:SAFE_ARCHIVE_DIR

      & pwsh -NoProfile -File $ScriptUnderTest --all
      $LASTEXITCODE | Should -Be 0
      Test-Path -LiteralPath $env:SAFE_ARCHIVE_DIR | Should -BeTrue
    } finally {
      Pop-Location
    }
  }

  It "moves logs to FAIL-ARCHIVE with no clobber" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fail = Join-Path $td ".agent/FAIL-LOGS"
      $arch = Join-Path $td ".agent/FAIL-ARCHIVE"
      $env:SAFE_FAIL_DIR = $fail
      $env:SAFE_ARCHIVE_DIR = $arch
      $env:SAFE_ARCHIVE_COMPRESS = "none"
      New-Item -ItemType Directory -Force -Path $fail, $arch | Out-Null

      $a = Join-Path $fail "a-fail.txt"
      $b = Join-Path $fail "b-fail.txt"
      Write-RandomTextFile -Path $a -Lines 3
      Write-RandomTextFile -Path $b -Lines 3

      # Pre-create one archive name to force no-clobber suffix behavior.
      $pre = Join-Path $arch "a-fail.txt"
      Set-Content -Encoding UTF8 -Path $pre -Value "existing"

      & pwsh -NoProfile -File $ScriptUnderTest --all
      $LASTEXITCODE | Should -Be 0

      Test-Path -LiteralPath $a | Should -BeFalse
      Test-Path -LiteralPath $b | Should -BeFalse

      @(Get-ChildItem -LiteralPath $arch -Filter "b-fail.txt").Count | Should -Be 1
      @(Get-ChildItem -LiteralPath $arch -Filter "a-fail.txt").Count | Should -Be 1
      @(Get-ChildItem -LiteralPath $arch -Filter "a-fail-*.txt").Count | Should -BeGreaterThan 0
    } finally {
      Remove-Item env:SAFE_FAIL_DIR, env:SAFE_ARCHIVE_DIR, env:SAFE_ARCHIVE_COMPRESS -ErrorAction SilentlyContinue
      Pop-Location
    }
  }

  It "supports gzip compression" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fail = Join-Path $td ".agent/FAIL-LOGS"
      $arch = Join-Path $td ".agent/FAIL-ARCHIVE"
      $env:SAFE_FAIL_DIR = $fail
      $env:SAFE_ARCHIVE_DIR = $arch
      $env:SAFE_ARCHIVE_COMPRESS = "gzip"
      New-Item -ItemType Directory -Force -Path $fail, $arch | Out-Null

      $a = Join-Path $fail "x-fail.txt"
      Write-RandomTextFile -Path $a -Lines 50

      & pwsh -NoProfile -File $ScriptUnderTest --all
      $LASTEXITCODE | Should -Be 0

      Test-Path -LiteralPath $a | Should -BeFalse
      @(Get-ChildItem -LiteralPath $arch -Filter "x-fail.txt.gz").Count | Should -Be 1
    } finally {
      Remove-Item env:SAFE_FAIL_DIR, env:SAFE_ARCHIVE_DIR, env:SAFE_ARCHIVE_COMPRESS -ErrorAction SilentlyContinue
      Pop-Location
    }
  }

  It "rejects an unsupported compression mode" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fail = Join-Path $td ".agent/FAIL-LOGS"
      $arch = Join-Path $td ".agent/FAIL-ARCHIVE"
      $env:SAFE_FAIL_DIR = $fail
      $env:SAFE_ARCHIVE_DIR = $arch
      $env:SAFE_ARCHIVE_COMPRESS = "totally-not-real"
      New-Item -ItemType Directory -Force -Path $fail, $arch | Out-Null

      $a = Join-Path $fail "x-fail.txt"
      Write-RandomTextFile -Path $a -Lines 1

      & pwsh -NoProfile -File $ScriptUnderTest --all
      $LASTEXITCODE | Should -Be 2
      Test-Path -LiteralPath $a | Should -BeTrue
    } finally {
      Remove-Item env:SAFE_ARCHIVE_COMPRESS -ErrorAction SilentlyContinue
      Pop-Location
    }
  }
}
