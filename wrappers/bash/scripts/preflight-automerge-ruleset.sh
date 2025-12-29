#!/usr/bin/env bash
#
# preflight-automerge-ruleset.sh - Verify GitHub Ruleset enforces required CI checks
#
# DESCRIPTION:
#   Pre-flight verification tool for GitHub auto-merge workflows. Validates that a
#   GitHub Ruleset is properly configured to protect the default branch with required
#   status checks before enabling auto-merge (Git Mode B).
#
#   Prevents the dangerous scenario where auto-merge is enabled but CI checks are
#   missing, which could allow broken code to merge automatically.
#
# USAGE:
#   preflight-automerge-ruleset.sh --repo OWNER/REPO --ruleset-name "NAME" --want '["check1","check2"]'
#   preflight-automerge-ruleset.sh --repo OWNER/REPO --ruleset-id 123 --want '["lint","test"]'
#
# INPUTS:
#   Required Arguments:
#     --repo OWNER/REPO      Repository slug (e.g., "m1ndn1nj4-0rg/example")
#     --want CONTEXTS_JSON   JSON array of required status check contexts
#                           Example: '["lint","typecheck","test"]'
#
#   Ruleset Selection (must provide one):
#     --ruleset-id ID        Ruleset numeric ID (from GitHub API)
#     --ruleset-name NAME    Ruleset name (exact string match)
#
#   Optional Arguments:
#     --api-version DATE     GitHub API version (default: 2022-11-28)
#     -h, --help            Show usage information
#
#   Environment Variables (Authentication):
#     gh auth               Prefers `gh api` if gh CLI is authenticated
#     TOKEN                 GitHub personal access token (fallback)
#     GITHUB_TOKEN          GitHub token (fallback if TOKEN not set)
#
# OUTPUTS:
#   Exit Codes:
#     0  Precheck OK - ruleset active, targets default branch, contexts present
#     1  Precheck failed - missing/disabled ruleset or contexts mismatch
#     2  Auth/permission error - caller should escalate to human
#     3  Usage/validation error - invalid arguments
#
#   Stdout:
#     (silent, all output goes to stderr)
#
#   Stderr:
#     INFO: PRECHECK_OK: ... - success message
#     WARN: <reason> - validation failures
#     ERROR: <reason> - fatal errors
#
# VALIDATION CHECKS:
#   1. Ruleset exists and is active (enforcement != "disabled")
#   2. Ruleset targets ~DEFAULT_BRANCH (not hardcoded branch name)
#   3. All required contexts in --want are present in ruleset
#   4. API authentication works (gh or TOKEN/GITHUB_TOKEN)
#
# SECURITY:
#   - NEVER prints tokens to stdout/stderr (security requirement)
#   - Exits with code 2 on auth errors so callers can escalate
#   - Uses jq for safe JSON parsing (prevents injection)
#   - Validates --want is a JSON array of strings
#
# PLATFORM COMPATIBILITY:
#   - Linux: Tested on Ubuntu 20.04+
#   - macOS: Compatible with Bash 3.2+ and 4.0+
#   - Windows: Works via Git Bash, WSL
#   - Requires: jq, gh (optional), curl (fallback)
#
# CONTRACT REFERENCES:
#   - GitHub Rulesets API: https://docs.github.com/en/rest/repos/rules
#   - Exit code 2 convention: Signal auth failure for human escalation
#   - Related: Git Mode B (auto-merge) workflows
#
# EXAMPLES:
#   # Check ruleset by name
#   preflight-automerge-ruleset.sh \
#     --repo m1ndn1nj4-0rg/Acronym-Wiki \
#     --ruleset-name "Main - PR Only + Green CI" \
#     --want '["lint","typecheck","test"]'
#
#   # Check ruleset by ID
#   preflight-automerge-ruleset.sh \
#     --repo octocat/example \
#     --ruleset-id 12345 \
#     --want '["build","test"]'
#
#   # Use in CI workflow
#   if ! preflight-automerge-ruleset.sh --repo "$REPO" --ruleset-name "$NAME" --want "$CHECKS"; then
#     echo "Cannot enable auto-merge: ruleset validation failed"
#     exit 1
#   fi
#
#   # Use with custom token
#   TOKEN="ghp_xxxx" preflight-automerge-ruleset.sh --repo owner/repo --want '["ci"]' --ruleset-id 999
#
# SEE ALSO:
#   - GitHub Rulesets API docs
#   - Git Mode B auto-merge workflows
# preflight-automerge-ruleset.sh
# Verify a GitHub Ruleset enforces required status checks on the default branch.
# Designed to be used before enabling auto-merge (Git Mode B).
#
# Security: This script never prints tokens. It uses `gh api` if available, otherwise curl with TOKEN/GITHUB_TOKEN.
# If authentication fails, exit with code 2 so callers can fall back to manual flow and ask a human to fix auth.
#
# IMPLEMENTATION NOTES:
# - Uses 'set -Eeuo pipefail' for strict error handling
# - Uses IFS=$'\n\t' to handle whitespace safely in loops
# - All JSON parsing done via jq (no string manipulation)
# - Helper functions: die, warn, info for consistent logging
#

set -Eeuo pipefail
IFS=$'\n\t'

# Helper functions for consistent logging
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Print warning message to stderr
# Args: $* = warning message
warn() { printf 'WARN: %s\n' "$*" >&2; }

# Print info message to stderr
# Args: $* = info message
info() { printf 'INFO: %s\n' "$*" >&2; }

# usage - Display help text and exit
# Embedded usage text matches CLI argument structure above
usage() {
  cat <<'USAGE'
Usage:
  scripts/preflight-automerge-ruleset.sh --repo OWNER/REPO [--ruleset-id ID | --ruleset-name NAME] --want CONTEXTS_JSON

Required:
  --repo OWNER/REPO            Repository slug (e.g., octocat/Hello-World)
  --want CONTEXTS_JSON         JSON array of required status check contexts (e.g., '["lint","test"]')

Ruleset selection:
  --ruleset-id ID              Ruleset numeric ID
  --ruleset-name NAME          Ruleset name (exact match)

Optional:
  --api-version YYYY-MM-DD     GitHub API version header (default: 2022-11-28)
  -h, --help                   Show help

Auth:
  Prefers `gh api` (uses gh auth). Otherwise uses curl with one of:
    - TOKEN
    - GITHUB_TOKEN
  This script MUST NOT print token values.

Exit codes:
  0  Precheck OK (ruleset active, targets default branch, required contexts present)
  1  Precheck failed (missing/disabled/contexts changed)
  2  Auth/permission error (caller should stop and ask human to fix)
  3  Usage/validation error

Examples:
  scripts/preflight-automerge-ruleset.sh --repo m1ndn1nj4-0rg/Acronym-Wiki \
    --ruleset-name "Main - PR Only + Green CI" \
    --want '["lint","typecheck","test"]'
USAGE
}

# require_cmd - Check if required command exists, exit if not
# Args: $1 = command name
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }

# json_has_default_branch_ref - Check if ruleset targets ~DEFAULT_BRANCH
# Reads: ruleset JSON from stdin
# Returns: 0 if ~DEFAULT_BRANCH in conditions.ref_name.include, else 1
json_has_default_branch_ref() {
  # Returns 0 if ruleset conditions include ~DEFAULT_BRANCH, otherwise 1.
  jq -e '((.conditions.ref_name.include // []) | index("~DEFAULT_BRANCH")) != null' >/dev/null
}

# collect_required_contexts - Extract required status check contexts from ruleset
# Reads: ruleset JSON from stdin
# Outputs: One context per line (sorted, unique)
collect_required_contexts() {
  # Print sorted unique contexts from required_status_checks rule.
  jq -r '
    [ .rules[]?
      | select(.type=="required_status_checks")
      | .parameters.required_status_checks[]?.context
    ]
    | unique
    | .[]
  '
}

#
# GITHUB API WRAPPERS
# Prefer gh CLI for auth, fallback to curl with TOKEN/GITHUB_TOKEN
#

# gh_get - Call GitHub API using gh CLI
# Args: $1 = API endpoint (e.g., "repos/owner/repo/rulesets")
gh_get() {
  local endpoint="$1"
  gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: ${API_VERSION}" "$endpoint"
}

# curl_get - Call GitHub API using curl with token auth
# Args: $1 = full URL
# Requires: TOKEN or GITHUB_TOKEN env var
# Security: Never prints token value
curl_get() {
  local url="$1"
  local token="${TOKEN:-${GITHUB_TOKEN:-}}"
  [[ -n "$token" ]] || die "No auth available: set TOKEN or GITHUB_TOKEN, or authenticate with gh"
  curl -sS -L \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: token ${token}" \
    -H "X-GitHub-Api-Version: ${API_VERSION}" \
    "$url"
}

# api_get_rulesets - Fetch all rulesets for a repository
# Args: $1 = repo (owner/name)
# Returns: JSON array of rulesets
api_get_rulesets() {
  local repo="$1"
  if command -v gh >/dev/null 2>&1; then
    gh_get "repos/${repo}/rulesets"
  else
    curl_get "https://api.github.com/repos/${repo}/rulesets"
  fi
}

# api_get_ruleset - Fetch a single ruleset by ID
# Args: $1 = repo (owner/name), $2 = ruleset ID
# Returns: JSON object for the ruleset
api_get_ruleset() {
  local repo="$1"
  local id="$2"
  if command -v gh >/dev/null 2>&1; then
    gh_get "repos/${repo}/rulesets/${id}"
  else
    curl_get "https://api.github.com/repos/${repo}/rulesets/${id}"
  fi
}

# classify_auth_error - Check if JSON response is an auth/permission error
# Reads: JSON from stdin
# Returns: 0 if auth error detected, 1 otherwise
# Used to distinguish auth failures from other API errors
classify_auth_error() {
  # Inspect JSON error bodies for auth/permission issues.
  # Returns 0 if looks like auth/permission problem, else 1.
  jq -e '
    (.message // "") as $m
    | ($m | test("Bad credentials|Requires authentication|Not Found|Resource not accessible|Must have admin rights|Forbidden"; "i"))
  ' >/dev/null
}

#
# MAIN LOGIC
# 1. Parse arguments
# 2. Fetch ruleset from GitHub API
# 3. Validate ruleset configuration
# 4. Check required contexts
#

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage; exit 0
  fi

  require_cmd jq

  API_VERSION="2022-11-28"
  REPO=""
  RULESET_ID=""
  RULESET_NAME=""
  WANT_JSON=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) REPO="${2:-}"; shift 2 ;;
      --ruleset-id) RULESET_ID="${2:-}"; shift 2 ;;
      --ruleset-name) RULESET_NAME="${2:-}"; shift 2 ;;
      --want) WANT_JSON="${2:-}"; shift 2 ;;
      --api-version) API_VERSION="${2:-}"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      --) shift; break ;;
      *) die "Unknown argument: $1 (use --help)" ;;
    esac
  done

  [[ -n "$REPO" ]] || { usage; exit 3; }
  [[ -n "$WANT_JSON" ]] || { usage; exit 3; }
  if [[ -z "$RULESET_ID" && -z "$RULESET_NAME" ]]; then
    die "Must provide --ruleset-id or --ruleset-name"
  fi

  # Validate want is a JSON array of strings
  if ! jq -e 'type=="array" and all(.[]; type=="string")' >/dev/null <<<"$WANT_JSON"; then
    die "--want must be a JSON array of strings (e.g., '[\"lint\",\"test\"]')"
  fi

  local rulesets_json
  if ! rulesets_json="$(api_get_rulesets "$REPO")"; then
    warn "Failed to fetch rulesets list"
    exit 2
  fi

  # If the API returned an error JSON, classify.
  if jq -e 'type=="object" and has("message") and has("status")' >/dev/null 2>&1 <<<"$rulesets_json"; then
    if classify_auth_error <<<"$rulesets_json"; then
      warn "Auth/permission error while fetching rulesets (repo=$REPO)"
      exit 2
    fi
    warn "Unexpected API error while fetching rulesets"
    printf '%s\n' "$rulesets_json" | jq -r '.message? // empty' >&2 || true
    exit 1
  fi

  if [[ -z "$RULESET_ID" ]]; then
    RULESET_ID="$(jq -r --arg name "$RULESET_NAME" '
      [ .[] | select(.name == $name) ][0].id // empty
    ' <<<"$rulesets_json")"
    [[ -n "$RULESET_ID" ]] || die "Ruleset not found by name: $RULESET_NAME"
  fi

  local rs_json
  if ! rs_json="$(api_get_ruleset "$REPO" "$RULESET_ID")"; then
    warn "Failed to fetch ruleset details"
    exit 2
  fi

  if jq -e 'type=="object" and has("message") and has("status")' >/dev/null 2>&1 <<<"$rs_json"; then
    if classify_auth_error <<<"$rs_json"; then
      warn "Auth/permission error while fetching ruleset (id=$RULESET_ID repo=$REPO)"
      exit 2
    fi
    warn "Unexpected API error while fetching ruleset"
    printf '%s\n' "$rs_json" | jq -r '.message? // empty' >&2 || true
    exit 1
  fi

  # Enforcement must be active
  local enforcement
  enforcement="$(jq -r '.enforcement // empty' <<<"$rs_json")"
  if [[ "$enforcement" != "active" ]]; then
    warn "Ruleset enforcement is not active (enforcement=$enforcement)"
    exit 1
  fi

  # Must include ~DEFAULT_BRANCH
  if ! json_has_default_branch_ref <<<"$rs_json"; then
    warn "Ruleset does not target ~DEFAULT_BRANCH"
    exit 1
  fi

  # Gather contexts
  local got_json
  got_json="$(collect_required_contexts <<<"$rs_json" | jq -R -s -c 'split("\n") | map(select(length>0)) | unique')"

  # Compute missing contexts: want - got
  local missing_count
  missing_count="$(jq -n --argjson want "$WANT_JSON" --argjson got "$got_json" '
    ($want - $got) | length
  ')"

  if [[ "$missing_count" -ne 0 ]]; then
    warn "Ruleset missing required status check contexts"
    info "want: $WANT_JSON"
    info "got : $got_json"
    exit 1
  fi

  info "PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe."
  exit 0
}

main "$@"
