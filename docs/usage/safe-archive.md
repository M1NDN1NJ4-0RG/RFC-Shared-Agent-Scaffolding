# Safe-Archive Documentation

## Overview

The `safe-run archive` subcommand creates compressed archives from source directories. It supports multiple compression formats and provides no-clobber protection to prevent accidental data loss.

## Usage

```bash
safe-run archive [OPTIONS] <source> <destination>
```

### Arguments

- `<source>` - Source directory to archive
- `<destination>` - Destination archive path (.tar.gz, .tar.bz2, or .zip)

### Options

- `--no-clobber` - Enable strict no-clobber mode (fail if destination exists)

## Supported Formats

| Extension | Format | Compression |
| ----------- | -------- | ------------- |
| `.tar.gz`, `.tgz` | Tar + Gzip | Fast, good compression |
| `.tar.bz2`, `.tbz2` | Tar + Bzip2 | Slower, better compression |
| `.zip` | ZIP | Cross-platform compatibility |

## No-Clobber Behavior

### Default Mode (Auto-Suffix)

When the destination file already exists, `safe-run archive` automatically adds a numeric suffix to avoid overwriting:

```bash
# First run creates output.tar.gz
safe-run archive source/ output.tar.gz
# Archive created: output.tar.gz

# Second run creates output.1.tar.gz
safe-run archive source/ output.tar.gz
# Archive created: output.1.tar.gz

# Third run creates output.2.tar.gz
safe-run archive source/ output.tar.gz
# Archive created: output.2.tar.gz
```

### Strict Mode (--no-clobber)

With the `--no-clobber` flag, the command fails instead of auto-suffixing:

```bash
# First run succeeds
safe-run archive --no-clobber source/ output.tar.gz
# Archive created: output.tar.gz

# Second run fails with exit code 40
safe-run archive --no-clobber source/ output.tar.gz
# ERROR: Destination already exists (no-clobber mode): output.tar.gz
# File collision detected. Use a different destination or remove --no-clobber flag.
# Exit code: 40
```

## Exit Codes

| Code | Meaning |
| ------ | --------- |
| 0 | Archive created successfully |
| 2 | Invalid arguments or source not found |
| 40 | No-clobber collision in strict mode |
| 50 | Archive creation failed (I/O error) |

## Examples

### Basic Archive Creation

```bash
# Create a gzip-compressed tar archive
safe-run archive project/ project-backup.tar.gz

# Create a bzip2-compressed tar archive (better compression)
safe-run archive logs/ logs-$(date +%Y%m%d).tar.bz2

# Create a zip archive (cross-platform)
safe-run archive reports/ reports.zip
```

### CI/CD Use Cases

#### Artifact Collection

```bash
# Archive build outputs
safe-run archive dist/ artifacts-${CI_BUILD_ID}.tar.gz

# Archive test results
safe-run archive test-results/ test-results-${CI_COMMIT_SHA}.zip
```

#### Log Archival

```bash
# Archive logs with timestamp
safe-run archive /var/log/app/ app-logs-$(date +%Y%m%d-%H%M%S).tar.gz
```

#### Backup Workflows

```bash
#!/bin/bash
# Backup script with automatic naming

BACKUP_DIR="/backups"
SOURCE_DIR="/data"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create backup with auto-suffix (safe from overwrites)
safe-run archive "${SOURCE_DIR}" "${BACKUP_DIR}/data-${TIMESTAMP}.tar.gz"

# Result: Even if script runs twice in same second, both backups are preserved
```

### Strict No-Clobber for Critical Operations

```bash
#!/bin/bash
# Release packaging script that must not overwrite

VERSION="v1.2.3"
ARCHIVE="release-${VERSION}.tar.gz"

# Fail if release archive already exists
if ! safe-run archive --no-clobber dist/ "${ARCHIVE}"; then
    echo "ERROR: Release ${VERSION} already packaged!"
    exit 1
fi

echo "Release archive created: ${ARCHIVE}"
```

## Archive Contents

The archive contains all files and directories from the source directory. The directory structure is preserved relative to the source directory.

### Example

Given this directory structure:

```
project/
├── src/
│   ├── main.rs
│   └── lib.rs
├── tests/
│   └── test.rs
└── README.md
```

Creating an archive:

```bash
safe-run archive project/ project.tar.gz
```

The archive contains:

```
./
src/main.rs
src/lib.rs
tests/test.rs
README.md
```

## Technical Details

### Implementation

- **Tar archives**: Uses the `tar` crate with `flate2` (gzip) or `bzip2` compression
- **Zip archives**: Uses the `zip` crate with deflate compression
- **No-clobber**: Filesystem-level checking before archive creation
- **Auto-suffix**: Numeric suffix (.1, .2, etc.) inserted before final extension

### Performance Considerations

- Compression is single-threaded (Rust standard library limitation)
- For large directories, `.tar.gz` offers the best balance of speed and compression
- `.tar.bz2` provides better compression but is significantly slower
- `.zip` is fastest for cross-platform compatibility but has larger archive sizes

### Platform Notes

- **Unix/Linux**: Full support for all formats
- **macOS**: Full support for all formats
- **Windows**: Full support for all formats (no special handling needed)

## Comparison with safe-run

| Feature | safe-run | safe-run archive |
| --------- | ---------- | ------------------ |
| Purpose | Execute commands with logging | Create directory archives |
| Output | Log files on failure | Archive files always |
| Success case | No artifacts | Creates archive |
| Failure case | Creates log | Returns error code |
| Use case | Command execution monitoring | Artifact collection, backups |

## Contract References

- **safe-archive-001**: Basic archive creation
- **safe-archive-002**: Multiple compression formats
- **safe-archive-003**: No-clobber with auto-suffix
- **safe-archive-004**: No-clobber strict mode

See `conformance/vectors.json` for detailed test vectors.
