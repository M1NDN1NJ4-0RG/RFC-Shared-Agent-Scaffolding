<#
.SYNOPSIS
  test-helpers.ps1 - Shared test utilities for PowerShell Pester test suites

.DESCRIPTION
  Common helper functions used across multiple Pester test files to reduce
  code duplication and ensure consistent test behavior.

  Exported Functions:
    - New-TempDir: Create isolated temporary directory for test execution
    - Add-FakeGhToPath: Inject fake gh CLI implementation for API testing
    - Write-RandomTextFile: Generate test files with random content

  These helpers support test isolation, fixture generation, and mocking
  of external dependencies (GitHub CLI).

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Cross-platform PATH handling ([System.IO.Path]::PathSeparator)

  Usage:
    This file is dot-sourced by test files:
      . "$PSScriptRoot/test-helpers.ps1"

    Functions are then available in the test scope.

  Design Notes:
    - New-TempDir uses GUID to ensure uniqueness
    - Add-FakeGhToPath creates platform-specific shims (.cmd on Windows, bash on Unix)
    - Write-RandomTextFile uses Get-Random for unique content per call
    - No test framework dependencies (pure PowerShell)

.LINK
  https://pester.dev/
#>
Set-StrictMode -Version Latest

function New-TempDir {
  <#
  .SYNOPSIS
    Create a unique temporary directory for test isolation

  .DESCRIPTION
    Creates a subdirectory under system temp with GUID-based naming to ensure
    each test gets an isolated workspace. Automatically creates parent directory
    (agent-ops-tests) if not present.

  .OUTPUTS
    String: Full path to created temporary directory

  .EXAMPLE
    $td = New-TempDir
    Push-Location $td
    try {
      # Test operations in isolated directory
    } finally {
      Pop-Location
    }

  .NOTES
    - Uses [System.IO.Path]::GetTempPath() for cross-platform temp location
    - Creates agent-ops-tests parent directory for organization
    - Subdirectory named with GUID (no collisions)
    - Caller responsible for cleanup (typically via Pop-Location in finally block)
  #>
  $base = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), 'agent-ops-tests')
  [System.IO.Directory]::CreateDirectory($base) | Out-Null
  $d = [System.IO.Path]::Combine($base, [System.Guid]::NewGuid().ToString('n'))
  [System.IO.Directory]::CreateDirectory($d) | Out-Null
  return $d
}

function Add-FakeGhToPath {
  <#
  .SYNOPSIS
    Create and inject a fake 'gh' CLI implementation for testing

  .DESCRIPTION
    Creates a minimal fake 'gh' CLI that returns predefined JSON fixtures.
    Useful for testing scripts that depend on GitHub CLI without making real API calls.

    The fake gh supports only the subset used by preflight_automerge_ruleset:
      gh api <endpoint> ...

    It ignores endpoint arguments and always returns FixtureJson to stdout.

  .PARAMETER FixtureJson
    JSON string to return when fake gh is invoked.
    Should match expected GitHub API response format.

  .PARAMETER OutDir
    Directory where fake gh shim will be created.
    This directory is prepended to PATH.

  .OUTPUTS
    String: Path to created shim directory (same as OutDir/fake-gh)

  .EXAMPLE
    $fixture = '{"rulesets":[{"id":123,"name":"Main"}]}'
    Add-FakeGhToPath -FixtureJson $fixture -OutDir $tempDir
    # Now 'gh api ...' will return the fixture

  .NOTES
    - Creates platform-specific shim (gh.cmd on Windows, gh bash script on Unix)
    - Prepends shim directory to PATH (shadows real gh if present)
    - Implementation uses pwsh to run a .ps1 that prints the fixture
    - Caller responsible for PATH cleanup (typically via temp dir cleanup)
  #>
  param(
    [Parameter(Mandatory=$true)][string]$FixtureJson,
    [Parameter(Mandatory=$true)][string]$OutDir
  )

  $shimDir = Join-Path $OutDir 'fake-gh'
  New-Item -ItemType Directory -Force -Path $shimDir | Out-Null

  $psImpl = Join-Path $shimDir 'gh_impl.ps1'
  Set-Content -Encoding UTF8 -Path $psImpl -Value @"
param([Parameter(ValueFromRemainingArguments=`$true)][string[]]`$Args)
Write-Output @'
$FixtureJson
'@
exit 0
"@

  if ($IsWindows) {
    $cmdShim = Join-Path $shimDir 'gh.cmd'
    Set-Content -Encoding ASCII -Path $cmdShim -Value ("@echo off`r`n" +
      "pwsh -NoProfile -ExecutionPolicy Bypass -File `"$psImpl`" %*`r`n")
  } else {
    $shShim = Join-Path $shimDir 'gh'
    Set-Content -Encoding UTF8 -Path $shShim -Value ("#!/usr/bin/env bash`n" +
      "exec pwsh -NoProfile -File `"$psImpl`" `"$@`"`n")
    try { & chmod +x $shShim | Out-Null } catch {}
  }

  $env:PATH = $shimDir + [System.IO.Path]::PathSeparator + $env:PATH
  return $shimDir
}

function Write-RandomTextFile {
  <#
  .SYNOPSIS
    Create a text file with random content for testing

  .DESCRIPTION
    Generates a text file with specified number of lines, each containing
    "line N <random-number>". Useful for creating unique test fixtures.

  .PARAMETER Path
    Full path where file will be created.

  .PARAMETER Lines
    Number of lines to generate.
    Default: 5

  .EXAMPLE
    Write-RandomTextFile -Path "test.txt" -Lines 10
    # Creates test.txt with 10 lines of random content

  .NOTES
    - Uses StringBuilder for efficiency
    - Each line includes Get-Random output for uniqueness
    - UTF8 encoding for cross-platform compatibility
  #>
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [int]$Lines = 5
  )
  $sb = New-Object System.Text.StringBuilder
  for ($i=1; $i -le $Lines; $i++) {
    [void]$sb.AppendLine("line $i $(Get-Random)")
  }
  Set-Content -Encoding UTF8 -Path $Path -Value $sb.ToString()
}
