import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / 'scripts'
MODULE_PATH = SCRIPTS / 'preflight_automerge_ruleset.py'


def load_module():
    spec = importlib.util.spec_from_file_location('preflight_automerge_ruleset', str(MODULE_PATH))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class TestPreflightAutomergeRuleset(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def _rulesets_list(self):
        return [
            {'id': 111, 'name': 'Main - PR Only + Green CI'},
            {'id': 222, 'name': 'Other Ruleset'},
        ]

    def _ruleset_detail(self, required_contexts):
        return {
            'id': 111,
            'name': 'Main - PR Only + Green CI',
            'enforcement': 'active',
            'conditions': {
                'ref_name': {
                    'include': ['~DEFAULT_BRANCH'],
                    'exclude': [],
                }
            },
            'rules': [
                {
                    'type': 'required_status_checks',
                    'parameters': {
                        'strict_required_status_checks_policy': False,
                        'required_status_checks': [{'context': c} for c in required_contexts],
                    },
                }
            ],
        }

    def test_classify_auth_detects_auth_errors(self):
        # classify_auth returns True if the response indicates an auth error
        self.assertTrue(self.mod.classify_auth({'message': 'Bad credentials'}))
        self.assertTrue(self.mod.classify_auth({'message': 'Requires authentication'}))
        self.assertTrue(self.mod.classify_auth({'message': 'Forbidden'}))
        self.assertFalse(self.mod.classify_auth({'message': 'Some other error'}))
        self.assertFalse(self.mod.classify_auth('not a dict'))

    def test_parse_args_rejects_malformed_want(self):
        # parse_args raises ValueError (caught by main, returns 3)
        # We can't test this directly since parse_args raises, not exits
        # Test via main instead
        rc = self.mod.main(['--repo','o/r','--ruleset-name','x','--want','not-json'])
        self.assertEqual(rc, 3)

    def test_success_path_via_http(self):
        want = ['lint', 'test']

        def fake_http_get(url, api_version):
            if url.endswith('/rulesets'):
                return 200, json.dumps(self._rulesets_list())
            if '/rulesets/111' in url:
                return 200, json.dumps(self._ruleset_detail(required_contexts=want))
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'}):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want',json.dumps(want)])
            self.assertEqual(rc, 0)

    def test_missing_required_context_fails(self):
        want = ['lint', 'test']
        have = ['lint']

        def fake_http_get(url, api_version):
            if url.endswith('/rulesets'):
                return 200, json.dumps(self._rulesets_list())
            if '/rulesets/111' in url:
                return 200, json.dumps(self._ruleset_detail(required_contexts=have))
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'}):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want',json.dumps(want)])
            self.assertNotEqual(rc, 0)

    def test_ruleset_not_found_returns_3(self):
        def fake_http_get(url, api_version):
            if url.endswith('/rulesets'):
                return 200, json.dumps([{'id': 999, 'name': 'nope'}])
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'}):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want','[]'])
            self.assertEqual(rc, 3)

    def test_auth_failure_returns_2(self):
        def fake_http_get(url, api_version):
            if url.endswith('/rulesets'):
                return 401, json.dumps({'message': 'Bad credentials'})
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'}):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','x','--want','[]'])
            self.assertEqual(rc, 2)

    def test_bearer_token_format_m0_p2_i1(self):
        """Validate M0-P2-I1: Authorization header uses Bearer token format"""
        import inspect
        
        # Check the source code contains "Bearer" in the Authorization header
        source = inspect.getsource(self.mod.http_get)
        self.assertIn('Bearer', source, "http_get should use 'Bearer' token format per M0-P2-I1")
        self.assertIn('Authorization', source, "http_get should set Authorization header")
        
        # Also verify it's not using the old 'token' format
        # Look for the pattern that would indicate old format
        self.assertNotIn('f"token {token}"', source, "Should not use deprecated 'token {token}' format")
