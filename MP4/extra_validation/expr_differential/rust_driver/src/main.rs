use expr::mapper_expr::{mapper_expr_evaluate, mapper_expr_new_from_string, MapperSignalValue};
use std::panic::{catch_unwind, AssertUnwindSafe};
fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    let text = std::fs::read_to_string(std::env::args().nth(1).unwrap()).unwrap();
    for line in text.lines().filter(|l| !l.is_empty()) {
        let parts: Vec<&str> = line.splitn(3, '|').collect();
        let (mode, ex, xs) = (parts[0], parts[1], parts[2]);
        let inf = mode.starts_with('f');
        let outf = if mode.len() == 2 { mode.ends_with('f') } else { inf };
        print!("{mode}|{ex}|");
        let made = catch_unwind(|| mapper_expr_new_from_string(ex, inf as i32, outf as i32, 1));
        let Ok(mut e) = made else { println!("PANIC-ON-PARSE"); continue };
        let mut out = String::new();
        for t in xs.split(',') {
            let inp = if inf { MapperSignalValue::F(t.parse::<f32>().unwrap()) }
                      else { MapperSignalValue::I32(t.parse::<i32>().unwrap()) };
            match catch_unwind(AssertUnwindSafe(|| mapper_expr_evaluate(&mut e, &inp))) {
                Ok(v) => out += &match v {
                    MapperSignalValue::F(f) => format!("{};", f),
                    MapperSignalValue::I32(i) => format!("{i};"),
                },
                Err(_) => { out += "PANIC;"; }
            }
        }
        println!("{out}");
    }
}
