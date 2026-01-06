//! # Retry Strategy
//!
//! Retry policies with exponential backoff and classification.
//!
//! # Purpose
//!
//! Provides retry logic with error classification to avoid retrying permanent failures.
//! Implements exponential backoff with jitter and total time budget.
//!
//! # Examples
//!
//! ```no_run
//! use bootstrap_v2::retry::{RetryPolicy, retry_with_backoff};
//! use bootstrap_v2::errors::BootstrapResult;
//!
//! # async fn example() -> BootstrapResult<()> {
//! let policy = RetryPolicy::network_default();
//! let result = retry_with_backoff(&policy, || async {
//!     // Potentially failing operation
//!     Ok::<_, anyhow::Error>(())
//! }).await?;
//! # Ok(())
//! # }
//! ```

use crate::bootstrap_v2::errors::BootstrapError;
use anyhow::Result;
use rand::Rng;
use std::future::Future;
use std::time::{Duration, Instant};

#[cfg(test)]
use std::sync::{Arc, Mutex};

/// Retry classification
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RetryClass {
    /// Transient error (safe to retry)
    Transient,

    /// Permanent error (do not retry)
    Permanent,

    /// Security error (checksum/signature mismatch)
    Security,

    /// Unsafe to retry (non-idempotent)
    Unsafe,
}

/// Retry policy
#[derive(Debug, Clone)]
pub struct RetryPolicy {
    /// Maximum retry attempts
    pub max_attempts: u32,

    /// Initial delay
    pub initial_delay: Duration,

    /// Maximum delay
    pub max_delay: Duration,

    /// Maximum total time
    pub max_total_time: Duration,

    /// Add jitter
    pub jitter: bool,
}

impl RetryPolicy {
    /// Default policy for network operations
    pub fn network_default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_secs(1),
            max_delay: Duration::from_secs(30),
            max_total_time: Duration::from_secs(60),
            jitter: true,
        }
    }

    /// Conservative policy for package manager operations
    pub fn package_manager_default() -> Self {
        Self {
            max_attempts: 2,
            initial_delay: Duration::from_secs(2),
            max_delay: Duration::from_secs(10),
            max_total_time: Duration::from_secs(30),
            jitter: false,
        }
    }
}

/// Classify error to determine if retry is appropriate
pub fn classify_error(error: &anyhow::Error) -> RetryClass {
    // Check if it's a BootstrapError
    if let Some(bootstrap_err) = error.downcast_ref::<BootstrapError>() {
        match bootstrap_err {
            BootstrapError::ChecksumMismatch { .. } => RetryClass::Security,
            BootstrapError::HttpError(_) => RetryClass::Transient,
            BootstrapError::ConfigError(_) => RetryClass::Permanent,
            BootstrapError::NotInRepo => RetryClass::Permanent,
            BootstrapError::NoPackageManager(_) => RetryClass::Permanent,
            _ => RetryClass::Permanent, // Conservative: don't retry by default
        }
    } else if let Some(io_err) = error.downcast_ref::<std::io::Error>() {
        match io_err.kind() {
            std::io::ErrorKind::TimedOut
            | std::io::ErrorKind::ConnectionReset
            | std::io::ErrorKind::ConnectionAborted
            | std::io::ErrorKind::ConnectionRefused => RetryClass::Transient,
            std::io::ErrorKind::NotFound
            | std::io::ErrorKind::PermissionDenied
            | std::io::ErrorKind::InvalidInput => RetryClass::Permanent,
            _ => RetryClass::Permanent, // Conservative
        }
    } else {
        // Unknown error type - don't retry
        RetryClass::Permanent
    }
}

/// Retry an operation with exponential backoff
pub async fn retry_with_backoff<F, Fut, T>(policy: &RetryPolicy, mut operation: F) -> Result<T>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T>>,
{
    let mut attempts = 0;
    let mut delay = policy.initial_delay;
    let started = Instant::now();

    loop {
        attempts += 1;

        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts >= policy.max_attempts => {
                return Err(e);
            }
            Err(e) => {
                // Classify the error
                match classify_error(&e) {
                    RetryClass::Transient => {
                        // Continue with retry
                    }
                    RetryClass::Permanent | RetryClass::Security | RetryClass::Unsafe => {
                        // Don't retry these errors
                        return Err(e);
                    }
                }

                // Check total time budget
                if started.elapsed() >= policy.max_total_time {
                    return Err(anyhow::anyhow!(
                        "Retry timeout exceeded after {:?}: {}",
                        started.elapsed(),
                        e
                    ));
                }

                // Add jitter if enabled
                let actual_delay = if policy.jitter {
                    let jitter_factor = 1.0 + (rand::thread_rng().gen::<f64>() * 0.3);
                    Duration::from_secs_f64(delay.as_secs_f64() * jitter_factor)
                } else {
                    delay
                };

                // Sleep before retry
                tokio::time::sleep(actual_delay).await;

                // Exponential backoff
                delay = (delay * 2).min(policy.max_delay);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_retry_policy_defaults() {
        let policy = RetryPolicy::network_default();
        assert_eq!(policy.max_attempts, 3);
        assert!(policy.jitter);

        let pm_policy = RetryPolicy::package_manager_default();
        assert_eq!(pm_policy.max_attempts, 2);
        assert!(!pm_policy.jitter);
    }

    #[test]
    fn test_error_classification() {
        let io_timeout = anyhow::anyhow!(std::io::Error::from(std::io::ErrorKind::TimedOut));
        assert_eq!(classify_error(&io_timeout), RetryClass::Transient);

        let io_not_found = anyhow::anyhow!(std::io::Error::from(std::io::ErrorKind::NotFound));
        assert_eq!(classify_error(&io_not_found), RetryClass::Permanent);

        let checksum_err = anyhow::anyhow!(BootstrapError::ChecksumMismatch {
            artifact: "test".to_string(),
            expected: "abc".to_string(),
            actual: "def".to_string(),
        });
        assert_eq!(classify_error(&checksum_err), RetryClass::Security);
    }

    #[tokio::test]
    async fn test_retry_success_immediate() {
        let policy = RetryPolicy::network_default();
        let call_count = Arc::new(Mutex::new(0));
        let count_clone = Arc::clone(&call_count);

        let result = retry_with_backoff(&policy, || {
            let count = Arc::clone(&count_clone);
            async move {
                *count.lock().unwrap() += 1;
                Ok::<i32, anyhow::Error>(42)
            }
        })
        .await;

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 42);
        assert_eq!(*call_count.lock().unwrap(), 1);
    }

    #[tokio::test]
    async fn test_retry_success_after_failures() {
        let policy = RetryPolicy {
            max_attempts: 3,
            initial_delay: Duration::from_millis(10),
            max_delay: Duration::from_millis(50),
            max_total_time: Duration::from_secs(5),
            jitter: false,
        };

        let call_count = Arc::new(Mutex::new(0));
        let count_clone = Arc::clone(&call_count);

        let result = retry_with_backoff(&policy, || {
            let count = Arc::clone(&count_clone);
            async move {
                let mut c = count.lock().unwrap();
                *c += 1;
                let current = *c;
                drop(c);

                if current < 3 {
                    Err(anyhow::anyhow!(std::io::Error::from(
                        std::io::ErrorKind::TimedOut
                    )))
                } else {
                    Ok(42)
                }
            }
        })
        .await;

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 42);
        assert_eq!(*call_count.lock().unwrap(), 3);
    }

    #[tokio::test]
    async fn test_retry_permanent_failure_no_retry() {
        let policy = RetryPolicy::network_default();
        let call_count = Arc::new(Mutex::new(0));
        let count_clone = Arc::clone(&call_count);

        let result = retry_with_backoff(&policy, || {
            let count = Arc::clone(&count_clone);
            async move {
                *count.lock().unwrap() += 1;
                Err::<i32, _>(anyhow::anyhow!(std::io::Error::from(
                    std::io::ErrorKind::NotFound
                )))
            }
        })
        .await;

        assert!(result.is_err());
        assert_eq!(*call_count.lock().unwrap(), 1); // Should not retry permanent errors
    }
}
