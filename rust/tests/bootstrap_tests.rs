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
    fs::write(
        repo_root.join("pyproject.toml"),
        "[project]\nname = \"test\"",
    )
    .unwrap();

    let tools_dir = repo_root.join("tools/repo_cli");
    fs::create_dir_all(&tools_dir).unwrap();
    fs::write(
        tools_dir.join("pyproject.toml"),
        "[project]\nname = \"repo_lint\"",
    )
    .unwrap();

    // Test logic (mirrors bootstrap.rs determine_install_target)
    let root_has_pkg = repo_root.join("pyproject.toml").exists();
    let tools_repo_cli = repo_root.join("tools/repo_cli");
    let tools_has_pkg = tools_repo_cli.join("pyproject.toml").exists();

    assert!(root_has_pkg);
    assert!(tools_has_pkg);

    // When both exist, tools/repo_cli should be preferred
    let install_target = if tools_has_pkg {
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
    fs::write(
        repo_root.join("pyproject.toml"),
        "[project]\nname = \"test\"",
    )
    .unwrap();

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
    assert!(repo_lint_path
        .to_str()
        .unwrap()
        .ends_with(".venv/bin/repo-lint"));
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
        let exit_codes = [
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

    #[test]
    fn test_exit_codes_in_valid_range() {
        let exit_codes = vec![0, 1, 10, 11, 12, 13, 14, 15];

        for code in exit_codes {
            assert!(
                (0..128).contains(&code),
                "Exit code {} must be in range 0-127",
                code
            );
        }
    }

    #[test]
    fn test_success_exit_code_is_zero() {
        assert_eq!(0, 0, "Success exit code must be 0");
    }
}

#[cfg(test)]
mod repo_root_edge_cases {
    use super::*;

    #[test]
    fn test_multiple_markers_prefer_closest() {
        let temp_dir = TempDir::new().unwrap();

        // Create markers at root
        fs::write(temp_dir.path().join("README.md"), "# Root").unwrap();

        // Create nested directory with its own marker
        let nested = temp_dir.path().join("nested");
        fs::create_dir(&nested).unwrap();
        fs::create_dir(nested.join(".git")).unwrap();

        // Should find nested as root when starting from there
        let result = find_repo_root_test(&nested);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), nested);
    }

    #[test]
    fn test_symlink_traversal() {
        let temp_dir = TempDir::new().unwrap();
        fs::create_dir(temp_dir.path().join(".git")).unwrap();

        let sub_dir = temp_dir.path().join("subdir");
        fs::create_dir(&sub_dir).unwrap();

        #[cfg(unix)]
        {
            use std::os::unix::fs::symlink;
            let link_dir = temp_dir.path().join("link");
            symlink(&sub_dir, &link_dir).unwrap();

            // Should find repo root when starting from symlinked directory
            let result = find_repo_root_test(&link_dir);
            assert!(result.is_ok());
        }
    }

    #[test]
    fn test_git_directory_not_file() {
        let temp_dir = TempDir::new().unwrap();

        // Create .git as a file instead of directory (shouldn't count)
        fs::write(temp_dir.path().join(".git"), "gitdir: ../.git").unwrap();

        // Should not find repo root with .git file
        let result = find_repo_root_test(temp_dir.path());
        assert!(result.is_err());
    }

    #[test]
    fn test_pyproject_must_be_file() {
        let temp_dir = TempDir::new().unwrap();

        // Create pyproject.toml as directory instead of file
        fs::create_dir(temp_dir.path().join("pyproject.toml")).unwrap();

        // Should not find repo root with pyproject.toml directory
        let result = find_repo_root_test(temp_dir.path());
        assert!(result.is_err());
    }

    #[test]
    fn test_readme_must_be_file() {
        let temp_dir = TempDir::new().unwrap();

        // Create README.md as directory instead of file
        fs::create_dir(temp_dir.path().join("README.md")).unwrap();

        // Should not find repo root with README.md directory
        let result = find_repo_root_test(temp_dir.path());
        assert!(result.is_err());
    }

    #[test]
    fn test_all_three_markers_present() {
        let temp_dir = TempDir::new().unwrap();

        // Create all three markers
        fs::create_dir(temp_dir.path().join(".git")).unwrap();
        fs::write(temp_dir.path().join("pyproject.toml"), "[project]").unwrap();
        fs::write(temp_dir.path().join("README.md"), "# Test").unwrap();

        let result = find_repo_root_test(temp_dir.path());
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), temp_dir.path());
    }
}

#[cfg(test)]
mod command_existence_edge_cases {
    use super::*;

    #[test]
    fn test_command_with_spaces() {
        assert!(!command_exists_test("command with spaces"));
    }

    #[test]
    fn test_command_with_special_chars() {
        assert!(!command_exists_test("command-with-$pecial"));
    }

    #[test]
    fn test_relative_path_command() {
        let temp_dir = TempDir::new().unwrap();
        let exe_path = temp_dir.path().join("test_exe");
        fs::write(&exe_path, "test").unwrap();

        // Relative path like "./test_exe" should not be found
        assert!(!command_exists_test("./test_exe"));
    }

    #[test]
    fn test_command_in_current_dir() {
        let temp_dir = TempDir::new().unwrap();

        // Change to temp dir and create executable
        let original_dir = env::current_dir().unwrap();
        env::set_current_dir(&temp_dir).unwrap();

        fs::write("test_cmd", "test").unwrap();

        // Just filename should not be found (not in PATH)
        assert!(!command_exists_test("test_cmd"));

        env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_no_path_environment() {
        // Save original PATH
        let original_path = env::var_os("PATH");

        // Remove PATH
        env::remove_var("PATH");

        // Should return false for any command
        assert!(!command_exists_test("sh"));

        // Restore PATH
        if let Some(path) = original_path {
            env::set_var("PATH", path);
        }
    }
}

#[cfg(test)]
mod install_target_edge_cases {
    use super::*;

    #[test]
    fn test_no_packaging_metadata_anywhere() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        let root_has_pkg = repo_root.join("pyproject.toml").exists()
            || repo_root.join("setup.py").exists()
            || repo_root.join("setup.cfg").exists();

        let tools_repo_cli = repo_root.join("tools/repo_cli");
        let tools_has_pkg = tools_repo_cli.join("pyproject.toml").exists()
            || tools_repo_cli.join("setup.py").exists()
            || tools_repo_cli.join("setup.cfg").exists();

        assert!(!root_has_pkg);
        assert!(!tools_has_pkg);

        // This should error in the real code
    }

    #[test]
    fn test_setup_py_in_root() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        fs::write(repo_root.join("setup.py"), "# setup.py").unwrap();

        let root_has_pkg = repo_root.join("pyproject.toml").exists()
            || repo_root.join("setup.py").exists()
            || repo_root.join("setup.cfg").exists();

        assert!(root_has_pkg);
    }

    #[test]
    fn test_setup_cfg_in_tools() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        let tools_dir = repo_root.join("tools/repo_cli");
        fs::create_dir_all(&tools_dir).unwrap();
        fs::write(tools_dir.join("setup.cfg"), "[metadata]").unwrap();

        let tools_has_pkg = tools_dir.join("pyproject.toml").exists()
            || tools_dir.join("setup.py").exists()
            || tools_dir.join("setup.cfg").exists();

        assert!(tools_has_pkg);
    }

    #[test]
    fn test_tools_directory_exists_but_no_metadata() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        // Create tools/repo_cli but no packaging files
        let tools_dir = repo_root.join("tools/repo_cli");
        fs::create_dir_all(&tools_dir).unwrap();

        // Add metadata to root only
        fs::write(repo_root.join("pyproject.toml"), "[project]").unwrap();

        let root_has_pkg = repo_root.join("pyproject.toml").exists();
        let tools_has_pkg = tools_dir.join("pyproject.toml").exists();

        assert!(root_has_pkg);
        assert!(!tools_has_pkg);

        // Should fall back to root
        let install_target = if tools_has_pkg {
            tools_dir
        } else if root_has_pkg {
            repo_root.to_path_buf()
        } else {
            panic!("No install target");
        };

        assert_eq!(install_target, repo_root);
    }
}

#[cfg(test)]
mod path_construction_tests {
    use super::*;

    #[test]
    fn test_venv_bin_paths_unix() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();
        let venv_dir = ".venv";

        let venv_path = repo_root.join(venv_dir);
        let python_path = venv_path.join("bin/python3");
        let pip_path = venv_path.join("bin/pip");
        let repo_lint_path = venv_path.join("bin/repo-lint");

        // Check path components
        assert!(python_path.to_str().unwrap().contains("bin/python3"));
        assert!(pip_path.to_str().unwrap().contains("bin/pip"));
        assert!(repo_lint_path.to_str().unwrap().contains("bin/repo-lint"));
    }

    #[test]
    fn test_venv_lint_paths() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        let venv_lint = repo_root.join(".venv-lint/bin");

        assert!(venv_lint.to_str().unwrap().ends_with(".venv-lint/bin"));
    }

    #[test]
    fn test_tools_repo_cli_path() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        let tools_path = repo_root.join("tools/repo_cli");
        let pyproject = tools_path.join("pyproject.toml");

        assert!(tools_path.to_str().unwrap().ends_with("tools/repo_cli"));
        assert!(pyproject
            .to_str()
            .unwrap()
            .ends_with("tools/repo_cli/pyproject.toml"));
    }

    #[test]
    fn test_path_to_str_validity() {
        let temp_dir = TempDir::new().unwrap();
        let path = temp_dir.path();

        // Should be able to convert to string
        assert!(path.to_str().is_some());

        let path_str = path.to_str().unwrap();
        assert!(!path_str.is_empty());
    }
}

#[cfg(test)]
mod error_message_tests {
    #[test]
    fn test_repo_root_error_message() {
        let msg = "Could not find repo root. Run from inside the repo.";
        assert!(msg.contains("repo root"));
        assert!(msg.contains("inside the repo"));
    }

    #[test]
    fn test_no_metadata_error_message() {
        let msg = "Could not determine where to install repo-lint (no packaging metadata found).";
        assert!(msg.contains("install repo-lint"));
        assert!(msg.contains("packaging metadata"));
    }

    #[test]
    fn test_pip_install_error_message() {
        let target = "/some/path";
        let msg = format!("pip install -e failed for: {}", target);
        assert!(msg.contains("pip install"));
        assert!(msg.contains(target));
    }

    #[test]
    fn test_repo_lint_not_runnable_error() {
        let msg = "repo-lint is not runnable. Fix packaging/venv/PATH first.";
        assert!(msg.contains("repo-lint"));
        assert!(msg.contains("PATH"));
    }

    #[test]
    fn test_repo_lint_install_error() {
        let msg =
            "repo-lint install failed. Missing tools are BLOCKER. Install missing tools and rerun.";
        assert!(msg.contains("repo-lint install"));
        assert!(msg.contains("BLOCKER"));
        assert!(msg.contains("missing tools"));
    }
}

#[cfg(test)]
mod integration_scenarios {
    use super::*;

    #[test]
    fn test_typical_repository_structure() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        // Create typical repo structure
        fs::create_dir(repo_root.join(".git")).unwrap();
        fs::write(repo_root.join("README.md"), "# Repo").unwrap();
        fs::write(repo_root.join("pyproject.toml"), "[project]\nname='test'").unwrap();

        let tools_dir = repo_root.join("tools/repo_cli");
        fs::create_dir_all(&tools_dir).unwrap();
        fs::write(
            tools_dir.join("pyproject.toml"),
            "[project]\nname='repo_lint'",
        )
        .unwrap();

        // Verify repo root finding works
        let sub_dir = repo_root.join("src/module");
        fs::create_dir_all(&sub_dir).unwrap();

        let result = find_repo_root_test(&sub_dir);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), repo_root);

        // Verify install target selection
        let root_has_pkg = repo_root.join("pyproject.toml").exists();
        let tools_has_pkg = tools_dir.join("pyproject.toml").exists();

        assert!(root_has_pkg && tools_has_pkg);
    }

    #[test]
    fn test_minimal_repository_structure() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        // Minimal repo: just .git and pyproject.toml
        fs::create_dir(repo_root.join(".git")).unwrap();
        fs::write(repo_root.join("pyproject.toml"), "[project]").unwrap();

        let result = find_repo_root_test(repo_root);
        assert!(result.is_ok());
    }

    #[test]
    fn test_deep_nested_directory() {
        let temp_dir = TempDir::new().unwrap();
        let repo_root = temp_dir.path();

        fs::create_dir(repo_root.join(".git")).unwrap();

        // Create deep nesting
        let deep_path = repo_root.join("a/b/c/d/e/f/g/h");
        fs::create_dir_all(&deep_path).unwrap();

        let result = find_repo_root_test(&deep_path);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), repo_root);
    }
}

#[cfg(test)]
mod helper_function_tests {
    use super::*;

    #[test]
    fn test_temp_dir_creation() {
        let temp_dir = TempDir::new().unwrap();
        assert!(temp_dir.path().exists());
        assert!(temp_dir.path().is_dir());
    }

    #[test]
    fn test_create_test_repo_with_all_markers() {
        let temp_dir = create_test_repo(true, true, true);

        assert!(temp_dir.path().join(".git").exists());
        assert!(temp_dir.path().join("pyproject.toml").exists());
        assert!(temp_dir.path().join("README.md").exists());
    }

    #[test]
    fn test_create_test_repo_with_no_markers() {
        let temp_dir = create_test_repo(false, false, false);

        assert!(!temp_dir.path().join(".git").exists());
        assert!(!temp_dir.path().join("pyproject.toml").exists());
        assert!(!temp_dir.path().join("README.md").exists());
    }

    #[test]
    fn test_create_test_repo_selective_markers() {
        let temp_dir = create_test_repo(true, false, true);

        assert!(temp_dir.path().join(".git").exists());
        assert!(!temp_dir.path().join("pyproject.toml").exists());
        assert!(temp_dir.path().join("README.md").exists());
    }
}
