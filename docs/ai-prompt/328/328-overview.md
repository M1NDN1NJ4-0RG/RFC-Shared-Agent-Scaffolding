# Issue 328 Overview
Last Updated: 2026-01-05
Related: Issue 328, PRs TBD

## Original Issue
# Issue: Add repo-wide `from __future__ import annotations` safely via AST-based helper script

## Goal
Create a **safe, deterministic** helper script that inserts:

```python
from __future__ import annotations
```

into Python files in the correct location, then run it repo-wide and commit the result.

This must be done in a way that is idempotent, AST-aware, and never breaks module docstrings.

⸻

## Requirements

### 1) Helper script (MANDATORY)

Create a new script:
- `scripts/add_future_annotations.py`

It must:
- Walk the repo and target only *.py files.
- Skip:
  - files inside virtualenvs and tool dirs (e.g. .venv/, .venv-lint/, .tox/, site-packages/, dist/, build/, .git/)
  - any file that is clearly generated (if the repo has a convention, follow it)
- Be idempotent:
  - If the future import already exists (anywhere in the file), do nothing.
- Insert the import in the correct place:
  1. Shebang line (if present) stays first: `#!/usr/bin/env python3`
  2. Encoding cookie (if present) stays immediately after shebang: `# -*- coding: utf-8 -*-`
  3. Module docstring stays at top (if present)
  4. Then insert: `from __future__ import annotations`
  5. Then the rest of imports / code continues as normal

Absolutely forbidden outcomes:
- Never insert the import above the module docstring.
- Never insert the import inside the module docstring.
- Never create duplicate future imports.
- Never reorder existing imports besides inserting this single line.

Implementation guidance:
- Use Python's tokenize module and/or ast to detect:
  - shebang
  - encoding cookie
  - module docstring boundaries
  - presence of an existing future import
- Prefer tokenize for precise placement and to avoid formatting drift.

The script must support:
- `--check` (no changes; exit 1 if any file would be changed, else 0)
- `--apply` (perform changes)
- `--verbose` (print each changed file)

⸻

### 2) Run it repo-wide (MANDATORY)

After the script is created:
1. Run:
   - `python3 scripts/add_future_annotations.py --check`
   - confirm it reports what it would change
2. Run:
   - `python3 scripts/add_future_annotations.py --apply`
3. Run formatting + lint gates:
   - `python3 -m tools.repo_lint check --ci`
   - any other canonical repo gates required by the repo (run them)

⸻

### 3) Tests (MANDATORY)

Add unit tests for the helper script.

Minimum cases:
- File with module docstring only → import inserted after docstring
- File with shebang + docstring → import after docstring (shebang stays first)
- File with encoding cookie + docstring → import after docstring (cookie preserved)
- File with no docstring → import inserted at the top (after shebang/cookie if present)
- File already containing `from __future__ import annotations` → no change
- File with other __future__ imports → add annotations without breaking ordering rules (keep existing future imports; add annotations in a safe spot without duplicates)

Tests must be deterministic and not depend on repository state.

⸻

## Deliverables
- `scripts/add_future_annotations.py`
- `tests/` coverage for the script
- Repo updated with correct future imports across Python files
- Clean CI gate: `python3 -m tools.repo_lint check --ci` must pass
- One commit containing only this change + any formatting changes required

⸻

## Completion Criteria

This issue is done only when:
- The script is merged and tests pass
- The script has been executed successfully
- The repo-wide placement is correct (docstrings untouched, no duplicates)
- All canonical checks pass

**DO NOT use regex for insertion. Use `tokenize`/`ast`.**

## Progress Tracker
- [x] Session start compliance completed
- [x] Explore repository structure
- [x] Create `scripts/add_future_annotations.py` script
- [x] Add comprehensive unit tests
- [x] Run script with `--check` to preview changes
- [x] Run script with `--apply` to apply changes
- [x] Run `repo-lint check --ci` to verify
- [x] Run code review
- [x] Address ALL code review feedback
- [x] Run CodeQL checker
- [x] Final verification
- [x] Commit and push all changes

## Session Notes (newest first)
### 2026-01-05 Session Complete - All Requirements Met
- Created AST-based script using tokenize module (NOT regex)
- Script correctly handles shebang, encoding cookies, and module docstrings
- Implemented --check, --apply, and --verbose flags
- Applied repo-wide: modified 78 Python files
- All 31 unit tests pass
- Code review completed with all feedback addressed
- CodeQL scan: 0 alerts (PASS)
- repo-lint check --ci: exit 0 (SUCCESS)
- Script is fully idempotent and safe
- Ready for merge

### 2026-01-05 Session Start
- Session compliance requirements read
- Bootstrapper completed successfully (exit 0)
- Environment activated and verified
- Health check passed (exit 0)
- Issue journal initialized
- Ready to begin implementation
