# Iteration 2/6: repair `rbtree-lab`

The controller evaluated the crate independently after your previous iteration.

| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 0/6 passed |
| Clippy (src) | 4 [correctness 0 / style 4 / complexity 0 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |

**Note:** iteration 1 scored worse (builds=0 tests_passed=6 unsafe=0 clippy_src=0) than iteration 0 (builds=1 tests_passed=0 unsafe=0 clippy_src=4). The controller reverted the code to iteration 0; the feedback below is for that restored version.

## Feedback from the evaluation

### Integrity checks
OK

### Compiler (`cargo build`)
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

### Tests (`cargo test`)
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

### Clippy (correctness / style / complexity / perf)
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

### Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
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

## Current Rust sources (supplied automatically)

### rust/src/lib.rs
```rust
pub mod rbtree;
```

### rust/src/rbtree.rs
```rust
use std::cell::RefCell;
use std::rc::Rc;

#[derive(Debug, PartialEq, Clone)]
pub enum Color {
    Red,
    Black,
}

pub type Key = i32;
pub type NodeRef = Rc<RefCell<Node>>;

#[derive(Debug, Clone)]
pub struct Node {
    pub key: Key,
    pub color: Color,
    pub left: Option<NodeRef>,   // None == NIL
    pub right: Option<NodeRef>,  // None == NIL
    pub parent: Option<NodeRef>, // None == NIL / root parent
}

#[derive(Debug, Clone)]
pub struct RBTree {
    /// Root of the tree. `None` means the tree is empty (NIL).
    pub root: Option<NodeRef>,
}

impl RBTree {
    pub fn new() -> Self {
        unimplemented!()
    }

    /// Performs a right rotation around non-NIL node `x`.
    pub fn right_rotate(&mut self, x: NodeRef) {
        unimplemented!()
    }

    /// Performs a left rotation around non-NIL node `x`.
    pub fn left_rotate(&mut self, x: NodeRef) {
        unimplemented!()
    }

    /// Recursively drops a subtree. `None` is treated as NIL.
    pub fn free_node(node: Option<NodeRef>) {
        unimplemented!()
    }

    /// Deletes the Red-Black Tree safely.
    pub fn delete_rbtree(self) {
        unimplemented!()
    }

    /// Fixes the Red-Black Tree after insertion (z must be non-NIL).
    pub fn rbtree_insert_fixup(&mut self, z: NodeRef) {
        unimplemented!()
    }

    /// Inserts a new key and returns the inserted node.
    pub fn rbtree_insert(&mut self, key: Key) -> Option<NodeRef> {
        unimplemented!()
    }

    /// Finds a node by key. Returns `None` if not found.
    pub fn rbtree_find(&self, key: Key) -> Option<NodeRef> {
        unimplemented!()
    }

    /// Returns the minimum node, or `None` if the tree is empty.
    pub fn rbtree_min(&self) -> Option<NodeRef> {
        unimplemented!()
    }

    /// Returns the maximum node, or `None` if the tree is empty.
    pub fn rbtree_max(&self) -> Option<NodeRef> {
        unimplemented!()
    }

    /// Replaces subtree rooted at `u` with subtree rooted at `v` (`None` == NIL).
    pub fn transplant(&mut self, u: NodeRef, v: Option<NodeRef>) {
        unimplemented!()
    }

    /// Fixes up after deletion starting from node `x` (`None` == NIL).
    pub fn delete_fixup(&mut self, x: Option<NodeRef>) {
        unimplemented!()
    }

    /// Erases node `p` (must be a valid non-NIL node in the tree).
    pub fn erase(&mut self, p: NodeRef) {
        unimplemented!()
    }

    /// In-order traversal of `curr` into `arr` until `n` elements (`None` == NIL).
    pub fn subtree_to_array(&self, curr: Option<NodeRef>, arr: &mut Vec<Key>, n: usize, count: &mut usize) {
        unimplemented!()
    }

    /// Returns up to `n` keys from the tree in-order.
    pub fn to_array(&self, n: usize) -> Vec<Key> {
        unimplemented!()
    }
}
```
