Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Run from repo root of this bundle.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = $here  # The powershell directory is the bundle root

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
$cfg.Run.Path = $tests
$cfg.Run.PassThru = $true
$cfg.Output.Verbosity = 'Detailed'
# Use kebab-case test file pattern instead of default *.Tests.ps1
$cfg.Filter.Tag = $null
$cfg.Filter.ExcludeTag = $null
# Pester 5 auto-discovers *-tests.ps1 files when Path is a directory
# We need to explicitly set the test files since we use kebab-case
$testFiles = Get-ChildItem -Path $tests -Filter "*-tests.ps1" -File
if ($testFiles.Count -eq 0) {
  Write-Error "No test files found matching *-tests.ps1 in $tests"
  exit 2
}
$cfg.Run.Path = $testFiles.FullName

$res = Invoke-Pester -Configuration $cfg
if ($res.FailedCount -gt 0) { exit 1 }
exit 0
