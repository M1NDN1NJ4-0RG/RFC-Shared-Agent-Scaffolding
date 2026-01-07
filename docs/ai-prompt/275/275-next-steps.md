# Issue #275 - Next Steps

## NEXT

- [ ] **Phase 0.1**: Reproduce baseline performance
  - [ ] Run `repo-lint check --ci` multiple times and record timing
  - [ ] Document baseline wall time
- [ ] **Phase 0.2**: Confirm current sequential execution
  - [ ] Locate and review runner orchestration code in `tools/repo_lint/cli_argparse.py`
  - [ ] Confirm sequential execution pattern
- [ ] **Phase 0.3**: Identify safe parallelization surfaces
  - [ ] Analyze which runners/tools can safely run in parallel
  - [ ] Document any shared resources that could cause races
- [ ] **Phase 1**: Add concurrency control surface (CLI + env)
  - [ ] Add `--jobs/-j` option to `repo-lint check`
  - [ ] Add `REPO_LINT_JOBS` env var support
  - [ ] Add validation for job count
  - [ ] Optional: Add `--progress` toggle
- [ ] **Phase 2**: Implement runner-level parallelism
  - [ ] Use `concurrent.futures.ThreadPoolExecutor` for runner-level parallelism
  - [ ] Implement buffered output to prevent interleaving
  - [ ] Ensure deterministic failure ordering
- [ ] **Phase 3** (Optional): Tool-level parallelism
  - [ ] Add task graph abstraction if needed
  - [ ] Parallelize read-only tools within runners
- [ ] **Phase 4**: Tests, benchmarks, and guardrails
  - [ ] Add unit tests for determinism
  - [ ] Add functional tests in CI
  - [ ] Create benchmark harness
  - [ ] Add safety switches (kill switch, debug mode)
- [ ] **Documentation updates**
  - [ ] Update `REPO-LINT-USER-MANUAL.md`
  - [ ] Update help output

## Resume Pointers

- **Branch**: Working on issue #275
- **Key files**:
  - `tools/repo_lint/cli_argparse.py` - CLI entrypoint
  - `tools/repo_lint/` - Main repo-lint implementation
- **Key commands**:
  - `repo-lint check --ci` - Run linting checks
  - `repo-lint --help` - View help
- **Current status**: Starting Phase 0 - preflight analysis
