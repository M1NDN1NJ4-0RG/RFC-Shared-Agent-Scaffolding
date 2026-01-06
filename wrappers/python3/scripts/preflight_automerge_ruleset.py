#!/usr/bin/env python3
"""GitHub Ruleset verification tool for automerge preflight checks.

This module verifies that a GitHub Repository Ruleset enforces required status
checks on the default branch, ensuring safe automerge workflows. It validates
ruleset configuration via the GitHub API using M0-P2-I1 Bearer token authentication.

:Purpose:
Prevents unsafe automerge operations by verifying that GitHub Rulesets require
all specified CI status checks (e.g., "lint", "test") to pass before merging
to the default branch. This is a preflight check to ensure repository protection
rules are properly configured.

M0-P2-I1: Bearer Token Authentication
--------------------------------------
All GitHub API calls use the modern Bearer token format:
    Authorization: Bearer <token>

This replaces the deprecated "token <token>" format. The implementation
prioritizes the 'gh' CLI when available (which handles auth automatically),
and falls back to urllib with explicit Bearer token headers.

:Environment Variables:
TOKEN : str, optional
    GitHub personal access token (classic or fine-grained)
    Used for authentication if 'gh' CLI is not available

GITHUB_TOKEN : str, optional
    Alternative to TOKEN, same purpose
    Checked as fallback if TOKEN is not set

:GitHub API Requirements:
The token must have the following scopes/permissions:
- Repository: Read access to administration (for rulesets)
- Classic token: repo scope
- Fine-grained token: Administration: Read-only

:CLI Interface:
    python3 preflight-automerge-ruleset.py \
        --repo OWNER/REPO \
        [--ruleset-id ID | --ruleset-name NAME] \
        --want '["context1", "context2"]' \
        [--api-version VERSION]

Required Arguments:
    --repo OWNER/REPO
        GitHub repository in owner/name format
    --want JSON_ARRAY
        JSON array of required status check context names
        Example: '["lint", "test", "build"]'

Ruleset Selection (one required):
    --ruleset-id ID
        Numeric ruleset ID (from GitHub UI or API)
    --ruleset-name NAME
        Ruleset name (looked up via API, then ID is resolved)

Optional Arguments:
    --api-version VERSION
        GitHub API version (default: 2022-11-28)

:Exit Codes:
0
    Verification passed: ruleset is active, targets default branch,
    and enforces all required status checks
1
    Precheck failed: ruleset missing, not active, doesn't target
    default branch, or missing required status checks
2
    Auth/permission error: bad credentials, forbidden, or missing token
3
    Usage error: invalid arguments, malformed JSON, ruleset not found

:Verification Logic:
1. Fetch all rulesets for the repository
2. If --ruleset-name provided, resolve to ruleset ID
3. Fetch detailed ruleset configuration
4. Verify enforcement = "active"
5. Verify conditions include "~DEFAULT_BRANCH"
6. Extract required_status_checks contexts
7. Verify all --want contexts are present

:Examples:
Verify by ruleset name::

    python3 preflight-automerge-ruleset.py \
        --repo M1NDN1NJ4-0RG/myrepo \
        --ruleset-name "Main - PR Only + Green CI" \
        --want '["lint", "test"]'

Verify by ruleset ID::

    python3 preflight-automerge-ruleset.py \
        --repo M1NDN1NJ4-0RG/myrepo \
        --ruleset-id 12345 \
        --want '["build", "security-scan"]'

Using with 'gh' CLI (recommended)::

    gh auth login  # Authenticate once
    python3 preflight-automerge-ruleset.py --repo owner/repo --ruleset-name "CI" --want '["test"]'

Using with TOKEN environment variable::

    export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
    python3 preflight-automerge-ruleset.py --repo owner/repo --ruleset-id 999 --want '["lint"]'

:Security Notes:
- Token values are NEVER printed to stdout or stderr
- Errors are classified as auth/permission vs. other API failures
- Uses GitHub API version headers for forward compatibility
- User-Agent header identifies the tool for GitHub API analytics

:Side Effects:
- Makes HTTP GET requests to api.github.com
- May invoke 'gh api' command if 'gh' CLI is available
- Prints INFO, WARN, and ERROR messages to stderr
- No filesystem modifications

:Contract References:
- **M0-P2-I1**: Bearer token authentication format for GitHub API

:See Also:
- GitHub Rulesets API: https://docs.github.com/en/rest/repos/rules
- GitHub API Authentication: https://docs.github.com/en/rest/authentication
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import List, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_VERSION_DEFAULT = "2022-11-28"


def eprint(*args: object) -> None:
    """Print to stderr for status and error messages.

    :param args: Variable arguments to print (passed to print())
    :returns: None

    All output is sent to stderr to avoid interfering with stdout,
    which may be captured by CI/CD pipelines.
    """
    print(*args, file=sys.stderr)


def usage() -> int:
    """Print usage message and return exit code 3.

    :returns: 3 (usage error exit code)

    Displays command-line syntax. Caller is expected to exit with
    the returned code.
    """
    eprint("Usage:")
    eprint(
        "  scripts/python3/preflight-automerge-ruleset.py --repo OWNER/REPO "
        '[--ruleset-id ID | --ruleset-name NAME] --want \'["lint","test"]\''
    )
    return 3


def have_cmd(cmd: str) -> bool:
    """Check if a command is available in PATH.

    :param cmd: Command name to search for (e.g., "gh")
    :returns: True if command exists and is executable, False otherwise

    Used to detect if 'gh' CLI is available for GitHub API calls.
    The 'gh' CLI handles authentication automatically and is preferred
    over direct HTTP requests when available.
    """
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False


def classify_auth(obj: object) -> bool:
    """Detect if a GitHub API error response indicates an authentication issue.

    :param obj: Response object (should be dict from parsed JSON)
    :returns: True if error message indicates auth/permission problem, False otherwise

    Detection Logic
    ---------------
    Searches the "message" field for common authentication/authorization errors:
    - "Bad credentials": Invalid or expired token
    - "Requires authentication": No token provided
    - "Resource not accessible": Insufficient permissions
    - "Forbidden": Access denied
    - "Must have admin rights": Missing required permission scope
    - "Not Found": May indicate private repo without access (403 disguised as 404)

    Used to differentiate auth failures (exit 2) from other API errors (exit 1).

    Examples
    --------
    >>> classify_auth({"message": "Bad credentials"})
    True
    >>> classify_auth({"message": "Validation failed"})
    False
    >>> classify_auth("not a dict")
    False
    """
    if not isinstance(obj, dict):
        return False
    msg = str(obj.get("message", "") or "")
    return (
        re.search(
            r"(Bad credentials|Requires authentication|Resource not accessible"
            r"|Forbidden|Must have admin rights|Not Found)",
            msg,
            re.I,
        )
        is not None
    )


def gh_api(endpoint: str, api_version: str) -> str | None:
    """Call GitHub API using the 'gh' CLI tool.

    :param endpoint: API endpoint path (e.g., "repos/owner/repo/rulesets")
    :param api_version: GitHub API version (e.g., "2022-11-28")
    :returns: Response body as string, or None on failure

    Uses 'gh api' command with appropriate headers:
    - Accept: application/vnd.github+json
    - X-GitHub-Api-Version: <api_version>

    Authentication is handled automatically by the 'gh' CLI, which uses
    the credentials from 'gh auth login'.

    Returns None on any failure (command not found, auth error, API error)
    to allow graceful fallback to http_get().

    Examples
    --------
    >>> response = gh_api("repos/owner/repo/rulesets", "2022-11-28")
    >>> if response:
    ...     data = json.loads(response)
    """
    try:
        out = subprocess.check_output(
            [
                "gh",
                "api",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                f"X-GitHub-Api-Version: {api_version}",
                endpoint,
            ]
        )
        return out.decode("utf-8", "replace")
    except Exception:
        return None


def http_get(url: str, api_version: str) -> Tuple[int, str]:
    """Perform HTTP GET request to GitHub API with M0-P2-I1 Bearer token auth.

    :param url: Full GitHub API URL (e.g., "https://api.github.com/repos/...")
    :param api_version: GitHub API version header value
    :returns: Tuple of (status_code, response_body)
    :raises RuntimeError: If TOKEN/GITHUB_TOKEN environment variable not set

    Headers Set
    -----------
    - Accept: application/vnd.github+json
    - Authorization: Bearer <token>  (M0-P2-I1)
    - X-GitHub-Api-Version: <api_version>
    - User-Agent: agent-ops-preflight

    Authentication (M0-P2-I1)
    -------------------------
    Uses the modern Bearer token format:
        Authorization: Bearer <token>

    This replaces the deprecated "token <token>" format. The token is
    read from TOKEN or GITHUB_TOKEN environment variables.

    Error Handling
    --------------
    - Returns (status_code, body) for both success and HTTP errors
    - HTTPError responses include the error body in the return value
    - Raises RuntimeError if no token is available (caller handles)

    Security
    --------
    - Token value is NEVER printed to stdout or stderr
    - Token is only used in Authorization header
    - No token value appears in error messages

    Examples
    --------
    >>> status, body = http_get("https://api.github.com/repos/owner/repo/rulesets", "2022-11-28")
    >>> if status == 200:
    ...     data = json.loads(body)
    >>> elif status == 401:
    ...     print("Authentication failed")
    """
    token = os.environ.get("TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise RuntimeError("No auth available: set TOKEN/GITHUB_TOKEN or authenticate with gh")
    req = Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    # M0-P2-I1: Use Bearer token format
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", api_version)
    req.add_header("User-Agent", "agent-ops-preflight")
    try:
        with urlopen(req) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, body
    except HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body


def parse_args(
    argv: List[str],
) -> Tuple[str, str | None, str | None, str, str] | None:
    """Parse command-line arguments for ruleset verification.

    :param argv: Command-line arguments (sys.argv[1:])
    :returns: Tuple of (repo, ruleset_id, ruleset_name, want, api_version) or None for help
    :raises ValueError: If arguments are missing, invalid, or conflicting

    Required Arguments
    ------------------
    --repo OWNER/REPO
        GitHub repository in owner/name format
    --want JSON_ARRAY
        JSON array of required status check contexts

    Ruleset Selection (one required)
    --------------------------------
    --ruleset-id ID
        Numeric ruleset ID
    --ruleset-name NAME
        Ruleset name (resolved to ID via API)

    Optional Arguments
    ------------------
    --api-version VERSION
        GitHub API version (default: 2022-11-28)
    -h, --help
        Display usage (returns None)

    Return Value
    ------------
    Success: (repo, ruleset_id, ruleset_name, want, api_version)
    - Either ruleset_id or ruleset_name will be None (mutually exclusive)
    - want is the raw JSON string (not parsed)

    Help requested: None

    Errors: Raises ValueError with descriptive message

    Examples
    --------
    >>> parse_args(["--repo", "owner/repo", "--ruleset-id", "123", "--want", '["test"]'])
    ("owner/repo", "123", None, '["test"]', "2022-11-28")

    >>> parse_args(["-h"])
    None
    """
    repo = None
    ruleset_id = None
    ruleset_name = None
    want = None
    api_version = API_VERSION_DEFAULT
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            return None
        if a == "--repo":
            repo = argv[i + 1]
            i += 2
            continue
        if a == "--ruleset-id":
            ruleset_id = argv[i + 1]
            i += 2
            continue
        if a == "--ruleset-name":
            ruleset_name = argv[i + 1]
            i += 2
            continue
        if a == "--want":
            want = argv[i + 1]
            i += 2
            continue
        if a == "--api-version":
            api_version = argv[i + 1]
            i += 2
            continue
        raise ValueError(f"Unknown argument: {a}")
    if not repo or not want or (not ruleset_id and not ruleset_name):
        raise ValueError("Missing required arguments")
    return repo, ruleset_id, ruleset_name, want, api_version


def main(argv: List[str]) -> int:
    """Execute GitHub Ruleset verification workflow.

    :param argv: Command-line arguments (sys.argv[1:])
    :returns: Exit code (0=pass, 1=precheck fail, 2=auth error, 3=usage error)

    Verification Workflow
    ---------------------
    1. Parse command-line arguments
    2. Validate --want is a JSON array of strings
    3. Fetch all rulesets for the repository (via gh or http_get)
    4. If --ruleset-name provided, resolve to ruleset ID
    5. Fetch detailed ruleset configuration
    6. Verify ruleset.enforcement == "active"
    7. Verify ruleset.conditions include "~DEFAULT_BRANCH"
    8. Extract required_status_checks contexts from rules
    9. Verify all --want contexts are present in ruleset

    API Call Strategy
    -----------------
    Prefers 'gh' CLI if available (better auth handling), falls back to
    direct HTTP requests with Bearer token auth (M0-P2-I1).

    Two API calls made:
    1. GET /repos/{repo}/rulesets (list all rulesets)
    2. GET /repos/{repo}/rulesets/{id} (get ruleset details)

    Exit Codes
    ----------
    0
        SUCCESS: Ruleset is active, targets default branch, and enforces
        all required status checks
    1
        PRECHECK FAIL: Ruleset missing required checks, not active, or
        doesn't target default branch
    2
        AUTH/PERMISSION ERROR: Bad credentials, forbidden, or token missing
    3
        USAGE ERROR: Invalid arguments, malformed JSON, or ruleset not found

    Side Effects
    ------------
    - Prints WARN/INFO/ERROR messages to stderr
    - Makes GitHub API calls (GET requests only, no modifications)
    - May invoke 'gh api' command if gh CLI is available

    Error Handling
    --------------
    - classify_auth() differentiates auth errors from API errors
    - JSON parsing errors handled gracefully with appropriate exit codes
    - API failures return 2 (auth) or 1 (other) based on error classification

    Examples
    --------
    >>> main(["--repo", "owner/repo", "--ruleset-id", "123", "--want", '["lint"]'])
    # INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.
    0

    >>> main(["--repo", "owner/repo", "--ruleset-name", "CI", "--want", '["missing"]'])
    # WARN: Ruleset missing required status check contexts
    # INFO: want: ["missing"]
    # INFO: got : ["lint", "test"]
    1
    """
    try:
        parsed = parse_args(argv)
    except Exception as e:
        eprint(f"ERROR: {e}")
        return 3
    if parsed is None:
        return usage()
    repo, ruleset_id, ruleset_name, want_raw, api_version = parsed

    try:
        want = json.loads(want_raw)
        if not isinstance(want, list) or not all(isinstance(x, str) for x in want):
            raise ValueError()
    except Exception:
        eprint("ERROR: --want must be a JSON array of strings")
        return 3

    # fetch rulesets list
    rulesets_obj = None
    if have_cmd("gh"):
        raw = gh_api(f"repos/{repo}/rulesets", api_version)
        if raw is None:
            eprint("WARN: Failed to call gh api")
            return 2
        try:
            rulesets_obj = json.loads(raw)
        except Exception:
            eprint("WARN: Invalid JSON from gh")
            return 2
    else:
        try:
            status, body = http_get(f"https://api.github.com/repos/{repo}/rulesets", api_version)
        except Exception:
            eprint("WARN: Failed to fetch rulesets")
            return 2
        obj = {}
        try:
            obj = json.loads(body) if body else {}
        except Exception:
            obj = {}
        if status >= 400:
            if classify_auth(obj):
                eprint("WARN: Auth/permission error while fetching rulesets")
                return 2
            eprint("WARN: Unexpected API error while fetching rulesets")
            return 1
        rulesets_obj = obj

    if not ruleset_id:
        found = None
        for rs in rulesets_obj:
            if isinstance(rs, dict) and rs.get("name") == ruleset_name:
                found = rs.get("id")
                break
        if not found:
            eprint(f"ERROR: Ruleset not found by name: {ruleset_name}")
            return 3
        ruleset_id = str(found)

    # fetch ruleset details
    rs_obj = None
    if have_cmd("gh"):
        raw = gh_api(f"repos/{repo}/rulesets/{ruleset_id}", api_version)
        if raw is None:
            eprint("WARN: Failed to call gh api")
            return 2
        try:
            rs_obj = json.loads(raw)
        except Exception:
            eprint("WARN: Invalid JSON from gh")
            return 2
    else:
        try:
            status, body = http_get(
                f"https://api.github.com/repos/{repo}/rulesets/{ruleset_id}",
                api_version,
            )
        except Exception:
            eprint("WARN: Failed to fetch ruleset")
            return 2
        obj = {}
        try:
            obj = json.loads(body) if body else {}
        except Exception:
            obj = {}
        if status >= 400:
            if classify_auth(obj):
                eprint("WARN: Auth/permission error while fetching ruleset")
                return 2
            eprint("WARN: Unexpected API error while fetching ruleset")
            return 1
        rs_obj = obj

    if rs_obj.get("enforcement") != "active":
        eprint(f"WARN: Ruleset enforcement is not active (enforcement={rs_obj.get('enforcement')})")
        return 1

    includes = ((rs_obj.get("conditions") or {}).get("ref_name") or {}).get("include") or []
    if "~DEFAULT_BRANCH" not in includes:
        eprint("WARN: Ruleset does not target ~DEFAULT_BRANCH")
        return 1

    got = set()
    for rule in rs_obj.get("rules") or []:
        if isinstance(rule, dict) and rule.get("type") == "required_status_checks":
            params = rule.get("parameters") or {}
            for item in params.get("required_status_checks") or []:
                if isinstance(item, dict):
                    ctx = item.get("context") or ""
                    if ctx:
                        got.add(ctx)

    missing = [x for x in want if x not in got]
    if missing:
        eprint("WARN: Ruleset missing required status check contexts")
        eprint(f"INFO: want: {json.dumps(want)}")
        eprint(f"INFO: got : {json.dumps(sorted(got))}")
        return 1

    eprint("INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
