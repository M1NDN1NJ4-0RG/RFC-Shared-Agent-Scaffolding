# Issue #278 - Next Steps

## NEXT

- [x] Phase 0.1: Snapshot repo + tooling (COMPLETE)
- [x] Phase 0.2: Inventory all Python files (COMPLETE)
- [ ] Phase 1.1: Collect "contracts" that already exist
  - [ ] Document exact current enforcement mechanisms
  - [ ] List what is enforced today (naming, docstrings, linting)
- [ ] Phase 1.2: Current-violations baseline
  - [ ] Run current Python checks and collect baseline
  - [ ] Identify most common failure categories
  - [ ] Determine which are autofixable

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
