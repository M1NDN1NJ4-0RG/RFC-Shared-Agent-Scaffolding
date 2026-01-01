@copilot 🚨 **MANDATORY FIRST STEP (NON-NEGOTIABLE): RUN THE FULL BOOTSTRAP TOOLCHAIN**

**Do not write tests. Do not claim fixes. Do not analyze.**  
Run the repo’s documented bootstrap sequence **FIRST**, and paste the **exact commands + success output snippet**.

---

# 🔥 BLOCKER: Fixtures/Vectors are leaking into `--ci` mode

I am looking at **repo-lint-failure-reports/20639029827/python-lint-output.txt** and it shows **fixture/vector violation files being linted** in CI mode. Example files in the output include:

- `all_docstring_violations.py`
- `black_violations.py`
- `pylint_violations.py`
- `ruff_violations.py`
- `naming-violations.py`

These are fixture/vector files and **MUST NOT** appear in `--ci` mode or normal user mode unless `--include-fixtures` is explicitly set.

---

# ✅ REQUIRED BEHAVIOR (INVARIANTS)

1. **Default `--ci` MUST exclude fixtures everywhere.**
2. **`--include-fixtures` MUST be the only way fixtures appear (in any mode).**
3. If fixtures appear without `--include-fixtures`, that is a **FAIL**.
4. **Runner isolation MUST hold**:
   - Python runner never receives Rust files
   - Rust runner never receives Python files
   - etc. for all supported runners

---

# 🧪 REQUIRED DELIVERABLE: EXHAUSTIVE FIXTURE/ISOLATION TEST MATRIX

Create a **unit test suite** under `tools/repo_lint/tests/` that validates *computed file lists* (no external tool execution; no CI log parsing).

The suite MUST cover the full matrix:

## A) Flag combos (fixtures)
For each selection mode below, assert the **exact final file set**:
- `--ci`
- `--include-fixtures`
- neither flag (local default)
- `--ci --include-fixtures`

## B) Runners (ALL of them)
For each runner (Python/Bash/PowerShell/Perl/YAML/Rust + any meta/shared runners):
- Assert it only receives files matching its language patterns
- Assert it never receives another language’s files
- Assert `has_files()` is based on the **same filtered file set** as execution

## C) Selection modes (ALL discovery paths)
Cover every file-discovery mechanism present:
- “all tracked files”
- “changed-only” / detect-changed path (if present)
- `--only <language>`
- any “vector mode / conformance” path
- any direct `get_tracked_files(...)` usage
- glob-based filters + YAML-config-based patterns

## D) Fixture path + glob edge cases
Fixtures must be excluded/included correctly for:
- nested fixtures directories
- fixtures that match language globs (`**/*.py`, `**/*.rs`, etc.)
- fixture names resembling real files (`*_runner.py`, `*_violations.*`)
- “surprising” fixture locations (if supported)
- case-sensitivity edge cases (if relevant)
- hyphen/underscore/mixed naming patterns

## E) Prove “impossible” outcomes are impossible
Add tests proving:
- Python files cannot appear in Rust inputs
- Rust files cannot appear in Python inputs
- Fixtures cannot appear in CI without `--include-fixtures`
- Runner-specific code paths cannot bypass exclusions

## F) Regression traps
Add tests for:
- double exclusion / duplicate filtering bugs
- missing imports / NameError in runners (e.g., `get_tracked_files`)
- mismatch between `has_files()` and actual execution file list
- mismatch between `check` and `fix` selection (fix must not broaden scope)

---

# 🧾 PROOF REQUIRED IN YOUR RESPONSE

After implementing, you MUST provide:

1. **Bootstrap commands** you ran + **success output snippet**
2. **Exact test commands** you ran
3. A brief summary of the **coverage matrix** (flag combos × runners × selection modes)
4. Evidence that tests **fail before the fix** (if any code changes required) and **pass after**

---

# 🚫 HARD STOP

Do NOT claim “complete” unless the test suite explicitly covers:
- **all runners**
- **all selection modes**
- **all flag combos**
- **negative “impossible outcome” proofs**
- **edge-case fixture paths/globs**

Now: run bootstrap, paste output, then implement the matrix tests + fix the leak.
