# AI Agent Constraints and Safety Rules

**Status:** Canonical source of truth for AI agent behavior constraints
**Last Updated:** 2025-12-30
**Applies To:** All AI agents, code assistants, and automated tools working in this repository

## Overview

This document defines explicit safety constraints and prohibited operations for AI agents working in this repository.
These rules exist to prevent destructive, irreversible, or dangerous operations that require explicit human oversight
and approval.

**Key Principle:** AI agents are productivity tools, not autonomous decision-makers for dangerous operations. When in
doubt, stop and escalate.

---

## Dangerous Commands — AI Prohibited Without Human Permission

AI agents (including GitHub Copilot, code assistants, and automated bots) are **NOT ALLOWED** to run the following
commands or operations without explicit human permission in the current PR/issue thread.

### Unsafe Fix Mode (STRICTLY PROHIBITED)

- **AI agents MUST NOT run `repo-lint fix --unsafe` under any circumstance.**
- **AI agents MUST NOT run `repo-lint fix --unsafe --yes-i-know` under any circumstance.**
- These are **human-only commands**. They require explicit human permission in the PR thread or issue.
- Unsafe fixes can alter code behavior in non-obvious ways and MUST be human-reviewed before execution.

**Rationale:** Unsafe fixers may change semantics, refactor code structure, or modify comments/docstrings in ways that
require human judgment. Running them without permission risks introducing unintended behavior changes.

### Destructive Cleanup/Uninstall Commands

AI agents MUST NOT run commands that uninstall system-level packages or tools:

- `apt remove`, `apt purge`, `apt autoremove`
- `brew uninstall`, `brew remove`
- `pip uninstall` (system-wide Python packages)
- `npm uninstall -g` (global packages)
- `rm -rf` on system directories (`/usr/`, `/opt/`, `/Library/`, etc.)

**Exception:** `repo-lint install --cleanup` is ALLOWED as it only removes repo-local installations (`.venv-lint/`, `.tools/`, etc.).

**Rationale:** System package removal can break developer environments and is irreversible without reinstallation.

### Repository History Rewriting

AI agents MUST NOT run commands that rewrite Git history:

- `git rebase --onto`
- `git filter-repo`, `git filter-branch`
- `git commit --amend` (on shared branches)
- `git push --force`, `git push --force-with-lease` (on protected branches)
- `git reset --hard` (on shared branches)

**Exception:** `git reset --soft` for local uncommitted work is allowed.

**Rationale:** History rewriting can corrupt shared branches and create merge conflicts for other contributors.

### Broad File Renames/Mass Transformations

AI agents MUST NOT run commands that perform broad, repository-wide changes:

- Mass `sed` sweeps across all files
- Bulk `git mv` operations without explicit file-by-file approval
- Automated refactoring tools that touch >10 files without human review
- `find . -name "*.py" -exec ...` style mass operations

**Rationale:** Mass transformations risk breaking unrelated code and are difficult to review comprehensively.

---

## Escalation Policy for Dangerous Operations

If an AI agent believes a dangerous operation is necessary to complete a task:

1. **STOP immediately** - do not proceed with the operation
2. **Comment on the PR/issue** with the exact opening line:

   ```
   **BLOCKED — HUMAN ACTION REQUIRED**
   ```

3. **Present minimal options** for how to proceed:
   - Explain why the dangerous operation seems necessary
   - List 2-3 alternative approaches (including manual steps)
   - Specify the exact command(s) that would be needed
4. **Mention @m1ndn1nj4** for human attention
5. **Wait for explicit human approval** before proceeding

**Example escalation:**

```
**BLOCKED — HUMAN ACTION REQUIRED**

@m1ndn1nj4 I need to apply unsafe fixes to rewrite docstrings in 15 Python files
to conform to the new contract. This requires `repo-lint fix --unsafe --yes-i-know`.

Options:
A. Human runs the command locally, reviews the patch, and commits manually
B. AI generates a manual checklist of required changes for human review
C. Human grants explicit permission for AI to run unsafe mode in CI (NOT RECOMMENDED)

Evidence: See conformance/repo-lint/vectors/docstrings/python-docstring-001.json
for expected format.
```

---

## Safe Operations (Allowed Without Permission)

The following operations are safe for AI agents to perform:

### Safe Lint/Fix Commands

- `repo-lint check` (read-only, no modifications)
- `repo-lint check --ci` (CI mode, fails on missing tools)
- `repo-lint fix` (safe fixes only: formatters + approved lint auto-fixes)
- `repo-lint install` (installs repo-local tools only)
- `repo-lint install --cleanup` (removes repo-local tools only)

### Safe Development Commands

- `python -m pytest` (run tests)
- `cargo build`, `cargo test` (Rust builds/tests)
- `git status`, `git diff`, `git log` (read-only Git commands)
- `git add`, `git commit` (on feature branches)
- `git push` (on feature branches, non-forced)

### Safe Analysis Commands

- Linters: `black --check`, `ruff check --no-fix`, `pylint`, `shellcheck`, `yamllint`
- Static analysis: `mypy`, `rustfmt --check`
- Dependency checks: `cargo audit`, `pip check`

---

## Integration with repo_lint Documentation

This AI constraints contract is referenced from:

- `tools/repo_lint/README.md` - repo_lint CLI documentation
- `CONTRIBUTING.md` - Main contributor guide
- `.github/copilot-instructions.md` - Agent behavior instructions

Any documentation of `repo-lint fix --unsafe` or `--yes-i-know` MUST link to this document and include prominent warnings.

---

## Updates to This Contract

Changes to this contract require:

1. PR with explicit rationale for the change
2. Review by repository maintainers
3. Update to "Last Updated" timestamp
4. Update to all documents that link here

**Do NOT** modify this contract as part of routine feature work or bug fixes.

---

## Enforcement

- **AI agents:** Follow these rules via `.github/copilot-instructions.md`
- **CI/CD:** `repo-lint fix --unsafe` is blocked in CI (hard-coded guard)
- **Humans:** Use personal judgment, but document risky operations in commit messages

Violations of these constraints by AI agents should be reported as bugs against the agent configuration.
