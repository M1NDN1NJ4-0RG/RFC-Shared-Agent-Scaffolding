// Test fixture for clippy violations

// Unused imports
use std::collections::HashMap;
use std::vec::Vec;

// Unused variable
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn unused_var() {
    let x = 42;
    let y = 10;
    println!("{}", x);
}

// Needless return
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn needless_return() -> i32 {
    return 42;
}

// Single char pattern
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn single_char() {
    let s = "hello";
    if s.contains("h") {
        println!("found");
    }
}

// Redundant clone
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn redundant_clone() {
    let s = String::from("hello");
    let t = s.clone();
    println!("{}", t);
}

// Comparison to empty slice
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn cmp_empty(v: &Vec<i32>) {
    if v.len() == 0 {
        println!("empty");
    }
}

// Manual implementation of Iterator
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn manual_map(v: Vec<i32>) -> Vec<i32> {
    let mut result = Vec::new();
    for item in v {
        result.push(item * 2);
    }
    result
}

// Explicit counter loop
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn explicit_counter() {
    let items = vec![1, 2, 3];
    for i in 0..items.len() {
        println!("{}", items[i]);
    }
}

// Redundant field names
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
struct Point {
    x: i32,
    y: i32,
}

// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn redundant_fields(x: i32, y: i32) -> Point {
    Point { x: x, y: y }
}

// Single match that could be if-let
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn single_match(opt: Option<i32>) {
    match opt {
        Some(x) => println!("{}", x),
        _ => {}
    }
}

// Needless bool
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn needless_bool(x: i32) -> bool {
    if x > 0 {
        return true;
    } else {
        return false;
    }
}

// Ptr arg instead of reference
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn ptr_arg(v: &Vec<i32>) {
    println!("{}", v.len());
}

// Unnecessary mut
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn unnecessary_mut() {
    let mut x = 5;
    println!("{}", x);
}

// Box::new in vec macro
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn box_vec() {
    let v = vec![Box::new(1), Box::new(2)];
}

// Redundant closure
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn redundant_closure() {
    let v = vec![1, 2, 3];
    let doubled: Vec<i32> = v.iter().map(|x| x * 2).collect();
}

// Unreadable literal
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn unreadable_literal() {
    let x = 1000000;
    let y = 0xFFFFFF;
}

// Default trait access
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn default_trait() {
    let x: i32 = Default::default();
}

// Unnecessary cast
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn unnecessary_cast() {
    let x = 42i32;
    let y = x as i32;
}

// Collapsible if
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn collapsible_if(x: i32, y: i32) {
    if x > 0 {
        if y > 0 {
            println!("both positive");
        }
    }
}

// Duplicate imports
use std::io;
use std::io::Write;

// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn main() {
    println!("violations");
}
