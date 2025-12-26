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

    def test_classify_auth_prefers_bearer_when_token(self):
        self.assertEqual(self.mod.classify_auth('abc'), 'bearer')
        self.assertEqual(self.mod.classify_auth('ghp_xxx'), 'token')

    def test_parse_args_rejects_malformed_want(self):
        with self.assertRaises(SystemExit):
            self.mod.parse_args(['--repo','o/r','--ruleset-name','x','--want','not-json'])

    def test_success_path_via_http(self):
        want = ['lint', 'test']

        def fake_http_get(url, token=None, accept=None):
            if url.endswith('/rulesets'):
                return 200, self._rulesets_list(), None
            if '/rulesets/111' in url:
                return 200, self._ruleset_detail(required_contexts=want), None
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.object(self.mod, 'get_env_token', return_value='dummy'):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want',json.dumps(want)])
            self.assertEqual(rc, 0)

    def test_missing_required_context_fails(self):
        want = ['lint', 'test']
        have = ['lint']

        def fake_http_get(url, token=None, accept=None):
            if url.endswith('/rulesets'):
                return 200, self._rulesets_list(), None
            if '/rulesets/111' in url:
                return 200, self._ruleset_detail(required_contexts=have), None
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.object(self.mod, 'get_env_token', return_value='dummy'):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want',json.dumps(want)])
            self.assertNotEqual(rc, 0)

    def test_ruleset_not_found_returns_3(self):
        def fake_http_get(url, token=None, accept=None):
            if url.endswith('/rulesets'):
                return 200, [{'id': 999, 'name': 'nope'}], None
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.object(self.mod, 'get_env_token', return_value='dummy'):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','Main - PR Only + Green CI','--want','[]'])
            self.assertEqual(rc, 3)

    def test_auth_failure_returns_2(self):
        def fake_http_get(url, token=None, accept=None):
            if url.endswith('/rulesets'):
                return 401, {'message': 'Bad credentials'}, None
            raise AssertionError(f'unexpected url {url}')

        with patch.object(self.mod, 'have_cmd', return_value=False), \
             patch.object(self.mod, 'http_get', side_effect=fake_http_get), \
             patch.object(self.mod, 'get_env_token', return_value='dummy'):
            rc = self.mod.main(['--repo','owner/repo','--ruleset-name','x','--want','[]'])
            self.assertEqual(rc, 2)
