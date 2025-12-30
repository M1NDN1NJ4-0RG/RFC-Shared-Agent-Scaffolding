# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20604554489
**Timestamp:** 2025-12-30 19:46:24 UTC
**Branch:** 144/merge
**Commit:** a5e14167571c125bedf6632dcb5de3aa539bf0cf

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | success |
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

❌ ruff: FAILED (55 violation(s))
   .: [ruff] test_violations.py:8:1: I001 [*] Import block is un-sorted or un-formatted
   .: [ruff] |
   .: [ruff] 7 |   # Ruff violation: F401 - unused import
   .: [ruff] 8 | / import os
   .: [ruff] 9 | | import sys
   .: [ruff] 10 | | import json
   .: [ruff] 11 | |
   .: [ruff] 12 | | # Pylint violation: Line too long in a string that Black won't touch
   .: [ruff] | |_^ I001
   .: [ruff] 13 |   VERY_LONG_STRING = "This is an extremely long string that exceeds the 120 character line length limit and Black cannot fix it because it's already a single string literal and there's no good place to break it"
   .: [ruff] |
   .: [ruff] = help: Organize imports
   .: [ruff] test_violations.py:8:8: F401 [*] `os` imported but unused
   .: [ruff] |
   .: [ruff] 7 | # Ruff violation: F401 - unused import
   .: [ruff] 8 | import os
   .: [ruff] |        ^^ F401
   .: [ruff] 9 | import sys
   .: [ruff] 10 | import json
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `os`
   .: [ruff] test_violations.py:9:8: F401 [*] `sys` imported but unused
   .: [ruff] |
   .: [ruff] 7 | # Ruff violation: F401 - unused import
   .: [ruff] 8 | import os
   .: [ruff] 9 | import sys
   .: [ruff] |        ^^^ F401
   .: [ruff] 10 | import json
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `sys`
   .: [ruff] test_violations.py:10:8: F401 [*] `json` imported but unused
   .: [ruff] |
   .: [ruff] 8 | import os
   .: [ruff] 9 | import sys
   .: [ruff] 10 | import json
   .: [ruff] |        ^^^^ F401
   .: [ruff] 11 |
   .: [ruff] 12 | # Pylint violation: Line too long in a string that Black won't touch
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `json`
   .: [ruff] test_violations.py:13:121: E501 Line too long (209 > 120)
   .: [ruff] |
   .: [ruff] 12 | # Pylint violation: Line too long in a string that Black won't touch
   .: [ruff] 13 | VERY_LONG_STRING = "This is an extremely long string that exceeds the 120 character line length limit and Black cannot fix it because it's already a single string literal and there's no good place to break it"
   .: [ruff] |                                                                                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ E501
   .: [ruff] 14 |
   .: [ruff] 15 | # Ruff violation: E501 - line too long (comment)
   .: [ruff] |
   .: [ruff] test_violations.py:16:121: E501 Line too long (138 > 120)
   .: [ruff] |
   .: [ruff] 15 | # Ruff violation: E501 - line too long (comment)
   .: [ruff] 16 | # This is a very long comment that exceeds the 120 character line length limit and will trigger a Ruff violation because it's way too long
   .: [ruff] |                                                                                                                         ^^^^^^^^^^^^^^^^^^ E501
   .: [ruff] |
   .: [ruff] [*] 4 fixable with the `--fix` option.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 55 violation(s) across 1 tool(s)
```

