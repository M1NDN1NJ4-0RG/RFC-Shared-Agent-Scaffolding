# Issue #278 - Next Steps

## NEXT

- [x] Phase 0: Preflight (COMPLETE)
- [x] Phase 1: Evaluate existing Python contracts (COMPLETE)
- [x] Phase 2: Define the policy (COMPLETE)
  - [x] Created `docs/contributing/python-typing-policy.md`
- [ ] Phase 3: Tooling design
  - [ ] 3.1: Evaluate existing repo_lint Python runner
  - [ ] 3.2: Enable Ruff ANN* rules in pyproject.toml
  - [ ] 3.3: Implement PEP 526 checking (if needed beyond Ruff)
  - [ ] 3.4: Docstring validation consolidation (MANDATORY)
  - [ ] 3.5: Markdown contracts + linting support (MANDATORY)
  - [ ] 3.6: TOML contracts + linting support (MANDATORY)

## Resume Pointers

**Branch:** Working on issue #278 (main branch or feature branch TBD)

**Key Files:**
- `docs/ai-prompt/278/278-overview.md` - Full issue description
- `docs/ai-prompt/278/278-next-steps.md` - This file
- `docs/ai-prompt/278/278-summary.md` - Updated with every commit

**Key Commands:**
- `repo-lint check --ci` - Run all linting checks
- `rg "pattern"` - Search using ripgrep (canonical search tool)

**Context:**
This is a fresh session start for issue #278. The issue requires implementing Python type annotation enforcement + reST docstring return types enforcement across the entire repository. This is a phased EPIC issue with multiple deliverables.
