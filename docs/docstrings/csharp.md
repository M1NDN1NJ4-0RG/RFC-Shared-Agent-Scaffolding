# C# Docstring Contract (DRAFT)

**Language:** C# (`.cs`)  
**Canonical style:** XML documentation comments using `///`  
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for C# source files that may be added to this repository in the future. It follows C# XML documentation conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding C# files, but expect refinement before official adoption.

## Required Semantic Sections

Every C# source file should include these sections in XML documentation comments:

1. **\<summary\>** - Brief description of class/method/file
2. **\<remarks\>** - Detailed description, what it does and does NOT do
3. **\<param\>** - Document each method parameter (if applicable)
4. **\<returns\>** - Return value documentation
5. **\<exception\>** - Document exceptions that may be thrown
6. **\<example\>** - Minimum 1 concrete usage example with \<code\> blocks
7. **\<seealso\>** - References to related classes/methods

### Optional Sections

- **\<platform\>** - Platform compatibility (.NET version, OS requirements) - **Recommended** (use \<remarks\>)
- **\<value\>** - For properties
- **\<typeparam\>** - For generic type parameters
- **\<permission\>** - Required permissions
- **\<include\>** - External documentation files

## Formatting Rules

### File-Level Documentation

```csharp
/// <summary>
/// One-line summary of what this program does
/// </summary>
/// <remarks>
/// Detailed description of what the program does.
/// Multiple paragraphs are allowed.
/// State what it does NOT do if relevant.
///
/// <para>
/// This program acts as a wrapper that discovers and executes the canonical tool.
/// </para>
///
/// <para>
/// Exit Codes:
/// <list type="bullet">
/// <item><term>0</term><description>Success - command executed successfully</description></item>
/// <item><term>1</term><description>General failure</description></item>
/// <item><term>2</term><description>Invalid arguments</description></item>
/// <item><term>127</term><description>Binary not found</description></item>
/// </list>
/// </para>
///
/// <para>
/// Platform: .NET 6.0 or later, cross-platform (Windows/Linux/macOS)
/// </para>
/// </remarks>
/// <seealso href="EXIT_CODES_CONTRACT.md"/>
using System;
using System.IO;
using System.Diagnostics;

namespace WrapperTool
{
    /// <summary>
    /// Main program class
    /// </summary>
    class Program
    {
        /// <summary>
        /// Main entry point
        /// </summary>
        /// <param name="args">Command-line arguments</param>
        /// <returns>Exit code (0 for success, non-zero for failure)</returns>
        static int Main(string[] args)
        {
            // Implementation
            return 0;
        }
    }
}
```

### Class Documentation

```csharp
/// <summary>
/// Binary discovery and execution wrapper
/// </summary>
/// <remarks>
/// <para>
/// This class discovers and invokes the canonical implementation.
/// It does NOT reimplement any contract logic.
/// </para>
/// <para>
/// Binary Discovery Order:
/// <list type="number">
/// <item><description>BINARY_PATH environment variable</description></item>
/// <item><description>./dist/&lt;os&gt;/&lt;arch&gt;/binary</description></item>
/// <item><description>PATH lookup</description></item>
/// </list>
/// </para>
/// </remarks>
public class BinaryWrapper
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BinaryWrapper"/> class
    /// </summary>
    /// <param name="binaryName">Name of binary to wrap</param>
    /// <exception cref="ArgumentNullException">
    /// Thrown when <paramref name="binaryName"/> is null or empty
    /// </exception>
    public BinaryWrapper(string binaryName)
    {
        if (string.IsNullOrEmpty(binaryName))
            throw new ArgumentNullException(nameof(binaryName));
            
        this.binaryName = binaryName;
    }

    /// <summary>
    /// Finds the binary path
    /// </summary>
    /// <returns>Full path to binary</returns>
    /// <exception cref="FileNotFoundException">
    /// Thrown when binary cannot be found
    /// </exception>
    /// <example>
    /// <code>
    /// var wrapper = new BinaryWrapper("tool");
    /// string path = wrapper.FindBinary();
    /// Console.WriteLine($"Found: {path}");
    /// </code>
    /// </example>
    public string FindBinary()
    {
        // Implementation
        return string.Empty;
    }

    /// <summary>
    /// Executes command with arguments
    /// </summary>
    /// <param name="arguments">Command arguments</param>
    /// <returns>Exit code from executed command</returns>
    /// <exception cref="InvalidOperationException">
    /// Thrown when execution fails
    /// </exception>
    public int Execute(string[] arguments)
    {
        // Implementation
        return 0;
    }

    private readonly string binaryName;
}
```

### Generic Class Documentation

```csharp
/// <summary>
/// Generic container wrapper
/// </summary>
/// <typeparam name="T">Element type (must be a reference type)</typeparam>
/// <remarks>
/// Provides a thin wrapper around standard collections with
/// additional validation and logging.
/// </remarks>
public class Container<T> where T : class
{
    /// <summary>
    /// Adds element to container
    /// </summary>
    /// <param name="value">Element to add</param>
    /// <exception cref="ArgumentNullException">
    /// Thrown when <paramref name="value"/> is null
    /// </exception>
    public void Add(T value)
    {
        if (value == null)
            throw new ArgumentNullException(nameof(value));
    }
}
```

### Key Rules

1. **/// for XML docs**: Always use `///` for documentation comments
2. **\<summary\> first**: Every public member needs `<summary>`
3. **\<param\> for all parameters**: Document every method parameter
4. **\<exception\> for all throws**: Document all exceptions
5. **\<typeparam\> for generics**: Document all generic type parameters
6. **\<returns\> for non-void**: Always document return values
7. **\<code\> in \<example\>**: Use proper XML structure for examples
8. **Exit codes in \<remarks\>**: Document exit codes using \<list\>

## Templates

### Minimal Template (Script.cs)

```csharp
/// <summary>
/// One-line summary of what this script does
/// </summary>
/// <remarks>
/// <para>Detailed description of behavior.</para>
/// <para>
/// Exit Codes:
/// <list type="bullet">
/// <item><term>0</term><description>Success</description></item>
/// <item><term>1</term><description>Failure</description></item>
/// </list>
/// </para>
/// <para>Platform: .NET 6.0+</para>
/// </remarks>
using System;

class Program
{
    /// <summary>
    /// Main entry point
    /// </summary>
    /// <param name="args">Command-line arguments</param>
    /// <returns>Exit code</returns>
    static int Main(string[] args)
    {
        Console.WriteLine("Hello, world!");
        return 0;
    }
}
```

### Full Template (Wrapper.cs)

```csharp
/// <summary>
/// Wrapper for canonical tool execution
/// </summary>
/// <remarks>
/// <para>
/// This program discovers and invokes the canonical implementation.
/// It does NOT reimplement any contract logic - purely a thin wrapper.
/// </para>
/// <para>
/// Binary Discovery Order:
/// <list type="number">
/// <item><description>BINARY_PATH environment variable</description></item>
/// <item><description>./dist/&lt;os&gt;/&lt;arch&gt;/binary</description></item>
/// <item><description>PATH lookup</description></item>
/// <item><description>Error with instructions (exit 127)</description></item>
/// </list>
/// </para>
/// <para>
/// Exit Codes:
/// <list type="bullet">
/// <item><term>0</term><description>Success - command executed successfully</description></item>
/// <item><term>1</term><description>General failure</description></item>
/// <item><term>2</term><description>Invalid arguments</description></item>
/// <item><term>127</term><description>Binary not found</description></item>
/// </list>
/// </para>
/// <para>Platform: .NET 6.0 or later, Windows/Linux/macOS</para>
/// </remarks>
/// <seealso href="docs/wrapper-discovery.md"/>
/// <seealso href="EXIT_CODES_CONTRACT.md"/>
using System;
using System.IO;
using System.Diagnostics;
using System.Linq;

namespace WrapperTool
{
    /// <summary>
    /// Main program class
    /// </summary>
    class Program
    {
        /// <summary>
        /// Main entry point
        /// </summary>
        /// <param name="args">Command-line arguments</param>
        /// <returns>Exit code</returns>
        /// <remarks>
        /// Parses arguments, finds binary, and executes command
        /// </remarks>
        static int Main(string[] args)
        {
            try
            {
                if (args.Length == 0)
                {
                    Console.Error.WriteLine("Usage: wrapper <command> [args...]");
                    return 2;
                }

                string binaryPath = FindBinary("tool");
                return ExecuteBinary(binaryPath, args);
            }
            catch (FileNotFoundException)
            {
                Console.Error.WriteLine("Error: Binary 'tool' not found");
                Console.Error.WriteLine("Set BINARY_PATH or install tool");
                return 127;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex.Message}");
                return 1;
            }
        }

        /// <summary>
        /// Finds the canonical binary
        /// </summary>
        /// <param name="binaryName">Name of binary to find</param>
        /// <returns>Full path to binary</returns>
        /// <exception cref="FileNotFoundException">
        /// Thrown when binary cannot be found
        /// </exception>
        /// <remarks>
        /// Searches BINARY_PATH env var, then dist/, then PATH
        /// </remarks>
        static string FindBinary(string binaryName)
        {
            // Check BINARY_PATH environment variable
            string? envPath = Environment.GetEnvironmentVariable("BINARY_PATH");
            if (!string.IsNullOrEmpty(envPath) && File.Exists(envPath))
            {
                return envPath;
            }

            // Additional discovery logic...
            throw new FileNotFoundException($"Binary '{binaryName}' not found");
        }

        /// <summary>
        /// Executes binary with arguments
        /// </summary>
        /// <param name="binaryPath">Path to binary</param>
        /// <param name="arguments">Arguments to pass</param>
        /// <returns>Exit code from executed command</returns>
        /// <exception cref="InvalidOperationException">
        /// Thrown when execution fails
        /// </exception>
        static int ExecuteBinary(string binaryPath, string[] arguments)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = binaryPath,
                Arguments = string.Join(" ", arguments.Select(a => $"\"{a}\"")),
                UseShellExecute = false
            };

            using var process = Process.Start(startInfo);
            process?.WaitForExit();
            return process?.ExitCode ?? 1;
        }
    }
}
```

## Validation (Future)

When this contract is officially adopted, the validator should check:

- Presence of `///` XML documentation
- `<summary>` tag for all public members
- `<remarks>` with detailed description
- `<example>` with code blocks
- Exit codes documented in `<remarks>`
- `<param>` for all method parameters
- `<returns>` for all non-void methods
- `<exception>` for thrown exceptions
- `<typeparam>` for generic parameters

## Common Mistakes (Future)

❌ **Wrong:** Missing XML documentation
```csharp
public void DoSomething() { }
```

✅ **Correct:** XML documentation required
```csharp
/// <summary>
/// Does something useful
/// </summary>
public void DoSomething() { }
```

## XML Documentation Tools

C# code following this contract can generate documentation:

```bash
# Visual Studio automatically generates XML files
# Enable in project properties: Build > XML documentation file

# Generate with docfx
docfx init
docfx build docfx.json

# Generate with Sandcastle Help File Builder
# Use SHFB GUI or command line
```

## References

- [C# XML Documentation Comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/)
- [Recommended XML Tags](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags)
- [.NET API Documentation Guidelines](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/)
- [EXIT_CODES_CONTRACT.md](./EXIT_CODES_CONTRACT.md) - Canonical exit code meanings
- [README.md](./README.md) - Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:
1. Add C# file patterns to validator
2. Implement CSharpValidator class
3. Add test coverage
4. Update README.md with C# entry
5. Mark as official (remove DRAFT status)
