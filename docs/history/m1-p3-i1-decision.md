# M1-P3-I1: Python 2 Support Policy Decision

**Status:** ✅ DECIDED - Drop Python 2 Support  
**Date Finalized:** 2025-12-26  
**Decision:** Option A (Drop Python 2 bundle)  
**Authority:** @m1ndn1nj4 (PR #9 comment)

---

## Decision Summary

**Python 2 support has been removed from the RFC Shared Agent Scaffolding project.**

The Python 2 bundle located at `RFC-Shared-Agent-Scaffolding-Example/scripts/python2/` has been completely removed from the repository.

---

## Rationale

### Why Drop Python 2?

1. **End of Life:** Python 2 reached official end-of-life on January 1, 2020 (over 5 years ago)
2. **Maintenance Burden:** Supporting Python 2 increases maintenance complexity and CI overhead
3. **Modern Tooling:** Most modern environments (including GitHub Actions) no longer provide Python 2 by default
4. **Resource Allocation:** Engineering resources are better spent on M2-M4 conformance infrastructure and CI hardening
5. **Target Audience:** RFC Shared Agent Scaffolding targets modern agent tooling and workflows

### Testing Challenges

The Python 2 bundle had persistent test failures:
- Import/packaging mismatches
- Module structure incompatibilities  
- No straightforward path to CI integration without significant additional work

---

## What Was Removed

The following directory and all its contents were deleted:

```
RFC-Shared-Agent-Scaffolding-Example/scripts/python2/
├── readme-tests.md
├── run_tests.sh
├── scripts/
│   ├── preflight_automerge_ruleset.py
│   ├── safe_archive.py
│   ├── safe_check.py
│   └── safe_run.py
└── tests/
    ├── _helpers.py
    ├── test_preflight_automerge_ruleset.py
    ├── test_safe_archive.py
    ├── test_safe_check.py
    └── test_safe_run.py
```

**Total lines removed:** ~948 lines of code and tests

---

## Supported Language Bundles (Post-Decision)

The RFC Shared Agent Scaffolding Example now supports:

- ✅ **Bash** (`scripts/bash/`)
- ✅ **Python 3** (`scripts/python3/`) - **Python 3.7+ recommended**
- ✅ **Perl** (`scripts/perl/`)
- ✅ **PowerShell** (`scripts/powershell/`)

---

## Migration Path for Legacy Users

If users require Python 2 support for legacy environments, they have two options:

1. **Pin to a previous version** (before Python 2 removal):
   - Use git tag/commit from before this decision
   - Note: Will not receive M1-M4 conformance updates

2. **Port to Python 3**:
   - Python 3.7+ is widely available and recommended
   - Migration tools exist (e.g., `2to3`, `python-modernize`)
   - Python 3 bundle is fully aligned with M0 contract (see M1-P2-I1-STATUS.md)

---

## Impact on Other Milestones

### M1 (Implementation Consistency)
- [x] M1-P3-I1: Decision made ✅
- Simplifies CI matrix (one less language to validate)
- Removes blocker for M4-P1-I1 (Multi-Language CI Enforcement)

### M2 (Conformance Infrastructure)
- Conformance test vectors (M2-P1-I1) will target 4 languages instead of 5
- Golden behavior assertions (M2-P2-I1) have reduced scope

### M4 (CI & Operational Hardening)
- CI matrix simplified (no Python 2 runner needed)
- Faster CI execution with fewer jobs

---

## Documentation Updates Required

- [ ] Update README.md to list supported languages (no Python 2)
- [ ] Update RFC if it mentions Python 2 (preliminary check shows no references)
- [ ] Update EPIC-3-M0-SUMMARY.md to mark M1-P3-I1 as DECIDED
- [ ] Update EPIC-3-UPDATE.md to reflect decision

---

## References

- **Epic Tracker:** Issue #3
- **Decision Comment:** PR #9, comment by @m1ndn1nj4
- **Related Work:** M1-P2-I1 (Python 3 Bundle Alignment) - completed
- **M0 Decisions:** M0-DECISIONS.md

---

**Refs:** #3
