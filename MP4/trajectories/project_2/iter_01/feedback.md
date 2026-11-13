| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 6/6 passed |
| Clippy (src) | 0 [correctness 0 / style 0 / complexity 0 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |

## Integrity
OK

## Build
```
OK (2 rustc warnings, e.g.:)
warning: unused import: `Key`
 --> src/bin/test.rs:1:22
  |
1 | use rbtree::rbtree::{Key, RBTree};
  |                      ^^^
  |
  = note: `#[warn(unused_imports)]` on by default


warning: function `insert_arr` is never used
  --> src/bin/test.rs:55:4
   |
55 | fn insert_arr(t: &mut RBTree, arr: &[i32]) {
   |    ^^^^^^^^^^
   |
   = note: `#[warn(dead_code)]` on by default


```

## Tests
6/6 passed.

## Clippy
```
correctness: 0, style: 0, complexity: 0, perf: 0 (warnings inside the read-only tests are ignored: 0)
```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 1, "primary_total": 0}
```
