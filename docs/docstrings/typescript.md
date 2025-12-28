# TypeScript Docstring Contract (DRAFT)

**Language:** TypeScript (`.ts`, `.tsx`)  
**Canonical style:** TSDoc comments using `/** ... */`  
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for TypeScript files that may be added to this repository in the future. It follows TSDoc (TypeScript documentation) conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding TypeScript files, but expect refinement before official adoption.

## Required Semantic Sections

Every TypeScript file should include these sections in TSDoc comments:

1. **@packageDocumentation** - Module/file description (for file-level)
2. **Summary paragraph** - Brief description
3. **@remarks** - Detailed description, what it does and does NOT do
4. **@param** - Document each function parameter (if applicable)
5. **@returns** - Return value documentation
6. **@throws** - Document errors/exceptions that may be thrown
7. **@example** - Minimum 1 concrete usage example
8. **@see** - References to related docs

### Optional Sections

- **@platform** - Platform compatibility (Node.js/browser, version) - **Recommended** (use @remarks)
- **@public**, **@private**, **@internal** - Visibility markers
- **@deprecated** - Deprecation warnings
- **@typeParam** - Generic type parameter documentation
- **@defaultValue** - Default value for parameters
- **@beta**, **@alpha** - API stability markers

## Formatting Rules

### File-Level Documentation

```typescript
#!/usr/bin/env node

/**
 * Wrapper for canonical tool execution
 *
 * @remarks
 * This script discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic - purely a thin wrapper.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/\<os\>/\<arch\>/binary
 * 3. PATH lookup
 * 4. Error with instructions (exit 127)
 *
 * Exit Codes:
 * - 0: Success - command executed successfully
 * - 1: General failure
 * - 2: Invalid arguments
 * - 127: Binary not found
 *
 * Platform: Node.js 16+ or modern browsers (ES2020+)
 *
 * @packageDocumentation
 *
 * @example Basic usage
 * ```bash
 * node wrapper.js command arg1 arg2
 * ```
 *
 * @example With environment override
 * ```bash
 * BINARY_PATH=/custom/path node wrapper.js command
 * ```
 *
 * @see {@link exit-codes-contract.md}
 */

import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';

/**
 * Main entry point
 *
 * @param args - Command-line arguments
 * @returns Exit code (0 for success, non-zero for failure)
 *
 * @remarks
 * Parses arguments, finds binary, and executes command
 *
 * @throws {@link Error}
 * Thrown when binary cannot be found or execution fails
 *
 * @example
 * ```typescript
 * const exitCode = await main(['command', 'arg1']);
 * process.exit(exitCode);
 * ```
 */
async function main(args: string[]): Promise<number> {
    // Implementation
    return 0;
}

// CLI entry point
if (require.main === module) {
    main(process.argv.slice(2))
        .then(code => process.exit(code))
        .catch(err => {
            console.error(err.message);
            process.exit(1);
        });
}

export { main };
```

### Interface Documentation

```typescript
/**
 * Configuration options for binary wrapper
 *
 * @remarks
 * Use this interface to configure wrapper behavior
 *
 * @public
 */
interface WrapperConfig {
    /**
     * Name of binary to wrap
     *
     * @remarks
     * Must be a valid executable name
     */
    binaryName: string;

    /**
     * Additional search paths
     *
     * @defaultValue `[]`
     */
    searchPaths?: string[];

    /**
     * Timeout in milliseconds
     *
     * @defaultValue `30000` (30 seconds)
     */
    timeout?: number;
}
```

### Class Documentation

```typescript
/**
 * Binary discovery and execution wrapper
 *
 * @remarks
 * This class discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/\<os\>/\<arch\>/binary
 * 3. PATH lookup
 *
 * @example Create and use wrapper
 * ```typescript
 * const wrapper = new BinaryWrapper('tool');
 * const exitCode = await wrapper.execute(['arg1', 'arg2']);
 * ```
 *
 * @public
 */
class BinaryWrapper {
    private readonly binaryName: string;
    private cachedPath: string | null = null;

    /**
     * Creates a new binary wrapper
     *
     * @param binaryName - Name of binary to wrap
     *
     * @throws {@link Error}
     * Thrown when binaryName is empty
     *
     * @example
     * ```typescript
     * const wrapper = new BinaryWrapper('tool');
     * ```
     */
    constructor(binaryName: string) {
        if (!binaryName) {
            throw new Error('binaryName cannot be empty');
        }
        this.binaryName = binaryName;
    }

    /**
     * Finds the binary path
     *
     * @returns Path to binary
     *
     * @throws {@link Error}
     * Thrown when binary cannot be found
     *
     * @remarks
     * Searches BINARY_PATH env var, then dist/, then PATH
     *
     * @example
     * ```typescript
     * const wrapper = new BinaryWrapper('tool');
     * const path = await wrapper.findBinary();
     * console.log(`Found: ${path}`);
     * ```
     */
    async findBinary(): Promise<string> {
        // Check cache
        if (this.cachedPath) {
            return this.cachedPath;
        }

        // Check BINARY_PATH environment variable
        const envPath = process.env.BINARY_PATH;
        if (envPath && existsSync(envPath)) {
            this.cachedPath = envPath;
            return envPath;
        }

        throw new Error(`Binary '${this.binaryName}' not found`);
    }

    /**
     * Executes command with arguments
     *
     * @param args - Command arguments
     * @returns Exit code from executed command
     *
     * @throws {@link Error}
     * Thrown when execution fails
     *
     * @example
     * ```typescript
     * const wrapper = new BinaryWrapper('tool');
     * const exitCode = await wrapper.execute(['--version']);
     * ```
     */
    async execute(args: string[]): Promise<number> {
        const binaryPath = await this.findBinary();
        
        return new Promise((resolve, reject) => {
            const child = spawn(binaryPath, args);
            
            child.on('exit', code => resolve(code ?? 1));
            child.on('error', err => reject(err));
        });
    }
}
```

### Generic Class Documentation

```typescript
/**
 * Generic container wrapper
 *
 * @typeParam T - Element type (must extend object)
 *
 * @remarks
 * Provides a thin wrapper around standard collections with
 * additional validation and logging.
 *
 * @example
 * ```typescript
 * const container = new Container<User>();
 * container.add({ id: 1, name: 'Alice' });
 * ```
 *
 * @public
 */
class Container<T extends object> {
    private items: T[] = [];

    /**
     * Adds element to container
     *
     * @param value - Element to add
     *
     * @throws {@link Error}
     * Thrown when value is null or undefined
     *
     * @example
     * ```typescript
     * const container = new Container<string>();
     * container.add('item');
     * ```
     */
    add(value: T): void {
        if (value === null || value === undefined) {
            throw new Error('Value cannot be null or undefined');
        }
        this.items.push(value);
    }

    /**
     * Gets all items
     *
     * @returns Array of all items
     */
    getAll(): readonly T[] {
        return this.items;
    }
}
```

### Key Rules

1. **`/**` for TSDoc**: Always use `/**` for documentation (not `//` or `/*`)
2. **Summary first**: First paragraph is always the summary
3. **@remarks for details**: Use `@remarks` for detailed description
4. **@param for all parameters**: Document every parameter with type
5. **@returns for non-void**: Always document return values
6. **@throws for errors**: Document all errors that may be thrown
7. **@typeParam for generics**: Document all generic type parameters
8. **@example with code blocks**: Use fenced code blocks (```)
9. **Exit codes in @remarks**: Document exit codes in file-level @remarks

## Templates

### Minimal Template (script.ts)

```typescript
#!/usr/bin/env node

/**
 * One-line summary of what this script does
 *
 * @remarks
 * Detailed description of behavior.
 *
 * Exit Codes:
 * - 0: Success
 * - 1: Failure
 *
 * Platform: Node.js 16+
 *
 * @packageDocumentation
 */

/**
 * Main entry point
 *
 * @param args - Command-line arguments
 * @returns Exit code
 */
function main(args: string[]): number {
    console.log('Hello, world!');
    return 0;
}

if (require.main === module) {
    process.exit(main(process.argv.slice(2)));
}

export { main };
```

### Full Template (wrapper.ts)

```typescript
#!/usr/bin/env node

/**
 * Wrapper for canonical tool execution
 *
 * @remarks
 * This program discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic - purely a thin wrapper.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/\<os\>/\<arch\>/binary
 * 3. PATH lookup
 * 4. Error with instructions (exit 127)
 *
 * Exit Codes:
 * - 0: Success - command executed successfully
 * - 1: General failure
 * - 2: Invalid arguments
 * - 127: Binary not found
 *
 * Platform: Node.js 16 or later, TypeScript 4.5+
 *
 * @packageDocumentation
 *
 * @author Repository contributors
 * @version 1.0
 *
 * @see {@link docs/wrapper-discovery.md}
 * @see {@link exit-codes-contract.md}
 */

import { spawn, SpawnOptions } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';

/**
 * Finds the canonical binary
 *
 * @param binaryName - Name of binary to find
 * @returns Path to binary
 *
 * @throws {@link Error}
 * Thrown when binary cannot be found
 *
 * @remarks
 * Searches BINARY_PATH env var, then dist/, then PATH
 *
 * @example
 * ```typescript
 * const path = await findBinary('tool');
 * console.log(`Found: ${path}`);
 * ```
 */
async function findBinary(binaryName: string): Promise<string> {
    // Check BINARY_PATH environment variable
    const envPath = process.env.BINARY_PATH;
    if (envPath && existsSync(envPath)) {
        return envPath;
    }

    // Additional discovery logic...
    throw new Error(`Binary '${binaryName}' not found. Set BINARY_PATH or install tool.`);
}

/**
 * Executes binary with arguments
 *
 * @param binaryPath - Path to binary
 * @param args - Arguments to pass
 * @returns Exit code from executed command
 *
 * @throws {@link Error}
 * Thrown when execution fails
 *
 * @example
 * ```typescript
 * const exitCode = await executeBinary('/usr/bin/tool', ['--version']);
 * ```
 */
async function executeBinary(binaryPath: string, args: string[]): Promise<number> {
    return new Promise((resolve, reject) => {
        const child = spawn(binaryPath, args, {
            stdio: 'inherit'
        });

        child.on('exit', code => resolve(code ?? 1));
        child.on('error', err => reject(err));
    });
}

/**
 * Main entry point
 *
 * @param args - Command-line arguments
 * @returns Exit code
 *
 * @remarks
 * Parses arguments, finds binary, and executes command
 *
 * @example
 * ```typescript
 * const exitCode = await main(['command', 'arg1', 'arg2']);
 * process.exit(exitCode);
 * ```
 */
async function main(args: string[]): Promise<number> {
    try {
        if (args.length === 0) {
            console.error('Usage: wrapper <command> [args...]');
            return 2;
        }

        const binaryPath = await findBinary('tool');
        return await executeBinary(binaryPath, args);
    } catch (err) {
        if (err instanceof Error) {
            if (err.message.includes('not found')) {
                console.error(`Error: ${err.message}`);
                return 127;
            }
            console.error(`Error: ${err.message}`);
        }
        return 1;
    }
}

// CLI entry point
if (require.main === module) {
    main(process.argv.slice(2))
        .then(code => process.exit(code))
        .catch(err => {
            console.error(err.message);
            process.exit(1);
        });
}

export { main, findBinary, executeBinary };
```

## Validation (Future)

When this contract is officially adopted, the validator should check:

- Presence of `/**` TSDoc comments
- `@packageDocumentation` for file-level docs
- Summary paragraph for all public members
- `@remarks` with detailed description
- `@example` with code blocks
- Exit codes documented in @remarks
- `@param` for all parameters
- `@returns` for all non-void functions
- `@throws` for errors
- `@typeParam` for generic parameters

## Common Mistakes (Future)

❌ **Wrong:** Using `//` for documentation
```typescript
// This won't be picked up by TSDoc
function doSomething() { }
```

✅ **Correct:** Use `/**` for TSDoc
```typescript
/**
 * Does something useful
 */
function doSomething() { }
```

## TSDoc Tools

TypeScript code following this contract can use various tools:

```bash
# Generate documentation with TypeDoc
typedoc --out docs src/

# Generate with API Extractor
api-extractor run

# Type check documentation
tsc --noEmit

# Lint documentation with ESLint plugin
npm install -D eslint-plugin-tsdoc
# Add to .eslintrc: "plugins": ["eslint-plugin-tsdoc"]
```

## References

- [TSDoc Official](https://tsdoc.org/)
- [TSDoc Tags](https://tsdoc.org/pages/tags/alpha/)
- [TypeDoc Documentation](https://typedoc.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [README.md](./README.md) - Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:
1. Add TypeScript file patterns to validator
2. Implement TypeScriptValidator class
3. Add test coverage
4. Update README.md with TypeScript entry
5. Mark as official (remove DRAFT status)
