//! Module with rustfmt violations.
//!
//! This module intentionally contains rustfmt formatting violations.
#![allow(clippy::all)]

/// Test function with bad formatting - violation 1.
pub fn bad_formatting(  x:i32,y:i32  )->i32{
return x+y;
}

/// Function with inconsistent indentation - violation 2.
pub fn bad_indentation() {
let x = 5;
    let y = 10;
        return x + y;
}

/// Function with bad brace placement - violation 3.
pub fn bad_braces()
{
    let result = if true
    {
        42
    }
    else
    {
        0
    };
    result
}

/// Main function for testing.
pub fn main() {
    let _ = bad_formatting(1,2);
    let _ = bad_indentation();
    let _ = bad_braces();
}
