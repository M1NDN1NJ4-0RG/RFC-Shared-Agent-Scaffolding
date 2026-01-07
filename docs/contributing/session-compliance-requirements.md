# Session Start/End Compliance Requirements (Canonical)

**Document Purpose:** This document defines the mandatory compliance requirements for Copilot agents working in this repository. It replaces any ambiguous or conflicting wording about session start, session end, and pre-commit requirements found elsewhere.

**Authority:** This document supersedes any conflicting guidance. When in doubt, follow this document.

**MANDATORY READING:** Every Copilot agent MUST read this entire document IMMEDIATELY when starting NEW work. Failure to read this document when starting NEW work is a violation.

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

## In-Session Work Requirements (MANDATORY)

This document is not a “planning exercise.” After Session Start completes successfully, you MUST execute the requested work.

### Non-negotiable behavior

- **No “bootstrap + catch-up only” sessions.** Completing session-start and then stopping to summarize “what we should do next” is a violation unless you are blocked or near context limits.
- **Implementation over narration.** Do the work. Output only actionable items: errors encountered and the exact next command/file change you are making.
- **Minimum progress rule:** In every session, you MUST do at least one of the following:
  - Produce a meaningful commit (preferred), OR
  - Create/update the issue journals with a concrete, file-path-level plan and clear resume instructions, OR
  - Escalate with `**BLOCKED — HUMAN ACTION REQUIRED**` (canonical format) with exact error output.

### Work loop (how to behave during the session)

After Session Start completes (exit 0):
1. Identify the active issue number and ensure the journals exist in:
   - `docs/ai-prompt/{ISSUE_NUMBER}/`
2. Read:
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-overview.md`
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-next-steps.md`
3. Execute the “NEXT” work items immediately. Do not stop after planning.

### “Near context limit” escape hatch (ONLY IF NECESSARY)

If you are getting close to token/window/context limits at any time:
1. Stop starting new work.
2. Commit whatever is already correct and complete.
3. Update:
   - `{ISSUE_NUMBER}-summary.md` (this commit’s work),
   - `{ISSUE_NUMBER}-overview.md` (checkbox/task progress),
   - `{ISSUE_NUMBER}-next-steps.md` with extremely detailed resume steps:
     - exact remaining checklist items
     - exact next commands to run
     - exact files/sections to open next
4. Push the branch so the next session can resume immediately.

---

## Session Start Requirements (MANDATORY)

**When:** At the start of NEW work sessions, **IMMEDIATELY** upon receiving the first user message, before ANY file exploration, repository analysis, problem investigation, or code changes.

**PROHIBITION (for NEW work only):** You may NOT read files, explore the repository, analyze the problem, or plan changes until the bootstrapper has completed successfully (exit code 0).

### Ordered Checklist

1. **Run the bootstrapper**
   ~~~bash
   ./scripts/session-start.sh
   ~~~
   - This script MUST complete with exit code 0
   - Typical completion time: 3-10 minutes
   - If it takes longer than 15 minutes or appears hung, STOP it and escalate
   - It installs/verifies ALL required tools (Python, Bash, PowerShell, Perl)
   - It creates/configures the `.venv/` virtual environment (activation happens in Step 2)
   - It installs the `repo-lint` package

2. **Activate the environment**
   ~~~bash
   source .venv/bin/activate && \
     PERL_HOME="$HOME/perl5" && \
     export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
     export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
     export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
     export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
     export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}"
   ~~~

3. **Verify `repo-lint` is functional**
   ~~~bash
   source .venv/bin/activate && \
     PERL_HOME="$HOME/perl5" && \
     export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
     export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
     export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
     export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
     export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}" && \
     repo-lint --help
   ~~~
   - MUST exit 0 and show help text

4. **Run health check** (minimal verification)
   ~~~bash
   source .venv/bin/activate && \
     PERL_HOME="$HOME/perl5" && \
     export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
     export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
     export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
     export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
     export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}" && \
     repo-lint check --ci
   ~~~
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
     - `docs/ai-prompt/{ISSUE_NUMBER}/`
     - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-overview.md`
     - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-next-steps.md`
     - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-summary.md`
     - Copy the ORIGINAL GitHub issue text into `{ISSUE_NUMBER}-overview.md` in Markdown, preserving checkboxes/tasks
        - This document needs to be updated with boxes checked as you go.

   **Journal File Definitions (NON-NEGOTIABLE)**

   - `docs/ai-prompt/{ISSUE_NUMBER}/` is the issue journal directory.

   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-overview.md`
     - MUST contain a copy of the ORIGINAL GitHub issue body (verbatim, in Markdown).
     - MUST be updated during the session to reflect progress (checkboxes checked, tasks completed).
     - Purpose: so the human can update the GitHub issue body to match the repo state (especially for EPIC / multi-PR issues).

   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-next-steps.md`
     - MUST contain extremely detailed, step-by-step next actions.
     - MUST include an extremely detailed “prompt to Copilot” so the next session can start with minimal catch-up.

   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-summary.md`
     - MUST be updated with EVERY COMMIT (not just at session end).
     - Put the latest changes, what was completed, and what remains, in a concise but concrete way.

   - **MANDATORY FIRST LINE in every `{ISSUE_NUMBER}-next-steps.md` file:**
     ~~~
     MANDATORY FIRST ACTION: Read `.github/copilot-instructions.md` and follow ALL REQUIREMENTS in `docs/contributing/session-compliance-requirements.md` BEFORE doing ANYTHING else. Non-negotiable.
     ~~~
   - Update journals EVERY session, even for minor changes

### Additional Rules

- If any required tool is missing (including any tool required by `repo-lint`), the bootstrapper will attempt to install it.
- If installation is blocked by environment constraints, escalate using `**BLOCKED — HUMAN ACTION REQUIRED**` and list the missing tools.
- Use `rg` (ripgrep) as the canonical grep/search tool for repository work unless a human explicitly instructs otherwise.
- Do NOT proceed with scripting/tooling work until `repo-lint` is installed, on PATH, and functional.


If any of the above steps fail:

1. **STOP immediately**
2. **Do NOT proceed with code changes**
3. **Escalate using the exact format below:**

~~~
**BLOCKED — HUMAN ACTION REQUIRED**

Bootstrapper failed at step: [step name]
Exit code: [number]
Error message:
[paste exact error]

Missing tools (if applicable): [list]

Manual install suggestions:
[paste from bootstrapper output]
~~~

---

## Pre-Commit Gate Requirements (MANDATORY)

**When:** BEFORE EVERY commit, period. No exceptions. This applies to ALL file types (scripts, docs, configs, workflows, everything).

**Rationale:** While the gate primarily validates scripts/tooling, repo-lint may check any file type. Run the full gate regardless of what you're committing.

**Hard requirement:** Any time you run a `repo-lint` command during this workflow, you MUST run it with the full venv + Perl environment activation block shown below (the multiline `source .venv/bin/activate` + `PERL_HOME` + exports). Do NOT shorten it or “assume” the environment is already configured.

**Exception:** Running `./scripts/session-end.sh` for repair is allowed without the activation block because it is the wrapper that self-heals/installs missing components.

### Ordered Checklist

1. **Ensure the environment is active** (pre-commit uses the fast path)
   ~~~bash
   source .venv/bin/activate && \
     PERL_HOME="$HOME/perl5" && \
     export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
     export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
     export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
     export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
     export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}"
   ~~~

2. **Run the pre-commit gate (FAST)**
   ~~~bash
   repo-lint check --ci
   ~~~

3. **Fix ALL reported violations**
   - Linting errors (shellcheck, ruff, pylint, perlcritic, PSScriptAnalyzer)
   - Formatting errors (shfmt, black)
   - Docstring violations (missing sections, wrong format)

4. **Re-run until exit code 0**
   ~~~bash
   repo-lint check --ci
   # MUST exit 0 before committing
   # Exit code 0 = ALL checks passed, OK to commit
   # Exit code 1 = Violations still exist, NOT OK to commit - fix and re-run
   # Exit code 2 = Missing tools / broken environment, NOT OK - run session-start/session-end to repair
   ~~~

5. **Update the issue summary BEFORE committing (MANDATORY)**
   - Update `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-summary.md` to reflect what this commit contains.
   - This file MUST be updated with EVERY commit.

6. **Only then commit**
   - Use `report_progress` tool to commit and push
   - You may NOT commit if exit code is 1 or 2

**Repair rule (only if needed):**
- If `repo-lint` is not found, or `repo-lint check --ci` exits **2**, run:
  ~~~bash
  ./scripts/session-end.sh
  ~~~
  Then re-run `repo-lint check --ci` until it exits 0.

### Exit Code Meanings

These exit codes refer to `repo-lint check --ci`:

- **0** = All checks passed → **OK to commit**
- **1** = Violations found → **NOT OK to commit** (fix violations, then re-run until exit 0)
- **2** = Missing tools / broken environment → **BLOCKER** (run `./scripts/session-end.sh` to repair; if still failing, escalate)

### STOP Conditions

If `./scripts/session-end.sh` exits with code 1 or 2:

**Exit Code 1:**
1. **Do NOT commit**
2. **Fix the violations**
3. **Re-run `./scripts/session-end.sh` until exit 0**
4. **Then commit**

**Exit Code 2:**
1. **STOP immediately**
2. **Do NOT commit**
3. **Escalate:**

~~~
**BLOCKED — HUMAN ACTION REQUIRED**

Pre-commit gate failed: missing tools
Exit code: 2

repo-lint output:
[paste output showing which tools are missing]

Attempted fix: [what you tried]
~~~

---

## Session End Requirements (MANDATORY)

**When:** At the end of EVERY Copilot session, before terminating.

**Requirement:** ALL work must be done on a Pull Request. Before making any code changes, ensure a PR exists (or create one). If you're working on code without a PR, that's a violation - create the PR immediately.

### Ordered Checklist

1. **Run the pre-commit gate (FAST)**
   - Use the full environment activation block from the Pre-Commit section, then run:
     ~~~bash
     repo-lint check --ci
     ~~~
   - Fix violations and re-run until exit code **0**.

2. **Commit changes**
   - Commit ALL meaningful work via `report_progress`.
   - Do not leave useful work uncommitted.

3. **If possible: approve any pending workflows and wait for the repo-lint umbrella workflow**
   - If the platform/UI allows approving pending workflows for the branch/PR, approve them.
   - Wait for the repo-lint umbrella workflow to finish.
   - If the umbrella workflow auto-fixes issues, pull/apply those updates as required.

4. **Initiate Copilot Code Review (MANDATORY)**
   - Trigger Copilot Code Review on the PR’s latest changes.

5. **Address ALL Copilot Code Review comments (MANDATORY)**
   - Treat **every** Copilot Code Review comment as a **required action**.
   - You may skip a comment **ONLY** if implementing it would:
     - Break existing, passing tests or CI checks (verified), OR
     - Violate an explicit technical constraint stated in the issue/PR description.
   - If you defer an item for **future usage**, you MUST:
     - Leave a nearby, durable `TODO` / `FUTURE:` note in the relevant file explaining **what** and **why**.
     - Only comment out code when necessary to keep builds/tests passing (e.g., Rust compile/build).

6. **Verify PR status checks**
   - Ensure required checks are passing for the PR’s HEAD commit.
   - If checks have not triggered, wait up to 5 minutes; if still no CI run, escalate using BLOCKED format.

7. **Update journals (ALWAYS REQUIRED)**
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-summary.md`
     - MUST already be current because it is required with EVERY commit.
     - If anything changed since the last commit, update it and include it in the final commit.

   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-overview.md`
     - Update to reflect session progress (checkboxes/tasks updated) so it matches the repo state.

   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-next-steps.md`
     - Update with extremely detailed next steps and a detailed prompt to Copilot to resume work.

8. **Verify repository state (SESSION END GATE)**
   ~~~bash
   ./scripts/session-end.sh
   # MUST exit 0 before ending the session.
   # Exit 0 = clean, OK to end session
   # Exit 1 = violations exist - fix violations, then re-run until exit 0
   # Exit 2 = missing tools - BLOCKER, escalate
   ~~~

9. **Ensure ALL work is committed**
   - After the session-end gate passes, ensure there are no uncommitted changes that would be lost.

### STOP Conditions

If `./scripts/session-end.sh` exits with code 1:

1. **Do NOT end the session**
2. **Fix the violations**
3. **Re-run `./scripts/session-end.sh` until exit 0**
4. **Only then end the session**

If repository is in unknown state (exit code 2, tools missing):

1. **Update journals documenting the blocker**
2. **Escalate:**

~~~
**BLOCKED — HUMAN ACTION REQUIRED**

Session ending with repository in unknown state.
repo-lint check --ci exit code: 2

Missing tools: [list]

Last known good state: [commit hash]
Current blocker: [description]
~~~

---

## Required Tools Definition

"Required tools" means ALL of the following are installed and functional:

### Core Utilities
- `rg (ripgrep)`

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

### GitHub Actionlint
- `actionlint` (linter for GitHub Action Workflows)

The session bootstrapper (`./scripts/session-start.sh`) installs/verifies ALL of these (it may delegate to scripts/bootstrap-repo-lint-toolchain.sh internally).

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

~~~
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
~~~

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
~~~bash
cd /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding && \
  ./scripts/session-start.sh
~~~
#### MUST exit 0, typical runtime 90-600 seconds

~~~bash
source .venv/bin/activate && \
  PERL_HOME="$HOME/perl5" && \
  export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
  export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
  export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
  export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
  export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}" && \
  repo-lint --help && \
  repo-lint check --ci
~~~

#### Exit 1 OK here because repo may have pre-existing violations, typical runtime 90-600 seconds

### Pre-Commit (BEFORE EVERY commit, ALL file types)
~~~bash
source .venv/bin/activate && \
  PERL_HOME="$HOME/perl5" && \
  export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
  export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
  export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
  export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
  export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}" && \
  repo-lint check --ci
~~~

#### MUST exit 0 before commit, typical runtime 90-600 seconds
#### Exit 0 = OK to commit
#### Exit 1 = violations exist, NOT OK - fix violations, re-run until 0
#### Exit 2 = environment/tools missing - run ./scripts/session-end.sh to repair, then re-run repo-lint check --ci
#### If Exit 2 persists AFTER repair, escalate using BLOCKED format

### Session End (BEFORE terminating)
#### Commit ALL meaningful work via report_progress BEFORE running ./scripts/session-end.sh
#### After ./scripts/session-end.sh passes, ensure there are no uncommitted changes

1. Run pre-commit gate: `repo-lint check --ci` (must exit 0)
1. Commit ALL meaningful work via report_progress
1. If possible, approve pending workflows and wait for the repo-lint umbrella workflow
1. Initiate Copilot Code Review (mandatory)
1. Treat ***ALL*** Copilot callouts as mandatory unless:
  - Implementing the suggestion would ***break something***, OR
  - There is a ***specific, concrete reason*** tied to future work, or a specific migration plan to keep the current approach.
  - If you do not apply a callout:
    - Leave an explicit note explaining ***why***.
1. Verify PR status checks passing
1. Update journals in docs/ai-prompt/{ISSUE}/ (always required)
1. Verify state:

~~~bash
./scripts/session-end.sh
~~~
#### Exit 0 OK,
#### Exit 1 Violations need to be fixed
#### Exit 2 = BLOCKER

**Key Differences:**
- Session start: exit 1 acceptable (pre-existing issues)
- Pre-commit: exit 0 required (YOUR changes must be clean)
- Session end: exit 0 required (must fix violations before ending the session)

---

## Document History

- 2025-12-31: Created canonical session requirements document
