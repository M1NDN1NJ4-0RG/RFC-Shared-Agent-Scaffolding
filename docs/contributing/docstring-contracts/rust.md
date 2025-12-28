# Rust Docstring Contract

**Language:** Rust (`.rs`)  
**Canonical style:** Rustdoc using `//!` for module docs, `///` for item docs

## Purpose

Rust source files in this repository use **Rustdoc** to document modules, functions, structs, and other items. Rustdoc comments support Markdown and integrate with `cargo doc` for generated documentation.

## Required Semantic Sections

Every Rust module (file) must include module-level documentation with these sections:

1. **Module summary** - First `//!` line: One-line summary (after `//! # Title`)
2. **# Purpose** - What the module/binary does
3. **# Architecture** or **# Behavior** - High-level design or behavioral contract
4. **# Exit Codes** - For binaries (main.rs): exit code meanings (0, 1, 2, 127, etc.)
5. **# Contract References** - Links to RFCs, specs, or related docs
6. **# Examples** - Minimum 1 code example (using ` ```rust` or ` ```bash`)

**Note:** Use "# Exit Codes" consistently instead of "# Exit Behavior" for clarity and alignment with other language contracts.

### Optional Sections

- **# Usage** - How to use the module/binary
- **# Platform Support** - Platform-specific notes - **Recommended**
- **# Safety** - Unsafe code documentation (if applicable)
- **# Panics** - Panic conditions (if applicable)
- **# Errors** - Error handling patterns

### Library vs Binary Documentation

**For `lib.rs` (library crates):**
- Focus on API documentation
- Document public modules, structs, functions
- Exit codes section is optional (libraries don't have exit codes)
- Emphasize examples showing library usage

**For `main.rs` (binary crates):**
- Document command-line interface
- **Must** include "# Exit Codes" section
- Emphasize examples showing command-line usage
- Document runtime behavior and architecture

### Function/Item Documentation

Functions, structs, and other items should use `///` comments with:
- Summary line
- `# Arguments` or `# Parameters` (if applicable)
- `# Returns` (for functions)
- `# Panics` (if applicable)
- `# Errors` (if returning Result)
- `# Examples` (recommended)

## Formatting Rules

### Module-Level Documentation

```rust
//! # Module Name or Binary Title
//!
//! One-line summary of what this module/binary does.
//!
//! # Purpose
//!
//! Detailed description of the module's role in the system.
//!
//! # Architecture
//!
//! High-level design overview:
//! - Component 1: Description
//! - Component 2: Description
//!
//! # Exit Codes
//!
//! - Exit code 0: Successfully parsed arguments and executed command
//! - Exit code 1: Error during tool execution
//! - Exit code 2: Invalid usage or missing required arguments
//! - Exit codes 3-255: Preserved from executed command
//!
//! # Contract References
//!
//! This implementation conforms to:
//! - rfc-shared-agent-scaffolding-v0.1.0.md (M0 contract)
//! - Conformance vectors in `conformance/vectors.json`
//!
//! # Examples
//!
//! ```bash
//! # Execute a command with safe-run semantics
//! cargo run -- run echo "Hello, world!"
//! ```

use std::process;

// Module code follows...
```

### Function Documentation

```rust
/// Brief one-line description of what the function does.
///
/// More detailed description if needed. Multiple paragraphs are allowed.
///
/// # Arguments
///
/// * `param1` - Description of first parameter
/// * `param2` - Description of second parameter
///
/// # Returns
///
/// Description of return value and its meaning.
///
/// # Panics
///
/// Describe conditions that cause panics (if applicable).
///
/// # Errors
///
/// Describe error conditions for Result-returning functions.
///
/// # Examples
///
/// ```
/// use crate::module::function_name;
/// 
/// let result = function_name(arg1, arg2);
/// assert_eq!(result, expected);
/// ```
pub fn function_name(param1: Type1, param2: Type2) -> ReturnType {
    // Implementation
}
```

### Key Rules

1. **Module docs**: Use `//!` for module-level (inner) documentation
2. **Item docs**: Use `///` for function/struct/item-level (outer) documentation
3. **Markdown headers**: Use `# Header` for sections (renders as H1 in docs)
4. **Code blocks**: Use ` ```rust` for Rust examples, ` ```bash` for shell examples
5. **Lists**: Use `- item` for unordered, `1. item` for ordered
6. **Inline code**: Use backticks for inline code references
7. **Links**: Use `[text](url)` or `[item_name]` for intra-doc links
8. **No blank `//!` or `///`**: Each doc line should have content or be separator

## Templates

### Library Module Template (lib.rs)

```rust
//! # Library Name
//!
//! One-line summary of what this library provides.
//!
//! # Purpose
//!
//! This library provides <functionality> for <use case>. It is designed to
//! be used as a dependency in other Rust projects.
//!
//! # Architecture
//!
//! - **Public API**: Exported functions and types in this module
//! - **Internal modules**: Private implementation details
//! - **Dependencies**: External crates used
//!
//! # Examples
//!
//! ```rust
//! use my_library::{function_name, StructName};
//!
//! // Example usage
//! let result = function_name(arg);
//! assert_eq!(result, expected);
//! ```
//!
//! # Contract References
//!
//! - API documentation: See individual function docs
//! - Design document: `docs/design.md`

pub mod submodule;

use std::collections::HashMap;

// Public API implementation...
```

### Binary Module Template (main.rs)

```rust
//! # Rust Binary Name
//!
//! One-line summary of what this binary does.
//!
//! # Purpose
//!
//! This tool serves as the <role> for the <contract>. It provides structured
//! logging and artifact generation for command execution.
//!
//! # Architecture
//!
//! - **Entry point**: This module (`main.rs`) initializes the CLI
//! - **CLI interface**: The `cli` module defines command-line interface
//! - **Implementation**: The `core` module implements business logic
//!
//! # Exit Codes
//!
//! - Exit code 0: Successfully completed operation
//! - Exit code 1: Error during execution
//! - Exit code 2: Invalid usage or missing arguments
//! - Exit codes 3-255: Preserved from executed command (if applicable)
//!
//! See [exit-codes-contract.md](../docs/contributing/docstring-contracts/exit-codes-contract.md) for
//! canonical exit code meanings.
//!
//! # Contract References
//!
//! This implementation conforms to:
//! - rfc-shared-agent-scaffolding-v0.1.0.md (M0 contract)
//! - Conformance vectors in `conformance/vectors.json`
//! - Wrapper discovery rules in `docs/architecture/wrapper-discovery.md`
//!
//! # Examples
//!
//! ```bash
//! # Execute a command with enhanced logging
//! cargo run -- run echo "Hello, world!"
//!
//! # Check command availability
//! cargo run -- check git --version
//! ```
//!
//! # Platform Support
//!
//! - Linux: Tested on Ubuntu 20.04+ with Rust 1.70+
//! - macOS: Compatible with macOS 11+ (Intel and Apple Silicon)
//! - Windows: Works on Windows 10+ with Rust 1.70+

mod cli;
mod core;

use clap::Parser;
use std::process;

/// Main entry point for the binary.
///
/// # Behavior
///
/// 1. Parses command-line arguments using clap
/// 2. Delegates execution to the appropriate handler
/// 3. Exits with the appropriate status code
///
/// # Exit Codes
///
/// - 0: Success
/// - 1-255: Error or child process exit code
fn main() {
    // Implementation
}
```

### Full Function Template

```rust
/// Find and validate the canonical binary using discovery order.
///
/// Searches for the binary in the following locations:
/// 1. BINARY_PATH environment variable
/// 2. ./rust/target/release/binary (dev mode)
/// 3. ./dist/<os>/<arch>/binary (CI artifacts)
/// 4. PATH lookup
///
/// # Arguments
///
/// * `repo_root` - Path to repository root directory
/// * `binary_name` - Name of the binary to find (without .exe extension)
///
/// # Returns
///
/// Returns `Ok(PathBuf)` with path to binary if found, or `Err(String)`
/// with actionable error message if not found.
///
/// # Errors
///
/// Returns error if:
/// - Binary not found in any search location
/// - Binary found but not executable
/// - Repository root is invalid
///
/// # Examples
///
/// ```
/// use std::path::PathBuf;
/// use crate::discovery::find_binary;
///
/// let repo_root = PathBuf::from("/path/to/repo");
/// let result = find_binary(&repo_root, "safe-run");
/// assert!(result.is_ok());
/// ```
pub fn find_binary(repo_root: &Path, binary_name: &str) -> Result<PathBuf, String> {
    // Implementation
}
```

## Examples (Existing Files)

### Example 1: Binary Main Module
**File:** `rust/src/main.rs`

This file demonstrates:
- Module-level `//!` documentation with `# Purpose`, `# Architecture`, `# Exit Behavior`
- `# Contract References` linking to RFCs and docs
- `# Examples` with bash code blocks
- Main function with `///` documentation

### Example 2: Library Module
**File:** `rust/src/cli.rs` (if exists) or submodules

This demonstrates:
- `//!` module overview
- `///` for public structs and functions
- `# Arguments` and `# Returns` sections
- Examples with ````rust` code blocks

### Example 3: Function Documentation
Throughout `rust/src/`:
- Public functions with `///` comments
- `# Panics` section when applicable
- `# Errors` section for Result types
- Inline examples

## Validation

The validator checks for:
- Presence of module-level documentation (`//!`) in the first 20 lines
- Presence of section headers: `# Purpose`, `# Examples`, `# Exit Behavior` or `# Exit Codes` (for main.rs)
- At least one code example with ` ``` `

The validator does NOT check:
- Rustdoc formatting perfection
- Function-level documentation completeness
- Link validity
- Grammar or spelling

## Common Mistakes

❌ **Wrong:** Using `///` for module docs
```rust
/// Module documentation
/// This is wrong for module-level docs

fn main() {}
```

✅ **Correct:** Use `//!` for module docs
```rust
//! Module documentation
//! This is correct for module-level docs

fn main() {}
```

❌ **Wrong:** No exit codes for binaries
```rust
//! # My Binary
//!
//! # Purpose
//! Does something useful.
```

✅ **Correct:** Document exit codes (use "# Exit Codes" not "# Exit Behavior")
```rust
//! # My Binary
//!
//! # Purpose
//! Does something useful.
//!
//! # Exit Codes
//!
//! - Exit code 0: Success
//! - Exit code 1: Failure
```

❌ **Wrong:** Missing examples
```rust
//! # Module
//!
//! # Purpose
//! Provides utilities.
```

✅ **Correct:** Always include examples
```rust
//! # Module
//!
//! # Purpose
//! Provides utilities.
//!
//! # Examples
//!
//! ```rust
//! use crate::module;
//! ```
```

❌ **Wrong:** No function documentation
```rust
pub fn important_function(x: i32) -> i32 {
    x + 1
}
```

✅ **Correct:** Document public items
```rust
/// Increments the input value by one.
///
/// # Arguments
///
/// * `x` - The value to increment
///
/// # Returns
///
/// The incremented value
pub fn important_function(x: i32) -> i32 {
    x + 1
}
```

## Rustdoc Integration

Code following this contract integrates with Rust's documentation tools:

```bash
# Generate HTML documentation
cargo doc --no-deps

# Generate and open in browser (RECOMMENDED for local preview)
cargo doc --no-deps --open

# Check documentation links
cargo doc --no-deps 2>&1 | grep warning

# Run documentation tests
cargo test --doc
```

**Best Practice:** Use `cargo doc --open` frequently during development to preview
how your documentation will look. This helps catch formatting issues, broken links,
and unclear examples before committing.

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [Rustdoc Book](https://doc.rust-lang.org/rustdoc/) - Official Rustdoc documentation
- [RFC 1574 – API Documentation Conventions](https://rust-lang.github.io/rfcs/1574-more-api-documentation-conventions.html)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/documentation.html)
- [Conformance Contract](../../usage/conformance-contract.md) - Behavior contract
