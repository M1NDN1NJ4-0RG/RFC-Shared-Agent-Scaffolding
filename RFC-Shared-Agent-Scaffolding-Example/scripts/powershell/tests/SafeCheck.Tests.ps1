#requires -Version 5.1
Set-StrictMode -Version Latest

Describe "safe-check.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptRoot = Join-Path $PSScriptRoot "..\scripts\powershell"
  }
  It "runs its own contract checks successfully in a clean temp workspace" {
    $td = New-TempDir
    Push-Location $td
    try {
      # Set up directory structure and copy scripts (like bash test does)
      $scriptsDir = Join-Path $td "scripts\powershell"
      New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
      New-Item -ItemType Directory -Force -Path ".agent\FAIL-LOGS" | Out-Null
      New-Item -ItemType Directory -Force -Path ".agent\FAIL-ARCHIVE" | Out-Null
      
      # Copy all PowerShell scripts
      Get-ChildItem -Path $script:ScriptRoot -Filter "*.ps1" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $scriptsDir
      }
      
      # Run safe-check.ps1 from the temp directory
      $safeCheckScript = Join-Path $scriptsDir "safe-check.ps1"
      & pwsh -NoProfile -File $safeCheckScript
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }
}
