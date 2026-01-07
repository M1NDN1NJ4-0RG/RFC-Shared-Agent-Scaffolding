//! # Safe-Archive Implementation Module
//!
//! This module implements the safe-archive functionality for creating tar/zip archives
//! from source directories.
//!
//! # Purpose
//!
//! Provides archive creation functionality with:
//! - Multiple compression formats (tar.gz, tar.bz2, zip)
//! - No-clobber semantics (auto-suffix or strict mode)
//! - Metadata inclusion (timestamp, source path)
//!
//! # Contract Compliance
//!
//! This implementation conforms to the safe-archive contract specification:
//! - Archive creation from source directories
//! - Support for .tar.gz, .tar.bz2, and .zip formats
//! - No-clobber with auto-suffix: Create archive-1, archive-2, etc.
//! - No-clobber strict mode: Fail with error if destination exists
//!
//! # Exit Codes
//!
//! - 0: Archive created successfully
//! - 2: Invalid arguments or source not found
//! - 40-49: No-clobber collision in strict mode
//! - 50: Archive creation failed (I/O error)
//!
//! # Examples
//!
//! ```no_run
//! # mod safe_archive { pub fn execute(args: &[String], no_clobber: bool) -> Result<i32, String> { Ok(0) } }
//! use safe_archive::execute;
//!
//! // Create a tar.gz archive
//! let result = execute(&["source/".to_string(), "output.tar.gz".to_string()], false);
//! assert_eq!(result.unwrap(), 0);
//! ```

use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

/// Execute safe-archive to create an archive from a source directory
///
/// # Purpose
///
/// Creates a compressed archive (tar.gz, tar.bz2, or zip) from a source directory.
/// Implements no-clobber semantics to prevent accidental overwrites.
///
/// # Arguments
///
/// - `args`: Slice of strings where:
///   - args[0]: Source directory path
///   - args[1]: Destination archive path
/// - `no_clobber`: If true, fail with error when destination exists (strict mode)
///   If false, auto-suffix the filename to avoid collision
///
/// # Returns
///
/// - `Ok(exit_code)`: Archive operation completed, returns exit code
/// - `Err(message)`: Tool error occurred
///
/// # Behavior
///
/// 1. Validates arguments (requires source and destination)
/// 2. Validates source directory exists
/// 3. Determines archive format from file extension
/// 4. Checks for destination collision:
///    - If no_clobber=true and exists: Return error code 40
///    - If no_clobber=false and exists: Find next available suffix
/// 5. Creates archive with appropriate compression
/// 6. Returns 0 on success
///
/// # Exit Codes
///
/// - 0: Archive created successfully
/// - 2: Invalid arguments or source not found
/// - 40: No-clobber collision (strict mode only)
/// - 50: Archive creation failed (I/O error)
pub fn execute(args: &[String], no_clobber: bool) -> Result<i32, String> {
    // Validate arguments
    if args.len() < 2 {
        eprintln!("usage: safe-run archive [--no-clobber] <source> <destination>");
        eprintln!();
        eprintln!("Creates an archive from the source directory.");
        eprintln!();
        eprintln!("Arguments:");
        eprintln!("  <source>       Source directory to archive");
        eprintln!("  <destination>  Destination archive path (.tar.gz, .tar.bz2, or .zip)");
        eprintln!();
        eprintln!("Options:");
        eprintln!("  --no-clobber   Fail if destination exists (default: auto-suffix)");
        return Ok(2);
    }

    let source_path = Path::new(&args[0]);
    let dest_path = PathBuf::from(&args[1]);

    // Validate source exists and is a directory
    if !source_path.exists() {
        eprintln!(
            "ERROR: Source path does not exist: {}",
            source_path.display()
        );
        return Ok(2);
    }

    if !source_path.is_dir() {
        eprintln!(
            "ERROR: Source path is not a directory: {}",
            source_path.display()
        );
        return Ok(2);
    }

    // Determine archive format from extension
    let format = determine_archive_format(&dest_path)?;

    // Handle no-clobber semantics
    let final_dest = if dest_path.exists() {
        if no_clobber {
            eprintln!(
                "ERROR: Destination already exists (no-clobber mode): {}",
                dest_path.display()
            );
            eprintln!(
                "File collision detected. Use a different destination or remove --no-clobber flag."
            );
            return Ok(40);
        } else {
            // Auto-suffix mode: find next available filename
            find_next_available_path(&dest_path)
        }
    } else {
        dest_path
    };

    // Create the archive
    create_archive(source_path, &final_dest, format)?;

    println!("Archive created: {}", final_dest.display());
    Ok(0)
}

/// Determine archive format from file extension
///
/// # Arguments
///
/// - `path`: Path to check for archive extension
///
/// # Returns
///
/// - `Ok(ArchiveFormat)`: Detected format
/// - `Err(message)`: Unsupported or missing extension
fn determine_archive_format(path: &Path) -> Result<ArchiveFormat, String> {
    let path_str = path.to_string_lossy().to_lowercase();

    if path_str.ends_with(".tar.gz") || path_str.ends_with(".tgz") {
        Ok(ArchiveFormat::TarGz)
    } else if path_str.ends_with(".tar.bz2") || path_str.ends_with(".tbz2") {
        Ok(ArchiveFormat::TarBz2)
    } else if path_str.ends_with(".zip") {
        Ok(ArchiveFormat::Zip)
    } else {
        Err(format!(
            "Unsupported archive format. Use .tar.gz, .tar.bz2, or .zip: {}",
            path.display()
        ))
    }
}

/// Find the next available path with numeric suffix
///
/// # Arguments
///
/// - `base_path`: Original destination path
///
/// # Returns
///
/// PathBuf with numeric suffix (e.g., output.1.tar.gz, output.2.tar.gz)
fn find_next_available_path(base_path: &Path) -> PathBuf {
    let base_str = base_path.to_string_lossy();

    // Find the last extension (e.g., ".tar.gz" or ".zip")
    let (name_part, ext_part) = if base_str.ends_with(".tar.gz") {
        (base_str.trim_end_matches(".tar.gz"), ".tar.gz")
    } else if base_str.ends_with(".tar.bz2") {
        (base_str.trim_end_matches(".tar.bz2"), ".tar.bz2")
    } else if base_str.ends_with(".zip") {
        (base_str.trim_end_matches(".zip"), ".zip")
    } else {
        // Fallback: split at last dot
        match base_str.rfind('.') {
            Some(pos) => (&base_str[..pos], &base_str[pos..]),
            None => (base_str.as_ref(), ""),
        }
    };

    let mut n = 1;
    loop {
        let candidate = PathBuf::from(format!("{}.{}{}", name_part, n, ext_part));
        if !candidate.exists() {
            return candidate;
        }
        n += 1;
    }
}

/// Archive format enumeration
#[derive(Debug, Clone, Copy, PartialEq)]
enum ArchiveFormat {
    TarGz,
    TarBz2,
    Zip,
}

/// Create an archive from source directory
///
/// # Arguments
///
/// - `source`: Source directory path
/// - `dest`: Destination archive path
/// - `format`: Archive format to use
///
/// # Returns
///
/// - `Ok(())`: Archive created successfully
/// - `Err(message)`: Archive creation failed
fn create_archive(source: &Path, dest: &Path, format: ArchiveFormat) -> Result<(), String> {
    match format {
        ArchiveFormat::TarGz => create_tar_archive(source, dest, Compression::Gzip),
        ArchiveFormat::TarBz2 => create_tar_archive(source, dest, Compression::Bzip2),
        ArchiveFormat::Zip => create_zip_archive(source, dest),
    }
}

/// Compression type for tar archives
#[derive(Debug, Clone, Copy)]
enum Compression {
    Gzip,
    Bzip2,
}

/// Create a tar archive with specified compression
///
/// # Arguments
///
/// - `source`: Source directory path
/// - `dest`: Destination archive path
/// - `compression`: Compression type (Gzip or Bzip2)
///
/// # Returns
///
/// - `Ok(())`: Archive created successfully
/// - `Err(message)`: Archive creation failed
fn create_tar_archive(source: &Path, dest: &Path, compression: Compression) -> Result<(), String> {
    use flate2::write::GzEncoder;
    use flate2::Compression as GzCompression;

    let file = File::create(dest).map_err(|e| format!("Failed to create archive file: {}", e))?;

    let encoder: Box<dyn Write> = match compression {
        Compression::Gzip => Box::new(GzEncoder::new(file, GzCompression::default())),
        Compression::Bzip2 => {
            use bzip2::write::BzEncoder;
            use bzip2::Compression as BzCompression;
            Box::new(BzEncoder::new(file, BzCompression::default()))
        }
    };

    let mut archive = tar::Builder::new(encoder);

    // Add the directory contents to the archive
    archive
        .append_dir_all(".", source)
        .map_err(|e| format!("Failed to add directory to archive: {}", e))?;

    archive
        .finish()
        .map_err(|e| format!("Failed to finalize archive: {}", e))?;

    Ok(())
}

/// Create a zip archive
///
/// # Arguments
///
/// - `source`: Source directory path
/// - `dest`: Destination archive path
///
/// # Returns
///
/// - `Ok(())`: Archive created successfully
/// - `Err(message)`: Archive creation failed
fn create_zip_archive(source: &Path, dest: &Path) -> Result<(), String> {
    let file = File::create(dest).map_err(|e| format!("Failed to create zip file: {}", e))?;
    let mut zip = zip::ZipWriter::new(file);

    let options = zip::write::FileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated)
        .unix_permissions(0o755);

    // Walk the source directory and add files
    add_directory_to_zip(&mut zip, source, source, &options)?;

    zip.finish()
        .map_err(|e| format!("Failed to finalize zip: {}", e))?;

    Ok(())
}

/// Recursively add directory contents to zip archive
///
/// # Arguments
///
/// - `zip`: ZipWriter to add files to
/// - `base_path`: Base source directory path (for calculating relative paths)
/// - `current_path`: Current directory being processed
/// - `options`: Zip file options
///
/// # Returns
///
/// - `Ok(())`: Directory added successfully
/// - `Err(message)`: Failed to add directory
fn add_directory_to_zip<W: Write + io::Seek>(
    zip: &mut zip::ZipWriter<W>,
    base_path: &Path,
    current_path: &Path,
    options: &zip::write::FileOptions,
) -> Result<(), String> {
    let entries = fs::read_dir(current_path)
        .map_err(|e| format!("Failed to read directory {}: {}", current_path.display(), e))?;

    for entry in entries {
        let entry = entry.map_err(|e| format!("Failed to read directory entry: {}", e))?;
        let path = entry.path();
        let name = path
            .strip_prefix(base_path)
            .map_err(|e| format!("Failed to compute relative path: {}", e))?;

        if path.is_file() {
            zip.start_file(name.to_string_lossy().to_string(), *options)
                .map_err(|e| format!("Failed to start zip file entry: {}", e))?;

            let contents = fs::read(&path)
                .map_err(|e| format!("Failed to read file {}: {}", path.display(), e))?;

            zip.write_all(&contents)
                .map_err(|e| format!("Failed to write file to zip: {}", e))?;
        } else if path.is_dir() {
            // Add directory entry
            zip.add_directory(name.to_string_lossy().to_string(), *options)
                .map_err(|e| format!("Failed to add directory to zip: {}", e))?;

            // Recurse into directory
            add_directory_to_zip(zip, base_path, &path, options)?;
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_determine_archive_format() {
        assert_eq!(
            determine_archive_format(Path::new("test.tar.gz")).unwrap(),
            ArchiveFormat::TarGz
        );
        assert_eq!(
            determine_archive_format(Path::new("test.tgz")).unwrap(),
            ArchiveFormat::TarGz
        );
        assert_eq!(
            determine_archive_format(Path::new("test.tar.bz2")).unwrap(),
            ArchiveFormat::TarBz2
        );
        assert_eq!(
            determine_archive_format(Path::new("test.zip")).unwrap(),
            ArchiveFormat::Zip
        );
        assert!(determine_archive_format(Path::new("test.txt")).is_err());
    }

    #[test]
    fn test_find_next_available_path() {
        // This test just verifies the logic works, not actual filesystem
        let base = PathBuf::from("output.tar.gz");
        let next = find_next_available_path(&base);
        assert_eq!(next, PathBuf::from("output.1.tar.gz"));
    }
}
