| Check | Result |
|---|---|
| Integrity | 2 violation(s) |
| Build | FAILED (1 error(s)) |
| Tests | 0/2 passed |
| Clippy (src) | n/a [n/a (does not build)] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

## Integrity
- public signature changed or missing: `pubfnnew()->ExprNode`
- public signature changed or missing: `pubfnexpr_free(&self)`

## Build
```
error[E0382]: borrow of moved value: `plhs`
   --> src/mapper_expr.rs:572:25
    |
504 | fn collapse_expr_to_left(plhs: &mut Box<ExprNode>, rhs: Box<ExprNode>, constant_folding: i32, vector_size: i32, _input_is_float: i32, _ou...
    |                          ---- move occurs because `plhs` has type `&mut Box<ExprNode>`, which does not implement the `Copy` trait
...
553 |     let mut last_ptr = plhs;
    |                        ---- value moved here
...
572 |         let next_take = plhs.next.take();
    |                         ^^^^^^^^^ value borrowed here after move


```

## Tests
not run (build failed)

## Clippy
```
not run (build failed)
```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
```
