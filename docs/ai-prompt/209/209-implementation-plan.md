# Repo-Lint Toolchain Bootstrapper - Detailed Implementation Plan

**Issue:** #209  
**Title:** [EPIC] Repo-Lint Toolchain Bootstrapper (Session-Start Compliance Gate)  
**Priority:** P0 / Blocker  
**Created:** 2025-12-31  
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

This plan outlines the implementation of a Bash-based bootstrapper script that automates the setup of the repo-lint toolchain and development environment. The bootstrapper will be the canonical session-start compliance gate for Copilot agents working on this repository.

**Key Insight:** A Rust implementation already exists (`rust/src/bootstrap.rs`), but the requirement specifies a **Bash script** at `scripts/bootstrap-repo-lint-toolchain.sh`. This plan assumes both implementations will coexist, with the Bash script potentially serving as a lighter-weight alternative for shell-based workflows.

---

## Phase 1: Core Bootstrapper Script Creation

### Item 1.1: Repository Root Discovery
**Objective:** Implement repo root location logic that works from any subdirectory

#### Sub-items:
- [ ] Create `scripts/bootstrap-repo-lint-toolchain.sh` with proper shebang (`#!/usr/bin/env bash`)
- [ ] Add script header documentation (exit codes, purpose, usage)
- [ ] Implement `find_repo_root()` function:
  - [ ] Start from current directory
  - [ ] Walk up directory tree looking for `.git`, `pyproject.toml`, or `README.md`
  - [ ] Return repo root path or exit with code 10 if not found
- [ ] Add error handling for edge cases (filesystem root reached, permission denied)
- [ ] Add debug logging: print repo root when found

**Acceptance:**
- Script can be run from any subdirectory within the repo
- Fails gracefully with exit code 10 if not in a repo

---

### Item 1.2: Python Virtual Environment Setup
**Objective:** Create or verify `.venv/` exists and is functional

#### Sub-items:
- [ ] Implement `ensure_venv()` function:
  - [ ] Check if `.venv/` exists at repo root
  - [ ] If missing, create with `python3 -m venv .venv`
  - [ ] Verify `.venv/bin/python3` exists and is executable
  - [ ] Exit with code 11 if venv creation fails
- [ ] Implement `activate_venv()` function:
  - [ ] Source `.venv/bin/activate` for current shell session
  - [ ] Export `VIRTUAL_ENV`, `PATH` updates
  - [ ] Verify activation by checking `which python3` points to `.venv/bin/python3`
- [ ] Add idempotency: skip creation if venv already exists and is valid
- [ ] Add logging: print venv path and activation status

**Acceptance:**
- `.venv/` is created on first run
- Subsequent runs reuse existing venv
- Venv is properly activated for current shell session

---

### Item 1.3: repo-lint Package Installation
**Objective:** Install repo-lint package into venv in editable mode

#### Sub-items:
- [ ] Implement `install_repo_lint()` function:
  - [ ] Upgrade pip/setuptools/wheel: `python3 -m pip install --upgrade pip setuptools wheel`
  - [ ] Determine install target:
    - [ ] Check if `tools/repo_lint/` exists → install from `tools/repo_lint/`
    - [ ] Otherwise check if `pyproject.toml` exists → install from repo root
    - [ ] Exit with code 12 if no valid install target found
  - [ ] Run `pip install -e <target>` to install repo-lint in editable mode
  - [ ] Verify installation by checking for `repo-lint` or `repo-cli` command
  - [ ] Exit with code 13 if repo-lint not found on PATH after install
- [ ] Add logging: print install target and installation progress
- [ ] Handle installation failures with clear error messages

**Acceptance:**
- repo-lint package is installed in editable mode
- `repo-lint --help` works after installation
- Idempotent: re-installation updates package without errors

---

### Item 1.4: repo-lint Verification
**Objective:** Verify repo-lint is functional and on PATH

#### Sub-items:
- [ ] Implement `verify_repo_lint()` function:
  - [ ] Check `which repo-lint` (or `repo-cli`) finds the command
  - [ ] Run `repo-lint --help` and verify exit code 0
  - [ ] Exit with code 14 if repo-lint exists but `--help` fails
  - [ ] Print repo-lint path and version if available
- [ ] Add logging: confirm repo-lint location and functionality

**Acceptance:**
- `repo-lint --help` succeeds
- Clear error message if verification fails

---

## Phase 2: Tool Installation and Verification

### Item 2.1: Core Utility Installation (rgrep)
**Objective:** Install or verify rgrep availability

#### Sub-items:
- [ ] Implement `check_command()` helper function:
  - [ ] Use `command -v <cmd>` to check if command exists on PATH
  - [ ] Return 0 if found, 1 if not found
- [ ] Implement `install_rgrep()` function:
  - [ ] Check if `rg` (ripgrep) exists
  - [ ] If missing, try platform-specific installation:
    - [ ] Linux (apt): `sudo apt-get install -y ripgrep`
    - [ ] macOS (brew): `brew install ripgrep`
  - [ ] If installation fails or no package manager available:
    - [ ] Warn loudly: "rgrep not available, falling back to grep"
    - [ ] Verify `grep` exists as fallback
    - [ ] Exit with code 2 if neither rgrep nor grep available
- [ ] Add logging: print installation method and result

**Acceptance:**
- `rg` is installed if possible
- Fallback to `grep` with warning if rgrep unavailable
- Fails if neither tool is available

---

### Item 2.2: Python Toolchain Installation
**Objective:** Install black, pylint, pytest, ruff, yamllint

#### Sub-items:
- [ ] Implement `install_python_tools()` function:
  - [ ] Use `repo-lint install` command if available (delegates to repo-lint's install logic)
  - [ ] Alternatively, read `pyproject.toml` for `[project.optional-dependencies.lint]` pinned versions
  - [ ] Install tools in venv: `pip install black==<version> ruff==<version> pylint==<version> yamllint==<version> pytest>=7.0.0`
  - [ ] Use `.venv-lint/` if repo-lint install command creates it
- [ ] Verify each tool after installation:
  - [ ] `black --version`
  - [ ] `ruff --version`
  - [ ] `pylint --version`
  - [ ] `yamllint --version`
  - [ ] `pytest --version`
- [ ] Exit with code 15 if any required Python tool fails to install
- [ ] Add logging: print each tool's version after successful install

**Acceptance:**
- All Python tools are installed in venv
- Versions match pinned versions from `pyproject.toml`
- Tools are functional and on PATH

---

### Item 2.3: Shell Toolchain Installation
**Objective:** Install shellcheck and shfmt

#### Sub-items:
- [ ] Implement `install_shellcheck()` function:
  - [ ] Check if `shellcheck` exists
  - [ ] If missing, try installation:
    - [ ] Linux (apt): `sudo apt-get install -y shellcheck`
    - [ ] macOS (brew): `brew install shellcheck`
  - [ ] If installation fails, print manual install instructions
  - [ ] Exit with code 2 if shellcheck cannot be installed and CI mode is active
- [ ] Implement `install_shfmt()` function:
  - [ ] Check if `shfmt` exists
  - [ ] If missing, try installation:
    - [ ] Via Go: `go install mvdan.cc/sh/v3/cmd/shfmt@latest`
    - [ ] Verify `$HOME/go/bin/shfmt` exists after install
    - [ ] Add `$HOME/go/bin` to PATH if not already present
  - [ ] If Go is not available, print manual install instructions
  - [ ] Exit with code 2 if shfmt cannot be installed and CI mode is active
- [ ] Verify each tool after installation:
  - [ ] `shellcheck --version`
  - [ ] `shfmt -version`
- [ ] Add logging: print installation method and version

**Acceptance:**
- shellcheck is installed and functional
- shfmt is installed and functional
- Clear instructions provided if manual installation needed

---

### Item 2.4: PowerShell Toolchain Installation
**Objective:** Install pwsh and PSScriptAnalyzer

#### Sub-items:
- [ ] Implement `install_pwsh()` function:
  - [ ] Check if `pwsh` exists
  - [ ] If missing, try installation:
    - [ ] Linux (apt, Debian/Ubuntu):
      ```bash
      # Download Microsoft repository GPG keys
      # Register Microsoft repository
      # sudo apt-get update
      # sudo apt-get install -y powershell
      ```
    - [ ] macOS (brew): `brew install --cask powershell`
  - [ ] If installation fails, print manual install instructions
  - [ ] Exit with code 2 if pwsh cannot be installed and CI mode is active
- [ ] Implement `install_psscriptanalyzer()` function:
  - [ ] Requires `pwsh` to be installed first
  - [ ] Run: `pwsh -Command "Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force"`
  - [ ] Verify module is installed: `pwsh -Command "Get-Module -ListAvailable PSScriptAnalyzer"`
  - [ ] Exit with code 2 if installation fails and CI mode is active
- [ ] Verify each tool after installation:
  - [ ] `pwsh --version`
  - [ ] `pwsh -Command "Get-Module -ListAvailable PSScriptAnalyzer"`
- [ ] Add logging: print installation method and version

**Acceptance:**
- pwsh is installed and functional
- PSScriptAnalyzer module is installed
- Clear instructions provided if manual installation needed

---

### Item 2.5: Perl Toolchain Installation
**Objective:** Install Perl::Critic and PPI

#### Sub-items:
- [ ] Implement `install_perl_tools()` function:
  - [ ] Check if `perl` exists (prerequisite)
  - [ ] Check if Perl::Critic is available: `perl -MPerl::Critic -e 'print "OK\n"'`
  - [ ] Check if PPI is available: `perl -MPPI -e 'print "OK\n"'`
  - [ ] If missing, try installation:
    - [ ] Option 1 (apt, Debian/Ubuntu): `sudo apt-get install -y libperl-critic-perl libppi-perl`
    - [ ] Option 2 (cpanm): `cpanm --notest Perl::Critic PPI`
    - [ ] Option 3 (cpan): `sudo cpan -T Perl::Critic PPI`
  - [ ] If installation fails, print manual install instructions
  - [ ] Exit with code 2 if Perl tools cannot be installed and CI mode is active
- [ ] Verify each module after installation:
  - [ ] `perl -MPerl::Critic -e 'print "OK\n"'`
  - [ ] `perl -MPPI -e 'print "OK\n"'`
- [ ] Add logging: print installation method and verification status

**Acceptance:**
- Perl::Critic is installed and importable
- PPI is installed and importable
- Clear instructions provided if manual installation needed

---

## Phase 3: Verification Gate and Error Handling

### Item 3.1: Final Verification Gate
**Objective:** Run `repo-lint check --ci` to verify complete setup

#### Sub-items:
- [ ] Implement `run_verification_gate()` function:
  - [ ] Run `repo-lint check --ci`
  - [ ] Capture exit code and output
  - [ ] If exit code 0: print success message
  - [ ] If exit code 1: print linting violations found (expected on dirty repo)
  - [ ] If exit code 2: print "Missing tools" error and list missing tools
  - [ ] If exit code 3: print "Internal error" and provide troubleshooting steps
  - [ ] Exit with the same code as `repo-lint check --ci`
- [ ] Add `--skip-verify` flag to skip verification gate (for debugging)
- [ ] Add logging: print verification gate output

**Acceptance:**
- `repo-lint check --ci` runs successfully
- Missing tools are clearly listed if verification fails
- Exit code matches `repo-lint check --ci` exit code

---

### Item 3.2: Error Handling and Messages
**Objective:** Provide clear, actionable error messages

#### Sub-items:
- [ ] Implement `die()` helper function:
  - [ ] Accepts message and exit code
  - [ ] Prints error message to stderr in red (if terminal supports color)
  - [ ] Exits with specified code
- [ ] Implement `warn()` helper function:
  - [ ] Accepts message
  - [ ] Prints warning message to stderr in yellow (if terminal supports color)
- [ ] Implement `log()` helper function:
  - [ ] Accepts message
  - [ ] Prints info message to stdout
- [ ] Document all exit codes in script header:
  - [ ] 0: Success
  - [ ] 1: Generic failure
  - [ ] 2: Missing tools (CI mode)
  - [ ] 10: Repo root not found
  - [ ] 11: Venv creation failed
  - [ ] 12: No valid install target found
  - [ ] 13: repo-lint not on PATH after install
  - [ ] 14: repo-lint exists but --help failed
  - [ ] 15: repo-lint install failed (missing tools)
- [ ] Add troubleshooting section in script header

**Acceptance:**
- All error messages are clear and actionable
- Exit codes are documented and consistent
- Warnings are distinct from errors

---

### Item 3.3: Idempotency and State Management
**Objective:** Ensure script can be run multiple times safely

#### Sub-items:
- [ ] Add checks before each operation:
  - [ ] Skip venv creation if `.venv/` exists and is valid
  - [ ] Skip tool installation if tool already exists on PATH
  - [ ] Allow `pip install -e` to update existing installation
- [ ] Add `--force` flag to force re-installation of all components
- [ ] Add `--cleanup` flag to remove `.venv/` and `.venv-lint/` (optional)
- [ ] Test idempotency:
  - [ ] Run script twice in succession
  - [ ] Verify second run completes quickly without errors
  - [ ] Verify tools are still functional after second run

**Acceptance:**
- Script runs successfully multiple times
- Second run is faster (skips already-installed components)
- `--force` flag forces full re-installation

---

## Phase 4: Documentation

### Item 4.1: Inline Script Documentation
**Objective:** Document script usage, exit codes, and behavior in script header

#### Sub-items:
- [ ] Add comprehensive header comment block:
  - [ ] Script purpose and overview
  - [ ] Usage examples
  - [ ] Exit codes with descriptions
  - [ ] Environment variables (if any)
  - [ ] Dependencies and prerequisites
  - [ ] Known limitations
- [ ] Add function-level documentation:
  - [ ] Purpose of each function
  - [ ] Parameters and return values
  - [ ] Exit codes (if function can exit)
- [ ] Add inline comments for complex logic

**Acceptance:**
- Script header contains all essential information
- Functions are clearly documented
- Script is self-documenting

---

### Item 4.2: External Documentation
**Objective:** Create comprehensive external documentation

#### Sub-items:
- [ ] Create `docs/tools/repo-cli/bootstrap-bash.md`:
  - [ ] Overview of Bash bootstrapper vs Rust bootstrapper
  - [ ] How to run the bootstrapper
  - [ ] What gets installed
  - [ ] Platform support and requirements
  - [ ] Troubleshooting common issues
  - [ ] Post-installation setup (activating venv)
  - [ ] Exit codes reference
  - [ ] FAQ
- [ ] Update `CONTRIBUTING.md` (if applicable):
  - [ ] Add "Session-Start Requirements" section
  - [ ] Instruct contributors to run bootstrapper before starting work
  - [ ] Link to detailed documentation
- [ ] Update `README.md` (if applicable):
  - [ ] Add "Quick Start" section with bootstrapper usage
  - [ ] Link to detailed documentation
- [ ] Update `docs/repo-cli-bootstrapper.md`:
  - [ ] Add section comparing Bash vs Rust implementations
  - [ ] Clarify when to use which implementation

**Acceptance:**
- Documentation is comprehensive and easy to follow
- Contributors can run bootstrapper without prior knowledge
- Troubleshooting section covers common issues

---

### Item 4.3: Copilot Session-Start Integration
**Objective:** Document how Copilot should use the bootstrapper at session start

#### Sub-items:
- [ ] Update `.github/copilot-instructions.md`:
  - [ ] Add to "SESSION START REQUIREMENTS (MANDATORY)" section
  - [ ] Specify exact command: `bash scripts/bootstrap-repo-lint-toolchain.sh`
  - [ ] Specify what to do if bootstrapper fails
  - [ ] Specify how to verify success
- [ ] Create example session-start workflow:
  - [ ] Run bootstrapper
  - [ ] Activate venv
  - [ ] Verify repo-lint works
  - [ ] Begin work
- [ ] Document escalation path if bootstrapper fails

**Acceptance:**
- Copilot instructions explicitly require running bootstrapper at session start
- Failure handling is clearly documented
- Success verification is straightforward

---

## Phase 5: Testing and Validation

### Item 5.1: Manual Testing
**Objective:** Manually test bootstrapper in various scenarios

#### Sub-items:
- [ ] Test from repo root directory
- [ ] Test from subdirectory (e.g., `scripts/`, `tools/`)
- [ ] Test on clean environment (no `.venv/`, no tools installed)
- [ ] Test on environment with partial setup (`.venv/` exists, some tools missing)
- [ ] Test on fully-configured environment (all tools installed)
- [ ] Test idempotency (run twice in succession)
- [ ] Test `--force` flag (if implemented)
- [ ] Test error cases:
  - [ ] Run outside repo directory (should exit with code 10)
  - [ ] Simulate missing Python (rename `python3` temporarily)
  - [ ] Simulate missing sudo access
- [ ] Test on different platforms:
  - [ ] Ubuntu/Debian (apt-based)
  - [ ] macOS (brew-based) - optional
- [ ] Verify final state after successful run:
  - [ ] `.venv/` exists and contains repo-lint
  - [ ] All tools are on PATH
  - [ ] `repo-lint check --ci` succeeds

**Acceptance:**
- All manual tests pass
- Error cases are handled gracefully
- Script works on target platforms

---

### Item 5.2: Automated Testing (Optional, if feasible)
**Objective:** Create lightweight automated tests for core logic

#### Sub-items:
- [ ] Create `scripts/tests/test_bootstrap_helpers.sh`:
  - [ ] Test `find_repo_root()` logic
  - [ ] Test `check_command()` logic
  - [ ] Test exit code handling
- [ ] Add test fixtures:
  - [ ] Mock repo structure (`.git`, `pyproject.toml`, etc.)
  - [ ] Mock command availability
- [ ] Run tests in CI (if applicable)

**Note:** Bash testing is complex; prioritize manual testing if automated testing is difficult.

**Acceptance:**
- Core helper functions have basic test coverage (if implemented)
- Tests run in CI (if implemented)

---

## Phase 6: CI Integration and Rollout

### Item 6.1: CI Workflow Updates
**Objective:** Ensure CI can use the bootstrapper

#### Sub-items:
- [ ] Review existing CI workflows (`.github/workflows/`)
- [ ] Identify workflows that need repo-lint toolchain
- [ ] Update workflows to run bootstrapper before linting:
  ```yaml
  - name: Bootstrap repo-lint toolchain
    run: bash scripts/bootstrap-repo-lint-toolchain.sh
  ```
- [ ] Ensure CI has required system packages pre-installed (or bootstrapper installs them)
- [ ] Test CI workflow changes on a separate branch

**Acceptance:**
- CI workflows successfully use bootstrapper
- CI runs are reproducible and deterministic

---

### Item 6.2: Rollout Plan
**Objective:** Plan staged rollout to avoid disruption

#### Sub-items:
- [ ] Phase 1: Documentation-only rollout
  - [ ] Merge documentation first
  - [ ] Announce availability in team channels (if applicable)
- [ ] Phase 2: Optional usage
  - [ ] Merge bootstrapper script
  - [ ] Encourage team to test locally
  - [ ] Collect feedback and iterate
- [ ] Phase 3: Mandatory usage
  - [ ] Update `.github/copilot-instructions.md` to require bootstrapper at session start
  - [ ] Monitor for issues
- [ ] Add deprecation notice for Rust bootstrapper (if Bash replaces it):
  - [ ] Or clarify that both implementations coexist and serve different use cases

**Acceptance:**
- Rollout is gradual and allows for feedback
- Team is not disrupted by sudden changes
- Issues are caught and fixed before mandatory usage

---

## TODOs & Deferrments

### Immediate TODOs (P0 - Blocker)
- [ ] **Phase 1**: Create Bash bootstrapper script with core functionality
- [ ] **Phase 2**: Implement tool installation logic for all required tools
- [ ] **Phase 3**: Add verification gate and error handling
- [ ] **Phase 4.1**: Add inline documentation to script
- [ ] **Phase 4.2**: Create external documentation
- [ ] **Phase 5.1**: Manual testing on Linux
- [ ] **Phase 6.1**: CI integration (if applicable)

### Secondary TODOs (P1 - High)
- [ ] **Phase 4.3**: Update Copilot session-start instructions
- [ ] **Phase 5.2**: Automated testing (if feasible)
- [ ] **Phase 6.2**: Rollout plan execution

### Deferrments (Future Work)
- **macOS Support**: Defer Homebrew-specific installation logic unless there's immediate need
- **Windows Support**: Bash script targets Unix-like systems; Windows support would require PowerShell version
- **Advanced Features**: Defer `--cleanup`, `--force`, verbose modes unless requested
- **Rust vs Bash Decision**: Defer decision on which implementation is canonical; assume coexistence for now
- **Tool Version Management**: Defer pinning system tool versions (shellcheck, shfmt, etc.) to specific versions unless required
- **Offline Installation**: Defer support for air-gapped/offline environments
- **Custom Tool Paths**: Defer support for installing tools in non-standard locations

### Out of Scope
- **IDE Integration**: Bootstrapper is CLI-focused; IDE setup is separate concern
- **Multi-Repo Support**: Bootstrapper is repo-specific; multi-repo tooling is separate epic
- **Tool Configuration**: Bootstrapper installs tools but doesn't manage `.pylintrc`, `.yamllint`, etc.
- **Security Scanning**: Tool vulnerability scanning is separate concern
- **Tool Upgrades**: Bootstrapper installs tools but doesn't manage ongoing upgrades

---

## Success Metrics

### Quantitative Metrics
- [ ] Bootstrapper runs successfully on clean Linux environment (100% success rate)
- [ ] Bootstrapper is idempotent (second run completes in < 10 seconds)
- [ ] `repo-lint check --ci` succeeds after running bootstrapper
- [ ] Zero "missing tools" escalations from Copilot after bootstrapper deployment

### Qualitative Metrics
- [ ] Contributors report bootstrapper is easy to use
- [ ] Error messages are clear and actionable
- [ ] Documentation is comprehensive and easy to follow
- [ ] Copilot agents successfully run bootstrapper at session start without intervention

---

## Risk Assessment

### High Risks
1. **Platform Variability**: Different Linux distributions may require different package managers or package names
   - **Mitigation**: Focus on Debian/Ubuntu (apt) as primary target; provide manual install instructions for other platforms
   
2. **Sudo Requirements**: Many tool installations require sudo, which may not be available in all environments
   - **Mitigation**: Detect missing sudo and fail gracefully with clear instructions; support user-level installations where possible

3. **Network Dependency**: Tool installations require internet access
   - **Mitigation**: Document network requirement; consider caching strategy for CI environments

### Medium Risks
1. **Rust vs Bash Confusion**: Two implementations may cause confusion about which to use
   - **Mitigation**: Clear documentation explaining both options and when to use each

2. **Tool Version Drift**: System package managers may install different versions than expected
   - **Mitigation**: Document version requirements; warn if versions differ significantly

3. **CI Environment Differences**: CI may have different package availability than local environments
   - **Mitigation**: Test bootstrapper in actual CI environment; pre-install required packages in CI setup

### Low Risks
1. **Idempotency Failures**: Running bootstrapper multiple times may cause issues
   - **Mitigation**: Thorough testing of idempotency; add safety checks

2. **PATH Pollution**: Adding many tools to PATH may cause conflicts
   - **Mitigation**: Use venv and `.venv-lint/` to isolate tool installations

---

## Appendix: Reference Information

### Related Issues
- Issue #209: This epic

### Related Documentation
- `docs/repo-cli-bootstrapper.md`: Rust bootstrapper documentation
- `.github/copilot-instructions.md`: Copilot agent guidelines
- `tools/repo_lint/README.md`: repo-lint tool documentation
- `pyproject.toml`: Python dependencies and tool configuration

### Related Code
- `rust/src/bootstrap.rs`: Rust bootstrapper implementation (reference for logic)
- `rust/src/bootstrap_main.rs`: Rust bootstrapper entry point
- `tools/repo_lint/install/`: repo-lint installation helpers

### External Resources
- Bash scripting best practices: https://google.github.io/styleguide/shellguide.html
- ShellCheck: https://www.shellcheck.net/
- Python venv: https://docs.python.org/3/library/venv.html

---

## Plan Version History

**v1.0 - 2025-12-31**
- Initial detailed implementation plan created
- Phased approach with 6 phases
- Comprehensive sub-items with checkboxes
- TODOs, deferrments, and out-of-scope items documented
- Success metrics and risk assessment included
