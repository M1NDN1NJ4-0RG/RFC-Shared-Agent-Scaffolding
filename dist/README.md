# dist/ — CI Artifact Staging Directory

## Purpose

The `dist/` directory is used for **CI artifact staging only**. It provides a standardized location for placing pre-built binaries during CI workflow runs, allowing language wrappers to discover and test against the canonical Rust tool.

## What Goes Here

Platform-specific compiled binaries created during CI builds:

- **Linux (x86_64):** `dist/linux/x86_64/safe-run`
- **macOS (Intel):** `dist/macos/x86_64/safe-run`
- **macOS (ARM):** `dist/macos/aarch64/safe-run`
- **Windows (x86_64):** `dist/windows/x86_64/safe-run.exe`

## Who/What Creates It

**CI workflows** create the `dist/` structure and populate it with binaries during workflow execution:

```yaml
# Example from .github/workflows/test-bash.yml
- name: Stage Rust binary for wrapper discovery
  run: |
    mkdir -p dist/linux/x86_64
    cp rust/target/release/safe-run dist/linux/x86_64/safe-run
    chmod +x dist/linux/x86_64/safe-run
```

**Local development:** You may manually create `dist/` and copy binaries for testing, but this is optional. Wrappers will first check `./target/release/` for local development workflows.

## Should This Be Committed?

**No.** The `dist/` directory and its contents should **not** be committed to version control.

- Build artifacts do not belong in source control
- CI rebuilds binaries on every run from source
- Committing binaries creates maintenance burden and repository bloat
- The `.gitignore` file excludes `dist/` to prevent accidental commits

## Wrapper Discovery Order

Language wrappers (Bash, Perl, Python3, PowerShell) discover the Rust canonical tool using this priority order:

1. **`SAFE_RUN_BIN` environment variable** (highest priority, for testing/CI overrides)
2. **`./target/release/<tool>`** (local development, after `cargo build --release`)
3. **`./dist/<os>/<arch>/<tool>`** (CI artifact staging, **this directory**)
4. **PATH lookup** (system-wide installation)
5. **Error with instructions** (if not found)

See [docs/architecture/wrapper-discovery.md](../docs/architecture/wrapper-discovery.md) for complete discovery rules.

## Related Documentation

- [Wrapper Discovery & Binary Invocation](../docs/architecture/wrapper-discovery.md)
- [Rust Canonical Tool Architecture](../docs/architecture/rust-canonical-tool.md)
- [CI Validation Checklist](../docs/testing/ci-validation-checklist.md)
