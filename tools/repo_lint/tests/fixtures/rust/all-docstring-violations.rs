// Missing module documentation

// Function without doc comment
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn no_doc() {
    println!("no documentation");
}

// Function with incomplete doc
/// Just a summary
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn partial_doc(x: i32, y: i32) -> i32 {
    x + y
}

// Missing parameter documentation
/// Adds two numbers
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn missing_params(x: i32, y: i32) -> i32 {
    x + y
}

// Missing return documentation
/// Computes something
/// 
/// # Arguments
/// * `x` - first value
/// * `y` - second value
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn missing_return(x: i32, y: i32) -> i32 {
    x + y
}

// Missing examples
/// Complex function that does something
/// 
/// # Arguments
/// * `data` - input data
/// 
/// # Returns
/// Processed data
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn no_examples(data: Vec<i32>) -> Vec<i32> {
    data
}

// Struct without documentation
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
struct NoDocStruct {
    field1: i32,
    field2: String,
}

// Struct with incomplete documentation
/// A structure
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
struct PartialStruct {
    /// Documented field
    field1: i32,
    // Missing doc for this field
    field2: String,
}

// Enum without documentation
enum NoDocEnum {
    Variant1,
    Variant2,
}

// Trait without documentation
trait NoDocTrait {
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    fn method(&self) -> i32;
}

// Implementation without documentation
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
impl NoDocStruct {
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    fn new() -> Self {
        NoDocStruct {
            field1: 0,
            field2: String::new(),
        }
    }
    
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    fn method(&self) -> i32 {
        self.field1
    }
}

// Module without documentation
mod inner {
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    pub fn helper() {}
}

// Const without documentation
const NO_DOC_CONST: i32 = 42;

// Static without documentation
static NO_DOC_STATIC: &str = "static";

// Type alias without documentation
type NoDocType = Vec<i32>;

// Missing panic documentation
/// Does something
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn may_panic(x: i32) -> i32 {
    if x < 0 {
        panic!("negative");
    }
    x
}

// Missing error documentation
/// Tries to do something
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn may_error(x: i32) -> Result<i32, String> {
    if x < 0 {
        Err("negative".to_string())
    } else {
        Ok(x)
    }
}

// Missing safety documentation
/// Unsafe function
unsafe fn unsafe_operation() {
    // Unsafe code
}

// Generic function without constraint documentation
/// Generic function
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
fn generic_func<T>(x: T) -> T {
    x
}

// Missing invariants documentation
/// Complex structure with invariants
// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
struct Complex {
    // Must be positive
    value: i32,
}

// INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
pub fn main() {}
