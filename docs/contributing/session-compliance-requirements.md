# Session Start/End Compliance Requirements (Canonical)

**Document Purpose:** This document defines the mandatory compliance requirements for Copilot agents working in this repository. It replaces any ambiguous or conflicting wording about session start, session end, and pre-commit requirements found elsewhere.

**Authority:** This document supersedes any conflicting guidance. When in doubt, follow this document.

**Last Updated:** 2025-12-31

---

## Why This Exists

This repository has experienced repeated compliance failures where Copilot agents:
- Start sessions without required tooling installed
- Commit code without running mandatory lint/format/docstring checks
- End sessions leaving the repository in an unknown state
- Ask for "exact install commands" instead of using the bootstrapper

This document exists to **prevent those failures** by establishing clear, non-negotiable checkpoints.

---

## Session Start Requirements (MANDATORY)

**When:** At the start of EVERY Copilot session, before making any code changes.

### Ordered Checklist

1. **Run the bootstrapper**
   ```bash
   ./scripts/bootstrap-repo-lint-toolchain.sh --all
   ```
   - This script MUST complete with exit code 0
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
     - **0** = No violations (ideal)
     - **1** = Violations found but tools work (acceptable - you'll fix violations later)
   - Unacceptable exit codes:
     - **2** = Missing tools → **BLOCKER**
     - Any other non-zero → investigate

5. **Initialize issue journals** (if working on a tracked issue)
   - For ANY new issue you begin work on, create:
     - `docs/ai-prompt/<ISSUE_NUMBER>/`
     - `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md`
     - Copy the ORIGINAL GitHub issue text into `<ISSUE_NUMBER>-overview.md` in Markdown, preserving checkboxes/tasks

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

**When:** BEFORE EVERY commit that touches ANY of the following:
- Scripts in `scripts/` directory
- Tooling code in `tools/` directory  
- Any `.sh`, `.bash`, `.py`, `.pl`, `.pm`, `.ps1`, `.psm1` files
- Workflow files in `.github/workflows/`

### Ordered Checklist

1. **Run repo-lint conformance check**
   ```bash
   repo-lint check --ci
   ```

2. **Fix ALL reported violations**
   - Linting errors (shellcheck, ruff, pylint, perlcritic, PSScriptAnalyzer)
   - Formatting errors (shfmt, black)
   - Docstring violations (missing sections, wrong format)

3. **Re-run until PASS**
   ```bash
   repo-lint check --ci
   # MUST exit 0 or 1 before committing
   # Exit 2 (missing tools) is a BLOCKER
   ```

4. **Only then commit**
   - Use `report_progress` tool to commit and push

### Exit Code Meanings

- **0** = All checks passed → **OK to commit**
- **1** = Violations found → **FIX, then re-run**
- **2** = Missing tools → **BLOCKER** (escalate with BLOCKED format)

### STOP Conditions

If `repo-lint check --ci` exits with code 2 (MISSING_TOOLS):

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

### Ordered Checklist

1. **Trigger GitHub Copilot Code Review**
   - Request a code review of the PR's latest changes
   - Review all feedback provided by Copilot

2. **Address ALL code review comments**
   - Treat **every** Copilot Code Review comment as a **required action**
   - This includes items labeled "nit", "code quality", "maintainability", "consistency", or "suggestion"
   - Do **not** classify review feedback as "non-blocking" or "nice-to-have"
   - **Nits are not optional**
   - You may skip or partially implement a review comment **only** if implementing it would:
     - break existing behavior, conformance, or CI/contracts, OR
     - violate repo contracts/naming rules, OR
     - exceed explicitly-approved scope constraints for the current PR
   - If you skip or partially implement any review comment, you MUST:
     - Leave a **nearby, durable** note explaining why (function/class docstring, module-level comment, or inline comment)
     - Mention it explicitly in the PR update comment

3. **Verify PR status checks**
   - Ensure all required PR status checks are passing (tests, linters, conformance, etc.)
   - Agents cannot always directly "run" GitHub Actions. Instead:
     - Verify the latest workflow/check runs exist and are passing for the PR's HEAD commit, OR
     - If checks have not triggered, take the minimal action that triggers them (e.g., push a follow-up commit)
   - If CodeQL is configured/enabled: ensure CodeQL is passing
   - If CodeQL is not configured: explicitly state that CodeQL cannot be verified

4. **Update journals**
   - If working on a tracked issue (e.g., `docs/ai-prompt/209/`):
     - Update `{ISSUE}-next-steps.md` with latest DONE entry (per-commit journal)
     - Update `{ISSUE}-issue-overview.md` progress tracker (per-session journal)

5. **Verify repository state**
   - Run final check:
     ```bash
     repo-lint check --ci
     # Exit 0 or 1 is OK
     ```
   - If exit 2 (missing tools): escalate with BLOCKED format

6. **Ensure work is committed**
   - All meaningful progress committed via `report_progress`
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
- No commits without passing pre-commit gate
- No session ends without updating journals

Violations of these requirements constitute non-compliance and will result in rework.

---

## Quick Reference

### Session Start
```bash
./scripts/bootstrap-repo-lint-toolchain.sh --all
source .venv/bin/activate
export PATH="$HOME/perl5/bin:$PATH"
export PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"
repo-lint --help  # verify
repo-lint check --ci  # health check (exit 0 or 1 OK)
```

### Pre-Commit
```bash
repo-lint check --ci  # MUST exit 0
# If exit 1: fix violations, re-run
# If exit 2: BLOCKED - escalate
```

### Session End
```bash
# Update journals in docs/ai-prompt/{ISSUE}/
repo-lint check --ci  # verify state (exit 0 or 1 OK, exit 2 = BLOCKED)
# Commit all work via report_progress
```

---

## Document History

- 2025-12-31: Created canonical session requirements document
