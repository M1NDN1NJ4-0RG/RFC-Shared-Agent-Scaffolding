# Build & Verification Standards

**Status:** Required for all code changes before merging.  
**Load:** When building code or verifying changes.

---

## Build Commands by Language

### Bash
```bash
cd RFC-Shared-Agent-Scaffolding-Example/scripts/bash
./run-tests.sh
```

**Requirements:**
- `bash` 4.0+ available
- `jq` installed (for JSON parsing in preflight)
- All tests pass (exit code 0)

### Python 3
```bash
cd RFC-Shared-Agent-Scaffolding-Example/scripts/python3
python3 -m unittest discover -s tests -v
```

**Requirements:**
- Python 3.7+ recommended
- No external dependencies beyond stdlib
- All tests pass (exit code 0)

### Perl
```bash
cd RFC-Shared-Agent-Scaffolding-Example/scripts/perl
./run-tests.sh
```

**Requirements:**
- Perl 5.x available
- Standard Perl modules only
- All tests pass (exit code 0)

### PowerShell
```powershell
cd RFC-Shared-Agent-Scaffolding-Example/scripts/powershell
pwsh -File run-tests.ps1
```

**Requirements:**
- PowerShell 7+ (pwsh) recommended
- Pester 5+ for tests
- All tests pass (exit code 0)

---

## Verification Checklist

Before requesting review or merging, verify:

### Code Quality
- [ ] **Linting:** Code passes linter (if configured)
- [ ] **Formatting:** Code follows project style
- [ ] **Comments:** Complex logic has explanatory comments
- [ ] **No dead code:** Removed commented-out code
- [ ] **No debug statements:** Removed print/console.log debugging

### Functionality
- [ ] **Tests pass:** All tests exit code 0
- [ ] **New tests added:** Features have tests
- [ ] **Regression tests:** Bug fixes have regression tests
- [ ] **Manual testing:** Exercised changed code paths
- [ ] **Edge cases:** Considered and tested

### Security
- [ ] **No secrets:** No tokens, passwords, API keys in code
- [ ] **No new vulnerabilities:** Security scanners pass (if configured)
- [ ] **Input validation:** User input is validated
- [ ] **Exit codes:** Error cases return appropriate codes (M0-P2-I2)

### Documentation
- [ ] **README updated:** If public API changed
- [ ] **Inline docs:** Functions have docstrings/comments
- [ ] **Examples updated:** If usage changed
- [ ] **Journal updated:** Progress recorded in `.docs/journal/CURRENT.md`

### Git Hygiene
- [ ] **Branch is clean:** `git status` shows clean working tree
- [ ] **Commits are meaningful:** Clear commit messages
- [ ] **No merge conflicts:** Branch is up-to-date with base
- [ ] **No force-push:** History is clean

---

## Approval Gates

**STOP and request approval before:**

### Changing Build Tooling
**Examples:**
- Switching from npm to yarn
- Adding a new build step
- Changing compiler flags
- Modifying CI/CD workflow files

**Why:** Build tool changes affect all contributors and CI.

**How to request:**
1. Comment on issue/PR: `**APPROVAL NEEDED: Build Tool Change**`
2. Describe the change and rationale
3. List alternatives considered
4. Wait for explicit approval

### Adding Dependencies
**Examples:**
- `npm install <package>`
- `pip install <package>`
- Adding to requirements.txt, package.json, etc.

**Why:** Dependencies increase attack surface and maintenance burden.

**How to request:**
1. See `50_DEPENDENCIES.md` for full policy
2. Run security scanner (GitHub Advisory Database)
3. Document why dependency is needed
4. Request approval before installing

### Structural Refactors
**Examples:**
- Moving files to different directories
- Renaming modules/packages
- Changing file structure
- Splitting or merging files

**Why:** Structural changes affect everyone working on the codebase.

**How to request:**
1. Comment on issue/PR: `**APPROVAL NEEDED: Structural Refactor**`
2. Describe the change and benefits
3. List files affected
4. Wait for explicit approval

---

## CI/CD Integration

### GitHub Actions (if configured)

**Workflow files:** `.github/workflows/*.yml`

**Common workflows:**
- `test-bash.yml` — Run Bash tests
- `test-python.yml` — Run Python 3 tests
- `test-perl.yml` — Run Perl tests
- `test-powershell.yml` — Run PowerShell tests

**CI must pass before merge:**
- All test workflows exit code 0
- No failing jobs
- Required checks configured in repository ruleset

### Pre-commit Hooks (if configured)

**Purpose:** Catch issues before commit.

**Common checks:**
- Linting (shellcheck, pylint, etc.)
- Formatting (prettier, black, etc.)
- Secret scanning
- Test execution (fast tests only)

**If pre-commit fails:**
1. Fix the issue locally
2. Run tests again
3. Commit only when checks pass

---

## Build Artifacts

### What to Commit
- Source code
- Tests
- Documentation
- Configuration files (non-secret)

### What NOT to Commit
- Build artifacts (`dist/`, `build/`, `target/`)
- Dependencies (`node_modules/`, `vendor/`, `.venv/`)
- Log files (`*.log`, `.agent/FAIL-LOGS/*`)
- Temporary files (`*.tmp`, `/tmp/*`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)

**Use `.gitignore`:**
```gitignore
# Build artifacts
dist/
build/
target/

# Dependencies
node_modules/
vendor/
.venv/

# Logs
*.log
.agent/FAIL-LOGS/

# Temp files
*.tmp
/tmp/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## Debugging Failed Builds

### Local Build Failure

**Steps:**
1. Read error message carefully
2. Check exit code (see M0-P2-I2 taxonomy)
3. Review recent changes (`git diff`)
4. Run tests in verbose mode
5. Check logs in `.agent/FAIL-LOGS/` (if using safe-run)

### CI Build Failure

**Steps:**
1. View workflow run in GitHub Actions
2. Identify failing job/step
3. Review logs from failing step
4. Reproduce failure locally
5. Fix and push update

**Common CI failures:**
- Missing dependencies (install in workflow)
- Path issues (use absolute paths or `cd` to correct directory)
- Environment differences (different OS, shell, etc.)
- Timeout (increase timeout or optimize tests)

---

## Performance Optimization

**When to optimize:**
- Build time > 5 minutes
- Test suite time > 60 seconds
- CI pipeline time > 10 minutes

**How to optimize:**
- Parallelize test execution
- Cache dependencies in CI
- Skip unnecessary steps
- Profile slow tests
- Use faster test runners

**When NOT to optimize:**
- Build is already fast enough
- Optimization adds complexity
- Diminishing returns

---

## Continuous Improvement

**After each PR:**
- Review what worked well
- Identify pain points
- Update documentation if needed
- Add automation if manual steps are repetitive

**Quarterly:**
- Review build tooling for updates
- Check for deprecated dependencies
- Audit CI pipeline efficiency
- Update this document with learnings

---

**Version:** 1.0  
**Last Updated:** 2025-12-26  
**Refs:** RFC v0.1.0 section 6.3
