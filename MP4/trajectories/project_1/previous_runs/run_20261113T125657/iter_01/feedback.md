| Check | Result |
|---|---|
| Integrity | 1 violation(s) |
| Build | OK |
| Tests | 1/2 passed |
| Clippy (src) | 2 [correctness 0 / style 2 / complexity 0 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |

## Integrity
- public signature changed or missing: `pubfnmapper_expr_evaluate<'a>(&mutMapperExpr,&'aMapperSignalValue)->MapperSignalValue`

## Build
```
OK (11 rustc warnings, e.g.:)
warning: unused macro definition: `trace`
  --> src/mapper_expr.rs:28:14
   |
28 | macro_rules! trace {
   |              ^^^^^
   |
   = note: `#[warn(unused_macros)]` on by default


warning: unused macro definition: `die_unless`
  --> src/mapper_expr.rs:36:14
   |
36 | macro_rules! die_unless {
   |              ^^^^^^^^^^


warning: type `stack_obj_t` should have an upper camel case name
   --> src/mapper_expr.rs:376:6
    |
376 | enum stack_obj_t {
    |      ^^^^^^^^^^^ help: convert the identifier to upper camel case: `StackObjT`
    |
    = note: `#[warn(non_camel_case_types)]` on by default


warning: constant `TRACING` is never used
  --> src/mapper_expr.rs:26:7
   |
26 | const TRACING: bool = false;
   |       ^^^^^^^
   |
   = note: `#[warn(dead_code)]` on by default


warning: enum `ExprFunc` is never used
  --> src/mapper_expr.rs:57:6
   |
57 | enum ExprFunc {
   |      ^^^^^^^^


```

## Tests
1/2 passed.
- test1: FAILED

#### test1
```
thread 'test1' panicked at src/bin/test.rs:11:5:
Test 1 failed: expected 3250.8108, got F(295.22467)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

## Clippy
```
correctness: 0, style: 2, complexity: 0, perf: 0 (warnings inside the read-only tests are ignored: 4)
[style] warning: you should consider adding a `Default` implementation for `ExprNode`
   --> src/mapper_expr.rs:341:5
    |
341 | /     pub fn new() -> ExprNode {
342 | |         ExprNode {
343 | |             tok: Token {
344 | |                 token_type: TokenType::End,
...   |
355 | |     }
    | |_____^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
    = note: `-W clippy::new-without-default` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
    |
340 + impl Default for ExprNode {
341 +     fn default() -> Self {
342 +         Self::new()
343 +     }
344 + }
    |


[style] warning: you should consider adding a `Default` implementation for `ExprNode`
   --> src/mapper_expr.rs:341:5
    |
341 | /     pub fn new() -> ExprNode {
342 | |         ExprNode {
343 | |             tok: Token {
344 | |                 token_type: TokenType::End,
...   |
355 | |     }
    | |_____^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
    = note: `-W clippy::new-without-default` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
    |
340 + impl Default for ExprNode {
341 +     fn default() -> Self {
342 +         Self::new()
343 +     }
344 + }
    |


```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 1, "primary_total": 0}
```
