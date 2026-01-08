# Issue #278 - Next Steps

## NEXT

Phase 3.4 is COMPLETE. Continue with Phase 3.5 (Markdown) and 3.6 (TOML):

- [x] Phase 0: Preflight (COMPLETE)
- [x] Phase 1: Evaluate existing Python contracts (COMPLETE)
- [x] Phase 2: Define the policy (COMPLETE)
- [ ] Phase 3: Tooling design (IN PROGRESS)
  - [x] 3.1: Evaluate existing repo_lint Python runner (COMPLETE)
  - [x] 3.2: Enable Ruff ANN* rules in pyproject.toml (COMPLETE)
  - [ ] 3.3: Implement PEP 526 checker (DEFERRED - will do after 3.4/3.5/3.6)
  - [x] 3.4: Docstring validation consolidation (COMPLETE - all runners migrated)
  - [ ] 3.5: Markdown contracts + linting support (NEXT)
  - [ ] 3.6: TOML contracts + linting support (AFTER 3.5)

**Phase 3.4 Status: COMPLETE ✅**
- Created `tools/repo_lint/docstrings/` internal package
- Migrated all 6 language validators (Python, Bash, PowerShell, Perl, Rust, YAML)
- Updated all 6 language runners to use internal module (zero subprocess overhead)
- Converted `scripts/validate_docstrings.py` to thin CLI wrapper
- All tests pass (exit 0)
- Foundation ready for future `:rtype:` enforcement

**Next: Phase 3.5 - Markdown Contracts**
1. Create `docs/contributing/markdown-contracts.md`
2. Install/configure markdownlint-cli2
3. Create Markdown runner in repo_lint
4. Fix repo-wide Markdown conformance
5. Add comprehensive tests

## Resume Pointers

**Branch:** copilot/enforce-python-type-annotations

**Key Commands:**
- `repo-lint check --ci` - Run all linting checks (exit 0 currently)
- `rg "pattern"` - Search using ripgrep (canonical search tool)

**Recent Commits:**
- e4dddb0: Migrated Python docstring validation to internal module
- ab633d3: Completed all language runners migration
- 5bd54d5: Converted validate_docstrings.py to thin CLI wrapper
