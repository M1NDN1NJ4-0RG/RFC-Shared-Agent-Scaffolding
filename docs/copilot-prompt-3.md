Implement and ENFORCE AI Next-Steps Journals as a mandatory workflow requirement.

1) Location and naming (MANDATORY)

- Ensure directory exists: docs/ai-prompt/
- EXACTLY ONE file per ORIGINAL issue number: docs/ai-prompt/<ISSUE_NUMBER>-next-steps.md
- Use the ORIGINAL issue number (not PR number unless explicitly instructed by a human).
- Do NOT create multiple files for the same issue.
- Do NOT delete or overwrite history.
- Newest content MUST always be at the top.

1) Update frequency (MANDATORY — NO EXCEPTIONS)

- The next-steps journal MUST be updated on EVERY SINGLE COMMIT related to the issue.
- A commit is NOT considered complete unless the journal has been updated.
- This applies to:
  - partial work
  - refactors
  - fixes
  - experiments
  - formatting-only changes
  - failed attempts
- If a commit touches the issue, it MUST update the journal.

1) Required file format (MANDATORY)
Each <ISSUE_NUMBER>-next-steps.md MUST follow this exact structure:

# Issue <ISSUE_NUMBER> AI Journal

Status: In Progress | Paused | Complete
Last Updated: YYYY-MM-DD
Related: Issue <ISSUE_NUMBER>, PRs <list>

## NEXT

- actionable next steps (newest at top)

---

## DONE (EXTREMELY DETAILED)

Each commit MUST add a new entry at the TOP of this section containing:

- timestamp and short label
- EXTREMELY DETAILED summary including:
  - files changed (full paths)
  - exact changes per file
  - why each change was made
  - commands/tests run and results
  - relevant CI logs/errors (references)
  - known issues, risks, or follow-ups

Old entries remain below. History is append-only.

1) Update rules (MANDATORY)

- Add new NEXT items at the top of NEXT.
- Move completed NEXT items into DONE.
- NEVER rewrite or condense previous DONE entries.
- NEVER skip a commit update.

1) Enforcement via Copilot instructions (MANDATORY)

- Update .github/copilot-instructions.md to state:
  - Updating docs/ai-prompt/<ISSUE_NUMBER>-next-steps.md is REQUIRED on EVERY commit.
  - Commits without a journal update are invalid.
  - The DONE section MUST be EXTREMELY DETAILED.
  - Multiple journals per issue are forbidden.
  - History must be preserved with newest entries first.

Deliverables for this PR:

- docs/ai-prompt/ directory (if missing)
- updated .github/copilot-instructions.md enforcing this behavior
- creation or update of the appropriate <ISSUE_NUMBER>-next-steps.md
