# C Docstring Contract (DRAFT)

**Language:** C (`.c`, `.h`)
**Canonical style:** Doxygen-style comments using `/** ... */` or `///`
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for C source files that may be added to this repository in the future. It follows Doxygen conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding C files, but expect refinement before official adoption.

## Required Semantic Sections

Every C source file should include these sections in header comments:

1. **@file** - File description and one-line summary
2. **@brief** - Brief description of the file/module
3. **@details** - What it does and does NOT do
4. **@param** - Document each function parameter (if applicable)
5. **@return** - Return value documentation
6. **@note** - Important notes, constraints, sharp edges
7. **@example** or **@code** - Minimum 1 concrete usage example

### Optional Sections

- **@platform** - Platform compatibility (OS, compiler requirements) - **Recommended**
- **@author** - Author information
- **@version** - Version information
- **@date** - Last modified date
- **@see** - References to related files/functions
- **@warning** - Warnings about usage
- **@bug** - Known bugs or limitations

## Formatting Rules

### File-Level Documentation

```c
/**
 * @file script-name.c
 * @brief One-line summary of what this file does
 *
 * @details
 * Detailed description of what the file does.
 * Multiple paragraphs are allowed.
 * State what it does NOT do if relevant.
 *
 * Exit Codes:
 * - 0: Success
 * - 1: General failure
 * - 2: Invalid arguments
 * - 127: Command not found
 *
 * @note
 * Important constraints or invariants
 *
 * @platform
 * Linux/Unix with GCC 4.8+ or Clang 3.4+
 *
 * @see exit-codes-contract.md
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * @brief Main entry point
 *
 * @param argc Argument count
 * @param argv Argument vector
 * @return Exit code (0 for success, non-zero for failure)
 *
 * @note
 * This function processes command-line arguments and delegates to handlers
 */
int main(int argc, char *argv[]) {
    // Implementation
    return 0;
}
```

### Function Documentation

```c
/**
 * @brief Find the canonical binary path
 *
 * @details
 * Searches for the binary in the following order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/<os>/<arch>/binary
 * 3. PATH lookup
 *
 * @param binary_name Name of binary to find (not NULL)
 * @param[out] result_path Buffer to store found path (must be PATH_MAX size)
 * @return 0 on success, -1 if not found, -2 if invalid args
 *
 * @note
 * Caller must allocate result_path buffer
 *
 * @warning
 * result_path must be at least PATH_MAX bytes
 *
 * @example
 * @code
 * char path[PATH_MAX];
 * if (find_binary("tool", path) == 0) {
 *     printf("Found: %s\n", path);
 * }
 * @endcode
 */
int find_binary(const char *binary_name, char *result_path);
```

### Key Rules

1. **Header guard**: Use `#ifndef` include guards for `.h` files
2. **Doxygen markers**: Use `/**` for Doxygen comments (not `/*`)
3. **@brief first**: Start function docs with `@brief`
4. **@param direction**: Use `[in]`, `[out]`, `[in,out]` for parameters
5. **@return**: Always document return values and meanings
6. **@note for constraints**: Use `@note` for important constraints
7. **Exit codes in @details**: Document exit codes in file-level `@details`

## Templates

### Minimal Template (script.c)

```c
/**
 * @file script.c
 * @brief One-line summary of what this script does
 *
 * @details
 * Detailed description of behavior.
 *
 * Exit Codes:
 * - 0: Success
 * - 1: Failure
 *
 * @platform
 * POSIX-compliant systems with GCC 4.8+
 */

#include <stdio.h>
#include <stdlib.h>

/**
 * @brief Main entry point
 * @param argc Argument count
 * @param argv Argument vector
 * @return Exit code
 */
int main(int argc, char *argv[]) {
    printf("Hello, world!\n");
    return EXIT_SUCCESS;
}
```

### Full Template (wrapper.c)

```c
/**
 * @file wrapper.c
 * @brief Wrapper for canonical tool execution
 *
 * @details
 * This program discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic - purely a thin wrapper.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/<os>/<arch>/binary
 * 3. PATH lookup via execvp()
 * 4. Error with instructions (exit 127)
 *
 * Exit Codes:
 * - 0: Success - command executed successfully
 * - 1: General failure
 * - 2: Invalid arguments
 * - 127: Binary not found
 *
 * @note
 * Do not modify discovery order without updating docs/architecture/wrapper-discovery.md
 *
 * @platform
 * Linux/Unix with GCC 4.8+, requires POSIX execvp()
 *
 * @author Repository contributors
 * @version 1.0
 *
 * @see docs/architecture/wrapper-discovery.md
 * @see exit-codes-contract.md
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>

#define MAX_ARGS 256

/**
 * @brief Find the canonical binary
 *
 * @param binary_name Name of binary to find
 * @param[out] path Buffer for result (must be PATH_MAX)
 * @return 0 on success, -1 if not found
 *
 * @note Searches BINARY_PATH env var, then dist/, then PATH
 */
int find_binary(const char *binary_name, char *path) {
    // Check BINARY_PATH environment variable
    char *env_path = getenv("BINARY_PATH");
    if (env_path != NULL) {
        strncpy(path, env_path, PATH_MAX - 1);
        path[PATH_MAX - 1] = '\0';
        return 0;
    }

    // Additional discovery logic...
    return -1;
}

/**
 * @brief Main entry point
 *
 * @param argc Argument count
 * @param argv Argument vector
 * @return Exit code
 *
 * @details
 * Parses arguments, finds binary, and executes command
 */
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        return 2;
    }

    char binary_path[PATH_MAX];
    if (find_binary("tool", binary_path) != 0) {
        fprintf(stderr, "Error: Binary 'tool' not found\n");
        fprintf(stderr, "Set BINARY_PATH or install tool\n");
        return 127;
    }

    // Execute binary
    execv(binary_path, &argv[1]);

    // If we get here, exec failed
    perror("execv");
    return 1;
}
```

### Header File Template (.h)

```c
/**
 * @file module.h
 * @brief Public interface for module functionality
 *
 * @details
 * This header defines the public API for the module.
 * Include this header to use module functions.
 *
 * @platform
 * C99 or later
 */

#ifndef MODULE_H
#define MODULE_H

#include <stddef.h>

/**
 * @brief Initialize the module
 * @return 0 on success, -1 on failure
 */
int module_init(void);

/**
 * @brief Clean up module resources
 */
void module_cleanup(void);

/**
 * @brief Process data with module
 * @param[in] input Input data
 * @param[out] output Output buffer (must be allocated)
 * @param size Size of output buffer
 * @return Number of bytes written, or -1 on error
 */
int module_process(const char *input, char *output, size_t size);

#endif /* MODULE_H */
```

## Validation (Future)

When this contract is officially adopted, the validator should check:

- Presence of `/**` Doxygen block at file level
- `@file` and `@brief` tags present
- `@details` with description
- `@example` or `@code` block with usage
- Exit codes documented in `@details`
- `@param` for all function parameters
- `@return` for all non-void functions

## Common Mistakes (Future)

❌ **Wrong:** Using `/*` instead of `/**` for Doxygen

```c
/* This won't be picked up by Doxygen */
int main() { }
```

✅ **Correct:** Use `/**` for documentation

```c
/** @brief Main function */
int main() { }
```

❌ **Wrong:** Missing parameter documentation

```c
/** @brief Does something */
int func(int x, char *y);
```

✅ **Correct:** Document all parameters

```c
/**
 * @brief Does something
 * @param x The value
 * @param y The string
 * @return Status code
 */
int func(int x, char *y);
```

## Doxygen Tools

C code following this contract can use Doxygen:

```bash
# Generate documentation
doxygen Doxyfile

# Generate with custom config
doxygen -g myconfig
doxygen myconfig

# Generate HTML and LaTeX
doxygen
```

## References

- [Doxygen Manual](https://www.doxygen.nl/manual/)
- [Doxygen Special Commands](https://www.doxygen.nl/manual/commands.html)
- [Linux Kernel Doc Guidelines](https://www.kernel.org/doc/html/latest/doc-guide/kernel-doc.html)
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [README.md](./README.md) - Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:

1. Add C file patterns to validator
2. Implement CValidator class
3. Add test coverage
4. Update README.md with C entry
5. Mark as official (remove DRAFT status)
