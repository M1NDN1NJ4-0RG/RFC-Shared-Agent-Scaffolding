# Ruby Docstring Contract (DRAFT)

**Language:** Ruby (`.rb`)
**Canonical style:** RDoc or YARD documentation using `#` comments
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for Ruby scripts that may be added to this repository in the future. It follows YARD (preferred) and RDoc conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding Ruby files, but expect refinement before official adoption.

## Required Semantic Sections

Every Ruby script should include these sections in documentation comments:

1. **@!attribute** or file-level comment - Script/module description and one-line summary
2. **@description** or description paragraph - What it does and does NOT do
3. **@param** - Document each method parameter (if applicable)
4. **@return** - Return value documentation
5. **@raise** or **@raise [ExceptionType]** - Document exceptions that may be raised
6. **@example** - Minimum 1 concrete usage example
7. **@see** - References to related docs

### Optional Sections

- **@note** - Important notes, constraints, sharp edges
- **@deprecated** - Deprecation warnings
- **@since** - Version information
- **@version** - Version information
- **@author** - Author information
- **@platform** - Platform compatibility (Ruby version, OS) - **Recommended** (use @note)

## Formatting Rules

### File-Level Documentation (YARD style)

```ruby
#!/usr/bin/env ruby
# frozen_string_literal: true

# @file script.rb
# @author Repository contributors
#
# One-line summary of what this script does
#
# Detailed description of what the script does.
# Multiple paragraphs are allowed.
# State what it does NOT do if relevant.
#
# This script acts as a wrapper that discovers and executes the canonical tool.
#
# @note Platform: Ruby 3.0+, cross-platform (Linux/macOS/Windows)
#
# Exit Codes:
#   0 - Success - command executed successfully
#   1 - General failure
#   2 - Invalid arguments
#   127 - Binary not found
#
# @example Basic usage
#   ruby script.rb command arg1 arg2
#
# @example With environment override
#   BINARY_PATH=/custom/path ruby script.rb command
#
# @see exit-codes-contract.md

require 'pathname'
require 'open3'

# Main entry point
#
# @param args [Array<String>] Command-line arguments
# @return [Integer] Exit code (0 for success, non-zero for failure)
def main(args)
  # Implementation
  0
end

exit main(ARGV) if __FILE__ == $PROGRAM_NAME
```

### Class Documentation

```ruby
# Binary discovery and execution wrapper
#
# This class discovers and invokes the canonical implementation.
# It does NOT reimplement any contract logic.
#
# Binary Discovery Order:
#   1. BINARY_PATH environment variable
#   2. ./dist/<os>/<arch>/binary
#   3. PATH lookup
#
# @example Create and use wrapper
#   wrapper = BinaryWrapper.new('tool')
#   exit_code = wrapper.execute(['arg1', 'arg2'])
#
# @note This class is thread-safe for discovery operations
class BinaryWrapper
  # @return [String] Name of the binary to wrap
  attr_reader :binary_name

  # Initialize a new wrapper
  #
  # @param binary_name [String] Name of binary to wrap
  # @raise [ArgumentError] if binary_name is nil or empty
  def initialize(binary_name)
    raise ArgumentError, 'binary_name cannot be nil or empty' if binary_name.nil? || binary_name.empty?
    
    @binary_name = binary_name
    @cached_path = nil
  end

  # Find the binary path
  #
  # Searches for the binary in the following order:
  #   1. BINARY_PATH environment variable
  #   2. ./dist/<os>/<arch>/binary
  #   3. PATH lookup
  #
  # @return [Pathname] Path to binary
  # @raise [RuntimeError] if binary not found
  #
  # @example
  #   wrapper = BinaryWrapper.new('tool')
  #   path = wrapper.find_binary
  #   puts "Found: #{path}"
  def find_binary
    # Implementation
    Pathname.new('/usr/bin/tool')
  end

  # Execute command with arguments
  #
  # @param args [Array<String>] Command arguments
  # @return [Integer] Exit code from executed command
  # @raise [RuntimeError] if execution fails
  #
  # @example
  #   wrapper = BinaryWrapper.new('tool')
  #   exit_code = wrapper.execute(['--version'])
  def execute(args)
    # Implementation
    0
  end
end
```

### Method Documentation

```ruby
# Find the canonical binary path
#
# Searches for the binary in the following locations:
#   1. BINARY_PATH environment variable
#   2. ./dist/<os>/<arch>/binary (relative to repo root)
#   3. PATH lookup via which command
#
# @param binary_name [String] Name of binary to find
# @return [String, nil] Path to binary if found, nil otherwise
#
# @note This method caches the result for performance
#
# @example
#   path = find_binary('tool')
#   puts "Found at: #{path}" if path
def find_binary(binary_name)
  # Implementation
end
```

### Key Rules

1. **Shebang first**: Always start with `#!/usr/bin/env ruby`
2. **frozen_string_literal**: Include `# frozen_string_literal: true` after shebang
3. **YARD tags**: Use `@param`, `@return`, `@raise`, `@example`, etc.
4. **Type annotations**: Use `[Type]` notation for types in YARD
5. **@return for all methods**: Always document return values
6. **@raise for exceptions**: Document all exceptions that may be raised
7. **Exit codes**: Document in file-level comments
8. **@example blocks**: Provide runnable code examples

## Templates

### Minimal Template (script.rb)

```ruby
#!/usr/bin/env ruby
# frozen_string_literal: true

# One-line summary of what this script does
#
# Detailed description of behavior.
#
# Exit Codes:
#   0 - Success
#   1 - Failure
#
# @note Platform: Ruby 3.0+

# Main entry point
#
# @param args [Array<String>] Command-line arguments
# @return [Integer] Exit code
def main(args)
  puts 'Hello, world!'
  0
end

exit main(ARGV) if __FILE__ == $PROGRAM_NAME
```

### Full Template (wrapper.rb)

```ruby
#!/usr/bin/env ruby
# frozen_string_literal: true

# Wrapper for canonical tool execution
#
# This script discovers and invokes the canonical implementation.
# It does NOT reimplement any contract logic - purely a thin wrapper.
#
# Binary Discovery Order:
#   1. BINARY_PATH environment variable
#   2. ./dist/<os>/<arch>/binary
#   3. PATH lookup via which command
#   4. Error with instructions (exit 127)
#
# Exit Codes:
#   0 - Success - command executed successfully
#   1 - General failure
#   2 - Invalid arguments
#   127 - Binary not found
#
# @author Repository contributors
# @version 1.0
#
# @note Platform: Ruby 3.0 or later, cross-platform
#
# @example Basic usage
#   ruby wrapper.rb command arg1 arg2
#
# @example With environment override
#   BINARY_PATH=/custom/path ruby wrapper.rb command
#
# @see docs/architecture/wrapper-discovery.md
# @see exit-codes-contract.md

require 'pathname'
require 'open3'
require 'rbconfig'

# Find the canonical binary
#
# Searches for the binary in the following order:
#   1. BINARY_PATH environment variable
#   2. ./dist/<os>/<arch>/binary
#   3. PATH lookup via which
#
# @param binary_name [String] Name of binary to find
# @return [Pathname] Path to binary
# @raise [RuntimeError] if binary not found
#
# @note Searches BINARY_PATH env var first
def find_binary(binary_name)
  # Check BINARY_PATH environment variable
  env_path = ENV['BINARY_PATH']
  if env_path && File.exist?(env_path)
    return Pathname.new(env_path)
  end

  # Check dist directory
  os = RbConfig::CONFIG['host_os']
  arch = RbConfig::CONFIG['host_cpu']
  dist_path = Pathname.new("dist/#{os}/#{arch}/#{binary_name}")
  return dist_path if dist_path.exist?

  # Check PATH
  path_result, status = Open3.capture2('which', binary_name)
  return Pathname.new(path_result.chomp) if status.success?

  raise "Binary '#{binary_name}' not found. Set BINARY_PATH or install tool."
end

# Execute binary with arguments
#
# @param binary_path [Pathname] Path to binary
# @param args [Array<String>] Arguments to pass
# @return [Integer] Exit code from executed command
#
# @raise [RuntimeError] if execution fails
def execute_binary(binary_path, args)
  # Execute and capture output
  stdout, stderr, status = Open3.capture3(binary_path.to_s, *args)
  
  $stdout.print stdout
  $stderr.print stderr
  
  status.exitstatus
end

# Main entry point
#
# @param args [Array<String>] Command-line arguments
# @return [Integer] Exit code
#
# Parses arguments, finds binary, and executes command
def main(args)
  if args.empty?
    warn "Usage: #{$PROGRAM_NAME} <command> [args...]"
    return 2
  end

  binary_path = find_binary('tool')
  execute_binary(binary_path, args)
rescue RuntimeError => e
  warn "Error: #{e.message}"
  127
rescue StandardError => e
  warn "Error: #{e.message}"
  1
end

exit main(ARGV) if __FILE__ == $PROGRAM_NAME
```

## Validation (Future)

When this contract is officially adopted, the validator should check:

- Presence of file-level documentation
- Shebang `#!/usr/bin/env ruby`
- `frozen_string_literal: true`
- Exit codes documented in file comments
- `@param` for all method parameters
- `@return` for all methods
- `@raise` for methods that raise exceptions
- `@example` with code

## Common Mistakes (Future)

❌ **Wrong:** Missing method documentation

```ruby
def important_method(x)
  x + 1
end
```

✅ **Correct:** Document all public methods

```ruby
# Increment value by one
#
# @param x [Integer] Value to increment
# @return [Integer] Incremented value
def important_method(x)
  x + 1
end
```

## Documentation Tools

Ruby code following this contract can use YARD:

```bash
# Generate documentation with YARD
yard doc

# Generate and view in browser
yard server

# Check documentation coverage
yard stats --list-undoc

# Generate with RDoc (alternative)
rdoc
```

## References

- [YARD Documentation](https://yardoc.org/)
- [YARD Tags](https://rubydoc.info/gems/yard/file/docs/Tags.md)
- [RDoc Markup](https://ruby.github.io/rdoc/RDoc/Markup.html)
- [Ruby Style Guide](https://rubystyle.guide/)
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [README.md](./README.md) - Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:

1. Add Ruby file patterns to validator
2. Implement RubyValidator class
3. Add test coverage
4. Update README.md with Ruby entry
5. Mark as official (remove DRAFT status)
