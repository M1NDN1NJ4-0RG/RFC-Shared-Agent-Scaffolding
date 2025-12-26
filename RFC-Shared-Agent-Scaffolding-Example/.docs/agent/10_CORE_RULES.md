# Core Agent Rules

**Status:** Non-negotiable, applies to all tasks.  
**Load:** Always (first shard after bootstrap).

---

## 1. Destructive Operations Policy

**Rule:** NO destructive commands without explicit human approval.

**Destructive operations include:**
- `git reset --hard`
- `git push --force`
- `rm -rf` / `del /s`
- File deletions (except temp files)
- Overwriting existing files without backup
- Dropping databases or data stores

**Exceptions:**
- Deleting files explicitly created by the agent for testing (e.g., `/tmp` files)
- Operations explicitly requested by the user in the issue/PR

**When in doubt:** Ask for approval before proceeding.

---

## 2. Small, Verifiable Chunks

**Rule:** Work in small, incremental units. Each chunk must be independently verifiable.

**Chunk size guidelines:**
- 1 chunk = 1 logical change
- Target: 10-100 lines changed per PR
- Maximum: 500 lines changed per PR (unless refactoring a monolith)

**Verification requirements:**
- Each chunk must build successfully
- Each chunk must pass tests
- Each chunk must be reviewable in < 10 minutes

**Anti-pattern:** Combining unrelated changes in one PR (e.g., feature + refactor + dependency update)

---

## 3. Resume Protocol

**Rule:** After any context loss, interruption, or session restart, follow the resume protocol.

**Resume steps:**
1. Read `.docs/journal/CURRENT.md`
2. Identify the **Active Chunk ID**
3. Load minimum relevant shards from `.docs/agent/` (use `00_INDEX.md`)
4. Validate reality:
   - Run `git status` to check working tree state
   - Check PR state (if applicable)
   - Review last verification notes
5. Continue at the next unchecked item in the active chunk

**When journal is stale:**
- Update it immediately before proceeding
- Add a journal entry explaining the staleness and recovery

---

## 4. Failure Handling

**Rule:** Failures are resumable state, not dead ends.

**When a command fails:**
1. **Capture forensics:** Logs, exit codes, output
2. **Archive artifacts:** Use `safe-archive` to preserve failure state
3. **Update journal:** Record failure, attempted fixes, outcome
4. **Create resumable state:** Ensure next agent can continue from failure point

**Use safe wrappers:**
- `safe-run.sh` / `safe_run.py` / etc. for command execution
- `safe-archive` for preserving state
- `safe-check` for prerequisite validation

**Never:**
- Silently swallow errors
- Retry indefinitely without human intervention
- Proceed to the next step when a prerequisite fails

---

## 5. Journal Discipline

**Rule:** Keep `.docs/journal/CURRENT.md` small and authoritative.

**CURRENT.md must contain:**
- Active Chunk ID
- Unchecked items (checklist)
- Last verification timestamp
- Next steps

**CURRENT.md must NOT contain:**
- Historical entries (move to `PR-LOG/`)
- Completed chunks (archive to `PR-LOG/`)
- Speculation or planning beyond next 2-3 chunks

**When CURRENT grows beyond ~100 lines:**
- Archive completed work to `PR-LOG/`
- Create new CURRENT.md with only active state

---

## 6. Test-First Mindset

**Rule:** Tests define the contract. Write tests before (or with) implementation.

**Test requirements:**
- Every new feature must have tests
- Every bug fix must have a regression test
- Tests must be deterministic (no flaky tests)
- Tests must be documented (purpose clear from name)

**Conformance testing:**
- When working on scripts, ensure conformance with `conformance/vectors.json`
- All implementations must pass the same vectors
- See `30_TESTING_STANDARDS.md` for details

---

## 7. Approval Gates

**Rule:** Certain actions require explicit human approval before proceeding.

**Approval required for:**
- Adding new dependencies (see `50_DEPENDENCIES.md`)
- Changing build tooling (e.g., switching from npm to yarn)
- Modifying CI/CD workflows
- Changing linting/formatting rules
- Structural refactors (e.g., moving files, renaming modules)

**How to request approval:**
1. Stop work
2. Comment on the PR or issue describing the proposed action
3. List alternatives considered
4. Wait for explicit approval before proceeding

---

## 8. Security Mindset

**Rule:** Security is non-negotiable. Never compromise security for convenience.

**Security requirements:**
- Never log secrets, tokens, or credentials
- Never commit secrets to source code
- Run security scanners before merging (CodeQL, dependency scanning)
- Fix critical vulnerabilities immediately
- Document security decisions in commit messages

**When adding dependencies:**
- Check GitHub Advisory Database for known vulnerabilities
- Pin versions in lock files
- See `50_DEPENDENCIES.md` for full policy

---

## 9. Progress Reporting

**Rule:** Report progress frequently using the `report_progress` tool.

**When to report:**
- After completing a meaningful unit of work
- Before requesting code review
- When updating the plan/checklist
- When blocked and escalating to humans

**Progress reports must include:**
- Commit message (clear, concise)
- Updated checklist showing progress
- Context for reviewers

---

## 10. Escalation Policy

**Rule:** When blocked, stop and escalate. Don't guess or invent solutions.

**Escalate when:**
- Requirements are unclear or conflicting
- Approval is needed (see rule #7)
- Architecture decision is required
- Implementation exceeds scope or expertise
- CI/build failures require human judgment

**Escalation format:**
1. Comment on PR with: `**BLOCKED — HUMAN ACTION REQUIRED**`
2. Describe the blocker clearly
3. Present minimum options (if applicable)
4. Mention `@m1ndn1nj4` for attention
5. **STOP** - no further work until unblocked

---

**Version:** 1.0  
**Last Updated:** 2025-12-26  
**Refs:** RFC v0.1.0 sections 3, 4.1-4.4
