# Issue 160 Overview

Last Updated: 2026-01-01
Related: Issue #160, PRs TBD

## ✅ LOCKED-IN HUMAN DECISIONS (Authoritative)

**Decision Owner:** Human (Ryan)
**Decision Dates:** 2025-12-31 (Rounds 1 & 2)

These decisions are **final and binding** for all Issue #160 work. All implementation MUST comply with these decisions.

### Round 1 Decisions (Phase 2 & 3) - ALL APPROVED ✅

1. 1. **Package `repo_lint` as installable tool** → YES (COMPLETE) 2. 2. **Add naming/style enforcement** → YES,
   check-only, external YAML + strict validation (COMPLETE) 3. **Pin external tool versions** → YES (COMPLETE) 4. **CLI
   usability improvements** → YES, Click + Rich + autocomplete + HOW-TO (COMPLETE) 5. **Code style clean-up** → YES with
   guardrails (Phase 3, DEFERRED) 6. **Comprehensive docstring audit** → YES (Phase 3, DEFERRED) 7. **Documentation
   updates** → YES (Phase 3, DEFERRED) 8. **Integration tests for runners** → YES (Phase 3, DEFERRED)

### Round 2 Decisions (Phase 2.5-2.9) - ALL APPROVED ✅

1. 1. 1. **Phase 2.5 Windows Validation** → Hybrid approach (CI-first validation) ✅ COMPLETE 2. **Phase 2.6-2.9
   Prioritization** → Sequential: 2.5 blockers → 2.9 → 2.7 → 2.8 → 2.6 → 3 3. **YAML-First Configuration Scope** →
   Aggressive migration while preserving contracts 4. **Exception System Pragma Policy** → Warn by default
   (configurable), YAML precedence, migration tool 5. **CLI Granularity vs Complexity** → Implement full flag set with
   strong UX (Rich-Click panels) 6. **Output Format Support** → Full suite: json, yaml, csv, xlsx (single normalized
   data model) 7. **`repo-lint doctor` Command Scope** → Minimum checks, check-only (no auto-fix) 8. 8. **Environment
   Commands** → Required, implement all three: which → env → activate 9. **Phase 2.9 Timing** → Must be implemented
   BEFORE Phase 2.6-2.8 (after Phase 2.5 blockers) 10. **Testing Strategy** → Standard coverage, tests before review,
   Windows CI where relevant

---

## Original Issue

# [EPIC] - `repo_lint` Improvement Plan

This plan outlines prioritized phases to address all findings. Each item includes context, affected components, and
suggested fixes.

**NOTE:** All work MUST comply with the Locked-In Human Decisions above.

---

## Phase 1 – Critical Fixes and Corrections (High Priority)

- - - [x] **Fix repository root detection** (Severity: **High**) - **Context:** `get_repo_root()` and `find_repo_root()`
  currently require a `.git` directory, causing failures outside Git worktrees. - **Affected Files:**
  `tools/repo_lint/install/install_helpers.py`, `tools/repo_lint/runners/base.py` (or wherever `find_repo_root` is
  defined). - **Fix Steps:** Modify these functions to check for `.git` but **if not found**, return the current working
  directory as root (or use an environment override). For example:

~~~python root = current while current != current.parent: if (current / ".git").exists(): root = current break current =
current.parent return root ~~~

    Ensure `find_repo_root` in all runners uses this updated logic.
  - **Rationale:** Allows `repo_lint` to run in directories without Git, matching user expectations.

- - [x] **Clarify exit codes for unsafe mode** (Severity: **High**)
  - **Context:** `repo_lint fix --unsafe` in CI or without `--yes-i-know` uses exit code 2 ("Missing tools"), which is misleading.
  - **Affected Files:** `tools/repo_lint/cli.py`, in `cmd_fix`.
  - **Fix Steps:** Introduce a new exit code (e.g. `ExitCode.UNSAFE_VIOLATION = 4`) or reuse code 3 for policy errors. Change the `return ExitCode.MISSING_TOOLS` on lines 22 and 36 of `cmd_fix` to this new code. Update `ExitCode` enum accordingly. Adjust help text to note this code.
  - - **Rationale:** Distinguishes configuration errors from missing tools, making CI logs clearer.

- - [x] **Handle partial install failures gracefully** (Severity: **Medium**)
  - **Context:** In `cmd_install`, if Python tool installation fails, the script still prints next-step instructions but ends with an error. This could confuse users.
  - **Affected Files:** `tools/repo_lint/cli.py`, lines around 45–60 in `cmd_install`.
  - **Fix Steps:** Change logic so that the overall success flag (`success`) is computed across all sections: if Python tools or any manual section fails, show errors but consider whether to continue. For example, do **not** `return ExitCode.INTERNAL_ERROR` immediately upon Python failure; instead, gather errors and only exit at end. Alternatively, exit early but skip printing irrelevant instructions. Update output messages accordingly.
  - - **Rationale:** Improves user experience during tool setup and makes failure reasons clear.

- - [x] **Ensure missing docstring validator is detected** (Severity: **Medium**)
  - **Context:** If `validate_docstrings.py` is missing, runners return a violation with an "script not found" error. This may be unclear.
  - **Affected Files:** `tools/repo_lint/runners/*_runner.py` (each `_run_docstring_validation` implementation).
  - **Fix Steps:** In `_run_docstring_validation` methods, catch the "script not found" case explicitly. Print a clear error (`"Docstring validation skipped: script not found"`). Optionally, raise a `MissingToolError`. Document this case in README.
  - - **Rationale:** Makes it obvious when docstring checks are not executed.

- - [x] **Validate non-Python unsafe mode behavior** (Severity: **Medium**)
  - **Context:** The `--unsafe` fix path only processes Python files. If a user passes `--only=perl` with `--unsafe`, the logic will not handle it.
  - **Affected Files:** `tools/repo_lint/cli.py`, `cmd_fix` unsafe section.
  - **Fix Steps:** Restrict `--unsafe` to only allow `--only=python` (error out otherwise), or extend unsafe fixer support to other languages (if implemented). At minimum, add a check:

~~~python if unsafe_mode and args.only and args.only != "python": print("❌ Unsafe fixes not supported for this
language", file=sys.stderr) return ExitCode.MISSING_TOOLS ~~~

  - - - **Rationale:** Prevents silent no-op when unsupported combinations are requested.

- - - [x] **Add missing unit tests for error conditions** (Severity: **Low**) - **Context:** Key error branches (missing
  tools, missing policy file, unsafe mode cases) lack automated tests. - **Affected Files:** Add to
  `tools/repo_lint/tests/`. - **Fix Steps:** Write tests using `pytest` to simulate: invoking `repo_lint check` without
  tools (expect exit code 2), `repo_lint fix` with `--unsafe` in CI (exit 2), missing policy (exit 3), etc. Use
  subprocess calls or invoke `main()` directly. - - **Rationale:** Catches regressions early and ensures CLI behavior is
  documented.

---

## Phase 2 – Major Enhancements and Alignments (Medium Priority)

- - [x] **Make `repo_lint` an installable package** (Severity: **Medium**) - - **Context:** Future Work (FW-013) calls
  for packaging the tool. - **Affected Files:** Project root. Need a `pyproject.toml` or `setup.py`, and modify code as
  needed. - - **Fix Steps:** - Create `pyproject.toml` (or `setup.py`) with package metadata, including
  `tools/repo_lint` as a module. - Define entry point:

      ~~~toml
      [project.scripts]
      repo-lint = "tools.repo_lint.cli:main"
      ~~~

- (Alternatively, setuptools `entry_points` in `setup.py`.) - Remove reliance on `python3 -m tools.repo_lint` in docs;
update to `repo-lint` command. - Ensure `__main__.py` is present or remove if using entry points. - **Rationale:**
Improves usability (one can `pip install -e .`) and aligns with future plan.

- - - [x] **Integrate naming-and-style enforcement** (Severity: **Medium**) - **Context:** The future work suggests
  `repo_lint` should enforce filename conventions (kebab-case, etc.). Currently, naming checks are done via CI or manual
  scripts, not by `repo_lint`. - - **Affected Files:** Likely add a new runner or extend an existing one. Could be a new
  "General" runner that checks all files, or integrate into common checks. - **Fix Steps:** - Define a "NamingRunner"
  (or add to `common.py`) that loads naming rules (from `docs/contributing/naming-and-style.md` or encode them). - In
  `check()`, gather all files and verify their names match regex per-language (e.g. Python `.py` files snake_case,
  non-scripts kebab-case). - Report violations via `LintResult`. - Optionally, add a fix mode: e.g. suggest renames
  (though renaming with history is non-trivial, so perhaps only report). - Add test fixtures in repo-lint tests for
  naming violations. - **Rationale:** Automates an important repository convention and prevents drift.

- - - [x] **Pin external tool versions in installer** (Severity: **Low**) - **Context:** We have
  `install/version_pins.py` with desired versions (Black, etc.), but `install_python_tools` currently installs latest
  (via `requirements-dev.txt`). - **Affected Files:** `tools/repo_lint/install/install_helpers.py` and
  `install/version_pins.py`. - **Fix Steps:** Use the version pins: in `install_python_tools`, instead of a generic pip
  install, construct commands like `pip install black=={version}` using the pins. Alternatively, generate a
  `requirements.txt` with pinned versions. Ensure `pip install .` or `requirements-dev.txt` uses these pins. - -
  **Rationale:** Guarantees deterministic linting behavior.

- - - [x] **Improve CLI usability** (Severity: **Low**) - **Context:** Minor enhancements for user experience. -
  **Affected Files:** `tools/repo_lint/cli.py`, README. - - **Fix Steps:** - Add better help text for `--only` and
  `--yes-i-know`. - Document the `repo-lint` command in the main README or a Usage doc. - Consider allowing
  configuration file (e.g. `.repo-lint.yaml`) for default options (suggestion, not required by contract). - -
  **Rationale:** Makes tool easier to adopt and reduces on-boarding friction.

---

## Phase 3 – Polish, Nits, and Minor Improvements (Low Priority)

- - - [ ] **Code style clean-up** (Severity: **Low**) - **Context:** Address minor style issues flagged by linters. -
  **Affected Files:** All Python files under `tools/repo_lint`. - **Fix Steps:** Run `flake8` or `pylint` on the
  `repo_lint` package, fix warnings (unused imports, variable names, line lengths). Align formatting with repository
  norms (e.g. order of imports). - - **Rationale:** Improves readability and prevents technical debt.

- - - [ ] **Add or improve docstrings in the code** (Severity: **Low**) - **Context:** Given the emphasis on contracts
  and documentation, the code should be thoroughly documented. Some private methods or CLI helpers lack docstrings. -
  **Affected Files:** Missing or incomplete docstrings (e.g. CLI parser creation, internal helpers). - **Fix Steps:**
  Audit all public functions/methods in `repo_lint` for missing documentation. Add descriptive docstrings (Purpose,
  parameters, return values). Align with reST or Google style per the repository's convention. - - **Rationale:** Helps
  future maintainers and ensures consistency with the project's documentation standards.

- - - [ ] **Update documentation** (Severity: **Low**) - **Context:** Once code changes are done, docs should reflect
  them. For example, after packaging, update instructions in `CONTRIBUTING.md` and the Future Work tracker to mark
  FW-013 as addressed. Any new CLI flags or behaviors should be documented. - **Affected Files:** `docs/README.md`,
  `docs/future-work.md`, `CONTRIBUTING.md`, `tools/repo_lint/README.md`. - - **Fix Steps:** - In `docs/future-work.md`,
  mark FW-013 as complete or remove. - In repo README, add a "Tools" section listing `repo-lint`. - In
  `CONTRIBUTING.md`, mention running `repo-lint` before PRs. - Ensure all doc links (to examples, RFC, etc.) are
  up-to-date. - **Rationale:** Keeps documentation accurate and helps onboard contributors.

- - - [ ] **Test coverage for runners (Optional)** (Severity: **Low**) - **Context:** While we have tests for each
  runner, they focus on isolated behavior. Integration tests (e.g. simulate a small mixed-language repo) could catch
  cross-cutting issues. - **Affected Files:** Possibly add new test files. - **Fix Steps:** Create integration tests
  that run `repo_lint check` on test repos with known violations in multiple languages, verifying combined output. - -
  **Rationale:** Ensures end-to-end functionality remains correct as improvements are made.

---

## Phase 2.5 – Rich UI "Glow Up" for Console Output + Rich-Click Help (CORE COMPLETE ✅)

**Goal:** Make `repo-lint` feel like a polished terminal application with professional-grade UI.

- - - [x] **Add UI/Reporter Layer** (Severity: **High**) - **Context:** All user-facing output should be routed through
  a single authoritative UI/reporting interface. - **Affected Files:** New:
  `tools/repo_lint/ui/{__init__,console,reporter,theme}.py` - **Implementation:** Created Reporter with methods:
  `render_header()`, `runner_started()`, `runner_completed()`, `render_results_table()`, `render_failures()`,
  `render_final_summary()`, `render_config_validation_errors()` - - **Status:** ✅ COMPLETE

- - - [x] **Extend Data Model for Results** (Severity: **High**) - **Context:** Need consistent results model for Rich
  table generation. - **Affected Files:** `tools/repo_lint/common.py` - **Implementation:** Extended `LintResult` with
  `file_count` and `duration` fields - - **Status:** ✅ COMPLETE

- - - [x] **Implement Results Rendering** (Severity: **High**) - **Context:** Rich tables/panels for interactive mode,
  stable output for CI mode. - **Affected Files:** `tools/repo_lint/ui/reporter.py`, `tools/repo_lint/reporting.py` - -
  **Implementation:** Reporter renders Rich tables in TTY mode, plain tables in CI mode - **Status:** ✅ COMPLETE

- - - [x] **Integrate Reporter into CLI** (Severity: **High**) - **Context:** Replace all direct prints with Reporter
  calls. - **Affected Files:** `tools/repo_lint/cli_argparse.py`, `tools/repo_lint/reporting.py` - **Implementation:**
  All output routes through Reporter; `ci_mode` flag passed through - - **Status:** ✅ COMPLETE

- - - [x] **Rich-Click Integration** (Severity: **High**) - **Context:** Beautiful help output with styled headings,
  option groups, examples. - **Affected Files:** `tools/repo_lint/cli.py`, `pyproject.toml` - - **Implementation:**
  Click-based CLI with Rich-Click styling, comprehensive help, option grouping - **Status:** ✅ COMPLETE

- - - [x] **Theme System** (Severity: **Medium**) - **Context:** User-configurable YAML theme for colors/icons/box
  styles/help formatting. - **Affected Files:** New: `conformance/repo-lint/repo-lint-ui-theme.yaml`,
  `tools/repo_lint/ui/theme.py` - - **Implementation:** YAML theme config with strict validation; precedence: flag > env
  > user config > default - **Status:** ✅ COMPLETE

- - - [x] **Update Tests for Rich Format** (Severity: **Medium**) - **Context:** `test_output_format.py` expects plain
  text; now outputs Rich tables. - **Affected Files:** `tools/repo_lint/tests/test_output_format.py` - - **Status:** ✅
  COMPLETE

- - - [x] **Windows Validation** (Severity: **High** - BLOCKER) - **Context:** MUST validate on Windows PowerShell,
  PowerShell 7+, Windows Terminal. - **Affected Files:** N/A (validation/testing task) - **Validation Required:** Help
  rendering, shell completion, stable CI output - **Status:** ✅ COMPLETE - CI validation added

- - - [x] **Documentation Updates** (Severity: **Medium**) - **Context:** Update HOW-TO with theme customization,
  Windows completion instructions. - **Affected Files:** `tools/repo_lint/HOW-TO-USE-THIS-TOOL.md` - - **Status:** ✅
  COMPLETE

**Rationale:** Professional UI significantly improves user experience. CI mode maintains determinism.

---

## Phase 2.6 – Centralized Exception Rules (Planned, NOT STARTED)

**Goal:** Add a strict, centralized YAML "exceptions roster" that declares *what to ignore, where, and why* — with
strong validation, auditability, and predictable CI behavior — **without removing pragma support**.

**Core Principle:** Exceptions are **data**, not **inline code graffiti**. Pragmas remain supported (backward
compatible). The YAML exceptions file becomes a first-class alternative (and preferred in docs).

- - - [ ] **Create Exceptions Schema & Validator** (Severity: **High**) - **Context:** Need centralized YAML config for
  ignore/exceptions with strict validation. - **Affected Files:** New:
  `conformance/repo-lint/repo-lint-exceptions.yaml`, `tools/repo_lint/conformance/exceptions_schema.py` - -
  **Requirements:** - YAML MUST have `---` and `...` markers - MUST include `config_type: repo-lint-exceptions` and
  `version: 1` - Unknown keys at any depth are hard errors - Each exception MUST include: `id`, `scope`, `ignores`,
  `reason`, `owner`, `created`, `expires`, `tracking` - Anti-Typo Contract: tools/codes MUST match known values from
  conformance configs - **Rationale:** Centralized exceptions are auditable, expirable, and have clear ownership.

- - - [ ] **Integrate Exceptions into Results & Reporting** (Severity: **High**) - **Context:** Filter violations via
  exceptions YAML before reporting; track ignored counts. - **Affected Files:** Results model, reporting layer -
  **Requirements:** - Violations carry metadata: tool, code, file, symbol - Filter violations before reporting - Track:
  original vs ignored vs remaining counts - CI FAIL on expired exceptions; TTY shows red panel - **Rationale:** Makes
  exception usage visible and prevents expired exceptions from going stale.

- - - [ ] **Keep Pragma Support & Add Conflict Detection** (Severity: **High**) - **Context:** Pragmas remain fully
  supported; YAML is additional mechanism. - **Affected Files:** CLI, runners - **Requirements:** - Pragmas remain
  supported (no breaking changes) - Add pragma warning toggle (configurable) - If YAML + pragma conflict → ALWAYS warn
  (even if warnings disabled) - Precedence: YAML exceptions > pragmas (deterministic) - **Rationale:** Backward
  compatibility while encouraging centralized approach.

- - - [ ] **Implement Symbol/Scope Matching** (Severity: **Medium**) - **Context:** Exceptions need to target specific
  modules, classes, functions, files, paths, globs. - **Affected Files:** Exception application logic -
  **Requirements:** - Python: module + qualified name matching - PowerShell/Bash/Perl/Rust: file/path scoping (AST
  symbol optional) - Regex matching with explicit anchoring requirements - **Rationale:** Precise targeting prevents
  over-broad exceptions.

- - - [ ] **Add Documentation for Exceptions** (Severity: **Medium**) - **Context:** Users need clear guidance on YAML
  exceptions vs pragmas. - **Affected Files:** `tools/repo_lint/HOW-TO-USE-THIS-TOOL.md` - - **Requirements:** - Add
  "Exceptions YAML" section with schema examples - Document "Pragmas remain supported" explicitly - Document pragma
  warning toggle behavior - Document conflict rules and precedence - **Rationale:** Clear documentation ensures adoption
  and correct usage.

- - - [ ] **Add Exception Tests** (Severity: **High**) - **Context:** Validate exception application, expiration,
  conflicts. - **Affected Files:** New test files - **Requirements:** - Validator tests: missing markers, wrong
  config_type, bad regex, expired exceptions - Integration tests: violations + exceptions (counts verified), pragma +
  YAML conflicts - **Rationale:** Ensures exceptions work correctly and catch regressions.

**Rationale:** Centralized exceptions with expiration and audit trails prevent "eternal mold" and improve
maintainability.

---

## Phase 2.7 – Extended CLI Granularity & Reporting ✅ COMPLETE (8/8 items)

**Status:** COMPLETE ✅
**Last Updated:** 2026-01-05

**Goal:** Add extremely granular CLI options for filtering, output control, and robust reporting.

**Mandatory Features:**

- - - [x] **Add Language and Tool Filtering** (Severity: **High**) ✅ COMPLETE - **Context:** Users need to run specific
  tools on specific languages. - **Implementation:** `tools/repo_lint/cli.py`, runner base classes - - **Delivered:** -
  ✅ `--lang <LANG>`: filter to single language (python, bash, perl, powershell, rust, yaml, all) - ✅ `--tool <TOOL>`:
  filter to specific tool(s) - repeatable - ✅ Tool availability validation with correct exit codes - ✅ Missing tools
  exit with code 2 - **Testing:** 25/25 Phase 2.7 tests pass

- - - [x] **Add Summary Modes** (Severity: **High**) ✅ COMPLETE (FIXED Critical Bug) - **Context:** Users need different
  levels of output detail. - **Implementation:** `tools/repo_lint/reporting.py`, `tools/repo_lint/ui/reporter.py` - -
  **Delivered:** - ✅ `--summary`: normal output + compact summary at end - ✅ `--summary-only`: ONLY compact summary (no
  per-file details) - ✅ `--summary-format <MODE>`: short, by-tool, by-file, by-code (all 4 modes working) - - **Bug
  Fixed:** Rich markup error in CI mode causing MarkupError (empty color tags) - **Testing:** All summary mode tests
  pass

- - - [x] **Add Verbosity Controls** (Severity: **Medium**) ✅ COMPLETE - **Context:** Prevent terminal spam; allow
  fine-tuned output. - **Implementation:** `tools/repo_lint/reporting.py`, `tools/repo_lint/ui/reporter.py` - -
  **Delivered:** - ✅ `--max-violations <N>`: hard cap for detailed items printed - ✅ `--show-files` / `--hide-files`:
  per-file breakdown control - ✅ `--show-codes` / `--hide-codes`: tool rule IDs/codes control - ✅ `--fail-fast`: stop
  after first tool failure - - **Testing:** Display control tests pass

- - - [x] **Add Output Formats & Report Generation** (Severity: **High**) ✅ COMPLETE - **Context:** Need structured
  output for humans and CI artifacts. - **Implementation:** `tools/repo_lint/reporting.py` with full format handlers - -
  **Delivered:** - ✅ `--format <FMT>`: rich (TTY default), plain (CI default), json, yaml, csv, xlsx - ✅ `--report
  <PATH>`: write consolidated report to disk - ✅ `--reports-dir <DIR>`: write per-tool reports + index summary - ✅
  JSON/YAML schemas stable - ✅ CSV output: summary.csv, violations.csv (full implementation) - ✅ XLSX output:
  report.xlsx with multiple sheets (full implementation with openpyxl) - **Testing:** Output format tests pass (xlsx
  skipped if openpyxl not installed)

- - - [x] **Add Fix-Mode Safety Features** (Severity: **High**) ✅ COMPLETE - **Context:** Fixing should be safe and
  predictable. - **Implementation:** `tools/repo_lint/cli.py` fix command - - **Delivered:** - ✅ `--dry-run`: show what
  would change without modifying files - ✅ `--diff`: show unified diff previews (TTY-only) - ✅ `--changed-only`:
  restrict to git-changed files (error if no git) - - **Testing:** Fix mode tests pass

- - [x] **Add `repo-lint doctor` Command** (Severity: **High**) ✅ COMPLETE - - **Context:** Need comprehensive
  environment + config sanity check. - **Implementation:** `tools/repo_lint/doctor.py` (full implementation) - -
  **Delivered:** - ✅ Checks: repo root, venv, tool registry, config validity, tool availability, PATH - ✅ Flags:
  `--format` (rich/plain/json/yaml), `--report`, `--ci` - ✅ Exit 0 if all green, 1 if any red - ✅ Output: green/red
  checklist with detailed diagnostics - **Testing:** Doctor command verified working

- - - [x] **Implement External Configuration Contract (YAML-First)** (Severity: **High**) ✅ COMPLETE - **Context:**
  Maximize user-configurability while preserving contract safety. - **Implementation Status:** - ✅ All configurable
  behavior IS in YAML (conformance/repo-lint/*.yaml) - ✅ Strict validation: `---`/`...` markers, `type`/`version`
  fields, unknown keys fail (config_validator.py) - ✅ YAML-first architecture fully implemented (yaml_loader.py) - ✅
  `dump-config` command: print fully-resolved config (YAML/JSON formats) - **IMPLEMENTED** - ✅ `validate-config <PATH>`
  command: validate without running - **IMPLEMENTED** - ✅ Custom config directory support via set_config_directory() and
  --config option - **IMPLEMENTED** - **Delivered:** 2026-01-05 - ✅ `dump-config --format yaml|json` command with config
  source display - ✅ `validate-config <PATH>` command with config-type-aware validation - ✅ Support for --config option
  in dump-config - ✅ Config directory precedence: --config flag > REPO_LINT_CONFIG_DIR env
> default - ✅ 10/10 unit tests passing - **Testing:** All config management tests pass

- - - [x] **Add Tool Registry & Discoverability Commands** (Severity: **Medium**) ✅ COMPLETE - **Context:** Users need
  to discover what languages/tools are supported. - **Implementation:** `tools/repo_lint/cli.py` with registry commands
  - - **Delivered:** - ✅ `list-langs` command: prints supported `--lang` values - ✅ `list-tools` command: prints
  supported tools (all or per-language via `--lang`) - ✅ `tool-help <TOOL>` command: prints tool info (description,
  language, fix-capable, version, config) - ✅ Tool registry derived from conformance configs (single source of truth) -
  **Testing:** Tool registry commands verified working

**Summary:**

- - - ✅ 8/8 major items COMPLETE and tested - ✅ 35/35 Phase 2.7 unit tests passing (25 original + 10 config tests) - ✅
  End-to-end CLI verification successful - ✅ Pre-commit gate: EXIT 0

**Rationale:** Granular control enables both power users and CI/CD integration.

---

## Phase 2.8 – Environment & PATH Management ✅ COMPLETE (7/7)

**Goal:** Add commands to help users manage venv/PATH setup for `repo-lint` without automatic rc file editing.

**Mandatory Features:**

- - [x] **Add `repo-lint env` Command** (Severity: **High**) ✅ COMPLETE - - **Context:** Shell integration helper that
  prints/writes PATH snippets. - **Affected Files:** `tools/repo_lint/cli.py`, new modules under `tools/repo_lint/env/`
  - - **Implementation:** Full CLI command with --print, --install, --shell, --venv, --path-only flags - **Status:**
  Session 5 (2026-01-05 19:00)

- - [x] **Add `repo-lint activate` Command** (Severity: **High**) ✅ COMPLETE - - **Context:** Convenience launcher that
  spawns subshell with venv activated. - **Affected Files:** `tools/repo_lint/cli.py` - - **Implementation:** Full CLI
  command with --venv, --shell, --command, --no-rc, --print, --ci flags - **Status:** Session 5 (2026-01-05 19:00)

- - [x] **Add `repo-lint which` Command** (Severity: **Medium**) ✅ COMPLETE - - **Context:** Diagnostic helper for
  PATH/venv confusion. - **Affected Files:** `tools/repo_lint/cli.py` - - **Implementation:** Full CLI command with Rich
  table output and --json flag - **Status:** Session 5 (2026-01-05 19:00)

- - - [x] **Implement Shared Venv Resolution Utility** (Severity: **High**) ✅ COMPLETE - **Context:** Single source of
  truth for venv detection. - **Affected Files:** `tools/repo_lint/env/venv_resolver.py` (250 lines) - -
  **Implementation:** 4-tier precedence, cross-platform support, 24 unit tests - **Status:** Session 5 (2026-01-05
  19:00)

- - - [x] **Cross-Platform Validation** (Severity: **High** - BLOCKER) ✅ COMPLETE (CI-based) - **Context:** Validated on
  Linux/macOS + Windows via CI - **Implementation:** Manual testing on Linux/macOS, CI validation approach for Windows -
  **Status:** Session 5 (2026-01-05 19:00)

- - - [x] **Update Documentation** (Severity: **Medium**) ✅ COMPLETE - **Context:** Users need clear guidance on
  env/activate/which usage. - **Affected Files:** `REPO-LINT-USER-MANUAL.md` (renamed from HOW-TO-USE-THIS-TOOL.md) - -
  **Implementation:** 100+ lines added with examples for all shells - **Status:** Session 5 (2026-01-05 19:00)

- - - [x] **yaml-docstrings Check** (Severity: **Medium**) ✅ COMPLETE (Outstanding TODO) - **Context:** YAML files have
  docstring contracts in the repository - **Affected Files:** `tools/repo_lint/runners/yaml_runner.py` -
  **Implementation:** New `_run_docstring_validation()` method, integrated into check() - - **Status:** Session 9
  (2026-01-05 22:40)

- - - [x] **actionlint Support** (Severity: **Medium**) ✅ COMPLETE (Outstanding TODO) - **Context:** GitHub Actions
  workflow linter (.github/workflows/*.yml) - **Affected Files:** `tools/repo_lint/runners/yaml_runner.py` -
  **Implementation:** New `_run_actionlint()` method, optional tool (check-only) - - **Status:** Session 9 (2026-01-05
  22:40)

**Rationale:** Explicit PATH/venv management improves usability without hostile automatic modifications.

**Phase 2.8 Status:** ✅ COMPLETE (7/7 items delivered)

- - - Sessions: 5 (core env commands) + 9 (yaml-docstrings + actionlint) - Total lines added: ~500+ lines (env module +
  CLI commands + YAML runner enhancements) - Pre-commit gate: EXIT 0 (16/16 runners passing)

---

## Phase 2.9 – Mandatory Integration & YAML-First Contracts (Cross-Cutting) ✅ COMPLETE

**Goal:** Ensure all helper scripts are integrated into `repo-lint` and all configuration is YAML-first.

**Mandatory Requirements:**

- - - [x] **Integrate External Helper Scripts** (Severity: **High**) - **Context:** Any helper scripts invoked by
  `repo-lint` MUST be integrated into the package. - - **Status:** ✅ COMPLETE - All helpers integrated, no external
  scripts remain - **Requirements:** - Helpers MUST live under `tools/repo_lint/` namespace - Helpers MUST have stable,
  testable Python API - Configuration MUST use conformance YAML system - Invocation MUST be centralized (no ad-hoc
  subprocess strings) - Helpers MUST be documented in HOW-TO - Helpers MUST have unit tests (success paths, failure
  modes, output schema) - Fail fast if external helper detected but not integrated - **Rationale:** No "mystery helper
  scripts"; everything is first-class.

- - - [x] **Migrate to YAML-First Configuration** (Severity: **High**) - **Context:** Maximize configurability while
  preserving contracts. - **Status:** ✅ COMPLETE - PR #207 merged, all configs migrated to YAML - **Completed Work:** -
  Created `tools/repo_lint/yaml_loader.py` (276 lines) - Created `conformance/repo-lint/repo-lint-file-patterns.yaml` -
  Migrated version pins from hardcoded constants to YAML - Migrated file patterns from hardcoded constants to YAML -
  Migrated exclusions from hardcoded constants to YAML - Added backward compatibility with deprecation warnings - Single
  source of truth: all configs in `conformance/repo-lint/*.yaml` - - **Requirements:** - All configurable behavior MUST
  be in YAML (not hard-coded constants or ad-hoc env vars) - Strict validation enforced - CLI flags override config but
  cannot violate contracts - Contract-critical behavior MUST NOT be disable-able - **Rationale:** Centralized, validated
  configuration prevents drift and improves maintainability.

**Rationale:** Cross-cutting contracts ensure consistency and quality across all features.

---

Each fix above should be committed with clear messages, linking to issues if the repository uses an issue tracker.
Prioritize the Phase 1 items immediately, as they address correctness and compliance issues. Phase 2 implements
requested features and contract alignments from the "Future Work" document. Phase 3 covers residual improvements and
housekeeping.

## Progress Tracker

- - - [x] Phase 1 – Critical Fixes and Corrections (High Priority) ✅ COMPLETE - [x] Fix repository root detection - [x]
  Clarify exit codes for unsafe mode - [x] Handle partial install failures gracefully - [x] Ensure missing docstring
  validator is detected - [x] Validate non-Python unsafe mode behavior - [x] Add missing unit tests for error conditions
  - [x] Phase 2 – Major Enhancements and Alignments ✅ COMPLETE - [x] Make `repo_lint` an installable package (✅ P2.1) -
  - [x] Integrate naming-and-style enforcement (✅ P2.2) - [x] Pin external tool versions in installer (✅ P2.3) - [x]
  Improve CLI usability (✅ P2.4 - Click + Rich + completion + HOW-TO) - [x] Phase 2.5 – Rich UI "Glow Up" ✅ ALL BLOCKERS
  RESOLVED - COMPLETE - [x] UI/Reporter Layer (2.5.3-A) - [x] Data Model Extensions (2.5.3-B, 2.5.3-C) - [x] Results
  Rendering (2.5.3-C) - [x] CLI Integration (2.5.3-D) - [x] Rich-Click Integration (2.5.3-E) - [x] Theme System
  (2.5.3-G) - [x] Test Updates (Session 2025-12-31 07:30 - test_output_format.py updated) - [x] Windows Validation
  (Session 2025-12-31 07:45 - Windows CI validation added) - [x] Documentation Updates (Session 2025-12-31 08:00 -
  HOW-TO updated with theme/Windows docs) - [x] Phase 2.9 – Mandatory Integration & YAML-First Contracts ✅ COMPLETE -
  [x] Integrate External Helper Scripts (All helpers integrated) - [x] Migrate to YAML-First Configuration (PR #207
  merged, yaml_loader.py created, all configs migrated) - [x] Phase 2.7 – Extended CLI Granularity & Reporting ✅
  COMPLETE (8/8 items) - [x] `--lang` and `--tool` filtering (COMPLETE) - [x] `repo-lint doctor` command (COMPLETE) - -
  [x] Tool registry and discoverability commands (list-langs, list-tools, tool-help - COMPLETE) - [x] Summary modes and
  verbosity controls (COMPLETE) - [x] Output formats (json, yaml, csv, xlsx - COMPLETE) - [x] Fix-mode safety
  (--dry-run, --diff, --changed-only - COMPLETE) - [x] External configuration contract (dump-config, validate-config -
  COMPLETE) - [x] Phase 2.8 – Environment & PATH Management ✅ COMPLETE (7/7 items) - [x] `repo-lint env` command (shell
  integration helper - Session 5) - [x] `repo-lint activate` command (subshell launcher - Session 5) - [x] `repo-lint
  which` command (diagnostics - Session 5) - - [x] Shared venv resolution utility (Session 5) - [x] Cross-platform
  validation (Linux/macOS/Windows - CI-based Session 5) - [x] Documentation updates (REPO-LINT-USER-MANUAL.md - Session
  5) - [x] yaml-docstrings check (Outstanding TODO - Session 9) - [x] actionlint support (Outstanding TODO - Session 9)
  - [ ] Phase 2.6 – Centralized Exception Rules (NEXT PRIORITY - after Phase 2.8) - [ ] Schema & Validator (2.6.1) - [ ]
  Integration into Results & Reporting (2.6.2) - [ ] Pragma Support & Conflict Detection (2.6.3) - [ ] Symbol/Scope
  Matching (2.6.4) - [ ] Documentation Updates (2.6.5) - [ ] Tests (2.6.6) - [ ] Phase 3 – Polish, Nits, and Minor
  Improvements (Low Priority) ⏸️ DEFERRED - [ ] Code style clean-up - [ ] Add or improve docstrings in the code - [ ]
  Update documentation - [ ] Test coverage for runners (Optional)

## Session Notes (newest first)

### 2025-12-31 06:41 - Consolidated Phase 2.5-2.9 into Canonical Overview ✅

**Session Complete:**

- - ✅ Consolidated all external documents into single canonical `160-overview.md` - ✅ Created `160-human-decisions-2.md`
  for human review (10 major decisions) - - ✅ Updated Progress Tracker to reflect actual completion state - ✅ Updated
  `160-next-steps.md` with current blockers and next actions

**Documents Consolidated:**

- - `160-phase-2-point-5-rich-glow-up.md` → Phase 2.5 section in overview - `160-phase-2-point-6-pragmas-sucks.md` →
  Phase 2.6 section in overview - `repo-lint-feature-set.md` → Phase 2.7 and 2.8 sections in overview

**New Phase Structure:**

- - - Phase 2.5: Rich UI "Glow Up" (CORE COMPLETE - 6/9 items; Windows validation BLOCKER) - Phase 2.6: Centralized
  Exception Rules (NOT STARTED - awaiting human decision) - Phase 2.7: Extended CLI Granularity & Reporting (NOT STARTED
  - awaiting human decision) - Phase 2.8: Environment & PATH Management (NOT STARTED - awaiting human decision) - Phase
  2.9: Mandatory Integration & YAML-First Contracts (NOT STARTED - awaiting human decision)

**Key Changes:**

- - - Normalized all requirements to use explicit MUST/SHOULD/MAY language - Added severity markers (High/Medium/Low)
  for all items - Marked blockers explicitly (Windows validation for Phase 2.5) - Created comprehensive human decision
  document (10 decisions covering priorities, scope, trade-offs)

**Human Decisions Required:**

- - - Phase 2.5 Windows validation: Blocker or deferred? - Phase 2.6-2.9 prioritization and sequencing - YAML-first
  configuration scope and aggressiveness - Pragma policy for centralized exceptions - CLI complexity vs usability
  trade-offs - Output format support (json/yaml/csv/xlsx) - `repo-lint doctor` command scope - - Environment commands
  priority - Phase 2.9 integration contract timing - Testing strategy and coverage requirements

**Files Changed:**

- - `docs/ai-prompt/160/160-overview.md`: Consolidated all content, updated progress tracker -
  `docs/ai-prompt/160/160-next-steps.md`: Updated with Phase 2.5 blockers and human decision requirement -
  `docs/ai-prompt/160/160-human-decisions-2.md`: Created (16KB, 10 major decisions)

**Rationale:**

- - - Per task requirements: merge all external phase documents into canonical overview - Eliminate duplication and
  ambiguity - Ensure single source of truth for Issue #160 - Surface decisions requiring human input before proceeding

**Next Steps:**

- - - Await human decisions on Phase 2.5 Windows validation approach - Await human decisions on Phase 2.6-2.9 priorities
  - Complete Phase 2.5 blockers once direction is clear - Do NOT proceed to Phase 2.6+ until human sign-off received

---

### 2025-12-31 04:10 - Phase 2 Complete ✅ - All Mandatory Validation Passed

**Session Complete:**

- - - ✅ Phase 1 (6/6) complete (from prior session) - ✅ Phase 2 (4/4) complete (this session) - P2.1: Installable
  package ✅ - P2.2: Naming enforcement ✅ - P2.3: Pinned versions ✅ - P2.4: Click CLI + Rich + completion + HOW-TO ✅ - ✅
  Code review completed and feedback addressed - ✅ CodeQL security scan: 0 alerts - ⏸️ Phase 3 deferred to future work

**Final Commit Summary:**

1. 1. 1. Fix: Add PyYAML dependency (8652a08) 2. Phase 2.4: Click migration (76380c9 → 0f969ec after rebase) 3. Fix:
   Code review feedback (7dd4dab)

**Work Completed:**

- - - Fixed CI PyYAML import error by adding to workflow pip install commands - Migrated CLI from argparse to Click with
  Rich formatting - Added shell completion support (bash, zsh, fish) - Created comprehensive HOW-TO-USE-THIS-TOOL.md
  (380+ lines) - Addressed all code review feedback - Passed CodeQL security scan (0 alerts)

**Next Steps for Future Work:**

- - - Phase 3.1: Code style clean-up - Phase 3.2: Comprehensive docstring audit - Phase 3.3: Documentation updates -
  Phase 3.4: Integration tests for runners

---

### 2025-12-31 03:15 - Phase 2 (Partial) Complete ✅

- - - Completed P2.1: Make repo_lint installable package - Added entry point to pyproject.toml: `repo-lint` command -
  Backward compatible with `python3 -m tools.repo_lint` - - Tested both invocation methods - Completed P2.2: Integrate
  naming/style enforcement (CHECK-ONLY) - Created 3 external YAML config files with strict validation requirements -
  Implemented strict config validator with pre-ingest checks - Implemented naming runner (check-only, no auto-renames) -
  Integrated into CLI workflow - All files pass linting (Black, Ruff, yamllint) - 2 rounds of code review, all issues
  addressed - CodeQL: 0 security alerts - Verified P2.3: Pin external tool versions (already complete from prior work) -
  P2.4 deferred: CLI usability (Click migration) - major refactor beyond scope - Phase 3 deferred to future work - Total
  work: Phase 1 (6/6) + Phase 2 (3/4) = 9/10 items complete

### 2025-12-31 01:25 - Phase 1 Complete ✅

- - - All 6 Phase 1 items implemented and tested - 20 tests passing (14 unit + 6 integration) - 4 iterations of code
  review feedback addressed - Final code review comments are nitpicks that contradict established codebase patterns: -
  Error messages use individual print statements (matches all existing patterns in cli.py) - Path traversal uses .parent
  chain (matches all 12+ test files in codebase) - Code follows minimal-change principle and repository conventions -
  Ready for human review and merge

### 2025-12-31 01:20 - Completed all Phase 1 items

- - - Item 1: Repository root detection - ✅ - Item 2: Exit code clarification - ✅ - Item 3: Install failure handling - ✅
  - Item 4: Docstring validator detection - ✅ - Item 5: Non-Python unsafe mode validation - ✅ - Item 6: Integration
  tests - ✅ - All tests passing, code review iterations complete

### 2025-12-31 01:02 - Completed exit code clarification for unsafe mode

- - Added `ExitCode.UNSAFE_VIOLATION = 4` for policy violations in unsafe mode - Updated `cmd_fix()` to use new exit
  code instead of MISSING_TOOLS - - Added 2 new unit tests, all 13 tests passing - Changes committed in 9cf27b3 - Ready
  for code review - Next item: Handle partial install failures gracefully

### 2025-12-31 00:37 - Addressed code review feedback

- - Fixed inconsistent fallback behavior in `get_repo_root()` - now starts from cwd like `find_repo_root()` - - Added
  comprehensive test coverage: 7 new tests (3 for get_repo_root, 4 for find_repo_root) - All tests passing (21/21 total)
  - Replied to both code review comments with commit hash e8070b0 - PR ready for re-review

### 2025-12-31 00:25 - Completed repository root detection fix

- - Fixed `get_repo_root()` and `find_repo_root()` to handle missing .git directory - - Both functions now return
  current working directory as fallback - All tests pass, code review passed with no comments - Ready for PR merge -
  this is the first item in the epic - Next session should address: "Clarify exit codes for unsafe mode" (new PR/branch)

### 2025-12-31 00:16 - Initial session

- - - Created overview and next-steps journal files - Reviewed repository structure and identified affected files -
  Planning to address Phase 1 critical fixes first

### 2025-12-31 04:19 - Phase 2.5 CORE COMPLETE ✅

**Session Complete:**

- - - ✅ Phase 2.5 core implementation (6/6 major sections) - 2.5.3-A: UI/Reporter Layer ✅ - 2.5.3-B: Data Model ✅ -
  2.5.3-C: Results Rendering ✅ - 2.5.3-D: CLI Integration ✅ - 2.5.3-E: Rich-Click ✅ - 2.5.3-G: Theme System ✅ - ✅ Code
  review completed (5 issues addressed) - ✅ CodeQL security scan: 0 alerts - ⏸️ Tests, Windows validation, docs deferred
  to next session

**Final Commit Summary:**

1. 1. 1. Phase 2.5: Add UI module, theme system, rich-click (a51b129) 2. Phase 2.5: Integrate Reporter into reporting.py
   (f8a440d) 3. Phase 2.5: Fix Reporter failure rendering (729e606) 4. Phase 2.5: Address code review feedback (c694562)

**Work Completed:**

- - - Created complete UI module (~1200 lines) - Integrated Rich-Click with comprehensive help - Implemented YAML theme
  configuration - Added CI vs Interactive output modes - All code review feedback addressed - Security scan passed

**Output Quality:**

```
Interactive Mode:
╭────────┬─────────┬───────┬────────────┬──────────╮
│ Runner │ Status  │ Files │ Violations │ Duration │
├────────┼─────────┼───────┼────────────┼──────────┤
│ ruff   │ ✅ PASS │     - │          0 │        - │
╰────────┴─────────┴───────┴────────────┴──────────╯
```

**Next Steps for Human/Future Work:**

- - - Update test_output_format.py for Rich format - Add Reporter/theme unit tests - Windows validation (BLOCKER for
  release) - Update HOW-TO documentation

**Achievement:** repo-lint now has professional-grade UI rivaling commercial tools! 🎉
