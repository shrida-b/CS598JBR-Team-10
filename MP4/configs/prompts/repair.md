# Iteration {iteration}/{max_iterations}: repair `{project_name}`

The controller evaluated your previous iteration independently. Current status:

{status_table}

{regression_note}

## Feedback from the evaluation

### Integrity checks
{integrity_feedback}

### Compiler (`cargo build`)
{build_feedback}

### Tests (`cargo test`)
{test_feedback}

### Clippy (correctness / style / complexity / perf)
{clippy_feedback}

### Unsafe metrics
{unsafe_feedback}

## Your task
Fix the problems above in priority order:
1. integrity violations and compile errors,
2. failing tests (read the failing test and the corresponding C code first),
3. any unsafe code (replace with safe abstractions),
4. Clippy warnings.

Do not break what already works: re-run `cargo test` after each change.
Call `finish` with a short summary when done.
