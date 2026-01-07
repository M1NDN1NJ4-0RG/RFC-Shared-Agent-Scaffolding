# [EPIC] [BLOCKER TO ISSUE #235] Rust: split `safe-run` and `bootstrap-repo-cli` into separate packages + purge proto bootstrapper remnants

## Context

Right now, `rust/Cargo.toml` defines a single package (`safe-run`) that also builds the `bootstrap-repo-cli` binary via a second `[[bin]]`.
That coupling means building one tends to build (or at least *touch*) the other, which slows iteration and makes CI/workflows harder to reason about.

There also appears to be an earlier “proto” Rust bootstrapper iteration living in the repo (not the current `bootstrap_v2` implementation), and we want it removed completely.

## Goals

- **Option B — True separation:** make `safe-run` and `bootstrap-repo-cli` separate Rust packages so building one does **not** require building the other.
- Remove *all* “proto-rust-bootstrapper” remnants from the repository (code, tests, docs references, dead files).

## Non-goals

- Refactoring behavior of the current bootstrapper (except where required for the split).
- Changing bootstrapper logic/UX/contracts unless it is required to keep things compiling and CI green.

## Acceptance criteria (definition of done)

- `cargo build -p safe-run` succeeds even if `bootstrap-repo-cli` is broken (i.e., it does not build it).
- `cargo build -p bootstrap-repo-cli` succeeds even if `safe-run` is broken (i.e., it does not build it).
- Existing workflows/scripts that build or run these binaries are updated and passing.
- All references to the removed proto bootstrapper are gone (or replaced with an explicit “removed/replaced” note where historical docs must remain).
- `rg -n "rust/src/bootstrap\.rs|\bbootstrap\.rs\b"` returns **no** matches (except where explicitly allowed by the issue, if any).
- When changes include Rust/source/script changes, `repo-lint check --ci` exits **0**.
- `repo-lint --help` works in the agent environment (verifies the toolchain is available).
- CI is green for the branch (all required workflows pass).

---

## Phase 0 — Preflight / Baseline

- [ ] Create a working branch for this change (do **not** work on main).
- [ ] Verify the agent environment is ready (tools are preinstalled by `copilot-setup-steps.yml`):
  - [ ] From repo root, run: `repo-lint --help` (must exit 0)
  - [ ] If this work will change Rust/source/script files, also run: `repo-lint check --ci` (must exit 0 before committing)
  - [ ] If changes are docs-only, `repo-lint check --ci` is NOT required.
- [ ] Capture baseline build commands (for before/after comparison):
  - [ ] `cd rust && cargo build --release`
  - [ ] `cd rust && cargo test`
- [ ] Identify the current entrypoints:
  - [ ] `safe-run` binary entrypoint
  - [ ] `bootstrap-repo-cli` binary entrypoint

---

## Phase 1 — Identify and remove “proto-rust-bootstrapper” artifacts

## 1.1 Locate proto artifacts (inventory)

- [ ] Use `rg (ripgrep)` to locate all files/mentions of the proto bootstrapper implementation and its tests/docs.
  - [ ] Include code, tests, and docs (especially under `docs/ai-prompt/**`).
- [ ] Produce a short list (in the PR description or an issue note) of:
  - [ ] Files to delete
  - [ ] Files to update (docs + tests)
  - [ ] Any suspected “dead” modules not referenced by the current binary

## 1.2 Remove proto code

- [ ] Remove the proto bootstrapper module(s) from the Rust crate source tree.
  - [ ] Delete the proto file(s).
  - [ ] Remove any `mod` / `pub mod` exports that referenced proto code.
  - [ ] Ensure no downstream compilation units still reference it.

## 1.3 Remove or rewrite proto-related tests

- [ ] Remove tests that only exist to mirror / validate the proto bootstrapper logic.
- [ ] If coverage is still needed:
  - [ ] Replace with tests that target the *current* bootstrapper implementation (the one we intend to keep).

## 1.4 Remove or update proto-related docs references

- [ ] Search `docs/**` for proto bootstrapper references.
- [ ] For historical docs that must remain:
  - [ ] Replace “this file exists at X” with “this file was removed/replaced by Y” and link to the new location.
- [ ] Ensure there are no remaining references to deleted proto paths.

**Gate:** After Phase 1 completes:

- [ ] `cd rust && cargo test` exits 0
- [ ] `rg -n "rust/src/bootstrap\.rs|\bbootstrap\.rs\b"` returns no matches (or only matches explicitly permitted by this issue)

---

## Phase 2 — Implement Option B (true separation) via Cargo workspace

## 2.1 Convert `rust/` to a Cargo workspace

- [ ] Replace `rust/Cargo.toml` with a workspace root:
  - [ ] `members` includes two packages:
    - [ ] `crates/safe-run/`
    - [ ] `crates/bootstrap-repo-cli/`
  - [ ] Set `default-members` to **only** what makes sense for typical dev flows (likely `safe-run`).
- [ ] Ensure `rust/Cargo.lock` is valid for the workspace.

## 2.2 Create the `safe-run` package

- [ ] Move `safe-run` code into `rust/crates/safe-run/`:
  - [ ] `Cargo.toml` for `safe-run`
  - [ ] `src/lib.rs` + modules
  - [ ] `src/main.rs` for the `safe-run` binary
- [ ] Ensure `safe-run`’s dependencies are **only** what it needs (remove bootstrapper-only deps).

## 2.3 Create the `bootstrap-repo-cli` package

- [ ] Move bootstrapper code into `rust/crates/bootstrap-repo-cli/`:
  - [ ] `Cargo.toml` for `bootstrap-repo-cli`
  - [ ] `src/main.rs` for the bootstrapper binary entrypoint
  - [ ] Move the current bootstrapper implementation directory/module (currently `bootstrap_v2`) under this crate.
- [ ] Ensure bootstrapper-only dependencies live only in the bootstrapper crate.

## 2.4 Optional: add a shared library crate (ONLY if it reduces duplication)

- [ ] If you find *real* shared code between the two packages:
  - [ ] Create `rust/crates/shared/` (or similar) and move only the shared pieces there.
- [ ] Do **not** invent a shared crate if it’s not needed.

## 2.5 Update imports, module paths, and docs

- [ ] Update any `use safe_run::...` or `crate::...` references affected by the move.
- [ ] Update docs that reference the old Rust paths so they match the new layout.

**Gate:** After Phase 2 completes:

- [ ] `cd rust && cargo build -p safe-run --release` exits 0
- [ ] `cd rust && cargo build -p bootstrap-repo-cli --release` exits 0
- [ ] `cd rust && cargo test -p safe-run` exits 0
- [ ] `cd rust && cargo test -p bootstrap-repo-cli` exits 0

---

## Phase 3 — Update CI/workflows/scripts to the new workspace layout

## 3.1 Workflows that build safe-run

- [ ] Update workflows (e.g., drift detection) to build `safe-run` via:
  - [ ] `cargo build -p safe-run --release`
- [ ] Update any hardcoded paths if they changed.

## 3.2 Workflows that build bootstrap-repo-cli

- [ ] Update workflows that build the bootstrapper binary to use:
  - [ ] `cargo build -p bootstrap-repo-cli --release`
- [ ] Verify the release workflow(s) produce the expected artifacts.

## 3.3 Scripts/docs invoking `cargo build`

- [ ] Update scripts and docs that run `cargo build` from `rust/` so they:
  - [ ] build the correct package explicitly (via `-p ...`)
  - [ ] do not unintentionally build both targets

**Gate:** After Phase 3 completes:

- [ ] CI workflows that previously built these binaries still pass on the branch.
- [ ] Local “smoke build” commands succeed:
  - [ ] `cd rust && cargo build -p safe-run --release`
  - [ ] `cd rust && cargo build -p bootstrap-repo-cli --release`

---

## Phase 4 — Final cleanup + verification

- [ ] Run final gates appropriate to the changes:
  - [ ] If Rust/source/script files changed: `repo-lint check --ci` must exit 0
  - [ ] If docs-only changes: skip `repo-lint check --ci`
- [ ] Ensure Rust formatting and linting pass before final push:
  - [ ] `cd rust && cargo fmt --all -- --check`
  - [ ] `cd rust && cargo clippy --all-targets --all-features -- -D warnings`
- [ ] Push the branch and confirm CI is green.

---

## Notes / Implementation hints

- Do NOT require `session-start.sh` / `session-end.sh` for Copilot sessions; the toolchain is preinstalled. Use `repo-lint --help` (and `repo-lint check --ci` when applicable) as the gate.
- Prefer workspace separation over complex build flags.
- Make package builds explicit in CI (always pass `-p <package>`).
- Keep target directory shared (`rust/target/`) unless you have a strong reason not to.
