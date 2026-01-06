//! Module with naming violations.
//!
//! This module intentionally violates Rust naming conventions.

/// Struct with bad name - violation 1 (should be PascalCase).
pub struct bad_struct_name {
    /// Field value.
    pub value: i32,
}

/// Function with bad name - violation 2 (should be snake_case).
pub fn BadFunctionName() -> i32 {
    42
}

/// Constant with bad name - violation 3 (should be SCREAMING_SNAKE_CASE).
pub const badConstant: i32 = 100;

/// Main function for testing.
pub fn main() {
    let _x = BadFunctionName();
    let _s = bad_struct_name { value: badConstant };
}
