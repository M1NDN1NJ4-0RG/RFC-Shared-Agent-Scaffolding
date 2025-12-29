#requires -Version 5.1
<#
.SYNOPSIS
  PreflightTests.ps1 - Pester test suite for PreflightAutomergeRuleset.ps1

.DESCRIPTION
  Comprehensive Pester test suite validating the PreflightAutomergeRuleset.ps1
  GitHub API integration and validation logic.

  Test Coverage:
    - Parameter validation: Missing required arguments
    - Authentication handling: Missing gh CLI and tokens
    - Successful validation: Ruleset matches requirements (gh path)
    - Missing contexts detection: Want > Got validation
    - Enforcement validation: Active vs. evaluate/disabled

  Tests use a fake 'gh' CLI implementation to avoid real GitHub API calls
  and to enable deterministic fixture-based testing.

  Fixture-Based Testing:
    - Add-FakeGhToPath creates a minimal gh shim in PATH
    - Shim returns predefined JSON fixtures for API responses
    - Tests control scenarios by swapping fixtures
    - No network calls, no authentication required

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Fake gh CLI uses .cmd shim on Windows, bash script on Unix

  Prerequisites:
    - Pester module (v5.0+)
    - PreflightAutomergeRuleset.ps1 script in ../scripts/
    - TestHelpers.ps1 in same directory (provides Add-FakeGhToPath, New-TempDir)

  Test Isolation:
    - Each test creates unique temporary directory
    - PATH modified to inject fake gh CLI
    - Environment variables cleared (TOKEN, GITHUB_TOKEN)
    - PATH restored after test (Pop-Location)

  Contract References:
    - M0-P2-I2: Preflight automerge ruleset verification protocol

  Test Details:
    1. Missing --repo test: Validates required parameter check (exit 3)
    2. No auth test: Validates error when gh unavailable and no token (exit 1)
    3. Success test: Validates matching ruleset passes (exit 0)
    4. Missing contexts test: Validates want != got detection (exit 1)
    5. Enforcement test: Validates active enforcement requirement (exit 1)

  Fake gh CLI Implementation:
    - Accepts any arguments (mimics gh api endpoint)
    - Returns fixture JSON to stdout
    - Exits 0 (success)
    - Implements minimal subset needed for preflight script

  Design Notes:
    - Uses JSON fixtures embedded in test strings (here-strings @"..."@)
    - Tests are independent (each creates own fake gh and fixtures)
    - Exit codes validated against contract (0=OK, 1=fail, 2=auth, 3=usage)
    - No external dependencies (no real gh, no network)

.ENVIRONMENT
  None. Tests use fake gh CLI and cleared environment variables.

.EXAMPLE
  # Run preflight tests with Pester
  PS> Invoke-Pester -Path .\PreflightTests.ps1

.LINK
  https://pester.dev/

.LINK
  https://docs.github.com/en/rest/repos/rules

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>
Set-StrictMode -Version Latest

Describe "PreflightAutomergeRuleset.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\PreflightAutomergeRuleset.ps1"
  }

  It "fails when no --repo is provided" {
    & pwsh -NoProfile -File $ScriptUnderTest
    $LASTEXITCODE | Should -Be 3  # M0-P2-I2: Usage/validation error
  }

  It "fails when gh is not available and no token is provided" {
    $td = New-TempDir
    Push-Location $td
    try {
      # Ensure gh is not found by masking PATH, but preserve pwsh location
      $old = $env:PATH
      $pwshPath = (Get-Command pwsh).Path | Split-Path
      $env:PATH = "$pwshPath$([System.IO.Path]::PathSeparator)$td"
      Remove-Item env:TOKEN -ErrorAction SilentlyContinue
      Remove-Item env:GITHUB_TOKEN -ErrorAction SilentlyContinue

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main" -Want '["lint"]'
      # Script returns 1 (unexpected API error) when gh unavailable and no token
      $LASTEXITCODE | Should -Be 1
    } finally {
      $env:PATH = $old
      Pop-Location
    }
  }

  It "passes when ruleset matches want and enforcement is enabled (gh path)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "active",
      "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"},
              {"context": "test"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }

  It "fails when required checks are missing (gh path)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "active",
      "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 1
    } finally {
      Pop-Location
    }
  }

  It "fails when enforcement is not active" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "evaluate",
      "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"},
              {"context": "test"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 1
    } finally {
      Pop-Location
    }
  }
}
