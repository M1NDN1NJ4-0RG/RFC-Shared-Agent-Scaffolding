# Git Workflow & PR Management

**Status:** Standard operating procedure for git and PR workflows.
**Load:** When creating PRs, managing branches, or working with git.

---

## 1. Mode Detection (MANDATORY)

**Before any PR work, detect the operational mode:**

### Safe Mode

**Indicators:**

- No `.git` directory present
- Git present but no auto-merge preflight proven
- No `.agent/auto-merge.enabled` feature flag

**Allowed operations in Safe Mode:**

- Create patches/diffs
- Snapshot changes
- Manual PR workflow only
- NO auto-merge

### Auto-Merge Mode

**Indicators:**

- Git present
- Preflight validation passed (see `22_AUTOMERGE_PREFLIGHT.md`)
- `.agent/auto-merge.enabled` feature flag present

**Allowed operations in Auto-Merge Mode:**

- All Safe Mode operations
- Enable auto-merge on PRs
- Wait for CI before merge
- See `21_AUTO_MERGE_WAITING.md` for timing constants

**Rule:** When in doubt, operate in Safe Mode.

---

## 2. Branch Naming Conventions

**Format:** `<category>/<short-description>`

**Categories:**

- `feature/` — New features
- `fix/` — Bug fixes
- `refactor/` — Code refactoring
- `docs/` — Documentation changes
- `test/` — Test additions or fixes
- `chore/` — Maintenance tasks

**Examples:**

- `feature/add-logging-semantics`
- `fix/safe-run-exit-codes`
- `refactor/split-monolithic-test`
- `docs/update-readme-templates`

**Rules:**

- Branch name should be kebab-case (lowercase, hyphen-separated)
- Keep branch names under 50 characters
- Avoid special characters except `/` and `-`

---

## 3. Commit Message Standards

**Format:**

```
<type>: <summary>

[optional body]

[optional footer]
```

**Types:**

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `test:` — Test changes
- `refactor:` — Code refactoring
- `chore:` — Maintenance

**Summary rules:**

- Use imperative mood ("Add feature" not "Added feature")
- Keep summary under 72 characters
- No period at the end

**Body rules (optional):**

- Explain WHY the change was made, not just WHAT
- Wrap at 72 characters
- Separate from summary with blank line

**Footer rules (optional):**

- `Refs: #issue-number` — Link to issue (non-closing)
- `Related to: #issue-number` — Related issue (non-closing)
- **NEVER use auto-close keywords** for epic issues (Fixes, Closes, Resolves)

**Examples:**

```
feat: Add split stdout/stderr logging to safe-run

Implements M0-P1-I1 contract decision. Captures stdout and stderr
separately with explicit markers for easier debugging.

Refs: #3
```

```
fix: Correct exit code for missing auth

Changes exit code from 1 to 2 when authentication is missing,
per M0-P2-I2 exit code taxonomy.

Refs: #3
```

---

## 4. PR Creation Workflow

### Step 1: Create Branch

```bash
git checkout -b <category>/<description>
```

### Step 2: Make Changes

- Follow `10_CORE_RULES.md` (small chunks, tests first)
- Commit frequently with clear messages
- Use `report_progress` tool to commit and push

### Step 3: Create PR

**PR Title format:** `<type>: <summary>`

- Same rules as commit summary
- Should match the primary commit if single-commit PR

**PR Description must include:**

- What changed (checklist of completed work)
- Why it changed (context, issue reference)
- How to verify (commands to run)
- Related issue reference (use `Refs:` not `Fixes:`)

**Example PR description:**

```markdown
## Summary
Implements M0-P1-I1: Split stdout/stderr logging semantics.

## Changes
- [x] Update safe-run.sh to capture streams separately
- [x] Add === STDOUT === and === STDERR === markers
- [x] Update tests to validate markers
- [x] Verify all tests pass

## Verification
```bash
cd RFC-Shared-Agent-Scaffolding-Example/scripts/bash
./run-tests.sh
```

## References

Refs: #3 (Epic Tracker - M0-P1-I1)

```

### Step 4: Verify Before Submission
- [ ] All tests pass locally
- [ ] Linters pass (if configured)
- [ ] Build succeeds (if applicable)
- [ ] No secrets or credentials in code
- [ ] Commit messages follow standards

---

## 5. PR Management

### Responding to Review Comments
- Address all comments before requesting re-review
- Use `git commit --fixup` for small fixes
- Avoid force-push unless absolutely necessary
- Keep PR conversation focused on the change

### Updating PR After Feedback
```bash
# Make fixes
git add .
git commit -m "fix: Address review feedback"
git push origin <branch-name>
```

### Merge Strategy

**Default:** Squash and merge (keeps history clean)

**Exceptions:**

- Large refactors may use merge commits
- Preserve commit structure only when explicitly required

---

## 6. Working Tree Hygiene

### Before Starting Work

```bash
git status          # Check clean working tree
git fetch origin    # Get latest changes
git pull --rebase   # Update local branch
```

### During Work

```bash
git status          # Check uncommitted changes
git diff            # Review changes before commit
git add -p          # Stage changes interactively (if needed)
```

### After PR Merged

```bash
git checkout main
git pull origin main
git branch -d <feature-branch>  # Delete local branch
```

---

## 7. Feature Flags

**Location:** `.agent/` directory

**Example flags:**

- `.agent/auto-merge.enabled` — Enables auto-merge mode
- `.agent/strict-mode.enabled` — Enables strict validation

**Rules:**

- Flags are empty files (presence = enabled, absence = disabled)
- Flags persist across context resets
- Flags allow graceful degradation

**Creating a flag:**

```bash
mkdir -p .agent
touch .agent/auto-merge.enabled
git add .agent/auto-merge.enabled
git commit -m "feat: Enable auto-merge mode"
```

---

## 8. Conflict Resolution

**When conflicts occur:**

1. **STOP** - Do not attempt to resolve conflicts yourself
2. Comment on PR: `**BLOCKED — MERGE CONFLICT**`
3. Describe the conflicting files
4. Request human intervention
5. Wait for explicit resolution instructions

**Why:** Git conflicts often involve context that agents lack. Human judgment prevents data loss.

---

## 9. Default Branch Protection

**Rule:** The default branch (usually `main` or `master`) is untouchable.

**All work happens on feature branches:**

- Create branch from default branch
- Make changes on feature branch
- PR from feature branch to default branch
- Merge via PR only (no direct commits to default)

**Exception:** Updating `.docs/journal/CURRENT.md` may happen on default branch if project policy allows.

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Refs:** RFC v0.1.0 sections 4.2, 5.1-5.3
