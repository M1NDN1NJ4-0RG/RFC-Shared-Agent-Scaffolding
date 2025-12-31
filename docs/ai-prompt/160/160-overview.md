# Issue 160 Overview
Last Updated: 2025-12-31
Related: Issue #160, PRs TBD

## Original Issue
# [EPIC] - `repo_lint` Improvement Plan

This plan outlines prioritized phases to address all findings. Each item includes context, affected components, and suggested fixes.

---

## Phase 1 – Critical Fixes and Corrections (High Priority)

- [ ] **Fix repository root detection** (Severity: **High**)  
  - **Context:** `get_repo_root()` and `find_repo_root()` currently require a `.git` directory, causing failures outside Git worktrees.  
  - **Affected Files:** `tools/repo_lint/install/install_helpers.py`, `tools/repo_lint/runners/base.py` (or wherever `find_repo_root` is defined).  
  - **Fix Steps:** Modify these functions to check for `.git` but **if not found**, return the current working directory as root (or use an environment override). For example:

    ~~~python
    root = current
    while current != current.parent:
        if (current / ".git").exists():
            root = current
            break
        current = current.parent
    return root
    ~~~

    Ensure `find_repo_root` in all runners uses this updated logic.  
  - **Rationale:** Allows `repo_lint` to run in directories without Git, matching user expectations.

- [ ] **Clarify exit codes for unsafe mode** (Severity: **High**)  
  - **Context:** `repo_lint fix --unsafe` in CI or without `--yes-i-know` uses exit code 2 ("Missing tools"), which is misleading.  
  - **Affected Files:** `tools/repo_lint/cli.py`, in `cmd_fix`.  
  - **Fix Steps:** Introduce a new exit code (e.g. `ExitCode.UNSAFE_VIOLATION = 4`) or reuse code 3 for policy errors. Change the `return ExitCode.MISSING_TOOLS` on lines 22 and 36 of `cmd_fix` to this new code. Update `ExitCode` enum accordingly. Adjust help text to note this code.  
  - **Rationale:** Distinguishes configuration errors from missing tools, making CI logs clearer.

- [ ] **Handle partial install failures gracefully** (Severity: **Medium**)  
  - **Context:** In `cmd_install`, if Python tool installation fails, the script still prints next-step instructions but ends with an error. This could confuse users.  
  - **Affected Files:** `tools/repo_lint/cli.py`, lines around 45–60 in `cmd_install`.  
  - **Fix Steps:** Change logic so that the overall success flag (`success`) is computed across all sections: if Python tools or any manual section fails, show errors but consider whether to continue. For example, do **not** `return ExitCode.INTERNAL_ERROR` immediately upon Python failure; instead, gather errors and only exit at end. Alternatively, exit early but skip printing irrelevant instructions. Update output messages accordingly.  
  - **Rationale:** Improves user experience during tool setup and makes failure reasons clear.

- [ ] **Ensure missing docstring validator is detected** (Severity: **Medium**)  
  - **Context:** If `validate_docstrings.py` is missing, runners return a violation with an "script not found" error. This may be unclear.  
  - **Affected Files:** `tools/repo_lint/runners/*_runner.py` (each `_run_docstring_validation` implementation).  
  - **Fix Steps:** In `_run_docstring_validation` methods, catch the "script not found" case explicitly. Print a clear error (`"Docstring validation skipped: script not found"`). Optionally, raise a `MissingToolError`. Document this case in README.  
  - **Rationale:** Makes it obvious when docstring checks are not executed.

- [ ] **Validate non-Python unsafe mode behavior** (Severity: **Medium**)  
  - **Context:** The `--unsafe` fix path only processes Python files. If a user passes `--only=perl` with `--unsafe`, the logic will not handle it.  
  - **Affected Files:** `tools/repo_lint/cli.py`, `cmd_fix` unsafe section.  
  - **Fix Steps:** Restrict `--unsafe` to only allow `--only=python` (error out otherwise), or extend unsafe fixer support to other languages (if implemented). At minimum, add a check:

    ~~~python
    if unsafe_mode and args.only and args.only != "python":
        print("❌ Unsafe fixes not supported for this language", file=sys.stderr)
        return ExitCode.MISSING_TOOLS
    ~~~

  - **Rationale:** Prevents silent no-op when unsupported combinations are requested.

- [ ] **Add missing unit tests for error conditions** (Severity: **Low**)  
  - **Context:** Key error branches (missing tools, missing policy file, unsafe mode cases) lack automated tests.  
  - **Affected Files:** Add to `tools/repo_lint/tests/`.  
  - **Fix Steps:** Write tests using `pytest` to simulate: invoking `repo_lint check` without tools (expect exit code 2), `repo_lint fix` with `--unsafe` in CI (exit 2), missing policy (exit 3), etc. Use subprocess calls or invoke `main()` directly.  
  - **Rationale:** Catches regressions early and ensures CLI behavior is documented.

---

## Phase 2 – Major Enhancements and Alignments (Medium Priority)

- [ ] **Make `repo_lint` an installable package** (Severity: **Medium**)  
  - **Context:** Future Work (FW-013) calls for packaging the tool.  
  - **Affected Files:** Project root. Need a `pyproject.toml` or `setup.py`, and modify code as needed.  
  - **Fix Steps:**  
    - Create `pyproject.toml` (or `setup.py`) with package metadata, including `tools/repo_lint` as a module.  
    - Define entry point:

      ~~~toml
      [project.scripts]
      repo-lint = "tools.repo_lint.cli:main"
      ~~~

    - (Alternatively, setuptools `entry_points` in `setup.py`.)  
    - Remove reliance on `python3 -m tools.repo_lint` in docs; update to `repo-lint` command.  
    - Ensure `__main__.py` is present or remove if using entry points.  
  - **Rationale:** Improves usability (one can `pip install -e .`) and aligns with future plan.

- [ ] **Integrate naming-and-style enforcement** (Severity: **Medium**)  
  - **Context:** The future work suggests `repo_lint` should enforce filename conventions (kebab-case, etc.). Currently, naming checks are done via CI or manual scripts, not by `repo_lint`.  
  - **Affected Files:** Likely add a new runner or extend an existing one. Could be a new "General" runner that checks all files, or integrate into common checks.  
  - **Fix Steps:**  
    - Define a "NamingRunner" (or add to `common.py`) that loads naming rules (from `docs/contributing/naming-and-style.md` or encode them).  
    - In `check()`, gather all files and verify their names match regex per-language (e.g. Python `.py` files snake_case, non-scripts kebab-case).  
    - Report violations via `LintResult`.  
    - Optionally, add a fix mode: e.g. suggest renames (though renaming with history is non-trivial, so perhaps only report).  
    - Add test fixtures in repo-lint tests for naming violations.  
  - **Rationale:** Automates an important repository convention and prevents drift.

- [ ] **Pin external tool versions in installer** (Severity: **Low**)  
  - **Context:** We have `install/version_pins.py` with desired versions (Black, etc.), but `install_python_tools` currently installs latest (via `requirements-dev.txt`).  
  - **Affected Files:** `tools/repo_lint/install/install_helpers.py` and `install/version_pins.py`.  
  - **Fix Steps:** Use the version pins: in `install_python_tools`, instead of a generic pip install, construct commands like `pip install black=={version}` using the pins. Alternatively, generate a `requirements.txt` with pinned versions. Ensure `pip install .` or `requirements-dev.txt` uses these pins.  
  - **Rationale:** Guarantees deterministic linting behavior.

- [ ] **Improve CLI usability** (Severity: **Low**)  
  - **Context:** Minor enhancements for user experience.  
  - **Affected Files:** `tools/repo_lint/cli.py`, README.  
  - **Fix Steps:**  
    - Add better help text for `--only` and `--yes-i-know`.  
    - Document the `repo-lint` command in the main README or a Usage doc.  
    - Consider allowing configuration file (e.g. `.repo-lint.yaml`) for default options (suggestion, not required by contract).  
  - **Rationale:** Makes tool easier to adopt and reduces on-boarding friction.

---

## Phase 3 – Polish, Nits, and Minor Improvements (Low Priority)

- [ ] **Code style clean-up** (Severity: **Low**)  
  - **Context:** Address minor style issues flagged by linters.  
  - **Affected Files:** All Python files under `tools/repo_lint`.  
  - **Fix Steps:** Run `flake8` or `pylint` on the `repo_lint` package, fix warnings (unused imports, variable names, line lengths). Align formatting with repository norms (e.g. order of imports).  
  - **Rationale:** Improves readability and prevents technical debt.

- [ ] **Add or improve docstrings in the code** (Severity: **Low**)  
  - **Context:** Given the emphasis on contracts and documentation, the code should be thoroughly documented. Some private methods or CLI helpers lack docstrings.  
  - **Affected Files:** Missing or incomplete docstrings (e.g. CLI parser creation, internal helpers).  
  - **Fix Steps:** Audit all public functions/methods in `repo_lint` for missing documentation. Add descriptive docstrings (Purpose, parameters, return values). Align with reST or Google style per the repository's convention.  
  - **Rationale:** Helps future maintainers and ensures consistency with the project's documentation standards.

- [ ] **Update documentation** (Severity: **Low**)  
  - **Context:** Once code changes are done, docs should reflect them. For example, after packaging, update instructions in `CONTRIBUTING.md` and the Future Work tracker to mark FW-013 as addressed. Any new CLI flags or behaviors should be documented.  
  - **Affected Files:** `docs/README.md`, `docs/future-work.md`, `CONTRIBUTING.md`, `tools/repo_lint/README.md`.  
  - **Fix Steps:**  
    - In `docs/future-work.md`, mark FW-013 as complete or remove.  
    - In repo README, add a "Tools" section listing `repo-lint`.  
    - In `CONTRIBUTING.md`, mention running `repo-lint` before PRs.  
    - Ensure all doc links (to examples, RFC, etc.) are up-to-date.  
  - **Rationale:** Keeps documentation accurate and helps onboard contributors.

- [ ] **Test coverage for runners (Optional)** (Severity: **Low**)  
  - **Context:** While we have tests for each runner, they focus on isolated behavior. Integration tests (e.g. simulate a small mixed-language repo) could catch cross-cutting issues.  
  - **Affected Files:** Possibly add new test files.  
  - **Fix Steps:** Create integration tests that run `repo_lint check` on test repos with known violations in multiple languages, verifying combined output.  
  - **Rationale:** Ensures end-to-end functionality remains correct as improvements are made.

---

Each fix above should be committed with clear messages, linking to issues if the repository uses an issue tracker. Prioritize the Phase 1 items immediately, as they address correctness and compliance issues. Phase 2 implements requested features and contract alignments from the "Future Work" document. Phase 3 covers residual improvements and housekeeping.

## Progress Tracker
- [x] Phase 1 – Critical Fixes and Corrections (High Priority) - IN PROGRESS
  - [x] Fix repository root detection - COMPLETED
  - [ ] Clarify exit codes for unsafe mode
  - [ ] Handle partial install failures gracefully
  - [ ] Ensure missing docstring validator is detected
  - [ ] Validate non-Python unsafe mode behavior
  - [ ] Add missing unit tests for error conditions
- [ ] Phase 2 – Major Enhancements and Alignments (Medium Priority)
  - [ ] Make `repo_lint` an installable package
  - [ ] Integrate naming-and-style enforcement
  - [ ] Pin external tool versions in installer
  - [ ] Improve CLI usability
- [ ] Phase 3 – Polish, Nits, and Minor Improvements (Low Priority)
  - [ ] Code style clean-up
  - [ ] Add or improve docstrings in the code
  - [ ] Update documentation
  - [ ] Test coverage for runners (Optional)

## Session Notes (newest first)
### 2025-12-31 00:25 - Completed repository root detection fix
- Fixed `get_repo_root()` and `find_repo_root()` to handle missing .git directory
- Both functions now return current working directory as fallback
- All tests pass, code review passed with no comments
- Ready for PR merge - this is the first item in the epic
- Next session should address: "Clarify exit codes for unsafe mode" (new PR/branch)

### 2025-12-31 00:16 - Initial session
- Created overview and next-steps journal files
- Reviewed repository structure and identified affected files
- Planning to address Phase 1 critical fixes first
