# Workflow Parity Analysis: Umbrella vs. Legacy Workflows

**Purpose:** Document parity between new umbrella workflow and legacy workflows to support Sub-Item 6.4.7 (migration) and Sub-Item 6.4.9 (CI verification).

**Date:** 2025-12-30 17:10

---

## Legacy Workflows to Migrate

### 1. `docstring-contract.yml`
**Purpose:** Validates docstring contracts for ALL scripts/YAML files repository-wide

**Triggers:**
- Pull requests modifying any script/YAML/docs
- Pushes to main
- Manual dispatch

**What it does:**
- Runs `python3 scripts/validate_docstrings.py` (no language selector, validates ALL)
- Single job: "Docstring Contract Validation"
- Uses Python 3.8+
- Uses `continue-on-error: true` (does not fail hard)

**Parity status:** ⚠️ PARTIAL - See analysis below

---

### 2. `lint-and-format-checker.yml`
**Purpose:** Runs linting and formatting checks for all languages

**Jobs:**
- `lint-python`: Black + Ruff + Pylint
- `lint-bash`: ShellCheck + shfmt
- `lint-powershell`: PSScriptAnalyzer
- `lint-perl`: Perl::Critic

**Triggers:**
- Push to main
- Pull requests to main
- Manual dispatch

**Features:**
- Auto-format with Black (same-repo PRs only)
- Patch artifact for fork PRs
- Parallel execution per language
- File detection (skips if no files exist)

**Parity status:** ✅ FULL - See analysis below

---

### 3. `yaml-lint.yml`
**Purpose:** YAML linting with yamllint

**What it does:**
- Runs yamllint on all YAML files
- Single job

**Parity status:** ✅ FULL - Umbrella workflow has YAML job

---

## Umbrella Workflow Coverage

### File: `.github/workflows/repo-lint-and-docstring-enforcement.yml`

**Jobs:**
1. **Auto-Fix: Black** - Runs first, applies Black formatting
2. **Detect Changed Files** - Determines which language buckets changed
3. **Repo Lint: Python** - Runs `python -m tools.repo_lint check --ci --only python`
4. **Repo Lint: Bash** - Runs `python -m tools.repo_lint check --ci --only bash`
5. **Repo Lint: PowerShell** - Runs `python -m tools.repo_lint check --ci --only powershell`
6. **Repo Lint: Perl** - Runs `python -m tools.repo_lint check --ci --only perl`
7. **Repo Lint: YAML** - Runs `python -m tools.repo_lint check --ci --only yaml`
8. **Consolidate and Archive Logs** - Collects all outputs

**Conditional Execution:**
- Language jobs run ONLY when:
  - Files for that language changed, OR
  - `shared_tooling` changed, OR
  - `force_all=true` (manual override)

**Shared Tooling Triggers:**
Changes to:
- `tools/repo_lint/`
- `scripts/validate_docstrings.py`
- `scripts/docstring_validators/`
- `pyproject.toml`
- `.github/workflows/`
- `docs/contributing/`

---

## Parity Analysis

### ✅ Linting Coverage (FULL PARITY)

| Tool/Check | Legacy Workflow | Umbrella Workflow | Notes |
|------------|----------------|-------------------|-------|
| Black (Python) | `lint-and-format-checker.yml` | `repo-lint-python` via `tools.repo_lint` | ✅ Same |
| Ruff (Python) | `lint-and-format-checker.yml` | `repo-lint-python` via `tools.repo_lint` | ✅ Same |
| Pylint (Python) | `lint-and-format-checker.yml` | `repo-lint-python` via `tools.repo_lint` | ✅ Same |
| ShellCheck (Bash) | `lint-and-format-checker.yml` | `repo-lint-bash` via `tools.repo_lint` | ✅ Same |
| shfmt (Bash) | `lint-and-format-checker.yml` | `repo-lint-bash` via `tools.repo_lint` | ✅ Same |
| PSScriptAnalyzer (PS) | `lint-and-format-checker.yml` | `repo-lint-powershell` via `tools.repo_lint` | ✅ Same |
| Perl::Critic (Perl) | `lint-and-format-checker.yml` | `repo-lint-perl` via `tools.repo_lint` | ✅ Same |
| yamllint (YAML) | `yaml-lint.yml` | `repo-lint-yaml` via `tools.repo_lint` | ✅ Same |

### ⚠️ Docstring Validation Coverage (PARTIAL PARITY)

| Aspect | Legacy (`docstring-contract.yml`) | Umbrella Workflow | Parity Status |
|--------|-----------------------------------|-------------------|---------------|
| **Scope** | ALL files repository-wide | Per-language (only changed languages) | ⚠️ **DIFFERENT** |
| **Invocation** | `validate_docstrings.py` (no args) | `validate_docstrings.py --language <lang>` per runner | ⚠️ **DIFFERENT** |
| **Trigger** | ANY script/YAML/doc change | Only when language files change (or shared_tooling) | ⚠️ **DIFFERENT** |
| **Fail behavior** | `continue-on-error: true` (warn only) | Hard fail | ⚠️ **DIFFERENT** |

**Key Difference:**
- **Legacy workflow** validates docstrings for ALL files on EVERY run (regardless of what changed)
- **Umbrella workflow** validates docstrings only for languages with changes (more efficient, but different scope)

**Impact:**
- If a Python file changes, umbrella workflow validates Python docstrings only
- Legacy workflow would validate Python + Bash + PowerShell + Perl + YAML docstrings (everything)
- Umbrella approach is more efficient but could miss cross-language docstring drift

**Mitigation:**
- `shared_tooling` flag triggers ALL language jobs when `scripts/validate_docstrings.py` changes
- `force_all=true` manual override runs all language jobs
- For merge to main, all docstrings are eventually validated (just not on every PR if unrelated)

### ✅ Auto-Fix Behavior (FULL PARITY)

| Feature | Legacy | Umbrella | Notes |
|---------|--------|----------|-------|
| Black auto-format | ✅ In `lint-python` job | ✅ In `Auto-Fix: Black` job | Same behavior |
| Same-repo only | ✅ Yes | ✅ Yes | Same |
| Fork patch artifact | ✅ Yes | ✅ Yes | Same |
| Bot-loop guard | ⚠️ Partial (actor only) | ✅ Full (actor + message marker) | **Umbrella is better** |

---

## Recommendations for Sub-Item 6.4.7 (Migration)

### Option A: Keep Both (Transitional)
**Pros:**
- Zero risk during transition
- Legacy provides full-scope docstring validation
- Umbrella provides efficient CI

**Cons:**
- Redundant CI runs
- Confusing for contributors
- Double maintenance burden

**Verdict:** ❌ Not sustainable long-term

---

### Option B: Migrate Fully + Add Periodic Full Scan
**Approach:**
1. Disable legacy workflows (`docstring-contract.yml`, `lint-and-format-checker.yml`, `yaml-lint.yml`)
2. Use umbrella workflow as canonical gate
3. Add weekly scheduled full-scan job that runs `repo-lint check --ci` (all languages, no conditional)
   - Recommended frequency: Weekly (every Monday at 00:00 UTC)
   - Covers cross-language docstring drift without slowing PR workflow

**Pros:**
- Single source of truth (umbrella)
- Efficient per-PR CI
- Periodic full validation catches drift
- Clean migration path

**Cons:**
- Docstring drift could go undetected between scheduled runs
- Requires adding scheduled workflow

**Verdict:** ✅ RECOMMENDED

---

### Option C: Add `--all` Flag to Umbrella Workflow
**Approach:**
1. Add `validate_all_docstrings` input to umbrella workflow (boolean, default: false)
2. When true, run full docstring validation (all languages) as separate job
3. Make this required for merges to `main` branch only (not feature PRs)

**Pros:**
- Per-PR CI remains efficient (conditional)
- Main branch gets full validation
- No separate scheduled workflow needed

**Cons:**
- Adds complexity to umbrella workflow
- Main branch merges slower

**Verdict:** ✅ VIABLE ALTERNATIVE

---

## Next Steps

1. **Verify umbrella workflow in CI** (Sub-Item 6.4.9)
   - Trigger workflow on this PR
   - Test conditional execution
   - Compare results with legacy workflows

2. **Choose migration strategy** (Sub-Item 6.4.7)
   - Get human approval for Option B or Option C
   - Document transition plan
   - Communicate to team

3. **Execute migration** (Sub-Item 6.4.7)
   - Disable legacy workflows
   - Update CONTRIBUTING.md if needed
   - Monitor first few PRs after migration

4. **Update epic-repo-lint-status.md**
   - Document migration complete
   - Mark Sub-Items 6.4.7 and 6.4.9 as done
