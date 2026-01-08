# Phase 2.5 — Rich “Glow Up” for `repo-lint` Console Output + Rich-Click Help

> **Goal:** Make `repo-lint` feel like a polished terminal application.
>
> - **All user-facing console output** must be rendered with **Python Rich** (tables, panels, progress, status, etc.).
> - **All CLI help output** must be rendered with **Rich-Click** so `repo-lint --help` is extremely readable and detailed.
> - **CI output** must remain stable, predictable, and greppable.
>
> This phase intentionally focuses on **TTY UX** (what humans see) — not internal logging.

---

## 2.5.0 Scope and Non-Goals

### In Scope

- - Rich rendering for all user-facing console output: - Command headers (mode, repo root, config files loaded,
  environment). - Per-runner status while running. - Results summaries. - Failure details. - Fix summaries. - Config
  validation failures (“scream loudly”). - Rich-Click help output for:
  - `repo-lint --help`
  - `repo-lint check --help`
  - `repo-lint fix --help`
  - `repo-lint install --help`
  - - Any subcommands/groups introduced later.
- Shell completion instructions included in docs (`HOW-TO-USE-THIS-TOOL.md`).
- - A user-configurable **Rich UI theme/config YAML** for per-person formatting preferences (colors/icons/box
  styles/help styling), with strict schema validation.

### Explicit Non-Goals

- - This phase does **not** redesign lint logic, policy logic, or runner implementations. - This phase does **not**
  change exit code semantics. - This phase does **not** implement new rule engines.

---

## 2.5.1 Console Output Contract (Human UX)

### Output Modes

`repo-lint` MUST support two user-visible modes of output:

1. 1. **Interactive / TTY mode (default)** - Rich output enabled. - Colors enabled. - Progress/spinners allowed. -
   Panels/tables used for summaries and failures.

2. **CI mode (`--ci`)**
   - - Output MUST be stable and predictable. - No ANSI colors. - No spinners/progress bars. - No dynamic/reflowing live
     updates. - Tables are allowed (and encouraged) as long as they remain stable. - Output must remain greppable.

> **Rule:** If `--ci` is set, UI rendering must degrade to stable, non-interactive output.

### TTY Detection Rules

- By default, `repo-lint` SHOULD treat output as **interactive** only when stdout is a TTY.
- If stdout is **not** a TTY (piped output, redirected to a file), `repo-lint` SHOULD behave like CI output (stable, no live rendering).
- `--ci` MUST force CI behavior regardless of TTY detection.

### CI Output Format (Stable)

In CI mode (or non-TTY output), output must still include:

- - One-line header - Per-runner results (line based; tables are allowed as long as they remain stable) - Failure
  sections (line based) - Final summary

**CI output MUST NOT depend on terminal width.**

### Styling and Theming (Rich UX)

**Intent:** Go BIG. Output should be visually scannable, consistent, and immediately “obvious” when something is
failing.

#### Global styling rules (Interactive / TTY)

- - Use **bold** for primary headings and status labels. - Use *italic* sparingly for contextual notes (e.g., “CI mode
  disables colors”). - Prefer **high-contrast** status colors: - PASS / OK: **green** - FAIL / ERROR: **red** - WARN /
  SKIP: **yellow** - INFO / RUNNING: **cyan** - Use **dim** text for low-priority metadata (timestamps, internal IDs,
  etc.). - Use consistent iconography:
  - `✅` PASS
  - `❌` FAIL
  - `⚠️` WARN
  - `⏭️` SKIP
  - `⏳` RUNNING

#### Panels and tables

- - Header panel: - Use a strong border style (cyan) and bold title. - Include quick context: repo root, configs, mode,
  filters. - Failure panels: - Use a red border, bold title, and include violation counts. - Results table:
  - Status column should include icon + colored label (e.g., `✅ PASS`, `❌ FAIL`).
  - - Columns should be aligned and stable.

#### Hyperlinks (clickable)

- - Output should include clickable hyperlinks when available, using Rich link markup:
  - Example: `[link=https://example]Text[/link]`
- - At minimum, render clickable links for:
  - Documentation references (e.g., `HOW-TO-USE-THIS-TOOL.md`, repo docs)
  - - Lint rule documentation references (when applicable) - Known remediation guides (“How to fix this”)

#### CI mode styling rules

- In `--ci` mode (or non-TTY output):
  - No colors (render with `no_color=True`).
  - - No spinners/progress bars. - No dynamic/reflowing live updates. - Output should remain **tabled and nice** (stable
    tables and stable ordering), but must avoid interactive effects. - Emojis/icons **are allowed** (✅ ❌ ⚠️ etc.), as
    long as output stays stable. - No hyperlink markup. - Keep output predictable and greppable.

#### Theme defaults (initial pick; adjustable later)

- - Primary highlight: **cyan** (headers, running state) - Success: **green** - Failure: **red** - Warning: **yellow** -
  Secondary metadata: **dim**
- Use `box.ROUNDED` for interactive panels/tables, and `box.SIMPLE` for CI/plain.
- - Theme defaults MUST be overridable via a user-configurable YAML theme file (see 2.5.3-G). - CI mode MUST remain
  deterministic and stable; user theme overrides MUST NOT silently change CI output unless explicitly enabled.

### Minimum UI Layout (Interactive)

Every invocation MUST render the following, in this order:

1. 1. **Header Panel** - Command name + subcommand - Repo root - Config files loaded - Output mode (TTY vs CI)
   - Selected filters (`--only`, etc.)

2. 2. **Per-runner Execution Feedback** - For each runner: a Rich status line or progress indicator while it runs. -
   Must not spam; should update in place.

3. 3. **Results Table** - One table summarizing runner results. - Columns (minimum): Runner, Status, Files, Violations,
   Duration

4. 4. **Failure Details (only for failures)** - For each failing runner: - A red panel header including counts. - A
   table of violations with stable columns. - If output is huge, show top N and indicate “+X more”.

5. 5. **Final Summary Panel** - PASS/FAIL counts - Exit code meaning

### Command Visual Grammar (MANDATORY)

**Intent:** Each command must have a consistent, recognizable “shape” so users can scan output instantly.

#### `repo-lint check` (Scan-first)

Output MUST follow this sequence:

1. 1. Header Panel 2. Runner execution feedback (status/progress) 3. Results Table (always) 4. Failure Details (only if
   failures) 5. Final Summary Panel

**Notes:**

- - The Results Table is the primary artifact; details are secondary. - Failure Details must be grouped by runner.

#### `repo-lint fix` (Action-first)

Output MUST follow this sequence:

1. Header Panel (include safety mode state: safe vs `--unsafe`)
2. 2. Pre-flight validation panel (config validation + safety gate summary) 3. Actions Taken Table (always) - Columns
   (minimum): Action, Target, Result, Notes 4. Post-fix verification summary - Must re-run relevant checks (or clearly
   state what was verified). 5. Final Summary Panel (include “files modified” count)

**Notes:**

- - The Actions Taken Table is the primary artifact. - If no changes were needed, Actions Taken Table must still render
  with a clear “No changes required” row.

#### `repo-lint install` (Stepwise checklist)

Output MUST follow this sequence:

1. 1. Header Panel 2. Installation Steps Checklist - A step-by-step checklist that marks each step PASS/FAIL. 3.
   Tools/Dependencies Table - Columns (minimum): Tool, Required Version (if pinned), Installed Version (if detectable),
   Status 4. Next Steps Panel - Show the exact next commands to run. 5. Final Summary Panel

**Notes:**

- - If any step fails, the final summary must clearly state what is blocked.

#### `repo-lint --help` / `<cmd> --help` (Self-teaching)

Help output MUST:

- - Use Rich-Click styling and option grouping - Include the Help Content Contract sections
- Include clickable links to `HOW-TO-USE-THIS-TOOL.md` (TTY mode)
- - Help styling (width, emphasis, minor styling preferences) should be configurable via the UI theme YAML (see
  2.5.3-G), without changing the required Help Content Contract sections or option grouping.

#### CI mode (`--ci`) alignment

- - Preserve the same command “shape” in CI mode, but render it as stable output (no spinners, no ANSI colors). - Tables
  are allowed in CI mode if they remain stable and do not depend on terminal width.

---

## 2.5.2 Rich-Click Help Contract

### Requirements

- - CLI must be implemented using **Click**. - Help output must be rendered using **Rich-Click**.

### Expectations

- `repo-lint --help` should be *rich*, highly readable, and structured:
  - - Styled headings - Styled option groups - Examples section (mandatory) - Notes for CI vs interactive mode - Clear
    exit code semantics summary - Clickable links to docs and relevant references (where supported by the terminal) -
    Help styling (width, emphasis, minor styling preferences) should be configurable via the UI theme YAML (see
    2.5.3-G), without changing the required Help Content Contract sections or option grouping.

### Help Content Requirements

Every command must include:

- - A short description - Detailed help text - Examples (at least 3)
- Notes about `--ci`
- Notes about config files in `conformance/repo-lint/`

### Help Content Contract (MANDATORY)

**Intent:** Help output must be consistent, discoverable, and “self-teaching” across every command.

#### Required Help Sections (every command)

Every Click command MUST include the following help content sections (in this order):

1. 1. **Summary** (1–2 lines) 2. **What this does** (short paragraph) 3. **Examples** (minimum 3; see format below)
4. **Output Modes** (TTY vs `--ci` expectations)
5. 5. **Configuration** (which YAML file(s) are used, where they live) 6. **Exit Codes** (include meanings for all codes
   this command can return) 7. **Troubleshooting** (most common failure modes + what to do)

#### Required Option Groups (stable grouping across commands)

Help output MUST group options under these headings (as applicable), using Rich-Click configuration:

- - **Execution** (e.g., dry-run, timeouts, concurrency if ever added)
- **Filtering** (e.g., `--only`, include/exclude selectors)
- - **Configuration** (e.g., config paths, overrides, validation toggles if allowed)
- **Output** (e.g., `--ci`, verbosity, format)
- **Safety** (e.g., `--unsafe`, `--yes-i-know`, other guardrails)
- - **Advanced** (only if absolutely necessary; keep small)

#### Examples Format (mandatory)

Each command’s help MUST include examples in a consistent format:

- - **Example 1 — Most common usage**
  - Command: `repo-lint <cmd> ...`
  - - What it does: one sentence - **Example 2 — CI usage**
  - Command: `repo-lint <cmd> --ci ...`
  - - What it does: one sentence - **Example 3 — Focused / filtered usage**
  - Command: `repo-lint <cmd> --only <lang> ...`
  - - What it does: one sentence

#### Windows / PowerShell requirements

- - Help output MUST render cleanly in: - Windows PowerShell - PowerShell 7+ - Windows Terminal - Help output MUST NOT
  depend on ANSI features that are commonly broken/disabled in Windows shells.
- Any Rich-Click settings required for Windows compatibility must be documented in `HOW-TO-USE-THIS-TOOL.md`.
- - Help output should prefer clean styling that renders well on Windows; hyperlinks are optional on Windows if
  terminals do not support them reliably.

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
- - Configure it based on mode: - Interactive: colors enabled, terminal forced.
  - CI: `no_color=True`, `force_terminal=False`.

### 2.5.3-C Stable Data Model for Results

Introduce (or standardize) a results model used by all runners so tables can be generated consistently.

Minimum fields:

- - runner name - ok/fail boolean - file count (if available) - violation count - duration - output summary - output
  details (structured, not raw blobs, where feasible)

### 2.5.3-D Update CLI Commands to Use Reporter

- - Replace all direct prints in:
  - `check`
  - `fix`
  - `install`
- - Ensure error messages in interactive mode are Rich panels. - Ensure error messages in CI mode are stable output (no
  colors, no live rendering).

### 2.5.3-E Rich-Click Integration

- - Integrate Rich-Click and configure: - wide help width - grouped options - rich styling - command ordering (stable) -
  show default values where meaningful

### 2.5.3-F Autocomplete and Completion Docs

- - Ensure the Click-based CLI supports shell completion.
- Add completion instructions to `HOW-TO-USE-THIS-TOOL.md` (per shell):
  - - bash - zsh - fish - PowerShell (if supported) - Windows PowerShell and PowerShell 7+ (must be validated; see
    2.5.4)

### 2.5.3-G UI Theme Config (YAML) — Per-Person Formatting

**Intent:** Allow users to customize Rich styling (colors, icons, box styles, help formatting) without editing code,
while keeping CI output deterministic.

#### Default + override locations

- - A default, repo-committed theme YAML MUST live at:
  - `conformance/repo-lint/repo-lint-ui-theme.yaml`
- - A per-user override MAY be loaded from (in precedence order):
  1. CLI flag: `--ui-theme <path>`
  2. Env var: `REPO_LINT_UI_THEME=<path>`
  3. User config path: `~/.config/repo-lint/repo-lint-ui-theme.yaml`

**CI determinism rule:**

- In `--ci` mode, user override loading MUST be disabled by default.
- If a user explicitly supplies `--ui-theme` in CI, it may be used **only** for non-disruptive, stability-safe settings (e.g., emoji enablement), but it MUST NOT enable ANSI colors, spinners, hyperlinks, or dynamic rendering.

#### YAML requirements (strict)

- - The theme YAML MUST be single-document YAML.
- YAML start marker `---` is REQUIRED.
- YAML end marker `...` is REQUIRED.
- - The YAML MUST include:
  - `config_type: repo-lint-ui-theme`
  - `version: 1`

#### Schema model (v1)

The v1 schema MUST support (at minimum):

- `interactive`:
  - `colors` (primary/success/failure/warning/info/metadata)
  - `icons` (pass/fail/warn/skip/running)
  - `box_style` (e.g., `ROUNDED`)
  - `hyperlinks_enabled` (bool)
- `ci`:
  - `icons_enabled` (bool)
  - `box_style` (e.g., `SIMPLE`)
- `help`:
  - `width` (int)
  - `show_defaults` (bool)

**Non-negotiable:** The theme YAML MUST NOT be able to override required semantic behavior (exit codes, Help Content
Contract sections/order, option group headings). It may only affect presentation.

#### Example `repo-lint-ui-theme.yaml` (v1)

```yaml
---
config_type: repo-lint-ui-theme
version: 1

interactive:
  box_style: ROUNDED
  hyperlinks_enabled: true
  colors:
    primary: cyan
    success: green
    failure: red
    warning: yellow
    info: cyan
    metadata: dim
  icons:
    pass: "✅"
    fail: "❌"
    warn: "⚠️"
    skip: "⏭️"
    running: "⏳"

ci:
  box_style: SIMPLE
  icons_enabled: true

help:
  width: 120
  show_defaults: true
...
```

#### Validation

- - Add a strict theme validator that: - Rejects unknown keys at all nesting levels - Produces file + YAML-path error
  messages - Fails fast and loudly

---

## 2.5.4 Validation and Test Plan

### Unit Tests

- - Verify reporter renders without crashing for: - no runners found - all pass - one fail - many fails - huge output
  truncation - config validation failure

### Integration Tests

- Run `repo-lint check` against a small fixture repo and assert:
  - - exit codes - results ordering - stable CI output structure

### Theme Config Validation (MANDATORY)

- Validate default theme file loads successfully: `conformance/repo-lint/repo-lint-ui-theme.yaml`.
- - Validate user override precedence (flag > env > user path).
- Validate that `--ci` disables user overrides by default.
- - Validate that a theme file with:
  - missing `---` / `...`
  - wrong `config_type`
  - unsupported `version`
  - - unknown keys - wrong types fails with clear, path-specific error messages.

### Cross-Platform / Shell Validation (MANDATORY)

The Click + Rich-Click CLI experience MUST be validated on:

- - Linux (bash/zsh) - macOS (zsh) - Windows: - Windows PowerShell - PowerShell 7+ - Windows Terminal

Minimum validations on Windows:

- `repo-lint --help` renders correctly (no broken layout, no unreadable styling).
- `repo-lint check --help` and `repo-lint fix --help` render correctly.
- - Shell completion installation instructions are correct and functional.
- Running `repo-lint check --ci` produces stable output.

If Windows validation fails, it is a release blocker for Phase 2.5.

---

## 2.5.5 Acceptance Criteria (Non-Negotiable)

- - [ ] All user-facing console output is routed through a single Reporter layer. - [ ] Interactive mode output uses
  Rich tables/panels/status. - [ ] CI mode output is stable and predictable (no ANSI colors, no spinners, no dynamic
  rendering).
- [ ] `repo-lint --help` and all subcommand help use Rich-Click.
- - [ ] Help output includes examples, config file notes, and CI notes. - [ ] Help output follows the **Help Content
  Contract (MANDATORY)** (sections + option grouping + examples format). - [ ] Help output and completion instructions
  are validated on Windows (Windows PowerShell + PowerShell 7+ + Windows Terminal).
- [ ] Console output follows the **Command Visual Grammar (MANDATORY)** for `check`, `fix`, and `install`.
- - [ ] Tests added/updated to cover reporter rendering paths.
- [ ] Documentation updated (`HOW-TO-USE-THIS-TOOL.md`) including shell completion setup.
- [ ] A default UI theme YAML exists at `conformance/repo-lint/repo-lint-ui-theme.yaml` and is validated before use.
- [ ] Per-user UI theme overrides are supported (flag/env/user path) and are disabled by default in `--ci` mode.
- - [ ] UI theme YAML can customize presentation only (colors/icons/box/help width) and cannot override semantic
  contracts.
