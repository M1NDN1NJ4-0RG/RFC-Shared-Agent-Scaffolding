# Session Start/End Compliance Requirements (Canonical)

**Document Purpose:** This document defines the mandatory compliance requirements for Copilot agents working in this repository. It replaces any ambiguous or conflicting wording about session start, session end, and pre-commit requirements found elsewhere.

**Authority:** This document supersedes any conflicting guidance. When in doubt, follow this document.

**MANDATORY READING:** Every Copilot agent MUST read this entire document IMMEDIATELY at session start, before ANY file exploration, repository analysis, or code changes. Failure to read this document is a violation.

**Last Updated:** 2025-12-31

---

## Why This Exists

This repository has experienced repeated compliance failures where Copilot agents:
- Start sessions without required tooling installed
- Commit code without running mandatory lint/format/docstring checks
- End sessions leaving the repository in an unknown state
- Ask for "exact install commands" instead of using the bootstrapper
- Skip quality gates by exploiting ambiguous wording

This document exists to **prevent those failures** by establishing clear, non-negotiable checkpoints with no loopholes.

---

## Session Start Requirements (MANDATORY)

**When:** At the start of EVERY Copilot session, **IMMEDIATELY** upon receiving the first user message, before ANY file exploration, repository analysis, problem investigation, or code changes.

**PROHIBITION:** You may NOT read files, explore the repository, analyze the problem, or plan changes until the bootstrapper has completed successfully (exit code 0).

### Ordered Checklist

1. **Run the bootstrapper**
   ```bash
   # First navigate to repository root
   cd /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
   # Then run bootstrapper
   ./scripts/bootstrap-repo-lint-toolchain.sh --all
   ```
   - This script MUST complete with exit code 0
   - Typical completion time: 3-10 minutes
   - If it takes longer than 15 minutes or appears hung, STOP it and escalate
   - It installs/verifies ALL required tools (Python, Bash, PowerShell, Perl)
   - It creates and activates the `.venv/` virtual environment
   - It installs the `repo-lint` package

2. **Activate the environment**
   ```bash
   source .venv/bin/activate
   export PATH="$HOME/perl5/bin:$PATH"
   export PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"
   ```

3. **Verify `repo-lint` is functional**
   ```bash
   repo-lint --help
   ```
   - MUST exit 0 and show help text

4. **Run health check** (minimal verification)
   ```bash
   repo-lint check --ci
   ```
   - Acceptable exit codes:
     - **0** = No violations (ideal - repo is clean)
     - **1** = Violations found but tools work (acceptable - repo has pre-existing issues you'll fix before committing YOUR changes)
   - Unacceptable exit codes:
     - **2** = Missing tools → **BLOCKER** - escalate immediately
     - Any other non-zero → **BLOCKER** - escalate immediately with exact exit code and full error output
   
   **Clarification:** Exit code 1 is acceptable ONLY at session start because the repository may have pre-existing violations. This does NOT mean you can commit with exit code 1. Before committing YOUR changes, pre-commit gate requires exit code 0.

5. **Initialize issue journals** (ALWAYS REQUIRED)
   - ALL work must be associated with a tracked issue
   - If the request isn't linked to an issue: ask the human to create one, or work in an existing catch-all issue
   - For ANY new issue you begin work on, create:
     - `docs/ai-prompt/<ISSUE_NUMBER>/`
     - `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md`
     - Copy the ORIGINAL GitHub issue text into `<ISSUE_NUMBER>-overview.md` in Markdown, preserving checkboxes/tasks
   - Update journals EVERY session, even for minor changes

### Additional Rules

- If any required tool is missing (including any tool required by `repo-lint`), the bootstrapper will attempt to install it.
- If installation is blocked by environment constraints, escalate using `**BLOCKED — HUMAN ACTION REQUIRED**` and list the missing tools.
- Use `rgrep` as the default grep/search tool for repository work unless a human explicitly instructs otherwise.
- Do NOT proceed with scripting/tooling work until `repo-lint` is installed, on PATH, and functional.

### STOP Conditions

If any of the above steps fail:

1. **STOP immediately**
2. **Do NOT proceed with code changes**
3. **Escalate using the exact format below:**

```
**BLOCKED — HUMAN ACTION REQUIRED**

Bootstrapper failed at step: [step name]
Exit code: [number]
Error message:
[paste exact error]

Missing tools (if applicable): [list]

Manual install suggestions:
[paste from bootstrapper output]
```

---

## Pre-Commit Gate Requirements (MANDATORY)

**When:** BEFORE EVERY commit, period. No exceptions. This applies to ALL file types (scripts, docs, configs, workflows, everything).

**Rationale:** While the gate primarily validates scripts/tooling, repo-lint may check any file type. Run the full gate regardless of what you're committing.

### Ordered Checklist

1. **Run repo-lint conformance check**
   ```bash
   repo-lint check --ci
   ```

2. **Fix ALL reported violations**
   - Linting errors (shellcheck, ruff, pylint, perlcritic, PSScriptAnalyzer)
   - Formatting errors (shfmt, black)
   - Docstring violations (missing sections, wrong format)

3. **Re-run until exit code 0**
   ```bash
   repo-lint check --ci
   # MUST exit 0 before committing
   # Exit code 0 = ALL checks passed, OK to commit
   # Exit code 1 = Violations still exist, NOT OK to commit - fix and re-run
   # Exit code 2 = Missing tools, BLOCKER - escalate
   ```

4. **Only then commit**
   - Use `report_progress` tool to commit and push
   - You may NOT commit if exit code is 1 or 2

### Exit Code Meanings

- **0** = All checks passed → **OK to commit**
- **1** = Violations found → **NOT OK to commit** - FIX violations, then re-run until exit 0
- **2** = Missing tools → **BLOCKER** (escalate with BLOCKED format)

### STOP Conditions

If `repo-lint check --ci` exits with code 1 or 2:

**Exit Code 1:**
1. **Do NOT commit**
2. **Fix the violations**
3. **Re-run until exit 0**
4. **Then commit**

**Exit Code 2:**
1. **STOP immediately**
2. **Do NOT commit**
3. **Escalate:**

```
**BLOCKED — HUMAN ACTION REQUIRED**

Pre-commit gate failed: missing tools
Exit code: 2

repo-lint output:
[paste output showing which tools are missing]

Attempted fix: [what you tried]
```

---

## Session End Requirements (MANDATORY)

**When:** At the end of EVERY Copilot session, before terminating.

**Requirement:** ALL work must be done on a Pull Request. Before making any code changes, ensure a PR exists (or create one). If you're working on code without a PR, that's a violation - create the PR immediately.

### Ordered Checklist

1. **Trigger GitHub Copilot Code Review**
   - Request a code review of the PR's latest changes
   - Review all feedback provided by Copilot
   - Code review is MANDATORY for every session that includes code changes

2. **Address ALL code review comments**
   - Treat **every** Copilot Code Review comment as a **required action**
   - This includes items labeled "nit", "code quality", "maintainability", "consistency", or "suggestion"
   - Do **not** classify review feedback as "non-blocking" or "nice-to-have"
   - **Nits are not optional**
   - You may skip a review comment **ONLY** if implementing it would:
     - Break existing, passing tests or CI checks (verified by running tests), OR
     - Violate an explicit technical constraint stated in the issue/PR description, OR
     - Require changes to files explicitly marked out-of-scope in the PR description
   - You may NOT skip a comment because it "exceeds scope" or is "too much work"
   - If you skip or partially implement any review comment, you MUST:
     - Leave a **nearby, durable** note explaining why (function/class docstring, module-level comment, or inline comment)
     - Mention it explicitly in the PR update comment, including WHAT was skipped and WHY

3. **Verify PR status checks**
   - Ensure all required PR status checks are passing (tests, linters, conformance, etc.)
   - Agents cannot always directly "run" GitHub Actions. Instead:
     - Verify the latest workflow/check runs exist and are passing for the PR's HEAD commit, OR
     - If checks haven't triggered on your latest commit, wait up to 5 minutes
     - If still no CI run after 5 minutes, escalate using BLOCKED format
     - Do NOT create empty or trivial commits solely to trigger CI
   - If CodeQL is configured/enabled: ensure CodeQL is passing
   - If CodeQL is not configured: explicitly state that CodeQL cannot be verified

4. **Update journals** (ALWAYS REQUIRED - NO EXCEPTIONS)
   - Update journals for EVERY session, even minor changes
   - If working on a tracked issue (e.g., `docs/ai-prompt/209/`):
     - Update `{ISSUE}-next-steps.md` with latest DONE entry (per-commit journal)
     - Update `{ISSUE}-issue-overview.md` progress tracker (per-session journal)
   - If not on a tracked issue: create one or use catch-all issue

5. **Verify repository state**
   - Run final check:
     ```bash
     repo-lint check --ci
     # Exit 0 or 1 is OK (same reasoning as session start)
     # Exit 0 = clean
     # Exit 1 = pre-existing violations (not from your changes - acceptable)
     # Exit 2 = missing tools - BLOCKER, escalate
     ```

6. **Ensure ALL work is committed**
   - ALL changes committed via `report_progress`, including:
     - Completed features/fixes
     - Work-in-progress changes (mark as WIP in commit message)
     - Experimental changes that inform the solution
     - ANY modified files that contain useful information
   - Only exclude: temporary test files, build artifacts, or debugging output
   - No uncommitted changes that would be lost

### STOP Conditions

If repository is in unknown state (exit code 2, tools missing):

1. **Update journals documenting the blocker**
2. **Escalate:**

```
**BLOCKED — HUMAN ACTION REQUIRED**

Session ending with repository in unknown state.
repo-lint check --ci exit code: 2

Missing tools: [list]

Last known good state: [commit hash]
Current blocker: [description]
```

---

## Required Tools Definition

"Required tools" means ALL of the following are installed and functional:

### Core Utilities
- `rgrep` or `grep` (with warning if grep)

### Python Toolchain (always required)
- `black` (formatter)
- `ruff` (linter)
- `pylint` (linter)
- `yamllint` (YAML linter)
- `pytest` (test framework)
- `repo-lint` (this repository's linting tool)

### Shell Toolchain (required for shell script changes)
- `shellcheck` (linter)
- `shfmt` (formatter)

### PowerShell Toolchain (required for PowerShell script changes)
- `pwsh` (PowerShell interpreter)
- `PSScriptAnalyzer` (linter)

### Perl Toolchain (required for Perl script changes)
- `perlcritic` (linter, from Perl::Critic)
- `PPI` (Perl parsing library)

The bootstrapper (`scripts/bootstrap-repo-lint-toolchain.sh --all`) installs ALL of these.

---

## Rule of Three (MANDATORY) — Repository Automation Only

This rule applies to **repository automation and tooling**, including:
- `tools/` code (repo tooling packages like `repo_lint`)
- `scripts/` (bash/python/perl/ps1 utilities)
- CI/workflows (`.github/workflows/`)
- test harnesses, fixtures, validators, conformance runners
- build/lint orchestration, log/forensics generation, plumbing code

It does **NOT** automatically apply to product/runtime/business logic unless a human explicitly says so.

### Requirement

If you implement the same logic **3+ times** within the scope above (copy/paste or near-identical patterns), you MUST refactor it into a shared helper.

### Rules

- Create a single helper in the most appropriate shared location (prefer existing shared modules; don't invent new structure unnecessarily).
- Update all call sites to use the helper (don't leave duplicate variants unless there is a real behavioral difference).
- Add/extend tests to lock behavior so the refactor does not change semantics.
- If refactoring would break existing behavior/contracts, STOP and document why using the repo's "durable note" rule.
- If two implementations must remain separate, explicitly document the reason and the behavioral difference (durable note).

### Enforcement

This is **MANDATORY** for repository tooling/scripting. Violations constitute non-compliance and will result in rework.

---

## Escalation Format (Canonical)

When blocked, use EXACTLY this format:

```
**BLOCKED — HUMAN ACTION REQUIRED**

[1-2 sentence description of blocker]

Context:
- Step that failed: [step name]
- Exit code: [number]
- Command run: [exact command]

Error output:
[paste relevant error message]

What I tried:
[list attempted fixes]

Suggested options:
1. [option 1]
2. [option 2]
```

Tag @m1ndn1nj4 if escalating.

---

## Enforcement

- These requirements are **non-negotiable**
- No "out of scope" deferrals for missing tools
- No "I'll fix it later" for lint violations
- No commits without passing pre-commit gate (exit code 0 required)
- No session ends without updating journals
- No work without an associated Pull Request

Violations of these requirements constitute non-compliance and will result in rework.

**Consequences for Repeated Violations:**
- First violation: Rework required, feedback provided
- Second violation in same session/PR: Session terminated, work reassigned
- Pattern of violations across sessions: Agent flagged for review

**What Counts as a Violation:**
- Committing with exit code 1 or 2
- Skipping bootstrapper at session start
- Not running code review before session end
- Not updating journals
- Working without a PR
- Exploiting loopholes or ambiguous wording in bad faith

---

## Quick Reference

### Session Start (IMMEDIATELY upon first message)
```bash
cd /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
./scripts/bootstrap-repo-lint-toolchain.sh --all  # MUST exit 0, typical 3-10 min
source .venv/bin/activate
export PATH="$HOME/perl5/bin:$PATH"
export PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"
repo-lint --help  # verify (MUST exit 0)
repo-lint check --ci  # health check (exit 0 or 1 OK, exit 2 = BLOCKER)
# Exit 1 OK here because repo may have pre-existing violations
```

### Pre-Commit (BEFORE EVERY commit, ALL file types)
```bash
repo-lint check --ci  # MUST exit 0 before commit
# Exit 0 = OK to commit
# Exit 1 = violations exist, NOT OK - fix violations, re-run until 0
# Exit 2 = BLOCKER - escalate immediately
```

### Session End (BEFORE terminating)
```bash
# 1. Trigger Copilot Code Review (mandatory)
# 2. Address ALL review comments (nits not optional)
# 3. Verify PR status checks passing
# 4. Update journals in docs/ai-prompt/{ISSUE}/ (always required)
# 5. Verify state:
repo-lint check --ci  # exit 0 or 1 OK, exit 2 = BLOCKER
# 6. Commit ALL work via report_progress
```

**Key Differences:**
- Session start: exit 1 acceptable (pre-existing issues)
- Pre-commit: exit 0 required (YOUR changes must be clean)
- Session end: exit 0 or 1 acceptable (state verification only)

---

## Document History

- 2025-12-31: Created canonical session requirements document
