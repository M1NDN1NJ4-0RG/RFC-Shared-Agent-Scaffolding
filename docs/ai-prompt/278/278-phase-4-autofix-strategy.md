# Phase 4: Autofix Strategy for Type Annotations

## Overview

This document outlines the autofix strategy for implementing type annotations across the repository per issue #278.

## Current State (Baseline)

### Violation Counts

From Phase 3.3 PEP 526 checker:
- **152 missing module-level/class attribute annotations** detected by custom PEP 526 checker

From Phase 1.2 baseline (Ruff ANN* rules):
- **722 total function annotation violations**:
  - 389 missing return type annotations (ANN201)
  - 287 missing parameter type annotations (ANN001)
  - 26 missing private function return types (ANN202)
  - 11 missing special method return types (ANN204)
  - 4 missing class method return types (ANN206)
  - 2 missing `*args` annotations (ANN002)
  - 2 missing `**kwargs` annotations (ANN003)
  - 1 bare `Any` usage (ANN401)

**Total violations to address: ~874 annotation violations**

## Phase 4.1: Non-Destructive Autofix Strategy

### What Ruff Can Auto-Fix (SAFE)

**Ruff with `--unsafe-fixes` can auto-add trivial return type annotations:**

1. ✅ **`-> None`** for functions with no return or explicit `return None`
   - Detection: Ruff ANN201, ANN202, ANN204, ANN206
   - Safety: High (static analysis reliably detects void functions)
   - Coverage: Estimated ~200-300 violations

2. ✅ **`-> int`** for functions returning integer literals
   - Example: `return 42` → `-> int`
   - Safety: High (literal type is unambiguous)

3. ✅ **`-> str`** for functions returning string literals
   - Example: `return "hello"` → `-> str`
   - Safety: High (literal type is unambiguous)

4. ✅ **`-> bool`** for functions returning boolean literals
   - Example: `return True` → `-> bool`
   - Safety: High (literal type is unambiguous)

5. ✅ **`-> str | None`** for optional returns (modern syntax)
   - Example: `return "yes" if flag else None` → `-> str | None`
   - Safety: High (analyzes all return paths)
   - Note: Uses PEP 604 syntax (`|` not `Optional[]`) - may need manual conversion to `Optional[T]` for max compatibility

6. ✅ **`-> str | int`** for union returns
   - Example: `return 42 if flag else "no"` → `-> str | int`
   - Safety: High (analyzes all return paths)

**Total coverage:** Estimated ~400-500 violations can be auto-fixed (60-70% of return type violations)

### What Cannot Be Auto-Fixed (REQUIRES HUMAN DECISION)

**Must be done manually:**
1. ❌ **Parameter type annotations** (ANN001, ANN002, ANN003)
   - Reason: Type inference is context-dependent and error-prone
   - Action: Manual annotation required

2. ❌ **Return type annotations for value-returning functions**
   - Reason: Return type depends on business logic and may be complex
   - Action: Manual annotation required

3. ❌ **Module-level variable annotations** (PEP 526)
   - Reason: No standard tool auto-infers these
   - Action: Manual annotation required

4. ❌ **Class attribute annotations** (PEP 526)
   - Reason: No standard tool auto-infers these
   - Action: Manual annotation required

5. ❌ **Docstring `:rtype:` fields**
   - Reason: Requires understanding of return value semantics
   - Action: Manual addition required

### Autofix Implementation Plan

#### Step 1: Enable Ruff `-> None` Autofix (SAFE)

**Command:**
```bash
ruff check --select ANN --fix --unsafe-fixes <files>
```

**Expected impact:**
- Automatically adds trivial return type annotations (None, int, str, bool, unions)
- Reduces ANN201/ANN202/ANN204/ANN206 violations by ~60-70%
- Very low risk (Ruff only infers from literal returns and control flow analysis)
- **Note:** Ruff uses PEP 604 syntax (`T | None`) - may need manual conversion to `Optional[T]` for strict compatibility (per policy)

**Prerequisites:**
- None (Ruff is already configured)

**Testing:**
- Run autofix on test fixtures first
- Verify no semantic changes
- Confirm CI stays green

#### Step 2: Manual Annotation Workflow (REQUIRED)

For the remaining ~600+ violations that cannot be auto-fixed:

**Workflow:**
1. Identify files with violations using Ruff report
2. For each file, manually add:
   - Parameter type annotations where missing
   - Return type annotations for value-returning functions
   - Module-level variable annotations
   - Class attribute annotations
   - Docstring `:rtype:` fields for non-None returns

**Tooling support:**
- Use Ruff's violation reports to locate issues
- Use PEP 526 checker output for module/class violations
- Use docstring validator output for missing `:rtype:`

## Phase 4.2: Bulk Migration PR Plan

### Strategy: Staged Per-Directory Commits

To avoid a massive "big bang" PR, break the migration into staged commits:

### Stage 1: Autofix `-> None` Annotations (AUTOMATED)

**Scope:** All Python files in repository

**Actions:**
1. Remove per-file-ignores for ANN* rules from `pyproject.toml` temporarily
2. Run `ruff check --select ANN --fix --unsafe-fixes --exclude "tools/repo_lint/tests/fixtures/**" .`
3. Review changes (should be trivial return type additions: None, int, str, bool, unions)
4. **Post-processing:** Convert PEP 604 syntax to `Optional[T]` for compatibility:
   - Find: `-> (\w+) \| None`
   - Replace: `-> Optional[$1]` (add `from typing import Optional` as needed)
5. Run `repo-lint check --ci --only python` to verify
6. Commit: "Add trivial return type annotations via Ruff autofix"
7. Restore per-file-ignores (to avoid CI failures on remaining violations)
8. Push and ensure CI green

**Expected result:**
- ~400-500 trivial return type annotations added
- No manual intervention for inference (Ruff handles it)
- Manual post-processing for Optional syntax conversion (~5-10 minutes)
- CI stays green (only safe changes)

### Stage 2: Manual Annotation by Directory (ITERATIVE)

**Scope:** One directory at a time, prioritized by importance

**Priority order:**
1. `tools/repo_lint/runners/` - Core runner infrastructure
2. `tools/repo_lint/checkers/` - Checker modules
3. `tools/repo_lint/docstrings/` - Docstring validators
4. `tools/repo_lint/` (root) - CLI and orchestration
5. `scripts/` - Utility scripts
6. `wrappers/` - Language wrappers
7. `tools/repo_lint/tests/` - Test files (lower priority)

**Per-directory workflow:**
1. Remove directory from per-file-ignores in `pyproject.toml`
2. Run `ruff check --select ANN <directory>` to see violations
3. Run PEP 526 checker to see module/class violations
4. Manually add all missing annotations:
   - Function parameters
   - Return types
   - Module-level variables
   - Class attributes
   - Docstring `:rtype:` fields
5. Run `repo-lint check --ci` to verify green
6. Commit: "Add type annotations to <directory>"
7. Push and ensure CI green
8. Repeat for next directory

**Commit size:**
- Keep commits small (1 directory or 1-2 large modules at a time)
- Each commit must pass CI
- Allows easy rollback if issues arise

### Stage 3: Final Cleanup and Enforcement

**Once all directories are annotated:**

1. Remove all ANN per-file-ignores from `pyproject.toml`
2. Enable PEP 526 enforcement in repo-lint config (report violations)
3. Update docstring validator to require `:rtype:` for non-None returns
4. Run full CI suite to confirm green
5. Update documentation (Phase 6)

**Result:**
- Full type annotation enforcement active
- CI fails on new unannotated code
- Documentation reflects new standards

## Safety Guardrails

### Pre-Commit Checks

Before committing any autofix or manual changes:

1. **Syntax check:** Python files must parse successfully
   ```bash
   python3 -m py_compile <files>
   ```

2. **Linting green:** All existing linters must pass
   ```bash
   repo-lint check --ci --only python
   ```

3. **Tests pass:** Unit tests must stay green
   ```bash
   python3 -m pytest tools/repo_lint/tests/
   ```

### Rollback Plan

If issues arise during migration:

1. **Revert commit:** Use git revert to undo problematic commit
2. **Re-add per-file-ignore:** Temporarily exclude problematic files
3. **Fix issues:** Address root cause before re-attempting
4. **Retry:** Re-run migration for affected files

## Timeline Estimate

### Stage 1: Autofix Trivial Returns (SEMI-AUTOMATED)
- **Effort:** 2-3 hours
  - Autofix: 5 minutes
  - Post-processing (Optional syntax): 30-60 minutes
  - Review and testing: 60-90 minutes
- **Risk:** Low (Ruff infers from literals and control flow)
- **Benefit:** ~400-500 violations resolved

### Stage 2: Manual annotations (SLOW)
- **Effort per directory:** 1-3 hours depending on size (reduced from 2-4h due to autofix)
- **Total effort:** ~15-25 hours for entire repository (reduced from 20-30h)
- **Risk:** Medium (requires careful type selection for remaining complex cases)
- **Benefit:** ~300-400 violations resolved (parameters + complex returns)

### Stage 3: Enforcement (FAST)
- **Effort:** 1-2 hours
- **Risk:** Low (config changes only)
- **Benefit:** Prevents future violations

## Success Criteria

- [x] Phase 4.1 complete: Autofix strategy documented
- [ ] Stage 1 complete: All safe `-> None` annotations added
- [ ] Stage 2 complete: All directories manually annotated
- [ ] Stage 3 complete: Enforcement enabled in CI
- [ ] Zero annotation violations in `repo-lint check --ci`
- [ ] CI green on all commits
- [ ] Documentation updated (Phase 6)

## Dependencies

**Blocked by:** None (Phase 3 complete)

**Blocks:**
- Phase 5 (CI enforcement rollout) - requires annotations in place
- Phase 6 (Documentation updates) - requires final state known

## Notes

- Manual annotations will be time-consuming but necessary
- Consider pair programming or code review for complex types
- Use `Any` with `# typing: Any (TODO: tighten)` for truly unknown types (per policy)
- Prefer `Optional[T]` over `T | None` for compatibility (per policy)
- Test fixtures may remain unannotated (intentional violations)
