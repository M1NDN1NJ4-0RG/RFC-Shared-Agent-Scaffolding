# Docstring Contracts

**Version:** 1.2 **Last Updated:** 2025-12-29 **Purpose:** Define clear, testable, and enforceable documentation
standards for all scripts, configuration files, and code symbols in this repository.

## Why Docstring Contracts

This repository is built around **contracts**: clear, testable requirements that prevent drift across languages and
reduce ambiguity for humans and AI coding agents.

Docstring contracts ensure:

- **Consistency**: All scripts share the same conceptual documentation structure
- **Discoverability**: Users and agents can quickly understand what a script does, how to use it, and what to expect
- **Cross-language alignment**: Multi-language implementations remain aligned on semantics
- **Agent-friendliness**: Agents have a single source of truth for documentation patterns

## Enforcement

**ALL scripts and code symbols in this repository MUST conform to their language's docstring contract**, regardless of location. Conformance is validated by CI via `.github/workflows/docstring-contract.yml`, which runs `scripts/validate_docstrings.py` on every PR.

### Current Enforcement (Phase 5.5)

The validator scans:

1. **File/module-level documentation** - All script files (`.sh`, `.ps1`, `.py`, `.pl`, `.pm`, `.rs`, `.yml`, `.yaml`)
2. **Symbol-level documentation** - All public/exported functions, classes, methods, and subs (Phase 5.5+)

### Enforcement Scope

- **File/module docs:** REQUIRED for all script files
- **Symbol docs:** REQUIRED for all public/exported symbols (functions, classes, methods, subs)
- **Private symbol docs:** RECOMMENDED but not enforced initially

**Violations fail the build** until corrected.

## Contract Version History

### Version 1.2 (2025-12-29) - Phase 5.5

- **Added symbol-level documentation contracts** (symbol-level-contracts.md)
  - Defined requirements for functions, classes, methods across all languages
  - Established enforcement scope (public/exported symbols minimum)
  - Created templates and examples for Python, Bash, Perl, PowerShell, Rust
  - Added pragma/exemption support for symbol-level documentation
- Updated Perl script naming convention from kebab-case to snake_case
- Aligned test runner naming across languages

### Version 1.1 (2025-12-28)

- Added comprehensive exit-codes-contract.md shared reference
- Enhanced validator with pragma support (`# noqa: EXITCODES`)
- Added basic content validation for exit codes
- Added single-file validation mode (`--file` flag)
- Added semantic section mapping table
- Added "How to Extend Contracts" guide
- Added "Prompting Tips for AI Tools" section
- Harmonized all language contracts with consistent templates
- Added Platform Compatibility as optional section across all contracts
- Clarified Triggers vs Usage for YAML files
- Made Permissions required for GitHub Actions workflows

### Version 1.0 (Initial)

- Initial docstring contract system
- Basic validation for presence of required sections
- Language-specific contracts for Bash, PowerShell, Python, Perl, Rust, YAML

## Language Contracts

Each language has its own contract document that specifies:

- **Required semantic sections** (what concepts must be documented)
- **Language-specific formatting rules** (how to express those concepts idiomatically)
- **Templates** (copy/paste starting points)
- **Examples** (real files in this repo that follow the contract)

| Language | Extensions | Contract Document |
|----------|------------|-------------------|
| Bash | `.sh`, `.bash`, `.zsh` | [bash.md](./bash.md) |
| PowerShell | `.ps1` | [powershell.md](./powershell.md) |
| Python 3 | `.py` | [python.md](./python.md) |
| Perl | `.pl`, `.pm`, `.t` | [perl.md](./perl.md) |
| Rust | `.rs` | [rust.md](./rust.md) |
| YAML | `.yml`, `.yaml` | [yaml.md](./yaml.md) |

### Future Contracts (DRAFT)

These contracts are preliminary and **not yet enforced by the validator**. Use them as guidance if adding these
languages to the repository, but expect refinement before official adoption.

| Language | Extensions | Contract Document | Status |
|----------|------------|-------------------|--------|
| JavaScript/Node.js | `.js`, `.mjs` | [javascript.md](./javascript.md) | DRAFT |
| C | `.c`, `.h` | [c.md](./c.md) | DRAFT |
| C++ | `.cpp`, `.hpp`, `.cc`, `.hh`, `.cxx` | [cpp.md](./cpp.md) | DRAFT |
| C# | `.cs` | [csharp.md](./csharp.md) | DRAFT |
| Ruby | `.rb` | [ruby.md](./ruby.md) | DRAFT |
| TypeScript | `.ts`, `.tsx` | [typescript.md](./typescript.md) | DRAFT |

### Esoteric / Satirical Contracts (UNOFFICIAL)

These contracts exist for entertainment, educational, or satirical purposes. **Do not use these languages in this
repository.**

| Language | Extensions | Contract Document | Status | Warning Level |
|----------|------------|-------------------|--------|---------------|
| Malbolge | `.mb`, `.malbolge` | [malbolge.md](./malbolge.md) | EXPERIMENTAL | ⚠️⚠️⚠️ EXISTENTIAL DREAD |

**Note:** The Malbolge contract demonstrates that even the most absurd and impractical languages can theoretically
follow documentation standards. It serves as a reminder to appreciate readable, maintainable code.

## Required Semantic Sections (All Languages)

### File/Module-Level Documentation

Every script's documentation must cover these concepts (using idiomatic section names):

1. **Name / one-line summary** - What is this script called and what does it do?
2. **Description / behavior** - What it does and what it does NOT do
3. **Usage** - How to invoke it (invocation pattern)
4. **Arguments / parameters** - What inputs it accepts (if applicable)
5. **Environment variables** - What environment configuration it uses (if applicable)
6. **Exit codes** - At least: 0 = success, non-zero = failure types
7. **Examples** - Minimum 1 concrete usage example
8. **Notes for maintainers** - Constraints, invariants, sharp edges

> Language contracts may add optional sections, but the above are required.

### Symbol-Level Documentation

Every function, class, method, and subroutine must be documented. See
**[symbol-level-contracts.md](./symbol-level-contracts.md)** for detailed requirements per language.

**Minimum requirements:**

- Functions/methods: Purpose, parameters, return value
- Classes/structs: Purpose, attributes/fields
- Public APIs: Full documentation including examples

**Phase 5.5 enforcement:** Public/exported symbols only. Private helper documentation recommended but not required
initially.

## Semantic Section to Language Keyword Mapping

This table maps the required semantic concepts to their language-specific keywords. Use this when writing documentation
or prompting AI tools.

| Semantic Concept | Bash | PowerShell | Python | Perl | Rust | YAML |
|-----------------|------|------------|--------|------|------|------|
| **Name/Summary** | `# script.sh - Summary` | `.SYNOPSIS` | First line of `"""` | `=head1 NAME` | `//! # Title` | `# Workflow:` or `# File:` |
| **Description** | `DESCRIPTION:` | `.DESCRIPTION` | First paragraph or `Purpose` section | `=head1 DESCRIPTION` | `//! # Purpose` | `# Purpose:` |
| **Usage** | `USAGE:` | `.SYNOPSIS` or `.EXAMPLE` | `CLI Interface` or `Usage` section | `=head1 SYNOPSIS` | `//! # Examples` (with bash blocks) | `# Triggers:` or `# Usage:` |
| **Arguments** | `INPUTS:` → Arguments | `.PARAMETER` | Function docstrings or `CLI Interface` | `=head1 OPTIONS` | `///` on structs/args | N/A (in YAML structure) |
| **Environment** | `INPUTS:` → Environment Variables | `.ENVIRONMENT` | `Environment Variables` section | `=head1 ENVIRONMENT VARIABLES` | Document in `# Purpose` or notes | `# Dependencies:` |
| **Exit Codes** | `OUTPUTS:` → Exit Codes | `.DESCRIPTION` or `.NOTES` → Exit Codes | `Exit Codes` section | `=head1 EXIT CODES` | `//! # Exit Behavior` or `//! # Exit Codes` | `# Notes:` → Exit codes |
| **Examples** | `EXAMPLES:` | `.EXAMPLE` | `Examples` section | `=head1 EXAMPLES` | `//! # Examples` | Example usage in `# Triggers:` |
| **Notes** | `NOTES:` | `.NOTES` | `Notes` section | `=head1 NOTES` | `//! # Contract References` or notes | `# Notes:` |

**Key observations:**

- Exit codes have different homes in different languages (dedicated section in most, embedded in description for
  PowerShell/YAML)
- Usage is sometimes combined with examples (Rust, PowerShell)
- Environment variables may be grouped with other inputs (Bash) or separate (most languages)

Refer to the [exit-codes-contract.md](./exit-codes-contract.md) for canonical exit code meanings across all languages.

## YAML Contract (Special Case)

YAML files don't have formal docstrings, but use **top-of-file comment headers** as their documentation contract.

GitHub Actions workflows and other YAML configs must include:

- **Workflow / File name**
- **Purpose**
- **Usage / Triggers**
- **Inputs / Dependencies**
- **Outputs / Side effects**
- **Notes for maintainers**

See [yaml.md](./yaml.md) for details.

## Scope

The validator enforces contracts on **ALL scripts repository-wide**:

- **All Bash scripts**: `**/*.sh`, `**/*.bash`, `**/*.zsh`
- **All PowerShell scripts**: `**/*.ps1`
- **All Python scripts**: `**/*.py`
- **All Perl scripts**: `**/*.pl`, `**/*.pm`
- **All Rust source files**: `rust/src/**/*.rs`
- **All YAML workflows**: `.github/workflows/*.yml`, `.github/workflows/*.yaml`
- **All YAML issue templates**: `.github/ISSUE_TEMPLATE/*.yml`, `.github/ISSUE_TEMPLATE/*.yaml`

**Exclusions**: Build artifacts (`dist/`, `target/`), dependencies (`node_modules/`), and Rust test files (`rust/tests/`) are excluded from validation.

This means **any new script added anywhere in the repository** will be validated against its language's docstring
contract.

## Validator

The validator (`scripts/validate_docstrings.py`) performs lightweight checks:

- **Presence** of a docstring/comment block near the top of file
- **Presence** of required semantic sections (regex-based)

It does **not** validate:

- Content quality or accuracy
- Deep grammar or formatting
- Runtime behavior

**Actionable errors:** When validation fails, the validator prints:

- File path
- Which section(s) are missing
- What was expected (short snippet)

## Quick Start (for script authors)

1. Choose your language from the table above
2. Open the contract document (e.g., `bash.md`)
3. Copy the template
4. Fill in the required sections
5. Run `python3 scripts/validate_docstrings.py` locally
6. Commit when validation passes

## CI Integration

The workflow `.github/workflows/docstring-contract.yml` runs on:

- Pull requests (affecting scripts, docs, contracts, or the validator)
- Pushes to `main`
- Manual dispatch

**Exit behavior:**

- Exit 0: All files conform
- Exit non-zero: Violations detected (see logs for details)

## How to Extend Contracts (Adding New Languages)

To add a new language to the docstring contract system:

### 1. Create the Contract Document

Create a new file `docs/contributing/docstring-contracts/<language>.md` with the following structure:

- **Language name and file extensions**
- **Purpose** - Why this language needs documentation standards
- **Required Semantic Sections** - Map the 8 core concepts to language-specific keywords
- **Formatting Rules** - Language-specific syntax and conventions
- **Templates** - Minimal and full templates developers can copy
- **Examples** - Reference existing files in the repo
- **Validation** - What the validator checks (and doesn't check)
- **Common Mistakes** - Anti-patterns with ❌/✅ examples
- **References** - Links to language documentation standards

### 2. Update the Validator

Edit `scripts/validate_docstrings.py`:

```python
# Add file extension patterns to IN_SCOPE_PATTERNS
IN_SCOPE_PATTERNS = [
    # ... existing patterns ...
    "**/*.ext",  # Your new language extension
]

# Create a validator class
class NewLanguageValidator:
    """Validates NewLanguage docstrings."""
    
    REQUIRED_SECTIONS = [
        r"pattern for section 1",
        r"pattern for section 2",
        # ... map to required semantic sections
    ]
    
    SECTION_NAMES = ["Section1", "Section2", ...]
    
    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate NewLanguage docstring."""
        # Check for docstring presence
        # Check for required sections
        # Return ValidationError if missing, None if valid
        pass

# Update validate_file() function
def validate_file(file_path: Path) -> Optional[ValidationError]:
    # ... existing code ...
    elif suffix == ".ext":
        return NewLanguageValidator.validate(file_path, content)
```

### 3. Update This README

- Add language to the **Language Contracts** table
- Add language column to the **Semantic Section Mapping** table
- Update **Scope** section with new file patterns

### 4. Test the Integration

```bash
# Create a test file in the new language with violations
touch test-script.ext

# Run validator - should fail
python3 scripts/validate_docstrings.py

# Add proper docstring following your contract
# Run validator again - should pass
python3 scripts/validate_docstrings.py
```

### 5. Add CI Coverage

The existing `.github/workflows/docstring-contract.yml` will automatically pick up the new language if you've updated the validator correctly.

### 6. Document Validator Behavior

Add a note to your language contract document showing:

- What the validator checks for
- Example validation error messages
- How to run validation locally

## Prompting Tips for AI Tools (GitHub Copilot, etc.)

When using AI coding assistants, use these prompts to ensure contract compliance:

### General Prompt Pattern

```
Create a [language] script that [does X].
Follow the docstring contract in docs/contributing/docstring-contracts/[language].md.
Include all required sections: name, description, usage, arguments,
environment variables, exit codes, examples, and notes.
```

### Language-Specific Prompts

**For Bash scripts:**

```
Create a Bash script with proper M0 contract docstring.
Use the template from docs/contributing/docstring-contracts/bash.md.
Include shebang #!/usr/bin/env bash, DESCRIPTION, USAGE, INPUTS,
OUTPUTS with exit codes, EXAMPLES, and NOTES sections.
```

**For Python scripts:**

```
Create a Python 3 script with module docstring following
docs/contributing/docstring-contracts/python.md. Use triple quotes, include Purpose,
Environment Variables, CLI Interface, Examples, Exit Codes,
and Notes sections in reStructuredText style.
```

**For PowerShell scripts:**

```
Create a PowerShell script with comment-based help following
docs/contributing/docstring-contracts/powershell.md. Include .SYNOPSIS, .DESCRIPTION,
.ENVIRONMENT, .EXAMPLE, and .NOTES keywords. Document exit codes
in .DESCRIPTION.
```

**For Perl scripts:**

```
Create a Perl script with POD documentation following
docs/contributing/docstring-contracts/perl.md. Include =head1 NAME, SYNOPSIS, DESCRIPTION,
ENVIRONMENT VARIABLES, EXIT CODES, EXAMPLES, and NOTES sections.
End with =cut.
```

**For Rust code:**

```
Create a Rust module with rustdoc comments following
docs/contributing/docstring-contracts/rust.md. Use //! for module docs with # Purpose,
# Architecture, # Exit Behavior, # Contract References, and
# Examples sections.
```

**For YAML workflows:**

```
Create a GitHub Actions workflow with header documentation following
docs/contributing/docstring-contracts/yaml.md. Include Workflow, Purpose, Triggers,
Dependencies, Outputs, and Notes sections as comments at the top.
```

### Validation Prompts

After generating code:

```
Verify this [language] script conforms to docs/contributing/docstring-contracts/[language].md.
Check all required sections are present and properly formatted.
```

### Reference the Validator

```
This script must pass validation by scripts/validate_docstrings.py.
Ensure it includes all required docstring sections for [language].
See docs/contributing/docstring-contracts/[language].md for the contract.
```

### Common AI Prompting Mistakes

❌ **Too vague:** "Add documentation to this script"

- AI may use generic/incomplete documentation

✅ **Specific contract reference:** "Add Bash docstring following docs/contributing/docstring-contracts/bash.md with all
required sections"

❌ **Missing exit codes:** "Document this function"

- Exit codes often overlooked

✅ **Explicit exit codes:** "Document with exit codes: 0=success, 1=failure, 127=not found per exit-codes-contract.md"

❌ **No validation check:** Accepting AI output without verification

- May be incomplete or non-conformant

✅ **Request validation:** "Generate script and verify it passes scripts/validate_docstrings.py"

### Example: Full Copilot Workflow

1. **Generate with contract:**

   ```
   @workspace Create a Bash wrapper script for safe-run following
   docs/contributing/docstring-contracts/bash.md. Include binary discovery, all required
   docstring sections, and exit codes per exit-codes-contract.md.
   ```

2. **Validate:**

   ```
   @terminal Run python3 scripts/validate_docstrings.py on the new script
   ```

3. **Fix violations:**

   ```
   @workspace The validator reports missing OUTPUTS section.
   Add OUTPUTS with exit codes 0, 1, 127 per docs/contributing/docstring-contracts/bash.md.
   ```

4. **Verify examples:**

   ```
   @workspace Add 2 more examples to the EXAMPLES section showing
   environment variable overrides and error cases.
   ```

## References

- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- `scripts/validate_docstrings.py` - Validator implementation (see its docstring for meta-example)
- [rfc-shared-agent-scaffolding-v0.1.0.md](../../rfc-shared-agent-scaffolding-v0.1.0.md) - M0 contract specification
- [Conformance Contract](../../usage/conformance-contract.md) - Behavior contract
- [Wrapper Discovery](../../architecture/wrapper-discovery.md) - Binary discovery rules
