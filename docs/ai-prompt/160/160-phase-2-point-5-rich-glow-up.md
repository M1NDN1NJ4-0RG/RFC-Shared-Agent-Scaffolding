<file name=0 path=160-phase-2.5-rich-glow-up.md># Phase 2.5 — Rich “Glow Up” for `repo_lint` Console Output + Rich-Click Help

> **Goal:** Make `repo_lint` feel like a polished terminal application.
>
> - **All user-facing console output** must be rendered with **Python Rich** (tables, panels, progress, status, etc.).
> - **All CLI help output** must be rendered with **Rich-Click** so `repo-lint --help` is extremely readable and detailed.
> - **CI output** must remain stable, plain, and greppable.
>
> This phase intentionally focuses on **TTY UX** (what humans see) — not internal logging.

---

## 2.5.0 Scope and Non-Goals

### In Scope
- Rich rendering for all user-facing console output:
  - Command headers (mode, repo root, config files loaded, environment).
  - Per-runner status while running.
  - Results summaries.
  - Failure details.
  - Fix summaries.
  - Config validation failures (“scream loudly”).
- Rich-Click help output for:
  - `repo-lint --help`
  - `repo-lint check --help`
  - `repo-lint fix --help`
  - `repo-lint install --help`
  - Any subcommands/groups introduced later.
- Shell completion instructions included in docs (`HOW-TO-USE-THIS-TOOL.md`).

### Explicit Non-Goals
- This phase does **not** redesign lint logic, policy logic, or runner implementations.
- This phase does **not** change exit code semantics.
- This phase does **not** implement new rule engines.

---

## 2.5.1 Console Output Contract (Human UX)

### Output Modes
`repo_lint` MUST support two user-visible modes of output:

1. **Interactive / TTY mode (default)**
   - Rich output enabled.
   - Colors enabled.
   - Progress/spinners allowed.
   - Panels/tables used for summaries and failures.


2. **CI mode (`--ci`)**
   - Output MUST be **plain** and stable.
   - No ANSI colors.
   - No spinners/progress bars.
   - No reflowing dynamic rendering.
   - Must remain greppable and predictable.

> **Rule:** If `--ci` is set, UI rendering must degrade to stable plain text output.

### Styling and Theming (Rich UX)

**Intent:** Go BIG. Output should be visually scannable, consistent, and immediately “obvious” when something is failing.

#### Global styling rules (Interactive / TTY)
- Use **bold** for primary headings and status labels.
- Use *italic* sparingly for contextual notes (e.g., “CI mode disables colors”).
- Prefer **high-contrast** status colors:
  - PASS / OK: **green**
  - FAIL / ERROR: **red**
  - WARN / SKIP: **yellow**
  - INFO / RUNNING: **cyan**
- Use **dim** text for low-priority metadata (timestamps, internal IDs, etc.).
- Use consistent iconography:
  - `✅` PASS
  - `❌` FAIL
  - `⚠️` WARN
  - `⏭️` SKIP
  - `⏳` RUNNING

#### Panels and tables
- Header panel:
  - Use a strong border style (cyan) and bold title.
  - Include quick context: repo root, configs, mode, filters.
- Failure panels:
  - Use a red border, bold title, and include violation counts.
- Results table:
  - Status column should include icon + colored label (e.g., `✅ PASS`, `❌ FAIL`).
  - Columns should be aligned and stable.

#### Hyperlinks (clickable)
- Output should include clickable hyperlinks when available, using Rich link markup:
  - Example: `[link=https://example]Text[/link]`
- At minimum, render clickable links for:
  - Documentation references (e.g., `HOW-TO-USE-THIS-TOOL.md`, repo docs)
  - Lint rule documentation references (when applicable)
  - Known remediation guides (“How to fix this”)

#### CI mode styling rules
- In `--ci` mode:
  - No colors (render with `no_color=True`).
  - No spinners/progress bars.
  - No dynamic/reflowing live updates.
  - Output should remain **tabled and nice** (e.g., a summary table with stable columns), but must avoid “fancy” interactive effects.
  - Emojis/icons **are allowed** in CI output (✅ ❌ ⚠️ etc.), as long as the output remains stable.
  - No hyperlink markup.
  - Keep output line-based and predictable.

### CI Output Format (Plain)
In CI mode, output must still include:
- One-line header
- Per-runner results (line based; tables are allowed as long as they remain stable)
- Failure sections (line based)
- Final summary

**CI output MUST NOT depend on terminal width.**

#### Theme defaults (initial pick; adjustable later)
- Primary highlight: **cyan** (headers, running state)
- Success: **green**
- Failure: **red**
- Warning: **yellow**
- Secondary metadata: **dim**
- Use `box.ROUNDED` for interactive panels/tables, and `box.SIMPLE` for CI/plain.

### Minimum UI Layout (Interactive)
Every invocation MUST render the following, in this order:

1. **Header Panel**
   - Command name + subcommand
   - Repo root
   - Config files loaded
   - Output mode (TTY vs CI)
   - Selected filters (`--only`, etc.)

2. **Per-runner Execution Feedback**
   - For each runner: a Rich status line or progress indicator while it runs.
   - Must not spam; should update in place.

3. **Results Table**
   - One table summarizing runner results.
   - Columns (minimum): Runner, Status, Files, Violations, Duration

4. **Failure Details (only for failures)**
   - For each failing runner:
     - A red panel header including counts.
     - A table of violations with stable columns.
     - If output is huge, show top N and indicate “+X more”.

5. **Final Summary Panel**
   - PASS/FAIL counts
   - Exit code meaning

### Command Visual Grammar (MANDATORY)

**Intent:** Each command must have a consistent, recognizable “shape” so users can scan output instantly.

#### `repo-lint check` (Scan-first)
Output MUST follow this sequence:
1. Header Panel
2. Runner execution feedback (status/progress)
3. Results Table (always)
4. Failure Details (only if failures)
5. Final Summary Panel

**Notes:**
- The Results Table is the primary artifact; details are secondary.
- Failure Details must be grouped by runner.

#### `repo-lint fix` (Action-first)
Output MUST follow this sequence:
1. Header Panel (include safety mode state: safe vs `--unsafe`)
2. Pre-flight validation panel (config validation + safety gate summary)
3. Actions Taken Table (always)
   - Columns (minimum): Action, Target, Result, Notes
4. Post-fix verification summary
   - Must re-run relevant checks (or clearly state what was verified).
5. Final Summary Panel (include “files modified” count)

**Notes:**
- The Actions Taken Table is the primary artifact.
- If no changes were needed, Actions Taken Table must still render with a clear “No changes required” row.

#### `repo-lint install` (Stepwise checklist)
Output MUST follow this sequence:
1. Header Panel
2. Installation Steps Checklist
   - A step-by-step checklist that marks each step PASS/FAIL.
3. Tools/Dependencies Table
   - Columns (minimum): Tool, Required Version (if pinned), Installed Version (if detectable), Status
4. Next Steps Panel
   - Show the exact next commands to run.
5. Final Summary Panel

**Notes:**
- If any step fails, the final summary must clearly state what is blocked.

#### `repo-lint --help` / `<cmd> --help` (Self-teaching)
Help output MUST:
- Use Rich-Click styling and option grouping
- Include the Help Content Contract sections
- Include clickable links to `HOW-TO-USE-THIS-TOOL.md` (TTY mode)

#### CI mode (`--ci`) alignment
- Preserve the same command “shape” in CI mode, but render it as stable, plain output (no spinners, no ANSI colors).
- Tables are allowed in CI mode if they remain stable and do not depend on terminal width.

---

## 2.5.2 Rich-Click Help Contract

### Requirements
- CLI must be implemented using **Click**.
- Help output must be rendered using **Rich-Click**.

### Expectations
- `repo-lint --help` should be *rich*, highly readable, and structured:
  - Styled headings
  - Styled option groups
  - Examples section (mandatory)
  - Notes for CI vs interactive mode
  - Clear exit code semantics summary
- Clickable links to docs and relevant references (where supported by the terminal)

### Help Content Requirements
Every command must include:
- A short description
- Detailed help text
- Examples (at least 3)
- Notes about `--ci`
- Notes about config files in `conformance/repo-lint/`

### Help Content Contract (MANDATORY)

**Intent:** Help output must be consistent, discoverable, and “self-teaching” across every command.

#### Required Help Sections (every command)
Every Click command MUST include the following help content sections (in this order):

1. **Summary** (1–2 lines)
2. **What this does** (short paragraph)
3. **Examples** (minimum 3; see format below)
4. **Output Modes** (TTY vs `--ci` expectations)
5. **Configuration** (which YAML file(s) are used, where they live)
6. **Exit Codes** (include meanings for all codes this command can return)
7. **Troubleshooting** (most common failure modes + what to do)

#### Required Option Groups (stable grouping across commands)
Help output MUST group options under these headings (as applicable), using Rich-Click configuration:

- **Execution** (e.g., dry-run, timeouts, concurrency if ever added)
- **Filtering** (e.g., `--only`, include/exclude selectors)
- **Configuration** (e.g., config paths, overrides, validation toggles if allowed)
- **Output** (e.g., `--ci`, verbosity, format)
- **Safety** (e.g., `--unsafe`, `--yes-i-know`, other guardrails)
- **Advanced** (only if absolutely necessary; keep small)

#### Examples Format (mandatory)
Each command’s help MUST include examples in a consistent format:

- **Example 1 — Most common usage**
  - Command: `repo-lint <cmd> ...`
  - What it does: one sentence
- **Example 2 — CI usage**
  - Command: `repo-lint <cmd> --ci ...`
  - What it does: one sentence
- **Example 3 — Focused / filtered usage**
  - Command: `repo-lint <cmd> --only <lang> ...`
  - What it does: one sentence

#### Windows / PowerShell requirements
- Help output MUST render cleanly in:
  - Windows PowerShell
  - PowerShell 7+
  - Windows Terminal
- Help output MUST NOT depend on ANSI features that are commonly broken/disabled in Windows shells.
- Any Rich-Click settings required for Windows compatibility must be documented in `HOW-TO-USE-THIS-TOOL.md`.
- Help output should prefer clean styling that renders well on Windows; hyperlinks are optional on Windows if terminals do not support them reliably.

---

## 2.5.3 Implementation Plan

### 2.5.3-A Add a Dedicated UI/Reporter Layer
Create a single authoritative UI/reporting interface so the rest of the code never calls `print()` directly.

**Files / Modules (suggested):**
- `tools/repo_lint/ui/console.py`
- `tools/repo_lint/ui/reporter.py`

**Reporter responsibilities:**
- `render_header(context)`
- `runner_started(name)`
- `runner_completed(result)`
- `render_results_table(results)`
- `render_failures(results)`
- `render_final_summary(results, exit_code)`
- `render_config_validation_errors(errors)`

> **Rule:** All user-facing output routes through the Reporter.

### 2.5.3-B Single Console Instance
- Create exactly one `rich.console.Console` instance per run.
- Configure it based on mode:
  - Interactive: colors enabled, terminal forced.
  - CI: `no_color=True`, `force_terminal=False`.

### 2.5.3-C Stable Data Model for Results
Introduce (or standardize) a results model used by all runners so tables can be generated consistently.

Minimum fields:
- runner name
- ok/fail boolean
- file count (if available)
- violation count
- duration
- output summary
- output details (structured, not raw blobs, where feasible)

### 2.5.3-D Update CLI Commands to Use Reporter
- Replace all direct prints in:
  - `check`
  - `fix`
  - `install`
- Ensure error messages in interactive mode are Rich panels.
- Ensure error messages in CI mode are plain lines.

### 2.5.3-E Rich-Click Integration
- Integrate Rich-Click and configure:
  - wide help width
  - grouped options
  - rich styling
  - command ordering (stable)
  - show default values where meaningful

### 2.5.3-F Autocomplete and Completion Docs
- Ensure the Click-based CLI supports shell completion.
- Add completion instructions to `HOW-TO-USE-THIS-TOOL.md` (per shell):
  - bash
  - zsh
  - fish
  - PowerShell (if supported)
  - Windows PowerShell and PowerShell 7+ (must be validated; see 2.5.4)

---

## 2.5.4 Validation and Test Plan

### Unit Tests
- Verify reporter renders without crashing for:
  - no runners found
  - all pass
  - one fail
  - many fails
  - huge output truncation
  - config validation failure

### Integration Tests
- Run `repo-lint check` against a small fixture repo and assert:
  - exit codes
  - results ordering
  - stable CI output structure

### Cross-Platform / Shell Validation (MANDATORY)

The Click + Rich-Click CLI experience MUST be validated on:
- Linux (bash/zsh)
- macOS (zsh)
- Windows:
  - Windows PowerShell
  - PowerShell 7+
  - Windows Terminal

Minimum validations on Windows:
- `repo-lint --help` renders correctly (no broken layout, no unreadable styling).
- `repo-lint check --help` and `repo-lint fix --help` render correctly.
- Shell completion installation instructions are correct and functional.
- Running `repo-lint check --ci` produces stable, plain output.

If Windows validation fails, it is a release blocker for Phase 2.5.

---

## 2.5.5 Acceptance Criteria (Non-Negotiable)

- [ ] All user-facing console output is routed through a single Reporter layer.
- [ ] Interactive mode output uses Rich tables/panels/status.
- [ ] CI mode output is plain text and stable (no ANSI, no spinners).
- [ ] `repo-lint --help` and all subcommand help use Rich-Click.
- [ ] Help output includes examples, config file notes, and CI notes.
- [ ] Tests added/updated to cover reporter rendering paths.
- [ ] Documentation updated (`HOW-TO-USE-THIS-TOOL.md`) including shell completion setup.
- [ ] Help output follows the **Help Content Contract (MANDATORY)** (sections + option grouping + examples format).
- [ ] Help output and completion instructions are validated on Windows (Windows PowerShell + PowerShell 7+ + Windows Terminal).
- [ ] Console output follows the **Command Visual Grammar (MANDATORY)** for `check`, `fix`, and `install`.
