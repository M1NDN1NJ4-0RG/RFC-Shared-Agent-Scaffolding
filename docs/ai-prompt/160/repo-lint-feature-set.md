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

# Acceptance Criteria
- [ ] `repo-lint env` exists and supports `--print`, `--install`, `--shell`, `--path-only`.
- [ ] `repo-lint activate` exists and supports interactive subshell and `--command`, with CI-safe behavior.
- [ ] `repo-lint which` exists and prints a Rich table + supports `--json`.
- [ ] All three share a single venv resolution implementation with documented precedence.
- [ ] Cross-platform behavior validated (Linux/macOS + Windows PowerShell).
- [ ] Tests added for resolver + snippets + activator command construction + diagnostics output.
- [ ] Docs updated with examples for all three commands.
