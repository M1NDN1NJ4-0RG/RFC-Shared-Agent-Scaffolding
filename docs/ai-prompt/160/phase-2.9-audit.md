# Phase 2.9: Integration & YAML-First Contracts - Audit Report

**Date:** 2025-12-31  
**Issue:** #160 Phase 2.9  
**Auditor:** AI Agent (Copilot)

---

## Executive Summary

This audit identifies:
1. **Integration Status** of all helper scripts and tools
2. **Hardcoded Configuration** that should be migrated to YAML
3. **Contract Violations** that need remediation
4. **Recommendations** for Phase 2.9 implementation

### Key Findings

- ✅ **High Integration:** Most helper scripts are already integrated with `repo_lint`
- ⚠️ **Configuration Duplication:** Version pins exist in 3 places (Python, YAML, pyproject.toml)
- ⚠️ **Hardcoded Patterns:** File patterns and exclusions are hardcoded in Python
- ✅ **YAML-First Progress:** 4 conformance YAML files already exist

---

## 1. Helper Scripts Integration Audit

### 1.1 Integrated Scripts (✅ Already Called by repo_lint)

| Script | Integrated By | Status | Notes |
|--------|---------------|--------|-------|
| `scripts/validate_docstrings.py` | All language runners | ✅ Integrated | Called via subprocess in `_run_docstring_validation()` |
| `scripts/docstring_validators/*.py` | `validate_docstrings.py` | ✅ Integrated | Modular validators, imported by main script |

**Evidence:**
- `tools/repo_lint/runners/python_runner.py:273-290` - Calls `validate_docstrings.py --language python`
- `tools/repo_lint/runners/bash_runner.py:217-234` - Calls `validate_docstrings.py --language bash`
- `tools/repo_lint/runners/perl_runner.py:135-152` - Calls `validate_docstrings.py --language perl`
- `tools/repo_lint/runners/powershell_runner.py:169-186` - Calls `validate_docstrings.py --language powershell`
- `tools/repo_lint/runners/rust_runner.py` - Calls `validate_docstrings.py --language rust`

### 1.2 Wrapper Scripts (✅ Thin Delegates to repo_lint)

| Script | Purpose | Status | Notes |
|--------|---------|--------|-------|
| `scripts/run-linters.sh` | Bash wrapper for `repo-lint` CLI | ✅ Wrapper Only | `exec python3 -m tools.repo_lint "$COMMAND"` (line 63) |

**Analysis:** This is a thin convenience wrapper with no business logic. Maps `--fix` and `--install` to `repo-lint` commands. Does not need integration work.

### 1.3 Standalone Scripts (⚠️ Not Currently Integrated)

| Script | Purpose | Integration Status | Recommendation |
|--------|---------|-------------------|----------------|
| `scripts/validate-structure.sh` | Repository structure validation | ⚠️ Standalone | Consider future integration (Phase 3?) |
| `scripts/verify-repo-references.sh` | Cross-reference validation | ⚠️ Standalone | Consider future integration (Phase 3?) |

**Decision Required:** Should these be integrated into `repo-lint` in Phase 2.9, or defer to later phases?

**Recommendation:** DEFER - These are structural/semantic validators, not linters. Keep as standalone for now.

---

## 2. Configuration Duplication Audit

### 2.1 Tool Version Pins (❌ HIGH PRIORITY - 3 Sources of Truth)

**Current State:**

1. **`tools/repo_lint/install/version_pins.py`** (Python code):
   ```python
   PYTHON_TOOLS = {
       "black": "24.10.0",
       "ruff": "0.8.4",
       "pylint": "3.3.2",
       "yamllint": "1.35.1",
   }
   BASH_TOOLS = {"shellcheck": None, "shfmt": "v3.12.0"}
   POWERSHELL_TOOLS = {"PSScriptAnalyzer": "1.23.0"}
   PERL_TOOLS = {"Perl::Critic": None}
   ```

2. **`conformance/repo-lint/repo-lint-linting-rules.yaml`** (YAML config):
   ```yaml
   languages:
     python:
       tools:
         black:
           version: "24.10.0"
         ruff:
           version: "0.8.4"
         pylint:
           version: "3.3.2"
   ```

3. **`pyproject.toml`** (Package dependencies):
   ```toml
   [project.optional-dependencies]
   lint = [
       "black==24.10.0",
       "ruff==0.8.4",
       "pylint==3.3.2",
       "yamllint==1.35.1",
   ]
   ```

**Contract Violation:** Multiple sources of truth for same data.

**Remediation (REQUIRED for Phase 2.9):**
1. Make `repo-lint-linting-rules.yaml` the SINGLE source of truth
2. Update `version_pins.py` to LOAD from YAML (not hardcode)
3. Keep `pyproject.toml` for package installation, but sync from YAML programmatically or via docs/process
4. Add validation to ensure versions stay in sync

### 2.2 File Patterns and Exclusions (❌ HIGH PRIORITY - Hardcoded in Python)

**Current State:**

**`scripts/validate_docstrings.py` (lines 185-270):**
```python
IN_SCOPE_PATTERNS = [
    "**/*.sh",
    "**/*.bash",
    "**/*.py",
    "**/*.ps1",
    "**/*.psm1",
    "**/*.pl",
    "**/*.pm",
    "**/*.yaml",
    "**/*.yml",
    "**/*.rs",
]

EXCLUDE_PATTERNS = [
    "dist/**",
    "target/**",
    ".venv*/**",
    "node_modules/**",
    "conformance/repo-lint/unsafe-fix-fixtures/**",
    "conformance/repo-lint/fixtures/**",
    # ... more patterns ...
]
```

**`tools/repo_lint/runners/base.py` (lines 42-44):**
```python
EXCLUDED_PATHS = [
    "conformance/repo-lint/unsafe-fix-fixtures/",
]
```

**Contract Violation:** Configuration is hardcoded, not YAML-first.

**Remediation (REQUIRED for Phase 2.9):**
1. Create new YAML config: `conformance/repo-lint/repo-lint-file-patterns.yaml`
2. Migrate `IN_SCOPE_PATTERNS` and `EXCLUDE_PATTERNS` to YAML
3. Update `validate_docstrings.py` to load patterns from YAML
4. Update `base.py` to load excluded paths from YAML
5. Ensure backward compatibility with deprecation warnings

---

## 3. Existing YAML Configuration (✅ Good Progress)

### 3.1 Current YAML Files

| File | Purpose | Status | Contract Compliance |
|------|---------|--------|---------------------|
| `conformance/repo-lint/repo-lint-naming-rules.yaml` | Filename conventions per language | ✅ Exists | ✅ Compliant |
| `conformance/repo-lint/repo-lint-docstring-rules.yaml` | Docstring requirements per language | ✅ Exists | ✅ Compliant |
| `conformance/repo-lint/repo-lint-linting-rules.yaml` | Linting tool configs per language | ✅ Exists | ⚠️ Duplicate with version_pins.py |
| `conformance/repo-lint/repo-lint-ui-theme.yaml` | Rich UI theme configuration | ✅ Exists | ✅ Compliant |

**Analysis:** Strong YAML-first foundation exists. Main issue is duplication/inconsistency with Python code.

### 3.2 Missing YAML Files (Needed for Phase 2.9)

| Missing Config | Purpose | Priority | Recommendation |
|----------------|---------|----------|----------------|
| `repo-lint-file-patterns.yaml` | File discovery patterns and exclusions | HIGH | Create in Phase 2.9 |
| `repo-lint-exception-rules.yaml` | Centralized exception rules (Phase 2.6) | DEFER | Create in Phase 2.6 |

---

## 4. Phase 2.9 Implementation Requirements

### 4.1 MANDATORY Changes

1. **Eliminate Version Duplication (HIGH PRIORITY)**
   - [ ] Update `tools/repo_lint/install/version_pins.py` to load from `repo-lint-linting-rules.yaml`
   - [ ] Add validation to ensure versions are consistent
   - [ ] Update installer to use YAML as source
   - [ ] Document sync process for `pyproject.toml`

2. **Create File Patterns YAML (HIGH PRIORITY)**
   - [ ] Create `conformance/repo-lint/repo-lint-file-patterns.yaml`
   - [ ] Define schema for in-scope patterns and exclusions
   - [ ] Migrate hardcoded patterns from `validate_docstrings.py`
   - [ ] Migrate hardcoded exclusions from `base.py`
   - [ ] Update all consumers to load from YAML

3. **Backward Compatibility (REQUIRED)**
   - [ ] Add deprecation warnings for direct Python constant usage
   - [ ] Support transition period (load from YAML if present, fall back to Python)
   - [ ] Document migration timeline

4. **CLI Override Validation (REQUIRED)**
   - [ ] Audit existing CLI flags for contract violations
   - [ ] Ensure `--only`, `--ci`, `--theme` etc don't bypass YAML contracts
   - [ ] Add validation layer

### 4.2 Documentation Requirements

1. **Integration Contract Document**
   - [ ] Create `docs/contributing/integration-contracts.md`
   - [ ] Define rules for YAML-first configuration
   - [ ] Specify when new YAML files should be created
   - [ ] Document precedence rules (YAML > CLI > defaults)

2. **YAML Schema Documentation**
   - [ ] Document all YAML file schemas
   - [ ] Provide validation examples
   - [ ] List required vs optional fields

### 4.3 Testing Requirements

1. **YAML Loading Tests**
   - [ ] Test version loading from `repo-lint-linting-rules.yaml`
   - [ ] Test pattern loading from `repo-lint-file-patterns.yaml`
   - [ ] Test validation failures for invalid YAML

2. **Contract Enforcement Tests**
   - [ ] Test CLI overrides respect contracts
   - [ ] Test deprecation warnings trigger correctly
   - [ ] Test backward compatibility fallbacks

3. **Integration Tests**
   - [ ] Test end-to-end workflows with YAML configs
   - [ ] Verify no regressions in existing functionality

---

## 5. Recommendations

### 5.1 Phase 2.9 Scope (Minimal Changes)

**INCLUDE in Phase 2.9:**
1. ✅ Eliminate version duplication (version_pins.py → YAML loader)
2. ✅ Create file-patterns YAML and migrate patterns
3. ✅ Add deprecation warnings
4. ✅ Document integration contracts
5. ✅ Add tests for YAML loading

**DEFER to Later Phases:**
1. ❌ Integration of `validate-structure.sh` (Phase 3 polish)
2. ❌ Integration of `verify-repo-references.sh` (Phase 3 polish)
3. ❌ Exception rules YAML (Phase 2.6 centralized exceptions)

### 5.2 Implementation Order

1. **Step 1:** Create `repo-lint-file-patterns.yaml` (new config)
2. **Step 2:** Update `version_pins.py` to load from YAML
3. **Step 3:** Update `validate_docstrings.py` to load patterns from YAML
4. **Step 4:** Update `base.py` to load exclusions from YAML
5. **Step 5:** Add deprecation warnings
6. **Step 6:** Add tests
7. **Step 7:** Document contracts

### 5.3 Success Criteria

Phase 2.9 is complete when:
- ✅ No configuration duplication between Python and YAML
- ✅ All reasonable configuration is in YAML files
- ✅ Backward compatibility maintained with deprecation warnings
- ✅ Tests pass and validate YAML-first behavior
- ✅ Documentation clearly specifies contracts

---

## 6. Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing workflows | HIGH | Maintain backward compatibility, add deprecation warnings |
| YAML schema invalid | MEDIUM | Use existing config_validator, add schema tests |
| Performance impact from YAML loading | LOW | Cache loaded configs, only load once per run |
| Version sync drift (YAML vs pyproject.toml) | MEDIUM | Document sync process, consider automation |

---

## 7. Open Questions for Human Decision

1. **Standalone Scripts:** Should `validate-structure.sh` and `verify-repo-references.sh` be integrated in Phase 2.9, or defer to Phase 3?
   - **Recommendation:** DEFER to Phase 3 (not linting tools)

2. **Version Sync:** Should `pyproject.toml` versions be automatically synced from YAML, or manually maintained?
   - **Recommendation:** Manual sync with documented process (avoid over-automation)

3. **Transition Period:** How long should deprecation warnings remain before hard-breaking Python constants?
   - **Recommendation:** 2-3 releases minimum

---

## 8. Next Steps

1. Human review and approval of audit findings
2. Implement Step 1-7 from section 5.2
3. Run pre-commit validation: `repo-lint check --ci`
4. Request code review
5. Merge and proceed to Phase 2.7

