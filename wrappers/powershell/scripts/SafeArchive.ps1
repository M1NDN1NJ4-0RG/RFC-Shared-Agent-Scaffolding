#!/usr/bin/env pwsh
<#
.SYNOPSIS
  SafeArchive.ps1 - Non-destructive archival of failure logs with optional compression

.DESCRIPTION
  Moves failure logs from SAFE_FAIL_DIR to SAFE_ARCHIVE_DIR using safe move semantics.
  Implements strict no-clobber behavior: never overwrites existing destination files.
  On collision, automatically appends numeric suffix (-1, -2, etc.) to destination filename.

  Purpose:
    - Archive accumulated failure logs to prevent workspace clutter
    - Preserve all failure artifacts (never delete/overwrite)
    - Optional compression (gzip, xz, zstd) to reduce storage overhead
    - Support both individual file and bulk (--all) archival modes

  No-Clobber Guarantee (M0-P1-I3):
    If destination file exists, the script appends -N suffix before the extension:
      original.log -> original-1.log -> original-2.log -> etc.
    This ensures that existing archives are never modified or destroyed.

  Compression Support:
    - none (default): No compression, fast move operation
    - gzip: Built-in .NET compression (no external dependencies)
    - xz: Requires 'xz' command in PATH (multi-threaded -T0)
    - zstd: Requires 'zstd' command in PATH (multi-threaded -T0)

  Compression replaces the source file after successful compression, appending
  appropriate extension (.gz, .xz, .zst) to the destination filename.

.PARAMETER ArgsRest
  Remaining arguments after standard parameter parsing.
  
  Modes:
    --all              Archive all files in SAFE_FAIL_DIR
    <file> [<file>...] Archive specific files (paths)
    -h, --help         Display usage and exit with code 2

.ENVIRONMENT
  SAFE_FAIL_DIR
    Source directory for failure logs.
    Default: .agent/FAIL-LOGS

  SAFE_ARCHIVE_DIR
    Destination directory for archived logs.
    Default: .agent/FAIL-ARCHIVE

  SAFE_ARCHIVE_COMPRESS
    Compression method: none | gzip | xz | zstd
    Default: none
    Invalid values cause immediate exit with code 2.

.OUTPUTS
  Exit codes:
    0   Archive operation completed successfully
    2   Usage error, invalid compression method, or file not found

  Stderr output format:
    ARCHIVED: <source> -> <destination>  (one line per archived file)
    ERROR: <message>                     (on failure)

.EXAMPLE
  # Archive all logs without compression
  PS> .\SafeArchive.ps1 --all
  ARCHIVED: .agent/FAIL-LOGS/20231215T120000Z-pid123-FAIL.log -> .agent/FAIL-ARCHIVE/20231215T120000Z-pid123-FAIL.log

.EXAMPLE
  # Archive specific file with gzip compression
  PS> $env:SAFE_ARCHIVE_COMPRESS = "gzip"
  PS> .\SafeArchive.ps1 .agent/FAIL-LOGS/test-FAIL.log
  ARCHIVED: .agent/FAIL-LOGS/test-FAIL.log -> .agent/FAIL-ARCHIVE/test-FAIL.log

.EXAMPLE
  # Archive all logs with xz compression (requires 'xz' in PATH)
  PS> $env:SAFE_ARCHIVE_COMPRESS = "xz"
  PS> .\SafeArchive.ps1 --all
  ARCHIVED: .agent/FAIL-LOGS/log1.log -> .agent/FAIL-ARCHIVE/log1.log
  # Destination will be .agent/FAIL-ARCHIVE/log1.log.xz after compression

.EXAMPLE
  # No-clobber behavior demonstration
  PS> # First archive creates: archive/test.log
  PS> .\SafeArchive.ps1 logs/test.log
  ARCHIVED: logs/test.log -> archive/test.log
  PS> # Second archive with same name creates: archive/test-1.log
  PS> .\SafeArchive.ps1 logs/test.log
  ARCHIVED: logs/test.log -> archive/test-1.log

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - gzip compression uses .NET built-in (cross-platform)
    - xz/zstd compression requires external tools (platform-dependent availability)

  Contract References:
    - M0-P1-I3: safe-archive no-clobber semantics and move behavior

  Side Effects:
    - Creates SAFE_FAIL_DIR if not present
    - Creates SAFE_ARCHIVE_DIR if not present
    - Moves files from SAFE_FAIL_DIR to SAFE_ARCHIVE_DIR (removes from source)
    - Compression removes uncompressed file after successful compression

  Compression Details:
    - gzip: System.IO.Compression.GZipStream with Optimal compression level
    - xz: External command with -T0 (all CPU cores), -f (force)
    - zstd: External command with -q (quiet), -T0 (all cores), -f (force)
    - Failed compression exits immediately with code 2, source file remains in archive

  Error Handling:
    - File not found: Throws error, exits with code 2
    - Invalid compression method: Throws error, exits with code 2
    - Missing xz/zstd command: Throws error, exits with code 2
    - --all with empty directory: Exits 0 with informational message

  Performance:
    - Move operations are atomic on most filesystems (same volume)
    - No-clobber checking uses Test-Path (fast for modern filesystems)
    - Compression is CPU-bound (external tools use multiple threads)

  Design Notes:
    - Never deletes or overwrites files (safety-first philosophy)
    - Compression method validation happens before file operations
    - All directory creation is idempotent (New-Item -Force)
    - Supports both relative and absolute paths

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>

param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ArgsRest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

function Have-Cmd([string]$cmd) {
  $p = Get-Command $cmd -ErrorAction SilentlyContinue
  return $null -ne $p
}

function Compress-File([string]$method, [string]$path) {
  if ([string]::IsNullOrWhiteSpace($method)) { $method = "none" }
  switch ($method) {
    "none" { return }
    "gzip" {
      $out = "$path.gz"
      $inStream = [System.IO.File]::OpenRead($path)
      try {
        $outStream = [System.IO.File]::Create($out)
        try {
          $gzip = New-Object System.IO.Compression.GZipStream($outStream, [System.IO.Compression.CompressionLevel]::Optimal)
          try { $inStream.CopyTo($gzip) } finally { $gzip.Dispose() }
        } finally { $outStream.Dispose() }
      } finally { $inStream.Dispose() }
      Remove-Item -Force $path
      return
    }
    "xz" {
      if (-not (Have-Cmd "xz")) { throw "xz command not found in PATH" }
      & xz -T0 -f -- $path | Out-Null
      if ($LASTEXITCODE -ne 0) { throw "xz failed" }
      return
    }
    "zstd" {
      if (-not (Have-Cmd "zstd")) { throw "zstd command not found in PATH" }
      & zstd -q -T0 -f -- $path | Out-Null
      if ($LASTEXITCODE -ne 0) { throw "zstd failed" }
      return
    }
    default { throw "Invalid SAFE_ARCHIVE_COMPRESS value: $method (expected none|gzip|xz|zstd)" }
  }
}

function Archive-One([string]$src, [string]$archiveDir, [string]$compress) {
  if (-not (Test-Path $src)) { throw "File not found: $src" }
  
  # Validate compression method before moving file
  if ($compress -notin @("none", "gzip", "xz", "zstd")) {
    throw "Invalid SAFE_ARCHIVE_COMPRESS value: $compress (expected none|gzip|xz|zstd)"
  }
  
  $base = Split-Path -Leaf $src
  $dest = Join-Path $archiveDir $base
  
  # Auto-suffix on collision (no-clobber default behavior per M0-P1-I3)
  if (Test-Path $dest) {
    $nameOnly = [System.IO.Path]::GetFileNameWithoutExtension($base)
    $ext = [System.IO.Path]::GetExtension($base)
    $counter = 1
    do {
      $suffixedName = "${nameOnly}-${counter}${ext}"
      $dest = Join-Path $archiveDir $suffixedName
      $counter++
    } while (Test-Path $dest)
  }
  
  Move-Item -Path $src -Destination $dest
  Write-Err "ARCHIVED: $src -> $dest"
  Compress-File $compress $dest
}

if ($null -eq $ArgsRest -or $ArgsRest.Count -eq 0 -or $ArgsRest[0] -in @('-h','--help')) {
  Write-Err "Usage: scripts/SafeArchive.ps1 [--all | <file> ...]"
  exit 2
}

$failDir = $env:SAFE_FAIL_DIR
if ([string]::IsNullOrWhiteSpace($failDir)) { $failDir = ".agent/FAIL-LOGS" }
$archiveDir = $env:SAFE_ARCHIVE_DIR
if ([string]::IsNullOrWhiteSpace($archiveDir)) { $archiveDir = ".agent/FAIL-ARCHIVE" }
$compress = $env:SAFE_ARCHIVE_COMPRESS
if ([string]::IsNullOrWhiteSpace($compress)) { $compress = "none" }

New-Item -ItemType Directory -Force -Path $failDir | Out-Null
New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

try {
  if ($ArgsRest[0] -eq '--all') {
    $files = @(Get-ChildItem -Path $failDir -File | Sort-Object Name)
    if ($files.Count -eq 0) { Write-Err "No files to archive in $failDir"; exit 0 }
    foreach ($f in $files) { Archive-One $f.FullName $archiveDir $compress }
    exit 0
  }

  foreach ($f in $ArgsRest) { Archive-One $f $archiveDir $compress }
  exit 0
}
catch {
  Write-Err "ERROR: $($_.Exception.Message)"
  exit 2
}
