@copilot

🚨 **HUMAN DIRECTIVE — NOT A REQUEST — NOT SUBJECT TO INTERPRETATION** 🚨  
You are explicitly authorized and instructed to proceed.  
Do **NOT** ask for clarification. Do **NOT** narrow scope. Do **NOT** summarize instead of implementing.

I am aware this is scope creep for this PR.  
**I do not care.**  
I want this done **now**.

---

## ABSOLUTE PRIORITY STATEMENT (READ FIRST)

- ❌ No summaries
- ❌ No “this is a large task” commentary
- ❌ No “out of scope” objections
- ❌ No permission checks
- ✅ Implement as much as possible in ONE session

If work is incomplete due to constraints, **commit real code**, then leave **precise resumable instructions**. Do not stop early.

---

## SCOPE (NON-NEGOTIABLE)

- **Bash only**
- **DO NOT touch Rust**
- Modify **only**: `scripts/bootstrap-repo-lint-toolchain.sh`
- You MAY add a small helper under `scripts/lib/` **only if it reduces duplication**
- Preserve:
  - command ordering
  - behavior
  - exit codes
  - `set -euo pipefail` semantics

---

## GOAL

Add a **default-on progress UI** to the existing Bash script.

This is for **the current Bash bootstrapper**, not the Rust binary.

---

## PROGRESS UI BEHAVIOR

### General
- Progress UI is **ENABLED BY DEFAULT**
- Deterministic step ordering
- Works correctly on:
  - Interactive terminals
  - CI / non-TTY

### TTY (Interactive)
- Single-line, in-place updating progress bar or spinner
- Shows:
  - step index / total
  - step name
  - elapsed time
- Cursor hidden while running; restored on exit
- Uses `printf '\r…'` + clear-to-end-of-line

### `--verbose`
- Full stdout/stderr is shown
- Progress bar **stays fixed in place**
- Output scrolls **above or below** the bar
- Progress bar continues updating while output streams

### Non-TTY / CI
- **NO ANSI**
- **NO carriage returns**
- Clean, line-oriented logs only

---

## STEP MODEL (REAL STEPS ONLY)

Reflect **actual stages already present** in the script.

At minimum:
1) Preflight / environment checks
2) Toolchain bootstrap phases
3) Each tool invocation (repo-lint, shellcheck, shfmt, actionlint, etc.)
4) Final verification gate

Each step MUST emit:
- start
- success (with duration)
- failure (with duration + failing command)

---

## IMPLEMENTATION REQUIREMENTS

- Detect TTY via `[[ -t 1 ]]`
- Respect `CI` and `NO_COLOR`
- Always restore terminal state:
  - cursor
  - line state
- Use `trap` on `EXIT INT TERM`
- Track per-step duration via `SECONDS` or `date +%s`
- Exit codes MUST remain unchanged
- DO NOT suppress output in CI
- If needed in TTY mode, you MAY buffer command output and replay it in `--verbose`

---

## SUGGESTED STRUCTURE (OPTIONAL, NOT EXHAUSTIVE)

You may introduce helpers such as:
- `is_tty`
- `progress_init`, `progress_cleanup`
- `step_start`
- `step_ok`
- `step_fail`
- `run_step "name" -- command ...`  
  (must return the original exit code)

Minimal refactor only — no behavior changes.

---

## TOKEN / CONTEXT ESCAPE HATCH (MANDATORY IF NEEDED)

If you approach token, context, or execution limits:

1) **STOP starting new work**
2) **COMMIT all completed code**
3) Update the journal:
   - `docs/ai-prompt/235/235-next-steps.md`
4) Use **exact, explicit wording** so the next session can resume immediately, including:
   - What progress UI pieces are COMPLETE
   - What step index / section you stopped at
   - What remains UNIMPLEMENTED
   - Any traps, cleanup, or edge cases still open

This escape hatch exists to **preserve momentum**, not reduce ambition.

---

## ACCEPTANCE CRITERIA

- Local TTY run shows live, in-place progress UI
- `--verbose` shows scrolling output without breaking the bar
- CI output is clean and readable
- Exit behavior unchanged
- Script passes existing shell linting

---

🚀 **BEGIN IMPLEMENTATION IMMEDIATELY.**
