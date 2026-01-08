# Issue #278 - Next Steps

## NEXT

- [x] Phase 0: Preflight (COMPLETE)
- [x] Phase 1: Evaluate existing Python contracts (COMPLETE)
- [x] Phase 2: Define the policy (COMPLETE)
- [ ] Phase 3: Tooling design (IN PROGRESS)
  - [ ] 3.1: Evaluate existing repo_lint Python runner (PARTIAL)
  - [x] 3.2: Enable Ruff ANN* rules in pyproject.toml (COMPLETE)
  - [ ] 3.3: Implement PEP 526 checker (REQUIRED - Ruff doesn't cover module/class attributes)
  - [ ] 3.4: Docstring validation consolidation (MANDATORY - large scope)
  - [ ] 3.5: Markdown contracts + linting support (MANDATORY - large scope)
  - [ ] 3.6: TOML contracts + linting support (MANDATORY - large scope)

**Phase 3 Status:**
- Created detailed implementation plan: `278-phase-3-implementation-plan.md`
- Estimated remaining scope: 28-48 hours
- Recommendation: Pick ONE of 3.4/3.5/3.6 and complete fully in next session

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
