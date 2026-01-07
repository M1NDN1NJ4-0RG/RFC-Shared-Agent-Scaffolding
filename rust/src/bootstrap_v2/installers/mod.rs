//! # Concrete Installer Implementations
//!
//! This module contains specific installer implementations for tools.
//!
//! # Purpose
//!
//! Provides concrete implementations of the Installer trait for various development tools.
//! Includes system package installers (ripgrep) and Python venv-based tools (black, ruff, pylint).
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::installers::InstallerRegistry;
//!
//! let registry = InstallerRegistry::new();
//! let installers = registry.resolve_dependencies(&["ripgrep", "python-black"]).unwrap();
//! ```

pub mod actionlint;
pub mod perl_tools;
pub mod powershell_tools;
pub mod python_tools;
pub mod repo_lint;
pub mod ripgrep;
pub mod shellcheck;
pub mod shfmt;

use crate::bootstrap_v2::errors::BootstrapResult;
use crate::bootstrap_v2::installer::Installer;
use std::collections::HashMap;
use std::sync::Arc;

/// Installer registry
pub struct InstallerRegistry {
    installers: HashMap<&'static str, Arc<dyn Installer>>,
}

impl InstallerRegistry {
    /// Create new registry with all installers
    pub fn new() -> Self {
        let mut registry = Self {
            installers: HashMap::new(),
        };

        // Register all installers
        registry.register(Arc::new(repo_lint::RepoLintInstaller));
        registry.register(Arc::new(ripgrep::RipgrepInstaller));
        registry.register(Arc::new(python_tools::BlackInstaller));
        registry.register(Arc::new(python_tools::RuffInstaller));
        registry.register(Arc::new(python_tools::PylintInstaller));
        registry.register(Arc::new(python_tools::YamllintInstaller));
        registry.register(Arc::new(python_tools::PytestInstaller));
        registry.register(Arc::new(actionlint::ActionlintInstaller));
        registry.register(Arc::new(shellcheck::ShellcheckInstaller));
        registry.register(Arc::new(shfmt::ShfmtInstaller));
        registry.register(Arc::new(perl_tools::PerlCriticInstaller));
        registry.register(Arc::new(perl_tools::PPIInstaller));
        registry.register(Arc::new(powershell_tools::PwshInstaller));
        registry.register(Arc::new(powershell_tools::PSScriptAnalyzerInstaller));

        registry
    }

    /// Register an installer
    pub fn register(&mut self, installer: Arc<dyn Installer>) {
        self.installers.insert(installer.id(), installer);
    }

    /// Get installer by ID
    pub fn get(&self, id: &str) -> Option<&Arc<dyn Installer>> {
        self.installers.get(id)
    }

    /// Resolve dependencies (returns installers in dependency order)
    pub fn resolve_dependencies(&self, ids: &[&str]) -> BootstrapResult<Vec<Arc<dyn Installer>>> {
        let mut resolved = Vec::new();
        let mut visited = std::collections::HashSet::new();

        for &id in ids {
            self.resolve_deps_recursive(id, &mut resolved, &mut visited)?;
        }

        Ok(resolved)
    }

    fn resolve_deps_recursive(
        &self,
        id: &str,
        resolved: &mut Vec<Arc<dyn Installer>>,
        visited: &mut std::collections::HashSet<String>,
    ) -> BootstrapResult<()> {
        if visited.contains(id) {
            return Ok(());
        }

        let installer = self.get(id).ok_or_else(|| {
            crate::bootstrap_v2::errors::BootstrapError::ToolNotFound(id.to_string())
        })?;

        // Resolve dependencies first
        for dep in installer.dependencies() {
            self.resolve_deps_recursive(dep, resolved, visited)?;
        }

        visited.insert(id.to_string());
        resolved.push(Arc::clone(installer));

        Ok(())
    }
}

impl Default for InstallerRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_registry_creation() {
        let registry = InstallerRegistry::new();
        assert!(registry.get("ripgrep").is_some());
        assert!(registry.get("nonexistent").is_none());
    }

    #[test]
    fn test_dependency_resolution() {
        let registry = InstallerRegistry::new();
        let resolved = registry
            .resolve_dependencies(&["ripgrep", "python-black"])
            .unwrap();
        assert!(!resolved.is_empty());
    }
}
