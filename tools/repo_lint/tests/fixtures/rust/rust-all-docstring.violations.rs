// Missing module documentation - violation 1

// Missing function documentation - violation 2
fn function_no_docs(x: i32) -> i32 {
    x + 1
}

// Missing struct documentation - violation 3
struct MyStruct {
    value: i32,
}

// Missing impl documentation - violation 4
impl MyStruct {
    fn new() -> Self {
        MyStruct { value: 0 }
    }
    
    // Missing method documentation - violation 5
    fn get_value(&self) -> i32 {
        self.value
    }
}

fn main() {
    let _ = function_no_docs(5);
}
