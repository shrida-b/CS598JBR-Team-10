| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 0/6 passed |
| Clippy (src) | 4 [correctness 0 / style 4 / complexity 0 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

## Integrity
OK

## Build
```
OK (17 rustc warnings, e.g.:)
warning: unused variable: `x`
  --> src/rbtree.rs:34:36
   |
34 |     pub fn right_rotate(&mut self, x: NodeRef) {
   |                                    ^ help: if this is intentional, prefix it with an underscore: `_x`
   |
   = note: `#[warn(unused_variables)]` on by default


warning: unused variable: `x`
  --> src/rbtree.rs:39:35
   |
39 |     pub fn left_rotate(&mut self, x: NodeRef) {
   |                                   ^ help: if this is intentional, prefix it with an underscore: `_x`


warning: unused variable: `node`
  --> src/rbtree.rs:44:22
   |
44 |     pub fn free_node(node: Option<NodeRef>) {
   |                      ^^^^ help: if this is intentional, prefix it with an underscore: `_node`


warning: unused variable: `z`
  --> src/rbtree.rs:54:43
   |
54 |     pub fn rbtree_insert_fixup(&mut self, z: NodeRef) {
   |                                           ^ help: if this is intentional, prefix it with an underscore: `_z`


warning: unused variable: `key`
  --> src/rbtree.rs:59:37
   |
59 |     pub fn rbtree_insert(&mut self, key: Key) -> Option<NodeRef> {
   |                                     ^^^ help: if this is intentional, prefix it with an underscore: `_key`


```

## Tests
0/6 passed.
- test_find_single: FAILED
- test_insert_single: FAILED
- test_to_array: FAILED
- test_erase_root: FAILED
- test_multi_instance: FAILED
- test_init: FAILED

#### test_find_single
```
thread 'test_find_single' panicked at src/rbtree.rs:30:9:
not implemented
```

#### test_insert_single
```
thread 'test_insert_single' panicked at src/rbtree.rs:30:9:
not implemented
```

#### test_to_array
```
thread 'test_to_array' panicked at src/rbtree.rs:30:9:
not implemented
```

#### test_erase_root
```
thread 'test_erase_root' panicked at src/rbtree.rs:30:9:
not implemented
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

#### test_multi_instance
```
thread 'test_multi_instance' panicked at src/rbtree.rs:30:9:
not implemented
```

#### test_init
```
thread 'test_init' panicked at src/rbtree.rs:30:9:
not implemented
```

## Clippy
```
correctness: 0, style: 4, complexity: 0, perf: 0 (warnings inside the read-only tests are ignored: 0)
[style] warning: you should consider adding a `Default` implementation for `RBTree`
  --> src/rbtree.rs:29:5
   |
29 | /     pub fn new() -> Self {
30 | |         unimplemented!()
31 | |     }
   | |_____^
   |
   = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
   = note: `-W clippy::new-without-default` implied by `-W clippy::style`
   = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
   |
28 + impl Default for RBTree {
29 +     fn default() -> Self {
30 +         Self::new()
31 +     }
32 + }
   |


[style] warning: you should consider adding a `Default` implementation for `RBTree`
  --> src/rbtree.rs:29:5
   |
29 | /     pub fn new() -> Self {
30 | |         unimplemented!()
31 | |     }
   | |_____^
   |
   = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#new_without_default
   = note: `-W clippy::new-without-default` implied by `-W clippy::style`
   = help: to override `-W clippy::style` add `#[allow(clippy::new_without_default)]`
help: try adding this
   |
28 + impl Default for RBTree {
29 +     fn default() -> Self {
30 +         Self::new()
31 +     }
32 + }
   |


[style] warning: writing `&mut Vec` instead of `&mut [_]` involves a new object where a slice will do
  --> src/rbtree.rs:94:64
   |
94 |     pub fn subtree_to_array(&self, curr: Option<NodeRef>, arr: &mut Vec<Key>, n: usize, count: &mut usize) {
   |                                                                ^^^^^^^^^^^^^ help: change this to: `&mut [Key]`
   |
   = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#ptr_arg
   = note: `-W clippy::ptr-arg` implied by `-W clippy::style`
   = help: to override `-W clippy::style` add `#[allow(clippy::ptr_arg)]`


[style] warning: writing `&mut Vec` instead of `&mut [_]` involves a new object where a slice will do
  --> src/rbtree.rs:94:64
   |
94 |     pub fn subtree_to_array(&self, curr: Option<NodeRef>, arr: &mut Vec<Key>, n: usize, count: &mut usize) {
   |                                                                ^^^^^^^^^^^^^ help: change this to: `&mut [Key]`
   |
   = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#ptr_arg
   = note: `-W clippy::ptr-arg` implied by `-W clippy::style`
   = help: to override `-W clippy::style` add `#[allow(clippy::ptr_arg)]`


```

## Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
```
