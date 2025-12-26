#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# preflight_automerge_ruleset.py (Python 2)
# Verifies a GitHub Ruleset enforces required status checks on ~DEFAULT_BRANCH.
# Exit codes: 0 ok, 1 precheck fail, 2 auth/permission issue, 3 usage error.
# Security: never prints token values.
from __future__ import print_function
import os
import sys
import json
import subprocess
import re

try:
    import urllib2
except ImportError:
    urllib2 = None

API_VERSION_DEFAULT = "2022-11-28"

def eprint(*args):
    print(*args, file=sys.stderr)

def usage():
    eprint("Usage:")
    eprint("  scripts/python2/preflight_automerge_ruleset.py --repo OWNER/REPO [--ruleset-id ID | --ruleset-name NAME] --want '[\"lint\",\"test\"]'")
    return 3

def have_cmd(cmd):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False

def classify_auth(obj):
    if not isinstance(obj, dict):
        return False
    msg = obj.get("message", "") or ""
    return re.search(r"(Bad credentials|Requires authentication|Resource not accessible|Forbidden|Must have admin rights|Not Found)", msg, re.I) is not None

def gh_api(endpoint, api_version):
    try:
        out = subprocess.check_output(["gh", "api",
                                       "-H", "Accept: application/vnd.github+json",
                                       "-H", "X-GitHub-Api-Version: %s" % api_version,
                                       endpoint])
        return out.decode("utf-8", "replace")
    except Exception:
        return None

def http_get(url, api_version):
    token = os.environ.get("TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise RuntimeError("No auth available: set TOKEN/GITHUB_TOKEN or authenticate with gh")
    req = urllib2.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", "token %s" % token)
    req.add_header("X-GitHub-Api-Version", api_version)
    req.add_header("User-Agent", "agent-ops-preflight")
    try:
        resp = urllib2.urlopen(req)
        body = resp.read()
        return resp.getcode(), body.decode("utf-8", "replace")
    except urllib2.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        return e.code, body
    except Exception as e:
        raise

def parse_args(argv):
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
        raise ValueError("Unknown argument: %s" % a)
    return repo, ruleset_id, ruleset_name, want, api_version

def main(argv):
    try:
        parsed = parse_args(argv)
    except Exception as e:
        eprint("ERROR: %s" % e)
        return 3
    if parsed is None:
        return usage()
    repo, ruleset_id, ruleset_name, want_raw, api_version = parsed
    if not repo or not want_raw or (not ruleset_id and not ruleset_name):
        return usage()

    try:
        want = json.loads(want_raw)
        if not isinstance(want, list) or not all(isinstance(x, (str, unicode)) for x in want):  # noqa: F821
            raise ValueError()
    except Exception:
        eprint("ERROR: --want must be a JSON array of strings")
        return 3

    # fetch rulesets list
    rulesets_obj = None
    if have_cmd("gh"):
        raw = gh_api("repos/%s/rulesets" % repo, api_version)
        if raw is None:
            eprint("WARN: Failed to call gh api")
            return 2
        try:
            rulesets_obj = json.loads(raw)
        except Exception:
            eprint("WARN: Invalid JSON from gh")
            return 2
    else:
        if urllib2 is None:
            eprint("ERROR: urllib2 unavailable")
            return 2
        try:
            status, body = http_get("https://api.github.com/repos/%s/rulesets" % repo, api_version)
        except Exception:
            eprint("WARN: Failed to fetch rulesets")
            return 2
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
            eprint("ERROR: Ruleset not found by name: %s" % ruleset_name)
            return 3
        ruleset_id = str(found)

    # fetch ruleset details
    rs_obj = None
    if have_cmd("gh"):
        raw = gh_api("repos/%s/rulesets/%s" % (repo, ruleset_id), api_version)
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
            status, body = http_get("https://api.github.com/repos/%s/rulesets/%s" % (repo, ruleset_id), api_version)
        except Exception:
            eprint("WARN: Failed to fetch ruleset")
            return 2
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
        eprint("WARN: Ruleset enforcement is not active (enforcement=%s)" % rs_obj.get("enforcement"))
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
        eprint("INFO: got : %s" % json.dumps(sorted(list(got))))
        return 1

    eprint("INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
