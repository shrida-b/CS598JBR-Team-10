| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 2/2 passed |
| Clippy (src) | 2 [correctness 0 / style 0 / complexity 2 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |

## Integrity
OK

## Build
```
OK (2 rustc warnings, e.g.:)
warning: type `Token` is more private than the item `ExprNode::tok`
   --> src/mapper_expr.rs:385:5
    |
385 |     pub tok: Token,
    |     ^^^^^^^^^^^^^^ field `ExprNode::tok` is reachable at visibility `pub`
    |
note: but type `Token` is only usable at visibility `pub(self)`
   --> src/mapper_expr.rs:198:1
    |
198 | struct Token {
    | ^^^^^^^^^^^^
    = note: `#[warn(private_interfaces)]` on by default


warning: unused import: `expr::mapper_expr`
 --> src/bin/test.rs:1:5
  |
1 | use expr::mapper_expr;
  |     ^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(unused_imports)]` on by default


```

## Tests
2/2 passed.

## Clippy
```
correctness: 0, style: 0, complexity: 2, perf: 0 (warnings inside the read-only tests are ignored: 4)
[complexity] warning: the following explicit lifetimes could be elided: 'a
    --> src/mapper_expr.rs:1132:29
     |
1132 | pub fn mapper_expr_evaluate<'a>(
     |                             ^^
1133 |     mapper: &mut MapperExpr,
1134 |     input: &'a MapperSignalValue,
     |             ^^
     |
     = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
     = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
     = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
     |
1132 ~ pub fn mapper_expr_evaluate(
1133 |     mapper: &mut MapperExpr,
1134 ~     input: &MapperSignalValue,
     |


[complexity] warning: the following explicit lifetimes could be elided: 'a
    --> src/mapper_expr.rs:1132:29
     |
1132 | pub fn mapper_expr_evaluate<'a>(
     |                             ^^
1133 |     mapper: &mut MapperExpr,
1134 |     input: &'a MapperSignalValue,
     |             ^^
     |
     = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
     = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
     = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
     |
1132 ~ pub fn mapper_expr_evaluate(
1133 |     mapper: &mut MapperExpr,
1134 ~     input: &MapperSignalValue,
     |


```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 1, "primary_total": 0}
```
