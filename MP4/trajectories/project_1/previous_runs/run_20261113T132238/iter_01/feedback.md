| Check | Result |
|---|---|
| Integrity | 3 violation(s) |
| Build | OK |
| Tests | 0/2 passed |
| Clippy (src) | 20 [correctness 0 / style 16 / complexity 4 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

## Integrity
- public signature changed or missing: `pubfnnew()->ExprNode`
- public signature changed or missing: `pubfnexpr_free(&self)`
- public enum `state_t` missing

## Build
```
OK (7 rustc warnings, e.g.:)
warning: unused macro definition: `trace`
  --> src/mapper_expr.rs:29:14
   |
29 | macro_rules! trace {
   |              ^^^^^
   |
   = note: `#[warn(unused_macros)]` on by default


warning: unused variable: `input_vec`
   --> src/mapper_expr.rs:533:21
    |
533 |                 let input_vec = input_vector.expect("Input required but not provided for expression evaluation");
    |                     ^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_input_vec`
    |
    = note: `#[warn(unused_variables)]` on by default


warning: type `Token` is more private than the item `ExprNode::tok`
   --> src/mapper_expr.rs:360:5
    |
360 |     pub tok: Token,
    |     ^^^^^^^^^^^^^^ field `ExprNode::tok` is reachable at visibility `pub`
    |
note: but type `Token` is only usable at visibility `pub(self)`
   --> src/mapper_expr.rs:155:1
    |
155 | struct Token {
    | ^^^^^^^^^^^^
    = note: `#[warn(private_interfaces)]` on by default


warning: variant `NFuncs` is never constructed
  --> src/mapper_expr.rs:90:5
   |
60 | enum ExprFunc {
   |      -------- variant in this enum
...
90 |     NFuncs,
   |     ^^^^^^
   |
   = note: `ExprFunc` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis
   = note: `#[warn(dead_code)]` on by default


warning: field `name` is never read
  --> src/mapper_expr.rs:95:5
   |
94 | struct FunctionEntry {
   |        ------------- field in this struct
95 |     name: &'static str,
   |     ^^^^
   |
   = note: `FunctionEntry` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis


```

## Tests
0/2 passed.
- test1: FAILED
- test2: FAILED

#### test1
```
thread 'test1' panicked at src/bin/test.rs:11:5:
Test 1 failed: expected 3250.8108, got F(52.0)
```

#### test2
```
Parsing: y=26.0*2.0/2.0 + x*30.0/(20.0*1.0)

thread 'test2' panicked at src/mapper_expr.rs:548:58:
called `Option::unwrap()` on a `None` value
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

## Clippy
```
correctness: 0, style: 16, complexity: 4, perf: 0 (warnings inside the read-only tests are ignored: 4)
[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:298:37
    |
298 |                     let float_val = format!("{}.{}", int_str, frac_str).parse().unwrap();
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
    = note: `-W clippy::uninlined-format-args` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::uninlined_format_args)]`
help: change this to
    |
298 -                     let float_val = format!("{}.{}", int_str, frac_str).parse().unwrap();
298 +                     let float_val = format!("{int_str}.{frac_str}").parse().unwrap();
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:298:37
    |
298 |                     let float_val = format!("{}.{}", int_str, frac_str).parse().unwrap();
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
    = note: `-W clippy::uninlined-format-args` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::uninlined_format_args)]`
help: change this to
    |
298 -                     let float_val = format!("{}.{}", int_str, frac_str).parse().unwrap();
298 +                     let float_val = format!("{int_str}.{frac_str}").parse().unwrap();
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:317:37
    |
317 |                     let float_val = format!("0.{}", frac_str).parse().unwrap();
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
317 -                     let float_val = format!("0.{}", frac_str).parse().unwrap();
317 +                     let float_val = format!("0.{frac_str}").parse().unwrap();
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:317:37
    |
317 |                     let float_val = format!("0.{}", frac_str).parse().unwrap();
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
317 -                     let float_val = format!("0.{}", frac_str).parse().unwrap();
317 +                     let float_val = format!("0.{frac_str}").parse().unwrap();
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:347:29
    |
347 | ...                   panic!("Unknown function: {}", name);
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
347 -                             panic!("Unknown function: {}", name);
347 +                             panic!("Unknown function: {name}");
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:347:29
    |
347 | ...                   panic!("Unknown function: {}", name);
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
347 -                             panic!("Unknown function: {}", name);
347 +                             panic!("Unknown function: {name}");
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:350:25
    |
350 |                         panic!("Unknown character '{}' in lexer", c);
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
350 -                         panic!("Unknown character '{}' in lexer", c);
350 +                         panic!("Unknown character '{c}' in lexer");
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:350:25
    |
350 |                         panic!("Unknown character '{}' in lexer", c);
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
350 -                         panic!("Unknown character '{}' in lexer", c);
350 +                         panic!("Unknown character '{c}' in lexer");
    |


[style] warning: this `map_or` can be simplified
   --> src/mapper_expr.rs:585:21
    |
585 |                     function_lookup(k).map_or(false, |f| f == func)
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#unnecessary_map_or
    = note: `-W clippy::unnecessary-map-or` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::unnecessary_map_or)]`
help: use a standard comparison instead
    |
585 -                     function_lookup(k).map_or(false, |f| f == func)
585 +                     function_lookup(k) == Some(func)
    |


[style] warning: this `map_or` can be simplified
   --> src/mapper_expr.rs:585:21
    |
585 |                     function_lookup(k).map_or(false, |f| f == func)
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#unnecessary_map_or
    = note: `-W clippy::unnecessary-map-or` implied by `-W clippy::style`
    = help: to override `-W clippy::style` add `#[allow(clippy::unnecessary_map_or)]`
help: use a standard comparison instead
    |
585 -                     function_lookup(k).map_or(false, |f| f == func)
585 +                     function_lookup(k) == Some(func)
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:640:13
    |
640 |             eprintln!("Stack: {:?}, tok: {:?}", stack, tok);
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
640 -             eprintln!("Stack: {:?}, tok: {:?}", stack, tok);
640 +             eprintln!("Stack: {stack:?}, tok: {tok:?}");
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:640:13
    |
640 |             eprintln!("Stack: {:?}, tok: {:?}", stack, tok);
    |             ^^^^^^^
... [1 chars truncated] ...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
640 -             eprintln!("Stack: {:?}, tok: {:?}", stack, tok);
640 +             eprintln!("Stack: {stack:?}, tok: {tok:?}");
    |


[style] warning: this `map_or` can be simplified
   --> src/mapper_expr.rs:845:29
    |
845 | ...                   function_lookup(k).map_or(false, |f| f == func)
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#unnecessary_map_or
help: use a standard comparison instead
    |
845 -                             function_lookup(k).map_or(false, |f| f == func)
845 +                             function_lookup(k) == Some(func)
    |


[style] warning: this `map_or` can be simplified
   --> src/mapper_expr.rs:845:29
    |
845 | ...                   function_lookup(k).map_or(false, |f| f == func)
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#unnecessary_map_or
help: use a standard comparison instead
    |
845 -                             function_lookup(k).map_or(false, |f| f == func)
845 +                             function_lookup(k) == Some(func)
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:999:9
    |
999 |         panic!("Expression contains history reference of {}", oldest_samps);
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
999 -         panic!("Expression contains history reference of {}", oldest_samps);
999 +         panic!("Expression contains history reference of {oldest_samps}");
    |


[style] warning: variables can be used directly in the `format!` string
   --> src/mapper_expr.rs:999:9
    |
999 |         panic!("Expression contains history reference of {}", oldest_samps);
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#uninlined_format_args
help: change this to
    |
999 -         panic!("Expression contains history reference of {}", oldest_samps);
999 +         panic!("Expression contains history reference of {oldest_samps}");
    |


[complexity] warning: this boolean expression can be simplified
   --> src/mapper_expr.rs:675:45
    |
675 | ...   die_unless!(!rhs.next.is_some() && (rhs.tok.token_type == TokenType::Int || rhs.tok.token_type == TokenType::Float), "expected lone...
    |                   ^^^^^^^^^^^^^^^^^^^ help: try: `rhs.next.is_none()`
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#nonminimal_bool
    = note: `-W clippy::nonminimal-bool` implied by `-W clippy::complexity`
    = help: to override `-W clippy::complexity` add `#[allow(clippy::nonminimal_bool)]`


[complexity] warning: this boolean expression can be simplified
   --> src/mapper_expr.rs:688:45
    |
688 | ...   die_unless!(!rhs.next.is_some() && (rhs.tok.token_type == TokenType::Int || rhs.tok.token_type == TokenType::Float), "expected lone...
    |                   ^^^^^^^^^^^^^^^^^^^ help: try: `rhs.next.is_none()`
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#nonminimal_bool


[complexity] warning: this boolean expression can be simplified
   --> src/mapper_expr.rs:675:45
    |
675 | ...   die_unless!(!rhs.next.is_some() && (rhs.tok.token_type == TokenType::Int || rhs.tok.token_type == TokenType::Float), "expected lone...
    |                   ^^^^^^^^^^^^^^^^^^^ help: try: `rhs.next.is_none()`
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#nonminimal_bool
    = note: `-W clippy::nonminimal-bool` implied by `-W clippy::complexity`
    = help: to override `-W clippy::complexity` add `#[allow(clippy::nonminimal_bool)]`


[complexity] warning: this boolean expression can be simplified
   --> src/mapper_expr.rs:688:45
    |
688 | ...   die_unless!(!rhs.next.is_some() && (rhs.tok.token_type == TokenType::Int || rhs.tok.token_type == TokenType::Float), "expected lone...
    |                   ^^^^^^^^^^^^^^^^^^^ help: try: `rhs.next.is_none()`
    |
    = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#nonminimal_bool


```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
```
