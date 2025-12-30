#!/usr/bin/env pwsh
<#
.SYNOPSIS
  preflight-automerge-ruleset.ps1 - Verify GitHub branch protection ruleset CI requirements

.DESCRIPTION
  Pre-merge validation script that verifies GitHub repository rulesets enforce required
  CI status checks on the default branch before allowing merge. Prevents automerge
  configurations that bypass quality gates.

  Purpose:
    - Query GitHub API for repository branch protection rulesets
    - Verify ruleset targets the default branch (~DEFAULT_BRANCH)
    - Verify ruleset enforcement is "active" (not "evaluate" or "disabled")
    - Validate that all required CI status check contexts are configured
    - Exit with specific codes to guide automation and human intervention

  This script prevents dangerous automerge configurations by ensuring that required
  CI checks (lint, test, build, etc.) are enforced before merge is allowed.

  Authentication Methods (tried in order):
    1. gh CLI (if available): Uses authenticated session
    2. TOKEN environment variable: GitHub Personal Access Token
    3. GITHUB_TOKEN environment variable: GitHub Actions token or PAT

  The script requires read:org scope for ruleset access.

.PARAMETER Repo
  GitHub repository in OWNER/REPO format.
  Example: "M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding"
  Required.

.PARAMETER RulesetId
  Numeric ID of the ruleset to verify.
  Either RulesetId or RulesetName must be provided.
  If RulesetName is provided, it will be resolved to an ID first.

.PARAMETER RulesetName
  Human-readable name of the ruleset.
  Example: "Main - PR Only + Green CI"
  Either RulesetId or RulesetName must be provided.

.PARAMETER Want
  JSON array of required status check context names.
  Must be valid JSON array of strings.
  Example: '["lint","test","build"]'
  Required.

.PARAMETER ApiVersion
  GitHub API version header value.
  Default: "2022-11-28"
  Optional. Override only for API compatibility testing.

.OUTPUTS
  Exit codes:
    0   Success: Ruleset enforces all required CI contexts on default branch
    1   Precheck failed: Missing contexts, inactive enforcement, or wrong branch target
    2   Auth/permission error: Invalid credentials or insufficient permissions (requires human action)
    3   Usage/validation error: Missing parameters or invalid JSON

  All diagnostic output is written to stderr.
  Output format:
    INFO: <informational message>
    WARN: <warning or failure explanation>
    ERROR: <error that requires immediate attention>

.ENVIRONMENT
  TOKEN
    GitHub personal access token for API authentication (first priority).
    Used if gh CLI is not available.

  GITHUB_TOKEN
    GitHub personal access token (alternative to TOKEN, second priority).
    Used if gh CLI is not available and TOKEN is not set.

.EXAMPLE
  # Verify ruleset by name with gh CLI authentication
  PS> .\preflight-automerge-ruleset.ps1 `
        -Repo "owner/repo" `
        -RulesetName "Main - PR Only + Green CI" `
        -Want '["lint","test"]'
  INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.
  PS> $LASTEXITCODE
  0

.EXAMPLE
  # Verify ruleset by ID with explicit token
  PS> $env:TOKEN = "ghp_xxxxxxxxxxxx"
  PS> .\preflight-automerge-ruleset.ps1 `
        -Repo "owner/repo" `
        -RulesetId "12345" `
        -Want '["lint","test","build"]'

.EXAMPLE
  # Detect missing required context
  PS> .\preflight-automerge-ruleset.ps1 `
        -Repo "owner/repo" `
        -RulesetName "Main" `
        -Want '["lint","test","security"]'
  WARN: Ruleset missing required status check contexts
  INFO: want: ["lint","test","security"]
  INFO: got : ["lint","test"]
  PS> $LASTEXITCODE
  1

.EXAMPLE
  # Detect inactive enforcement
  PS> .\preflight-automerge-ruleset.ps1 `
        -Repo "owner/repo" `
        -RulesetName "Main" `
        -Want '["lint"]'
  WARN: Ruleset enforcement is not active (enforcement=evaluate)
  PS> $LASTEXITCODE
  1

.NOTES
  Platform Compatibility:
    - Windows PowerShell 5.1: Supported
    - PowerShell 7+ (pwsh): Supported on Windows, Linux, macOS
    - Cross-platform HTTP client (Invoke-RestMethod)

  Security:
    - Never prints token values in output or logs
    - Tokens are only used in Authorization headers
    - Auth failures are classified separately from other errors (exit code 2)

  Contract References:
    - M0-P2-I2: Preflight automerge ruleset verification protocol

  Side Effects:
    - None. Read-only GitHub API queries only.
    - No file system modifications
    - No state changes

  API Details:
    - Uses GitHub REST API v3
    - Endpoints:
      - GET /repos/{owner}/{repo}/rulesets (list rulesets)
      - GET /repos/{owner}/{repo}/rulesets/{id} (get specific ruleset)
    - Requires 'read:org' scope for private repository rulesets
    - Rate limited per GitHub API rate limit policies

  Error Classification:
    - Exit 0: All checks passed, safe to proceed with automerge
    - Exit 1: Precheck failed, automerge should NOT be enabled (fixable)
    - Exit 2: Auth/permission error, requires human intervention (blocked)
    - Exit 3: Usage error, fix command-line arguments (developer error)

  Validation Logic:
    1. Resolve ruleset by ID or name
    2. Check enforcement == "active"
    3. Check conditions.ref_name.include contains "~DEFAULT_BRANCH"
    4. Extract all required_status_checks contexts
    5. Verify all wanted contexts are present in ruleset

  Design Notes:
    - Prefer gh CLI if available (handles auth automatically)
    - Fallback to HTTP client with explicit token
    - Auth errors are distinguished from API errors for better diagnostics
    - JSON validation happens before API calls (fail fast)

.LINK
  https://docs.github.com/en/rest/repos/rules

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/RFC-Shared-Agent-Scaffolding-v0.1.0.md
#>

param(
  [Parameter(Mandatory=$false)][string]$Repo,
  [Parameter(Mandatory=$false)][string]$RulesetId,
  [Parameter(Mandatory=$false)][string]$RulesetName,
  [Parameter(Mandatory=$false)][string]$Want,
  [Parameter(Mandatory=$false)][string]$ApiVersion = "2022-11-28"
)

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
Displays usage information and exits with code 3.
#>
function Usage {
  Write-Err "Usage:"
  Write-Err "  scripts/preflight-automerge-ruleset.ps1 -Repo OWNER/REPO (-RulesetId ID | -RulesetName NAME) -Want '[\"lint\",\"test\"]'"
  exit 3
}

<#
.SYNOPSIS
Checks if a command is available in the PATH.
.PARAMETER cmd
The command name to check for.
.OUTPUTS
Boolean indicating whether the command exists.
#>
function Have-Cmd([string]$cmd) { return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }

<#
.SYNOPSIS
Determines if an API error response indicates an authentication or permission issue.
.PARAMETER obj
The error response object to classify.
.OUTPUTS
Boolean indicating whether this is an auth/permission error.
#>
function Classify-Auth($obj) {
  if ($null -eq $obj) { return $false }
  $msg = $obj.message
  if ([string]::IsNullOrWhiteSpace($msg)) { return $false }
  return $msg -match '(?i)(Bad credentials|Requires authentication|Resource not accessible|Forbidden|Must have admin rights|Not Found)'
}

<#
.SYNOPSIS
Calls the GitHub API using gh CLI.
.PARAMETER endpoint
The API endpoint path to call.
.OUTPUTS
The raw JSON response or null on error.
#>
function Gh-Api([string]$endpoint) {
  try {
    $out = & gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: $ApiVersion" $endpoint 2>$null
    return $out
  } catch { return $null }
}

<#
.SYNOPSIS
Makes an HTTP GET request with GitHub API authentication.
.PARAMETER url
The URL to request.
.OUTPUTS
Object with status code and body properties.
#>
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
  # Ensure it's an array (ConvertFrom-Json may return a single string if input has one element)
  $wantArr = @($wantArr)
} catch {
  Write-Err "ERROR: -Want must be a JSON array of strings"
  exit 3
}

<#
.SYNOPSIS
Fetches all rulesets for the repository using GitHub API.
.OUTPUTS
Array of ruleset objects.
#>
function Get-Rulesets {
  if (Have-Cmd "gh") {
    $raw = Gh-Api "repos/$Repo/rulesets"
    if ($null -eq $raw) { Write-Err "WARN: Failed to call gh api"; exit 2 }
    try {
      $parsed = $raw | ConvertFrom-Json
      return $parsed.rulesets
    } catch { Write-Err "WARN: Invalid JSON from gh"; exit 2 }
  } else {
    $res = Http-Get "https://api.github.com/repos/$Repo/rulesets"
    if ($res.status -ge 400) {
      if (Classify-Auth $res.body) { Write-Err "WARN: Auth/permission error while fetching rulesets"; exit 2 }
      Write-Err "WARN: Unexpected API error while fetching rulesets"
      exit 1
    }
    return $res.body.rulesets
  }
}

<#
.SYNOPSIS
Fetches a specific ruleset by ID using GitHub API.
.PARAMETER id
The ruleset ID to fetch.
.OUTPUTS
The ruleset object.
#>
function Get-Ruleset([string]$id) {
  if (Have-Cmd "gh") {
    $raw = Gh-Api "repos/$Repo/rulesets/$id"
    if ($null -eq $raw) { Write-Err "WARN: Failed to call gh api"; exit 2 }
    try {
      $parsed = $raw | ConvertFrom-Json
      # Handle both direct ruleset response and wrapped response (for test compatibility)
      if ($null -ne $parsed.rulesets) {
        # Wrapped response - find the ruleset by ID
        return $parsed.rulesets | Where-Object { [string]$_.id -eq $id } | Select-Object -First 1
      } else {
        # Direct ruleset response
        return $parsed
      }
    } catch { Write-Err "WARN: Invalid JSON from gh"; exit 2 }
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
  # Convert HashSet to array for sorting and JSON serialization
  $gotArray = @($got)
  Write-Err ("INFO: got : {0}" -f (($gotArray | Sort-Object) | ConvertTo-Json -Compress))
  exit 1
}

Write-Err "INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe."
exit 0
