#requires -Version 5.1
Set-StrictMode -Version Latest

. "$PSScriptRoot/TestHelpers.ps1"

$ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\powershell\safe-run.ps1"

Describe "safe-run.ps1" {

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

      $files = Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-fail.txt"
      $files.Count | Should -Be 1

      $txt = Get-Content -LiteralPath $files[0].FullName -Raw
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
      $psi.Arguments = "-NoProfile -File `"$ScriptUnderTest`" -- pwsh -NoProfile -Command `"1..10 | ForEach-Object { Write-Output ('L' + $_) }; exit 2`""
      $psi.RedirectStandardError = $true
      $psi.RedirectStandardOutput = $true
      $psi.UseShellExecute = $false
      $p = [System.Diagnostics.Process]::Start($psi)
      $stdout = $p.StandardOutput.ReadToEnd()
      $stderr = $p.StandardError.ReadToEnd()
      $p.WaitForExit()

      $p.ExitCode | Should -Be 2
      $stderr | Should -Match "Tail of captured output"
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

      $files = Get-ChildItem -LiteralPath $env:SAFE_LOG_DIR -Filter "*-fail.txt"
      $files.Count | Should -Be 1
      ($files[0].Length -gt 1000000) | Should -BeTrue
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
}
