#requires -Version 5.1
Set-StrictMode -Version Latest

Describe "safe-archive.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\safe-archive.ps1"
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
