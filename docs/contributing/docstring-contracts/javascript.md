# JavaScript/Node.js Docstring Contract (DRAFT)

**Language:** JavaScript/Node.js (`.js`, `.mjs`)
**Canonical style:** JSDoc comments using `/** ... */`
**Status:** DRAFT - Not yet enforced by validator

## Purpose

This is a **preliminary contract** for JavaScript/Node.js scripts that may be added to this repository in the future. It
follows JSDoc conventions while aligning with the semantic requirements of other language contracts.

**Note:** This contract is not yet enforced. Use it as guidance if adding JavaScript files, but expect refinement before
official adoption.

## Required Semantic Sections

Every JavaScript script/module should include these sections in JSDoc comments:

1. 1. **@file** - File description and one-line summary 2. **@description** - What the module/script does and does NOT
   do 3. **@module** or **@namespace** - Module name 4. **@param** - Document each parameter (if applicable) 5.
   **@returns** - Return value documentation 6. **@throws** - Documented error conditions 7. **@example** - Minimum 1
   concrete usage example 8. **@see** - References to related docs

### Optional Sections

- - **@platform** - Platform compatibility (Node.js version, browser support) - **Recommended** - **@author** - Author
  information - **@version** - Version information - **@license** - License information - **@todo** - Known limitations
  or future work

## Formatting Rules

### Structure

```javascript
#!/usr/bin/env node
/**
 * @file One-line summary of what this script does.
 * @description
 * Detailed description of what the script does.
 * Multiple paragraphs are allowed.
 * State what it does NOT do if relevant.
 *
 * This script acts as a wrapper that discovers and executes the canonical tool.
 *
 * @module script-name
 *
 * @requires module:fs
 * @requires module:path
 *
 * @example
 * // Basic usage
 * node script-name.js --help
 *
 * @example
 * // With environment override
 * BINARY_PATH=/custom/path node script-name.js command
 *
 * @platform Node.js 16+
 *
 * @see {@link docs/architecture/wrapper-discovery.md}
 * @see {@link exit-codes-contract.md}
 */

const fs = require('fs');
const path = require('path');

/**
 * Main entry point for the script.
 *
 * @param {string[]} args - Command-line arguments
 * @returns {Promise<number>} Exit code (0 for success, non-zero for failure)
 *
 * @throws {Error} If binary not found
 *
 * @example
 * main(process.argv.slice(2))
 *   .then(code => process.exit(code))
 *   .catch(err => {
 *     console.error(err.message);
 *     process.exit(1);
 *   });
 */
async function main(args) {
  // Implementation
  return 0;
}

// Exit code handling
if (require.main === module) {
  main(process.argv.slice(2))
    .then(code => process.exit(code))
    .catch(err => {
      console.error(err.message);
      process.exit(1);
    });
}

module.exports = { main };
```

### Key Rules

1. **Shebang for scripts**: Use `#!/usr/bin/env node` for executable scripts
2. **File-level JSDoc**: Start with `/**` (not `/*`)
3. 3. **@file and @description**: Required at top of file
4. **@param types**: Use JSDoc type syntax: `{string}`, `{number}`, `{Array<string>}`
5. 5. **@returns**: Always document return value for functions 6. **@throws**: Document exceptions that can be thrown 7.
   **@example**: Include runnable code examples 8. **Exit codes**: Document in @description or separate section

## Exit Code Documentation

Document exit codes in the file-level `@description`:

```javascript
/**
 * @description
 * ...
 *
 * Exit Codes:
 * - 0: Success - operation completed
 * - 1: General failure
 * - 2: Invalid arguments
 * - 127: Binary not found
 *
 * @see {@link exit-codes-contract.md}
 */
```

## Templates

### Minimal Template

```javascript
#!/usr/bin/env node
/**
 * @file script-name.js - One-line summary
 * @description
 * Detailed description of behavior.
 *
 * Exit Codes:
 * - 0: Success
 * - 1: Failure
 *
 * @module script-name
 *
 * @example
 * node script-name.js arg
 *
 * @platform Node.js 16+
 */

/**
 * Main function.
 * @returns {number} Exit code
 */
function main() {
  console.log('Hello, world!');
  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { main };
```

### Full Template (ES Modules)

```javascript
#!/usr/bin/env node
/**
 * @file wrapper-tool.mjs - Wrapper for canonical tool
 * @description
 * This script discovers and invokes the canonical implementation.
 * It does NOT reimplement any contract logic - purely a thin invoker.
 *
 * Binary Discovery Order:
 * 1. BINARY_PATH environment variable
 * 2. ./dist/<os>/<arch>/binary
 * 3. PATH lookup
 * 4. Error with instructions (exit 127)
 *
 * Exit Codes:
 * - 0: Success
 * - 1: General failure
 * - 127: Binary not found
 *
 * @module wrapper-tool
 *
 * @requires module:fs/promises
 * @requires module:child_process
 *
 * @example
 * import { main } from './wrapper-tool.mjs';
 * const exitCode = await main(['echo', 'hello']);
 *
 * @platform Node.js 16+ (ESM support required)
 *
 * @see {@link docs/architecture/wrapper-discovery.md}
 * @see {@link exit-codes-contract.md}
 */

import { spawn } from 'child_process';
import { access, constants } from 'fs/promises';
import { join } from 'path';

/**
 * Find the canonical binary.
 *
 * @param {string} binaryName - Name of binary to find
 * @returns {Promise<string>} Path to binary
 * @throws {Error} If binary not found
 */
async function findBinary(binaryName) {
  // Implementation
  throw new Error('Not implemented');
}

/**
 * Main entry point.
 *
 * @param {string[]} args - Command-line arguments
 * @returns {Promise<number>} Exit code
 *
 * @example
 * await main(['command', 'arg1', 'arg2']);
 */
async function main(args) {
  try {
    const binary = await findBinary('tool');
    // Execute binary
    return 0;
  } catch (err) {
    console.error(err.message);
    return err.code === 'ENOENT' ? 127 : 1;
  }
}

// CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  main(process.argv.slice(2))
    .then(code => process.exit(code))
    .catch(err => {
      console.error(err.message);
      process.exit(1);
    });
}

export { main, findBinary };
```

## Validation (Future)

When this contract is officially adopted, the validator should check:

- Presence of `/**` JSDoc block at file level
- `@file` and `@description` tags present
- `@example` tag with code example
- Exit codes documented in `@description`
- `@param` for all function parameters
- `@returns` for all functions

## Common Mistakes (Future)

These will be documented once the contract is enforced.

## JSDoc Tools

Scripts following this contract can use standard JSDoc tools:

```bash
# Generate documentation
npx jsdoc script.js

# Generate with custom template
npx jsdoc script.js -t node_modules/docdash

# Validate JSDoc
npx eslint script.js --plugin jsdoc
```

## References

- [JSDoc Official Documentation](https://jsdoc.app/)
- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [TypeScript JSDoc Support](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- - [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings - [README.md](./README.md) -
  Overview of docstring contracts

## Status

**DRAFT** - This contract is not yet enforced. Feedback welcome before official adoption.

To adopt this contract:

1. 1. Add JavaScript file patterns to validator 2. Implement JavaScriptValidator class 3. Add test coverage 4. Update
   README.md with JavaScript entry 5. Mark as official (remove DRAFT status)
