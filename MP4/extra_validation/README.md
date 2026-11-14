# Extra validation beyond the CRUST-Bench tests

> **Note for the group: please decide whether to add this to the Overleaf report.**
> Everything below is ready to paste. Delete this note box (or the whole folder) once
> you've decided.

## Why this exists

The benchmark has only **2 tests for expr** and **6 for rbtree-lab**. Hidden tests may
also be graded (§3.2), so we checked both translations against far more inputs than the
visible tests use. This is **evaluation only**:

- The agent never saw these inputs or results.
- Nothing in `translations/` was changed because of them.
- None of the checks uses FFI from the translations. The C code is compiled separately,
  only as a reference oracle.

Reproduce everything with one command (about a minute):

```bash
bash MP4/extra_validation/run.sh
```

## Results (2026-11-14)

**expr: differential testing against the original C implementation.**
`expr_differential/` compiles the unmodified `subjects/project_1/mapper_expr.c` with a
small C driver (`c_driver.c`). It runs 79 expressions (`cases.txt`) through both the C
code and our Rust translation, feeding each a sequence of inputs.

The expressions cover operator precedence and associativity, unary minus, parentheses,
all 28 built-in functions (`pow`, `sin` … `min`, `max`, `pi`), history references
(`x{-1}`, `x{-2}`, `y{-1}`), vector indexing, and integer, float and mixed modes.

- **All 74 valid expressions agree exactly** (floats within 1e-6), including stateful
  history across consecutive evaluations.
- **Leading space:** `" y = x * 2 "` is rejected by C with a lexer error; Rust accepts it
  and returns 8. Rust is more lenient here.
- **Malformed expressions** (`y=x+`, `y=(x`, `z=x`, `y=foo(x)`): both print the same
  error message. C then returns `NULL`, while Rust panics, because the required Rust
  signature `mapper_expr_new_from_string(...) -> MapperExpr` has no way to signal failure.

**rbtree-lab: the C project's extra tests, plus randomized stress.**
`rbtree_stress/` uses only the public API. It has two parts:

1. **Ports of the C test-suite checks that the Rust benchmark does not run:**
   `test_minmax_suite` (commented out in the CRUST-Bench Rust tests),
   `test_distinct_values`, `test_duplicate_values` and `test_to_array_suite`. These
   include the red-black colour and search constraints. **All pass.**
2. **Random stress:** 4 seeds × 1,250 random insert, find and erase operations (5,000
   total) with duplicate and negative keys, each run ending by erasing everything.
   After **every** operation it checks:
   - root is black, no red node has a red child, and every root-to-leaf path has the
     same number of black nodes;
   - BST order, and that every `parent` pointer is consistent;
   - `to_array`, `rbtree_min`/`rbtree_max` and `rbtree_find` against a reference
     multiset.

   **All invariants held.**

## Recommendation

**Add it, briefly.** The report's Reflection names thin test coverage as a main
limitation, and this is concrete evidence that the translations are correct beyond the
visible tests. It also shows extra care. Keep it short, and present it as *our*
post-hoc evaluation, not part of the agent loop.

Suggested spot: a new paragraph at the end of **§ Overall Results** (after the notes
list), and change the Reflection sentence "passing them is a weak guarantee for any
hidden tests" to point to it.

### Paste-ready LaTeX

```latex
\paragraph{Additional validation (beyond the benchmark tests).} Because the benchmark has
only 2 tests for \texttt{expr} and 6 for \texttt{rbtree-lab}, we ran extra checks after the
pipeline finished. These checks were never shown to the agent, and no code was changed
because of them (\texttt{MP4/extra\_validation/run.sh}).
\begin{itemize}
  \item \texttt{expr}: differential testing against the unmodified C implementation on
        79 new expressions, covering precedence, unary minus, all 28 built-in functions,
        history references (\texttt{x\{-1\}}, \texttt{y\{-1\}}), and integer, float and
        mixed modes. All 74 valid expressions produced identical results on every input.
        The only differences are on invalid input: C rejects a leading space before
        \texttt{y} while Rust accepts it, and on malformed expressions C returns
        \texttt{NULL} while Rust panics, because the required signature returns
        \texttt{MapperExpr} rather than an \texttt{Option}.
  \item \texttt{rbtree-lab}: the C project's own tests that the Rust benchmark omits
        (\texttt{test\_minmax}, \texttt{test\_distinct\_values}, \texttt{test\_duplicate\_values},
        \texttt{test\_to\_array\_suite}) all pass. A randomized stress test of 5{,}000
        insert, find and erase operations with duplicate keys checked, after every
        operation, all red-black invariants, BST order, parent-pointer consistency, and
        \texttt{to\_array}, \texttt{rbtree\_min} and \texttt{rbtree\_max} against a
        reference model; all held.
\end{itemize}
```

If you add it, also replace this Reflection sentence:

> "Test coverage is thin: `expr` has only 2 benchmark tests, so passing them is a weak
> guarantee for any hidden tests."

with:

```latex
  \item Test coverage is thin: \texttt{expr} has only 2 benchmark tests. Our post-hoc
        differential testing against the C implementation (above) found no behavioural
        differences on valid input, but the agent itself only saw the benchmark tests.
```

## Files

| Path | What it is |
|---|---|
| `run.sh` | runs both checks |
| `expr_differential/cases.txt` | 79 test cases: `mode\|expression\|inputs` (`f` float, `i` int, `fi`/`if` mixed) |
| `expr_differential/c_driver.c` | C driver for the original `mapper_expr.c` (compiled from `subjects/`, unmodified) |
| `expr_differential/rust_driver/` | Rust driver for `translations/project_1` |
| `expr_differential/compare.py` | compares outputs |
| `rbtree_stress/` | C-suite ports and randomized invariant checks for `translations/project_2` |
