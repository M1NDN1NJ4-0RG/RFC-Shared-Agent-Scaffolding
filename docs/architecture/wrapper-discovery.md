# Wrapper Discovery & Binary Invocation

## Overview

Language-specific wrappers (Bash, Perl, Python3, PowerShell) act as **thin invokers** that discover and execute the Rust canonical tool binary. This document defines the deterministic discovery rules that all wrappers must follow.

## Discovery Rules

Wrappers MUST attempt to locate the Rust binary in the following order:

### 1. Environment Override: `SAFE_RUN_BIN`

If the `SAFE_RUN_BIN` environment variable is set, use that path without validation.

**Use case:** Testing, CI overrides, custom installations

```bash
export SAFE_RUN_BIN=/custom/path/to/safe-run
./safe-run.sh arg1 arg2  # Uses /custom/path/to/safe-run
```

### 2. Dev Mode: `./target/release/<tool>`

Check if `./target/release/<tool>` exists relative to the wrapper's repository root.

**Use case:** Local development, testing Rust changes

```bash
cd /path/to/repo
cargo build --release
./wrappers/scripts/bash/scripts/safe-run.sh arg1 arg2
# Uses ./target/release/safe-run
```

### 3. CI Artifact: `./dist/<os>/<arch>/<tool>`

Check if `./dist/<os>/<arch>/<tool>` exists relative to the repository root.

**Use case:** CI workflows with pre-built binaries

Platform-specific paths:
- Linux: `./dist/linux/x86_64/safe-run`
- macOS (Intel): `./dist/macos/x86_64/safe-run`
- macOS (ARM): `./dist/macos/aarch64/safe-run`
- Windows: `./dist/windows/x86_64/safe-run.exe`

```bash
# CI workflow example
- name: Build Rust tool
  run: cargo build --release
- name: Copy to dist
  run: |
    mkdir -p dist/linux/x86_64
    cp target/release/safe-run dist/linux/x86_64/
- name: Test wrapper
  run: ./safe-run.sh echo "Hello"  # Uses ./dist/linux/x86_64/safe-run
```

### 4. PATH Lookup

Search for `<tool>` in the system PATH.

**Use case:** System-wide installation, published releases

```bash
# Install to PATH
cargo install --path ./rust

# Wrapper uses `which safe-run` or equivalent
./safe-run.sh arg1 arg2
```

### 5. Fallback: Error with Instructions

If no binary is found, the wrapper MUST:

1. Print an actionable error message to stderr
2. Exit with code 127 (command not found convention)

**Example error message:**

```
ERROR: Rust canonical tool not found.

Searched locations:
  1. SAFE_RUN_BIN env var (not set)
  2. ./target/release/safe-run (not found)
  3. ./dist/linux/x86_64/safe-run (not found)
  4. PATH lookup (not found)

To install:
  1. Clone the repository
  2. cd rust/
  3. cargo build --release

Or download a pre-built binary from:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases

For more information, see:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/architecture/rust-canonical-tool.md
```

## Argument Pass-Through

Wrappers MUST pass all arguments to the Rust binary **without modification or interpretation**.

### ✅ Correct:

```bash
# Bash wrapper
exec "$SAFE_RUN_BIN" "$@"
```

```powershell
# PowerShell wrapper
& $SafeRunBin @args
```

```python
# Python wrapper
import sys
import subprocess
result = subprocess.run([binary_path] + sys.argv[1:])
sys.exit(result.returncode)
```

### ❌ Incorrect:

```bash
# DO NOT parse or interpret arguments
if [[ "$1" == "--help" ]]; then
  echo "Custom help message"  # WRONG - let Rust handle --help
fi
```

## Exit Code Forwarding

Wrappers MUST preserve the exit code from the Rust binary.

### ✅ Correct:

```bash
# Bash
exec "$SAFE_RUN_BIN" "$@"  # exec replaces shell, preserves exit code
```

```python
# Python
sys.exit(subprocess.run([binary_path] + sys.argv[1:]).returncode)
```

```powershell
# PowerShell
$proc = Start-Process -FilePath $SafeRunBin -ArgumentList $args -Wait -PassThru
exit $proc.ExitCode
```

## Legacy Fallback (Optional)

Wrappers MAY implement a legacy fallback mode for migration purposes:

```bash
if [[ "$SAFE_RUN_USE_LEGACY" == "1" ]]; then
  # Run old implementation
  legacy_safe_run "$@"
  exit $?
fi
```

**Requirements:**

1. Legacy mode MUST be opt-in (env var required)
2. Default behavior MUST be Rust binary
3. Legacy mode SHOULD print a deprecation warning
4. Legacy mode should be removed after transition period

## Platform-Specific Considerations

### Bash/Perl/Python (Unix-like)

- Use `exec` to replace the shell process when possible
- Preserve signal handling
- No shebangs in the Rust binary (wrappers handle that)

### PowerShell (Windows)

- Handle `.exe` extension automatically
- Preserve exit codes correctly (use `$LASTEXITCODE` or `$proc.ExitCode`)
- Support both PowerShell 5.1 (Windows) and PowerShell 7+ (cross-platform)

## Testing Discovery Logic

Wrappers SHOULD include tests that validate discovery logic:

```bash
# Test 1: SAFE_RUN_BIN override
export SAFE_RUN_BIN=/fake/path
./safe-run.sh --version 2>&1 | grep "not found" || echo "FAIL"

# Test 2: Dev mode
cargo build --release
unset SAFE_RUN_BIN
./safe-run.sh --version | grep "safe-run" || echo "FAIL"

# Test 3: Error fallback
rm -rf target/ dist/
unset SAFE_RUN_BIN
./safe-run.sh 2>&1 | grep "ERROR" || echo "FAIL"
```

## Migration Strategy

During the transition from independent implementations to Rust canonical:

1. **Phase 1:** Wrappers detect Rust binary, fall back to legacy if missing
2. **Phase 2:** CI builds Rust binary, wrappers use it by default
3. **Phase 3:** Remove legacy implementations, require Rust binary
4. **Phase 4:** Wrappers become pure invokers (no fallback code)

## References

- [Rust Canonical Tool](./rust-canonical-tool.md)
- [Conformance Contract](../usage/conformance-contract.md)
- [EPIC #33: Rust Canonical Tool](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33)
