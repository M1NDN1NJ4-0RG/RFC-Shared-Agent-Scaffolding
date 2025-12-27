<#
.SYNOPSIS
  run-tests.ps1 - PowerShell test runner for safe-run/safe-archive/preflight wrappers

.DESCRIPTION
  Executes all Pester test files in the tests/ directory using Pester v5+
  configuration. Discovers and runs test files matching *-tests.ps1 pattern.

  Purpose:
    - Provide consistent test execution environment
    - Configure Pester for kebab-case test file naming convention
    - Set SAFE_RUN_BIN for wrapper tests (points to Rust canonical binary)
    - Report test results with detailed verbosity
    - Exit with non-zero code on test failures (CI/CD compatible)

  Test Discovery:
    Pester's default discovery pattern is *.Tests.ps1 (PascalCase).
    This runner explicitly discovers *-tests.ps1 (kebab-case) files
    and passes them to Pester.

  Environment Setup:
    - Detects repository root (3 levels up from PowerShell directory)
    - Searches for Rust safe-run binary in standard locations:
      - rust/target/release/safe-run[.exe] (dev mode)
      - dist/<os>/<arch>/safe-run[.exe] (CI artifacts)
    - Sets SAFE_RUN_BIN if binary found (enables wrapper tests)

.OUTPUTS
  Exit codes:
    0   All tests passed
    1   One or more tests failed
    2   Prerequisites not met (pwsh or Pester not found, no test files)

  Test results are printed to stdout with Pester's 'Detailed' verbosity.

.EXAMPLE
  # Run all tests
  PS> .\run-tests.ps1
  Agent Ops PowerShell test runner
  Root: /path/to/powershell
  # Pester output follows...

.EXAMPLE
  # Run from CI/CD
  PS> pwsh -NoProfile -File run-tests.ps1
  # Exit code signals pass/fail

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported (limited to Windows)
    - PowerShell 7+ (pwsh): Required for cross-platform execution

  Prerequisites:
    - pwsh (PowerShell 7+) must be in PATH
    - Pester module must be installed (any discoverable version, v5+ recommended)
    - Rust canonical safe-run binary should be built (tests will fail without it)

  Installation:
    If Pester is not installed, the script prints installation instructions:
      pwsh -NoProfile -Command "Install-Module Pester -Scope CurrentUser"

  Test File Discovery:
    - Searches tests/ directory for *-tests.ps1 files
    - Explicitly passes file list to Pester (overrides default discovery)
    - Exits with error if no test files found

  Pester Configuration:
    - Run.PassThru = true (return test results for exit code determination)
    - Output.Verbosity = 'Detailed' (show test names and results)
    - Run.Path = explicit file list (override default *.Tests.ps1 pattern)

  Side Effects:
    - Sets SAFE_RUN_BIN environment variable (if Rust binary found)
    - Modifies working directory context (Push-Location/Pop-Location in tests)
    - Creates temporary test directories (cleaned up by tests)

  Design Notes:
    - Fails fast if prerequisites missing (pwsh, Pester)
    - Provides clear error messages with actionable remediation
    - No silent fallbacks (offline-safe, won't auto-install Pester)
    - Exit code strictly follows convention (0=pass, 1=fail, 2=error)

.LINK
  https://pester.dev/

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Run from repo root of this bundle.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = $here  # The powershell directory is the bundle root

# For thin wrapper tests: point to Rust canonical binary
$repoRoot = Resolve-Path (Join-Path $root "..\..\..") -ErrorAction SilentlyContinue
if ($repoRoot) {
    $rustBinary = Join-Path $repoRoot "rust" "target" "release" "safe-run"
    if (Test-Path $rustBinary) {
        $env:SAFE_RUN_BIN = $rustBinary
    }
}

Write-Host "Agent Ops PowerShell test runner"
Write-Host "Root: $root"

if (-not (Get-Command pwsh -ErrorAction SilentlyContinue)) {
  Write-Error "pwsh not found on PATH. Install PowerShell 7+."
  exit 2
}

# Prefer Pester v5+, but don't auto-install (offline-safe).
if (-not (Get-Module -ListAvailable -Name Pester)) {
  Write-Host ""
  Write-Host "Pester module not found." -ForegroundColor Yellow
  Write-Host "Install it, then re-run:" -ForegroundColor Yellow
  Write-Host "  pwsh -NoProfile -Command \"Install-Module Pester -Scope CurrentUser\"" -ForegroundColor Yellow
  Write-Host ""
  exit 2
}

Import-Module Pester -ErrorAction Stop

$tests = Join-Path $root "tests"
$cfg = New-PesterConfiguration
$cfg.Run.PassThru = $true
$cfg.Output.Verbosity = 'Detailed'
# Work around Pester's default discovery pattern (*.Tests.ps1, PascalCase).
$cfg.Filter.Tag = $null
$cfg.Filter.ExcludeTag = $null
# Our tests use kebab-case (*-tests.ps1), which Pester will NOT auto-discover
# when only Run.Path is set to a directory, so we explicitly resolve the files.
$testFiles = Get-ChildItem -Path $tests -Filter "*-tests.ps1" -File
if ($testFiles.Count -eq 0) {
  Write-Error "No test files found matching *-tests.ps1 in $tests"
  exit 2
}
$cfg.Run.Path = $testFiles.FullName

$res = Invoke-Pester -Configuration $cfg
if ($res.FailedCount -gt 0) { exit 1 }
exit 0
