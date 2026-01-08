# JSON/JSONC Docstring Contracts

**Status:** Canonical source of truth for JSON/JSONC documentation requirements  
**Last Updated:** 2026-01-08  
**Enforcement:** Part of `repo-lint check --ci` (docstring validation)

## Overview

This document defines documentation requirements for JSON and JSONC files in the RFC-Shared-Agent-Scaffolding
repository.

**Key Distinction:**
- **JSON (`.json`)**: Standard JSON does NOT support comments per RFC 8259 specification
- **JSONC (`.jsonc`)**: JSON with Comments - supports `//` and `/* */` style comments

---

## JSON Files (`.json`)

### Documentation Requirements

**File-level documentation:** NOT possible via comments in strict JSON (comments forbidden by RFC 8259 spec)

**MANDATORY Self-Documentation Fields:**

Since JSON cannot contain comments, ALL `.json` files MUST include metadata fields for self-documentation.

**Required Fields (at minimum ONE of the following):**

1. **`"$schema"`** (RECOMMENDED): URL to JSON Schema definition
   - Provides machine-readable documentation
   - Enables validation and IDE autocomplete
   - Example: `"$schema": "https://json.schemastore.org/prettierrc.json"`

2. **`"description"`** (REQUIRED if no `$schema`): Human-readable description of file purpose
   - Brief summary of what the file configures/defines
   - Example: `"description": "Prettier formatting configuration for repository"`

**Optional But Recommended:**

- `"name"`: Identifier for the configuration (useful for configs)
- `"version"`: Version information for the configuration
- `"title"`: Alternative to "description" (some schemas use "title" instead)

**Minimum Requirement:** EVERY `.json` file MUST have EITHER `$schema` OR `description` at the root level.

**Example: Self-documenting JSON with $schema**

```json
{
  "$schema": "https://json.schemastore.org/prettierrc.json",
  "printWidth": 120,
  "tabWidth": 2
}
```

**Example: Self-documenting JSON with description**

```json
{
  "description": "Production environment configuration for service XYZ",
  "name": "production-config",
  "version": "1.0.0",
  "settings": {
    "timeout": 3000,
    "retries": 3
  }
}
```

### Validation

`.json` files ARE validated for required metadata fields by the JSON runner.

**Enforcement:**
- JSON runner checks for presence of `$schema` OR `description` field at root level
- Files without either field will fail validation
- Pragma exemptions available: Add `// noqa: JSON_METADATA` comment in nearby JSONC or README

**Validation focus:**
- Metadata field presence (via JSON runner custom validator)
- Schema validation (if `$schema` provided)
- Format validation (via Prettier)
- Structural validation (valid JSON syntax)

---

## JSONC Files (`.jsonc`)

### Documentation Requirements

JSONC files support comments and MUST include file-level documentation.

### Required File-Level Header

All `.jsonc` files MUST begin with a header comment block containing:

1. **Purpose:** Brief description of what the file configures/defines
2. **Schema/Format:** Reference to format or schema (if applicable)
3. **Last Updated:** Date of last significant change
4. **Notes:** Important constraints, dependencies, or warnings (if applicable)

**Format:** Use single-line (`//`) or multi-line (`/* */`) comments at the top of the file

### Minimal Required Sections

**MANDATORY:**
- Purpose/Description

**RECOMMENDED:**
- Schema reference (if applicable)
- Last updated date
- Usage notes

**OPTIONAL:**
- Author/Maintainer
- Related documentation links
- Version information

---

## JSONC Header Format Examples

### Example 1: Configuration File Header

```jsonc
// Purpose: Markdown linting configuration for markdownlint-cli2
// Schema: https://github.com/DavidAnson/markdownlint-cli2#configuration
// Last Updated: 2026-01-08
//
// This configuration enforces markdown standards across the repository.
// See docs/contributing/markdown-contracts.md for detailed rules.

{
  "config": {
    "default": true,
    "MD013": {
      "line_length": 120
    }
  }
}
```

### Example 2: Multi-line Comment Header

```jsonc
/*
 * Purpose: TypeScript compiler configuration for the project
 * Schema: https://www.typescriptlang.org/tsconfig
 * Last Updated: 2026-01-08
 *
 * This file configures the TypeScript compiler options.
 * Do not modify without reviewing impact on build process.
 */
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs"
  }
}
```

### Example 3: Minimal Valid Header

```jsonc
// Purpose: VS Code workspace settings for this repository
{
  "editor.formatOnSave": true,
  "files.insertFinalNewline": true
}
```

---

## Inline Documentation (JSONC)

### Property Documentation

For complex configurations, add inline comments to explain non-obvious settings:

```jsonc
{
  "timeout": 3000, // Connection timeout in milliseconds

  // Retry policy: exponential backoff with max 5 attempts
  "retries": {
    "maxAttempts": 5,
    "backoffMultiplier": 2,
    "initialDelay": 100
  }
}
```

### Section Comments

Group related settings with section comments:

```jsonc
{
  // === Network Configuration ===
  "host": "localhost",
  "port": 8080,
  "timeout": 30000,

  // === Security Settings ===
  "enableSSL": true,
  "certificatePath": "/path/to/cert.pem"
}
```

---

## Comment Style Guidelines

### Good Comment Practices

**DO:**
- Explain WHY a setting has a particular value
- Document non-obvious constraints or dependencies
- Reference related documentation or issues
- Warn about breaking changes or deprecated features

**DON'T:**
- State the obvious ("timeout is timeout")
- Duplicate information already in property names
- Include outdated comments (remove or update)
- Use comments for debugging/TODO items (use proper issue tracking)

### Comment Examples

```jsonc
// ✅ Good - Explains WHY
{
  // Increased from 100 to 500 to handle slow CI environments (Issue #123)
  "slowTestTimeout": 500
}

// ❌ Bad - States the obvious
{
  // This is the timeout value
  "timeout": 3000
}

// ✅ Good - Documents constraint
{
  // Must match the value in backend/config.json to avoid auth failures
  "apiVersion": "v2"
}

// ❌ Bad - TODO in production config
{
  // TODO: fix this later
  "hackValue": 42
}
```

---

## Validation Rules

### Automated Checks

The JSONC docstring validator checks for:

1. **File-level header present:** At least one comment block at the start of the file
2. **Purpose documented:** Header contains purpose/description information
3. **Comment placement:** File-level comments appear before the first JSON structure

### Validation Errors

**Error: Missing file-level documentation**
```jsonc
// ❌ Invalid - No header comment
{
  "config": "value"
}
```

**Fix:**
```jsonc
// ✅ Valid - Header added
// Purpose: Application configuration
{
  "config": "value"
}
```

---

## Exemptions and Pragmas

### Pragma Support

Use `// noqa: DOCUMENTATION` to exempt a file from documentation requirements:

```jsonc
// noqa: DOCUMENTATION
{
  "test": "fixture"
}
```

**When to use exemptions:**
- Test fixtures that are intentionally minimal
- Auto-generated files (document the generator instead)
- Temporary/experimental configurations

**Important:** Exemptions MUST have a clear reason and should be time-bounded.

---

## Migration Guide

### Adding Documentation to Existing JSONC Files

1. **Identify purpose:** Understand what the file configures
2. **Check for schema:** See if there's a JSON Schema or format documentation
3. **Add minimal header:** Start with just Purpose
4. **Enhance gradually:** Add Schema, Notes, etc. as needed
5. **Review inline comments:** Remove outdated comments, add helpful ones

### Converting JSON to JSONC

**When to convert:**
- File would benefit from comments (complex configuration)
- File is hand-edited regularly
- Documentation would prevent common mistakes

**When NOT to convert:**
- Auto-generated files (lock files, build outputs)
- Files consumed by tools that don't support JSONC
- Simple files where structure is self-explanatory

**Conversion steps:**
1. Rename `.json` to `.jsonc`
2. Add file-level header comment
3. Update tooling to recognize `.jsonc` extension
4. Add inline comments for complex sections
5. Update `.gitattributes` if needed for language detection

---

## Directory-Specific Guidelines

### Configuration Directories

Files in config directories (`.vscode/`, `.github/`, etc.) should document:
- What the configuration affects
- When to modify vs. when to leave as-is
- Links to official documentation

### Test Fixtures

Test fixture JSONC files should document:
- What test case/scenario the fixture represents
- Expected behavior when used
- Any special properties or edge cases

### Conformance Vectors

Conformance test vectors should document:
- Test vector purpose (what's being tested)
- Expected validation result
- Related specification section

---

## Tooling Integration

### Editor Support

Most modern editors support JSONC:
- **VS Code:** Native support (auto-detected)
- **IntelliJ/WebStorm:** Supports comments in JSON files
- **Vim/Neovim:** Use `jsonc` filetype

### Linting

JSONC files are validated for:
1. **Format:** Via Prettier (ensures consistent style)
2. **Documentation:** Via custom docstring validator
3. **Schema:** Via JSON Schema validators (if schema defined)

---

## Examples

### Complete Example: `.vscode/settings.json` (renamed to `.jsonc`)

```jsonc
/*
 * Purpose: VS Code workspace settings for RFC-Shared-Agent-Scaffolding
 * Last Updated: 2026-01-08
 *
 * These settings ensure consistent editor behavior across all contributors.
 * See .editorconfig for language-agnostic editor settings.
 */
{
  // === Editor Behavior ===
  "editor.formatOnSave": true,
  "editor.rulers": [120], // Match repo line-length standard

  // === File Handling ===
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,

  // === Python Settings ===
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",

  // === Markdown Settings ===
  "[markdown]": {
    "editor.wordWrap": "on",
    "editor.quickSuggestions": false,
  },
}
```

---

## Compliance Checklist

Before committing JSONC files:

- [ ] File has header comment with Purpose
- [ ] Header includes Last Updated date (if recommended)
- [ ] Complex settings have inline comments explaining WHY
- [ ] No obvious/redundant comments
- [ ] No TODO/FIXME comments (use issue tracker)
- [ ] Comments follow style guidelines (explain WHY not WHAT)
- [ ] File passes `repo-lint check --ci`

---

## References

- [JSON Specification (RFC 8259)](https://datatracker.ietf.org/doc/html/rfc8259) - Why JSON forbids comments
- [JSON5 Specification](https://json5.org/) - Extended JSON format with comments
- [JSONC Format](https://code.visualstudio.com/docs/languages/json#_json-with-comments) - VS Code documentation
- [Google JSON Style Guide](https://google.github.io/styleguide/jsoncstyleguide.xml) - JSON formatting best practices

---

## Version History

- **2026-01-08:** Initial version (Phase 3.9 of Issue #278)
  - Established JSONC docstring requirements
  - Defined file-level header format
  - Inline comment guidelines
  - Exemption/pragma support
