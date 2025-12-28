# Future Semantic Validation Plans

**Purpose:** Outline potential enhancements for deeper semantic validation of docstrings.

**Version:** 1.0  
**Last Updated:** 2025-12-28  
**Status:** Planning / Not Yet Implemented

## Overview

The current validator (v1.1) performs lightweight structural validation:
- Presence of required sections
- Basic content checks for exit codes (0 and 1 documented)
- Shebang validation for scripts

This document outlines potential future enhancements for deeper semantic validation.

## Proposed Enhancements

### 1. Parameter/Argument Matching

**Goal:** Ensure documented parameters match actual code parameters.

#### Bash
- Parse function definitions and check documented INPUTS match parameters
- Validate getopts options are documented
- Example: If script has `getopts "abc:"`, verify `-a`, `-b`, `-c` are documented

#### Python
- Parse function signatures and check docstring parameters match
- Validate argparse arguments are documented
- Use AST parsing to extract function parameters
- Example: If function has `def foo(bar, baz):`, verify `bar` and `baz` in docstring

#### PowerShell
- Parse `param()` blocks and check `.PARAMETER` sections match
- Validate mandatory vs optional parameter documentation
- Example: If `param([string]$Name)`, verify `.PARAMETER Name` exists

#### Rust
- Parse function signatures in `main.rs` and check documentation
- Validate clap/structopt arguments are documented
- Example: If using `#[clap(short, long)]`, verify in examples

### 2. Type Hint Validation

**Goal:** Ensure documented types match actual type hints/annotations.

#### Python
- Extract type hints from function signatures
- Compare with documented types in docstrings
- Example: `def foo(x: int) -> str:` should document `x` as `int` and return as `str`

#### Rust
- Extract types from function signatures
- Validate documented types match Rust type system
- Example: `fn foo(x: u32) -> String` should document accordingly

### 3. Exit Code Completeness

**Goal:** Stricter validation of exit code documentation.

**Current:** Checks for at least exit codes 0 and 1  
**Enhanced:**
- Require specific exit codes mentioned in the code to be documented
- Parse `exit N` statements and verify N is documented
- Validate exit code ranges (e.g., 128+ for signals)
- Check for documented but unused exit codes

#### Implementation Ideas
- AST parsing for Python: `sys.exit(N)`
- Regex for Bash: `exit N`
- Rust: `process::exit(N)` or `ExitCode::from(N)`

### 4. Example Code Validation

**Goal:** Ensure documented examples are syntactically valid and runnable.

**Approaches:**
- Extract code blocks from examples
- Run syntax validation (but not execution)
- Bash: `bash -n` for syntax check
- Python: `ast.parse()` for syntax check
- PowerShell: `Get-Command -Syntax` validation

### 5. Cross-Reference Validation

**Goal:** Validate links and references within documentation.

**Checks:**
- Verify file paths referenced actually exist
- Check intra-doc links (Perl `L<>`, Markdown links)
- Validate URLs are reachable (optional, can be slow)
- Ensure referenced sections exist

### 6. Consistency Checks

**Goal:** Ensure consistency within a single docstring.

**Checks:**
- If script uses environment variables in code, they're documented
- If script creates files, side effects are documented
- Parameter count matches between synopsis and detailed sections
- Example commands use correct script name

### 7. Style and Formatting

**Goal:** Enforce consistent style within docstrings.

**Checks:**
- Line length limits (80 chars for Bash, 72 for Python docstrings)
- Consistent indentation
- Proper capitalization of section headers
- Consistent use of punctuation

## Implementation Strategy

### Phase 1: Parser Infrastructure
1. Add AST parsing for Python
2. Add basic parsing for Bash (variables, functions, exit calls)
3. Add PowerShell param block parsing
4. Add Rust function signature parsing

### Phase 2: Incremental Validation
1. Start with least invasive checks (parameter count)
2. Add warnings (non-blocking) before making checks required
3. Provide detailed fix suggestions in error messages

### Phase 3: Configuration and Pragmas
1. Add configuration file for validation levels
2. Extend pragma system: `# noqa: PARAM_MATCH`, `# noqa: TYPE_HINT`
3. Allow per-project customization

### Phase 4: IDE Integration
1. Provide LSP (Language Server Protocol) integration
2. Real-time validation in editors
3. Auto-fix suggestions

## Considerations

### Performance
- Deeper validation will be slower
- Consider caching results
- Allow parallel validation
- Make expensive checks optional

### Backward Compatibility
- New checks should not break existing valid docstrings
- Use opt-in flags for strict validation
- Provide migration guides

### Maintenance
- Keep validators simple and maintainable
- Document validation rules clearly
- Provide test coverage for validators

## Non-Goals

- **Not a full linter replacement:** Use shellcheck, pylint, etc. for code quality
- **Not a runtime validator:** We validate documentation, not behavior
- **Not a formatter:** Use black, shfmt, etc. for code formatting

## References

- PEP 257: Python Docstring Conventions
- Google Python Style Guide: Docstrings
- Rust API Guidelines: Documentation
- PowerShell Comment-Based Help
- shellcheck: Bash linting tool (inspiration for validation patterns)

## Next Steps

1. Gather feedback from repository maintainers
2. Prioritize which enhancements provide most value
3. Create proof-of-concept for parameter matching
4. Assess performance impact of deeper validation
5. Update validator incrementally with new checks

## Conclusion

These enhancements would make docstring validation much more robust, catching more
documentation drift and errors. However, they should be implemented carefully to
avoid false positives and maintain validator performance.

The goal is to make documentation so accurate and consistent that it becomes
a reliable source of truth for both humans and AI agents.
