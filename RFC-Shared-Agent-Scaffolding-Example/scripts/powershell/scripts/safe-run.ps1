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
    # This matches the behavior of bash/perl/python3 wrappers
    # which walk up from the script's directory, not the working directory
    
    # Get the script's directory (resolves symlinks)
    $scriptPath = if ($PSCommandPath) {
        # PS 3.0+
        $PSCommandPath
    } else {
        # PS 2.0 fallback
        $MyInvocation.MyCommand.Path
    }
    
    if (-not $scriptPath) {
        # Unable to determine script location, fall back to working directory
        $current = (Get-Location).Path
    } else {
        $current = Split-Path -Parent (Resolve-Path $scriptPath).Path
    }
    
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
    # Note: $IsLinux, $IsMacOS, $IsWindows are only available in PowerShell 6.0+
    # For PowerShell 5.1 (Windows-only), we assume Windows
    $os = "unknown"
    
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell 6.0+ (Core) - cross-platform
        if ($IsLinux) { $os = "linux" }
        elseif ($IsMacOS) { $os = "macos" }
        elseif ($IsWindows) { $os = "windows" }
    } else {
        # PowerShell 5.1 and earlier - Windows only
        $os = "windows"
    }
    
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

# Verify binary exists before attempting to invoke it
# This provides better error handling than relying on exception
if (-not (Test-Path $binary)) {
    Write-Err "ERROR: Binary not found at path: $binary"
    Write-Err ""
    Write-Err "This may indicate:"
    Write-Err "  - SAFE_RUN_BIN points to a non-existent file"
    Write-Err "  - The Rust binary has not been built yet"
    Write-Err "  - The binary was deleted after discovery"
    Write-Err ""
    Write-Err "To install:"
    Write-Err "  1. Clone the repository"
    Write-Err "  2. cd rust/"
    Write-Err "  3. cargo build --release"
    Write-Err ""
    Write-Err "Or download a pre-built binary from:"
    Write-Err "  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases"
    exit 127
}

# Invoke the Rust canonical tool with all arguments passed through
# The 'run' subcommand is required by the Rust CLI structure
try {
    & $binary run @invokeArgs
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        # If LASTEXITCODE is null, the command may have failed to execute
        # This shouldn't happen if binary exists, but handle defensively
        Write-Err "WARNING: Unable to determine exit code from binary execution"
        exit 1
    }
    exit $exitCode
} catch {
    Write-Err "ERROR: Failed to execute binary: $binary"
    Write-Err "Error: $_"
    Write-Err ""
    Write-Err "This may be a permissions issue or the binary is corrupted."
    Write-Err "Try:"
    Write-Err "  1. Verify the binary is executable"
    Write-Err "  2. Check file permissions"
    Write-Err "  3. Rebuild: cd rust/ && cargo build --release"
    exit 127
}
