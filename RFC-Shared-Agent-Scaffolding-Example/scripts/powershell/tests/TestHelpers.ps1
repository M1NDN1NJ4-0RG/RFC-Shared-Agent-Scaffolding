Set-StrictMode -Version Latest

function New-TempDir {
  $base = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), 'agent-ops-tests')
  [System.IO.Directory]::CreateDirectory($base) | Out-Null
  $d = [System.IO.Path]::Combine($base, [System.Guid]::NewGuid().ToString('n'))
  [System.IO.Directory]::CreateDirectory($d) | Out-Null
  return $d
}

function Add-FakeGhToPath {
  <#
    Creates a tiny fake 'gh' CLI implementation and prepends it to PATH.

    The fake supports only the subset used by preflight_automerge_ruleset:
      gh api <endpoint> ...

    It prints FixtureJson to stdout regardless of endpoint, so tests can
    control scenarios by swapping fixtures.
  #>
  param(
    [Parameter(Mandatory=$true)][string]$FixtureJson,
    [Parameter(Mandatory=$true)][string]$OutDir
  )

  $shimDir = Join-Path $OutDir 'fake-gh'
  New-Item -ItemType Directory -Force -Path $shimDir | Out-Null

  $psImpl = Join-Path $shimDir 'gh_impl.ps1'
  Set-Content -Encoding UTF8 -Path $psImpl -Value @"
param([Parameter(ValueFromRemainingArguments=`$true)][string[]]`$Args)
Write-Output @'
$FixtureJson
'@
exit 0
"@

  if ($IsWindows) {
    $cmdShim = Join-Path $shimDir 'gh.cmd'
    Set-Content -Encoding ASCII -Path $cmdShim -Value ("@echo off`r`n" +
      "pwsh -NoProfile -ExecutionPolicy Bypass -File `"$psImpl`" %*`r`n")
  } else {
    $shShim = Join-Path $shimDir 'gh'
    Set-Content -Encoding UTF8 -Path $shShim -Value ("#!/usr/bin/env bash`n" +
      "exec pwsh -NoProfile -File `"$psImpl`" `"$@`"`n")
    try { & chmod +x $shShim | Out-Null } catch {}
  }

  $env:PATH = $shimDir + [System.IO.Path]::PathSeparator + $env:PATH
  return $shimDir
}

function Write-RandomTextFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [int]$Lines = 5
  )
  $sb = New-Object System.Text.StringBuilder
  for ($i=1; $i -le $Lines; $i++) {
    [void]$sb.AppendLine("line $i $(Get-Random)")
  }
  Set-Content -Encoding UTF8 -Path $Path -Value $sb.ToString()
}
