| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 0/2 passed |
| Clippy (src) | 4 [correctness 0 / style 2 / complexity 2 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

## Integrity
OK

## Build
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

## Tests
0/2 passed.
- test1: FAILED
- test2: FAILED

#### test1
```
thread 'test1' panicked at src/mapper_expr.rs:201:5:
not implemented
```

#### test2
```
Parsing: y=26.0*2.0/2.0 + x*30.0/(20.0*1.0)

thread 'test2' panicked at src/mapper_expr.rs:201:5:
not implemented
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

## Clippy
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

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
```
