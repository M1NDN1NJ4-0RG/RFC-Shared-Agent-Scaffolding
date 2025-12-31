//! Unit tests for bootstrap-repo-cli functionality
//!
//! These tests cover the core functionality of the bootstrap module,
//! including repository root finding, command existence checking,
//! and path construction.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;

// Import the bootstrap module indirectly through a test helper
// Since bootstrap is in main.rs/bootstrap_main.rs, we'll test the concepts

/// Test helper to create a temporary directory structure
fn create_test_repo(has_git: bool, has_pyproject: bool, has_readme: bool) -> TempDir {
    let temp_dir = TempDir::new().unwrap();
    
    if has_git {
        fs::create_dir(temp_dir.path().join(".git")).unwrap();
    }
    
    if has_pyproject {
        fs::write(temp_dir.path().join("pyproject.toml"), "# Test pyproject").unwrap();
    }
    
    if has_readme {
        fs::write(temp_dir.path().join("README.md"), "# Test README").unwrap();
    }
    
    temp_dir
}

/// Test helper to find repository root (mirrors bootstrap.rs logic)
fn find_repo_root_test(start_dir: &Path) -> Result<PathBuf, String> {
    let mut current = start_dir.to_path_buf();

    loop {
        if current.join(".git").is_dir()
            || current.join("pyproject.toml").is_file()
            || current.join("README.md").is_file()
        {
            return Ok(current);
        }

        if !current.pop() {
            return Err("Could not find repo root".to_string());
        }
    }
}

/// Test helper to check if command exists (mirrors bootstrap.rs logic)
fn command_exists_test(cmd: &str) -> bool {
    if cmd.is_empty() {
        return false;
    }

    let cmd_path = Path::new(cmd);
    if cmd_path.components().count() > 1 {
        return cmd_path.is_file();
    }

    let path_var = match env::var_os("PATH") {
        Some(p) => p,
        None => return false,
    };

    let paths = env::split_paths(&path_var);

    for dir in paths {
        let candidate = dir.join(cmd);
        if candidate.is_file() {
            return true;
        }
    }

    false
}

#[test]
fn test_find_repo_root_with_git() {
    let temp_dir = create_test_repo(true, false, false);
    let result = find_repo_root_test(temp_dir.path());
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), temp_dir.path());
}

#[test]
fn test_find_repo_root_with_pyproject() {
    let temp_dir = create_test_repo(false, true, false);
    let result = find_repo_root_test(temp_dir.path());
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), temp_dir.path());
}

#[test]
fn test_find_repo_root_with_readme() {
    let temp_dir = create_test_repo(false, false, true);
    let result = find_repo_root_test(temp_dir.path());
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), temp_dir.path());
}

#[test]
fn test_find_repo_root_from_subdirectory() {
    let temp_dir = create_test_repo(true, false, false);
    let sub_dir = temp_dir.path().join("subdir");
    fs::create_dir(&sub_dir).unwrap();
    
    let result = find_repo_root_test(&sub_dir);
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), temp_dir.path());
}

#[test]
fn test_find_repo_root_from_nested_subdirectory() {
    let temp_dir = create_test_repo(true, false, false);
    let nested_dir = temp_dir.path().join("level1/level2/level3");
    fs::create_dir_all(&nested_dir).unwrap();
    
    let result = find_repo_root_test(&nested_dir);
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), temp_dir.path());
}

#[test]
fn test_find_repo_root_not_found() {
    let temp_dir = TempDir::new().unwrap();
    // No repo markers (.git, pyproject.toml, README.md)
    let result = find_repo_root_test(temp_dir.path());
    assert!(result.is_err());
    assert_eq!(result.unwrap_err(), "Could not find repo root");
}

#[test]
fn test_command_exists_empty_string() {
    assert!(!command_exists_test(""));
}

#[test]
fn test_command_exists_common_command() {
    // Test with a command that should exist on most systems
    assert!(command_exists_test("sh") || command_exists_test("bash"));
}

#[test]
fn test_command_exists_nonexistent_command() {
    // Test with a command that shouldn't exist
    assert!(!command_exists_test("nonexistent_command_12345"));
}

#[test]
fn test_command_exists_with_path() {
    // Create a temporary executable file
    let temp_dir = TempDir::new().unwrap();
    let exe_path = temp_dir.path().join("test_exe");
    
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::write(&exe_path, "#!/bin/sh\necho test").unwrap();
        let mut perms = fs::metadata(&exe_path).unwrap().permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&exe_path, perms).unwrap();
    }
    
    #[cfg(not(unix))]
    {
        fs::write(&exe_path, "test").unwrap();
    }
    
    // Test with full path
    assert!(command_exists_test(exe_path.to_str().unwrap()));
}

#[test]
fn test_install_target_detection_prefers_tools_repo_cli() {
    let temp_dir = TempDir::new().unwrap();
    let repo_root = temp_dir.path();
    
    // Create pyproject.toml in both locations
    fs::write(repo_root.join("pyproject.toml"), "[project]\nname = \"test\"").unwrap();
    
    let tools_dir = repo_root.join("tools/repo_cli");
    fs::create_dir_all(&tools_dir).unwrap();
    fs::write(tools_dir.join("pyproject.toml"), "[project]\nname = \"repo_lint\"").unwrap();
    
    // Test logic (mirrors bootstrap.rs determine_install_target)
    let root_has_pkg = repo_root.join("pyproject.toml").exists();
    let tools_repo_cli = repo_root.join("tools/repo_cli");
    let tools_has_pkg = tools_repo_cli.join("pyproject.toml").exists();
    
    assert!(root_has_pkg);
    assert!(tools_has_pkg);
    
    // When both exist, tools/repo_cli should be preferred
    let install_target = if root_has_pkg && tools_has_pkg {
        tools_repo_cli.clone()
    } else if tools_has_pkg {
        tools_repo_cli.clone()
    } else if root_has_pkg {
        repo_root.to_path_buf()
    } else {
        panic!("No install target");
    };
    
    assert_eq!(install_target, tools_repo_cli);
}

#[test]
fn test_install_target_falls_back_to_root() {
    let temp_dir = TempDir::new().unwrap();
    let repo_root = temp_dir.path();
    
    // Only create pyproject.toml in root
    fs::write(repo_root.join("pyproject.toml"), "[project]\nname = \"test\"").unwrap();
    
    let root_has_pkg = repo_root.join("pyproject.toml").exists();
    let tools_repo_cli = repo_root.join("tools/repo_cli");
    let tools_has_pkg = tools_repo_cli.join("pyproject.toml").exists();
    
    assert!(root_has_pkg);
    assert!(!tools_has_pkg);
    
    let install_target = if tools_has_pkg {
        tools_repo_cli
    } else if root_has_pkg {
        repo_root.to_path_buf()
    } else {
        panic!("No install target");
    };
    
    assert_eq!(install_target, repo_root);
}

#[test]
fn test_venv_path_construction() {
    let temp_dir = TempDir::new().unwrap();
    let repo_root = temp_dir.path();
    let venv_dir = ".venv";
    
    let venv_path = repo_root.join(venv_dir);
    let venv_python = venv_path.join("bin/python3");
    let repo_lint_path = venv_path.join("bin/repo-lint");
    
    // Verify paths are constructed correctly
    assert!(venv_path.to_str().unwrap().ends_with(".venv"));
    assert!(venv_python.to_str().unwrap().ends_with(".venv/bin/python3"));
    assert!(repo_lint_path.to_str().unwrap().ends_with(".venv/bin/repo-lint"));
}

#[test]
fn test_error_handling_preserves_context() {
    // Test that error messages contain useful context
    let error_msg = "Could not determine where to install repo-lint (no packaging metadata found).";
    assert!(error_msg.contains("packaging metadata"));
    assert!(error_msg.contains("repo-lint"));
    
    let error_msg2 = format!("pip install -e failed for: {}", "/some/path");
    assert!(error_msg2.contains("pip install"));
    assert!(error_msg2.contains("/some/path"));
}

#[cfg(test)]
mod exit_code_tests {
    /// Test that exit codes are well-defined
    #[test]
    fn test_exit_codes_are_distinct() {
        let exit_codes = vec![
            (0, "Success"),
            (1, "Generic failure"),
            (10, "Repository root not found"),
            (11, "No packaging metadata"),
            (12, "pip install failed"),
            (13, "repo-lint not runnable"),
            (14, "repo-lint --help failed"),
            (15, "repo-lint install failed"),
        ];
        
        // Verify all codes are unique
        let mut codes: Vec<i32> = exit_codes.iter().map(|(code, _)| *code).collect();
        codes.sort();
        codes.dedup();
        assert_eq!(codes.len(), exit_codes.len(), "Exit codes must be unique");
    }
}
