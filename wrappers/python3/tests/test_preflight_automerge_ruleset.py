"""Unit tests for preflight_automerge_ruleset.py GitHub Ruleset verification tool.

This test module validates the preflight_automerge_ruleset.py implementation,
focusing on M0-P2-I1 Bearer token authentication, error classification, and
GitHub Ruleset verification logic.

Purpose
-------
Validates that the preflight_automerge_ruleset.py script correctly verifies
GitHub Ruleset configuration and uses proper Bearer token authentication.

Test Coverage
-------------
- Authentication error detection via classify_auth()
- Malformed --want argument rejection (non-JSON, non-array)
- Success path: Ruleset active, targets default branch, has all required checks
- Missing required check detection: Reports missing contexts
- Ruleset not found by name: Returns exit code 3
- Auth failure handling: Returns exit code 2 for 401/403 errors
- M0-P2-I1 Bearer token format validation in source code

Environment Variables
---------------------
TOKEN : str, optional
    GitHub personal access token (tested by tests, mocked).

GITHUB_TOKEN : str, optional
    GitHub personal access token (alternative, tested by tests, mocked).

Examples
--------
Run tests via pytest::

    pytest test-preflight_automerge_ruleset.py

Exit Codes
----------
0
    All tests passed
1
    One or more tests failed

Contract Validation (M0-P2-I1)
------------------------------
The http_get() function uses the modern Bearer token format:
    Authorization: Bearer <token>

This replaces the deprecated "token <token>" format. The test validates
this by inspecting the source code of http_get() to ensure it contains
the correct authentication header format.

Test Dependencies
-----------------
Uses unittest.mock.patch to mock GitHub API calls:
- have_cmd() mocked to return False (force HTTP path)
- http_get() mocked to return fixture responses
- gh_api() not used (have_cmd returns False)

All tests run fully offline with no actual GitHub API calls.

Test Fixtures
-------------
- _rulesets_list(): Mock response for GET /repos/{repo}/rulesets
- _ruleset_detail(contexts): Mock response for GET /repos/{repo}/rulesets/{id}

Platform Notes
--------------
- All tests are platform-independent (Linux, macOS, Windows compatible)
- No network access required (all API calls mocked)
- Uses importlib to dynamically load the module under test
"""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
MODULE_PATH = SCRIPTS / "preflight_automerge_ruleset.py"


def load_module():
    """Dynamically load preflight_automerge_ruleset.py as a Python module.

    Returns:
        Loaded module object

    Uses importlib to load the script even though it has hyphens in the
    filename (which aren't valid in Python module names). This allows
    tests to import and inspect functions from the script.
    """
    spec = importlib.util.spec_from_file_location("preflight_automerge_ruleset", str(MODULE_PATH))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class TestPreflightAutomergeRuleset(unittest.TestCase):
    """Test preflight_automerge_ruleset.py wrapper script.
    
    Validates ruleset verification logic including auth detection,
    argument parsing, and required context checking.
    """
    
    def setUp(self):
        """Set up test by loading the module."""
        self.mod = load_module()

    def _rulesets_list(self):
        """Generate test ruleset list fixture.
        
        Returns:
            List of ruleset dicts for testing
        """
        return [
            {"id": 111, "name": "Main - PR Only + Green CI"},
            {"id": 222, "name": "Other Ruleset"},
        ]

    def _ruleset_detail(self, required_contexts):
        """Generate test ruleset detail fixture.
        
        Args:
            required_contexts: List of required status check contexts
            
        Returns:
            Dict representing a GitHub ruleset configuration
        """
        return {
            "id": 111,
            "name": "Main - PR Only + Green CI",
            "enforcement": "active",
            "conditions": {
                "ref_name": {
                    "include": ["~DEFAULT_BRANCH"],
                    "exclude": [],
                }
            },
            "rules": [
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": False,
                        "required_status_checks": [{"context": c} for c in required_contexts],
                    },
                }
            ],
        }

    def test_classify_auth_detects_auth_errors(self):
        """Test that classify_auth correctly identifies authentication errors."""
        # classify_auth returns True if the response indicates an auth error
        self.assertTrue(self.mod.classify_auth({"message": "Bad credentials"}))
        self.assertTrue(self.mod.classify_auth({"message": "Requires authentication"}))
        self.assertTrue(self.mod.classify_auth({"message": "Forbidden"}))
        self.assertFalse(self.mod.classify_auth({"message": "Some other error"}))
        self.assertFalse(self.mod.classify_auth("not a dict"))

    def test_parse_args_rejects_malformed_want(self):
        """Test that malformed --want argument returns exit code 3."""
        # parse_args raises ValueError (caught by main, returns 3)
        # We can't test this directly since parse_args raises, not exits
        # Test via main instead
        rc = self.mod.main(["--repo", "o/r", "--ruleset-name", "x", "--want", "not-json"])
        self.assertEqual(rc, 3)

    def test_success_path_via_http(self):
        """Test successful ruleset verification via HTTP API.
        
        Returns:
            None (unittest test method)
        
        Verifies that the script correctly validates required contexts when
        accessing GitHub API via HTTP (gh CLI not available).
        """
        want = ["lint", "test"]

        def fake_http_get(url, api_version):
            """Mock HTTP GET for ruleset API calls.
            
            Args:
                url: API endpoint URL
                api_version: GitHub API version string
                
            Returns:
                Tuple of (status_code, json_body)
            """
            if url.endswith("/rulesets"):
                return 200, json.dumps(self._rulesets_list())
            if "/rulesets/111" in url:
                return 200, json.dumps(self._ruleset_detail(required_contexts=want))
            raise AssertionError(f"unexpected url {url}")

        with patch.object(self.mod, "have_cmd", return_value=False), patch.object(
            self.mod, "http_get", side_effect=fake_http_get
        ), patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            rc = self.mod.main(
                [
                    "--repo",
                    "owner/repo",
                    "--ruleset-name",
                    "Main - PR Only + Green CI",
                    "--want",
                    json.dumps(want),
                ]
            )
            self.assertEqual(rc, 0)

    def test_missing_required_context_fails(self):
        """Test that missing required status contexts causes failure.
        
        Returns:
            None (unittest test method)
        
        Verifies that the script exits with non-zero when the ruleset
        is missing one of the required status check contexts.
        """
        want = ["lint", "test"]
        have = ["lint"]

        def fake_http_get(url, api_version):
            """Mock HTTP GET missing one required context.
            
            Args:
                url: API endpoint URL
                api_version: GitHub API version string
                
            Returns:
                Tuple of (status_code, json_body)
            """
            if url.endswith("/rulesets"):
                return 200, json.dumps(self._rulesets_list())
            if "/rulesets/111" in url:
                return 200, json.dumps(self._ruleset_detail(required_contexts=have))
            raise AssertionError(f"unexpected url {url}")

        with patch.object(self.mod, "have_cmd", return_value=False), patch.object(
            self.mod, "http_get", side_effect=fake_http_get
        ), patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            rc = self.mod.main(
                [
                    "--repo",
                    "owner/repo",
                    "--ruleset-name",
                    "Main - PR Only + Green CI",
                    "--want",
                    json.dumps(want),
                ]
            )
            self.assertNotEqual(rc, 0)

    def test_ruleset_not_found_returns_3(self):
        """Test that non-existent ruleset returns exit code 3.
        
        Returns:
            None (unittest test method)
        
        Verifies that the script returns exit code 3 when the specified
        ruleset name is not found in the repository's rulesets.
        """
        def fake_http_get(url, api_version):
            """Mock HTTP GET with no matching ruleset.
            
            Args:
                url: API endpoint URL
                api_version: GitHub API version string
                
            Returns:
                Tuple of (status_code, json_body)
            """
            if url.endswith("/rulesets"):
                return 200, json.dumps([{"id": 999, "name": "nope"}])
            raise AssertionError(f"unexpected url {url}")

        with patch.object(self.mod, "have_cmd", return_value=False), patch.object(
            self.mod, "http_get", side_effect=fake_http_get
        ), patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            rc = self.mod.main(
                [
                    "--repo",
                    "owner/repo",
                    "--ruleset-name",
                    "Main - PR Only + Green CI",
                    "--want",
                    "[]",
                ]
            )
            self.assertEqual(rc, 3)

    def test_auth_failure_returns_2(self):
        """Test that authentication failure returns exit code 2.
        
        Returns:
            None (unittest test method)
        
        Verifies that the script returns exit code 2 when GitHub API
        returns a 401 authentication error.
        """
        def fake_http_get(url, api_version):
            """Mock HTTP GET with auth error.
            
            Args:
                url: API endpoint URL
                api_version: GitHub API version string
                
            Returns:
                Tuple of (status_code, json_body)
            """
            if url.endswith("/rulesets"):
                return 401, json.dumps({"message": "Bad credentials"})
            raise AssertionError(f"unexpected url {url}")

        with patch.object(self.mod, "have_cmd", return_value=False), patch.object(
            self.mod, "http_get", side_effect=fake_http_get
        ), patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"}):
            rc = self.mod.main(["--repo", "owner/repo", "--ruleset-name", "x", "--want", "[]"])
            self.assertEqual(rc, 2)

    def test_bearer_token_format_m0_p2_i1(self):
        """Validate M0-P2-I1: Authorization header uses Bearer token format"""
        import inspect

        # Check the source code contains "Bearer" in the Authorization header
        source = inspect.getsource(self.mod.http_get)
        self.assertIn("Bearer", source, "http_get should use 'Bearer' token format per M0-P2-I1")
        self.assertIn("Authorization", source, "http_get should set Authorization header")

        # Also verify it's not using the old 'token' format
        # Look for the pattern that would indicate old format
        self.assertNotIn(
            'f"token {token}"',
            source,
            "Should not use deprecated 'token {token}' format",
        )
