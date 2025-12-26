#!/usr/bin/env pwsh
<#
.SYNOPSIS
  preflight_automerge_ruleset.ps1 - Verify GitHub ruleset required CI contexts on default branch.
.DESCRIPTION
  Exit codes:
    0  OK
    1  Precheck failed
    2  Auth/permission error (stop and ask human to fix)
    3  Usage/validation error
.SECURITY
  Never prints token values.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Write-Err([string]$Msg) { [Console]::Error.WriteLine($Msg) }

param(
  [Parameter(Mandatory=$false)][string]$Repo,
  [Parameter(Mandatory=$false)][string]$RulesetId,
  [Parameter(Mandatory=$false)][string]$RulesetName,
  [Parameter(Mandatory=$false)][string]$Want,
  [Parameter(Mandatory=$false)][string]$ApiVersion = "2022-11-28"
)

function Usage {
  Write-Err "Usage:"
  Write-Err "  scripts/powershell/preflight_automerge_ruleset.ps1 -Repo OWNER/REPO (-RulesetId ID | -RulesetName NAME) -Want '[\"lint\",\"test\"]'"
  exit 3
}

function Have-Cmd([string]$cmd) { return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }

function Classify-Auth($obj) {
  if ($null -eq $obj) { return $false }
  $msg = $obj.message
  if ([string]::IsNullOrWhiteSpace($msg)) { return $false }
  return $msg -match '(?i)(Bad credentials|Requires authentication|Resource not accessible|Forbidden|Must have admin rights|Not Found)'
}

function Gh-Api([string]$endpoint) {
  try {
    $out = & gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: $ApiVersion" $endpoint 2>$null
    return $out
  } catch { return $null }
}

function Http-Get([string]$url) {
  $token = $env:TOKEN
  if ([string]::IsNullOrWhiteSpace($token)) { $token = $env:GITHUB_TOKEN }
  if ([string]::IsNullOrWhiteSpace($token)) { throw "No auth available: set TOKEN/GITHUB_TOKEN or authenticate with gh" }

  $headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "token $token"
    "X-GitHub-Api-Version" = $ApiVersion
    "User-Agent" = "agent-ops-preflight"
  }
  try {
    $resp = Invoke-RestMethod -Method Get -Uri $url -Headers $headers -ErrorAction Stop
    return @{ status = 200; body = $resp }
  } catch {
    $err = $_.Exception.Response
    if ($null -ne $err) {
      try {
        $reader = New-Object System.IO.StreamReader($err.GetResponseStream())
        $text = $reader.ReadToEnd()
        $obj = $null
        try { $obj = $text | ConvertFrom-Json } catch { $obj = @{ message = $text } }
        return @{ status = [int]$err.StatusCode; body = $obj }
      } catch {
        return @{ status = 500; body = @{ message = "Request failed" } }
      }
    }
    return @{ status = 500; body = @{ message = "Request failed" } }
  }
}

if ([string]::IsNullOrWhiteSpace($Repo) -or [string]::IsNullOrWhiteSpace($Want) -or (
    [string]::IsNullOrWhiteSpace($RulesetId) -and [string]::IsNullOrWhiteSpace($RulesetName)
)) { Usage }

# Validate Want JSON
$wantArr = $null
try {
  $wantArr = $Want | ConvertFrom-Json
  if ($wantArr -isnot [System.Collections.IEnumerable]) { throw "want not array" }
} catch {
  Write-Err "ERROR: -Want must be a JSON array of strings"
  exit 3
}

function Get-Rulesets {
  if (Have-Cmd "gh") {
    $raw = Gh-Api "repos/$Repo/rulesets"
    if ($null -eq $raw) { Write-Err "WARN: Failed to call gh api"; exit 2 }
    try { return $raw | ConvertFrom-Json } catch { Write-Err "WARN: Invalid JSON from gh"; exit 2 }
  } else {
    $res = Http-Get "https://api.github.com/repos/$Repo/rulesets"
    if ($res.status -ge 400) {
      if (Classify-Auth $res.body) { Write-Err "WARN: Auth/permission error while fetching rulesets"; exit 2 }
      Write-Err "WARN: Unexpected API error while fetching rulesets"
      exit 1
    }
    return $res.body
  }
}

function Get-Ruleset([string]$id) {
  if (Have-Cmd "gh") {
    $raw = Gh-Api "repos/$Repo/rulesets/$id"
    if ($null -eq $raw) { Write-Err "WARN: Failed to call gh api"; exit 2 }
    try { return $raw | ConvertFrom-Json } catch { Write-Err "WARN: Invalid JSON from gh"; exit 2 }
  } else {
    $res = Http-Get "https://api.github.com/repos/$Repo/rulesets/$id"
    if ($res.status -ge 400) {
      if (Classify-Auth $res.body) { Write-Err "WARN: Auth/permission error while fetching ruleset"; exit 2 }
      Write-Err "WARN: Unexpected API error while fetching ruleset"
      exit 1
    }
    return $res.body
  }
}

$rulesets = Get-Rulesets

if ([string]::IsNullOrWhiteSpace($RulesetId)) {
  $match = $rulesets | Where-Object { $_.name -eq $RulesetName } | Select-Object -First 1
  if ($null -eq $match) { Write-Err "ERROR: Ruleset not found by name: $RulesetName"; exit 3 }
  $RulesetId = [string]$match.id
}

$rs = Get-Ruleset $RulesetId

if ($rs.enforcement -ne "active") { Write-Err "WARN: Ruleset enforcement is not active (enforcement=$($rs.enforcement))"; exit 1 }

$includes = @()
try { $includes = $rs.conditions.ref_name.include } catch { $includes = @() }
if ($includes -notcontains "~DEFAULT_BRANCH") { Write-Err "WARN: Ruleset does not target ~DEFAULT_BRANCH"; exit 1 }

$got = New-Object System.Collections.Generic.HashSet[string]
foreach ($rule in ($rs.rules | Where-Object { $_.type -eq "required_status_checks" })) {
  foreach ($c in ($rule.parameters.required_status_checks)) {
    if ($null -ne $c.context -and $c.context -ne "") { $got.Add([string]$c.context) | Out-Null }
  }
}

$missing = @()
foreach ($w in $wantArr) { if (-not $got.Contains([string]$w)) { $missing += [string]$w } }

if ($missing.Count -gt 0) {
  Write-Err "WARN: Ruleset missing required status check contexts"
  Write-Err ("INFO: want: {0}" -f ($wantArr | ConvertTo-Json -Compress))
  Write-Err ("INFO: got : {0}" -f (($got.ToArray() | Sort-Object) | ConvertTo-Json -Compress))
  exit 1
}

Write-Err "INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe."
exit 0
