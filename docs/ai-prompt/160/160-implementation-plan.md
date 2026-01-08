# Issue #160 Implementation Plan - Based on Human Decisions

**Last Updated:** 2025-12-31 07:10 UTC
**Source:** `160-human-decisions-2.md` (Locked In Decisions)

---

## IMPLEMENTATION ORDER (MANDATORY SEQUENCE)

### **PHASE 0: Complete Phase 2.5 Blockers** (IMMEDIATE - BEFORE ANY OTHER WORK)

**Status:** 3 items remaining (6/9 complete)

1. ⚠️ **Update `test_output_format.py` for Rich table format** (NEXT)
   - Tests currently fail because output format changed from plain text to Rich tables
   - Update tests to verify table structure instead of plain text patterns
   - Ensure exit code tests still pass

2. ⚠️ **Add Windows CI validation** (RELEASE BLOCKER)
   - Decision: Hybrid approach - CI-first Windows validation
   - Add Windows GitHub Actions runners to `.github/workflows/`
   - Validate: Rich console output, Rich-Click help, shell completion (to extent testable in CI)
   - Manual validation on physical Windows machine is explicitly deferred

3. ⚠️ **Update `HOW-TO-USE-THIS-TOOL.md`**
   - Add Windows PowerShell completion instructions
   - Add theme customization guide (YAML theme system)
   - Add output mode examples (interactive vs CI)

---

### **PHASE 1: Phase 2.9 - Integration & YAML-First Contracts** (AFTER 2.5 BLOCKERS)

**Decision:** Phase 2.9 MUST be implemented BEFORE Phase 2.6-2.8 work proceeds.

**Requirements:**

1. Audit existing helper scripts for integration needs
2. Enforce YAML-first contracts for all new work
3. Apply retroactive enforcement from audit findings

**Specific Tasks:**

- Identify any non-integrated helper scripts in the repository
- Document integration requirements
- Migrate configuration to YAML where possible
- Enforce contracts: "Any behavior that can reasonably be configured MUST be in YAML"
- Multi-file structure (separate conformance YAML by concern)
- Backward compatibility via transition period with deprecation warnings
- CLI overrides allowed ONLY if they don't violate contracts

---

### **PHASE 2: Phase 2.7 - CLI Granularity & Reporting Surface** (AFTER 2.9)

**Decision:** Implement full flag set with Rich-Click help panels to mitigate complexity.

**CLI Flags to Implement:**

**Filtering Flags:**

- `--lang <language>` (repeatable): Filter to specific language(s)
- `--tool <tool>` (repeatable): Run specific tool(s) only
- `--changed-only`: Only check files changed in git
- `--diff <ref>`: Check files changed vs specific git ref

**Output Flags:**

- `--format <format>`: Output format (rich|plain|json|yaml|csv|xlsx)
- `--summary`: Show summary after results
- `--summary-only`: Show ONLY summary (no individual violations)
- `--summary-format <format>`: Format for summary output
- `--report <path>`: Write report to file
- `--reports-dir <dir>`: Directory for reports
- `--show-files` / `--hide-files`: Control file listing
- `--show-codes` / `--hide-codes`: Control error code display

**Execution Flags:**

- `--max-violations <n>`: Stop after N violations
- `--fail-fast`: Stop on first error
- `--dry-run`: Show what would be done (fix mode)

**Info Flags:**

- `--list-langs`: List supported languages
- `--list-tools`: List available tools
- `--tool-help <tool>`: Show help for specific tool
- `--explain-tool <tool>`: Explain what a tool does

**Help Organization:**

- Use Rich-Click panels: Filtering / Output / Execution / Info
- Excellent examples in help text
- Clear error messages with deterministic exit codes

**Output Format Requirements:**

- Support: `rich`, `plain`, `json`, `yaml`, `csv`, `xlsx`
- All formats derive from single normalized data model
- XLSX support requires `openpyxl` dependency (packaging extra)
- Ensure CI installs it where needed

**New Commands:**

1. **`repo-lint doctor`** (Diagnostic Command)
   - **Decision:** Minimum checks, check-only (no auto-fix)
   - Checks: repo root, venv resolution, config validity, tool registry load, tool availability, PATH sanity
   - Check-only: report + suggest fixes (NO automatic changes)
   - Help content with exact references
   - Documentation file: `tools/repo_lint/HOW-TO-USE.md`

2. **`repo-lint list-langs`** - List supported languages
3. **`repo-lint list-tools`** - List available linting tools
4. **`repo-lint tool-help <tool>`** - Show tool-specific help
5. **`repo-lint explain-tool <tool>`** - Explain tool purpose and usage

---

### **PHASE 3: Phase 2.8 - Environment & PATH Management** (AFTER 2.7)

**Decision:** Required. Implement all three in this order: `which` → `env` → `activate`

**1. `repo-lint which <tool>`** (FIRST - Highest Value, Lowest Effort)

- Show which version of a tool would be used
- Diagnostic command for PATH troubleshooting
- Examples:

  ```bash
  repo-lint which black
  # Output: /home/user/.venv-lint/bin/black (version 24.10.0)

  repo-lint which shellcheck
  # Output: /usr/bin/shellcheck (version 0.9.0)
  ```

**2. `repo-lint env`** (SECOND)

- Print environment variables for tools
- Shows: tool paths, versions, configuration
- Useful for debugging and CI setup
- Cross-platform scripting (Bash, PowerShell, Fish)

**3. `repo-lint activate`** (THIRD - Most Complex)

- Activate repo-lint environment in current shell
- Subshell handling (most complex)
- Cross-platform support

---

### **PHASE 4: Phase 2.6 - Centralized Exception Rules** (AFTER 2.7 & 2.8)

**Decision:** Warn on pragmas by default (configurable), YAML precedence strict, migration tool prints suggestions.

**Requirements:**

1. **YAML Exception Files**
   - Centralized exception configuration
   - Replace/supplement pragma-based exceptions
   - Multi-file structure under `conformance/repo-lint/`

2. **Pragma Handling**
   - Warn on pragmas by default (this warning MUST be configurable/disable-able)
   - YAML exceptions have strict precedence over pragmas when both apply
   - Maintain backward compatibility

3. **Migration Tool**
   - `repo-lint pragmas scan`: Scan codebase for pragma usage
   - Print suggestions for YAML entries
   - May optionally write draft file
   - MUST NOT silently rewrite canonical exception files

4. **Precedence Rules**
   - When both YAML and pragma apply to same target: YAML wins (strict)
   - Document this behavior clearly

---

### **PHASE 5: Phase 3 - Polish** (LAST - AFTER ALL FEATURES STABLE)

**Decision:** Deferred until all features are stable.

**Tasks:**

- Code style cleanup (flake8, pylint)
- Docstring improvements
- Documentation updates
- Integration tests (optional)
- Test coverage for runners (optional)

---

## TESTING STRATEGY (APPLIES TO ALL PHASES)

**Decision:** Standard coverage, tests required before review, Windows CI for relevant phases.

**Requirements:**

1. **Coverage:** Unit tests + targeted integration tests for major workflows
2. **Timing:** Tests MUST be added and passing BEFORE code review
3. **Windows CI:** Include for phases where Windows behavior is relevant
   - Phase 2.5: Rich UI, help output, shell integration
   - Phase 2.7: CLI flags, output formats, doctor command
   - Phase 2.8: Environment commands, PATH management

**Test Standards:**

- Unit tests for all new functions/methods
- Integration tests for end-to-end workflows
- Cross-platform validation where applicable
- All tests must pass before requesting code review

---

## CONFIGURATION CONTRACTS (CROSS-CUTTING)

### YAML-First Migration

**From Decision 3:**

- Migrate ALL behavior that can reasonably be configured to YAML
- Maintain multi-file structure (separate conformance YAML files by concern)
- Preserve backward compatibility via transition period with deprecation warnings
- Only allow CLI overrides that do NOT violate contracts

### Exception System Precedence

**From Decision 4:**

- YAML exceptions have strict precedence over pragmas
- Warn on pragmas by default (configurable)
- Migration tool prints suggestions (may write draft, won't silently overwrite)

### Output Format Contract

**From Decision 6:**

- All formats derive from single normalized data model
- XLSX support required (handle as explicit packaging extra)
- Ensure CI installs dependencies where needed

---

## COMPLETED PHASES - READY TO PROCEED

Phase 2.5 (Rich UI "Glow Up") and Phase 2.9 (YAML-First Configuration) are COMPLETE.

All Phase 2.7 work is now UNBLOCKED and IN PROGRESS.
