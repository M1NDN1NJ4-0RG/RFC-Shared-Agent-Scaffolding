## Feature Set (MANDATORY): `repo-lint env` + `repo-lint activate` + `repo-lint which`
We need THREE complementary UX variants:
1) `repo-lint env` — shell integration helper (prints and optionally writes snippet files; MUST NOT auto-edit user rc files).
2) `repo-lint activate` — convenience launcher that spawns a subshell (or runs a command) with the target venv activated so the CLI is immediately usable without manually sourcing activation scripts.
3) `repo-lint which` — diagnostic helper that prints the resolved repo root, venv path, bin/scripts dir, and resolved executable(s), so PATH/venv confusion becomes a one-liner debug.


### Non-negotiable constraints
- NEVER attempt to modify the user’s PATH “automatically” during `pip install` or import time. It’s not reliable and it’s hostile.
- Any persistent changes must be explicit opt-in and MUST NOT edit `.bashrc`/`.zshrc` automatically.
- Must be cross-platform (Linux/macOS + Windows PowerShell).
- Output/behavior must be deterministic and testable.
- Must follow Phase 2.5 Console Output + Rich-Click Help Content Contracts.
- GENERAL RULE (MANDATORY): Any third-party packages rolled into `repo-lint` (new Python deps, extras, or vendored libs) MUST be added to every CI workflow/action/job that depends on them, or CI will fail.
- This includes: lint/test umbrella workflows, repo-lint-specific workflows, and any helper workflows that invoke `repo-lint`.
- Dependency installation steps MUST be updated in lockstep with code changes (same PR), and verified on all supported OS runners.
- Packaging note: if using extras (e.g., `.[dev]`, `.[lint]`), CI MUST install the correct extra(s) explicitly.

## Mandatory: Internal Integration Contract (No “Mystery Helper Scripts”)

If `repo-lint` relies on any helper scripts/tools that are not already clearly part of the `repo-lint` package (e.g., separate one-off scripts living elsewhere in the repo), those helpers MUST be **fully integrated** into `repo-lint` as first-class components.

This requirement applies to:
- Any script/module invoked by `repo-lint` at runtime (subprocess calls, imports, or file execution)
- Any validation/enforcement logic currently implemented in separate helper scripts

This requirement does NOT apply to:
- CI workflows (GitHub Actions / pipeline YAMLs)

### Integration Requirements (Non-negotiable)
- The helper MUST live under the `repo-lint` package/module namespace (e.g., `tools/repo_lint/...`) and be included in packaging (wheel/sdist).
- The helper MUST have a stable, testable Python API (even if it can also be executed as a script).
- Any configuration it uses MUST be wired into the conformance YAML system (and validated by the same strict config validator).
- Invocation MUST be centralized through a single internal interface (no ad-hoc subprocess strings scattered across runners).
- The helper MUST be documented in `HOW-TO-USE-THIS-TOOL.md` and referenced in the Tool Registry Contract (where applicable).
- The helper MUST have unit tests covering:
  - success paths
  - failure modes (missing deps, invalid config, bad input)
  - output schema stability if it emits structured results

### Enforcement
- If `repo-lint` detects it is configured to call an external helper that is not integrated, it MUST fail fast with a clear error explaining what must be integrated and where.


## Mandatory: External Configuration Contract (YAML-First)

`repo-lint` MUST maximize user-configurability while preserving contract safety.

### Scope

Any behavior that can reasonably be configured externally MUST be migrated to the conformance YAML configuration system (or a dedicated `repo-lint` YAML config), including but not limited to:
- tool enable/disable lists (per language)
- tool invocation options/args (where safe)
- file targeting patterns (include/exclude globs)
- severity mapping and fail thresholds
- output styling/theme selections (TTY)
- reporting formats and report destinations (defaults)
- exception/ignore policies (YAML exceptions + pragma policies)

In addition, any behavior currently controlled by:
- hard-coded constants
- ad-hoc environment variables
- CLI-only flags with no config equivalent
- separate helper-script config files

MUST be migrated to YAML-first configuration **wherever it is safe and does not violate contracts**.

### Non-negotiable rules

- External configuration MUST be expressed in YAML (YAML-first).
- Config MUST be strictly validated before use, with:
  - required document start marker `---`
  - required document end marker `...`
  - required `type` marker and `version`
  - schema validation + semantic validation (anti-typo, enum checks, path checks)
- Unknown keys MUST fail validation by default (no silent ignores).
- Config layering MUST be deterministic:
  - Baseline conformance configs in `conformance/repo-lint/` (committed)
  - Optional user overrides supplied explicitly via CLI flags (never auto-discovered in CI)
- CLI flags MUST override config defaults, but MUST NOT allow violating contracts.
- Contract-critical behavior MUST NOT be disable-able via config (e.g., config validation itself, contract enforcement, unsafe-mode acknowledgements).

### Required CLI support

- Add `--config <PATH>` to commands that need configurable defaults (`check`, `fix`, `doctor`, and any future reporting commands).
- Add `--dump-config` (TTY-only) to print the fully-resolved configuration after layering.
- Add `--validate-config <PATH>` command or subcommand (no linting run) that validates a config file and exits non-zero on errors.

### CI determinism

- In `--ci` mode, `repo-lint` MUST NOT auto-load user config from the working directory or home directory.
- In `--ci` mode, only configs explicitly passed via `--config` may be used.
- CI output MUST include a line indicating which config(s) were loaded (or "none").

## Mandatory: Rich-Click CLI Granularity for `check` / `fix` (Per-language + Per-tool + Summary Modes)

We need extremely granular, Rich-Click-documented options for running **specific tools** and controlling **how much output** is emitted.

### Command surface (minimum)
These flags MUST apply to `repo-lint check` and `repo-lint fix` (where applicable):

- `--lang <LANG>`
  - Filters execution to a single language.
  - Supported values MUST include: `python`, `bash`, `perl`, `powershell`, `rust`, `yaml`, `markdown`, `all`.
  - If omitted, tool runs the current default behavior (likely all enabled languages).

- `--tool <TOOL>`
  - Filters execution to a single underlying tool within the selected language.
  - Example: `repo-lint check --lang python --tool black`
  - MUST be repeatable: `--tool black --tool ruff` (or accept comma-separated lists, but repeatable is preferred).
  - MUST validate that the tool is known for the chosen language.

- `--summary` / `--summary-only`
  - `--summary`: show normal output PLUS a compact summary at the end.
  - `--summary-only`: show ONLY a compact summary (no per-file/per-line details).
  - MUST work for full runs and `--tool`-filtered runs.

### Tool availability behavior (non-negotiable)
When `--tool <TOOL>` is requested and the tool is not available:
- The command MUST produce a clear, actionable error:
  - “❌ Tool not installed: <TOOL>”
  - Include the expected install mechanism:
    - If it is a Python dependency: recommend `repo-lint install` (and/or `pip install -e .[dev]` if packaging supports extras).
    - If it is manual/system-level: explicitly say "install manually" and provide the package name(s) we expect (best effort).
- The command MUST exit with the correct exit code for missing tools (match existing ExitCode contract).
- If multiple tools are requested and only some are missing:
  - By default: fail the run (CI-safe)
  - Optional (nice-to-have): a `--skip-missing-tools` flag that continues running available tools but still prints a missing-tools summary and returns non-zero.
### Fix-mode Safety (Mandatory)

Fixing should be safe and predictable.

- Add `--dry-run` to `repo-lint fix`:
  - Shows what would change without modifying files.
- Add `--diff` (TTY-only):
  - Shows unified diff previews for changes (where possible).
- Add `--changed-only` (optional but strongly recommended):
  - If a git worktree is present, restrict checks/fixes to changed files by default when requested.
  - If git is not present, this flag MUST error with a clear message (do not silently broaden scope).

### Output-detail controls (robust-as-hell; minimum set)
Add these flags to control verbosity and ergonomics (all must be Rich-Click documented and tested):

- `--max-violations <N>`
  - Hard cap for detailed items printed (prevents terminal spam).
  - Summary MUST still include total counts.

- `--show-files` / `--hide-files`
  - Whether to list per-file breakdown rows in output tables.

- `--show-codes` / `--hide-codes`
  - Whether to include tool rule IDs/codes (e.g. `ruff:F401`, `pylint:C0114`).

- `--fail-fast`
  - Stop after the first tool failure (useful for local iteration).
  - In CI, default should remain “run all tools then summarize”, unless explicitly set.

- `--explain-tool <TOOL>`
  - Prints what the tool does, what files it targets, how it is invoked, and how to install it.
  - MUST NOT run linting; informational only.

### Output Formats + Reports (Mandatory)

We need a stable way to capture output for humans and CI artifacts.

Add these flags to `repo-lint check` and `repo-lint fix`:

- `--format <FMT>`
  - Supported values MUST include: `rich` (TTY default), `plain` (CI default), `json`, `yaml`, `csv`, `xlsx`.
  - `--ci` MUST force `plain` unless the user explicitly sets `--format`.
  - `csv` and `xlsx` outputs MUST be based on the same underlying normalized data model used for `json`/`yaml`.

- `--report <PATH>`
  - Writes a single consolidated report to disk.
  - If `--format json`, output MUST be valid JSON with a stable schema. If `--format yaml`, output MUST be valid YAML with a stable schema.

- `--reports-dir <DIR>`
  - Writes per-tool reports (one file per tool, plus an index summary file).
  - File naming MUST be deterministic and collision-safe.
  - When `--format csv`, `--reports-dir` MUST emit:
    - `summary.csv` (run-level summary)
    - `violations.csv` (one row per violation)
    - `tools.csv` (one row per tool run)
  - When `--format xlsx`, `--reports-dir` MUST emit:
    - `report.xlsx` with sheets: `Summary`, `Tools`, `Violations`, `MissingTools`, `Ignored`
  - When `--format yaml`, `--reports-dir` MUST emit:
    - `report.yaml` and `index.yaml` (if per-tool files are also emitted)

- `--summary-format <MODE>`
  - Supported values MUST include: `short`, `by-tool`, `by-file`, `by-code`.
  - MUST work with `--summary` and `--summary-only`.

- Report schema (minimum; applies to JSON/YAML and is the source for CSV/XLSX):
- run metadata: repo root, timestamp, platform, python version
- filters: lang(s), tool(s)
- results: per-tool exit status, counts, top offending files, codes
- missing tools summary
- ignored-by-exceptions counts (if exceptions/pragma logic exists)
- normalized tabular model:
  - tools table: tool name, language, status, exit code, duration, missing?
  - violations table: file, line, col, tool, code, message, severity, ignored?, ignore_source, ignore_id
  - summary table: totals by tool/lang/code/file (as requested by `--summary-format`)



### Rich-Click help contract for these flags

Help output MUST show:
  - Examples:
    - `repo-lint check --lang python --tool black --summary-only`
    - `repo-lint check --lang yaml --tool yamllint --max-violations 50`
  - Tool/value enums for `--lang` and `--tool` (where possible).
  - Clear notes about missing-tool behavior and exit codes.



### Back-compat

Existing flags (e.g. `--only` if present) must be supported or cleanly aliased to `--lang`.
If both `--only` and `--lang` are provided, error out with a clear message to avoid ambiguity.



### Tool Registry Contract (Source of Truth)

To keep `--tool` robust and to prevent drift, `repo-lint` MUST maintain a single canonical tool registry.

- The tool registry MUST be derived from the conformance linting/docstring configs (not hard-coded in multiple places).
  - Example: `conformance/repo-lint/repo-lint-linting-rules.yaml` declares tools per language.
  - Example: `conformance/repo-lint/repo-lint-docstring-rules.yaml` declares the docstring validator(s) per language.
- `--tool <TOOL>` MUST validate against this registry.
- Rich-Click help SHOULD enumerate known tools per language (or provide a `--list-tools` command if the list is too long).


### Discoverability (Mandatory)

Add these flags to `repo-lint check` and `repo-lint fix`:

- `--list-langs`
  - Prints supported `--lang` values (stable output).

- `--list-tools [--lang <LANG>]`
  - Prints supported tools.
  - If `--lang` is provided, list only tools for that language.
  - If `--lang` is omitted, list all tools grouped by language.

- `--tool-help <TOOL>`
  - Alias of `--explain-tool <TOOL>` (keep both; users will try both names).

These MUST NOT run linting; informational only.

---

## Extra Glam (MANDATORY): Help Panels + `repo-lint doctor`

### Rich-Click Help Panels (Mandatory)

Rich-Click help output MUST group options into panels/sections with consistent headings. Minimum panels:
- **Filtering**: `--lang`, `--tool`, `--changed-only`
- **Output**: `--summary`, `--summary-only`, `--summary-format`, `--format`, `--report`, `--reports-dir`, `--max-violations`, `--show-files/--hide-files`, `--show-codes/--hide-codes`
- **Execution**: `--fail-fast`, `--skip-missing-tools`
- **Info/Debug**: `--list-langs`, `--list-tools`, `--tool-help`, `--explain-tool`, `--print`, `--no-color`, `--ci`

### `repo-lint doctor` (Mandatory)

Add a new command `repo-lint doctor` that performs a comprehensive environment + configuration sanity check and prints a single **green/red checklist**.

It MUST check:
- repo root resolution
- venv resolution
- tool registry load from conformance YAML
- config validity for all conformance files (linting/docstring/naming/ui theme/exceptions if present)
- tool availability per config (installed vs missing)
- PATH sanity (what `shutil.which("repo-lint")` resolves to)

Flags:
- `--format <FMT>`: supports `rich`, `plain`, `json`, `yaml`
- `--report <PATH>`: write the checklist report
- `--ci`: plain output + non-zero exit if any red items

Exit codes:
- 0 if all checks green
- non-zero if any checks red (use existing policy/tooling exit code conventions)

---

# Shared: Venv + Repo Root Resolution (Used by env/activate/which)

## Venv resolver precedence (shared utility)
Implement a robust resolver (single source of truth):
1) If `--venv` provided -> use it
2) Else if `.venv/` exists under repo root -> use it
3) Else if current Python appears to be running inside a venv (compare `sys.prefix` vs `sys.base_prefix`) -> use `sys.prefix`
4) Else error with a helpful message explaining how to create/select a venv

## Repo root detection (must NOT require .git)
Use the repo-lint repo-root contract (fallback to CWD if no markers found; support env override if already implemented).

## Paths derived from venv
- Linux/macOS:
  - bin dir: `<venv>/bin`
  - activation: `<venv>/bin/activate`
  - fish activation: `<venv>/bin/activate.fish` (if present)
- Windows:
  - scripts dir: `<venv>\\Scripts`
  - activation: `<venv>\\Scripts\\Activate.ps1`
  - cmd activation: `<venv>\\Scripts\\activate.bat`

Add helper `get_venv_bin_dir(venv_path)` returning the correct path by OS.

---

# Part A — `repo-lint env` (Shell Integration Helper)

## CLI
Add Click subcommand:
- `repo-lint env`

### Flags
- `--print` (default): print instructions + shell snippet
- `--install`: write a snippet file to user config dir AND print exact line(s) user must add to their shell rc manually
- `--shell [bash|zsh|fish|powershell]`: select snippet type
  - Default: detect current shell where feasible; otherwise default to bash on *nix and powershell on Windows
- `--venv <path>`: explicit venv path
- `--path-only`: print ONLY the export/set PATH line(s), no prose (automation-friendly)
- `--no-color`: force plain output (piping)
- Respect `--ci`: if `--ci`, default to `--path-only`-style output unless user explicitly requests prose

### Snippet generation
- bash/zsh:
  - `export PATH="<venv>/bin:$PATH"`
- fish:
  - `set -gx PATH "<venv>/bin" $PATH`
- powershell:
  - `$env:Path = "<venv>\\Scripts;" + $env:Path`

### Install file location (opt-in, no rc edits)
On `--install`, write snippet to:
- Linux/macOS: `~/.config/repo-lint/shell/repo-lint-env.<shell>`
- Windows: `%APPDATA%\\repo-lint\\shell\\repo-lint-env.powershell.ps1`

Then print:
- Where file was written
- EXACT line user must add manually:
  - bash/zsh: `source ~/.config/repo-lint/shell/repo-lint-env.bash`
  - fish: `source ~/.config/repo-lint/shell/repo-lint-env.fish`
  - powershell: `. $env:APPDATA\repo-lint\shell\repo-lint-env.powershell.ps1`

### Docs
Update `tools/repo_lint/HOW-TO-USE-THIS-TOOL.md` with a section:
- “Making repo-lint available in your shell”
- Examples for bash/zsh/fish/powershell
- Clarify why rc edits are manual (by design)

### Tests
- unit tests for:
  - venv resolution precedence/errors
  - snippet generation per shell
  - `--path-only` stable output
  - `--install` writes correct file contents (temp dirs / monkeypatch home/appdata)

---

# Part B — `repo-lint activate` (Subshell Launcher / Command Runner)

## CLI
Add Click subcommand:
- `repo-lint activate`

### Flags
- `--venv <path>`: explicit venv path (same resolver)
- `--shell [bash|zsh|fish|powershell|cmd]`: subshell to launch
  - Default: detect current shell if possible; else bash (*nix) / powershell (Windows)
- `--command "<cmd>"`: run a single command inside the activated environment and return its exit code (no interactive shell)
- `--no-rc`: start subshell without loading user rc files when possible (nice-to-have)
- `--print`: print the exact underlying command being executed (debug)
- `--ci`: disallow interactive subshell; require `--command` to avoid hanging CI

### Behavior
#### Linux/macOS
- Interactive:
  - bash: `bash -i -c "source <venv>/bin/activate; exec bash -i"` (or minimal profile if `--no-rc`)
  - zsh: `zsh -i -c "source <venv>/bin/activate; exec zsh -i"`
  - fish: `fish -i -c "source <venv>/bin/activate.fish; exec fish -i"` (if activate.fish missing, fallback or error)
- Command mode:
  - bash: `bash -lc "source <venv>/bin/activate && <cmd>"`
  - zsh:  `zsh -lc  "source <venv>/bin/activate && <cmd>"`

#### Windows
- PowerShell activation: `<venv>\\Scripts\\Activate.ps1`
- Interactive:
  - `powershell -NoExit -Command "& '<venv>\\Scripts\\Activate.ps1';"`
- Command mode:
  - `powershell -NoProfile -Command "& '<venv>\\Scripts\\Activate.ps1'; <cmd>"`

(Optionally support cmd: `<venv>\\Scripts\\activate.bat`.)

### UX / Safety
- If activation scripts missing, error with remediation guidance.
- In interactive mode, print: “Launching subshell with venv activated at <path>”
- In `--command` mode, forward stdout/stderr and return child exit code.

### Tests
- unit tests for command construction (per OS/shell)
- optional integration test (skippable) validating `--command` runs with venv prefix

---

# Part C — `repo-lint which` (Diagnostics / PATH sanity)

## Goal
Make it trivial to debug:
- “Which repo root did you pick?”
- “Which venv did you resolve?”
- “What PATH entry should exist?”
- “Which executable is actually being invoked?”

## CLI
Add Click subcommand:
- `repo-lint which`

### Flags
- `--venv <path>`: explicit venv
- `--shell [bash|zsh|fish|powershell]`: include shell-specific PATH export line
- `--path-line`: print only the PATH line (like `env --path-only` but diagnostic)
- `--json`: output machine-readable JSON (stable keys)
- `--ci`: force stable/plain output (no colors)

### Output (TTY default, Rich table)
Render a table with rows:
- Repo root
- Resolved venv
- Venv bin/scripts dir
- Activation script path
- Resolved `repo-lint` executable path (from:
  - `shutil.which("repo-lint")`
  - plus: the expected venv-local console script path `<venv>/bin/repo-lint` or `<venv>\\Scripts\\repo-lint.exe` if present)
- Python executable in use (`sys.executable`)
- Interpreter prefix/base prefix (`sys.prefix`, `sys.base_prefix`)
- Detected shell (best effort)

If `shutil.which("repo-lint")` points somewhere NOT under the resolved venv, show a warning:
- “repo-lint on PATH does not match resolved venv; consider using `repo-lint env` or `repo-lint activate`”

### JSON Contract (if `--json`)
Stable keys:
- `repo_root`
- `venv_path`
- `venv_bin_dir`
- `activation_script`
- `path_repo_lint`
- `expected_repo_lint`
- `python_executable`
- `sys_prefix`
- `sys_base_prefix`
- `shell_detected`

### Tests
- unit tests for:
  - correct expected paths per OS
  - mismatch detection logic
  - `--json` stable output keys

### Docs
Update `HOW-TO-USE-THIS-TOOL.md`:
- Add section “Debugging PATH / venv issues with `repo-lint which`”
- Include examples:
  - `repo-lint which`
  - `repo-lint which --json`
  - `repo-lint which --shell zsh --path-line`

---

# Implementation Notes / File Suggestions
Create shared modules:
- `tools/repo_lint/env/venv_resolver.py`
- `tools/repo_lint/env/shell_snippets.py`
- `tools/repo_lint/env/activator.py`
- `tools/repo_lint/env/which.py` (or diagnostics)

Wire into Click CLI. Ensure Rich-Click help includes:
- Summary / What this does / Examples / Output modes / Configuration / Exit codes / Troubleshooting.

---

- [ ] `repo-lint env` exists and supports `--print`, `--install`, `--shell`, `--path-only`.
- [ ] `repo-lint activate` exists and supports interactive subshell and `--command`, with CI-safe behavior.
- [ ] `repo-lint which` exists and prints a Rich table + supports `--json`.
- [ ] All three share a single venv resolution implementation with documented precedence.
- [ ] Cross-platform behavior validated (Linux/macOS + Windows PowerShell).
- [ ] Tests added for resolver + snippets + activator command construction + diagnostics output.
- [ ] Docs updated with examples for all three commands.
- [ ] `repo-lint check` and `repo-lint fix` support `--lang <LANG>` and repeatable `--tool <TOOL>` with Rich-Click help and examples.
- [ ] Missing requested tools produce a clear actionable error and the correct exit code (CI-safe, deterministic).
- [ ] `--summary` and `--summary-only` work for full runs and tool-filtered runs.
- [ ] Verbosity controls (`--max-violations`, `--show-files/--hide-files`, `--show-codes/--hide-codes`, `--fail-fast`) are implemented, documented, and tested.
- [ ] `--list-langs` and `--list-tools` exist and do not run linting; output is stable and documented.
- [ ] `--format` supports at least `rich`, `plain`, and `json`, with `--ci` defaulting to `plain`.
- [ ] `--report` and `--reports-dir` write deterministic report artifacts; JSON schema is stable and tested.
- [ ] `--summary-format` supports `short`, `by-tool`, `by-file`, `by-code`.
- [ ] `repo-lint fix` supports `--dry-run` and `--diff` (TTY-only); behavior is documented and tested.
- [ ] `--format` supports `json`, `yaml`, `csv`, and `xlsx` using a single normalized data model.
- [ ] `--reports-dir` emits deterministic multi-file artifacts for `csv` and `xlsx` (with required files/sheets).
- [ ] Rich-Click help groups options into panels with consistent headings (Filtering/Output/Execution/Info).
- [ ] `repo-lint doctor` exists and produces a green/red checklist; supports `--format`, `--report`, and `--ci`.
- [ ] Any non-`repo-lint` helper scripts required by `repo-lint` are fully integrated into the `repo-lint` package namespace, documented, and covered by unit tests (CI workflows excluded).
- [ ] Any behavior that can be configured externally (including behavior currently driven by constants/env/CLI-only toggles) is migrated to YAML-first configuration without allowing contract violations.
- [ ] `--config`, `--dump-config` (TTY-only), and `--validate-config` (no linting) are implemented, documented, and tested.
- [ ] `--ci` mode is deterministic: no auto-discovered configs; only explicit `--config` is honored.
- [ ] Any new third-party dependencies introduced for `repo-lint` are reflected in all CI workflows/actions/jobs that rely on them (including correct extras), verified across supported OS runners.
- [ ] If the dependency set changes, update both: pyproject.toml (or requirements) and CI install steps in the same PR.
