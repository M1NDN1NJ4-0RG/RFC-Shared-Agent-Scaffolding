# GitHub Copilot Agent Instructions

## ⚠️ MANDATORY FIRST STEP ⚠️

Read `docs/contributing/session-compliance-requirements.md` **IMMEDIATELY** at session start.

**Exception (allowed before bootstrap):** Reading **this** file and `docs/contributing/session-compliance-requirements.md` is allowed before running the bootstrapper. Do **not** read/scan other repository files until the bootstrapper completes successfully (exit 0), per the compliance document.

This is **MANDATORY** for NEW work sessions. You may NOT:
- Explore files
- Analyze the problem
- Read repository contents
- Plan changes
- Make any code modifications

Until you have read the complete Session Compliance Requirements document.

**After reading:** Follow the Session Start checklist **exactly** as specified in that document (run `./scripts/session-start.sh`, activate environment, verify tools, etc.).

---

## Repository State and Inventory

**Current State:** Bootstrap/Empty

**Current Inventory:**
- `README.md` (minimal placeholder)
- `LICENSE` (Unlicense)

**Not Present / May Be Incomplete:**
- RFCs may be incomplete or evolving
- Tests may be incomplete or evolving
- Documentation structure may be incomplete or evolving

**Note:** CI/CD workflows may exist under `.github/workflows/`. Always verify repository reality before claiming something is missing.

## Intended Purpose

This repository is **RFC-driven** and **agent-scaffolding oriented**. Its purpose is to serve as a foundation for collaborative, structured work driven by explicit requirements and human direction.

**Critical Constraint:** Until concrete files, workflows, and RFC structures exist in this repository, agents **MUST NOT invent architecture, workflows, or milestone structures**. All work must be explicitly requested and approved by humans.

## Bootstrap Expectations

When CI, tests, or build steps are **not present**, the agent must:

1. **Add minimal scaffolding only when explicitly requested by a human**
   - Example minimal actions (require human approval):
     - Add a small `Makefile` with basic targets (`test`, `lint`, `build`)
     - Add a `package.json` with minimal test script if Node.js project
     - Add a `pyproject.toml` or `setup.py` for Python projects
   - **Do NOT** create comprehensive tooling or complex structures

2. **Document all assumptions in the PR description**
   - State what was assumed about the project (language, toolchain, etc.)
   - List any dependencies or prerequisites introduced
   - Explain why the minimal scaffolding was chosen

3. **Keep PRs tiny**
   - One PR = One minimal, verifiable change

4. **Request human approval before proceeding**
   - If unclear whether to add scaffolding, stop and escalate

## Governance Model

**Canonical Epic Tracker:** Placeholder for future implementation.

**Stable Item ID Format:** `MX-PY-IZ`
- `M` = Milestone (e.g., `M0`, `M1`)
- `P` = Epic/Parent (e.g., `P1`, `P2`)
- `I` = Item (e.g., `I1`, `I2`)
- **Example:** `M0-P1-I1`

## Build Instructions & Rules

**Where to Look for Build/Test/Run/Lint Steps (once added):**
- `.github/workflows/` — CI/CD automation
- `package.json` scripts — Node.js projects
- `Makefile` — Language-agnostic build automation
- `scripts/` — Custom build/test/deployment scripts
- `tools/` — Developer tooling and utilities

**Rules:**
1. **Do NOT claim verification that wasn't performed**
2. **When adding CI, keep it minimal and deterministic**
3. **Prefer conformance/test-first thinking**
4. **Avoid cross-language drift by documenting parity rules**

## PR Discipline and Operational Behavior

- Keep PRs small, single-purpose, and scoped.
- No drive-by refactors/formatting unless explicitly requested.

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

The canonical session start requirements are defined in the compliance document and supersede any conflicting guidance.

**Quick Summary (must match compliance doc):**
1. Run bootstrapper: `./scripts/session-start.sh` (MUST exit 0)
2. Activate environment (venv + Perl PATH/PERL5LIB)
3. Verify `repo-lint --help` works
4. Run health check: `repo-lint check --ci` (exit 0/1 acceptable ONLY at session start; exit 2 = BLOCKER)
5. Initialize issue journals (if working on tracked issue)

## SESSION EXIT REQUIREMENTS (MANDATORY)

**SEE: `docs/contributing/session-compliance-requirements.md`**

**Quick Summary (must match compliance doc):**
1. If this session includes scripting/tooling changes: run pre-commit gate `repo-lint check --ci` and fix until exit 0
2. Commit ALL meaningful work (and keep journals current)
3. Initiate Copilot Code Review and address required feedback (per compliance doc)
4. Verify repository state: `./scripts/session-end.sh` (MUST exit 0)

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
1. Explicit human direction (issues, PR comments, direct requests)
2. `docs/contributing/session-compliance-requirements.md` (canonical)
3. This `.github/copilot-instructions.md` file
4. Existing repo patterns
5. General best practices

**Tooling note:** Use `rg` (ripgrep) as the canonical grep/search tool unless a human explicitly instructs otherwise.
