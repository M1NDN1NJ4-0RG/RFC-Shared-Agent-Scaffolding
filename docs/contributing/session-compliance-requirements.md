# Session Start/End Compliance Requirements (Canonical)

**Document Purpose:** This document defines the mandatory compliance requirements for Copilot agents working in this repository. It replaces any ambiguous or conflicting wording about session start, session end, and pre-commit requirements found elsewhere.

**Authority:** This document supersedes any conflicting guidance. When in doubt, follow this document.

**MANDATORY READING:** Every Copilot agent MUST read this entire document IMMEDIATELY when starting NEW work. Failure to read this document when starting NEW work is a violation.

**Exception (allowed before bootstrap):** Reading `docs/contributing/session-compliance-requirements.md` and `.github/copilot-instructions.md` is permitted before running the bootstrapper. No other repository file exploration/analysis is permitted until the bootstrapper completes successfully (exit 0).

**Last Updated:** 2026-01-06

---

## In-Session Work Requirements (MANDATORY)

After Session Start completes successfully, you MUST execute the requested work.

### Non-negotiable behavior

- **No “bootstrap + catch-up only” sessions.** Completing session-start and then stopping to summarize “what we should do next” is a violation unless you are blocked or near context limits.
- **Implementation over narration.** Do the work.
- **Minimum progress rule:** In every session, you MUST do at least one of:
  - Produce a meaningful commit (preferred), OR
  - Update the issue journals with file-path-level resume instructions, OR
  - Escalate with `**BLOCKED — HUMAN ACTION REQUIRED**` including exact error output.

### Near context limit escape hatch (ONLY IF NECESSARY)

If you are getting close to token/window/context limits:
1. Stop starting new work.
2. Commit whatever is already correct and complete.
3. Update journals (`*-summary.md`, `*-overview.md`, `*-next-steps.md`) with extremely detailed resume steps.
4. Push the branch.

---

## Session Start Requirements (MANDATORY)

**When:** At the start of NEW work sessions, immediately upon first message, before ANY repo exploration/analysis/work.

**PROHIBITION (for NEW work only):** You may NOT read files, explore the repository, analyze the problem, or plan changes until the bootstrapper has completed successfully (exit 0).

**Exception:** Reading this file and `.github/copilot-instructions.md` is permitted before bootstrap.

### Ordered Checklist

1. Run bootstrapper:
   ~~~bash
   ./scripts/session-start.sh
   ~~~
   MUST exit 0.

2. Activate environment (venv + Perl):
   ~~~bash
   source .venv/bin/activate &&      PERL_HOME="$HOME/perl5" &&      export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" &&      export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" &&      export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" &&      export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" &&      export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}"
   ~~~

3. Verify `repo-lint` works:
   ~~~bash
   repo-lint --help
   ~~~
   MUST exit 0.

4. Health check:
   ~~~bash
   repo-lint check --ci
   ~~~
   Acceptable exit codes at session start:
   - 0 (clean)
   - 1 (violations exist, but tooling works)
   Unacceptable:
   - 2 (missing tools) → BLOCKER
   - any other non-zero → BLOCKER

5. Initialize issue journals (always required):
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-overview.md`
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-next-steps.md`
   - `docs/ai-prompt/{ISSUE_NUMBER}/{ISSUE_NUMBER}-summary.md`

   Definitions:
   - `*-overview.md`: original issue body (verbatim) + progress updates
   - `*-next-steps.md`: extremely detailed resume steps + prompt
   - `*-summary.md`: MUST be updated with EVERY commit

---

## Pre-Commit Gate Requirements (MANDATORY)

**When required:** BEFORE committing changes that include **scripting/tooling files**.

**Scripting/tooling files include:** `*.py`, `*.sh`, `*.bash`, `*.pl`, `*.pm`, `*.ps1`, `*.psm1`, `*.rs`, plus any other executable/script files in `tools/` or `scripts/`.

**Docs-only / non-scripting commits:** If the commit contains ONLY documentation (e.g. `*.md`) or other non-scripting files not checked by repo-lint for this gate, running `repo-lint check --ci` is recommended but not required.

**Requirement (when applicable):**
- Run `repo-lint check --ci` and fix until it exits **0** before committing.

Exit codes:
- 0 = OK to commit
- 1 = violations exist → NOT OK to commit
- 2 = missing tools → BLOCKER (run `./scripts/session-end.sh` to repair; if still failing, escalate)

---

## Session End Requirements (MANDATORY)

**When:** At the end of EVERY Copilot session, before terminating.

**Allowed session end exit codes:** **0 only.**

### Ordered Checklist

1. If this session includes scripting/tooling changes: run pre-commit gate (`repo-lint check --ci`) and fix until exit 0.
2. Commit ALL meaningful work and keep journals current.
3. Verify repository state:
   ~~~bash
   ./scripts/session-end.sh
   ~~~
   MUST exit 0.

If any required step fails, escalate using:

~~~
**BLOCKED — HUMAN ACTION REQUIRED**
~~~

Include: failing step, exact command, exit code, and error output; mention `@m1ndn1nj4`.

---

## Required Tools Definition

"Required tools" means all are installed and functional (as enforced by `./scripts/session-start.sh`):
- `rg` (ripgrep)
- Python: `black`, `ruff`, `pylint`, `yamllint`, `pytest`, `repo-lint`
- Shell: `shellcheck`, `shfmt` (when shell scripts exist/changed)
- PowerShell: `pwsh`, `PSScriptAnalyzer` (when PowerShell exists/changed)
- Perl: `perlcritic`, `PPI` (when Perl exists/changed)
- GitHub Actions: `actionlint` (when workflows exist/changed)
