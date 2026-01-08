# GitHub Copilot Agent Instructions

## ⚠️ MANDATORY FIRST STEP ⚠️

Read `docs/contributing/session-compliance-requirements.md` **IMMEDIATELY** at session start.

**Exception (allowed before anything else):** Reading **this** file and `docs/contributing/session-compliance-requirements.md` is allowed before doing any work.

This is **MANDATORY** for NEW work sessions. You may NOT:

- - - Explore files (beyond opening these two compliance docs) - Analyze the problem - Plan changes - Make any code
  modifications

Until you have read the complete Session Compliance Requirements document.

**After reading:** Follow the requirements **exactly** as specified in that document.

---

## Environment Reality (IMPORTANT)

This repository uses **Copilot Coding Agent “customize the agent environment”** setup via:

- `.github/workflows/copilot-setup-steps.yml`

That workflow preinstalls the required toolchains for the agent environment. Therefore:

- `./scripts/session-start.sh` is **NOT** required at session start.
- `./scripts/session-end.sh` is **NOT** required at session end.

If tooling is missing or broken anyway, follow the **repair/escalation rules** in the compliance document (including using `./scripts/session-end.sh` as a repair step when permitted).

---

## Tooling Rules

### Required search tool

- **Use `rg` (ripgrep) as the canonical search tool.**
- **Do NOT use `grep`** unless a human explicitly instructs otherwise.

### Pre-flight sanity check (MANDATORY at session start)

After reading the compliance document, immediately verify tooling works:

```bash
repo-lint --help
```

Must exit **0**. If it fails, follow the compliance doc’s escalation/repair path.

---

## Rule of Three (MANDATORY) — Repo Tooling / Scripts / CI Only

Applies to repository automation and tooling (`tools/`, `scripts/`, CI workflows, test harnesses). If logic appears 3+ times, refactor into a shared helper and update call sites.

---

## Pre-Commit repo-lint Gate (MANDATORY for scripting/tooling changes ONLY)

**Requirement:** If your commit includes **ANY changes** to **scripting/tooling files** (examples: `*.py`, `*.sh`, `*.bash`, `*.pl`, `*.pm`, `*.ps1`, `*.psm1`, `*.rs`, plus other executable/script files in `tools/` or `scripts/`), you MUST run:

- `repo-lint check --ci`

**Docs-only / non-scripting commits:** If the commit includes ONLY documentation (e.g. `*.md`) or other non-scripting files not checked by repo-lint for this gate, running `repo-lint check --ci` is **recommended** but **not required**.

**Exit requirement (when applicable):** `repo-lint check --ci` MUST exit **0** before you commit.

---

## SESSION START REQUIREMENTS (MANDATORY)

**SEE: `docs/contributing/session-compliance-requirements.md`**

The canonical session requirements are defined in the compliance document and supersede any conflicting guidance.

**Quick Summary (must match compliance doc):**

1. Read `docs/contributing/session-compliance-requirements.md` (MANDATORY)
2. Verify `repo-lint --help` exits 0 (MANDATORY)
3. 3. 3. Initialize/update issue journals for the issue you are working on (MANDATORY) 4. Execute requested work
   (MANDATORY: no “catch-up only” sessions)

## SESSION EXIT REQUIREMENTS (MANDATORY)

**SEE: `docs/contributing/session-compliance-requirements.md`**

**Quick Summary (must match compliance doc):**

1. If this session includes scripting/tooling changes: run pre-commit gate `repo-lint check --ci` and fix until exit 0
2. 2. 2. Commit ALL meaningful work (and keep journals current) 3. Initiate Copilot Code Review and address required
   feedback (per compliance doc) 4. Ensure the repo/PR is in a clean, resumable state

---

## HUMAN ESCALATION & MENTION POLICY

When human action is required, the agent MUST stop and comment:

```
**BLOCKED — HUMAN ACTION REQUIRED**
```

Include the failing step, exact command, exit code, and error output; mention `@m1ndn1nj4`.

---

## Trust and Precedence

**Important reality:** This file is automatically read first by Copilot.

**Canonical authority:** `docs/contributing/session-compliance-requirements.md` contains hard requirements that apply to ANY Copilot session. If anything in this file conflicts with the compliance requirements, the compliance requirements win.

**Precedence:**

1. 1. 1. Explicit human direction (issues, PR comments, direct requests)
2. `docs/contributing/session-compliance-requirements.md` (canonical)
3. This `.github/copilot-instructions.md` file
4. 4. 4. Existing repo patterns 5. General best practices
