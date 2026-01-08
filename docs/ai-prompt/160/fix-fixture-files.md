## Issue #160 — Rebuild repo_lint test fixtures + add verified `.RESET.diff` patches (ALL languages)

You are working on **Issue #160**.

### Goal

We must have **one fixture file per linter/tool** (paths listed below) where each fixture intentionally contains **MULTIPLE violations** for that tool, and we must also have a **matching `.RESET.diff` file for each fixture** that can restore the fixture to the canonical “bad” state via `git apply` / `patch`.

This work is NOT DONE until:

- All fixture files exist at the exact paths below
- Every fixture contains multiple violations appropriate for the tool it targets
- Every fixture has a corresponding `.RESET.diff`
- Every `.RESET.diff` is verified to apply cleanly using `git apply` (and/or `patch`)
- `REPO-LINT-USER-MANUAL.md` is updated to match the new fixture + reset-diff reality (see hard requirement at end)
- Full repo verification passes (`./scripts/session-end.sh` exit code 0)

---

## ABSOLUTE EXECUTION RULES (DO NOT VIOLATE)

- **DO THESE STEPS IN ORDER. DO NOT SKIP STEPS.**
- **DO NOT PROCEED TO THE NEXT STEP UNTIL THE CURRENT STEP COMPLETES SUCCESSFULLY (EXIT CODE 0).**
- **NO PROGRESS SUMMARIES. NO STATUS NARRATION.** Output only:
  - errors encountered
  - the exact command you are running next
  - the exact file you are editing next
- **DO NOT END THE SESSION** unless you are approaching token/context/time limits. If you must stop, follow the Safety Valve section exactly.

---

## 1) MANDATORY FIRST STEP — RUN AND WAIT

- From repo root, run:
  `./scripts/bootstrap_watch.py`
- WAIT FOR IT TO FINISH AND CONFIRM IT SUCCEEDS (EXIT CODE 0).
- Do not assume it “probably worked.” Do not stop early.

---

## 2) REMOVE EXISTING FIXTURES + RESET DIFFS (CLEAN SLATE)

Before creating anything new, remove any existing fixture files and any existing `.RESET.diff` files that correspond to these targets.

- Delete the fixture and its `.RESET.diff` if either exists.
- Do not leave stale files behind.

Example (adapt paths as needed):

~~~bash
rm -f tools/repo_lint/tests/**/**.RESET.diff
rm -f tools/repo_lint/tests/bash/*.sh
rm -f tools/repo_lint/tests/perl/*.pl
rm -f tools/repo_lint/tests/powershell/*.ps1
rm -f tools/repo_lint/tests/python/*.py
rm -f tools/repo_lint/tests/rust/*.rs
rm -f tools/repo_lint/tests/yaml/*.yaml
~~~

After deletion, verify the target list is absent:

~~~bash
ls -la tools/repo_lint/tests/** || true
~~~

---

## 3) CREATE FIXTURES (EACH MUST CONTAIN MULTIPLE VIOLATIONS)

Create these exact files (and only these files for this issue). Each file must contain **multiple violations** for its intended tool.

### Bash

~~~plaintext
tools/repo_lint/tests/bash/bash-docstring-violations.sh
tools/repo_lint/tests/bash/bash_naming_violations.sh
tools/repo_lint/tests/bash/bash-shellcheck-violations.sh
tools/repo_lint/tests/bash/bash-shfmt-violations.sh
~~~

### Perl

~~~plaintext
tools/repo_lint/tests/perl/perl_docstring_violations.pl
tools/repo_lint/tests/perl/perl-perlNamingViolations.pl
tools/repo_lint/tests/perl/perl-perlcritic_violations.pl
~~~

### PowerShell

~~~plaintext
tools/repo_lint/tests/powershell/PowershellAllDocstringViolations.ps1
tools/repo_lint/tests/powershell/PowershellPsScriptAnalyzerViolations.ps1
tools/repo_lint/tests/powershell/Powershell-naming-violations.ps1
~~~

### Python

~~~plaintext
tools/repo_lint/tests/python/python_all_docstring_violations.py
tools/repo_lint/tests/python/python_black_violations.py
tools/repo_lint/tests/python/python-naming-violations.py
tools/repo_lint/tests/python/python_pylint_violations.py
tools/repo_lint/tests/python/python_ruff_violations.py
~~~

### Rust

~~~plaintext
tools/repo_lint/tests/rust/rust-all-docstring.violations.rs
tools/repo_lint/tests/rust/rust-clippy-violations.rs
tools/repo_lint/tests/rust/rust-rustfmt-violations.rs
tools/repo_lint/tests/rust/rustNamingViolations.rs
~~~

### YAML

~~~plaintext
tools/repo_lint/tests/yaml/yaml-actionlint-violations.yaml
tools/repo_lint/tests/yaml/yaml-all-docstring-violations.yaml
tools/repo_lint/tests/yaml/yaml-yamllint-violations.yaml
tools/repo_lint/tests/yaml/yaml_naming_violations.yaml
~~~

---

## 3.1) DOCSTRING CONTRACT REQUIREMENT (MANDATORY, READ CAREFULLY)

This is a hard rule:

- **ALL fixture files EXCEPT the `*docstring*violations*` fixtures MUST contain docstrings that fully CONFORM to this repository’s docstring contracts for that language.**
- The **docstring violation fixtures** are the ONLY fixtures allowed to violate docstring contracts.

This means:

- `bash-docstring-violations.sh`, `perl_docstring_violations.pl`, `PowershellAllDocstringViolations.ps1`, `python_all_docstring_violations.py`, `rust-all-docstring.violations.rs`, `yaml-all-docstring-violations.yaml`
  - These should contain **multiple docstring/contract violations** on purpose.
- Every other fixture must have **valid, contract-compliant docstrings**.

---

## 3.2) NAMING VIOLATION FIXTURES MUST BE “CLEAN EXCEPT NAMING” (MANDATORY)

This is also a hard rule:

For each `*naming*violations*` fixture:

- The file must conform to **ALL** linting and docstring contracts for that language
- The file must intentionally violate **ONLY** the repo’s naming contract enforcement for that language:
  - filename (already set by this issue’s required paths)
  - plus any symbols inside the file (functions/classes/vars/etc.) that your naming enforcement checks

In other words: these fixtures should be “clean” under every other linter, and fail **only** the naming-contract checks.

---

## 3.3) GENERAL FIXTURE CONTENT REQUIREMENTS (MANDATORY)

For each fixture:

- Include **at least 3 distinct violations** relevant to the tool it targets (more is fine).
- Violations must be deterministic and repeatable.
- Do NOT make environment-dependent violations (no relying on external network, time, machine-specific paths, etc.).
- Ensure each fixture is “obviously wrong” for that tool (e.g., not borderline).

---

## 4) GENERATE A `.RESET.diff` FOR EACH FIXTURE (PATCH/GITHUB COMPATIBLE)

For every fixture file above, create a sibling file:

~~~plaintext
<fixture_file>.RESET.diff
~~~

### `.RESET.diff` rules

- Must be compatible with **GitHub viewing** and apply cleanly with **`git apply`**.
- Must restore the fixture to the canonical “bad” state (the intentionally-violating content).
- Do NOT hand-wave these diffs. Generate them mechanically from git.

### Required workflow to generate each `.RESET.diff`

Do this for each fixture file:

1) Ensure the fixture file exists with the intended canonical “bad” content.
2) Stage NOTHING yet.
3) Generate the diff against `HEAD`:

~~~bash
git diff --no-color -- tools/repo_lint/tests/<...>/<fixture> > tools/repo_lint/tests/<...>/<fixture>.RESET.diff
~~~

1) Sanity check the diff file is non-empty:

~~~bash
test -s tools/repo_lint/tests/<...>/<fixture>.RESET.diff
~~~

---

## 5) VERIFY EACH `.RESET.diff` ACTUALLY APPLIES (MANDATORY)

You must prove each `.RESET.diff` works.

For each fixture:

1) Make a temporary edit to the fixture (change a line) so it no longer matches canonical.
2) Apply the RESET diff:

~~~bash
git apply --whitespace=nowarn tools/repo_lint/tests/<...>/<fixture>.RESET.diff
~~~

1) Verify the fixture is restored to canonical (use `git diff` to confirm it matches the expected “bad” content state you authored).
2) If `git apply` fails:
   - FIX the `.RESET.diff` generation process (do not “force apply”)
   - Re-run the verification until it applies cleanly

Optional additional verification (if available):

~~~bash
patch -p1 < tools/repo_lint/tests/<...>/<fixture>.RESET.diff
~~~

---

## 6) FINAL VERIFICATION

- Run:
  `./scripts/session-end.sh`
If non-zero:
- Fix failures and rerun until **exit code 0**.

---

## CONTEXT / TOKEN / TIME SAFETY VALVE (ONLY IF NECESSARY)

If you are approaching token/context/time limits:

1) **Commit all completed work immediately** (even partial, but coherent).
2) Create/update the journal file for this issue:

~~~plaintext
docs/ai-prompt/160/160-next-steps.md
~~~

1) The journal MUST include:

- Exact stopping point (what was completed vs not)
- Exact next commands to run
- Exact next files to edit
- Any known failing checks and where to look

1) Stop ONLY after the repo is clean and resumable:

~~~bash
git status
~~~

---

## HARD REQUIREMENT — UPDATE USER MANUAL (MANDATORY, MUST MATCH REALITY)

At the very end (after fixtures and `.RESET.diff` are created + verified), update:

~~~plaintext
REPO-LINT-USER-MANUAL.md
~~~

Requirements:

- Document the exact fixture paths for each language/tool (must match the list in this issue).
- Document the `.RESET.diff` behavior and how to apply it (`git apply` and optionally `patch`).
- Remove/replace any outdated references to old fixture names/paths.
- **Verify the manual matches reality** by cross-checking:
  - The file paths exist
  - The `.RESET.diff` files exist
  - The apply commands in the manual actually work

Do NOT mark Issue #160 done until the manual is updated and verified.

---

## Notes (DO NOT IGNORE)

- Do not keep old fixtures. Remove them first.
- Do not create “single violation” fixtures. Each must have multiple violations.
- Naming violation fixtures must be “clean except naming”.
- Non-docstring fixtures MUST have docstrings that conform to repo contracts.
- Do not mark this done until `.RESET.diff` files are proven with `git apply`.
- Do not mark this done until `REPO-LINT-USER-MANUAL.md` is updated and verified.
