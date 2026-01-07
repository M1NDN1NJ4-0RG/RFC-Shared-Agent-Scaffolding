# Issue #278 - Next Steps

## NEXT

- [x] Phase 0.1: Snapshot repo + tooling (COMPLETE)
- [x] Phase 0.2: Inventory all Python files (COMPLETE)
- [x] Phase 1.1: Collect "contracts" that already exist (COMPLETE)
- [x] Phase 1.2: Current-violations baseline (COMPLETE)
- [ ] Phase 2.1: Policy specification (MANDATORY)
  - [ ] Create `docs/contributing/python-typing-policy.md`
  - [ ] Define PEP 526 annotation scope (module-level, class attributes)
  - [ ] Define required annotation patterns (empty literals, None inits, etc.)
  - [ ] Define fallback types policy (Any with tags, object, etc.)
- [ ] Phase 2.2: Function annotations policy (MANDATORY)
  - [ ] Document mandatory function annotation requirements
  - [ ] Define `*args`/`**kwargs` typing policy
- [ ] Phase 2.3: Docstring return type policy (MANDATORY)
  - [ ] Document `:rtype:` requirement for non-None returns

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
