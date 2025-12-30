# GitHub Copilot Agent Instructions

## Repository State and Inventory

**Current State:** Bootstrap/Empty

**Current Inventory:**
- `README.md` (minimal placeholder)
- `LICENSE` (Unlicense)

**Not Present:**
- No CI/CD workflows
- No tests
- No build scripts
- No RFCs
- No scripts directory
- No documentation structure

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


**Stop and Escalate if Human Action Required:**
- If you encounter ambiguity, missing requirements, or need approval: **STOP**
- Do NOT guess or invent solutions
- Follow the escalation policy below
- **When blocked:** Add a comment to the PR AND stop — no further commits or pushes until unblocked

## SESSION EXIT REQUIREMENTS (MANDATORY)

Before ending **EVERY session** (including pausing, handing off, or saying work is complete), the agent MUST ensure the following have been run and reviewed:
- Code review checks
- CodeQL checks

Rules:
- If these checks are available as GitHub PR/Checks (Actions/Checks), the agent MUST run them and confirm results.
- If any check fails, the agent MUST either fix the failures or escalate as **BLOCKED — HUMAN ACTION REQUIRED** with references to the failing checks/logs.
- If the repository does not yet have these checks configured, the agent MUST explicitly state they cannot be run because they are not configured (do NOT claim they ran), and escalate to the human to decide whether to add/enable them.

## AI Next-Steps Journals (MANDATORY)

**Purpose:** Maintain persistent, detailed context for every commit on an issue. This is a REQUIRED workflow component, not optional.

**MANDATORY UPDATE FREQUENCY:**
- The next-steps journal MUST be updated on EVERY SINGLE COMMIT related to an issue
- A commit is NOT considered complete unless the journal has been updated
- This applies to ALL commits: partial work, refactors, fixes, experiments, formatting changes, failed attempts
- **NO EXCEPTIONS**

**Directory and Naming (MANDATORY):**
- **Directory:** `docs/ai-prompt/` (must exist)
- **File naming:** `<ISSUE_NUMBER>-next-steps.md` (EXACTLY ONE file per ORIGINAL GitHub issue)
- Use the ORIGINAL GitHub issue number (not PR number)
- Do NOT create multiple files for the same issue
- Do NOT delete or overwrite history

**Required File Format (MANDATORY):**
```markdown
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

[Previous entries below, newest first...]
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

**Enforcement:**
- Updating `docs/ai-prompt/<ISSUE_NUMBER>-next-steps.md` is REQUIRED on EVERY commit
- Commits without a journal update are INVALID
- Multiple journals per issue are FORBIDDEN
- The DONE section MUST be EXTREMELY DETAILED

**Integration with Existing Journals:**
- `docs/history/ai-agent-guidelines/journal/` contains PR-level logs (optional)
- `docs/ai-prompt/` contains mandatory issue-level next-steps journals (REQUIRED)
- Next-steps journals are per-commit tracking, PR logs are optional summaries

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
