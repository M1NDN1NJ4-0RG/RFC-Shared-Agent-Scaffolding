# MANDATORY = MANDATORY. MANDATORY ≠ OPTIONAL. ZERO WIGGLE ROOM

@copilot YOU ARE WORKING ON **PR #297**.

## NON-NEGOTIABLE LAW (READ FIRST, THEN OBEY)

1) IMMEDIATELY open and read (ENTIRE FILES):
- `.github/copilot-instructions.md`
- `docs/contributing/session-compliance-requirements.md`

2) COMPLY WITH THEM EXACTLY.
No reinterpretation. No shortcuts. No “close enough.”

## TOOLING REQUIREMENT — USE RIPGREP ONLY
`rg` (ripgrep) is preinstalled in the Copilot agent environment.  
You MUST use `rg` for searching. **DO NOT USE `grep`.**

## OBJECTIVE (THIS IS THE ONLY DEFINITION OF "DONE")

This PR introduces safe MD013 tooling and then uses it to reduce MD013 violations WITHOUT mangling Markdown structure.

### "Done" means
- Both MD013 scripts are reviewed and validated
- Exhaustive unit tests exist and pass for both scripts
- Option B is the preferred path and must be proven safe on real repo files
- MD013 fixes are applied in controlled batches with verification after every batch
- `repo-lint check --ci --only markdown` shows materially reduced MD013 counts and no structural damage to Markdown

## HARD BEHAVIOR RULES (NO LOOPHOLES)

- Do NOT narrate progress. Output only:
  - the exact action you are taking next
  - the exact command you are running next (if any)
  - the exact file(s) you are changing next
- Do NOT run bulk operations repo-wide until small-batch validation proves safety.
- Do NOT “trust” rewrites: always inspect diffs for list/checkbox/table/code integrity.

## REQUIRED EXECUTION ORDER (DO NOT REORDER)

### 1) SESSION START (MANDATORY)

From repo root, run: `repo-lint —help`
MUST exit **0**.
Then run: `repo-lint check —ci`

Acceptable exit codes at session start:
- 0 (clean)
- 1 (violations exist, but tooling works)

Unacceptable / blocker:
- 2 (missing tools)
- any other non-zero

If blocked, attempt repair ONE time only: `./scripts/session-end.sh`
Then rerun `repo-lint --help` and `repo-lint check --ci`. If still blocked, stop and post:
```plaintext
BLOCKED — HUMAN ACTION REQUIRED
```
Include exact commands, exit codes, and error output.

### 2) READ PR CONTEXT + JOURNALS (MANDATORY)

Open PR #297 and read the PR description, changed files list, and any review comments.

Then read ALL of:
- `docs/ai-prompt/297/297-overview.md`
- `docs/ai-prompt/297/297-next-steps.md`
- `docs/ai-prompt/297/297-summary.md`

Do not stop after reading.

### 3) ADDRESS ALL REVIEW COMMENTS (MANDATORY)

Open: `https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/pull/297#pullrequestreview-3640238927`  
Process comments TOP-TO-BOTTOM. Do not skip.

For EACH comment:
1) Quote the comment in your output (short excerpt is fine).
2) Implement the change.
3) If verification is needed, run the smallest relevant command(s).
4) Mark the comment addressed in the PR UI ONLY when truly resolved.

If a comment is skipped (allowed reasons only):
- Add a durable `TODO:`/`FUTURE:` near the code.
- Record in journals: comment summary + reason + exact future action.

### 4) VERIFY THE TWO NEW SCRIPTS EXIST IN MAINLINE PR CONTENT (MANDATORY)

Confirm these files are present in this PR and open them:
- `repo-lint-failure-reports/20821497186/fix_md013_line_length_option_a.py`
- `repo-lint-failure-reports/20821238493/fix_md013_line_length_option_b.py`
Preference: **Option B**.

### 5) CREATE COMPREHENSIVE, EXHAUSTIVE UNIT TESTS FOR BOTH SCRIPTS (MANDATORY)

Create test suites that prove we do NOT reintroduce prior damage.

Tests MUST include at minimum:

- Bullet lists: `-`, `*`, `+`
- Numbered lists: `1.`, `2.`, `10.` etc.
- Checkboxes: `- [ ]`, `- [x]`, `* [ ]`, nested checkboxes
- Nested lists (multiple levels) with correct indentation preserved
- Mixed list paragraphs (list item followed by wrapped continuation lines)
- Code blocks fenced with backticks AND tildes (must remain byte-identical)
- Indented code blocks (must remain unchanged)
- Tables (header + separator + rows) must remain unchanged (byte-identical)
- Blockquotes `>` unchanged
- Headings `#`..`######` unchanged
- Link reference definitions (`[id]: https://...`) unchanged
- Inline code (backticks) must not be reflowed incorrectly
- Lines containing URLs must not be reflowed incorrectly
- HTML blocks preserved
- Newline behavior preserved (final newline and general line endings)
- Deterministic output: running the same script twice yields identical output

Hard requirement: tests must assert we do NOT recreate the historical mangling:
- No collapsing list items into one paragraph
- No duplicating list markers (e.g., `1. 1. 1.`)
- No breaking checkbox syntax
- No destroying nested list structure

Run tests until they pass.

### 6) RUN OPTION B ON ONE FILE ONLY (MANDATORY SAFETY TRIAL)

After tests pass:

1) Identify ONE Markdown file with MD013 violations.
2) Ensure working tree clean before trial.
3) Run Option B on ONLY that file.
4) Manually inspect the diff and confirm:
   - Lists remain correct
   - Checkboxes remain correct
   - Tables unchanged
   - Code blocks unchanged
5) Run: `repo-lint check --ci --only markdown`
If anything is mangled: STOP and fix script + tests first.

### 7) APPLY MD013 FIXES IN CONTROLLED BATCHES (MANDATORY)

Do NOT bulk-run across the repo immediately.

Batch sequence (MANDATORY):
- Batch 1: 3–5 files
- Batch 2: 10–20 files
- Batch 3: 50 files
- Only after those succeed: expand further

For EACH batch:
- Ensure clean working tree before starting
- Run Option B only on that batch
- Manually inspect representative diffs (especially list-heavy docs)
- Run: `repo-lint check --ci --only markdown`
- Commit with a message that includes batch number and MD013 progress
- Update journals immediately after commit

Stop immediately if any mangling is detected.

### 8) PRE-COMMIT GATE + FINAL VERIFICATION (MANDATORY)

Before final push/finish:
- Run: `repo-lint check —ci`
- Ensure the PR is clean and resumable.

### 9) JOURNAL UPDATES (MANDATORY)

Update these files to reflect what you actually did:
- `docs/ai-prompt/297/297-summary.md` (MUST be updated with every commit)
- `docs/ai-prompt/297/297-overview.md` (checkbox/task progress)
- `docs/ai-prompt/297/297-next-steps.md` (remaining work, with exact resume steps)

## CONTEXT/TOKEN SAFETY VALVE (ONLY IF YOU ARE ACTUALLY NEARING LIMITS)

If you are approaching context limits:
1) STOP starting new work.
2) Commit everything already correct and complete immediately.
3) Update journals with EXTREMELY detailed resume instructions:
   - remaining review comments (short excerpts)
   - exact files/sections to open next
   - exact commands to run next
4) If you changed scripting/tooling files: run `repo-lint check --ci` until exit 0.
5) Stop ONLY after the repo is clean, pushed, and resumable.

## FINAL REMINDER

DO NOT STOP UNTIL:
- ALL review comments in `https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/pull/297#pullrequestreview-3640238927` are addressed or defensibly deferred with durable TODO notes, AND
- the repo is clean and resumable per compliance requirements.  Found 2 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                            
  File                                Line   Message                                                                                        
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  fix_md013_line_length_option_a.py    277   R1737: Use 'yield from' directly instead of yielding each element one by one (use-yield-from)  
  fix_md013_line_length_option_b.py    360   R1737: Use 'yield from' directly instead of yielding each element one by one (use-yield-from)  
                                                                                                                                            

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           python-docstrings Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
  Found 20 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                             
  File                                Line   Message                                                                                                                                         
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  fix_md013_line_length_option_a.py      -   Missing required sections: Purpose, Environment Variables, Examples, Exit Codes (Expected reST-style sections in module docstring)              
  fix_md013_line_length_option_a.py     61   Symbol 'def _starts_fence()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)       
  fix_md013_line_length_option_a.py     70   Symbol 'def _ends_fence()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)         
  fix_md013_line_length_option_a.py     79   Symbol 'def _is_table_block()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)     
  fix_md013_line_length_option_a.py     86   Symbol 'def _is_indented_code()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)   
  fix_md013_line_length_option_a.py     95   Symbol 'def _is_list_item()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)       
  fix_md013_line_length_option_a.py    100   Symbol 'def _should_skip_line()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)   
  fix_md013_line_length_option_a.py    121   Symbol 'def _wrap_paragraph()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)     
  fix_md013_line_length_option_a.py    132   Symbol 'def _collect_paragraph()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)  
  fix_md013_line_length_option_a.py    155   Symbol 'def _copy_list_block()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)    
  fix_md013_line_length_option_a.py    191   Symbol 'def _rewrite_file()': Missing function docstring (Function must have a docstring)                                                       
  fix_md013_line_length_option_a.py    272   Symbol 'def _iter_md_files()': Missing function docstring (Function must have a docstring)                                                      
  fix_md013_line_length_option_a.py    281   Symbol 'def main()': Missing function docstring (Function must have a docstring)                                                                
  fix_md013_line_length_option_b.py      -   Missing required sections: Purpose, Environment Variables, Examples, Exit Codes (Expected reST-style sections in module docstring)              
  fix_md013_line_length_option_b.py     72   Symbol 'def _starts_fence()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)       
  fix_md013_line_length_option_b.py     81   Symbol 'def _ends_fence()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)         
  fix_md013_line_length_option_b.py     90   Symbol 'def _is_table_block()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)     
  fix_md013_line_length_option_b.py     97   Symbol 'def _is_indented_code()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)   
  fix_md013_line_length_option_b.py    102   Symbol 'def _should_skip_line()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)   
  fix_md013_line_length_option_b.py    121   Symbol 'def _wrap_text()': Missing :param, :returns (Function docstring must include :param, :returns field(s) per PEP 287 reST style)          
                                                                                                                                                                                             

           Summary           
  Total Runners: 4           
    Passed: 1                
    Failed: 3                
  Total Violations: 26       
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

