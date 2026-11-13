| Check | Result |
|---|---|
| Integrity | 1 violation(s) |
| Build | FAILED (1 error(s)) |
| Tests | 0/2 passed |
| Clippy (src) | n/a [n/a (does not build)] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

## Integrity
- public enum `state_t` missing

## Build
```
error: this file contains an unclosed delimiter
    --> src/mapper_expr.rs:1021:3
     |
485  | pub enum StateT {
     |                 - unclosed delimiter
...
1021 | }
     |  ^


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
