# [EPIC] [BLOCKER TO ISSUE #160] Issue: Add safe parallelism to `repo-lint check --ci` (concurrent.futures) with deterministic output

> **Goal:** Speed up `repo-lint check --ci` by introducing **safe, deterministic parallel execution** using Python’s `concurrent.futures` **wherever it is safe**, while preserving correctness, reproducibility, and readable logs.

## Why we’re doing this

`repo-lint check --ci` currently runs checks **sequentially**, which makes total runtime roughly the **sum** of runner/tool runtimes. Many checks are independent (especially across language runners) and spend most time in **subprocesses**, making them good candidates for **threaded concurrency**.

## Non-goals (for now)

- Do **not** parallelize `repo-lint fix` initially.
- Do **not** change the semantics of pass/fail, exit codes, or report formats.
- Do **not** allow non-deterministic output ordering in CI artifacts/logs.

## Constraints / Contracts

- Output in CI must remain **deterministic**.
- Parallel execution must not introduce flaky behavior.
- If any runner/tool is not thread-safe (shared temp paths, shared output files, etc.), it must be kept sequential.
- All failures must be surfaced clearly, with a stable ordering.

## Definitions

- **Runner**: language-scoped runner (bash/perl/powershell/python/yaml/etc.)
- **Tool**: concrete linter/formatter invoked by a runner
- **Task**: an executable unit of work (runner-level or tool-level)

---

## Phase 0 — Preflight analysis and compare notes

## P0.1 Reproduce baseline performance (mandatory)

- [ ] From repo root, run:
  - [ ] `repo-lint check --ci` (baseline time)
  - [ ] `repo-lint check --ci` again (warm cache time)
- [ ] Record:
  - [ ] Total wall time
  - [ ] Per-runner / per-tool timing if available (or add temporary timing logs)

## P0.2 Confirm current sequential execution (mandatory)

- [ ] Locate and review the runner orchestration code:
  - [ ] `tools/repo_lint/cli_argparse.py` (or current CLI entrypoint)
- [ ] Confirm whether runners are executed with a plain `for runner in runners:` loop and whether tools inside each runner run sequentially.

## P0.3 Identify safe parallelization surfaces (mandatory)

- [ ] Produce a short list in the PR description (or a doc in `docs/`) of:
  - [ ] **Safe parallel targets** (expected: runner-level checks)
  - [ ] **Probably-safe targets** (tool-level checks inside some runners)
  - [ ] **Unsafe targets** (fix mode, anything writing to shared locations)
- [ ] Note any shared resources that could cause races:
  - shared report paths
  - shared temp dirs
  - shared caches / lockfiles
  - shared stdout/stderr streams

**Exit criteria:** We have a baseline and a concrete list of where concurrency is safe.

---

## Phase 1 — Add a concurrency control surface (CLI + env)

## P1.1 Add `--jobs/-j` and env override

- [ ] Add CLI option for `repo-lint check`:
  - [ ] `--jobs/-j` (int, default `1`)
  - [ ] env override: `REPO_LINT_JOBS`
- [ ] Validation:
  - [ ] values < 1 should error
  - [ ] optional cap to CPU count (documented behavior)

## P1.2 Add `--progress` toggle (optional but recommended)

- [ ] Add `--progress` (default: off)
- [ ] Auto-disable progress output in CI / non-TTY unless explicitly enabled
  - Use `sys.stdout.isatty()` as a gate
- [ ] Prefer Rich progress if the project already uses Rich

**Exit criteria:** `repo-lint check --ci --jobs N` parses and is wired (even if still runs sequentially until Phase 2).

---

## Phase 2 — Parallelize at the runner level (safe, big win)

> **This is the primary speed win with the lowest risk.**
> Runners are mostly independent (bash vs python vs yaml vs …).

## P2.1 Implement runner-level parallelism for `check --ci`

- [ ] In the runner orchestration function (e.g., `_run_all_runners(...)`):
  - [ ] If action == `check` and jobs > 1:
    - [ ] Use `concurrent.futures.ThreadPoolExecutor(max_workers=jobs)`
    - [ ] Submit one future per runner: `executor.submit(action_callback, runner)`
  - [ ] Collect results in a **stable order** (e.g., by runner name)
    - **Do not** stream raw output from threads directly to the console

## P2.2 Prevent interleaved output

Implement one of the following (choose 1; recommendation is A or B):

A) Buffered output per runner (recommended)

- [ ] Capture stdout/stderr for each runner’s tool invocations (subprocess capture)
- [ ] Store per-runner log buffer
- [ ] Print buffers in deterministic order after all futures complete (or after each completes, but still printed in
      deterministic order)

B) “Quiet workers + summary printer”**

- [ ] Workers run in quiet mode
- [ ] Main thread prints a structured summary (per runner/tool) after completion

C) Locking stdout

- [ ] Use a global print lock
- [ ] This avoids interleaving but still risks messy log ordering (least preferred)

## P2.3 Deterministic failure ordering

- [ ] Failures should be reported in stable order:
  - runner order (fixed)
  - tool order within runner (fixed)
- [ ] Ensure exit code behavior remains unchanged (any failure -> non-zero)

**Exit criteria:** `repo-lint check --ci --jobs 4` produces the same result as `--jobs 1`, faster, with readable deterministic logs.

---

## Phase 3 — (Optional) Parallelize tool-level checks inside runners

> Only do this where:
>
> - tools are independent **and**
> - they do not contend over the same files/output paths **and**
> - log capture is robust.

## P3.1 Add a “task graph” abstraction (recommended)

- [ ] Introduce a small internal model:
  - `Task(id, runner, tool, command, affected_paths, mode)`
- [ ] Use this to:
  - group tasks that can run concurrently
  - enforce ordering where required

## P3.2 Parallelize only “read-only” tools

- [ ] For each runner:
  - [ ] Identify read-only tool invocations (linters/checkers)
  - [ ] Exclude anything that:
    - writes files
    - creates shared artifacts
    - depends on another tool’s output
- [ ] Execute eligible tools with a `ThreadPoolExecutor` limited by:
  - global `--jobs` or a runner-specific min(job, tool_count)

## P3.3 Keep ordering stable

- [ ] Even if tools run concurrently:
  - [ ] store results keyed by tool name
  - [ ] render results in the canonical tool order

**Exit criteria:** Optional tool-level concurrency yields incremental speedups without flakiness.

---

## Phase 4 — Tests, benchmarks, and guardrails (mandatory)

## P4.1 Unit tests for determinism

- [ ] Add tests to ensure:
  - [ ] stable ordering of runner results regardless of completion order
  - [ ] stable ordering of tool results (if P3 is implemented)
  - [ ] no missing output sections when multiple failures occur

## P4.2 Functional tests in CI

- [ ] Ensure CI runs:
  - [ ] `repo-lint check --ci --jobs 1`
  - [ ] `repo-lint check --ci --jobs 4` (or CPU count capped)
- [ ] Validate that results match (same failures, same exit code)

## P4.3 Benchmark harness

- [ ] Add a simple benchmark doc or script:
  - [ ] baseline vs `--jobs N`
  - [ ] recommended: `hyperfine` if available
- [ ] Record results in a markdown report:
  - `docs/benchmarks/repo-lint-parallelism.md` (or similar)

## P4.4 Safety switches

- [ ] Add a kill switch env var:
  - [ ] `REPO_LINT_DISABLE_CONCURRENCY=1` forces sequential execution
- [ ] Add a debug mode:
  - [ ] `REPO_LINT_DEBUG_TIMING=1` prints per-runner timing summary (deterministic)

**Exit criteria:** Deterministic behavior is tested, concurrency can be disabled, and benchmarks prove improvement.

---

## Documentation updates (mandatory)

- [ ] Update `REPO-LINT-USER-MANUAL.md`:
  - [ ] Document `--jobs/-j`
  - [ ] Document env vars (`REPO_LINT_JOBS`, disable flag)
  - [ ] Document expected behavior in CI (deterministic logs)
- [ ] Update help output / README snippets as needed.

---

## Acceptance criteria

- [ ] `repo-lint check --ci --jobs 1` behaves exactly as before.
- [ ] `repo-lint check --ci --jobs N` is faster on realistic repos, without changing results.
- [ ] Output ordering is deterministic and readable (no interleaved garbage).
- [ ] CI includes coverage for `--jobs 1` and `--jobs > 1`.
- [ ] Concurrency can be disabled via env var.
- [ ] Documentation is updated to match reality.

---

## Notes / Implementation recommendations

- Prefer `ThreadPoolExecutor` over `ProcessPoolExecutor`:
  - Most time is in subprocess tools; threads are sufficient and simpler.
- Keep `fix` sequential until a dependency graph exists.
- When capturing subprocess output:
  - use `text=True`, capture both stdout and stderr
  - store them per runner/tool and emit them deterministically.
