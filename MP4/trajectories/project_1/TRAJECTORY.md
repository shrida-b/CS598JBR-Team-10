# Trajectory: expr (project_1)

Status: **success**; best iteration 1.

| Iter | Score (builds, tests, integrity, unsafe, clippy) | Turns | Improved | Reverted | Agent summary |
|---|---|---|---|---|---|
| 0 | builds=1 tests_passed=0 integrity_violations=0 unsafe=0 clippy_src=4 | - | - |  | skeleton baseline |
| 1 | builds=1 tests_passed=2 integrity_violations=0 unsafe=0 clippy_src=0 | 18 | True |  | Translated mapper_expr from C to safe Rust: - Added #![forbid(unsafe_code)] to src/lib.rs. - Implemented MapperSignalValue (as_f32, as_i32, and coercion helpers). - Implemented function lookup table w |

## Final evaluation

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


Files: `events.jsonl` (every model response and tool call), `iter_NN/prompt.md`, `iter_NN/session_messages.json`, `iter_NN/feedback.{json,md}`, `iter_NN/diff.patch`, `iter_NN/snapshot/`, `summary.json`.
