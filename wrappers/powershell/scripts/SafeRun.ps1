#!/usr/bin/env pwsh
<#
.SYNOPSIS
  SafeRun.ps1 - PowerShell wrapper for Rust canonical safe-run tool

.DESCRIPTION
  Thin invoker that discovers and delegates to the Rust canonical safe-run implementation.
  This wrapper does NOT reimplement any contract logic; all behavior is defined by the
  Rust binary per RFC-Shared-Agent-Scaffolding-v0.1.0.md (M0-P1-I1, M0-P1-I2).

  Purpose:
    - Discover the Rust canonical safe-run binary using standardized search order
    - Pass through all arguments and environment variables unchanged
    - Preserve exit codes from the canonical tool
    - Provide actionable error messages if the binary is not found

  Binary Discovery Order (per docs/wrapper-discovery.md):
    1. SAFE_RUN_BIN environment variable (if set and valid)
    2. ./rust/target/release/safe-run[.exe] (dev mode, relative to repo root)
    3. ./dist/<os>/<arch>/safe-run[.exe] (CI artifacts)
    4. PATH lookup (system installation)
    5. Error with installation instructions (exit 127)

  The wrapper walks up from its own script directory to find the repository root
  (identified by RFC-Shared-Agent-Scaffolding-v0.1.0.md or .git), ensuring consistent
  behavior regardless of working directory.

.PARAMETER args
  All arguments are passed through to the Rust canonical tool via the 'run' subcommand.
  An optional leading '--' separator is stripped if present (common shell convention).

  Examples:
    SafeRun.ps1 -- pwsh -Command "Write-Output 'test'"
    SafeRun.ps1 pwsh -Command "Write-Output 'test'"  # Also valid

.ENVIRONMENT
  SAFE_RUN_BIN
    Override binary discovery. If set, this path is used directly without fallback search.
    Useful for testing specific builds or custom installations.

  SAFE_LOG_DIR
    Passed through to the Rust tool. Specifies where failure logs are written.
    Default: .agent/FAIL-LOGS (relative to working directory)
    Contract: M0-P1-I2

  SAFE_SNIPPET_LINES
    Passed through to the Rust tool. Number of tail lines to print to stderr on failure.
    Default: 0 (no snippet)
    Set to positive integer (e.g., 10) to enable tail output on stderr.
    The snippet is printed after "command failed ... log:" line for quick diagnosis.
    Full output is always in the log file.
    Note: Extremely large values may produce noisy stderr.
    Contract: M0-P1-I2

  SAFE_RUN_VIEW
    Passed through to the Rust tool. Output view format for failure logs.
    Values: split (default) | merged
    - split: Separate stdout/stderr sections
    - merged: Interleaved output in observed order with sequence markers
    Contract: M0-P1-I1

.OUTPUTS
  Exit code from the Rust canonical tool is preserved via $LASTEXITCODE.
  
  Exit codes:
    0       Command succeeded (no failure artifact created)
    1-126   Command failed (failure artifact created in SAFE_LOG_DIR)
    127     Rust binary not found (see error message for installation instructions)
    
  $LASTEXITCODE is explicitly propagated to ensure correct exit status for CI/CD pipelines.

.EXAMPLE
  # Run a command that succeeds
  PS> .\SafeRun.ps1 -- pwsh -Command "Write-Output 'hello'"
  hello
  PS> $LASTEXITCODE
  0

.EXAMPLE
  # Run a command that fails (creates failure log)
  PS> $env:SAFE_LOG_DIR = ".agent/FAIL-LOGS"
  PS> $env:SAFE_SNIPPET_LINES = "5"
  PS> .\SafeRun.ps1 -- pwsh -Command "Write-Error 'boom'; exit 42"
  # Stderr will show last 5 lines of output
  # Failure log created: .agent/FAIL-LOGS/20231215T143022Z-pid1234-FAIL.log
  PS> $LASTEXITCODE
  42

.EXAMPLE
  # Use custom binary location
  PS> $env:SAFE_RUN_BIN = "/opt/custom/safe-run"
  PS> .\SafeRun.ps1 -- echo "test"

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported (Windows-only features)
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Platform detection uses $IsWindows/$IsLinux/$IsMacOS (pwsh 6+) or assumes Windows (5.1)
    - Binary name automatically adjusted (.exe suffix on Windows)

  Contract References:
    - M0-P1-I1: safe-run split stdout/stderr format with event ledger
    - M0-P1-I2: Failure artifact naming and metadata
    - M0-P3: Wrapper discovery protocol (docs/wrapper-discovery.md)

  Side Effects:
    - None from wrapper itself
    - Rust canonical tool creates failure logs in SAFE_LOG_DIR on command failure
    - Failure logs are ISO8601-timestamped: YYYYMMDDTHHMMSSZ-pidNNN-FAIL.log

  Error Handling:
    - Binary not found: Exit 127 with actionable error message
    - Binary exists but can't execute: Exit 127 with diagnostic guidance
    - LASTEXITCODE propagation: Wrapper explicitly checks and propagates $LASTEXITCODE

  Performance:
    - Discovery overhead: Negligible (file system checks only)
    - No process spawning until Rust binary is invoked
    - No output buffering or transformation (direct passthrough)

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/wrapper-discovery.md

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
.SYNOPSIS
Writes an error message to stderr.
.PARAMETER Msg
The error message to write.
#>
function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

<#
.SYNOPSIS
Finds the repository root by walking up the directory tree.
.OUTPUTS
String path to the repository root directory.
#>
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
    $errorMessage = $_.Exception.Message
    
    # Check if the error is due to access denied / permission issues
    if ($errorMessage -match "Access.*denied|UnauthorizedAccess|permission") {
        Write-Err "ERROR: Permission denied executing binary: $binary"
        Write-Err "Error: $errorMessage"
        Write-Err ""
        Write-Err "Try:"
        Write-Err "  1. Check file permissions"
        Write-Err "  2. Run PowerShell as Administrator (if needed)"
        Write-Err "  3. Verify antivirus isn't blocking execution"
        exit 126
    } else {
        Write-Err "ERROR: Failed to execute binary: $binary"
        Write-Err "Error: $errorMessage"
        Write-Err ""
        Write-Err "This may indicate the binary is corrupted or incompatible."
        Write-Err "Try:"
        Write-Err "  1. Verify the binary is executable"
        Write-Err "  2. Rebuild: cd rust/ && cargo build --release"
        exit 127
    }
}
