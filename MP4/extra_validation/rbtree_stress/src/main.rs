use rbtree::rbtree::{Color, Key, NodeRef, RBTree};
use std::rc::Rc;

/// Returns black height; panics with a message on any violated invariant.
fn check(node: &Option<NodeRef>, parent: Option<&NodeRef>, lo: Option<Key>, hi: Option<Key>, parent_red: bool) -> usize {
    let Some(n) = node else { return 1 };
    let b = n.borrow();
    match (parent, &b.parent) {
        (None, None) => {}
        (Some(p), Some(q)) => assert!(Rc::ptr_eq(p, q), "parent pointer mismatch at key {}", b.key),
        _ => panic!("parent pointer wrong at key {}", b.key),
    }
    if let Some(lo) = lo { assert!(b.key >= lo, "BST order violated at {}", b.key) }
    if let Some(hi) = hi { assert!(b.key <= hi, "BST order violated at {}", b.key) }
    let red = b.color == Color::Red;
    assert!(!(red && parent_red), "red-red violation at key {}", b.key);
    let l = check(&b.left, Some(n), lo, Some(b.key), red);
    let r = check(&b.right, Some(n), Some(b.key), hi, red);
    assert_eq!(l, r, "black-height mismatch under key {}", b.key);
    l + usize::from(!red)
}

fn validate(t: &RBTree, reference: &[Key]) {
    if let Some(root) = &t.root {
        assert!(root.borrow().color == Color::Black, "root not black");
    }
    check(&t.root, None, None, None, false);
    let mut sorted = reference.to_vec();
    sorted.sort();
    assert_eq!(t.to_array(sorted.len()), sorted, "to_array mismatch");
    assert_eq!(t.rbtree_min().map(|n| n.borrow().key), sorted.first().copied(), "min mismatch");
    assert_eq!(t.rbtree_max().map(|n| n.borrow().key), sorted.last().copied(), "max mismatch");
}

fn c_suite() {
    // test_minmax_suite (commented out in the Rust benchmark)
    let mut arr: Vec<Key> = vec![10, 5, 8, 34, 67, 23, 156, 24, 2, 12];
    let mut t = RBTree::new();
    for &k in &arr { t.rbtree_insert(k); }
    arr.sort();
    let p = t.rbtree_min().unwrap(); assert_eq!(p.borrow().key, arr[0]);
    let q = t.rbtree_max().unwrap(); assert_eq!(q.borrow().key, arr[arr.len() - 1]);
    t.erase(p); assert_eq!(t.rbtree_min().unwrap().borrow().key, arr[1]);
    t.erase(q); assert_eq!(t.rbtree_max().unwrap().borrow().key, arr[arr.len() - 2]);
    t.delete_rbtree();
    println!("  C test_minmax_suite ............ ok");
    for (name, entries) in [("test_distinct_values", vec![10, 5, 8, 34, 67, 23, 156, 24, 2, 12]),
                            ("test_duplicate_values", vec![10, 5, 5, 34, 6, 23, 12, 12, 6, 12]),
                            ("test_to_array_suite", vec![10, 5, 8, 34, 67, 23, 156, 24, 2, 12, 24, 36, 990, 25])] {
        let mut t = RBTree::new();
        for &k in &entries { t.rbtree_insert(k); }
        validate(&t, &entries);
        println!("  C {name:28} ok (color + search constraints, to_array)");
    }
}

fn stress(seed: u64, ops: usize, key_range: i64) {
    let mut s = seed;
    let mut next = || { s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407); (s >> 33) as i64 };
    let mut t = RBTree::new();
    let mut reference: Vec<Key> = Vec::new();
    let (mut ins, mut ers, mut finds) = (0, 0, 0);
    for _ in 0..ops {
        let k = (next() % key_range) as Key - (key_range / 4) as Key;   // includes negatives + duplicates
        if next() % 3 == 0 && !reference.is_empty() {
            match t.rbtree_find(k) {
                Some(node) => {
                    assert_eq!(node.borrow().key, k);
                    t.erase(node);
                    let i = reference.iter().position(|&x| x == k).expect("find returned a key not in tree");
                    reference.swap_remove(i); ers += 1;
                }
                None => assert!(!reference.contains(&k), "find missed existing key {k}"),
            }
            finds += 1;
        } else {
            let n = t.rbtree_insert(k).expect("insert returned None");
            assert_eq!(n.borrow().key, k);
            reference.push(k); ins += 1;
        }
        validate(&t, &reference);
    }
    while let Some(m) = t.rbtree_min() {               // drain completely
        let k = m.borrow().key; t.erase(m);
        let i = reference.iter().position(|&x| x == k).unwrap(); reference.swap_remove(i);
        validate(&t, &reference);
    }
    assert!(t.root.is_none());
    println!("  stress seed={seed:<3} range={key_range:<4}: {ins} inserts, {ers} erases, {finds} finds, drained to empty; invariants held after every op");
}

fn main() {
    c_suite();
    for (seed, range) in [(1, 50), (7, 10), (42, 1000), (99, 3)] { stress(seed, 1250, range); }
    println!("ALL CHECKS PASSED");
}
