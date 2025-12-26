# -*- coding: utf-8 -*-
    from __future__ import print_function
    import os, tempfile, shutil, unittest, json
    from ._helpers import run_py, make_exe

    class PreflightAutomergeRulesetTests(unittest.TestCase):
        def setUp(self):
            self.tmp=tempfile.mkdtemp(prefix="preflight-test-")
            self.bin=os.path.join(self.tmp, "bin")
            os.makedirs(self.bin)
            self.scripts=os.path.join(self.tmp, "scripts")
            os.makedirs(self.scripts)
            shutil.copy2(os.path.join(os.path.dirname(__file__), "..", "preflight_automerge_ruleset.py"),
                         os.path.join(self.scripts, "preflight_automerge_ruleset.py"))
            self.preflight=os.path.join(self.scripts, "preflight_automerge_ruleset.py")

            # Fake `gh` that returns deterministic JSON for rulesets endpoints.
            gh_script = r'''#!/usr/bin/env python3
import sys, json, os
args=sys.argv[1:]
# We only implement what the preflight script uses: `gh api <endpoint>`
if len(args) >= 2 and args[0] == "api":
    ep=args[1]
    if ep.endswith("/rulesets"):
        # list rulesets
        sys.stdout.write(json.dumps([
            {"id": 101, "name": "Main - PR Only + Green CI", "enforcement": "active"},
            {"id": 202, "name": "Other Ruleset", "enforcement": "active"}
        ]))
        sys.exit(0)
    if "/rulesets/" in ep:
        sys.stdout.write(json.dumps({
            "id": 101,
            "name": "Main - PR Only + Green CI",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [
                {"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "lint"}, {"context": "test"}]}}
            ]
        }))
        sys.exit(0)
sys.stderr.write("unsupported gh invocation: %r\n" % args)
sys.exit(2)
'''
            make_exe(os.path.join(self.bin, "gh"), gh_script)

            self.env=os.environ.copy()
            self.env["PATH"]=self.bin + os.pathsep + self.env.get("PATH","")

        def tearDown(self):
            shutil.rmtree(self.tmp, ignore_errors=True)

        def test_passes_when_ruleset_matches(self):
            rc, out, err, cmd = run_py(self.preflight, ["--repo", "OWNER/REPO", "--ruleset-name", "Main - PR Only + Green CI", "--want", '["lint","test"]'], cwd=self.tmp, env=self.env)
            self.assertEqual(rc, 0, "stderr=%s" % err)
            self.assertIn(b"PASS", out)

        def test_fails_when_missing_want_check(self):
            rc, out, err, cmd = run_py(self.preflight, ["--repo", "OWNER/REPO", "--ruleset-name", "Main - PR Only + Green CI", "--want", '["lint","does-not-exist"]'], cwd=self.tmp, env=self.env)
            self.assertNotEqual(rc, 0)
            self.assertIn(b"Missing required checks", out)

        def test_fails_when_ruleset_name_not_found(self):
            rc, out, err, cmd = run_py(self.preflight, ["--repo", "OWNER/REPO", "--ruleset-name", "Nope", "--want", '["lint"]'], cwd=self.tmp, env=self.env)
            self.assertNotEqual(rc, 0)
            self.assertIn(b"not found", out.lower())

    if __name__ == "__main__":
        unittest.main()
