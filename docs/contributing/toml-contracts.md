# TOML Contracts

**Status:** Canonical source of truth for TOML formatting requirements
**Last Updated:** 2026-01-08
**Enforcement:** Enforced via `taplo` in `repo-lint check --ci`

## Overview

This document defines the mandatory TOML formatting and style requirements for the RFC-Shared-Agent-Scaffolding repository. These standards ensure consistency, readability, and maintainability across all TOML configuration files.

**Key Principle:** All TOML files must follow a consistent, deterministic style that is machine-checkable and auto-fixable.

---

## Scope

### Files Enforced

**Default:** All `*.toml` files in the repository are subject to TOML linting.

**Included files:**

- `pyproject.toml` (Python project configuration)
- `Cargo.toml` (Rust project manifests)
- `.bootstrap.toml` (bootstrap configuration)
- `rust/.cargo/config.toml` (Cargo configuration)
- `taplo.toml` (Taplo configuration itself)
- Any future `*.toml` configuration files

### Exclusions

The following files/directories are **explicitly excluded** from TOML linting:

1. **Vendored/third-party lockfiles:** (none currently)
   - **Future:** If external TOML lockfiles are vendored, add exclusions here

2. **Temporary/scratch files:** Any `*.toml` files in `/tmp/` or build artifacts

**Important:** Exclusions MUST be documented with a clear reason. Avoid broad exclusions.

---

## Ruleset

### Rule Philosophy

This ruleset follows **TOML Best Practices** from authoritative sources:

- [TOML Specification v1.0.0](https://toml.io/en/v1.0.0) - Official TOML specification
- [Taplo Documentation](https://taplo.tamasfe.dev/) - Industry-standard TOML formatter
- [Cargo Book TOML Guide](https://doc.rust-lang.org/cargo/reference/manifest.html) - Rust TOML best practices

**Core Principles:**

- **Prefer machine-fixable rules** to reduce manual effort
- **No vague rules:** Every rule must be deterministic and checkable
- **Compatibility first:** Rules must work with TOML v1.0.0
- **Readability:** TOML files should be easy to read and edit by humans
- **Consistency:** Use one style throughout the repository

### Core Rules (MANDATORY)

#### 1. Indentation and Whitespace

**Indentation:** Use **2 spaces** for indentation (Taplo default, widely used convention)

**Rationale:** 2 spaces provide good readability while conserving horizontal space in nested structures.

```toml
# ✅ Correct - 2 space indentation
[tool.black]
line-length = 120
target-version = ['py38']
exclude = '''
  /(
    \.git
    | dist
  )/
'''

# ❌ Wrong - 4 space indentation
[tool.black]
    line-length = 120
    target-version = ['py38']
```

**No tabs:** Use spaces only, never tabs

**Rationale:** TOML spec allows tabs, but spaces are more consistent across editors.

```toml
# ✅ Correct - spaces
[project]
name = "repo_lint"

# ❌ Wrong - tabs
[project]
	name = "repo_lint"
```

**Trailing whitespace:** Remove all trailing whitespace from lines

**Rationale:** Prevents diff noise and inconsistent rendering.

#### 2. Key-Value Formatting

**Space around equals:** MUST have exactly one space on each side of `=`

**Rationale:** Improves readability and consistency (TOML best practice).

```toml
# ✅ Correct
name = "repo_lint"
version = "0.1.0"

# ❌ Wrong - no spaces
name="repo_lint"

# ❌ Wrong - multiple spaces
version  =  "0.1.0"
```

**Key ordering:** Keys within a table SHOULD be alphabetically sorted when practical

**Rationale:** Makes it easier to find keys and prevents merge conflicts.

**Exception:** Cargo.toml follows Cargo conventions where certain keys (name, version, edition) come first by convention.

```toml
# ✅ Correct - alphabetical within reason
[project]
description = "Unified multi-language lint tool"
name = "repo_lint"
requires-python = ">=3.8"
version = "0.1.0"

# ✅ Also acceptable - logical grouping (Cargo style)
[package]
name = "bootstrap-repo-cli"
version = "0.1.0"
edition = "2021"
```

#### 3. Quoting

**String quoting:** Use **double quotes** (`"`) for strings, not single quotes (`'`)

**Rationale:** Double quotes are more common in TOML and JSON; single quotes are only for literal strings.

```toml
# ✅ Correct - double quotes
name = "repo_lint"
description = "A linting tool"

# ❌ Wrong - single quotes (literal strings)
name = 'repo_lint'
```

**Multi-line strings:** Use triple double-quotes (`"""`) for multi-line strings

```toml
# ✅ Correct
exclude = '''
/(
  \.git
  | dist
)/
'''

# Also correct (double quotes)
exclude = """
/(
  \\.git
  | dist
)/
"""
```

**Bare keys:** Prefer bare keys (unquoted) when possible

```toml
# ✅ Correct - bare keys
[tool.black]
line-length = 120

# ❌ Wrong - unnecessary quotes
["tool"."black"]
"line-length" = 120
```

#### 4. Arrays

**Inline arrays:** Short arrays (≤3 items) MAY be inline

```toml
# ✅ Correct - short inline array
target-version = ['py38']
tags = ["cli", "linting"]

# ✅ Also correct - multi-line for clarity
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=10.0",
]
```

**Multi-line arrays:** Arrays with >3 items SHOULD be multi-line

**Formatting:**

- One item per line
- Indent items by 2 spaces (or 4 spaces from enclosing table)
- Trailing comma on last item (prevents diff noise)

```toml
# ✅ Correct - multi-line array
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=10.0",
    "rich-click>=1.6.0",
]

# ❌ Wrong - long inline array
dependencies = ["PyYAML>=6.0", "click>=8.0", "rich>=10.0", "rich-click>=1.6.0"]

# ❌ Wrong - no trailing comma
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0"
]
```

**Trailing commas:** MUST use trailing comma on last item in multi-line arrays

**Rationale:** Prevents diff noise when adding new items.

#### 5. Tables and Sections

**Table header spacing:** Blank line BEFORE each top-level `[table]` header (except the first)

**Rationale:** Improves visual separation and readability.

```toml
# ✅ Correct - blank lines before tables
[build-system]
requires = ["setuptools>=61.0"]

[project]
name = "repo_lint"

[tool.black]
line-length = 120

# ❌ Wrong - no blank lines
[build-system]
requires = ["setuptools>=61.0"]
[project]
name = "repo_lint"
[tool.black]
line-length = 120
```

**Blank line after table header:** No blank line immediately after `[table]` header

```toml
# ✅ Correct
[project]
name = "repo_lint"
version = "0.1.0"

# ❌ Wrong - unnecessary blank line
[project]

name = "repo_lint"
```

**Dotted keys vs nested tables:** Prefer nested tables `[a.b.c]` over dotted keys for deep nesting

```toml
# ✅ Correct - nested table header
[tool.black]
line-length = 120

# ❌ Avoid - dotted key (less clear for deep nesting)
tool.black.line-length = 120
```

#### 6. Comments

**Comment style:** Use `#` for comments with a space after the `#`

```toml
# ✅ Correct comment format
# This is a comment
name = "repo_lint"  # Inline comment

#❌ Wrong - no space after #
name = "repo_lint"
```

**Inline comments:** Separate inline comments from code with at least 2 spaces

```toml
# ✅ Correct - 2+ spaces
name = "repo_lint"  # Project name

# ❌ Wrong - only 1 space
version = "0.1.0" # Version
```

**Comment position:** Comments SHOULD appear above the line they describe (not inline) for multi-line values

```toml
# ✅ Correct - comment above
# Testing dependencies
test = [
    "pytest>=7.0.0",
]

# ❌ Avoid - inline comment for multi-line value
test = [  # Testing dependencies
    "pytest>=7.0.0",
]
```

#### 7. Line Length

**Maximum line length:** **120 characters**

**Rationale:** Matches the repository's line length standard (Python, Markdown) for consistency.

**Exception:** Long string values (URLs, file paths) MAY exceed 120 characters if splitting would break functionality.

```toml
# ✅ Correct - within limit
description = "Unified multi-language lint and docstring validation tool"

# ⚠️ Acceptable exception - URL
repository = "https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding"

# ❌ Wrong - unnecessarily long line that could be split
very-long-array = ["item1", "item2", "item3", "item4", "item5", "item6", "item7", "item8", "item9", "item10"]

# ✅ Better - split array
very-long-array = [
    "item1", "item2", "item3",
    "item4", "item5", "item6",
    "item7", "item8", "item9",
    "item10",
]
```

#### 8. Table Ordering

**Top-level table order:** Tables SHOULD follow a logical order:

1. `[build-system]` (if present)
2. `[package]` or `[project]` (package metadata)
3. `[dependencies]` / `[project.dependencies]`
4. `[tool.*]` tables (tool-specific configuration)

**Rationale:** Puts the most important metadata first, makes files easier to navigate.

```toml
# ✅ Correct order
[build-system]
requires = ["setuptools>=61.0"]

[project]
name = "repo_lint"
version = "0.1.0"

[project.dependencies]
click = ">=8.0"

[tool.black]
line-length = 120

# ❌ Wrong order - tool config before project metadata
[tool.black]
line-length = 120

[project]
name = "repo_lint"
```

---

## Taplo Configuration

The `.taplo.toml` configuration file (or `taplo.toml`) at the repository root defines these rules for `taplo fmt` and `taplo lint`.

**Key settings:**

```toml
# Formatting rules
[formatting]
indent_tables = true
indent_entries = true
indent_string = "  "  # 2 spaces
trailing_newline = true
allowed_blank_lines = 1
column_width = 120
compact_arrays = false
compact_inline_tables = false
```

**Rule enforcement:**

- `taplo fmt` - Auto-formats TOML files according to rules
- `taplo lint` - Checks TOML files for violations

---

## Enforcement

### Via repo-lint

TOML files are checked automatically as part of `repo-lint check --ci`:

```bash
# Check all TOML files
repo-lint check --lang toml

# Auto-fix TOML formatting
repo-lint fix --lang toml

# Check only TOML (skip other languages)
repo-lint check --only toml
```

### Via Taplo directly

You can also use Taplo directly:

```bash
# Check TOML files
taplo lint **/*.toml

# Format TOML files
taplo fmt **/*.toml
```

---

## Examples

### Good Example (pyproject.toml excerpt)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "repo_lint"
version = "0.1.0"
description = "Unified multi-language lint and docstring validation tool"
requires-python = ">=3.8"
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=10.0",
    "rich-click>=1.6.0",
]

[project.scripts]
repo-lint = "tools.repo_lint.cli:main"

[tool.black]
line-length = 120
target-version = ['py38']
```

### Bad Example (violations)

```toml
[build-system]
requires= ["setuptools>=61.0","wheel"]  # ❌ No spaces around =, no spacing in array
build-backend="setuptools.build_meta"  # ❌ No space around =
[project]  # ❌ No blank line before table
name = 'repo_lint'  # ❌ Single quotes
version = "0.1.0"
	description = "Tool"  # ❌ Tab instead of spaces
dependencies=["PyYAML>=6.0", "click>=8.0", "rich>=10.0", "rich-click>=1.6.0"]  # ❌ Long inline array, no spaces
[project.scripts]  # ❌ No blank line
repo-lint = "tools.repo_lint.cli:main"
[tool.black]  # ❌ No blank line
line-length=120  # ❌ No spaces around =
```

---

## Migration Guide

For existing TOML files that don't conform to these rules:

1. **Auto-fix first:** Run `taplo fmt **/*.toml` to auto-format all files
2. **Review changes:** Use `git diff` to review all changes before committing
3. **Manual fixes:** Address any remaining issues `taplo lint` reports
4. **Commit:** Commit the formatted files

**Important:** Always review auto-formatted changes before committing, especially for critical configuration files like `Cargo.toml` and `pyproject.toml`.

---

## References

- [TOML v1.0.0 Specification](https://toml.io/en/v1.0.0)
- [Taplo Documentation](https://taplo.tamasfe.dev/)
- [Cargo Manifest Format](https://doc.rust-lang.org/cargo/reference/manifest.html)
- Repository Markdown Contracts: `docs/contributing/markdown-contracts.md` (similar structure)

---

## Change Log

- **2026-01-08:** Initial version (Phase 3.6.1 - Issue #278)
