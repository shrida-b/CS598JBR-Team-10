| Check | Result |
|---|---|
| Integrity | 2 violation(s) |
| Build | FAILED (1 error(s)) |
| Tests | 0/2 passed |
| Clippy (src) | n/a [n/a (does not build)] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |

## Integrity
- public signature changed or missing: `pubfnmapper_expr_evaluate<'a>(&mutMapperExpr,&'aMapperSignalValue)->MapperSignalValue`
- public enum `state_t` missing

## Build
```
error[E0412]: cannot find type `stack_obj_t` in this scope
   --> src/mapper_expr.rs:219:23
    |
219 | fn printstack(stack: &stack_obj_t, stack_size: i32){
    |                       ^^^^^^^^^^^ not found in this scope


```

## Tests
not run (build failed)

## Clippy
```
not run (build failed)
```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 1, "primary_total": 0}
```
