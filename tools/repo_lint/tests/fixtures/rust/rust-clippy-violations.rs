///! Module with Clippy violations.
//!
//! This module intentionally contains Clippy lint violations.

/// Test function with clippy violations.
pub fn clippy_violations() {
    // Violation 1: needless_return
    let x = 5;
    return x + 1;
}

/// Function with unnecessary clone - violation 2.
pub fn unnecessary_clone() {
    let s = String::from("hello");
    let _s2 = s.clone();
    println!("{}", s);
}

/// Function with manual string formatting - violation 3.
pub fn manual_format() {
    let name = "world";
    let _greeting = format!("{}{}", "hello ", name);
}

/// Function with comparison to bool - violation 4.
pub fn bool_comparison(flag: bool) -> bool {
    if flag == true {
        return false;
    }
    true
}

/// Main function for testing.
pub fn main() {
    clippy_violations();
    unnecessary_clone();
    manual_format();
    let _ = bool_comparison(true);
}
