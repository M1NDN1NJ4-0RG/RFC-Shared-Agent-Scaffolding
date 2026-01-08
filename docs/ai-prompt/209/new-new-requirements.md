@copilot **MANDATORY: SESSION START/END COMPLIANCE + DOC UPDATES + NEW CANONICAL WORDING**

## 0) Non-Negotiable Rules (READ CAREFULLY)

### Session Start (EVERY SINGLE SESSION — NO EXCEPTIONS)

1) You MUST run the repo-lint bootstrapper at the start of EVERY session.
   - It MUST install/verify ALL required tools (Python, Bash, PowerShell, Perl, etc.).
   - If any required tool cannot be installed or verified, STOP and escalate using:
     `**BLOCKED — HUMAN ACTION REQUIRED**`

### Pre-Commit Gate (BEFORE EVERY COMMIT THAT TOUCHES SCRIPTS/TOOLING)

1) You MUST run `repo-lint`/`repo-cli` conformance checks before committing:
   - `repo-cli check --ci` (or the canonical command defined by the repo)
2) If the command exits non-zero:
   - You MUST fix ALL reported linting/formatting/docstring issues.
   - Re-run until exit code == 0.
   - Only then commit.

### Session End (EVERY SINGLE SESSION)

1) Ensure the repo is in a known-good state:
   - Tools installed (bootstrapper ran successfully)
   - Checks pass (or you escalated with BLOCKED format)
2) Update journals (see below) before ending the session.

No “out of scope.” No deferrals. Missing tools are a blocker.

---

## 1) Read the canonical instructions (MANDATORY)

1) Open and read: `.github/copilot-instructions.md`
2) Identify any wording that is ambiguous about:
   - Session Start requirements
   - Session End requirements
   - Pre-commit lint/docstring gate
   - What “required tools” means
3) Do NOT change this file in this step unless explicitly instructed later.

---

## 2) Read and update issue journals (MANDATORY)

1) Read every file under: `docs/ai-prompt/290/*`
2) Update BOTH:
   - `docs/ai-prompt/290/290-next-steps.md`
   - `docs/ai-prompt/290/290-issue-overview.md`
3) Journals must reflect:
   - What work has been completed already (with checkboxes updated)
   - What remains
   - Exact commands run and results (if any)
   - Any blockers, with the exact BLOCKED format if applicable

---

## 3) Draft the replacement document for ambiguous session rules (MANDATORY)

Create a new document (path/name your choice, but propose a final location) that will serve as the **canonical
replacement** for any ambiguous wording about:

- Session Start requirements
- Session End requirements
- Pre-commit repo-lint gate requirements

### Document requirements (no ambiguity allowed)

The document MUST:

1) Define Session Start as an ordered checklist:
   - Run bootstrapper
   - Verify tool availability
   - Verify `repo-cli --help`
   - Verify `repo-cli check --ci` is runnable (or define the minimal “health check”)
2) Define Pre-Commit Gate as an ordered checklist:
   - `repo-cli check --ci`
   - fix all failures
   - re-run until PASS
   - only then commit
3) Define Session End as an ordered checklist:
   - update journals
   - verify checks are passing OR escalate with BLOCKED
4) Include explicit “STOP conditions” and the exact escalation format:
   - `**BLOCKED — HUMAN ACTION REQUIRED**`
5) Include a one-paragraph “Why this exists” explaining it prevents repeated compliance failures.

### Output

When done, paste the full contents of the drafted document into your PR comment.

---

## 4) Deliverables required in your final update comment

- Confirmation you read `.github/copilot-instructions.md`
- Confirmation you read `docs/ai-prompt/290/*`
- Links/paths to the updated `290-next-steps.md` and `290-issue-overview.md`
- The full text of the new “Session Start/End Requirements” replacement document
