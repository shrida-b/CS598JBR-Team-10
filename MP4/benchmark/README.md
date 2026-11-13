# CRUST-Bench Rust specifications (read-only)

Copied unmodified (minus nested `.git/`) from CRUST-Bench
(<https://github.com/anirudhkhatry/CRUST-bench>, `datasets/CRUST_bench.zip`, `RBench/`).

| Project | Directory | Interface | Tests |
|---|---|---|---|
| project_1 `expr` | `RBench/expr` | `src/interfaces/mapper_expr.rs` | `src/bin/test.rs` (2 tests) |
| project_2 `rbtree-lab` | `RBench/rbtree_lab` | `src/interfaces/rbtree.rs` | `src/bin/test.rs` (6 tests; a 7th is commented out) |

The pipeline copies each spec into `translations/project_<N>/`, places
`src/interfaces/<module>.rs` at `src/<module>.rs` (the module path `lib.rs`
expects), and the agent fills in the `unimplemented!()` bodies. Tests and
public signatures are integrity-checked against these files after every iteration.
