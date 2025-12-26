#!/usr/bin/env python3
# preflight_automerge_ruleset.py (Python 3)
# Verifies a GitHub Ruleset enforces required status checks on ~DEFAULT_BRANCH.
# Exit codes: 0 ok, 1 precheck fail, 2 auth/permission issue, 3 usage error.
# Security: never prints token values.
import os
import sys
import json
import subprocess
import re
from typing import List, Optional, Tuple, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_VERSION_DEFAULT = "2022-11-28"

def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)

def usage() -> int:
    eprint("Usage:")
    eprint("  scripts/python3/preflight_automerge_ruleset.py --repo OWNER/REPO [--ruleset-id ID | --ruleset-name NAME] --want '[\"lint\",\"test\"]'")
    return 3

def have_cmd(cmd: str) -> bool:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False

def classify_auth(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    msg = str(obj.get("message", "") or "")
    return re.search(r"(Bad credentials|Requires authentication|Resource not accessible|Forbidden|Must have admin rights|Not Found)", msg, re.I) is not None

def gh_api(endpoint: str, api_version: str) -> Optional[str]:
    try:
        out = subprocess.check_output([
            "gh", "api",
            "-H", "Accept: application/vnd.github+json",
            "-H", f"X-GitHub-Api-Version: {api_version}",
            endpoint
        ])
        return out.decode("utf-8", "replace")
    except Exception:
        return None

def http_get(url: str, api_version: str) -> Tuple[int, str]:
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

def parse_args(argv: List[str]) -> Optional[Tuple[str, Optional[str], Optional[str], str, str]]:
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
            repo = argv[i+1]; i += 2; continue
        if a == "--ruleset-id":
            ruleset_id = argv[i+1]; i += 2; continue
        if a == "--ruleset-name":
            ruleset_name = argv[i+1]; i += 2; continue
        if a == "--want":
            want = argv[i+1]; i += 2; continue
        if a == "--api-version":
            api_version = argv[i+1]; i += 2; continue
        raise ValueError(f"Unknown argument: {a}")
    if not repo or not want or (not ruleset_id and not ruleset_name):
        raise ValueError("Missing required arguments")
    return repo, ruleset_id, ruleset_name, want, api_version

def main(argv: List[str]) -> int:
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
            status, body = http_get(f"https://api.github.com/repos/{repo}/rulesets/{ruleset_id}", api_version)
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

    includes = (((rs_obj.get("conditions") or {}).get("ref_name") or {}).get("include") or [])
    if "~DEFAULT_BRANCH" not in includes:
        eprint("WARN: Ruleset does not target ~DEFAULT_BRANCH")
        return 1

    got = set()
    for rule in (rs_obj.get("rules") or []):
        if isinstance(rule, dict) and rule.get("type") == "required_status_checks":
            params = rule.get("parameters") or {}
            for item in (params.get("required_status_checks") or []):
                if isinstance(item, dict):
                    ctx = item.get("context") or ""
                    if ctx:
                        got.add(ctx)

    missing = [x for x in want if x not in got]
    if missing:
        eprint("WARN: Ruleset missing required status check contexts")
        eprint("INFO: want: %s" % json.dumps(want))
        eprint("INFO: got : %s" % json.dumps(sorted(got)))
        return 1

    eprint("INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
