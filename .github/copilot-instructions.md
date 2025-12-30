# GitHub Copilot Agent Instructions

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
   - Example: Adding a `Makefile` with one `test` target is one PR
   - Avoid combining multiple structural changes

4. **Request human approval before proceeding**
   - If unclear whether to add scaffolding, stop and escalate
   - Present options and await explicit direction

## Governance Model

**Canonical Epic Tracker:** Placeholder for future implementation.

**Stable Item ID Format:** `MX-PY-IZ`
- `M` = Milestone (e.g., `M0`, `M1`)
- `P` = Epic/Parent (e.g., `P1`, `P2`)
- `I` = Item (e.g., `I1`, `I2`)
- **Example:** `M0-P1-I1`

**Work Traceability:**
- Once Item IDs exist, all work (PRs, issues, commits) **MUST** trace back to a valid Item ID
- Until the governance structure is established, agents **MUST** ask for human direction before inventing milestone structures
- **Do NOT** create placeholder epics, milestones, or item hierarchies without explicit instruction

## Build Instructions & Rules

**Where to Look for Build/Test/Run/Lint Steps (once added):**
- `.github/workflows/` — CI/CD automation
- `package.json` scripts — Node.js projects
- `Makefile` — Language-agnostic build automation
- `scripts/` — Custom build/test/deployment scripts
- `tools/` — Developer tooling and utilities
- Language-specific files: `pyproject.toml`, `Cargo.toml`, `pom.xml`, etc.

**Rules:**
1. **Do NOT claim verification that wasn't performed**
   - If you didn't run tests, don't claim tests pass
   - Be explicit: "Built locally with `make build`" or "CI not yet configured"

2. **When adding CI, keep it minimal and deterministic**
   - Document exact commands the CI runs
   - Example: "CI runs: `npm install && npm test`"
   - Avoid non-deterministic steps (network calls without caching, flaky tests)

3. **Prefer conformance/test-first thinking**
   - When adding features, add tests first or simultaneously
   - Conformance tests validate expected behavior across implementations

4. **Avoid cross-language drift by documenting parity rules**
   - If the project supports multiple languages/implementations, document expected behavior consistency
   - Example: "Python and Node.js implementations must expose identical CLI interfaces"

## Project Layout

**Recommended Known Locations:**
- `.github/workflows/` — GitHub Actions workflows
- `conformance/` — Cross-implementation conformance tests
- `scripts/` — Automation scripts (build, deploy, utilities)
- `docs/` — Documentation (guides, architecture, API specs)
- `rfc/` or `rfc/markdown/` — Request for Comments documents
- `src/` or language-specific directories — Source code
- `tests/` or `test/` — Test suites

**Rule:** If directories don't exist yet, **DO NOT** create large structures without explicit instruction. Start minimal.

**Example Minimal Start:**
- Need to add a script? Create `scripts/` and add ONE script
- Need to add documentation? Create `docs/` and add ONE document
- Need to add an RFC? Create `rfc/` and add ONE RFC file

## PR Discipline and Operational Behavior

**Single-Thread Work Rule:**
- Work on ONE change/concern per PR, even before Item IDs exist
- Don't batch unrelated changes together
- Example: Don't combine "add Makefile" + "update README" + "add linter config" in one PR
- Each concern gets its own focused PR

**Small PRs:**
- One logical change per PR
- Prefer 10-50 lines changed over 500+ lines
- Split large changes into sequential, dependent PRs

**Single Responsibility:**
- Each PR addresses ONE concern
- Don't mix refactoring with feature additions
- Don't combine dependency updates with code changes


**No Drive-By Refactors / Formatting:**
- **DO NOT** make cosmetic changes, formatting fixes, or refactors unless explicitly requested
- Avoid "while I'm here..." improvements
- Stick to the scope of the task
- If you notice issues, note them in PR comments for future work, but don't fix them now
- Exception: If a linter/formatter is already configured and running in CI, apply its fixes

## Rule of Three (MANDATORY) — Repo Tooling / Scripts / CI Only

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
- Create a single helper in the most appropriate shared location (prefer existing shared modules; don’t invent new structure unnecessarily).
- Update all call sites to use the helper (don’t leave duplicate variants unless there is a real behavioral difference).
- Add/extend tests to lock behavior so the refactor does not change semantics.
- If refactoring would break existing behavior/contracts, STOP and document why using the repo’s “durable note” rule.
- If two implementations must remain separate, explicitly document the reason and the behavioral difference (durable note).

**Explicit Claims in PR Body:**
- State what changed and why
- Example: "Added `make test` target to run unit tests via pytest"
- List what was NOT done if relevant: "Did NOT add integration tests (out of scope)"

**Reproducible Validation Steps:**
- Provide exact commands to run locally
- Example:
  ```
  Validation steps:
  1. Clone the repo
  2. Run `make test`
  3. Verify output shows "All tests passed"
  ```
- Include expected output or success criteria


**Exact Commands:**
- Always specify the full command
- ✅ Good: `npm install && npm run test:unit`
- ❌ Bad: "Run the tests"

**Pre-Commit Repo Lint Gate (MANDATORY):**
- Before creating **ANY** commit, you MUST run:
  - `python3 -m tools.repo_lint check --ci`
- The command MUST exit **0** (PASS).
- If it fails, you MUST fix the reported issues and re-run it until it passes.
- Do NOT commit “known failing” work.

**Stop and Escalate if Human Action Required:**
- If you encounter ambiguity, missing requirements, or need approval: **STOP**
- Do NOT guess or invent solutions
- Follow the escalation policy below
- **When blocked:** Add a comment to the PR AND stop — no further commits or pushes until unblocked

## SESSION START REQUIREMENTS (MANDATORY)

At the start of **EVERY session**, before making changes, the agent MUST ensure the required tooling is installed and available in the working environment.

Required tools (install/verify each session):
- `rgrep` (PREFERRED grep tool in this repository)
- `black`
- `pylint`
- `pytest`
- `ruff`
- `yamllint`
- `shellcheck`
- `shfmt`
- `pwsh`
- `PSScriptAnalyzer`
- `Perl::Critic`
- `PPI`

Rules:
- If any required tool is missing, install it before proceeding.
- If installation is blocked by environment constraints, escalate using `**BLOCKED — HUMAN ACTION REQUIRED**` and list the missing tools.
- Use `rgrep` as the default grep/search tool for repository work unless a human explicitly instructs otherwise.

- For ANY new issue you begin work on, initialize the issue journal directory:
  - Create: `docs/ai-prompt/<ISSUE_NUMBER>/`
  - Create: `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md`
  - Copy the ORIGINAL GitHub issue text into `<ISSUE_NUMBER>-overview.md` in Markdown, preserving checkboxes/tasks.

## SESSION EXIT REQUIREMENTS (MANDATORY)

Before ending **EVERY session** (including pausing, handing off, or saying work is complete), the agent MUST perform an automated review pass AND ensure validation/security checks are in a known-good state.

Required before session end:
- Trigger a **GitHub Copilot Code Review** of the PR’s latest changes and review the feedback
- Ensure all required PR status checks are passing (tests, linters, conformance, etc.)
- Ensure CodeQL is passing **IF** CodeQL is configured/enabled for the repository

Definitions:
- **Copilot Code Review:** the GitHub Copilot PR review feature (Copilot leaves review comments on the PR). This is not the same as human code review.
- **Required PR status checks:** the status checks enforced by branch protection/rulesets on the PR.
- **CodeQL:** GitHub Code Scanning (CodeQL) analysis results, if CodeQL is configured.

Rules:
- Copilot Code Review is a required final quality gate:
  - Treat **every** Copilot Code Review comment as a **required action** — including items labeled “nit”, “code quality”, “maintainability”, “consistency”, or “suggestion”.
  - Do **not** classify review feedback as “non-blocking” or “nice-to-have”. **Nits are not optional.**
  - You may skip or partially implement a review comment **only** if implementing it would:
    - break existing behavior, conformance, or CI/contracts, OR
    - violate repo contracts/naming rules, OR
    - exceed explicitly-approved scope constraints for the current PR.
  - If you skip or partially implement any review comment, you MUST:
    - Leave a **nearby, durable** note explaining why, located at one of:
      - the relevant function/class docstring
      - the module-level docstring/header comment
      - an inline comment immediately above the impacted code
    - Mention it explicitly in the PR update comment (see `### 5) Output required in your PR update comment`), including **what was skipped** and **why**, plus where the local note was left.
  - If the agent cannot resolve an issue without human direction, escalate using the exact escalation format below.
- Agents cannot always directly “run” GitHub Actions in all environments. The agent MUST instead:
  - Verify the latest workflow/check runs exist and are passing for the PR’s HEAD commit, OR
  - If checks have not triggered, take the minimal action that triggers them (e.g., push a follow-up commit) when permitted.
- If CodeQL is not configured/enabled, the agent MUST explicitly state that CodeQL cannot be verified because it is not configured (do NOT claim it ran).

Escalation format (MUST match the policy below):
- Comment on the PR with the exact opening line:
  `**BLOCKED — HUMAN ACTION REQUIRED**`
- Include:
  - what Copilot Code Review reported (and why it can’t be resolved)
  - which checks are failing or missing
  - what evidence you have (check names / log references)
  - the minimal options to proceed

## AI Next-Steps Journals (MANDATORY)

**Purpose:** Maintain persistent, detailed context for every commit on an issue. This is a REQUIRED workflow component, not optional.

**MANDATORY UPDATE FREQUENCY:**
- The next-steps journal MUST be updated on EVERY SINGLE COMMIT related to an issue
- A commit is NOT considered complete unless the journal has been updated
- This applies to ALL commits: partial work, refactors, fixes, experiments, formatting changes, failed attempts
- **NO EXCEPTIONS**

**Directory and Naming (MANDATORY):**
- **Directory:** `docs/ai-prompt/<ISSUE_NUMBER>/` (must exist)
- **Next-steps file:** `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-next-steps.md` (EXACTLY ONE per ORIGINAL GitHub issue)
- **Overview file:** `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md` (EXACTLY ONE per ORIGINAL GitHub issue)

**Required File Format (MANDATORY):**

Path: `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-next-steps.md`

```markdown
MUST READ: `.github/copilot-instructions.md` FIRST! 
MUST READ: `docs/contributing/naming-and-style.md` SECOND!
<!-- DO NOT EDIT OR REMOVE THE LINE ABOVE -->
# Issue <ISSUE_NUMBER> AI Journal
Status: In Progress | Paused | Complete
Last Updated: YYYY-MM-DD
Related: Issue <ISSUE_NUMBER>, PRs <list>

## NEXT
- actionable next steps (newest at top)

---

## DONE (EXTREMELY DETAILED)
### YYYY-MM-DD HH:MM - <short label>
**Files Changed:**
- `path/to/file1.ext`: <exact changes>
- `path/to/file2.ext`: <exact changes>

**Changes Made:**
- Extremely detailed summary including:
  - Why each change was made
  - Commands/tests run and results
  - Relevant CI logs/errors (references)
  - Known issues, risks, or follow-ups

**Verification:**
- <commands run>
- <results>

---

<!-- PREVIOUS ENTRIES DELIMITER -->

---
```

**Required Overview File Format (MANDATORY):**

Path: `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md`

This file MUST start by copying the ORIGINAL GitHub issue body verbatim into a section titled `## Original Issue`.

It MUST also include a live, maintained progress tracker that is updated before the end of EVERY session:
```markdown
# Issue <ISSUE_NUMBER> Overview
Last Updated: YYYY-MM-DD
Related: Issue <ISSUE_NUMBER>, PRs <list>

## Original Issue
<verbatim copy of the GitHub issue body in Markdown>

## Progress Tracker
- [ ] Item 1
  - [ ] Sub-item A
  - [ ] Sub-item B
- [x] Item 2

## Session Notes (newest first)
### YYYY-MM-DD HH:MM - <short label>
- Summary of what changed this session
- Links/references to PRs/commits/checks
```

**Update Rules (MANDATORY):**
- Add new NEXT items at the TOP of the NEXT section
- Move completed NEXT items to DONE with EXTREMELY DETAILED entry
- Each DONE entry MUST include:
  - Timestamp and short label
  - Full file paths of all changes
  - Exact changes per file
  - Rationale for each change
  - Commands/tests run with results
  - CI log references if applicable
  - Known issues or follow-ups
- NEVER rewrite or condense previous DONE entries
- NEVER skip a commit update
- History is append-only, newest entries first
- `*-next-steps.md` is per-commit and MUST be updated on EVERY commit.
- `*-overview.md` is per-session and MUST be updated before ending EVERY session.

**Enforcement:**
- Updating `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-next-steps.md` is REQUIRED on EVERY commit
- Updating `docs/ai-prompt/<ISSUE_NUMBER>/<ISSUE_NUMBER>-overview.md` is REQUIRED before ending EVERY session

**Integration with Existing Journals:**
- `docs/history/ai-agent-guidelines/journal/` contains PR-level logs (optional)
- `docs/ai-prompt/<ISSUE_NUMBER>/` contains mandatory issue-level journals: overview (per-session) + next-steps (per-commit)

## HUMAN ESCALATION & MENTION POLICY

When human action is required, the agent **MUST**:

1. **STOP all work immediately**
2. **Comment on the active PR** with the exact opening line:
   ```
   **BLOCKED — HUMAN ACTION REQUIRED**
   ```
3. **Present minimum options** for how to proceed
4. **Mention @m1ndn1nj4** for attention
5. **Wait for explicit human direction** before continuing

**Examples of when to escalate:**
- Unclear requirements or conflicting instructions
- Need to create new directory structures not yet defined
- Need to choose between multiple valid approaches
- CI/build failures that require architectural decisions
- Adding dependencies or tooling that may have broad impact
- Governance/Item ID structure questions

**Do NOT:**
- Guess at requirements
- Invent project structure without approval
- Proceed with major changes without confirmation
- Create placeholder epics or milestones

## Trust and Precedence

**Trust this file first:** The instructions in `.github/copilot-instructions.md` are authoritative for this repository.

**DO NOT update `.github/copilot-instructions.md` without explicit approval:**
- This file governs agent behavior
- Agents must NOT modify it as part of other work
- Agents must NOT "helpfully" rewrite or improve these instructions
- Changes to this file require explicit human request and review

**When to search further:**
- If these instructions are incomplete for your task
- If repository reality contradicts these instructions (e.g., existing patterns differ)
- If you need domain-specific technical guidance not covered here

**Precedence (current state):**
1. Explicit human direction (issues, PR comments, direct requests)
2. This `.github/copilot-instructions.md` file
3. Existing patterns in the repository (if they exist)
4. General best practices (only when above don't apply)

**Repo Truth Hierarchy (future-facing):**

As the repository matures, the following hierarchy will apply when content exists:
- **RFC text overrides README:** When RFCs are written, they are the authoritative source of truth for design and requirements
- **Canonical tracker governs scope:** When a canonical epic/item tracker exists, it defines what work is in/out of scope
- **Workflows define verification:** When CI/CD workflows exist, they define the required validation steps
- **Conflicts require escalation:** When sources conflict (e.g., RFC vs. existing code, tracker vs. README), **STOP** and escalate to humans — do not choose

**Keep it simple:** When in doubt, do less rather than more. Humans can always request additional work, but removing unwanted scaffolding is costly.
