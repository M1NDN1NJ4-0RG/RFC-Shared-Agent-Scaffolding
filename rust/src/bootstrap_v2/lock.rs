//! # Resource Locking
//!
//! Lock manager for shared resources (apt, brew, cache, venv).

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Semaphore;

/// Lock names
pub const BREW_LOCK: &str = "brew_lock";
pub const APT_LOCK: &str = "apt_lock";
pub const CACHE_LOCK: &str = "cache_lock";
pub const VENV_LOCK: &str = "venv_lock";

/// Lock manager
#[derive(Clone)]
pub struct LockManager {
    #[allow(dead_code)] // Will be used in later phases
    locks: Arc<HashMap<String, Arc<Semaphore>>>,
}

impl LockManager {
    /// Create new lock manager
    pub fn new() -> Self {
        let mut locks = HashMap::new();
        locks.insert(BREW_LOCK.to_string(), Arc::new(Semaphore::new(1)));
        locks.insert(APT_LOCK.to_string(), Arc::new(Semaphore::new(1)));
        locks.insert(CACHE_LOCK.to_string(), Arc::new(Semaphore::new(1)));
        locks.insert(VENV_LOCK.to_string(), Arc::new(Semaphore::new(1)));

        Self {
            locks: Arc::new(locks),
        }
    }
}

impl Default for LockManager {
    fn default() -> Self {
        Self::new()
    }
}
