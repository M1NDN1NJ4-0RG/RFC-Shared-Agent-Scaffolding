# Phase 2.6 — Centralized Exception Rules (No Pragmas Required) for `repo-lint`

> **Goal:** Add a **strict, centralized YAML “exceptions roster”** that declares *what to ignore, where, and why* — with strong validation, auditability, and predictable CI behavior — **without removing pragma support**.

> **Core Principle:** Exceptions are **data**, not **inline code graffiti**.
> - Pragmas remain supported (backward compatible).
> - The YAML exceptions file becomes a first-class alternative (and preferred in docs).

---

## 2.6.0 Scope and Non-Goals

### In Scope
- Add a new YAML config file for centralized ignore/exceptions.
- Define schema + strict validator (same standards as other conformance YAMLs).
- Implement exception application in `repo-lint` for:
  - Docstring validation (function/method/class/module scoping)
  - Linting rule enforcement (per-tool/per-rule scoping)
  - Naming checks (if/when implemented)
- Provide a “why” and “owner” trail for every exception.
- Provide expiration and audit support so exceptions don’t become immortal mold.
- Keep pragma support fully intact, but make YAML-based exceptions a supported parallel mechanism.

### Explicit Non-Goals (for Phase 2.6)
- Removing or breaking pragma support.
- Auto-editing code to remove existing pragmas (optional future phase; a migration helper can exist later).
- Allowing exceptions to disable hard policy/contract enforcement invisibly.

---

## 2.6.1 New Config File: Exceptions / Ignore Rules YAML

### File Location
- `conformance/repo-lint/repo-lint-exceptions.yaml`

### YAML Requirements (STRICT)
- Single-document YAML only
- `---` required
- `...` required
- Must include:
  - `config_type: repo-lint-exceptions`
  - `version: 1`
- Unknown keys at any depth are hard errors
- All string matching must be explicitly typed: `exact`, `glob`, or `regex`
- Regex MUST be anchored unless explicitly `anchored: false`

### High-level Schema (v1)
Top-level keys:
- `meta` (optional but recommended)
- `defaults` (optional)
- `exceptions` (required list)

### Exception Entry Model (v1)
Each entry MUST include:
- `id` (string; stable identifier like `EXC-0001`)
- `scope` (object; where it applies)
- `ignores` (list; what to ignore)
- `reason` (string; why this exists)
- `owner` (string; who owns the exception / team / person)
- `created` (date string `YYYY-MM-DD`)
- `expires` (date string `YYYY-MM-DD` OR `null`)
- `tracking` (optional string; issue/link)

#### `scope` object
Required:
- `language` (enum: `python`, `bash`, `perl`, `powershell`, `rust`, `yaml`, `markdown`, `all`)
- `target_type` (enum: `module`, `class`, `function`, `method`, `file`, `path`, `glob`)

Optional:
- `path` (string)
- `symbol` (string; for function/class/method; supports qualified names)
- `match` (enum: `exact`, `glob`, `regex`)
- `case_sensitive` (bool; default true)
- `include_tests` (bool; default true)

#### `ignores` entries
Each ignore MUST include:
- `category` (enum: `docstrings`, `lint`, `naming`, `other`)
- `tool` (string; e.g., `pylint`, `ruff`, `black`, `shellcheck`, `yamllint`, `custom-docstring-validator`)
- `code` (string; e.g., `pylint:C0116`, `ruff:D103`, `docstring:missing_params`, `naming:snake_case`)
- `severity_override` (optional enum: `low`, `medium`, `high`) — for reporting only
- `notes` (optional string)

### Anti-Typo Contract (MANDATORY)

Exceptions are a policy surface area; typos must not silently weaken enforcement.

- Every `ignores[].tool` MUST match a known tool identifier (from the linting/docstring conformance configs).
- Every `ignores[].code` MUST match a known rule/code for that tool (or a known `category`-scoped code such as `docstring:*` if the docstring validator is internal).
- Unknown tools or codes MUST fail validation (default behavior).
- If an escape hatch is ever required, it MUST be explicit and opt-in via config, e.g. `defaults.allow_unknown_codes: true`, and when enabled it MUST emit a warning and include unknown items in the final summary.

---

## 2.6.2 Enforcement Model & Semantics

### Priority / Precedence Rules
Order of evaluation:
1. Hard policy rules (cannot be overridden)
2. Exceptions YAML
3. Pragmas (still supported)

### Pragma Support Contract (Explicit)
- Pragmas remain **fully supported**.
- The Exceptions YAML is an additional mechanism, not a replacement.
- Documentation should recommend YAML exceptions as the *preferred* method, but pragmas remain valid.

### Conflict Rules (YAML vs Pragma)
If both apply to the same target + rule:
- YAML and pragma MUST produce the same final behavior.
- If behavior differs (conflict):
  - Emit a conflict warning (always, even if pragma warnings are otherwise disabled).
  - Prefer YAML exceptions over pragmas (deterministic + centralized), unless a `prefer_pragmas: true` flag exists (optional future, not required in 2.6).

### Matching Rules
- `target_type: function|method|class` uses symbol resolution when feasible (strongest in Python).
- `target_type: file|path|glob` uses filesystem matching against repo root.
- Regex compiled once; failures are fatal during validation.

### Expiration Rules (The “No Eternal Mold” Contract)
- If `expires` is in the past:
  - CI mode: FAIL with a clear error listing expired exceptions
  - TTY mode: big red panel “Expired Exceptions Detected”
- If `expires` is within N days (default 14):
  - warn (yellow) and include in summary
- If `expires` is null:
  - allowed, but must include explicit permanent rationale in `reason`
  - report these under “Evergreen Exceptions” for auditing

---

## 2.6.3 Optional Pragma Warning Behavior (Configurable)

### Default behavior
- If pragmas are detected, `repo-lint` MAY warn:
  - “Pragma ignore detected; consider migrating to `repo-lint-exceptions.yaml` for centralized control.”

### Configurable warning toggle
Add a setting (choose one mechanism; implement at least one in 2.6):

**Option A — CLI flag**
- `--warn-pragmas / --no-warn-pragmas`
- Default: `--warn-pragmas` in TTY mode, `--no-warn-pragmas` in CI mode (unless explicitly enabled)

**Option B — Config entry in linting rules YAML**
- `conformance/repo-lint/repo-lint-linting-rules.yaml`:
  - `behavior.warn_on_pragmas: true|false`

**Non-negotiable exception**
- If there is a pragma/YAML conflict, warnings MUST always be emitted regardless of the toggle.

---

## 2.6.4 Brilliant Ideas to Apply to Existing YAML Files (Vectors Upgrade)

### 2.6.4-A Add Standard `meta` Block to ALL conformance YAMLs
Apply to:
- `repo-lint-naming-rules.yaml`
- `repo-lint-docstring-rules.yaml`
- `repo-lint-linting-rules.yaml`
- `repo-lint-ui-theme.yaml`
- NEW: `repo-lint-exceptions.yaml`

Recommended fields:
- `meta.schema`
- `meta.schema_version`
- `meta.updated`
- `meta.owner`
- `meta.description`

### 2.6.4-B Add `strict: true` to All conformance YAMLs
- Unknown keys fail validation
- Wrong types fail validation
- Missing required keys fail validation

### 2.6.4-C Add “Config Self-Identification” Contract to All conformance YAMLs
Mandatory everywhere:
- `config_type`
- `version`

### 2.6.4-D Add “Config bundle” concept (OPTIONAL, Future-proofing)
Optional later:
- `conformance/repo-lint/config-bundle.yaml`
that references all config paths as a single entrypoint.

---

## 2.6.5 Implementation Plan (Phase / Item / Sub-Item)

### Phase 2.6.1 — Define Schema + Validator (High)
- [ ] Create new conformance file:
  - [ ] Add `conformance/repo-lint/repo-lint-exceptions.yaml` (default empty structure)
  - [ ] Add docs describing schema and examples
- [ ] Add strict validator:
  - [ ] Implement `tools/repo_lint/conformance/exceptions_schema.py`
  - [ ] Reject unknown keys at every level
  - [ ] Validate `config_type`, `version`, and YAML markers `---` / `...`
  - [ ] Validate date formats (`YYYY-MM-DD`)
  - [ ] Validate expiration logic (expired/expiring soon)
  - [ ] Validate regex patterns compile

### Phase 2.6.2 — Integrate Exceptions into Results + Reporting (High)
- [ ] Exception-aware results model:
  - [ ] Violations carry metadata: tool, code, file, symbol (if known)
  - [ ] Filter violations via exceptions YAML before reporting
  - [ ] Track: original vs ignored vs remaining counts
- [ ] Reporting:
  - [ ] TTY: show “Ignored by Exceptions: X” summary
  - [ ] CI: include “Ignored by Exceptions: X” line
  - [ ] Expired exceptions: CI FAIL; TTY red panel

### Phase 2.6.3 — Keep Pragmas + Optional Warning Control (Medium)
- [ ] Keep pragma evaluation (no breaking changes)
- [ ] Add pragma warning toggle (Option A or B)
- [ ] Implement conflict detection:
  - [ ] If YAML + pragma both match same target+rule and disagree → emit conflict warning ALWAYS
  - [ ] Document precedence behavior

### Phase 2.6.4 — Symbol/Scope Matching Expansion (Medium–High)
- [ ] Python symbol matching (module + qualified name)
- [ ] PowerShell: file/path scoping required; AST symbol optional
- [ ] Bash/Perl/Rust: start with file/path scoping; document limitations

### Phase 2.6.5 — Documentation Updates (Medium)
- [ ] Update `HOW-TO-USE-THIS-TOOL.md`:
  - [ ] Add “Exceptions YAML” section
  - [ ] Add “Pragmas remain supported” note
  - [ ] Add “pragma warning toggle” behavior
  - [ ] Add conflict rules and examples

### Phase 2.6.6 — Tests (High)
- [ ] Validator tests:
  - [ ] Missing markers / wrong config_type / bad regex
  - [ ] Expired exception → CI failure
- [ ] Integration tests:
  - [ ] Fixture with violations + exceptions (counts verified)
  - [ ] Fixture with pragma + YAML conflict (warning emitted even if warnings disabled)

---

## 2.6.6 Acceptance Criteria (Non-Negotiable)
- [ ] New file exists: `conformance/repo-lint/repo-lint-exceptions.yaml`
- [ ] Strict schema validation implemented and enforced before use
- [ ] Unknown keys cause failure (no silent ignores)
- [ ] Exceptions apply deterministically
- [ ] Expired exceptions cause CI failure
- [ ] Output shows counts of ignored violations (TTY + CI)
- [ ] Pragmas remain supported (no breaking changes)
- [ ] Pragma warning is configurable (can be disabled), BUT conflicts always warn
- [ ] Documentation updated with schema + examples + pragma compatibility

---

## 2.6.7 Additional Armor (Recommended)

### 2.6.7-A Exception Transparency (Human trust)
- Add `--show-ignored` (TTY-only) to display a table mapping suppressed violations to `exception.id`.
- Add `--explain-ignored <EXC-ID>` to print the exact scope + ignore codes + reason + expiry.

### 2.6.7-B Exception Auditing (Anti-mold)
- Add `repo-lint exceptions report`:
  - Lists all exceptions grouped by `owner` and by `tool`.
  - Highlights expiring soon and expired.
  - Highlights `expires: null` (“evergreen”) entries.
- Add an “Exception Budget” warning (configurable threshold):
  - If total exceptions exceed N (or exceptions for a tool exceed M), warn loudly.

### 2.6.7-C Determinism Contract (Diff-friendly)
- Exceptions MUST be sorted by `id` when rendered.
- `ignores` within an exception SHOULD be sorted by `category`, then `tool`, then `code`.
- Output MUST be stable regardless of filesystem traversal order.

### 2.6.7-D CI Safety Guardrails
- In `--ci` mode, refuse to load user override exception files unless explicitly provided (mirrors the UI theme determinism rule).
- If both YAML exceptions and pragmas are used in the same run, include a CI summary line:
  - `Ignored by YAML exceptions: X | Ignored by pragmas: Y | Conflicts: Z`

### 2.6.7-E Migration Helper (Non-destructive)
- Add `repo-lint pragmas scan` that:
  - Finds pragmas and prints suggested YAML entries.
  - Does NOT auto-edit code.
  - Supports `--output suggested-exceptions.yaml`.
