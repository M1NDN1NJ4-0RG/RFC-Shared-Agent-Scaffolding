# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20602534735
**Timestamp:** 2025-12-30 17:50:47 UTC
**Branch:** 140/merge
**Commit:** d52996610062eac2d75ea4d28a1ac7dc34320ac2

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | failure |
| Repo Lint: Perl | failure |
| Repo Lint: YAML | failure |
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

❌ ruff: FAILED (44 violation(s))
   .: [ruff] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:14:1: E402 Module level import not at top of file
   .: [ruff] |
   .: [ruff] 13 | # Unused import (Ruff F401 - not auto-fixable as it might be intentional)
   .: [ruff] 14 | import os  # noqa: F401 - Remove this noqa to trigger violation
   .: [ruff] | ^^^^^^^^^ E402
   .: [ruff] 15 | import sys
   .: [ruff] |
   .: [ruff] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:14:1: I001 [*] Import block is un-sorted or un-formatted
   .: [ruff] |
   .: [ruff] 13 |   # Unused import (Ruff F401 - not auto-fixable as it might be intentional)
   .: [ruff] 14 | / import os  # noqa: F401 - Remove this noqa to trigger violation
   .: [ruff] 15 | | import sys
   .: [ruff] 16 | |
   .: [ruff] 17 | |
   .: [ruff] 18 | | # Line too long (Ruff E501 - not auto-fixable as Black won't break it)
   .: [ruff] | |_^ I001
   .: [ruff] 19 |   VERY_LONG_STRING_THAT_EXCEEDS_THE_LINE_LENGTH_LIMIT_OF_ONE_HUNDRED_TWENTY_CHARACTERS_AND_CANNOT_BE_AUTO_FIXED_BY_BLACK = (
   .: [ruff] 20 |       "value"
   .: [ruff] |
   .: [ruff] = help: Organize imports
   .: [ruff] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:15:1: E402 Module level import not at top of file
   .: [ruff] |
   .: [ruff] 13 | # Unused import (Ruff F401 - not auto-fixable as it might be intentional)
   .: [ruff] 14 | import os  # noqa: F401 - Remove this noqa to trigger violation
   .: [ruff] 15 | import sys
   .: [ruff] | ^^^^^^^^^^ E402
   .: [ruff] |
   .: [ruff] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:15:8: F401 [*] `sys` imported but unused
   .: [ruff] |
   .: [ruff] 13 | # Unused import (Ruff F401 - not auto-fixable as it might be intentional)
   .: [ruff] 14 | import os  # noqa: F401 - Remove this noqa to trigger violation
   .: [ruff] 15 | import sys
   .: [ruff] |        ^^^ F401
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `sys`
   .: [ruff] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:19:121: E501 Line too long (122 > 120)
   .: [ruff] |
   .: [ruff] 18 | # Line too long (Ruff E501 - not auto-fixable as Black won't break it)
   .: [ruff] 19 | VERY_LONG_STRING_THAT_EXCEEDS_THE_LINE_LENGTH_LIMIT_OF_ONE_HUNDRED_TWENTY_CHARACTERS_AND_CANNOT_BE_AUTO_FIXED_BY_BLACK = (
   .: [ruff] |                                                                                                                         ^^ E501
   .: [ruff] 20 |     "value"
   .: [ruff] 21 | )
   .: [ruff] |
   .: [ruff] [*] 2 fixable with the `--fix` option.

❌ pylint: FAILED (6 violation(s))
   .: [pylint] ************* Module missing_docstring
   .: [pylint] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:19:0: C0301: Line too long (122/120) (line-too-long)
   .: [pylint] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:14:0: C0413: Import "import os" should be placed at the top of the module (wrong-import-position)
   .: [pylint] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:15:0: C0413: Import "import sys" should be placed at the top of the module (wrong-import-position)
   .: [pylint] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:14:0: W0611: Unused import os (unused-import)
   .: [pylint] conformance/repo-lint/fixtures/violations/python/missing_docstring.py:15:0: W0611: Unused import sys (unused-import)

❌ validate_docstrings: FAILED (6 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 5 violation(s) in 1 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/python/missing_docstring.py
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/python/missing_docstring.py:4
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/python/missing_docstring.py:8
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/python/missing_docstring.py:24
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/python/missing_docstring.py:9

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 56 violation(s) across 3 tool(s)
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

❌ shellcheck: FAILED (2 violation(s))
   .: [shellcheck] conformance/repo-lint/fixtures/violations/bash/missing-docstring.sh:11:1: warning: UNUSED_VAR appears unused. Verify use (or export if used externally). [SC2034]
   .: [shellcheck] conformance/repo-lint/fixtures/violations/bash/missing-docstring.sh:16:7: note: Double quote to prevent globbing and word splitting. [SC2086]

❌ shfmt: FAILED (1 violation(s))
   .: [shfmt] Shell scripts do not match shfmt style. Run 'python -m tools.repo_lint fix' to auto-format.

❌ validate_docstrings: FAILED (20 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 46 violation(s) in 9 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/bash/missing-docstring.sh
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 23 violation(s) across 3 tool(s)
```

## PowerShell Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PowerShell Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ validate_docstrings: FAILED (6 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 5 violation(s) in 1 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/powershell/MissingDocstring.ps1
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/powershell/MissingDocstring.ps1:4
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/powershell/MissingDocstring.ps1:14
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/powershell/MissingDocstring.ps1:20
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/powershell/MissingDocstring.ps1:25

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 6 violation(s) across 1 tool(s)
```

## Perl Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Perl Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ validate_docstrings: FAILED (5 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 4 violation(s) in 1 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/perl/missing_docstring.pl
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/perl/missing_docstring.pl:8
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/perl/missing_docstring.pl:14
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/conformance/repo-lint/fixtures/violations/perl/missing_docstring.pl:21

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 5 violation(s) across 1 tool(s)
```

## YAML Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YAML Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ yamllint: FAILED (12 violation(s))
   .: [yamllint] .github/workflows/drift-detection.yml:265:121: [warning] line too long (141 > 120 characters) (line-length)
   .: [yamllint] .github/workflows/drift-detection.yml:266:121: [warning] line too long (149 > 120 characters) (line-length)
   .: [yamllint] .github/workflows/drift-detection.yml:267:121: [warning] line too long (141 > 120 characters) (line-length)
   .: [yamllint] .github/workflows/repo-lint-weekly-full-scan.yml:82:121: [warning] line too long (130 > 120 characters) (line-length)
   .: [yamllint] .github/workflows/repo-lint-weekly-full-scan.yml:101:121: [warning] line too long (226 > 120 characters) (line-length)
   .: [yamllint] .github/workflows/rust-conformance.yml:98:121: [warning] line too long (164 > 120 characters) (line-length)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:4:1: [warning] missing document start "---" (document-start)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:4:121: [warning] line too long (130 > 120 characters) (line-length)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:7:12: [error] trailing spaces (trailing-spaces)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:11:4: [error] wrong indentation: expected 2 but found 3 (indentation)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:12:5: [error] wrong indentation: expected 5 but found 4 (indentation)
   .: [yamllint] conformance/repo-lint/fixtures/violations/yaml/bad-formatting.yml:15:3: [warning] comment not indented like content (comments-indentation)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 12 violation(s) across 1 tool(s)
```

