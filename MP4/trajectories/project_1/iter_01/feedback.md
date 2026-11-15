| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 2/2 passed |
| Clippy (src) | 0 [correctness 0 / style 0 / complexity 0 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |

## Integrity
OK

## Build
```
OK (1 rustc warnings, e.g.:)
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
correctness: 0, style: 0, complexity: 0, perf: 0 (warnings inside the read-only tests are ignored: 4)
```

## Unsafe metrics
```
{"pointer_arithmetic": 0, "unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "total_spans": 34145, "raw_pointer_dereferences": 0, "raw_pointer_declarations": 0, "unsafe_ratio": 0.0, "primary_total": 0, "forbid_unsafe_code": 1}
```
