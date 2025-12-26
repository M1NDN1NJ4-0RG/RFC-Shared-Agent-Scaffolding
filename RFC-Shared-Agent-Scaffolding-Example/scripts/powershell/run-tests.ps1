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

$res = Invoke-Pester -Configuration $cfg
if ($res.FailedCount -gt 0) { exit 1 }
exit 0
