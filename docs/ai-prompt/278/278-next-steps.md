# Issue #278 - Next Steps

## NEXT

- [ ] Phase 0.1: Snapshot repo + tooling
  - [ ] Capture current Python toolchain versions (already done via repo-lint check --ci)
  - [ ] Search and document where Python lint/docstring/naming contracts are documented
- [ ] Phase 0.2: Inventory all Python files
  - [ ] Enumerate and classify all `*.py` files
  - [ ] Identify excluded directories/patterns
  - [ ] Create deliverable: `278-python-annotation-inventory.md`

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
