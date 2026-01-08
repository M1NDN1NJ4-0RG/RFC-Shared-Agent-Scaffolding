@copilot

🚨 **MANDATORY FIRST STEP (NO EXCEPTIONS): RUN FULL BOOTSTRAP TOOLCHAIN**
- You MUST run the repo’s documented full bootstrap sequence FIRST.
- Do not begin analysis, debugging, test-writing, or code changes until bootstrap completes successfully.
- Any “verified” statement without bootstrap output is invalid.

---

# TASK: FIX fixture filtering + prove every fixture-related path works (NO HAND-WAVING)

## Primary evidence file (MUST REVIEW IN FULL)
After bootstrap completes, you MUST open and read this file in the repo and treat it as the source-of-truth for current failures:

- `repo-lint-failure-reports/20638414426/python-lint-output.txt`

You MUST extract:
- every fixture-related violation
- every instance where fixture paths appear when they should be excluded
- every instance of runner isolation failure (e.g., cross-language paths leaking)
- any contradictions vs what this PR claims is “done”

---

## Non-negotiable deliverable
You must **IDENTIFY AND FIX** the underlying causes. Do not write a “forensic report” as the primary output. The primary output is:
1) code fixes
2) proof (commands + outputs) that the fixes work

---

## Required verification coverage (ALL PATHS — CI + NORMAL UX)
You MUST verify **every code path in `tools/repo_lint` that can include/exclude fixtures or filter file sets**, across BOTH:
- **CI-only paths** (explicitly `--ci` mode and anything gated by CI behavior), AND
- **normal user UX paths** (local/default behavior without `--ci`, plus typical user CLI flows)

### A) Mode + flag combinations (MUST TEST ALL)
You MUST validate exact file selection results for each of these modes:
- `--ci` (default CI mode)
- `--include-fixtures` (local UX, explicit include)
- neither flag (normal local UX default)
- `--ci` + `--include-fixtures` (explicit override)

**Invariants (MUST ENFORCE):**
- Default `--ci` MUST exclude fixtures everywhere.
- In normal UX mode, fixtures MUST NOT appear unless `--include-fixtures` is explicitly set.
- `--include-fixtures` MUST be the ONLY mechanism that allows fixtures to appear (in any mode).
- If any code path includes fixtures without `--include-fixtures`, that is a FAIL.

### B) File discovery / selection mechanisms (MUST COVER ALL THAT EXIST)
You MUST cover every file-discovery mechanism supported by this repo-lint toolchain in BOTH CI + normal UX contexts:
- “all tracked files”
- “changed-only” / detect-changed path (if supported)
- `--only <language>`
- any vector/conformance mode (if present)
- any direct helper usage paths (e.g., `get_tracked_files(...)`)
- any glob-based filters and any YAML-config-based patterns

### C) Runner isolation + consistency (ALL RUNNERS, ALL MODES)
For each runner (Python/Bash/PowerShell/Perl/YAML/Rust + any shared/meta runners), in BOTH CI + normal UX:
- Assert it only receives files matching its language patterns.
- Assert it never receives files from another language, even if fixtures exist.
- Assert runner `has_files()` logic uses the SAME filtered set as runner execution inputs (no mismatch allowed).
- Assert `check` and `fix` do NOT diverge in selection scope (fix must not broaden inputs).

If you believe an outcome “cannot happen,” you MUST prove it via a test that would fail if it did happen.

---

## Testing requirements (MUST BE UNIT-LEVEL, DETERMINISTIC)
You MUST add or extend unit tests that validate both:
1) **file selection** (exact included/excluded path sets)
2) **runner isolation** (no cross-language leakage)

Existing test file that must remain clean and compliant if modified:
- `tools/repo_lint/tests/test_fixture_vector_mode.py`

Any test files you touch or create MUST pass:
- repo-lint linting
- docstring contract validation

MANDATORY: **Do not commit** until lint + docstrings + tests all pass locally.

---

## Proof required (MUST INCLUDE RAW COMMANDS + OUTPUT SNIPPETS)
Your final response MUST include:

### 1) Bootstrap proof
- The exact bootstrap command(s) you ran
- A success output snippet

### 2) Failure reproduction (before fix)
- The exact command(s) used to reproduce failures from:
  `repo-lint-failure-reports/20638414426/python-lint-output.txt`
- Output snippet showing fixture-related failures BEFORE the fix

### 3) Fix verification (after fix)
- Commands + outputs proving:
  - fixtures are excluded in `--ci` by default
  - fixtures do NOT appear in normal UX mode unless `--include-fixtures` is provided
  - fixtures ONLY appear when `--include-fixtures` is set
  - runner isolation is enforced for ALL runners
  - `has_files()` and execution inputs match
  - `check` and `fix` selection scopes match
- Passing pytest output
- Passing lint + docstring validation output

---

## NO-WIGGLE-RULES
- No “I believe”, “should”, “seems”, or “likely”.
- No claiming completion without command outputs.
- No relying on CI logs for correctness.
- No partial fixes.

---

## Journaling is mandatory (EVERY SESSION, SUCCESS OR FAILURE)
At the end of **EVERY** session (even if everything is fixed and passing), you MUST update this file:

- `docs/ai-prompt/221/221-next-steps.md`

This update MUST include:
- what you did this session (bulleted, concrete)
- what is now verified working (with commands run)
- what remains broken (if anything) and why
- the exact next commands to run and files to inspect for the next session
- acceptance criteria for declaring the work DONE

No exceptions. No “already covered above.” The journal must stand alone.

---

## Session limit contingency (MANDATORY)
If you are approaching session/context limits before completing this task:

1) **STOP making changes immediately.**
2) Write **EXTREMELY DETAILED** next steps into **THIS FILE** (no substitutes, no summaries):
   - `docs/ai-prompt/221/221-next-steps.md`
3) The next steps MUST include:
   - exact files to open
   - exact functions to inspect
   - exact commands to run to reproduce
   - exact hypotheses to validate or falsify
   - exact tests to add or extend (with matrix coverage)
   - explicit acceptance criteria for declaring the task DONE

These instructions must allow a new session to resume work immediately with zero interpretation or guesswork.
