# Docstring Contracts

**Purpose:** Define clear, testable, and enforceable documentation standards for all scripts and configuration files in this repository.

## Why Docstring Contracts?

This repository is built around **contracts**: clear, testable requirements that prevent drift across languages and reduce ambiguity for humans and AI coding agents.

Docstring contracts ensure:
- **Consistency**: All scripts share the same conceptual documentation structure
- **Discoverability**: Users and agents can quickly understand what a script does, how to use it, and what to expect
- **Cross-language alignment**: Multi-language implementations remain aligned on semantics
- **Agent-friendliness**: Agents have a single source of truth for documentation patterns

## Enforcement

**ALL scripts in this repository MUST conform to their language's docstring contract**, regardless of location. Conformance is validated by CI via `.github/workflows/docstring-contract.yml`, which runs `scripts/validate-docstrings.py` on every PR.

The validator scans the entire repository for script files (`.sh`, `.ps1`, `.py`, `.pl`, `.pm`, `.rs`, `.yml`, `.yaml`) and validates each one against its language contract. This ensures that any new script added anywhere in the repository will be checked.

**Violations fail the build** until corrected.

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

## Required Semantic Sections (All Languages)

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

This means **any new script added anywhere in the repository** will be validated against its language's docstring contract.

## Validator

The validator (`scripts/validate-docstrings.py`) performs lightweight checks:
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
5. Run `python3 scripts/validate-docstrings.py` locally
6. Commit when validation passes

## CI Integration

The workflow `.github/workflows/docstring-contract.yml` runs on:
- Pull requests (affecting scripts, docs, contracts, or the validator)
- Pushes to `main`
- Manual dispatch

**Exit behavior:**
- Exit 0: All files conform
- Exit non-zero: Violations detected (see logs for details)

## References

- RFC-Shared-Agent-Scaffolding-v0.1.0.md (contract specification)
- [Conformance Contract](../conformance-contract.md)
- [Wrapper Discovery](../wrapper-discovery.md)
