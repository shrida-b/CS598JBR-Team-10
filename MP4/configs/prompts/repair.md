# Iteration {iteration}/{max_iterations}: repair `{project_name}`

The controller evaluated the crate independently after your previous iteration.

{status_table}

{regression_note}

## Feedback from the evaluation

### Integrity checks
{integrity_feedback}

### Compiler (`cargo build`)
```
{build_feedback}
```

### Tests (`cargo test`)
{test_feedback}

### Clippy (correctness / style / complexity / perf)
```
{clippy_feedback}
```

### Unsafe metrics
```
{unsafe_feedback}
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

{current_rust}
