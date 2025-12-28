# Perl Docstring Contract

**Language:** Perl (`.pl`, `.pm`, `.t`)  
**Canonical style:** POD (Plain Old Documentation) using `=head1`, `=head2`, `=over`, `=item`

## Purpose

Perl scripts in this repository use **POD (Plain Old Documentation)** to document their purpose, usage, and behavior. POD is Perl's standard documentation format, compatible with `perldoc` and other documentation tools.

## Required Semantic Sections

Every Perl script must include these POD sections (using `=head1` headers):

1. **=head1 NAME** - Script name and one-line summary
2. **=head1 SYNOPSIS** - Usage examples (invocation patterns)
3. **=head1 DESCRIPTION** - What the script does and does NOT do
4. **=head1 BINARY DISCOVERY** or **=head1 ENVIRONMENT VARIABLES** - Configuration (for wrappers, use BINARY DISCOVERY; for others, use ENVIRONMENT VARIABLES if applicable)
5. **=head1 ENVIRONMENT VARIABLES** - Variables used and defaults (if not already covered)
6. **=head1 EXIT CODES** - At least: 0 = success, non-zero = failure types
7. **=head1 EXAMPLES** - Minimum 1 concrete usage example
8. **=head1 NOTES** or **=head1 CAVEATS** - Maintainer notes, constraints (optional but recommended)

### Optional Sections

- **=head1 OPTIONS** - Command-line options (if using Getopt)
- **=head1 PLATFORM** - Platform compatibility (OS, Perl version requirements) - **Recommended**
- **=head1 FILES** - Files read or written
- **=head1 DIAGNOSTICS** - Error messages explained
- **=head1 SEE ALSO** - References to related docs
- **=head1 AUTHOR** - Author information (if applicable)

## Formatting Rules

### Structure

```perl
#!/usr/bin/env perl

=head1 NAME

script-name.pl - One-line summary of what this script does

=head1 SYNOPSIS

  # Basic usage
  script-name.pl -- <command> [args...]
  
  # Optional leading "--" separator
  script-name.pl <command> [args...]
  
  # Examples
  script-name.pl -- echo "Hello, world!"
  script-name.pl perl my-script.pl

=head1 DESCRIPTION

This Perl script discovers and invokes the canonical implementation. It does
NOT reimplement any contract logic - it is purely a thin invoker that handles
binary discovery and argument pass-through.

The tool executes commands with enhanced logging. On success (exit code 0),
no artifacts are created. On failure (non-zero exit), a detailed log file is
written with complete stdout/stderr capture.

=head1 BINARY DISCOVERY

The wrapper searches for the canonical binary in the following order
(per docs/architecture/wrapper-discovery.md):

=over 4

=item 1. B<BINARY_PATH> environment variable

If set, uses this path without validation. Use for testing, CI overrides,
or custom installations.

=item 2. B<./rust/target/release/binary> (dev mode)

Relative to repository root. Use for local development and testing changes.

=item 3. B<./dist/E<lt>osE<gt>/E<lt>archE<gt>/binary> (CI artifacts)

Platform-specific paths:
  - Linux: ./dist/linux/x86_64/binary
  - macOS (Intel): ./dist/macos/x86_64/binary
  - macOS (ARM): ./dist/macos/aarch64/binary
  - Windows: ./dist/windows/x86_64/binary.exe

=item 4. B<PATH> lookup

Searches for 'binary' in system PATH (system-wide installation).

=item 5. B<Error with instructions> (exit 127)

If no binary is found, prints actionable error message with installation
instructions and exits with code 127 (command not found).

=back

=head1 ENVIRONMENT VARIABLES

=head2 Wrapper Control

=over 4

=item B<BINARY_PATH>

Override binary discovery. If set, this path is used without further searching.

Example:

  export BINARY_PATH=/custom/path/to/binary
  script-name.pl -- echo "test"

=back

=head2 Tool Configuration (Passed Through)

=over 4

=item B<LOG_DIR>

Directory for failure logs (default: .agent/FAIL-LOGS).
Passed through to the canonical tool.

=item B<SNIPPET_LINES>

Number of tail lines to print on failure (default: 0).
Set to 0 to disable snippet output. Passed through to canonical tool.

=back

=head1 EXIT CODES

The script forwards exit codes from the canonical tool:

=over 4

=item B<0>

Success - command executed successfully

=item B<1-255>

Failure - child process exit code (forwarded from canonical tool)

=item B<127>

Binary not found - canonical tool is not installed or discoverable

=back

=head1 EXAMPLES

=head2 Basic Usage

  # Execute a simple command
  script-name.pl -- echo "Hello, world!"
  
  # Without leading separator
  script-name.pl echo "test"

=head2 Environment Override

  # Override binary path
  export BINARY_PATH=/custom/path
  script-name.pl -- test-command
  
  # Set log directory
  export LOG_DIR=/tmp/logs
  script-name.pl -- failing-command

=head2 Complex Command

  # Multi-argument command
  script-name.pl -- perl -e 'print "Hello\n"'

=head1 NOTES

=over 4

=item *

Do not modify discovery order without updating docs/architecture/wrapper-discovery.md

=item *

Exit codes must match canonical tool behavior per conformance contract

=item *

Always preserve child process exit codes (0-255 range)

=back

=head1 SEE ALSO

L<docs/architecture/wrapper-discovery.md>, L<docs/usage/conformance-contract.md>

=cut

use strict;
use warnings;
use v5.10;

# Script implementation follows...
```

### Key Rules

1. **Shebang first**: Always start with `#!/usr/bin/env perl`
2. **POD placement**: POD can be anywhere, but conventionally at the top (after shebang)
3. **=cut required**: End POD block with `=cut` before code
4. **Headers**: Use `=head1` for major sections, `=head2` for subsections
5. **Lists**: Use `=over 4` / `=item` / `=back` for bulleted/numbered lists
6. **Bold**: Use `B<text>` for bold/emphasis
7. **Italic**: Use `I<text>` for italic/variables
8. **Code**: Use `C<code>` for inline code
9. **Escapes**: Use `E<lt>` for `<`, `E<gt>` for `>`
10. **Indentation**: Two spaces for code examples under sections
11. **Links**: Use `L<text|url>` for URLs, `L<Module::Name>` for modules, `L<perldoc>` for Perl docs
12. **File paths**: Use `F<path/to/file>` for file and directory names
13. **Section naming**: Use "NOTES" (not "CAVEATS") for consistency across contracts

### Intra-Document Links

POD supports linking to other documentation:

```perl
=head1 SEE ALSO

L<docs/architecture/wrapper-discovery.md> - Wrapper discovery rules

L<perlfunc> - Perl built-in functions reference

L<Module::Name> - Link to installed module documentation

L<https://example.com> - External URL

L<Exit Codes|exit-codes-contract.md> - Link with custom text
```

## Templates

### Minimal Template

```perl
#!/usr/bin/env perl

=head1 NAME

script-name.pl - One-line summary of what this script does

=head1 SYNOPSIS

  script-name.pl <command> [args...]

=head1 DESCRIPTION

Detailed description of behavior.

=head1 ENVIRONMENT VARIABLES

=over 4

=item B<ENV_VAR>

Description (default: value)

=back

=head1 EXIT CODES

=over 4

=item B<0>

Success

=item B<1>

Failure

=back

=head1 EXAMPLES

  # Basic usage
  script-name.pl echo "hello"

=head1 NOTES

=over 4

=item *

Important constraint or note for maintainers

=back

=cut

use strict;
use warnings;
use v5.10;

# Script implementation follows...
```

### Full Template (with optional sections)

```perl
#!/usr/bin/env perl

=head1 NAME

script-name.pl - One-line summary of what this script does

=head1 SYNOPSIS

  # Basic usage - execute a command with enhanced logging
  script-name.pl -- <command> [args...]
  
  # Optional leading "--" separator
  script-name.pl <command> [args...]
  
  # Examples
  script-name.pl -- echo "Hello, world!"
  script-name.pl perl my-script.pl
  script-name.pl npm test

=head1 DESCRIPTION

This Perl wrapper discovers and invokes the canonical implementation. It does
NOT reimplement any contract logic - it is purely a thin invoker that handles
binary discovery and argument pass-through.

Detailed behavior description. State what it does NOT do if relevant.

=head1 BINARY DISCOVERY

The wrapper searches for the canonical binary in the following order
(per docs/architecture/wrapper-discovery.md):

=over 4

=item 1. B<BINARY_PATH> environment variable

If set, uses this path without validation.

=item 2. B<./rust/target/release/binary> (dev mode)

Relative to repository root.

=item 3. B<./dist/E<lt>osE<gt>/E<lt>archE<gt>/binary> (CI artifacts)

Platform-specific paths.

=item 4. B<PATH> lookup

System-wide installation.

=item 5. B<Error with instructions> (exit 127)

If not found, prints error and exits.

=back

=head1 OPTIONS

=over 4

=item B<--help>

Display usage information.

=item B<--version>

Display version information.

=back

=head1 ENVIRONMENT VARIABLES

=head2 Wrapper Control

=over 4

=item B<BINARY_PATH>

Override binary discovery. If set, this path is used directly.

Example:

  export BINARY_PATH=/custom/path/to/binary
  script-name.pl -- echo "test"

=back

=head2 Tool Configuration (Passed Through)

=over 4

=item B<LOG_DIR>

Directory for failure logs (default: .agent/FAIL-LOGS).

=item B<SNIPPET_LINES>

Number of tail lines to print on failure (default: 0).

=item B<VIEW_MODE>

Output view format: split (default) | merged

=back

=head1 EXIT CODES

=over 4

=item B<0>

Success - command executed successfully

=item B<1-255>

Failure - child process exit code (forwarded)

=item B<127>

Binary not found

=back

=head1 EXAMPLES

=head2 Basic Usage

  # Execute a simple command
  script-name.pl -- echo "Hello, world!"
  
  # Without separator
  script-name.pl echo "test"

=head2 Environment Override

  # Override binary path
  export BINARY_PATH=/custom/path
  script-name.pl -- test-command

=head2 Complex Command

  # Multi-argument command
  script-name.pl -- perl -e 'print "Hello\n"'

=head1 FILES

=over 4

=item F<.agent/FAIL-LOGS/*.log>

Failure logs created by the canonical tool.

=back

=head1 DIAGNOSTICS

=over 4

=item C<Binary not found>

The canonical tool binary could not be located. Install it or set BINARY_PATH.

=back

=head1 NOTES

=over 4

=item *

Do not modify discovery order without updating docs

=item *

Exit codes must match canonical tool behavior

=item *

Always preserve child process exit codes

=back

=head1 AUTHOR

Repository: L<https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding>

=head1 SEE ALSO

L<docs/architecture/wrapper-discovery.md>, L<docs/usage/conformance-contract.md>

=cut

use strict;
use warnings;
use v5.10;

# Script implementation follows...
```

## Examples (Existing Files)

### Example 1: Wrapper Script
**File:** `wrappers/scripts/perl/scripts/safe-run.pl`

This file demonstrates:
- Full POD with all required sections
- BINARY DISCOVERY section with `=over`/`=item`/`=back`
- Multiple ENVIRONMENT VARIABLES subsections
- EXAMPLES with multiple subsections
- Proper use of `B<bold>`, `I<italic>`, `C<code>`

### Example 2: Test Module
**File:** `wrappers/scripts/perl/tests/lib/TestUtil.pm`

This file demonstrates:
- Module-level POD (for `.pm` files)
- SYNOPSIS with function usage
- FUNCTIONS section documenting each exported function
- NOTES section for module constraints

### Example 3: Utility Script
**File:** `wrappers/scripts/perl/scripts/safe-check.pl`

This file demonstrates:
- DESCRIPTION that states what it does NOT do
- OPTIONS section for command-line flags
- EXIT CODES with multiple failure modes
- FILES section documenting artifacts

## Validation

The validator checks for:
- Presence of POD block (between `=head1 NAME` and `=cut`)
- Presence of section headers: `=head1 NAME`, `=head1 SYNOPSIS`, `=head1 DESCRIPTION`, `=head1 ENVIRONMENT VARIABLES`, `=head1 EXIT CODES`, `=head1 EXAMPLES`
- At least one example under EXAMPLES section

The validator does NOT check:
- POD syntax perfection
- Formatting consistency
- Link validity
- Grammar or spelling

## Common Mistakes

❌ **Wrong:** Missing `=cut` at end of POD
```perl
=head1 NAME

script.pl - Summary

use strict;
```

✅ **Correct:** Always end POD with `=cut`
```perl
=head1 NAME

script.pl - Summary

=cut

use strict;
```

❌ **Wrong:** No EXIT CODES section
```perl
=head1 DESCRIPTION

Does something useful.

=head1 EXAMPLES

  script.pl test
```

✅ **Correct:** Always document exit codes
```perl
=head1 DESCRIPTION

Does something useful.

=head1 EXIT CODES

=over 4

=item B<0>

Success

=item B<1>

Failure

=back

=head1 EXAMPLES

  script.pl test
```

❌ **Wrong:** Using `<` and `>` directly
```perl
=head1 SYNOPSIS

  script.pl <command> [args...]
```

✅ **Correct:** Escape angle brackets in non-code context (or use as-is in code examples - POD is forgiving for indented code)
```perl
=head1 SYNOPSIS

  script.pl E<lt>commandE<gt> [args...]
  
  # Or in code examples (indented), use directly:
  script.pl <command> [args...]
```

Note: In practice, POD is forgiving in code examples (indented lines). Escaping is most important in regular paragraphs.

## POD Documentation Tools

Scripts following this contract are compatible with Perl's documentation tools:

```bash
# View POD as formatted text
perldoc script-name.pl

# Convert POD to HTML
pod2html script-name.pl > script-name.html

# Convert POD to plain text
pod2text script-name.pl

# Check POD syntax
podchecker script-name.pl
```

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [perlpod – Plain Old Documentation](https://perldoc.perl.org/perlpod)
- [perlpodstyle – POD Style Guide](https://perldoc.perl.org/perlpodstyle)
- [Wrapper Discovery](../../architecture/wrapper-discovery.md) - Binary discovery rules for wrappers
- [Conformance Contract](../../usage/conformance-contract.md) - Behavior contract
