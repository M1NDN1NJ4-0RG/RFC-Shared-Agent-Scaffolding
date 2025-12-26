mod cli;

use clap::Parser;
use std::process;

fn main() {
    let args = cli::Cli::parse();

    match args.run() {
        Ok(exit_code) => process::exit(exit_code),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}
