#requires -Version 5.1
Set-StrictMode -Version Latest

Describe "safe-check.ps1" {
  BeforeAll {
    . "$PSScriptRoot/test-helpers.ps1"
    $script:ScriptRoot = Join-Path $PSScriptRoot "..\scripts"
    
    # Find Rust binary for wrapper discovery (like Bash test does)
    # PSScriptRoot is .../RFC-Shared-Agent-Scaffolding-Example/scripts/powershell/tests
    # Repo root is 3 levels up from tests: ../../../
    $script:RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
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
      
      # Run safe-check.ps1 from the temp directory
      $safeCheckScript = Join-Path $scriptsDir "safe-check.ps1"
      & pwsh -NoProfile -File $safeCheckScript
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }
}
