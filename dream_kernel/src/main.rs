use dream_kernel::{demo_sequence, sequence_to_json};
use std::path::PathBuf;

fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let command = args.get(1).map(String::as_str).unwrap_or("demo");
    match command {
        "demo" => match demo_sequence() {
            Ok(sequence) => {
                let json = sequence_to_json(&sequence);
                if let Some(path) = output_path(&args[2..]) {
                    if let Err(error) = std::fs::write(&path, format!("{json}\n")) {
                        eprintln!("dream-kernel write failed for {}: {error}", path.display());
                        std::process::exit(1);
                    }
                } else {
                    println!("{json}");
                }
            }
            Err(error) => {
                eprintln!("dream-kernel demo failed: {error}");
                std::process::exit(1);
            }
        },
        _ => {
            eprintln!("usage: dream-kernel demo [--out PATH]");
            std::process::exit(2);
        }
    }
}

fn output_path(args: &[String]) -> Option<PathBuf> {
    match args {
        [] => None,
        [flag, path] if flag == "--out" => Some(PathBuf::from(path)),
        _ => {
            eprintln!("usage: dream-kernel demo [--out PATH]");
            std::process::exit(2);
        }
    }
}
