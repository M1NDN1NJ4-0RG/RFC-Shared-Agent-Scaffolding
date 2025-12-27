#!/usr/bin/env pwsh
<#
.SYNOPSIS
  safe-run.ps1 - Thin invoker for Rust canonical safe-run tool

.DESCRIPTION
  This wrapper discovers and invokes the Rust canonical implementation.
  It does NOT reimplement any contract logic.

  Binary Discovery Order (per docs/wrapper-discovery.md):
    1. SAFE_RUN_BIN env var (if set)
    2. ./rust/target/release/safe-run (dev mode, relative to repo root)
    3. ./dist/<os>/<arch>/safe-run (CI artifacts)
    4. PATH lookup (system installation)
    5. Error with actionable instructions (exit 127)
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

function Find-RepoRoot {
    # Walk up from script location to find repository root
    $scriptPath = $PSCommandPath
    $current = Split-Path -Parent $scriptPath
    
    while ($current) {
        $rfcFile = Join-Path $current "RFC-Shared-Agent-Scaffolding-v0.1.0.md"
        $gitDir = Join-Path $current ".git"
        
        if ((Test-Path $rfcFile) -or (Test-Path $gitDir)) {
            return $current
        }
        
        $parent = Split-Path -Parent $current
        if (-not $parent -or $parent -eq $current) { break }
        $current = $parent
    }
    
    return $null
}

function Detect-Platform {
    # Detect OS
    $os = if ($IsLinux) { "linux" }
          elseif ($IsMacOS) { "macos" }
          elseif ($IsWindows) { "windows" }
          else { "unknown" }
    
    # Detect architecture
    $arch = switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture) {
        'X64' { 'x86_64' }
        'Arm64' { 'aarch64' }
        default { 'unknown' }
    }
    
    return "$os/$arch"
}

function Find-SafeRunBinary {
    # 1. Environment override
    if ($env:SAFE_RUN_BIN) {
        return $env:SAFE_RUN_BIN
    }
    
    $repoRoot = Find-RepoRoot
    
    # Determine binary name with platform-specific extension
    $binaryName = if ($IsWindows) { "safe-run.exe" } else { "safe-run" }
    
    # 2. Dev mode: ./rust/target/release/safe-run[.exe]
    if ($repoRoot) {
        $devBin = Join-Path $repoRoot "rust" "target" "release" $binaryName
        if (Test-Path $devBin) {
            return $devBin
        }
    }
    
    # 3. CI artifact: ./dist/<os>/<arch>/safe-run[.exe]
    if ($repoRoot) {
        $platform = Detect-Platform
        if ($platform -ne "unknown/unknown") {
            $parts = $platform -split '/'
            $ciBin = Join-Path $repoRoot "dist" $parts[0] $parts[1] $binaryName
            if (Test-Path $ciBin) {
                return $ciBin
            }
        }
    }
    
    # 4. PATH lookup
    $whichResult = Get-Command "safe-run" -ErrorAction SilentlyContinue
    if ($whichResult) {
        return $whichResult.Source
    }
    
    # 5. Not found
    return $null
}

# Main execution
$binary = Find-SafeRunBinary

if (-not $binary) {
    Write-Err @"
ERROR: Rust canonical tool not found.

Searched locations:
  1. SAFE_RUN_BIN env var (not set or invalid)
  2. ./rust/target/release/safe-run[.exe] (not found)
  3. ./dist/<os>/<arch>/safe-run[.exe] (not found)
  4. PATH lookup (not found)

To install:
  1. Clone the repository
  2. cd rust/
  3. cargo build --release

Or download a pre-built binary from:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases

For more information, see:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/rust-canonical-tool.md
"@
    exit 127
}

# Parse arguments: handle optional "--" separator
$invokeArgs = @($args)
if ($invokeArgs.Count -gt 0 -and $invokeArgs[0] -eq '--') {
    $invokeArgs = $invokeArgs[1..($invokeArgs.Count-1)]
}

# Invoke the Rust canonical tool with all arguments passed through
# The 'run' subcommand is required by the Rust CLI structure
try {
    & $binary run @invokeArgs
    exit $LASTEXITCODE
} catch {
    Write-Err "ERROR: Failed to execute binary: $binary"
    Write-Err "Error: $_"
    Write-Err ""
    Write-Err "Searched locations:"
    Write-Err "  1. SAFE_RUN_BIN env var"
    Write-Err "  2. ./rust/target/release/safe-run[.exe]"
    Write-Err "  3. ./dist/<os>/<arch>/safe-run[.exe]"
    Write-Err "  4. PATH lookup"
    exit 127
}
