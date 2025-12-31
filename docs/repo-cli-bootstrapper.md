# Bootstrap Repo-CLI Tool - Installation and Usage Guide

## Overview

The `bootstrap-repo-cli` is a Rust binary that automates the setup of the repo-lint toolchain and associated development tools in a local Python virtual environment. It replaces the bash script `scripts/bootstrap-repo-cli.sh` with a cross-platform, maintainable Rust implementation.

## Purpose

This tool is designed to bootstrap a development environment with all necessary linting, formatting, and validation tools required for contributing to this repository. It handles:

- Python virtual environment creation (.venv)
- repo-lint package installation
- System tool installations (shellcheck, shfmt, ripgrep, PowerShell, Perl modules)
- Tool verification and validation

## Platform Support

**Supported Platforms:**
- Linux (Debian/Ubuntu with apt-get)
- macOS (with Homebrew or manual tool installation)
- Other Unix-like systems

**Requirements:**
- Python 3.x (with venv module)
- sudo access (for system package installations)
- Internet connection (for downloading packages)

**Optional Package Managers:**
- `apt-get` (for shellcheck, ripgrep, PowerShell on Debian/Ubuntu)
- `go` (for shfmt installation)
- `cpan` or `cpanm` (for Perl::Critic and PPI)
- `pwsh` (PowerShell for PSScriptAnalyzer)

## Installation

### Building from Source

1. **Prerequisites:**
   ```bash
   # Ensure Rust is installed
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Clone the repository
   git clone https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding.git
   cd RFC-Shared-Agent-Scaffolding
   ```

2. **Build the binary:**
   ```bash
   cd rust
   cargo build --release --bin bootstrap-repo-cli
   ```

3. **Binary location:**
   - Debug build: `rust/target/debug/bootstrap-repo-cli`
   - Release build: `rust/target/release/bootstrap-repo-cli`

### Installing to PATH (Optional)

To make the binary available system-wide:

```bash
# Option 1: Copy to a directory in your PATH
sudo cp rust/target/release/bootstrap-repo-cli /usr/local/bin/

# Option 2: Create a symlink
sudo ln -s $(pwd)/rust/target/release/bootstrap-repo-cli /usr/local/bin/bootstrap-repo-cli

# Option 3: Add to your shell profile (bash/zsh)
export PATH="$(pwd)/rust/target/release:$PATH"
```

## Usage

### Basic Usage

Run the bootstrap tool from anywhere inside the repository:

```bash
# If installed to PATH
bootstrap-repo-cli

# If running from source
./rust/target/release/bootstrap-repo-cli

# Or from the rust directory
cd rust
cargo run --bin bootstrap-repo-cli
```

The tool will automatically:
1. Find the repository root by searching for `.git`, `pyproject.toml`, or `README.md`
2. Change to the repository root directory
3. Execute the bootstrap sequence

### What Gets Installed

#### Automatic Installations

1. **Python Virtual Environment (.venv)**
   - Created at repository root
   - Isolated Python environment for repo-lint

2. **repo-lint Package**
   - Installed in editable mode from `tools/repo_cli` or repository root
   - Includes all Python linting tools (black, ruff, pylint, yamllint)
   - Additional tools installed in `.venv-lint/`

3. **System Tools** (if package managers available):
   - **shellcheck**: Bash script linter (via apt-get)
   - **shfmt**: Shell script formatter (via go install)
   - **ripgrep (rg)**: Fast file search tool (via apt-get)
   - **PowerShell (pwsh)**: PowerShell interpreter (via apt-get + Microsoft repos)
   - **PSScriptAnalyzer**: PowerShell linter (via PowerShell module)
   - **Perl::Critic**: Perl linter (via cpan/cpanm or apt-get)
   - **PPI**: Perl parsing library (via cpan/cpanm or apt-get)

### Post-Installation Setup

After running the bootstrap tool, activate the environment in your shell:

```bash
# Activate the Python virtual environment
source .venv/bin/activate

# Add tool directories to PATH
export PATH=".venv-lint/bin:$HOME/go/bin:$PATH"
```

To make this permanent, add to your `.bashrc` or `.zshrc`:

```bash
# Add to ~/.bashrc or ~/.zshrc
cd /path/to/RFC-Shared-Agent-Scaffolding
source .venv/bin/activate
export PATH="$(pwd)/.venv-lint/bin:$HOME/go/bin:$PATH"
```

## Exit Codes

The tool uses specific exit codes to indicate different failure modes:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success - all operations completed |
| 1 | Generic failure |
| 10 | Repository root could not be located |
| 11 | Could not determine install target (no packaging metadata found) |
| 12 | pip install -e failed |
| 13 | repo-lint is not runnable after install |
| 14 | repo-lint exists but failed to run --help |
| 15 | repo-lint install failed (missing tools) |

## Output Format

The tool uses prefixed log messages for clarity:

- `[bootstrap]` - Normal progress messages
- `[bootstrap][WARN]` - Warnings (non-fatal issues)
- `[bootstrap][ERROR]` - Error messages before exit

Example output:
```
[bootstrap] Repo root: /path/to/RFC-Shared-Agent-Scaffolding
[bootstrap] Creating venv: .venv
[bootstrap] Activating venv
[bootstrap] Upgrading pip tooling
[bootstrap] Installing repo-lint (editable) from: /path/to/RFC-Shared-Agent-Scaffolding
[bootstrap] Verifying repo-lint is on PATH
[bootstrap] repo-lint OK: /path/to/.venv/bin/repo-lint
[bootstrap] Running: repo-lint install
[bootstrap] Installing additional required tools...
[bootstrap] Installing shellcheck...
[bootstrap] ✓ shellcheck: /usr/bin/shellcheck
[bootstrap] SUCCESS: Bootstrap complete!
```

## Troubleshooting

### Common Issues

#### 1. Repository root not found (Exit code 10)

**Problem:** Tool cannot locate the repository root.

**Solution:**
- Ensure you're inside the repository directory
- Check that `.git`, `pyproject.toml`, or `README.md` exists
- Run from a subdirectory within the repository

#### 2. pip install failed (Exit code 12)

**Problem:** Python package installation failed.

**Solution:**
```bash
# Ensure Python 3 and venv are installed
sudo apt-get install python3 python3-venv python3-pip

# Check Python version
python3 --version

# Manually test venv creation
python3 -m venv test_venv
```

#### 3. repo-lint not runnable (Exit code 13)

**Problem:** repo-lint installed but not executable.

**Solution:**
```bash
# Check if repo-lint exists
ls -la .venv/bin/repo-lint

# Check if it's executable
file .venv/bin/repo-lint

# Try running directly
.venv/bin/repo-lint --help

# Check Python path
.venv/bin/python3 -c "import sys; print(sys.executable)"
```

#### 4. System tools not installing

**Problem:** shellcheck, shfmt, or other tools fail to install.

**Solution:**

For **apt-get** tools (shellcheck, ripgrep, PowerShell):
```bash
# Update package lists
sudo apt-get update

# Install individually
sudo apt-get install shellcheck
sudo apt-get install ripgrep
```

For **shfmt** (requires Go):
```bash
# Install Go first
sudo apt-get install golang-go

# Then let bootstrap install shfmt, or install manually
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Add Go bin to PATH
export PATH="$HOME/go/bin:$PATH"
```

For **Perl modules**:
```bash
# Option 1: Via apt (Debian/Ubuntu)
sudo apt-get install libperl-critic-perl libppi-perl

# Option 2: Via cpan
sudo cpan -T Perl::Critic PPI

# Option 3: Via cpanm (recommended)
sudo cpan -T App::cpanminus
cpanm --notest Perl::Critic PPI
```

For **PowerShell modules**:
```bash
# After PowerShell is installed
pwsh -Command "Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force"
```

### Manual Verification

Check what was installed:

```bash
# Check repo-lint
.venv/bin/repo-lint --version
.venv/bin/repo-lint --help

# Check system tools
which shellcheck
which shfmt
which rg
which pwsh
perl -MPerl::Critic -e 'print "Perl::Critic OK\n"'
pwsh -Command "Get-Module -ListAvailable PSScriptAnalyzer"
```

### Verbose Debugging

For development and debugging:

```bash
# Build with debug symbols
cd rust
cargo build --bin bootstrap-repo-cli

# Run with environment variable for more output
RUST_BACKTRACE=1 ./target/debug/bootstrap-repo-cli
```

## Development

### Running Tests

```bash
cd rust

# Run unit tests (when added)
cargo test --bin bootstrap-repo-cli

# Run clippy for linting
cargo clippy --bin bootstrap-repo-cli

# Check formatting
cargo fmt --check

# Apply formatting
cargo fmt
```

### Modifying the Tool

The source code is located at:
- Main implementation: `rust/src/bootstrap.rs`
- Binary entry point: `rust/src/bootstrap_main.rs`
- Cargo configuration: `rust/Cargo.toml`

Key functions:
- `find_repo_root()` - Locates repository root
- `create_venv()` - Creates Python virtual environment
- `install_repo_lint()` - Installs repo-lint package
- `verify_repo_lint()` - Verifies installation
- `run_repo_lint_install()` - Runs repo-lint's install command
- `install_*()` functions - Install individual system tools
- `verify_tools()` - Verifies all tool installations

### Adding New Tools

To add a new tool installation:

1. Create a new `install_<tool>()` function following existing patterns
2. Add platform-specific installation logic
3. Call the function from `run()` in the "Install additional tools" section
4. Add verification in `verify_tools()` and `print_success_summary()`

Example:
```rust
/// Install newtool via apt-get
fn install_newtool() {
    if command_exists("newtool") {
        return;
    }

    log("Installing newtool...");
    if install_via_apt("newtool") {
        // Successfully installed
    } else {
        warn("newtool not found and apt-get not available. Please install manually.");
    }
}
```

## Comparison with Bash Script

| Feature | Bash Script | Rust Binary |
|---------|-------------|-------------|
| Lines of code | 321 | ~620 (including docs) |
| Platform support | Unix/Linux (bash) | Unix/Linux (cross-platform Rust) |
| Error handling | Basic exit codes | Structured error types + codes |
| Maintainability | Moderate | High (type safety, modular) |
| Performance | Fast (shell) | Fast (compiled) |
| Dependencies | bash, command, python3 | Rust stdlib only |
| Command existence | Uses `command -v` (shell-dependent) | Cross-platform PATH checking |
| Temporary files | Hardcoded `/tmp/` | Platform-appropriate `temp_dir()` |
| Code reuse | Some duplication | Helper functions (Rule of Three) |

### Advantages of Rust Implementation

1. **Type Safety**: Compile-time checks prevent many runtime errors
2. **Better Error Messages**: Structured error handling with context preservation
3. **Cross-Platform**: PATH checking works on Unix and Windows
4. **Maintainability**: Modular design with helper functions
5. **No Shell Dependencies**: Doesn't rely on bash-specific features
6. **Memory Safety**: Rust's ownership system prevents common bugs

## FAQ

**Q: Do I need to run this every time I work on the repository?**

A: No. Once you've run it successfully, you only need to activate the venv:
```bash
source .venv/bin/activate
export PATH=".venv-lint/bin:$HOME/go/bin:$PATH"
```

**Q: Can I use the bash script instead?**

A: The bash script (`scripts/bootstrap-repo-cli.sh`) is being deprecated in favor of the Rust binary. While it may still work, the Rust version is recommended for better reliability and error handling.

**Q: What if I already have some tools installed?**

A: The bootstrap tool checks for existing installations and skips tools that are already available on your PATH.

**Q: Can I run this in a CI environment?**

A: Yes. The tool is designed to work in automated environments. It handles failures gracefully and provides appropriate exit codes for CI systems.

**Q: How do I update tools after initial installation?**

A: Re-run the bootstrap tool. It will update pip/setuptools/wheel and reinstall repo-lint. For system tools, you may need to update them separately using their respective package managers.

**Q: What if I don't have sudo access?**

A: You can still use the tool for Python venv and repo-lint installation. System tools will need to be installed manually by a system administrator or using user-level package managers.

## Contributing

When making changes to the bootstrap tool:

1. Follow Rust coding standards (rustfmt, clippy)
2. Add unit tests for new functionality
3. Update this documentation with any changes
4. Test on multiple platforms if possible
5. Preserve backward compatibility with exit codes

## License

Same license as the repository (Unlicense).

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for similar problems
- Include the full error output and exit code
