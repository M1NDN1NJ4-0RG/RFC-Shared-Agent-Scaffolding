# Fixtures Directory

This directory contains **test fixtures** - input data and helper scripts used by conformance tests.

## Purpose

Fixtures provide controlled, repeatable test inputs:
- Helper scripts that produce specific outputs
- Sample input files for archive tests
- Mock configuration files
- Test data files

## Organization

Fixtures can be organized by test category:
```
fixtures/
├── safe-run/          # Fixtures for safe-run tests
│   ├── simple_success.sh
│   ├── print_and_exit.sh
│   └── long_running.sh
├── safe-archive/      # Fixtures for safe-archive tests
│   └── sample_files/
└── preflight/         # Fixtures for preflight tests
    └── mock_responses/
```

## Helper Scripts

Helper scripts should be:
- **Portable** - work on all target platforms (or have platform-specific versions)
- **Simple** - single responsibility, minimal dependencies
- **Documented** - clear header comments explaining purpose and usage

### Example Helper Script Structure

```bash
#!/bin/bash
# Purpose: Print to stdout and stderr, then exit with code
# Usage: print_and_exit.sh <stdout_text> <stderr_text> <exit_code>
# Example: print_and_exit.sh "OUT_TEXT" "ERR_TEXT" 7

echo -n "$1"
echo -n "$2" >&2
exit "$3"
```

## Status

**Current Status:** Directory structure created. Fixtures will be added as needed for tests.

## Platform Considerations

- Unix scripts should use `#!/bin/bash` shebang
- Windows scripts should use `.ps1` or `.bat` extensions
- Cross-platform scripts should be tested on all target platforms
- Scripts should handle arguments consistently across platforms
