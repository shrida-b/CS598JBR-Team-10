# Iteration {iteration}/{max_iterations}: initial translation of `{project_name}`

C project files (under `c/`):
{c_files}

Rust crate `{crate_name}` (under `rust/`). Modules to implement:
{modules}

Benchmark tests (read-only):
{test_files}

Steps:
1. Study the C sources and headers to understand data structures and behavior.
2. Study the Rust interface file(s) and the tests to learn the exact required API
   and expected behavior. The interface is the specification: keep every public
   item's signature exactly as given.
3. Replace every `unimplemented!()` with a real, safe, idiomatic implementation
   (usually by writing the whole module with `write_file`). Add
   `#![forbid(unsafe_code)]` as the first line of `rust/src/lib.rs`.
4. Run `cargo check` and fix all errors; then `cargo test` and fix failures; then
   `cargo clippy` and `unsafe_metrics` and fix what they report.
5. Call `finish` with a short summary of what is done and what remains.

{inlined_context}
