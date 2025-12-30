# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20603428712
**Timestamp:** 2025-12-30 18:46:53 UTC
**Branch:** 141/merge
**Commit:** 67b71f405469f6e67d26e0247df8c882b2bc3634

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Python Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ validate_docstrings: FAILED (2 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 1 violation(s) in 1 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/tests/test_rust_runner.py:150

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 2 violation(s) across 1 tool(s)
```

## Bash Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bash Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ validate_docstrings: FAILED (20 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 45 violation(s) in 8 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:124
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:128
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:170
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:175
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:202
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:225
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:237
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:251
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/preflight-automerge-ruleset.sh:268
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/safe-archive.sh:117
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/safe-archive.sh:148
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/scripts/safe-run.sh:117
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:116
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:127
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:137
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:158
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:168
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:180
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/lib.sh:200

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 20 violation(s) across 1 tool(s)
```

