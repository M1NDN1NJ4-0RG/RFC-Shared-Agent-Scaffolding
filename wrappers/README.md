# Language Wrappers

This directory contains thin wrapper scripts in multiple languages that discover and invoke the Rust canonical tool (`safe-run`, `safe-check`, `safe-archive`).

## Purpose

The wrappers act as **invokers**, not independent implementations. They provide:

1. **Cross-language compatibility** - Use the canonical tool from any scripting language
2. **Automatic binary discovery** - Find the Rust binary via multiple fallback strategies
3. **Transparent argument passing** - Forward all arguments to the canonical tool
4. **Exit code forwarding** - Preserve the exact exit code from the canonical tool
5. **Actionable error messages** - Guide users when the Rust binary is missing

## Available Wrappers

### Bash

**Location:** `wrappers/bash/scripts/`

- `safe-run.sh` - Execute commands with event logging
- `safe-check.sh` - Check for existing artifacts
- `safe-archive.sh` - Archive artifacts to timestamped directories

**Requirements:** Bash 4.0+, jq (for conformance testing)

**Usage:**
```bash
./wrappers/bash/scripts/safe-run.sh echo "Hello, World!"
```

### Perl

**Location:** `wrappers/perl/scripts/`

- `safe-run.pl` - Execute commands with event logging
- `safe-check.pl` - Check for existing artifacts
- `safe-archive.pl` - Archive artifacts to timestamped directories

**Requirements:** Perl 5.10+

**Usage:**
```bash
perl ./wrappers/perl/scripts/safe-run.pl echo "Hello, World!"
```

### Python 3

**Location:** `wrappers/python3/scripts/`

- `safe-run.py` - Execute commands with event logging
- `safe-check.py` - Check for existing artifacts
- `safe-archive.py` - Archive artifacts to timestamped directories

**Requirements:** Python 3.8+

**Usage:**
```bash
python3 ./wrappers/python3/scripts/safe-run.py echo "Hello, World!"
```

### PowerShell

**Location:** `wrappers/powershell/scripts/`

- `safe-run.ps1` - Execute commands with event logging
- `safe-check.ps1` - Check for existing artifacts
- `safe-archive.ps1` - Archive artifacts to timestamped directories

**Requirements:** PowerShell 5.1+ (Windows), PowerShell Core 7+ (cross-platform)

**Usage:**
```powershell
pwsh ./wrappers/powershell/scripts/safe-run.ps1 echo "Hello, World!"
```

## How Wrappers Locate the Rust Binary

Wrappers use the following discovery strategy (in order of priority):

1. **Environment variable:** `SAFE_RUN_BIN` (or `SAFE_CHECK_BIN`, `SAFE_ARCHIVE_BIN`)
   - Absolute path to the canonical binary
   - Highest priority - overrides all other methods
   
2. **Dev mode:** `rust/target/release/safe-run` (relative to repository root)
   - Used when running from within the repository during development
   
3. **CI artifacts:** `dist/<os>/<arch>/safe-run`
   - Used in CI/CD pipelines where binaries are staged
   
4. **System PATH:** Search `$PATH` for `safe-run`
   - Falls back to system-installed binary

If none of these locations contain the binary, the wrapper exits with an actionable error message explaining how to build or install the Rust canonical tool.

## Running Wrapper Tests

Each language wrapper has its own test suite documented in its `README.md`:

- **Bash:** `wrappers/bash/README.md` - Test documentation
- **Perl:** `wrappers/perl/README.md` - Test documentation and examples
- **Python 3:** `wrappers/python3/README.md` - Test documentation
- **PowerShell:** `wrappers/powershell/README.md` - Test documentation

To run tests for a specific language:

```bash
# Bash
cd wrappers/bash && bash run-tests.sh

# Perl
cd wrappers/perl && bash run-tests.sh

# Python 3
cd wrappers/python3 && bash run-tests.sh

# PowerShell
cd wrappers/powershell && pwsh run-tests.ps1
```

## Conformance Testing

All wrappers must pass the same conformance test suite defined in `conformance/vectors.json`. This ensures behavioral parity across all language implementations.

See:
- [Conformance Contract](../docs/usage/conformance-contract.md) - Contract specification
- [Drift Detection](../.github/workflows/drift-detection.yml) - Cross-language behavioral validation

## Architecture

Wrappers follow a canonical structure:

```
wrappers/<language>/
├── scripts/              # Implementation files (safe-run.*, safe-check.*, safe-archive.*)
├── tests/                # Test files
├── run-tests.*           # Test runner script
└── README.md             # Test documentation and language-specific notes
```

See:
- [Wrapper Discovery](../docs/architecture/wrapper-discovery.md) - Binary discovery algorithm
- [Canonical Structure](../docs/architecture/canonical-structure.md) - Repository layout

## Contributing

When adding or modifying wrappers:

1. Maintain the invoker pattern - delegate all logic to the Rust canonical tool
2. Preserve binary discovery order and error messages
3. Add tests for any new functionality
4. Run conformance suite to verify behavioral parity
5. Follow language-specific docstring contracts (see `docs/contributing/docstring-contracts/`)

See [Contributing Guide](../docs/contributing/contributing-guide.md) for full details.
