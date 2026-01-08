# C++ Docstring Contract (DRAFT)

**Language:** C++ (`.cpp`, `.hpp`, `.cc`, `.hh`, `.cxx`, `.h`)
**Canonical style:** Doxygen-style comments using `/** ... */`, `///`, or `//!`
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for C++ source files that may be added to this repository in the future. It follows Doxygen conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding C++ files, but expect refinement before official adoption.

## Required Semantic Sections

Every C++ source file should include these sections in header comments:

1. **@file** - File description and one-line summary
2. **@brief** - Brief description of the file/module/class
3. **@details** - What it does and does NOT do
4. **@param** - Document each function parameter (if applicable)
5. **@return** or **@returns** - Return value documentation
6. **@note** - Important notes, constraints, sharp edges
7. **@example** or **@code** - Minimum 1 concrete usage example

### Optional Sections

- **@platform** - Platform compatibility (OS, compiler, C++ version) - **Recommended**
- **@author** - Author information
- **@version** - Version information
- **@date** - Last modified date
- **@see** - References to related files/classes
- **@warning** - Warnings about usage
- **@throw** or **@throws** - Exception documentation
- **@tparam** - Template parameter documentation

## Formatting Rules

### File-Level Documentation

```cpp
/**
 * @file script.cpp
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
 * Uses C++17 features (std::filesystem)
 *
 * @platform
 * Linux/Unix/Windows with C++17 compiler (GCC 7+, Clang 5+, MSVC 2017+)
 *
 * @see exit-codes-contract.md
 */

#include <iostream>
#include <string>
#include <vector>
#include <filesystem>

namespace fs = std::filesystem;

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
int main(int argc, char* argv[]) {
    // Implementation
    return EXIT_SUCCESS;
}
```

### Class Documentation

```cpp
/**
 * @brief Binary discovery and execution wrapper
 *
 * @details
 * This class discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/<os>/<arch>/binary
 * 3. PATH lookup
 *
 * @note
 * Thread-safe for discovery operations
 *
 * @warning
 * Execute methods are not thread-safe
 */
class BinaryWrapper {
public:
    /**
     * @brief Construct a wrapper
     * @param binary_name Name of binary to wrap
     * @throws std::runtime_error if binary_name is empty
     */
    explicit BinaryWrapper(const std::string& binary_name);

    /**
     * @brief Find the binary path
     * @return Path to binary if found
     * @throws std::runtime_error if binary not found
     */
    fs::path find_binary() const;

    /**
     * @brief Execute command with arguments
     * @param args Command arguments
     * @return Exit code from executed command
     * @throws std::runtime_error if execution fails
     */
    int execute(const std::vector<std::string>& args);

private:
    std::string binary_name_;
    mutable fs::path cached_path_;
};
```

### Template Documentation

```cpp
/**
 * @brief Generic container wrapper
 *
 * @tparam T Element type (must be copy-constructible)
 * @tparam Allocator Allocator type (default: std::allocator<T>)
 *
 * @details
 * Provides a thin wrapper around standard containers with
 * additional validation and logging.
 */
template<typename T, typename Allocator = std::allocator<T>>
class Container {
public:
    /**
     * @brief Add element to container
     * @param value Element to add
     * @throws std::bad_alloc if allocation fails
     */
    void add(const T& value);
};
```

### Key Rules

1. **Namespace documentation**: Document namespaces with `@namespace`
2. **Doxygen markers**: Use `/**`, `///`, or `//!` for Doxygen comments
3. **@brief first**: Start class/function docs with `@brief`
4. **@param direction**: Use `[in]`, `[out]`, `[in,out]` for parameters
5. **@return/@returns**: Always document return values
6. **@throw/@throws**: Document all exceptions that may be thrown
7. **@tparam**: Document all template parameters
8. **Exit codes**: Document in file-level `@details`

## Templates

### Minimal Template (script.cpp)

```cpp
/**
 * @file script.cpp
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
 * C++17 or later
 */

#include <iostream>
#include <cstdlib>

/**
 * @brief Main entry point
 * @param argc Argument count
 * @param argv Argument vector
 * @return Exit code
 */
int main(int argc, char* argv[]) {
    std::cout << "Hello, world!" << std::endl;
    return EXIT_SUCCESS;
}
```

### Full Template (wrapper.cpp)

```cpp
/**
 * @file wrapper.cpp
 * @brief Wrapper for canonical tool execution
 *
 * @details
 * This program discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic - purely a thin wrapper.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/<os>/<arch>/binary
 * 3. PATH lookup via std::filesystem
 * 4. Error with instructions (exit 127)
 *
 * Exit Codes:
 * - 0: Success - command executed successfully
 * - 1: General failure or exception
 * - 2: Invalid arguments
 * - 127: Binary not found
 *
 * @note
 * Requires C++17 for std::filesystem
 *
 * @platform
 * C++17 or later with GCC 7+, Clang 5+, or MSVC 2017+
 *
 * @author Repository contributors
 * @version 1.0
 *
 * @see docs/architecture/wrapper-discovery.md
 * @see exit-codes-contract.md
 */

#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <cstdlib>
#include <stdexcept>

// POSIX headers for fork/execv (Unix/Linux/macOS)
#ifndef _WIN32
#include <unistd.h>
#include <sys/wait.h>
#endif

namespace fs = std::filesystem;

/**
 * @brief Find the canonical binary
 *
 * @param binary_name Name of binary to find
 * @return Path to binary
 * @throws std::runtime_error if binary not found
 *
 * @note Searches BINARY_PATH env var, then dist/, then PATH
 */
fs::path find_binary(const std::string& binary_name) {
    // Check BINARY_PATH environment variable
    if (const char* env_path = std::getenv("BINARY_PATH")) {
        fs::path path(env_path);
        if (fs::exists(path)) {
            return path;
        }
    }

    // Additional discovery logic...
    throw std::runtime_error("Binary '" + binary_name + "' not found");
}

/**
 * @brief Execute binary with arguments
 *
 * @param binary_path Path to binary
 * @param args Arguments to pass
 * @return Exit code from executed command
 *
 * @throws std::runtime_error if execution fails
 *
 * @note
 * This implementation uses execv (POSIX) to avoid shell injection vulnerabilities.
 * On Windows, use CreateProcess or similar APIs instead of system().
 */
int execute_binary(const fs::path& binary_path,
                   const std::vector<std::string>& args) {
#ifdef _WIN32
    // Windows implementation using CreateProcess would go here
    // This is a simplified example - real code should use CreateProcess
    // to avoid shell injection vulnerabilities
    throw std::runtime_error(
        "execute_binary not implemented for Windows. "
        "Use CreateProcess API with proper argument escaping."
    );
#else
    // POSIX implementation using fork + execv to avoid shell injection
    // Build argv-style array: [binary_path, args..., nullptr]
    std::vector<char*> c_args;
    std::string binary_str = binary_path.string();
    c_args.push_back(const_cast<char*>(binary_str.c_str()));
    for (const auto& arg : args) {
        c_args.push_back(const_cast<char*>(arg.c_str()));
    }
    c_args.push_back(nullptr);

    pid_t pid = fork();
    if (pid < 0) {
        throw std::runtime_error("fork() failed");
    }

    if (pid == 0) {
        // Child process: replace image with target binary
        execv(binary_str.c_str(), c_args.data());
        // If execv returns, an error occurred
        std::_Exit(127);
    }

    // Parent process: wait for child
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) {
        throw std::runtime_error("waitpid() failed");
    }

    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }

    // Abnormal termination (signal, etc.)
    throw std::runtime_error("Process terminated abnormally");
#endif
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
int main(int argc, char* argv[]) {
    try {
        if (argc < 2) {
            std::cerr << "Usage: " << argv[0] << " <command> [args...]" << std::endl;
            return 2;
        }

        auto binary_path = find_binary("tool");

        std::vector<std::string> args(argv + 1, argv + argc);
        return execute_binary(binary_path, args);

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
```

### Header File Template (.hpp)

```cpp
/**
 * @file module.hpp
 * @brief Public interface for module functionality
 *
 * @details
 * This header defines the public API for the module.
 * Include this header to use module classes and functions.
 *
 * @platform
 * C++11 or later
 */

#ifndef MODULE_HPP
#define MODULE_HPP

#include <string>
#include <memory>

/**
 * @namespace module
 * @brief Module functionality namespace
 */
namespace module {

/**
 * @brief Initialize the module
 * @return true on success, false on failure
 */
bool initialize();

/**
 * @brief Clean up module resources
 */
void cleanup();

/**
 * @class Processor
 * @brief Data processor class
 */
class Processor {
public:
    /**
     * @brief Create a processor
     * @return Unique pointer to processor
     */
    static std::unique_ptr<Processor> create();

    /**
     * @brief Process input data
     * @param input Input string
     * @return Processed output
     * @throws std::invalid_argument if input is empty
     */
    std::string process(const std::string& input);

    /// Virtual destructor
    virtual ~Processor() = default;
};

} // namespace module

#endif // MODULE_HPP
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
- `@throw` for functions that may throw exceptions
- `@tparam` for template parameters

## Common Mistakes (Future)

❌ **Wrong:** Missing exception documentation

```cpp
/** @brief Does something */
void func() { throw std::runtime_error("fail"); }
```

✅ **Correct:** Document exceptions

```cpp
/**
 * @brief Does something
 * @throws std::runtime_error on failure
 */
void func() { throw std::runtime_error("fail"); }
```

## Doxygen Tools

C++ code following this contract can use Doxygen:

```bash
# Generate documentation
doxygen Doxyfile

# Common Doxyfile settings for C++
# EXTRACT_ALL = YES
# EXTRACT_PRIVATE = NO
# EXTRACT_STATIC = YES
# RECURSIVE = YES
```

## References

- [Doxygen Manual](https://www.doxygen.nl/manual/)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [README.md](./README.md) - Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:

1. Add C++ file patterns to validator
2. Implement CppValidator class
3. Add test coverage
4. Update README.md with C++ entry
5. Mark as official (remove DRAFT status)
