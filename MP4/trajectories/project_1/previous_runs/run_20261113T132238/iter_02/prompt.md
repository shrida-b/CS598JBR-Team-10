# Iteration 2/6: repair `expr`

The controller evaluated the crate independently after your previous iteration.

| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 0/2 passed |
| Clippy (src) | 4 [correctness 0 / style 2 / complexity 2 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

**Note:** iteration 1 scored worse (builds=1 tests_passed=0 integrity_violations=3 unsafe=0 clippy_src=20) than iteration 0 (builds=1 tests_passed=0 integrity_violations=0 unsafe=0 clippy_src=4). The controller reverted the code to iteration 0; the feedback below is for that restored version.

## Feedback from the evaluation

### Integrity checks
OK

### Compiler (`cargo build`)
```
OK (53 rustc warnings, e.g.:)
warning: unused import: `std::f32::consts::PI`
 --> src/mapper_expr.rs:1:5
  |
1 | use std::f32::consts::PI;
  |     ^^^^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(unused_imports)]` on by default


warning: unused import: `lazy_static::lazy_static`
 --> src/mapper_expr.rs:4:5
  |
4 | use lazy_static::lazy_static;
  |     ^^^^^^^^^^^^^^^^^^^^^^^^


warning: unused macro definition: `trace`
  --> src/mapper_expr.rs:19:14
   |
19 | macro_rules! trace {
   |              ^^^^^
   |
   = note: `#[warn(unused_macros)]` on by default


warning: unused macro definition: `die_unless`
  --> src/mapper_expr.rs:26:14
   |
26 | macro_rules! die_unless {
   |              ^^^^^^^^^^


warning: type `state_t` should have an upper camel case name
   --> src/mapper_expr.rs:151:10
    |
151 | pub enum state_t{
    |          ^^^^^^^ help: convert the identifier to upper camel case: `StateT`
    |
    = note: `#[warn(non_camel_case_types)]` on by default


```

### Tests (`cargo test`)
0/2 passed.
- test1: FAILED
- test2: FAILED

#### test1
```
thread 'test1' panicked at src/mapper_expr.rs:201:5:
not implemented
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

#### test2
```
Parsing: y=26.0*2.0/2.0 + x*30.0/(20.0*1.0)

thread 'test2' panicked at src/mapper_expr.rs:201:5:
not implemented
```

### Clippy (correctness / style / complexity / perf)
```
correctness: 0, style: 2, complexity: 2, perf: 0 (warnings inside the read-only tests are ignored: 4)
[style] warning: you should consider adding a `Default` implementation for `ExprNode`
   --> src/mapper_expr.rs:175:5
    |
175 | /     pub fn new() -> ExprNode{
176 | |         unimplemented!();
177 | |     }
    | |_____^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
    = note: `-W clippy::new-without-default` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
    |
174 + impl Default for ExprNode {
175 +     fn default() -> Self {
176 +         Self::new()
177 +     }
178 + }
    |


[style] warning: you should consider adding a `Default` implementation for `ExprNode`
   --> src/mapper_expr.rs:175:5
    |
175 | /     pub fn new() -> ExprNode{
176 | |         unimplemented!();
177 | |     }
    | |_____^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
    = note: `-W clippy::new-without-default` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
    |
174 + impl Default for ExprNode {
175 +     fn default() -> Self {
176 +         Self::new()
177 +     }
178 + }
    |


[complexity] warning: the following explicit lifetimes could be elided: 'a
   --> src/mapper_expr.rs:203:29
    |
203 | pub fn mapper_expr_evaluate<'a>(mapper: &mut MapperExpr, 
    |                             ^^
204 |                          input: &'a MapperSignalValue) -> MapperSignalValue{
    |                                  ^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
    = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
    = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
    |
203 ~ pub fn mapper_expr_evaluate(mapper: &mut MapperExpr, 
204 ~                          input: &MapperSignalValue) -> MapperSignalValue{
    |


[complexity] warning: the following explicit lifetimes could be elided: 'a
   --> src/mapper_expr.rs:203:29
    |
203 | pub fn mapper_expr_evaluate<'a>(mapper: &mut MapperExpr, 
    |                             ^^
204 |                          input: &'a MapperSignalValue) -> MapperSignalValue{
    |                                  ^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
    = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
    = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
    |
203 ~ pub fn mapper_expr_evaluate(mapper: &mut MapperExpr, 
204 ~                          input: &MapperSignalValue) -> MapperSignalValue{
    |


```

### Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
```

## Your task
Fix the problems above in priority order:
1. integrity violations and compile errors,
2. failing tests (re-read the failing test and the corresponding C code first:
   `c/` is still available through `read_file` / `search`),
3. any unsafe code (replace it with safe abstractions),
4. Clippy warnings in `src/` (warnings inside the read-only tests do not count).

Prefer small targeted edits (`replace_in_file`) over rewriting whole files, and do
not break what already works: re-run `cargo test` after each change. Call `finish`
with a short summary when done.

## Current Rust sources (supplied automatically)

### rust/src/lib.rs
```rust
pub mod mapper_expr;
```

### rust/src/mapper_expr.rs
```rust
use std::f32::consts::PI;
use std::collections::HashMap;
use std::sync::Arc;
use lazy_static::lazy_static;
#[derive(Clone, Copy, Debug)]
pub enum MapperSignalValue {
    F(f32),
    I32(i32),
}
impl MapperSignalValue {
    pub fn as_f32(&self) -> Option<f32> {
       unimplemented!() 
    }
    pub fn as_i32(&self) -> Option<i32> {
        unimplemented!()
    }
}
const STACK_SIZE: usize = 256;
macro_rules! trace {
    ($($arg:tt)*) => {
        if TRACING {
            println!("-- {}", format!($($arg)*));
        }
    };
}
macro_rules! die_unless {
    ($cond:expr, $($arg:tt)*) => {
        if !$cond {
            println!("-- {}", format!($($arg)*));
            assert!($cond);
        }
    };
}
fn minf(x: f32, y: f32) -> f32 {
    unimplemented!();
}
fn maxf(x: f32, y: f32) -> f32 {
    unimplemented!();
}
fn pif() -> f32 {
    unimplemented!();
}
#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExprFunc {
    Unknown = -1,
    Pow = 0,
    Sin,
    Cos,
    Tan,
    Abs,
    Sqrt,
    Log,
    Log10,
    Exp,
    Floor,
    Round,
    Ceil,
    Asin,
    Acos,
    Atan,
    Atan2,
    Sinh,
    Cosh,
    Tanh,
    Logb,
    Exp2,
    Log2,
    Hypot,
    Cbrt,
    Trunc,
    Min,
    Max,
    Pi,
    NFuncs,
}
#[derive(Debug, Clone, Copy)]
struct FunctionEntry {
    name: &'static str,
    arity: u32,
    func: fn(f32, f32) -> f32,
}
lazy_static::lazy_static! {
    static ref FUNCTION_TABLE: HashMap<&'static str, FunctionEntry> = {
        let mut m = HashMap::new();
        m.insert("pow", FunctionEntry { name: "pow", arity: 2, func: f32::powf });
        m.insert("sin", FunctionEntry { name: "sin", arity: 1, func: |x, _| x.sin() });
        m.insert("cos", FunctionEntry { name: "cos", arity: 1, func: |x, _| x.cos() });
        m.insert("tan", FunctionEntry { name: "tan", arity: 1, func: |x, _| x.tan() });
        m.insert("abs", FunctionEntry { name: "abs", arity: 1, func: |x, _| x.abs() });
        m.insert("sqrt", FunctionEntry { name: "sqrt", arity: 1, func: |x, _| x.sqrt() });
        m.insert("log", FunctionEntry { name: "log", arity: 1, func: |x, _| x.ln() });
        m.insert("log10", FunctionEntry { name: "log10", arity: 1, func: |x, _| x.log10() });
        m.insert("exp", FunctionEntry { name: "exp", arity: 1, func: |x, _| x.exp() });
        m.insert("floor", FunctionEntry { name: "floor", arity: 1, func: |x, _| x.floor() });
        m.insert("round", FunctionEntry { name: "round", arity: 1, func: |x, _| x.round() });
        m.insert("ceil", FunctionEntry { name: "ceil", arity: 1, func: |x, _| x.ceil() });
        m.insert("min", FunctionEntry { name: "min", arity: 2, func: minf });
        m.insert("max", FunctionEntry { name: "max", arity: 2, func: maxf });
        m.insert("pi", FunctionEntry { name: "pi", arity: 0, func: |_, _| pif() });
        m
    };
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TokenType {
    Float,
    Int,
    Op,
    OpenParen,
    CloseParen,
    Var,
    OpenSquare,
    CloseSquare,
    OpenCurly,
    CloseCurly,
    Func,
    Comma,
    End,
    ToFloat,
    ToInt32,
}
#[derive(Debug, Clone, Copy)]
struct Token {
    token_type: TokenType,
    value: Option<f32>,
    int_value: Option<i32>,
    var: Option<char>,
    op: Option<char>,
}
fn function_lookup(s: &str) -> Option<&'static FunctionEntry> {
    unimplemented!();
}
fn expr_lex(s: Vec<&str>) -> Vec<Token>{
    unimplemented!();
}
pub struct ExprNode{
    pub tok: Token,
    pub is_float: i32,
    pub history_index: i32,
    pub vector_index: i32,
    pub next: Option<Arc<ExprNode>>,
}
pub struct MapperExpr{
    pub node: ExprNode,
    pub vector_size: i32,
    pub history_size: i32,
    pub history_pos: i32,
    pub input_history: Vec<MapperSignalValue>,
    pub output_history: Vec<MapperSignalValue>,
}
pub enum state_t{
    YEQUAL_Y,
    YEQUAL_EQ,
    EXPR,
    EXPR_RIGHT,
    TERM,
    TERM_RIGHT,
    VALUE,
    NEGATE,
    VAR_RIGHT,
    VAR_VECTINDEX,
    VAR_HISTINDEX,
    CLOSE_VECTINDEX,
    CLOSE_HISTINDEX,
    OPEN_PAREN,
    CLOSE_PAREN,
    COMMA,
    END,
}
enum stack_obj_t {
    State(state_t),
    Node(ExprNode),
}
impl ExprNode{
    pub fn new() -> ExprNode{
        unimplemented!();
    }
    pub fn expr_free(&self){
        unimplemented!();
    }
}
fn printtoken(t: &Token){
    unimplemented!();
}
fn printexprnode(s: &str, list: &ExprNode){
    unimplemented!();
}
fn printexpr(s: &str, list: &MapperExpr){
    unimplemented!();
}
fn printstack(stack: &stack_obj_t, stack_size: i32){
    unimplemented!();
}
fn collapse_expr_to_left(plhs: &mut ExprNode, constant_folding: i32){
    unimplemented!();
}
pub fn mapper_expr_new_from_string(s: &str, 
                                input_is_float: i32,
                                output_is_float: i32,
                                vector_size: i32)-> MapperExpr{
    unimplemented!();
}
pub fn mapper_expr_evaluate<'a>(mapper: &mut MapperExpr, 
                         input: &'a MapperSignalValue) -> MapperSignalValue{
    unimplemented!();
}
```
