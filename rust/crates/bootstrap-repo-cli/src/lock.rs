//! # Resource Locking
//!
//! Lock manager for shared resources (apt, brew, cache, venv).
//!
//! # Purpose
//!
//! Provides lock management with timeout and exponential backoff for shared resources.
//! Prevents concurrent access to package managers and other shared resources.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::lock::{LockManager, BREW_LOCK};
//! use std::time::Duration;
//!
//! # async fn example() {
//! let manager = LockManager::new();
//! let guard = manager.acquire(BREW_LOCK, Duration::from_secs(60), true).await.unwrap();
//! // Critical section - brew is locked
//! drop(guard); // Release lock
//! # }
//! ```

use crate::errors::{BootstrapError, BootstrapResult};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Semaphore, SemaphorePermit};
use tokio::time::sleep;

/// Lock names
pub const BREW_LOCK: &str = "brew_lock";
pub const APT_LOCK: &str = "apt_lock";
pub const CACHE_LOCK: &str = "cache_lock";
pub const VENV_LOCK: &str = "venv_lock";
pub const PACKAGE_MANAGER_LOCK: &str = "package_manager_lock";

/// Lock guard - automatically releases lock when dropped
pub struct LockGuard<'a> {
    _permit: SemaphorePermit<'a>,
    lock_name: String,
}

impl<'a> LockGuard<'a> {
    /// Get lock name
    pub fn lock_name(&self) -> &str {
        &self.lock_name
    }
}

/// Lock manager
#[derive(Clone)]
pub struct LockManager {
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
        locks.insert(
            PACKAGE_MANAGER_LOCK.to_string(),
            Arc::new(Semaphore::new(1)),
        );

        Self {
            locks: Arc::new(locks),
        }
    }

    /// Acquire a lock with timeout and exponential backoff
    ///
    /// # Arguments
    /// * `lock_name` - Name of the lock to acquire
    /// * `max_wait` - Maximum time to wait for lock
    /// * `ci_mode` - Whether in CI mode (affects max wait time)
    pub async fn acquire<'a>(
        &'a self,
        lock_name: &str,
        max_wait: Duration,
        ci_mode: bool,
    ) -> BootstrapResult<LockGuard<'a>> {
        let semaphore = self
            .locks
            .get(lock_name)
            .ok_or_else(|| BootstrapError::ConfigError(format!("Unknown lock: {}", lock_name)))?;

        let started = Instant::now();
        let mut timeout_duration = Duration::from_millis(100);
        let max_timeout = Duration::from_secs(2);

        // Adjust max wait based on CI mode
        let effective_max_wait = if ci_mode {
            Duration::from_secs(60) // CI: 60s max
        } else {
            max_wait.min(Duration::from_secs(180)) // Interactive: 180s max
        };

        loop {
            // Try to acquire the lock with timeout
            match tokio::time::timeout(timeout_duration, semaphore.acquire()).await {
                Ok(Ok(permit)) => {
                    return Ok(LockGuard {
                        _permit: permit,
                        lock_name: lock_name.to_string(),
                    });
                }
                Ok(Err(_)) => {
                    // Semaphore closed (shouldn't happen)
                    return Err(BootstrapError::ConfigError(format!(
                        "Lock {} is closed",
                        lock_name
                    )));
                }
                Err(_) => {
                    // Timeout - check if we should continue waiting
                    if started.elapsed() >= effective_max_wait {
                        return Err(BootstrapError::ConfigError(format!(
                            "Timeout waiting for lock {} after {:?}",
                            lock_name,
                            started.elapsed()
                        )));
                    }

                    // Sleep with backoff before next attempt
                    let backoff_delay = timeout_duration.min(max_timeout);
                    sleep(backoff_delay).await;

                    // Exponential backoff for next timeout
                    timeout_duration = (timeout_duration * 2).min(max_timeout);
                }
            }
        }
    }

    /// Try to acquire a lock without waiting
    pub async fn try_acquire<'a>(&'a self, lock_name: &str) -> BootstrapResult<LockGuard<'a>> {
        let semaphore = self
            .locks
            .get(lock_name)
            .ok_or_else(|| BootstrapError::ConfigError(format!("Unknown lock: {}", lock_name)))?;

        match semaphore.try_acquire() {
            Ok(permit) => Ok(LockGuard {
                _permit: permit,
                lock_name: lock_name.to_string(),
            }),
            Err(_) => Err(BootstrapError::ConfigError(format!(
                "Lock {} is currently held",
                lock_name
            ))),
        }
    }
}

impl Default for LockManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_lock_acquire_release() {
        let manager = LockManager::new();

        // Acquire lock
        let guard = manager
            .acquire(BREW_LOCK, Duration::from_secs(1), false)
            .await
            .unwrap();

        assert_eq!(guard.lock_name(), BREW_LOCK);

        // Drop guard to release lock
        drop(guard);

        // Should be able to acquire again
        let guard2 = manager
            .acquire(BREW_LOCK, Duration::from_secs(1), false)
            .await
            .unwrap();
        assert_eq!(guard2.lock_name(), BREW_LOCK);
    }

    #[tokio::test]
    async fn test_lock_contention() {
        let manager = LockManager::new();

        // Acquire lock in one task
        let _guard = manager
            .try_acquire(BREW_LOCK)
            .await
            .expect("Should acquire lock");

        // Try to acquire in same context (should fail immediately)
        let result = manager.try_acquire(BREW_LOCK).await;
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_unknown_lock() {
        let manager = LockManager::new();

        let result = manager
            .acquire("unknown_lock", Duration::from_secs(1), false)
            .await;
        assert!(result.is_err());
    }
}
