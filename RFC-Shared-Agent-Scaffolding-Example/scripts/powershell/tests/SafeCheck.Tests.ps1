#requires -Version 5.1
Set-StrictMode -Version Latest

. "$PSScriptRoot/TestHelpers.ps1"

$ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\powershell\safe-check.ps1"

Describe "safe-check.ps1" {
  It "runs its own contract checks successfully in a clean temp workspace" {
    $td = New-TempDir
    Push-Location $td
    try {
      & pwsh -NoProfile -File $ScriptUnderTest
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }
}
