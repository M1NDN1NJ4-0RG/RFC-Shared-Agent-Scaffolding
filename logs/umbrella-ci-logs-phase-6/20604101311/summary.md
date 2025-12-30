# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20604101311
**Timestamp:** 2025-12-30 19:19:45 UTC
**Branch:** 144/merge
**Commit:** f3b4613078859b81c4bd55c4a1a47f15d1c2e8ab

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

❌ ruff: FAILED (8 violation(s))
   .: [ruff] tools/repo_lint/runners/rust_runner.py:217:61: F821 Undefined name `Path`
   .: [ruff] |
   .: [ruff] 215 |         return LintResult(tool="clippy", passed=False, violations=violations[:50])  # Limit output
   .: [ruff] 216 |
   .: [ruff] 217 |     def _parse_clippy_json_line(self, line: str, rust_dir: "Path") -> Optional[Violation]:
   .: [ruff] |                                                             ^^^^ F821
   .: [ruff] 218 |         """Parse a single line of clippy JSON output.
   .: [ruff] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 8 violation(s) across 1 tool(s)
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
   .: [validate_docstrings] ❌ Validation FAILED: 23 violation(s) in 4 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-preflight-automerge-ruleset.sh:98
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-preflight-automerge-ruleset.sh:111
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-preflight-automerge-ruleset.sh:130
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-preflight-automerge-ruleset.sh:149
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-preflight-automerge-ruleset.sh:168
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-archive.sh:57
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-archive.sh:80
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-archive.sh:97
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-archive.sh:114
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-check.sh:70
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:111
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:125
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:147
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:165
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:182
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:207
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:237
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:267
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/wrappers/bash/tests/test-safe-run.sh:292

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 20 violation(s) across 1 tool(s)
```

