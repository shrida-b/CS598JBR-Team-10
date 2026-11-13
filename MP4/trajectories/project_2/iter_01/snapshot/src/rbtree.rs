use std::cell::RefCell;
use std::rc::Rc;

#[derive(Debug, PartialEq, Eq, Clone)]
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

#[derive(Debug, Clone, Default)]
pub struct RBTree {
    /// Root of the tree. `None` means the tree is empty (NIL).
    pub root: Option<NodeRef>,
}

impl Drop for RBTree {
    fn drop(&mut self) {
        let root = self.root.take();
        Self::free_node(root);
    }
}

fn get_color(node: &Option<NodeRef>) -> Color {
    match node {
        Some(n) => n.borrow().color.clone(),
        None => Color::Black,
    }
}

fn is_same_node(a: &Option<NodeRef>, b: &Option<NodeRef>) -> bool {
    match (a, b) {
        (Some(na), Some(nb)) => Rc::ptr_eq(na, nb),
        (None, None) => true,
        _ => false,
    }
}

impl RBTree {
    pub fn new() -> Self {
        RBTree { root: None }
    }

    /// Performs a right rotation around non-NIL node `x`.
    pub fn right_rotate(&mut self, x: NodeRef) {
        let y = match x.borrow().left.clone() {
            Some(y) => y,
            None => return,
        };

        let y_right = y.borrow().right.clone();
        x.borrow_mut().left = y_right.clone();

        if let Some(ref yr) = y_right {
            yr.borrow_mut().parent = Some(x.clone());
        }

        let x_parent = x.borrow().parent.clone();
        y.borrow_mut().parent = x_parent.clone();

        if let Some(ref xp) = x_parent {
            let is_left = match xp.borrow().left {
                Some(ref l) => Rc::ptr_eq(l, &x),
                None => false,
            };
            if is_left {
                xp.borrow_mut().left = Some(y.clone());
            } else {
                xp.borrow_mut().right = Some(y.clone());
            }
        } else {
            self.root = Some(y.clone());
        }

        y.borrow_mut().right = Some(x.clone());
        x.borrow_mut().parent = Some(y);
    }

    /// Performs a left rotation around non-NIL node `x`.
    pub fn left_rotate(&mut self, x: NodeRef) {
        let y = match x.borrow().right.clone() {
            Some(y) => y,
            None => return,
        };

        let y_left = y.borrow().left.clone();
        x.borrow_mut().right = y_left.clone();

        if let Some(ref yl) = y_left {
            yl.borrow_mut().parent = Some(x.clone());
        }

        let x_parent = x.borrow().parent.clone();
        y.borrow_mut().parent = x_parent.clone();

        if let Some(ref xp) = x_parent {
            let is_left = match xp.borrow().left {
                Some(ref l) => Rc::ptr_eq(l, &x),
                None => false,
            };
            if is_left {
                xp.borrow_mut().left = Some(y.clone());
            } else {
                xp.borrow_mut().right = Some(y.clone());
            }
        } else {
            self.root = Some(y.clone());
        }

        y.borrow_mut().left = Some(x.clone());
        x.borrow_mut().parent = Some(y);
    }

    /// Recursively drops a subtree. `None` is treated as NIL.
    pub fn free_node(node: Option<NodeRef>) {
        if let Some(n) = node {
            let left = n.borrow_mut().left.take();
            let right = n.borrow_mut().right.take();
            n.borrow_mut().parent.take();
            Self::free_node(left);
            Self::free_node(right);
        }
    }

    /// Deletes the Red-Black Tree safely.
    pub fn delete_rbtree(mut self) {
        let root = self.root.take();
        Self::free_node(root);
    }

    /// Fixes the Red-Black Tree after insertion (z must be non-NIL).
    pub fn rbtree_insert_fixup(&mut self, mut z: NodeRef) {
        loop {
            let parent = z.borrow().parent.clone();
            let parent = match parent {
                Some(p) if p.borrow().color == Color::Red => p,
                _ => break,
            };

            let gparent = parent
                .borrow()
                .parent
                .clone()
                .expect("parent is Red, so grandparent must exist");

            let parent_is_left = match gparent.borrow().left {
                Some(ref l) => Rc::ptr_eq(l, &parent),
                None => false,
            };

            if parent_is_left {
                let uncle = gparent.borrow().right.clone();
                let uncle_is_red =
                    uncle.as_ref().is_some_and(|u| u.borrow().color == Color::Red);

                if uncle_is_red {
                    let uncle = uncle.unwrap();
                    parent.borrow_mut().color = Color::Black;
                    uncle.borrow_mut().color = Color::Black;
                    gparent.borrow_mut().color = Color::Red;
                    z = gparent;
                } else {
                    let z_is_right = match parent.borrow().right {
                        Some(ref r) => Rc::ptr_eq(r, &z),
                        None => false,
                    };
                    if z_is_right {
                        z = parent.clone();
                        self.left_rotate(z.clone());
                    }
                    let current_parent = z.borrow().parent.clone().unwrap();
                    let current_gparent = current_parent.borrow().parent.clone().unwrap();
                    current_parent.borrow_mut().color = Color::Black;
                    current_gparent.borrow_mut().color = Color::Red;
                    self.right_rotate(current_gparent);
                }
            } else {
                let uncle = gparent.borrow().left.clone();
                let uncle_is_red =
                    uncle.as_ref().is_some_and(|u| u.borrow().color == Color::Red);

                if uncle_is_red {
                    let uncle = uncle.unwrap();
                    parent.borrow_mut().color = Color::Black;
                    uncle.borrow_mut().color = Color::Black;
                    gparent.borrow_mut().color = Color::Red;
                    z = gparent;
                } else {
                    let z_is_left = match parent.borrow().left {
                        Some(ref l) => Rc::ptr_eq(l, &z),
                        None => false,
                    };
                    if z_is_left {
                        z = parent.clone();
                        self.right_rotate(z.clone());
                    }
                    let current_parent = z.borrow().parent.clone().unwrap();
                    let current_gparent = current_parent.borrow().parent.clone().unwrap();
                    current_parent.borrow_mut().color = Color::Black;
                    current_gparent.borrow_mut().color = Color::Red;
                    self.left_rotate(current_gparent);
                }
            }
        }

        if let Some(ref root) = self.root {
            root.borrow_mut().color = Color::Black;
        }
    }

    /// Inserts a new key and returns the inserted node.
    pub fn rbtree_insert(&mut self, key: Key) -> Option<NodeRef> {
        let z = Rc::new(RefCell::new(Node {
            key,
            color: Color::Red,
            left: None,
            right: None,
            parent: None,
        }));

        let mut y: Option<NodeRef> = None;
        let mut x: Option<NodeRef> = self.root.clone();

        while let Some(curr) = x {
            y = Some(curr.clone());
            if key < curr.borrow().key {
                x = curr.borrow().left.clone();
            } else {
                x = curr.borrow().right.clone();
            }
        }

        z.borrow_mut().parent = y.clone();

        if let Some(ref y_node) = y {
            if key < y_node.borrow().key {
                y_node.borrow_mut().left = Some(z.clone());
            } else {
                y_node.borrow_mut().right = Some(z.clone());
            }
        } else {
            self.root = Some(z.clone());
        }

        self.rbtree_insert_fixup(z.clone());
        Some(z)
    }

    /// Finds a node by key. Returns `None` if not found.
    pub fn rbtree_find(&self, key: Key) -> Option<NodeRef> {
        let mut current = self.root.clone();
        while let Some(curr) = current {
            let curr_key = curr.borrow().key;
            if curr_key == key {
                return Some(curr);
            }
            if key < curr_key {
                current = curr.borrow().left.clone();
            } else {
                current = curr.borrow().right.clone();
            }
        }
        None
    }

    /// Returns the minimum node, or `None` if the tree is empty.
    pub fn rbtree_min(&self) -> Option<NodeRef> {
        let mut curr = self.root.clone()?;
        while let Some(left) = curr.clone().borrow().left.clone() {
            curr = left;
        }
        Some(curr)
    }

    /// Returns the maximum node, or `None` if the tree is empty.
    pub fn rbtree_max(&self) -> Option<NodeRef> {
        let mut curr = self.root.clone()?;
        while let Some(right) = curr.clone().borrow().right.clone() {
            curr = right;
        }
        Some(curr)
    }

    /// Replaces subtree rooted at `u` with subtree rooted at `v` (`None` == NIL).
    pub fn transplant(&mut self, u: NodeRef, v: Option<NodeRef>) {
        let u_parent = u.borrow().parent.clone();
        if let Some(ref p) = u_parent {
            let is_left = match p.borrow().left {
                Some(ref l) => Rc::ptr_eq(l, &u),
                None => false,
            };
            if is_left {
                p.borrow_mut().left = v.clone();
            } else {
                p.borrow_mut().right = v.clone();
            }
        } else {
            self.root = v.clone();
        }
        if let Some(ref v_node) = v {
            v_node.borrow_mut().parent = u_parent;
        }
    }

    /// Fixes up after deletion starting from node `x` (`None` == NIL).
    pub fn delete_fixup(&mut self, mut x: Option<NodeRef>) {
        while !is_same_node(&x, &self.root) && get_color(&x) == Color::Black {
            let x_node = match x.clone() {
                Some(n) => n,
                None => break,
            };
            let parent = match x_node.borrow().parent.clone() {
                Some(p) => p,
                None => break,
            };

            let is_left = match parent.borrow().left {
                Some(ref l) => Rc::ptr_eq(l, &x_node),
                None => false,
            };

            if is_left {
                let mut w = parent.borrow().right.clone();
                if get_color(&w) == Color::Red {
                    if let Some(ref w_node) = w {
                        w_node.borrow_mut().color = Color::Black;
                    }
                    parent.borrow_mut().color = Color::Red;
                    self.left_rotate(parent.clone());
                    w = parent.borrow().right.clone();
                }

                let w_node = match w {
                    Some(ref n) => n.clone(),
                    None => {
                        x = Some(parent);
                        continue;
                    }
                };

                let w_left = w_node.borrow().left.clone();
                let w_right = w_node.borrow().right.clone();

                if get_color(&w_left) == Color::Black && get_color(&w_right) == Color::Black {
                    w_node.borrow_mut().color = Color::Red;
                    x = Some(parent);
                } else {
                    if get_color(&w_right) == Color::Black {
                        if let Some(ref wl) = w_left {
                            wl.borrow_mut().color = Color::Black;
                        }
                        w_node.borrow_mut().color = Color::Red;
                        self.right_rotate(w_node.clone());
                    }

                    let w_node = parent.borrow().right.clone().unwrap();
                    let parent_color = parent.borrow().color.clone();
                    w_node.borrow_mut().color = parent_color;
                    parent.borrow_mut().color = Color::Black;
                    if let Some(ref wr) = w_node.borrow().right.clone() {
                        wr.borrow_mut().color = Color::Black;
                    }
                    self.left_rotate(parent.clone());
                    x = self.root.clone();
                }
            } else {
                let mut w = parent.borrow().left.clone();
                if get_color(&w) == Color::Red {
                    if let Some(ref w_node) = w {
                        w_node.borrow_mut().color = Color::Black;
                    }
                    parent.borrow_mut().color = Color::Red;
                    self.right_rotate(parent.clone());
                    w = parent.borrow().left.clone();
                }

                let w_node = match w {
                    Some(ref n) => n.clone(),
                    None => {
                        x = Some(parent);
                        continue;
                    }
                };

                let w_left = w_node.borrow().left.clone();
                let w_right = w_node.borrow().right.clone();

                if get_color(&w_right) == Color::Black && get_color(&w_left) == Color::Black {
                    w_node.borrow_mut().color = Color::Red;
                    x = Some(parent);
                } else {
                    if get_color(&w_left) == Color::Black {
                        if let Some(ref wr) = w_right {
                            wr.borrow_mut().color = Color::Black;
                        }
                        w_node.borrow_mut().color = Color::Red;
                        self.left_rotate(w_node.clone());
                    }

                    let w_node = parent.borrow().left.clone().unwrap();
                    let parent_color = parent.borrow().color.clone();
                    w_node.borrow_mut().color = parent_color;
                    parent.borrow_mut().color = Color::Black;
                    if let Some(ref wl) = w_node.borrow().left.clone() {
                        wl.borrow_mut().color = Color::Black;
                    }
                    self.right_rotate(parent.clone());
                    x = self.root.clone();
                }
            }
        }

        if let Some(ref x_node) = x {
            x_node.borrow_mut().color = Color::Black;
        }
    }

    /// Erases node `p` (must be a valid non-NIL node in the tree).
    pub fn erase(&mut self, p: NodeRef) {
        let mut y = p.clone();
        let mut y_original_color = y.borrow().color.clone();

        let p_left = p.borrow().left.clone();
        let p_right = p.borrow().right.clone();

        let x: Option<NodeRef>;
        let mut sentinel_opt: Option<NodeRef> = None;

        if p_left.is_none() {
            if let Some(ref r) = p_right {
                x = Some(r.clone());
                self.transplant(p.clone(), Some(r.clone()));
            } else if p.borrow().parent.is_some() {
                let s = Rc::new(RefCell::new(Node {
                    key: 0,
                    color: Color::Black,
                    left: None,
                    right: None,
                    parent: None,
                }));
                self.transplant(p.clone(), Some(s.clone()));
                x = Some(s.clone());
                sentinel_opt = Some(s);
            } else {
                self.transplant(p.clone(), None);
                x = None;
            }
        } else if p_right.is_none() {
            if let Some(ref l) = p_left {
                x = Some(l.clone());
                self.transplant(p.clone(), Some(l.clone()));
            } else if p.borrow().parent.is_some() {
                let s = Rc::new(RefCell::new(Node {
                    key: 0,
                    color: Color::Black,
                    left: None,
                    right: None,
                    parent: None,
                }));
                self.transplant(p.clone(), Some(s.clone()));
                x = Some(s.clone());
                sentinel_opt = Some(s);
            } else {
                self.transplant(p.clone(), None);
                x = None;
            }
        } else {
            let mut min_y = p_right.clone().unwrap();
            while let Some(left) = min_y.clone().borrow().left.clone() {
                min_y = left;
            }
            y = min_y;
            y_original_color = y.borrow().color.clone();

            let y_right = y.borrow().right.clone();
            if let Some(ref r) = y_right {
                x = Some(r.clone());
            } else {
                let s = Rc::new(RefCell::new(Node {
                    key: 0,
                    color: Color::Black,
                    left: None,
                    right: None,
                    parent: None,
                }));
                x = Some(s.clone());
                sentinel_opt = Some(s);
            }

            let y_parent = y.borrow().parent.clone().unwrap();
            if Rc::ptr_eq(&y_parent, &p) {
                if let Some(ref x_node) = x {
                    x_node.borrow_mut().parent = Some(y.clone());
                }
            } else {
                self.transplant(y.clone(), x.clone());
                y.borrow_mut().right = p.borrow().right.clone();
                if let Some(ref yr) = y.borrow().right {
                    yr.borrow_mut().parent = Some(y.clone());
                }
            }

            self.transplant(p.clone(), Some(y.clone()));
            y.borrow_mut().left = p.borrow().left.clone();
            if let Some(ref yl) = y.borrow().left {
                yl.borrow_mut().parent = Some(y.clone());
            }
            y.borrow_mut().color = p.borrow().color.clone();
        }

        if y_original_color == Color::Black {
            self.delete_fixup(x);
        }

        if let Some(s) = sentinel_opt {
            if let Some(sp) = s.borrow().parent.clone() {
                if match sp.borrow().left {
                    Some(ref l) => Rc::ptr_eq(l, &s),
                    None => false,
                } {
                    sp.borrow_mut().left = None;
                }
                if match sp.borrow().right {
                    Some(ref r) => Rc::ptr_eq(r, &s),
                    None => false,
                } {
                    sp.borrow_mut().right = None;
                }
            }
            if match self.root {
                Some(ref r) => Rc::ptr_eq(r, &s),
                None => false,
            } {
                self.root = None;
            }
            s.borrow_mut().parent = None;
        }

        p.borrow_mut().left = None;
        p.borrow_mut().right = None;
        p.borrow_mut().parent = None;
    }

    /// In-order traversal of `curr` into `arr` until `n` elements (`None` == NIL).
    #[allow(clippy::only_used_in_recursion)]
    pub fn subtree_to_array(
        &self,
        curr: Option<NodeRef>,
        arr: &mut Vec<Key>,
        n: usize,
        count: &mut usize,
    ) {
        let node = match curr {
            Some(n) => n,
            None => return,
        };
        self.subtree_to_array(node.borrow().left.clone(), arr, n, count);
        if *count < n {
            arr.push(node.borrow().key);
            *count += 1;
        } else {
            return;
        }
        self.subtree_to_array(node.borrow().right.clone(), arr, n, count);
    }

    /// Returns up to `n` keys from the tree in-order.
    pub fn to_array(&self, n: usize) -> Vec<Key> {
        let mut arr = Vec::new();
        let mut count = 0;
        if let Some(ref root) = self.root {
            self.subtree_to_array(Some(root.clone()), &mut arr, n, &mut count);
        }
        arr
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn check_search_constraint(
        node: &Option<NodeRef>,
        min: Option<Key>,
        max: Option<Key>,
    ) -> bool {
        let n = match node {
            Some(n) => n,
            None => return true,
        };
        let key = n.borrow().key;
        if let Some(min_val) = min {
            if key < min_val {
                return false;
            }
        }
        if let Some(max_val) = max {
            if key > max_val {
                return false;
            }
        }
        check_search_constraint(&n.borrow().left, min, Some(key))
            && check_search_constraint(&n.borrow().right, Some(key), max)
    }

    fn check_color_constraint(
        node: &Option<NodeRef>,
        parent_color: Color,
        black_depth: usize,
        max_black_depth: &mut Option<usize>,
    ) -> bool {
        let n = match node {
            Some(n) => n,
            None => {
                if let Some(max_d) = max_black_depth {
                    if black_depth != *max_d {
                        return false;
                    }
                } else {
                    *max_black_depth = Some(black_depth);
                }
                return true;
            }
        };
        if parent_color == Color::Red && n.borrow().color == Color::Red {
            return false;
        }
        let current_color = n.borrow().color.clone();
        let next_depth = black_depth + if current_color == Color::Black { 1 } else { 0 };
        check_color_constraint(
            &n.borrow().left,
            current_color.clone(),
            next_depth,
            max_black_depth,
        ) && check_color_constraint(
            &n.borrow().right,
            current_color,
            next_depth,
            max_black_depth,
        )
    }

    fn verify_rbtree(tree: &RBTree) {
        if let Some(ref root) = tree.root {
            assert_eq!(root.borrow().color, Color::Black);
        }
        assert!(check_search_constraint(&tree.root, None, None));
        let mut max_black_depth = None;
        assert!(check_color_constraint(
            &tree.root,
            Color::Black,
            0,
            &mut max_black_depth
        ));
    }

    #[test]
    fn test_minmax_suite() {
        let mut t = RBTree::new();
        let arr = vec![10, 5, 8, 34, 67, 23, 156, 24, 2, 12];
        for &k in &arr {
            t.rbtree_insert(k);
            verify_rbtree(&t);
        }

        let mut sorted = arr.clone();
        sorted.sort();

        let min_node = t.rbtree_min().unwrap();
        assert_eq!(min_node.borrow().key, sorted[0]);

        let max_node = t.rbtree_max().unwrap();
        assert_eq!(max_node.borrow().key, sorted[sorted.len() - 1]);

        t.erase(min_node);
        verify_rbtree(&t);
        let min_node2 = t.rbtree_min().unwrap();
        assert_eq!(min_node2.borrow().key, sorted[1]);

        t.erase(max_node);
        verify_rbtree(&t);
        let max_node2 = t.rbtree_max().unwrap();
        assert_eq!(max_node2.borrow().key, sorted[sorted.len() - 2]);
    }

    #[test]
    fn test_erase_all() {
        let mut t = RBTree::new();
        let arr = vec![10, 5, 8, 34, 67, 23, 156, 24, 2, 12];
        let mut nodes = Vec::new();
        for &k in &arr {
            nodes.push(t.rbtree_insert(k).unwrap());
            verify_rbtree(&t);
        }
        for n in nodes {
            t.erase(n);
            verify_rbtree(&t);
        }
        assert!(t.root.is_none());
    }

    #[test]
    fn test_duplicates() {
        let mut t = RBTree::new();
        let arr = vec![10, 5, 5, 34, 6, 23, 12, 12, 6, 12];
        for &k in &arr {
            t.rbtree_insert(k);
            verify_rbtree(&t);
        }
    }

    #[test]
    fn test_delete_rbtree_explicit() {
        let mut t = RBTree::new();
        t.rbtree_insert(10);
        t.rbtree_insert(20);
        t.delete_rbtree();
    }
}
