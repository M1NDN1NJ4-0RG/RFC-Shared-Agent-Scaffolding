# Testing Standards & Requirements

**Status:** Mandatory for all code changes.  
**Load:** When writing tests, running tests, or implementing features.

---

## Core Testing Principles

1. **Tests define the contract** — Implementation follows tests, not vice versa
2. **Test-first workflow** — Write tests before or alongside implementation
3. **Deterministic tests** — Same input = same output, every time
4. **Self-documenting tests** — Test name clearly describes what is tested
5. **Fast tests** — Unit tests run in seconds, not minutes

---

## Test Coverage Requirements

### New Features
- **Minimum:** 1 happy path test
- **Recommended:** Happy path + 2 edge cases + 1 error case
- **Required:** All public API functions must have tests

### Bug Fixes
- **Mandatory:** Regression test that fails before fix, passes after fix
- **Purpose:** Prevent same bug from recurring

### Refactoring
- **Mandatory:** All existing tests must still pass
- **Recommended:** Add tests for newly exposed edge cases

---

## Conformance Testing

**For script bundles (Bash, Python, Perl, PowerShell):**

All implementations **MUST** pass the same conformance vectors defined in `/conformance/vectors.json`.

### Running Conformance Tests

```bash
# Bash
cd RFC-Shared-Agent-Scaffolding-Example/scripts/bash
./run-tests.sh

# Python 3
cd RFC-Shared-Agent-Scaffolding-Example/scripts/python3
./run_tests.sh

# Perl
cd RFC-Shared-Agent-Scaffolding-Example/scripts/perl
./run-tests.sh

# PowerShell
cd RFC-Shared-Agent-Scaffolding-Example/scripts/powershell
pwsh -File run-tests.ps1
```

### Conformance Requirements

**Pass criteria:**
- Exit code 0 (all tests pass)
- No stderr output (except expected test output)
- All vectors from `conformance/vectors.json` validated

**Failure:**
- Indicates implementation drift
- Must be fixed before merging
- See M2-P2-I1 for drift detection details

---

## Test Naming Conventions

### Unit Tests
**Format:** `test_<function>_<scenario>`

**Examples:**
- `test_safe_run_success_no_artifacts`
- `test_safe_run_failure_creates_log`
- `test_preflight_missing_context_fails`

### Integration Tests
**Format:** `test_<workflow>_<scenario>`

**Examples:**
- `test_pr_workflow_auto_merge_success`
- `test_build_workflow_dependencies_installed`

### Conformance Tests
**Format:** Match vector ID from `conformance/vectors.json`

**Examples:**
- `test_safe_run_001` (maps to vector `safe-run-001`)
- `test_preflight_002` (maps to vector `preflight-002`)

---

## Test Organization

### Directory Structure
```
scripts/<language>/
├── scripts/              # Implementation code
│   ├── safe_run.sh
│   ├── preflight_automerge_ruleset.sh
│   └── ...
└── tests/               # Test files
    ├── test_safe_run.sh
    ├── test_preflight.sh
    └── ...
```

### Test File Naming
- Test files named `test_<module>.sh` / `.py` / `.pl` / `.ps1`
- One test file per implementation file (generally)
- Helper files prefixed with `helper_` or in `lib/` subdirectory

---

## M0 Contract Validation

Tests **MUST** validate M0 contract decisions:

### M0-P1-I1: safe-run Logging Semantics
```python
# Python example
content = log_file.read_text()
assert '=== STDOUT ===' in content
assert '=== STDERR ===' in content
```

### M0-P1-I2: Log File Naming
```bash
# Bash example
log_file=$(ls .agent/FAIL-LOGS/*.log)
[[ "$log_file" =~ [0-9]{8}T[0-9]{6}Z-pid[0-9]+-FAIL\.log ]]
```

### M0-P1-I3: safe-archive No-Clobber
```perl
# Perl example
ok(-f 'output.tar.gz', 'original file exists');
ok(-f 'output.1.tar.gz', 'suffixed file created');
```

### M0-P2-I1: Auth Header Format
```powershell
# PowerShell example
$source = Get-Content $scriptPath -Raw
$source | Should -Match 'Bearer'
```

### M0-P2-I2: Exit Code Taxonomy
All tests must assert **exact** exit codes per the taxonomy.

---

## Test Execution Requirements

### Before Committing
- [ ] All tests pass locally
- [ ] No new test failures introduced
- [ ] Tests are deterministic (run twice to verify)

### In CI
- [ ] All language bundles tested
- [ ] Conformance vectors validated
- [ ] Exit code 0 or CI fails

### After Merge
- [ ] Verify tests still pass on default branch
- [ ] Update test documentation if behavior changed

---

## Mocking & Fixtures

### When to Mock
- External API calls (GitHub API, etc.)
- Filesystem operations (for speed)
- Network requests
- Time-dependent behavior

### When NOT to Mock
- Core business logic
- File I/O that's fast enough
- Exit code behavior
- Log formatting

### Fixture Guidelines
- Store fixtures in `tests/fixtures/` directory
- JSON fixtures for API responses
- Text files for expected outputs
- Keep fixtures minimal (only relevant data)

---

## Test Output Expectations

### Success Output
```
Running tests...
✓ test_safe_run_success
✓ test_safe_run_failure
✓ test_preflight_auth
All tests passed.
```

### Failure Output
```
Running tests...
✓ test_safe_run_success
✗ test_safe_run_failure
  Expected exit code 7, got 1

FAILED: 1 test(s) failed
```

### Verbose Mode (Optional)
- Show test execution details
- Print actual vs expected values on failure
- Enable with `-v` or `--verbose` flag

---

## Performance Testing

**Not required for every change, but consider when:**
- Adding new file operations
- Implementing archiving/compression
- Processing large outputs

**Performance targets:**
- Unit tests: < 1 second each
- Integration tests: < 10 seconds each
- Full test suite: < 60 seconds total

---

## Anti-patterns

❌ **Don't:** Skip tests "because it's a small change"  
✅ **Do:** Add tests for every functional change

❌ **Don't:** Comment out failing tests  
✅ **Do:** Fix the test or the code

❌ **Don't:** Depend on test execution order  
✅ **Do:** Make each test independent

❌ **Don't:** Hard-code paths or assumptions  
✅ **Do:** Use temp directories and cleanup

❌ **Don't:** Assert on exact string matches for error messages  
✅ **Do:** Assert on exit codes and key markers

---

**Version:** 1.0  
**Last Updated:** 2025-12-26  
**Refs:** RFC v0.1.0 section 6.2, M0 contract decisions
