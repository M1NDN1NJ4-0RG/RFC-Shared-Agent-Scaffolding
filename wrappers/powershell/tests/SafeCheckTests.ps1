#requires -Version 5.1
<#
.SYNOPSIS
  SafeCheckTests.ps1 - Pester test suite for SafeCheck.ps1 contract verifier

.DESCRIPTION
  Pester test suite that validates the SafeCheck.ps1 contract verification script.
  
  The SafeCheck.ps1 script is itself a test, so this meta-test ensures that the
  contract verifier runs successfully in a clean, isolated environment.

  Test Coverage:
    - Runs SafeCheck.ps1 in temporary workspace
    - Validates successful execution (exit code 0)
    - Ensures contract checks for SafeRun and SafeArchive pass
    - Verifies proper environment isolation (no pollution from host)

  The test copies all PowerShell scripts to a temp directory and runs SafeCheck.ps1
  there, mimicking the environment it would encounter in CI/CD.

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS

  Prerequisites:
    - Pester module (v5.0+)
    - SafeCheck.ps1 script in ../scripts/
    - SafeRun.ps1 script in ../scripts/
    - SafeArchive.ps1 script in ../scripts/
    - TestHelpers.ps1 in same directory
    - Rust canonical safe-run binary must be discoverable

  Test Isolation:
    - Creates unique temporary workspace for each test
    - Cleans environment variables before execution
    - Sets SAFE_RUN_BIN to ensure Rust binary is found
    - Copies all scripts to temp location (no shared state)

  Contract References:
    - M0-P1-I1: safe-run contract (tested by SafeCheck.ps1)
    - M0-P1-I2: Failure artifact contract (tested by SafeCheck.ps1)
    - M0-P1-I3: safe-archive no-clobber contract (tested by SafeCheck.ps1)

  Design Notes:
    - Single test ensures SafeCheck.ps1 works end-to-end
    - Mimics Bash test approach (copies scripts, sets SAFE_RUN_BIN)
    - Validates entire contract verification workflow in one go

.ENVIRONMENT
  None. Tests run in isolated environments.

.EXAMPLE
  # Run SafeCheck tests with Pester
  PS> Invoke-Pester -Path .\SafeCheckTests.ps1

.LINK
  https://pester.dev/

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>
Set-StrictMode -Version Latest

Describe "SafeCheck.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptRoot = Join-Path $PSScriptRoot "..\scripts"
    
    # Find Rust binary for wrapper discovery (like Bash test does)
    # PSScriptRoot is .../wrappers/powershell/tests
    # Repo root is 2 levels up from tests: ../../
    $script:RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    $script:SafeRunBinPath = $null
    
    $binaryName = if ($IsWindows) { "safe-run.exe" } else { "safe-run" }
    $distPath = Join-Path $script:RepoRoot "dist" "$(if ($IsWindows) { 'windows' } elseif ($IsMacOS) { 'macos' } else { 'linux' })" "x86_64" $binaryName
    $devPath = Join-Path $script:RepoRoot "rust" "target" "release" $binaryName
    
    if (Test-Path $distPath) {
      $script:SafeRunBinPath = $distPath
    } elseif (Test-Path $devPath) {
      $script:SafeRunBinPath = $devPath
    } else {
      throw "Rust binary not found for tests. Searched: $distPath, $devPath"
    }
  }
  It "runs its own contract checks successfully in a clean temp workspace" {
    $td = New-TempDir
    Push-Location $td
    try {
      # Clean up any environment pollution from previous tests
      Remove-Item env:SAFE_FAIL_DIR, env:SAFE_ARCHIVE_DIR, env:SAFE_ARCHIVE_COMPRESS, env:SAFE_LOG_DIR, env:SAFE_SNIPPET_LINES, env:SAFE_RUN_VIEW, env:SAFE_RUN_BIN -ErrorAction SilentlyContinue
      
      # Set SAFE_RUN_BIN so wrapper can find binary (like Bash test does)
      $env:SAFE_RUN_BIN = $script:SafeRunBinPath
      
      # Set up directory structure and copy scripts (like bash test does)
      $scriptsDir = Join-Path $td "scripts"
      New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
      New-Item -ItemType Directory -Force -Path ".agent\FAIL-LOGS" | Out-Null
      # Create empty FAIL-ARCHIVE (ensure no leftover files from environment)
      if (Test-Path ".agent\FAIL-ARCHIVE") {
        Remove-Item -Recurse -Force ".agent\FAIL-ARCHIVE"
      }
      New-Item -ItemType Directory -Force -Path ".agent\FAIL-ARCHIVE" | Out-Null
      
      # Copy all PowerShell scripts
      Get-ChildItem -Path $script:ScriptRoot -Filter "*.ps1" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $scriptsDir
      }
      
      # Run SafeCheck.ps1 from the temp directory
      $safeCheckScript = Join-Path $scriptsDir "SafeCheck.ps1"
      & pwsh -NoProfile -File $safeCheckScript
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }
}
