# Iteration {iteration}/{max_iterations}: initial translation of `{project_name}`

C project files (under `c/`):
{c_files}

Rust crate `{crate_name}` (under `rust/`). Modules to implement:
{modules}

Benchmark tests (read-only):
{test_files}

Steps:
1. Read the C sources and headers to understand data structures and behavior.
2. Read the Rust interface file(s) and the tests to learn the exact required API
   and expected behavior.
3. Replace every `unimplemented!()` with a real, safe, idiomatic implementation.
   Add `#![forbid(unsafe_code)]` to `rust/src/lib.rs` if it is not already there.
4. Run `cargo check` and fix all errors; then `cargo test` and fix failures; then
   `cargo clippy` and `unsafe_metrics` and fix what they report.
5. Call `finish` with a short summary of what is done and what remains.
