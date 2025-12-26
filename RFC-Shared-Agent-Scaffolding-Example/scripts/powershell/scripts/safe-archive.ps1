#!/usr/bin/env pwsh
<#
.SYNOPSIS
  safe-archive.ps1 - Non-destructively archive failure logs from .agent/FAIL-LOGS to .agent/FAIL-ARCHIVE (no-clobber).

.ENVIRONMENT
  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)
  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)
  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)

.NOTES
  - Never deletes. Uses move semantics but will not overwrite an existing destination.
  - gzip uses built-in compression; xz/zstd require external commands.
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
  Write-Err "Usage: scripts/safe-archive.ps1 [--all | <file> ...]"
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
