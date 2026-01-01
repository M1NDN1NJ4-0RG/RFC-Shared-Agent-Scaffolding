// Test fixture for rustfmt violations

// Bad indentation
fn bad_indent() {
let x = 1;
  let y = 2;
    let z = 3;
}

// Inconsistent spacing
fn bad_spacing(){
let x=1+2;
let y = 3+4;
let z  =  5  +  6;
}

// Long lines
fn long_line() {
    let message = "this is an extremely long string that exceeds the maximum line length configured for rustfmt and should be wrapped";
}

// Bad brace style
fn bad_braces()
{
    println!("wrong");
}

// Inconsistent array formatting
fn bad_arrays() {
    let arr1 = [1,2,3,4,5];
    let arr2 = [ 1, 2, 3, 4, 5 ];
    let arr3 = [
    1,
    2,
    3
    ];
}

// Bad struct formatting
struct BadStruct{pub field1: i32,pub field2: String}

// Bad enum formatting
enum BadEnum{Variant1,Variant2,Variant3}

// Inconsistent trait implementation
impl BadStruct{fn method(&self)->i32{self.field1}}

// Missing trailing comma in multiline
fn missing_comma() {
    let data = vec![
        1,
        2,
        3
    ];
}

// Bad match formatting
fn bad_match(x: i32) {
    match x {
        1=>println!("one"),
        2=>println!("two"),
        _=>println!("other")
    }
}

// Bad import formatting
use std::collections::HashMap;use std::vec::Vec;use std::string::String;

// Inconsistent module spacing
mod module1{fn func(){}}
mod module2 {
    fn func() {
    }
}

// Bad tuple formatting
fn bad_tuples() {
    let t1 = (1,2,3);
    let t2 = ( 1 , 2 , 3 );
}

// Bad closure formatting
fn bad_closures() {
    let f1=|x|x+1;
    let f2 = |x|{x+1};
}

// Inconsistent generic formatting
fn bad_generics<T,U>(x: T,y: U){
}

// Bad where clause formatting
fn bad_where<T>(x: T)where T:Clone{
}

// Trailing whitespace
fn trailing_spaces() {
    let x = 1;   
    let y = 2;  
}
