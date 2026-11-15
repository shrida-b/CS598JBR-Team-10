# Iteration 2/6: repair `expr`

The controller evaluated the crate independently after your previous iteration.

| Check | Result |
|---|---|
| Integrity | OK |
| Build | OK |
| Tests | 2/2 passed |
| Clippy (src) | 2 [correctness 0 / style 0 / complexity 2 / perf 0] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | present |



## Feedback from the evaluation

### Integrity checks
OK

### Compiler (`cargo build`)
```
OK (2 rustc warnings, e.g.:)
warning: type `Token` is more private than the item `ExprNode::tok`
   --> src/mapper_expr.rs:385:5
    |
385 |     pub tok: Token,
    |     ^^^^^^^^^^^^^^ field `ExprNode::tok` is reachable at visibility `pub`
    |
note: but type `Token` is only usable at visibility `pub(self)`
   --> src/mapper_expr.rs:198:1
    |
198 | struct Token {
    | ^^^^^^^^^^^^
    = note: `#[warn(private_interfaces)]` on by default


warning: unused import: `expr::mapper_expr`
 --> src/bin/test.rs:1:5
  |
1 | use expr::mapper_expr;
  |     ^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(unused_imports)]` on by default


```

### Tests (`cargo test`)
2/2 passed.

### Clippy (correctness / style / complexity / perf)
```
correctness: 0, style: 0, complexity: 2, perf: 0 (warnings inside the read-only tests are ignored: 4)
[complexity] warning: the following explicit lifetimes could be elided: 'a
    --> src/mapper_expr.rs:1132:29
     |
1132 | pub fn mapper_expr_evaluate<'a>(
     |                             ^^
1133 |     mapper: &mut MapperExpr,
1134 |     input: &'a MapperSignalValue,
     |             ^^
     |
     = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
     = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
     = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
     |
1132 ~ pub fn mapper_expr_evaluate(
1133 |     mapper: &mut MapperExpr,
1134 ~     input: &MapperSignalValue,
     |


[complexity] warning: the following explicit lifetimes could be elided: 'a
    --> src/mapper_expr.rs:1132:29
     |
1132 | pub fn mapper_expr_evaluate<'a>(
     |                             ^^
1133 |     mapper: &mut MapperExpr,
1134 |     input: &'a MapperSignalValue,
     |             ^^
     |
     = help: for further information visit https://rust-lang.github.io/rust-clippy/master/index.html#needless_lifetimes
     = note: `-W clippy::needless-lifetimes` implied by `-W clippy::complexity`
     = help: to override `-W clippy::complexity` add `#[allow(clippy::needless_lifetimes)]`
help: elide the lifetimes
     |
1132 ~ pub fn mapper_expr_evaluate(
1133 |     mapper: &mut MapperExpr,
1134 ~     input: &MapperSignalValue,
     |


```

### Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 1, "primary_total": 0}
```

## Required public API (must all be present with these exact signatures)
- [mapper_expr] pub enum MapperSignalValue
- [mapper_expr] pub struct ExprNode
- [mapper_expr] pub struct MapperExpr
- [mapper_expr] pub enum state_t
- [mapper_expr] pub fn as_f32(&self) -> Option<f32>
- [mapper_expr] pub fn as_i32(&self) -> Option<i32>
- [mapper_expr] pub fn new() -> ExprNode
- [mapper_expr] pub fn expr_free(&self)
- [mapper_expr] pub fn mapper_expr_new_from_string(s: &str, input_is_float: i32, output_is_float: i32, vector_size: i32)-> MapperExpr
- [mapper_expr] pub fn mapper_expr_evaluate<'a>(mapper: &mut MapperExpr, input: &'a MapperSignalValue) -> MapperSignalValue

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

## Current Rust sources and original C sources (supplied automatically)

### rust/src/lib.rs
```rust
#![forbid(unsafe_code)]
pub mod mapper_expr;

```

### rust/src/mapper_expr.rs
```rust
use std::collections::HashMap;
use std::f32::consts::PI;
use std::sync::Arc;

#[derive(Clone, Copy, Debug)]
pub enum MapperSignalValue {
    F(f32),
    I32(i32),
}

impl MapperSignalValue {
    pub fn as_f32(&self) -> Option<f32> {
        match self {
            MapperSignalValue::F(v) => Some(*v),
            MapperSignalValue::I32(_) => None,
        }
    }

    pub fn as_i32(&self) -> Option<i32> {
        match self {
            MapperSignalValue::I32(v) => Some(*v),
            MapperSignalValue::F(_) => None,
        }
    }

    fn coerce_f32(self) -> f32 {
        match self {
            MapperSignalValue::F(v) => v,
            MapperSignalValue::I32(v) => v as f32,
        }
    }

    fn coerce_i32(self) -> i32 {
        match self {
            MapperSignalValue::I32(v) => v,
            MapperSignalValue::F(v) => v as i32,
        }
    }
}

const STACK_SIZE: usize = 256;
const TRACING: bool = false;

macro_rules! trace {
    ($($arg:tt)*) => {
        if TRACING {
            println!("-- {}", format!($($arg)*));
        }
    };
}

macro_rules! die_unless {
    ($cond:expr, $($arg:tt)*) => {
        if !$cond {
            println!("-- {}", format!($($arg)*));
            assert!($cond);
        }
    };
}

fn minf(x: f32, y: f32) -> f32 {
    if y < x {
        y
    } else {
        x
    }
}

fn maxf(x: f32, y: f32) -> f32 {
    if y > x {
        y
    } else {
        x
    }
}

fn pif() -> f32 {
    PI
}

fn logbf(x: f32) -> f32 {
    if x.is_nan() {
        x
    } else if x == 0.0 {
        f32::NEG_INFINITY
    } else if x.is_infinite() {
        f32::INFINITY
    } else {
        let bits = x.to_bits();
        let exp = ((bits >> 23) & 0xff) as i32;
        if exp == 0 {
            let mant = bits & 0x7f_ffff;
            (-127 - (mant.leading_zeros() as i32 - 9)) as f32
        } else {
            (exp - 127) as f32
        }
    }
}

#[allow(dead_code)]
#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExprFunc {
    Unknown = -1,
    Pow = 0,
    Sin,
    Cos,
    Tan,
    Abs,
    Sqrt,
    Log,
    Log10,
    Exp,
    Floor,
    Round,
    Ceil,
    Asin,
    Acos,
    Atan,
    Atan2,
    Sinh,
    Cosh,
    Tanh,
    Logb,
    Exp2,
    Log2,
    Hypot,
    Cbrt,
    Trunc,
    Min,
    Max,
    Pi,
    NFuncs,
}

#[derive(Debug, Clone, Copy)]
struct FunctionEntry {
    name: &'static str,
    arity: u32,
    func: fn(f32, f32) -> f32,
}

lazy_static::lazy_static! {
    static ref FUNCTION_TABLE: HashMap<&'static str, FunctionEntry> = {
        let mut m = HashMap::new();
        m.insert("pow", FunctionEntry { name: "pow", arity: 2, func: f32::powf });
        m.insert("sin", FunctionEntry { name: "sin", arity: 1, func: |x, _| x.sin() });
        m.insert("cos", FunctionEntry { name: "cos", arity: 1, func: |x, _| x.cos() });
        m.insert("tan", FunctionEntry { name: "tan", arity: 1, func: |x, _| x.tan() });
        m.insert("abs", FunctionEntry { name: "abs", arity: 1, func: |x, _| x.abs() });
        m.insert("sqrt", FunctionEntry { name: "sqrt", arity: 1, func: |x, _| x.sqrt() });
        m.insert("log", FunctionEntry { name: "log", arity: 1, func: |x, _| x.ln() });
        m.insert("log10", FunctionEntry { name: "log10", arity: 1, func: |x, _| x.log10() });
        m.insert("exp", FunctionEntry { name: "exp", arity: 1, func: |x, _| x.exp() });
        m.insert("floor", FunctionEntry { name: "floor", arity: 1, func: |x, _| x.floor() });
        m.insert("round", FunctionEntry { name: "round", arity: 1, func: |x, _| x.round() });
        m.insert("ceil", FunctionEntry { name: "ceil", arity: 1, func: |x, _| x.ceil() });
        m.insert("asin", FunctionEntry { name: "asin", arity: 1, func: |x, _| x.asin() });
        m.insert("acos", FunctionEntry { name: "acos", arity: 1, func: |x, _| x.acos() });
        m.insert("atan", FunctionEntry { name: "atan", arity: 1, func: |x, _| x.atan() });
        m.insert("atan2", FunctionEntry { name: "atan2", arity: 2, func: f32::atan2 });
        m.insert("sinh", FunctionEntry { name: "sinh", arity: 1, func: |x, _| x.sinh() });
        m.insert("cosh", FunctionEntry { name: "cosh", arity: 1, func: |x, _| x.cosh() });
        m.insert("tanh", FunctionEntry { name: "tanh", arity: 1, func: |x, _| x.tanh() });
        m.insert("logb", FunctionEntry { name: "logb", arity: 1, func: |x, _| logbf(x) });
        m.insert("exp2", FunctionEntry { name: "exp2", arity: 1, func: |x, _| x.exp2() });
        m.insert("log2", FunctionEntry { name: "log2", arity: 1, func: |x, _| x.log2() });
        m.insert("hypot", FunctionEntry { name: "hypot", arity: 2, func: f32::hypot });
        m.insert("cbrt", FunctionEntry { name: "cbrt", arity: 1, func: |x, _| x.cbrt() });
        m.insert("trunc", FunctionEntry { name: "trunc", arity: 1, func: |x, _| x.trunc() });
        m.insert("min", FunctionEntry { name: "min", arity: 2, func: minf });
        m.insert("max", FunctionEntry { name: "max", arity: 2, func: maxf });
        m.insert("pi", FunctionEntry { name: "pi", arity: 0, func: |_, _| pif() });
        m
    };
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TokenType {
    Float,
    Int,
    Op,
    OpenParen,
    CloseParen,
    Var,
    OpenSquare,
    CloseSquare,
    OpenCurly,
    CloseCurly,
    Func,
    Comma,
    End,
    ToFloat,
    ToInt32,
}

#[derive(Debug, Clone, Copy)]
struct Token {
    token_type: TokenType,
    value: Option<f32>,
    int_value: Option<i32>,
    var: Option<char>,
    op: Option<char>,
    func: Option<&'static FunctionEntry>,
}

impl Token {
    fn simple(token_type: TokenType) -> Self {
        Self {
            token_type,
            value: None,
            int_value: None,
            var: None,
            op: None,
            func: None,
        }
    }

    fn float(val: f32) -> Self {
        Self {
            token_type: TokenType::Float,
            value: Some(val),
            int_value: None,
            var: None,
            op: None,
            func: None,
        }
    }

    fn int(val: i32) -> Self {
        Self {
            token_type: TokenType::Int,
            value: None,
            int_value: Some(val),
            var: None,
            op: None,
            func: None,
        }
    }

    fn op(c: char) -> Self {
        Self {
            token_type: TokenType::Op,
            value: None,
            int_value: None,
            var: None,
            op: Some(c),
            func: None,
        }
    }

    fn var(c: char) -> Self {
        Self {
            token_type: TokenType::Var,
            value: None,
            int_value: None,
            var: Some(c),
            op: None,
            func: None,
        }
    }

    fn func(entry: Option<&'static FunctionEntry>) -> Self {
        Self {
            token_type: TokenType::Func,
            value: None,
            int_value: None,
            var: None,
            op: None,
            func: entry,
        }
    }
}

fn function_lookup(s: &str) -> Option<&'static FunctionEntry> {
    FUNCTION_TABLE.get(s)
}

fn expr_lex(s: &str) -> Result<Vec<Token>, &'static str> {
    let bytes = s.as_bytes();
    let mut i = 0;
    let mut tokens = Vec::new();

    loop {
        while i < bytes.len() && bytes[i].is_ascii_whitespace() {
            i += 1;
        }
        if i >= bytes.len() {
            tokens.push(Token::simple(TokenType::End));
            return Ok(tokens);
        }

        let b = bytes[i];
        if b.is_ascii_digit() {
            let start = i;
            while i < bytes.len() && bytes[i].is_ascii_digit() {
                i += 1;
            }
            if i < bytes.len() && bytes[i] == b'.' {
                i += 1;
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1;
                }
                let val = s[start..i]
                    .parse::<f32>()
                    .map_err(|_| "Invalid float literal in lexer.")?;
                tokens.push(Token::float(val));
            } else {
                let val = s[start..i]
                    .parse::<i32>()
                    .map_err(|_| "Invalid integer literal in lexer.")?;
                tokens.push(Token::int(val));
            }
        } else if b == b'.' {
            let start = i;
            i += 1;
            if i < bytes.len() && bytes[i].is_ascii_digit() {
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1;
                }
                let val = s[start..i]
                    .parse::<f32>()
                    .map_err(|_| "Invalid float literal in lexer.")?;
                tokens.push(Token::float(val));
            } else {
                return Err("Error in lexical analysis.");
            }
        } else {
            match b {
                b'+' | b'-' | b'/' | b'*' | b'=' => {
                    tokens.push(Token::op(b as char));
                    i += 1;
                }
                b'(' => {
                    tokens.push(Token::simple(TokenType::OpenParen));
                    i += 1;
                }
                b')' => {
                    tokens.push(Token::simple(TokenType::CloseParen));
                    i += 1;
                }
                b'x' | b'y' => {
                    tokens.push(Token::var(b as char));
                    i += 1;
                }
                b'[' => {
                    tokens.push(Token::simple(TokenType::OpenSquare));
                    i += 1;
                }
                b']' => {
                    tokens.push(Token::simple(TokenType::CloseSquare));
                    i += 1;
                }
                b'{' => {
                    tokens.push(Token::simple(TokenType::OpenCurly));
                    i += 1;
                }
                b'}' => {
                    tokens.push(Token::simple(TokenType::CloseCurly));
                    i += 1;
                }
                b',' => {
                    tokens.push(Token::simple(TokenType::Comma));
                    i += 1;
                }
                _ if b.is_ascii_alphabetic() => {
                    let start = i;
                    while i < bytes.len() && bytes[i].is_ascii_alphanumeric() {
                        i += 1;
                    }
                    let name = &s[start..i];
                    tokens.push(Token::func(function_lookup(name)));
                }
                _ => {
                    println!("unknown character '{}' in lexer", b as char);
                    return Err("Error in lexical analysis.");
                }
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct ExprNode {
    pub tok: Token,
    pub is_float: i32,
    pub history_index: i32,
    pub vector_index: i32,
    pub next: Option<Arc<ExprNode>>,
}

pub struct MapperExpr {
    pub node: ExprNode,
    pub vector_size: i32,
    pub history_size: i32,
    pub history_pos: i32,
    pub input_history: Vec<MapperSignalValue>,
    pub output_history: Vec<MapperSignalValue>,
}

#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum state_t {
    YEQUAL_Y,
    YEQUAL_EQ,
    EXPR,
    EXPR_RIGHT,
    TERM,
    TERM_RIGHT,
    VALUE,
    NEGATE,
    VAR_RIGHT,
    VAR_VECTINDEX,
    VAR_HISTINDEX,
    CLOSE_VECTINDEX,
    CLOSE_HISTINDEX,
    OPEN_PAREN,
    CLOSE_PAREN,
    COMMA,
    END,
}

#[allow(non_camel_case_types)]
enum stack_obj_t {
    State(state_t),
    Node(ExprNode),
}

impl ExprNode {
    pub fn new() -> ExprNode {
        ExprNode {
            tok: Token::simple(TokenType::End),
            is_float: 0,
            history_index: 0,
            vector_index: 0,
            next: None,
        }
    }

    fn with_token(tok: Token, is_float: i32) -> ExprNode {
        ExprNode {
            tok,
            is_float,
            history_index: 0,
            vector_index: 0,
            next: None,
        }
    }

    pub fn expr_free(&self) {}
}

impl Default for ExprNode {
    fn default() -> Self {
        Self::new()
    }
}

fn printtoken(t: &Token) {
    match t.token_type {
        TokenType::Float => print!("{}", t.value.unwrap_or(0.0)),
        TokenType::Int => print!("{}", t.int_value.unwrap_or(0)),
        TokenType::Op => print!("{}", t.op.unwrap_or('?')),
        TokenType::OpenParen => print!("("),
        TokenType::CloseParen => print!(")"),
        TokenType::Var => print!("VAR({})", t.var.unwrap_or('?')),
        TokenType::OpenSquare => print!("["),
        TokenType::CloseSquare => print!("]"),
        TokenType::OpenCurly => print!("{{"),
        TokenType::CloseCurly => print!("}}"),
        TokenType::Func => print!("FUNC({})", t.func.map_or("unknown", |f| f.name)),
        TokenType::Comma => print!(","),
        TokenType::End => print!("END"),
        TokenType::ToFloat => print!("(float)"),
        TokenType::ToInt32 => print!("(int32)"),
    }
}

fn printexprnode(s: &str, list: &ExprNode) {
    print!("{s}");
    let mut cur = Some(list);
    while let Some(node) = cur {
        if node.is_float != 0
            && node.tok.token_type != TokenType::Float
            && node.tok.token_type != TokenType::ToFloat
        {
            print!(".");
        }
        printtoken(&node.tok);
        if node.tok.token_type == TokenType::Var {
            if node.history_index < 0 {
                print!("{{{}}}", node.history_index);
            }
            if node.vector_index > -1 {
                print!("[{}]", node.vector_index);
            }
        }
        cur = node.next.as_deref();
        if cur.is_some() {
            print!(" ");
        }
    }
}

#[allow(dead_code)]
fn printexpr(s: &str, expr: &MapperExpr) {
    printexprnode(s, &expr.node);
}

fn printstack(stack: &[stack_obj_t]) {
    print!("Stack: ");
    for item in stack {
        match item {
            stack_obj_t::Node(node) => {
                print!("[");
                printexprnode("", node);
                print!("] ");
            }
            stack_obj_t::State(state) => {
                print!("{state:?} ");
            }
        }
    }
    println!();
}

fn contains_var(node: &ExprNode) -> bool {
    let mut cur = Some(node);
    while let Some(n) = cur {
        if n.tok.token_type == TokenType::Var {
            return true;
        }
        cur = n.next.as_deref();
    }
    false
}

fn last_node(node: &ExprNode) -> &ExprNode {
    let mut cur = node;
    while let Some(ref next) = cur.next {
        cur = next;
    }
    cur
}

fn append_tail(head: &mut ExprNode, tail: ExprNode) {
    let mut cur = head;
    while let Some(ref mut next) = cur.next {
        cur = Arc::make_mut(next);
    }
    cur.next = Some(Arc::new(tail));
}

fn take_last_node(head: &mut ExprNode) -> Option<ExprNode> {
    head.next.as_ref()?;
    let mut cur = head;
    while cur
        .next
        .as_ref()
        .is_some_and(|next| next.next.is_some())
    {
        cur = Arc::make_mut(cur.next.as_mut().unwrap());
    }
    let last_arc = cur.next.take()?;
    Some(Arc::try_unwrap(last_arc).unwrap_or_else(|a| (*a).clone()))
}

fn collapse_expr_to_left(
    plhs: &mut ExprNode,
    mut rhs: ExprNode,
    constant_folding: i32,
) -> Result<(), &'static str> {
    let refvar = contains_var(plhs) || contains_var(&rhs);
    let lhs_is_float = last_node(plhs).is_float != 0;
    let rhs_is_float = last_node(&rhs).is_float != 0;
    let is_float = lhs_is_float || rhs_is_float;

    if lhs_is_float && !rhs_is_float {
        append_tail(&mut rhs, ExprNode::with_token(Token::simple(TokenType::ToFloat), 1));
        if let Some(last) = take_last_node(plhs) {
            append_tail(&mut rhs, last);
            append_tail(plhs, rhs);
        } else {
            replace_single(plhs, rhs);
        }
    } else if !lhs_is_float && rhs_is_float {
        if let Some(mut last) = take_last_node(plhs) {
            last.is_float = 1;
            append_tail(&mut rhs, last);
            let mut coerce = ExprNode::with_token(Token::simple(TokenType::ToFloat), 1);
            coerce.next = Some(Arc::new(rhs));
            append_tail(plhs, coerce);
        } else {
            let mut last = std::mem::replace(
                plhs,
                ExprNode::with_token(Token::simple(TokenType::ToFloat), 1),
            );
            last.is_float = 1;
            append_tail(&mut rhs, last);
            plhs.next = Some(Arc::new(rhs));
        }
    } else if let Some(last) = take_last_node(plhs) {
        append_tail(&mut rhs, last);
        append_tail(plhs, rhs);
    } else {
        replace_single(plhs, rhs);
    }

    if constant_folding != 0 && !refvar {
        let v = evaluate_node_list(plhs, None)?;
        plhs.next = None;
        plhs.is_float = i32::from(is_float);
        if is_float {
            plhs.tok = Token::float(v.coerce_f32());
        } else {
            plhs.tok = Token::int(v.coerce_i32());
        }
    }
    Ok(())
}

fn replace_single(plhs: &mut ExprNode, rhs: ExprNode) {
    let last = std::mem::replace(plhs, rhs);
    append_tail(plhs, last);
}

fn parse_expr(
    s: &str,
    input_is_float: i32,
    output_is_float: i32,
    vector_size: i32,
) -> Result<MapperExpr, &'static str> {
    let tokens = expr_lex(s)?;
    let mut tok_idx = 0;
    let mut stack: Vec<stack_obj_t> = Vec::with_capacity(STACK_SIZE);
    let mut next_token = true;
    let mut var_allowed = true;
    let mut oldest_samps: f32 = 0.0;
    let mut tok = tokens[0];

    stack.push(stack_obj_t::State(state_t::EXPR));
    stack.push(stack_obj_t::State(state_t::YEQUAL_EQ));
    stack.push(stack_obj_t::State(state_t::YEQUAL_Y));

    let mut result: Option<ExprNode> = None;

    while !stack.is_empty() {
        if stack.len() > STACK_SIZE {
            return Err("Parser stack overflow.");
        }
        if next_token {
            tok = tokens[tok_idx];
            if tok_idx + 1 < tokens.len() {
                tok_idx += 1;
            }
        }
        next_token = false;

        if matches!(stack.last(), Some(stack_obj_t::Node(_))) {
            let len = stack.len();
            if len == 1 {
                if let Some(stack_obj_t::Node(node)) = stack.pop() {
                    result = Some(node);
                    break;
                }
            }
            if len >= 2 && matches!(stack[len - 2], stack_obj_t::State(_)) {
                if len >= 3 && matches!(stack[len - 3], stack_obj_t::Node(_)) {
                    match &stack[len - 2] {
                        stack_obj_t::State(state_t::EXPR_RIGHT)
                        | stack_obj_t::State(state_t::TERM_RIGHT)
                        | stack_obj_t::State(state_t::CLOSE_PAREN) => {
                            let Some(stack_obj_t::Node(rhs)) = stack.pop() else {
                                return Err("Expected node on stack.");
                            };
                            let new_len = stack.len();
                            if let stack_obj_t::Node(ref mut lhs) = stack[new_len - 2] {
                                collapse_expr_to_left(lhs, rhs, 1)?;
                            }
                        }
                        stack_obj_t::State(state_t::CLOSE_HISTINDEX) => {
                            let Some(stack_obj_t::Node(idx_node)) = stack.pop() else {
                                return Err("Expected node on stack.");
                            };
                            die_unless!(
                                idx_node.next.is_none()
                                    && matches!(
                                        idx_node.tok.token_type,
                                        TokenType::Int | TokenType::Float
                                    ),
                                "expected lonely INT or FLOAT expression on the stack."
                            );
                            let hist_idx = match idx_node.tok.token_type {
                                TokenType::Float => idx_node.tok.value.unwrap_or(0.0) as i32,
                                TokenType::Int => idx_node.tok.int_value.unwrap_or(0),
                                _ => return Err("Expected INT or FLOAT history index."),
                            };
                            let new_len = stack.len();
                            if let stack_obj_t::Node(ref mut var_node) = stack[new_len - 2] {
                                die_unless!(
                                    var_node.tok.token_type == TokenType::Var,
                                    "expected VAR two-down on the stack."
                                );
                                var_node.history_index = hist_idx;
                                if oldest_samps > hist_idx as f32 {
                                    oldest_samps = hist_idx as f32;
                                }
                            }
                        }
                        stack_obj_t::State(state_t::CLOSE_VECTINDEX) => {
                            let Some(stack_obj_t::Node(idx_node)) = stack.pop() else {
                                return Err("Expected node on stack.");
                            };
                            die_unless!(
                                idx_node.next.is_none()
                                    && matches!(
                                        idx_node.tok.token_type,
                                        TokenType::Int | TokenType::Float
                                    ),
                                "expected lonely INT or FLOAT expression on the stack."
                            );
                            let vect_idx = match idx_node.tok.token_type {
                                TokenType::Float => idx_node.tok.value.unwrap_or(0.0) as i32,
                                TokenType::Int => idx_node.tok.int_value.unwrap_or(0),
                                _ => return Err("Expected INT or FLOAT vector index."),
                            };
                            if vect_idx > 0 {
                                return Err("Vector indexing not yet implemented.");
                            }
                            if vect_idx < 0 || vect_idx >= vector_size {
                                return Err("Vector index outside input size.");
                            }
                            let new_len = stack.len();
                            if let stack_obj_t::Node(ref mut var_node) = stack[new_len - 2] {
                                die_unless!(
                                    var_node.tok.token_type == TokenType::Var,
                                    "expected VAR two-down on the stack."
                                );
                                var_node.vector_index = vect_idx;
                            }
                        }
                        _ => return Err("Unexpected parser state below node."),
                    }
                } else {
                    stack.swap(len - 2, len - 1);
                }
            }
            if TRACING {
                printstack(&stack);
            }
            continue;
        }

        let state = match stack.last() {
            Some(stack_obj_t::State(st)) => *st,
            _ => return Err("Expected state on parser stack."),
        };

        match state {
            state_t::YEQUAL_Y => {
                if tok.token_type == TokenType::Var && tok.var == Some('y') {
                    stack.pop();
                    next_token = true;
                } else {
                    return Err("Error in y= prefix.");
                }
            }
            state_t::YEQUAL_EQ => {
                if tok.token_type == TokenType::Op && tok.op == Some('=') {
                    stack.pop();
                    next_token = true;
                } else {
                    return Err("Error in y= prefix.");
                }
            }
            state_t::EXPR => {
                stack.pop();
                stack.push(stack_obj_t::State(state_t::EXPR_RIGHT));
                stack.push(stack_obj_t::State(state_t::TERM));
            }
            state_t::EXPR_RIGHT => {
                stack.pop();
                if tok.token_type == TokenType::Op && matches!(tok.op, Some('+') | Some('-')) {
                    if let Some(stack_obj_t::Node(node)) = stack.last_mut() {
                        let is_f = last_node(node).is_float;
                        append_tail(node, ExprNode::with_token(tok, is_f));
                    }
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                }
            }
            state_t::TERM => {
                stack.pop();
                stack.push(stack_obj_t::State(state_t::TERM_RIGHT));
                stack.push(stack_obj_t::State(state_t::VALUE));
            }
            state_t::TERM_RIGHT => {
                stack.pop();
                if tok.token_type == TokenType::Op && matches!(tok.op, Some('*') | Some('/')) {
                    if let Some(stack_obj_t::Node(node)) = stack.last_mut() {
                        let is_f = last_node(node).is_float;
                        append_tail(node, ExprNode::with_token(tok, is_f));
                    }
                    stack.push(stack_obj_t::State(state_t::TERM));
                    next_token = true;
                }
            }
            state_t::VALUE => match tok.token_type {
                TokenType::Int => {
                    stack.pop();
                    stack.push(stack_obj_t::Node(ExprNode::with_token(tok, 0)));
                    next_token = true;
                }
                TokenType::Float => {
                    stack.pop();
                    stack.push(stack_obj_t::Node(ExprNode::with_token(tok, 1)));
                    next_token = true;
                }
                TokenType::Var => {
                    if var_allowed {
                        stack.pop();
                        stack.push(stack_obj_t::Node(ExprNode::with_token(tok, input_is_float)));
                        stack.push(stack_obj_t::State(state_t::VAR_RIGHT));
                        next_token = true;
                    } else {
                        return Err("Unexpected variable reference.");
                    }
                }
                TokenType::OpenParen => {
                    stack.pop();
                    stack.push(stack_obj_t::State(state_t::CLOSE_PAREN));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                }
                TokenType::Func => {
                    stack.pop();
                    let entry = tok.func.ok_or("Unknown function.")?;
                    stack.push(stack_obj_t::Node(ExprNode::with_token(tok, 1)));
                    if entry.arity > 0 {
                        stack.push(stack_obj_t::State(state_t::CLOSE_PAREN));
                        stack.push(stack_obj_t::State(state_t::EXPR));
                        for _ in 1..entry.arity {
                            stack.push(stack_obj_t::State(state_t::COMMA));
                            stack.push(stack_obj_t::State(state_t::EXPR));
                        }
                        stack.push(stack_obj_t::State(state_t::OPEN_PAREN));
                    }
                    next_token = true;
                }
                TokenType::Op if tok.op == Some('-') => {
                    stack.pop();
                    stack.push(stack_obj_t::State(state_t::NEGATE));
                    stack.push(stack_obj_t::State(state_t::VALUE));
                    next_token = true;
                }
                _ => return Err("Expected value."),
            },
            state_t::NEGATE => {
                stack.pop();
                if let Some(stack_obj_t::Node(rhs)) = stack.pop() {
                    let mut e = ExprNode::with_token(Token::int(0), 0);
                    e.next = Some(Arc::new(ExprNode::with_token(Token::op('-'), 0)));
                    collapse_expr_to_left(&mut e, rhs, 1)?;
                    stack.push(stack_obj_t::Node(e));
                } else {
                    return Err("Expected to negate an expression.");
                }
            }
            state_t::VAR_RIGHT => {
                stack.pop();
                if tok.token_type == TokenType::OpenSquare {
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                } else if tok.token_type == TokenType::OpenCurly {
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                }
            }
            state_t::VAR_VECTINDEX => {
                stack.pop();
                if tok.token_type == TokenType::OpenSquare {
                    var_allowed = false;
                    stack.push(stack_obj_t::State(state_t::CLOSE_VECTINDEX));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                }
            }
            state_t::VAR_HISTINDEX => {
                stack.pop();
                if tok.token_type == TokenType::OpenCurly {
                    var_allowed = false;
                    stack.push(stack_obj_t::State(state_t::CLOSE_HISTINDEX));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                }
            }
            state_t::CLOSE_VECTINDEX => {
                if tok.token_type == TokenType::CloseSquare {
                    var_allowed = true;
                    stack.pop();
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                    next_token = true;
                } else {
                    return Err("Expected ']'.");
                }
            }
            state_t::CLOSE_HISTINDEX => {
                if tok.token_type == TokenType::CloseCurly {
                    var_allowed = true;
                    stack.pop();
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                    next_token = true;
                } else {
                    return Err("Expected '}'.");
                }
            }
            state_t::CLOSE_PAREN => {
                if tok.token_type == TokenType::CloseParen {
                    stack.pop();
                    next_token = true;
                } else {
                    return Err("Expected ')'.");
                }
            }
            state_t::COMMA => {
                if tok.token_type == TokenType::Comma {
                    stack.pop();
                    let prev_idx = stack[..stack.len().saturating_sub(1)]
                        .iter()
                        .rposition(|x| matches!(x, stack_obj_t::Node(_)));
                    if let Some(i) = prev_idx {
                        let Some(stack_obj_t::Node(rhs)) = stack.pop() else {
                            return Err("Expected node before comma.");
                        };
                        if let stack_obj_t::Node(ref mut lhs) = stack[i] {
                            collapse_expr_to_left(lhs, rhs, 0)?;
                        }
                    }
                    next_token = true;
                } else {
                    return Err("Expected ','.");
                }
            }
            state_t::OPEN_PAREN => {
                if tok.token_type == TokenType::OpenParen {
                    stack.pop();
                    next_token = true;
                } else {
                    return Err("Expected '('.");
                }
            }
            state_t::END => {
                if tok.token_type == TokenType::End {
                    stack.pop();
                } else {
                    return Err("Expected END.");
                }
            }
        }

        if TRACING {
            printstack(&stack);
        }
    }

    let mut expr_node = result.ok_or("Failed to parse expression.")?;

    if oldest_samps < -100.0 {
        trace!("Expression contains history reference of {}", oldest_samps);
        return Err("History reference out of bounds.");
    }

    let final_is_float = last_node(&expr_node).is_float != 0;
    if final_is_float && output_is_float == 0 {
        append_tail(
            &mut expr_node,
            ExprNode::with_token(Token::simple(TokenType::ToInt32), 0),
        );
    } else if !final_is_float && output_is_float != 0 {
        append_tail(
            &mut expr_node,
            ExprNode::with_token(Token::simple(TokenType::ToFloat), 1),
        );
    }

    if vector_size > 1 {
        let mut cur = Some(&expr_node);
        while let Some(n) = cur {
            if n.tok.token_type == TokenType::Var && n.vector_index > 0 {
                trace!("vector indexing not yet implemented");
                return Err("Vector indexing not yet implemented.");
            }
            cur = n.next.as_deref();
        }
    }

    let history_size = ((-oldest_samps).ceil() as i32) + 1;
    let zero_in = if input_is_float != 0 {
        MapperSignalValue::F(0.0)
    } else {
        MapperSignalValue::I32(0)
    };
    let zero_out = if output_is_float != 0 {
        MapperSignalValue::F(0.0)
    } else {
        MapperSignalValue::I32(0)
    };

    Ok(MapperExpr {
        node: expr_node,
        vector_size,
        history_size,
        history_pos: -1,
        input_history: vec![zero_in; (vector_size * history_size) as usize],
        output_history: vec![zero_out; history_size as usize],
    })
}

pub fn mapper_expr_new_from_string(
    s: &str,
    input_is_float: i32,
    output_is_float: i32,
    vector_size: i32,
) -> MapperExpr {
    match parse_expr(s, input_is_float, output_is_float, vector_size) {
        Ok(expr) => expr,
        Err(msg) => {
            println!("{msg}");
            panic!("{msg}");
        }
    }
}

fn evaluate_node_list(
    start_node: &ExprNode,
    mapper: Option<&MapperExpr>,
) -> Result<MapperSignalValue, &'static str> {
    let mut stack: Vec<MapperSignalValue> = Vec::with_capacity(STACK_SIZE);
    let mut cur = Some(start_node);

    while let Some(node) = cur {
        match node.tok.token_type {
            TokenType::Int => {
                stack.push(MapperSignalValue::I32(node.tok.int_value.unwrap_or(0)));
            }
            TokenType::Float => {
                stack.push(MapperSignalValue::F(node.tok.value.unwrap_or(0.0)));
            }
            TokenType::Var => {
                let m = mapper.ok_or("Input required but not provided for expression evaluation.")?;
                let idx = (node.history_index + m.history_pos + m.history_size)
                    .rem_euclid(m.history_size);
                match node.tok.var {
                    Some('x') => {
                        let v_idx = (idx * m.vector_size + node.vector_index) as usize;
                        stack.push(m.input_history[v_idx]);
                    }
                    Some('y') => {
                        stack.push(m.output_history[idx as usize]);
                    }
                    _ => return Err("Unknown variable in expression."),
                }
            }
            TokenType::ToFloat => {
                let top = stack.last_mut().ok_or("Stack underflow on ToFloat.")?;
                *top = MapperSignalValue::F(top.coerce_f32());
            }
            TokenType::ToInt32 => {
                let top = stack.last_mut().ok_or("Stack underflow on ToInt32.")?;
                *top = MapperSignalValue::I32(top.coerce_i32());
            }
            TokenType::Op => {
                let right = stack.pop().ok_or("Stack underflow on Op.")?;
                let left = stack.pop().ok_or("Stack underflow on Op.")?;
                let op = node.tok.op.ok_or("Missing operator.")?;
                if node.is_float != 0 {
                    let l = left.coerce_f32();
                    let r = right.coerce_f32();
                    let res = match op {
                        '+' => l + r,
                        '-' => l - r,
                        '*' => l * r,
                        '/' => l / r,
                        _ => return Err("Unknown operator."),
                    };
                    trace!("{} {} {} = {}", l, op, r, res);
                    stack.push(MapperSignalValue::F(res));
                } else {
                    let l = left.coerce_i32();
                    let r = right.coerce_i32();
                    let res = match op {
                        '+' => l.wrapping_add(r),
                        '-' => l.wrapping_sub(r),
                        '*' => l.wrapping_mul(r),
                        '/' => l.wrapping_div(r),
                        _ => return Err("Unknown operator."),
                    };
                    trace!("{} {} {} = {}", l, op, r, res);
                    stack.push(MapperSignalValue::I32(res));
                }
            }
            TokenType::Func => {
                let entry = node.tok.func.ok_or("Unknown function.")?;
                match entry.arity {
                    0 => {
                        let res = (entry.func)(0.0, 0.0);
                        trace!("{} = {}", entry.name, res);
                        stack.push(MapperSignalValue::F(res));
                    }
                    1 => {
                        let right = stack.pop().ok_or("Stack underflow on Func1.")?.coerce_f32();
                        let res = (entry.func)(right, 0.0);
                        trace!("{}({}) = {}", entry.name, right, res);
                        stack.push(MapperSignalValue::F(res));
                    }
                    2 => {
                        let right = stack.pop().ok_or("Stack underflow on Func2.")?.coerce_f32();
                        let left = stack.pop().ok_or("Stack underflow on Func2.")?.coerce_f32();
                        let res = (entry.func)(left, right);
                        trace!("{}({},{}) = {}", entry.name, left, right, res);
                        stack.push(MapperSignalValue::F(res));
                    }
                    _ => return Err("Unsupported function arity."),
                }
            }
            _ => return Err("Unexpected token in expression."),
        }
        cur = node.next.as_deref();
    }

    stack.first().copied().ok_or("Empty evaluation stack.")
}

pub fn mapper_expr_evaluate<'a>(
    mapper: &mut MapperExpr,
    input: &'a MapperSignalValue,
) -> MapperSignalValue {
    mapper.history_pos = (mapper.history_pos + 1) % mapper.history_size;
    let base = (mapper.history_pos * mapper.vector_size) as usize;
    mapper.input_history[base] = *input;

    match evaluate_node_list(&mapper.node, Some(mapper)) {
        Ok(val) => {
            mapper.output_history[mapper.history_pos as usize] = val;
            val
        }
        Err(msg) => {
            trace!("{}", msg);
            MapperSignalValue::I32(0)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn c_test2_integer_mode() {
        let mut e = mapper_expr_new_from_string("y=26*2/2+x*30/(20*1)", 0, 0, 1);
        for x in [3, 321] {
            let expected = 26 * 2 / 2 + x * 30 / 20;
            let out = mapper_expr_evaluate(&mut e, &MapperSignalValue::I32(x));
            assert_eq!(out.as_i32(), Some(expected));
            assert_eq!(out.as_f32(), None);
        }
        e.node.expr_free();
    }

    #[test]
    fn history_input_and_output() {
        let mut e = mapper_expr_new_from_string("y=x+x{-1}+y{-1}", 1, 1, 1);
        let y0 = mapper_expr_evaluate(&mut e, &MapperSignalValue::F(1.0));
        assert_eq!(y0.as_f32(), Some(1.0));
        let y1 = mapper_expr_evaluate(&mut e, &MapperSignalValue::F(2.0));
        assert_eq!(y1.as_f32(), Some(4.0));
        let y2 = mapper_expr_evaluate(&mut e, &MapperSignalValue::F(3.0));
        assert_eq!(y2.as_f32(), Some(9.0));
    }

    #[test]
    fn functions_and_coercion() {
        let mut e = mapper_expr_new_from_string("y=min(x, max(2, logb(8))) + atan2(1, 1)", 0, 1, 1);
        let out = mapper_expr_evaluate(&mut e, &MapperSignalValue::I32(5));
        let expected = 3.0_f32 + std::f32::consts::FRAC_PI_4;
        assert!((out.as_f32().unwrap() - expected).abs() < 1e-6);

        let mut e_int = mapper_expr_new_from_string("y=-x[0]+sin(pi/2)", 0, 0, 1);
        let out_int = mapper_expr_evaluate(&mut e_int, &MapperSignalValue::I32(10));
        assert_eq!(out_int.as_i32(), Some(-9));

        let n = ExprNode::new();
        n.expr_free();
    }
}

```

### c/mapper_expr.c
```c
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mapper_expr.h"

typedef union _mapper_signal_value_t
{
    float f;
    int i32;
} mapper_signal_value_t;

#define STACK_SIZE 256
#ifdef DEBUG
#define TRACING 0 /* Set non-zero to see trace during parse & eval. */
#else
#define TRACING 0
#endif

/**** Debug macros ****/

/*! Debug tracer */
#ifdef DEBUG
#ifdef __GNUC__
#include <stdio.h>
#include <assert.h>
#define trace(...) { printf("-- " __VA_ARGS__); }
#define die_unless(a, ...) { if (!(a)) { printf("-- " __VA_ARGS__); assert(a); } }
#else
static void trace(...)
{
};
static void die_unless(...) {};
#endif
#else
#ifdef __GNUC__
#define trace(...) {}
#define die_unless(...) {}
#else
static void trace(...)
{
};
static void die_unless(...) {};
#endif
#endif

static float minf(float x, float y)
{
    if (y < x) return y;
    else return x;
}

static float maxf(float x, float y)
{
    if (y > x) return y;
    else return x;
}

static float pif()
{
    return M_PI;
}

typedef enum {
    FUNC_UNKNOWN=-1,
    FUNC_POW=0,
    FUNC_SIN,
    FUNC_COS,
    FUNC_TAN,
    FUNC_ABS,
    FUNC_SQRT,
    FUNC_LOG,
    FUNC_LOG10,
    FUNC_EXP,
    FUNC_FLOOR,
    FUNC_ROUND,
    FUNC_CEIL,
    FUNC_ASIN,
    FUNC_ACOS,
    FUNC_ATAN,
    FUNC_ATAN2,
    FUNC_SINH,
    FUNC_COSH,
    FUNC_TANH,
    FUNC_LOGB,
    FUNC_EXP2,
    FUNC_LOG2,
    FUNC_HYPOT,
    FUNC_CBRT,
    FUNC_TRUNC,
    FUNC_MIN,
    FUNC_MAX,
    FUNC_PI,
    N_FUNCS
} expr_func_t;

static struct {
    const char *name;
    unsigned int arity;
    void *func;
} function_table[] = {
    { "pow", 2, powf },
    { "sin", 1, sinf },
    { "cos", 1, cosf },
    { "tan", 1, tanf },
    { "abs", 1, fabsf },
    { "sqrt", 1, sqrtf },
    { "log", 1, logf },
    { "log10", 1, log10f },
    { "exp", 1, expf },
    { "floor", 1, floorf },
    { "round", 1, roundf },
    { "ceil", 1, ceilf },
    { "asin", 1, asinf },
    { "acos", 1, acosf },
    { "atan", 1, atanf },
    { "atan2", 2, atan2f },
    { "sinh", 1, sinhf },
    { "cosh", 1, coshf },
    { "tanh", 1, tanhf },
    { "logb", 1, logbf },
    { "exp2", 1, exp2f },
    { "log2", 1, log2f },
    { "hypot", 2, hypotf },
    { "cbrt", 1, cbrtf },
    { "trunc", 1, truncf },
    { "min", 2, minf },
    { "max", 2, maxf },
    { "pi", 0, pif },
};

typedef float func_float_arity0();
typedef float func_float_arity1(float);
typedef float func_float_arity2(float,float);

typedef struct _token {
    enum {
        TOK_FLOAT,
        TOK_INT,
        TOK_OP,
        TOK_OPEN_PAREN,
        TOK_CLOSE_PAREN,
        TOK_VAR,
        TOK_OPEN_SQUARE,
        TOK_CLOSE_SQUARE,
        TOK_OPEN_CURLY,
        TOK_CLOSE_CURLY,
        TOK_FUNC,
        TOK_COMMA,
        TOK_END,
        TOK_TOFLOAT,
        TOK_TOINT32,
    } type;
    union {
        float f;
        int i;
        char var;
        char op;
        expr_func_t func;
    };
} token_t;

static expr_func_t function_lookup(const char *s, int len)
{
    int i;
    for (i=0; i<N_FUNCS; i++) {
        if (strncmp(s, function_table[i].name, len)==0)
            return i;
    }
    return FUNC_UNKNOWN;
}

static int expr_lex(const char **str, token_t *tok)
{
    int n=0;
    char c = **str;
    const char *s;
    int integer_found = 0;

    if (c==0) {
        tok->type = TOK_END;
        return 0;
    }

  again:

    if (isdigit(c)) {
        s = *str;
        do {
            c = (*(++*str));
        } while (c && isdigit(c));
        n = atoi(s);
        integer_found = 1;
        if (c!='.') {
            tok->i = n;
            tok->type = TOK_INT;
            return 0;
        }
    }

    switch (c) {
    case '.':
        s = *str;
        c = (*(++*str));
        if (!isdigit(c) && integer_found) {
            tok->type = TOK_FLOAT;
            tok->f = (float)n;
            return 0;
        }
        if (!isdigit(c))
            break;
        do {
            c = (*(++*str));
        } while (c && isdigit(c));
        tok->f = (float)n + atof(s);
        tok->type = TOK_FLOAT;
        return 0;
    case '+':
    case '-':
    case '/':
    case '*':
    case '=':
        tok->type = TOK_OP;
        tok->op = c;
        ++*str;
        return 0;
    case '(':
        tok->type = TOK_OPEN_PAREN;
        ++*str;
        return 0;
    case ')':
        tok->type = TOK_CLOSE_PAREN;
        ++*str;
        return 0;
    case 'x':
    case 'y':
        tok->type = TOK_VAR;
        tok->var = c;
        ++*str;
        return 0;
    case '[':
        tok->type = TOK_OPEN_SQUARE;
        ++*str;
        return 0;
    case ']':
        tok->type = TOK_CLOSE_SQUARE;
        ++*str;
        return 0;
    case '{':
        tok->type = TOK_OPEN_CURLY;
        ++*str;
        return 0;
    case '}':
        tok->type = TOK_CLOSE_CURLY;
        ++*str;
        return 0;
    case ' ':
    case '\t':
    case '\r':
    case '\n':
        c = (*(++*str));
        goto again;
    case ',':
        tok->type = TOK_COMMA;
        ++*str;
        return 0;
    default:
        if (!isalpha(c)) {
            printf("unknown character '%c' in lexer\n", c);
            break;
        }
        s = *str;
        while (c && (isalpha(c) || isdigit(c)))
            c = (*(++*str));
        tok->type = TOK_FUNC;
        tok->func = function_lookup(s, *str-s);
        return 0;
    }

    return 1;
}

typedef struct _exprnode
{
    token_t tok;
    int is_float;
    int history_index;  // when tok.type==TOK_VAR
    int vector_index;   // when tok.type==TOK_VAR
    struct _exprnode *next;
} *exprnode;

struct _mapper_expr
{
    exprnode node;
    int vector_size;
    int history_size;
    int history_pos;
    mapper_signal_value_t *input_history;
    mapper_signal_value_t *output_history;
};

typedef enum {
    YEQUAL_Y,
    YEQUAL_EQ,
    EXPR,
    EXPR_RIGHT,
    TERM,
    TERM_RIGHT,
    VALUE,
    NEGATE,
    VAR_RIGHT,
    VAR_VECTINDEX,
    VAR_HISTINDEX,
    CLOSE_VECTINDEX,
    CLOSE_HISTINDEX,
    OPEN_PAREN,
    CLOSE_PAREN,
    COMMA,
    END,
} state_t;

typedef struct _stack_obj
{
    union {
        state_t state;
        exprnode node;
    };
    enum {
        ST_STATE,
        ST_NODE,
    } type;
} stack_obj_t;

static exprnode exprnode_new(token_t *tok, int is_float)
{
    exprnode t = (exprnode)
        malloc(sizeof(struct _exprnode));
    t->tok = *tok;
    t->is_float = is_float;
    t->history_index = 0;
    t->vector_index = 0;
    t->next = 0;
    return t;
}

static void exprnode_free(exprnode e)
{
    while (e) {
        exprnode tmp = e;
        e = e->next;
        free(tmp);
    }
}

void mapper_expr_free(mapper_expr expr)
{
    exprnode_free(expr->node);
    free(expr->input_history);
    free(expr->output_history);
    free(expr);
}

#ifdef DEBUG
void printtoken(token_t *tok)
{
    switch (tok->type) {
    case TOK_FLOAT:        printf("%f", tok->f);          break;
    case TOK_INT:          printf("%d", tok->i);          break;
    case TOK_OP:           printf("%c", tok->op);         break;
    case TOK_OPEN_PAREN:   printf("(");                   break;
    case TOK_CLOSE_PAREN:  printf(")");                   break;
    case TOK_VAR:          printf("VAR(%c)", tok->var);   break;
    case TOK_OPEN_SQUARE:  printf("[");                   break;
    case TOK_CLOSE_SQUARE: printf("]");                   break;
    case TOK_OPEN_CURLY:   printf("{");                   break;
    case TOK_CLOSE_CURLY:  printf("}");                   break;
    case TOK_FUNC:         printf("FUNC(%s)",
                                  function_table[tok->func].name);
        break;
    case TOK_COMMA:        printf(",");                   break;
    case TOK_END:          printf("END");                 break;
    case TOK_TOFLOAT:      printf("(float)");             break;
    case TOK_TOINT32:      printf("(int32)");             break;
    default:               printf("(unknown token)");     break;
    }
}

void printexprnode(const char *s, exprnode list)
{
    printf("%s", s);
    while (list) {
        if (list->is_float
            && list->tok.type != TOK_FLOAT
            && list->tok.type != TOK_TOFLOAT)
            printf(".");
        printtoken(&list->tok);
        if (list->tok.type == TOK_VAR) {
            if (list->history_index < 0)
                printf("{%d}", list->history_index);
            if (list->vector_index > -1)
                printf("[%d]", list->vector_index);
        }
        list = list->next;
        if (list) printf(" ");
    }
}

void printexpr(const char*s, mapper_expr e)
{
    printexprnode(s, e->node);
}

void printstack(stack_obj_t *stack, int top)
{
    const char *state_name[] = {
        "YEQUAL_Y", "YEQUAL_EQ", "EXPR", "EXPR_RIGHT", "TERM",
        "TERM_RIGHT", "VALUE", "NEGATE", "VAR_RIGHT",
        "VAR_VECTINDEX", "VAR_HISTINDEX", "CLOSE_VECTINDEX",
        "CLOSE_HISTINDEX", "OPEN_PAREN", "CLOSE_PAREN",
        "COMMA", "END" };

    int i;
    printf("Stack: ");
    for (i=0; i<=top; i++) {
        if (stack[i].type == ST_NODE) {
            printf("[");
            printexprnode("", stack[i].node);
            printf("] ");
            continue;
        }
        printf("%s ", state_name[stack[i].state]);
    }
    printf("\n");
}
#endif

static void collapse_expr_to_left(exprnode* plhs, exprnode rhs,
                                  int constant_folding)
{
    // track whether any variable references
    int refvar = 0;
    int is_float = 0;

    // find trailing operator on right hand side
    exprnode rhs_last = rhs;
    if (rhs->tok.type == TOK_VAR)
        refvar = 1;
    while (rhs_last->next) {
        if (rhs_last->tok.type == TOK_VAR)
            refvar = 1;
        rhs_last = rhs_last->next;
    }

    // find pointer to insertion place:
    // - could be a function that needs args,
    // - otherwise assume it's before the trailing operator
    exprnode *plhs_last = plhs;
    if ((*plhs_last)->tok.type == TOK_VAR)
        refvar = 1;
    while ((*plhs_last)->next) {
        if ((*plhs_last)->tok.type == TOK_VAR)
            refvar = 1;
        plhs_last = &(*plhs_last)->next;
    }

    // insert float coersion if sides disagree on type
    token_t coerce;
    coerce.type = TOK_TOFLOAT;
    is_float = (*plhs_last)->is_float || rhs_last->is_float;
    if ((*plhs_last)->is_float && !rhs_last->is_float) {
        rhs_last = rhs_last->next = exprnode_new(&coerce, 1);
    } else if (!(*plhs_last)->is_float && rhs_last->is_float) {
        exprnode e = exprnode_new(&coerce, 1);
        e->next = (*plhs_last);
        (*plhs_last) = e;
        plhs_last = &e->next;
        e->next->is_float = 1;
    }

    // insert the list before the trailing op of left hand side
    rhs_last->next = (*plhs_last);
    (*plhs_last) = rhs;

    // if there were no variable references, then expression is
    // constant, so evaluate it immediately
    if (constant_folding && !refvar) {
        struct _mapper_expr e;
        e.node = *plhs;
        mapper_signal_value_t v;
        mapper_expr_evaluate(&e, 0, &v);

        exprnode_free((*plhs)->next);
        (*plhs)->next = 0;
        (*plhs)->is_float = is_float;

        if (is_float) {
            (*plhs)->tok.type = TOK_FLOAT;
            (*plhs)->tok.f = v.f;
        }
        else {
            (*plhs)->tok.type = TOK_INT;
            (*plhs)->tok.i = v.i32;
        }
    }
}

/* Macros to help express stack operations in parser. */
#define PUSHSTATE(x) { top++; stack[top].state = x; stack[top].type = ST_STATE; }
#define PUSHEXPR(x, f) { top++; stack[top].node = exprnode_new(&x, f); stack[top].type = ST_NODE; }
#define POP() (top--)
#define TOPSTATE_IS(x) (stack[top].type == ST_STATE && stack[top].state == x)
#define APPEND_OP(x)                                                    \
    if (stack[top].type == ST_NODE) {                                   \
        exprnode e = stack[top].node;                                   \
        while (e->next) e = e->next;                                    \
        e->next = exprnode_new(&tok, 0);                                \
        e->next->is_float = e->is_float;                                \
    }
#define SUCCESS(x) { result = x; goto done; }
#define FAIL(msg) { error_message = msg; result = 0; goto done; }

/*! Create a new expression by parsing the given string. */
mapper_expr mapper_expr_new_from_string(const char *str,
                                        int input_is_float,
                                        int output_is_float,
                                        int vector_size)
{
    const char *s = str;
    if (!str) return 0;
    stack_obj_t stack[STACK_SIZE];
    int top = -1;
    exprnode result = 0;
    const char *error_message = 0;

    token_t tok;
    int i, next_token = 1;

    int var_allowed = 1;
    float oldest_samps = 0;

    PUSHSTATE(EXPR);
    PUSHSTATE(YEQUAL_EQ);
    PUSHSTATE(YEQUAL_Y);

    while (top >= 0) {
        if (next_token && expr_lex(&s, &tok))
            {FAIL("Error in lexical analysis.");}
        next_token = 0;

        if (stack[top].type == ST_NODE) {
            if (top==0)
                SUCCESS(stack[top].node);
            if (stack[top-1].type == ST_STATE) {
                if (top >= 2 && stack[top-2].type == ST_NODE) {
                    if (stack[top-1].type == ST_STATE
                        && (stack[top-1].state == EXPR_RIGHT
                            || stack[top-1].state == TERM_RIGHT
                            || stack[top-1].state == CLOSE_PAREN))
                    {
                        collapse_expr_to_left(&stack[top-2].node,
                                              stack[top].node, 1);
                        POP();
                    }
                    else if (stack[top-1].type == ST_STATE
                             && stack[top-1].state == CLOSE_HISTINDEX)
                    {
                        die_unless(stack[top-2].node->tok.type == TOK_VAR,
                                   "expected VAR two-down on the stack.\n");
                        die_unless(!stack[top].node->next && (stack[top].node->tok.type == TOK_INT
                                                              || stack[top].node->tok.type == TOK_FLOAT),
                                   "expected lonely INT or FLOAT expression on the stack.\n");
                        if (stack[top].node->tok.type == TOK_FLOAT)
                            stack[top-2].node->history_index = (int)stack[top].node->tok.f;
                        else
                            stack[top-2].node->history_index = stack[top].node->tok.i;

                        /* Track the oldest history reference in order
                         * to know how much buffer needs to be
                         * allocated for this expression. */
                        if (oldest_samps > stack[top-2].node->history_index)
                            oldest_samps = stack[top-2].node->history_index;

                        exprnode_free(stack[top].node);
                        POP();
                    }
                    else if (stack[top-1].type == ST_STATE
                             && stack[top-1].state == CLOSE_VECTINDEX)
                    {
                        die_unless(stack[top-2].node->tok.type == TOK_VAR,
                                   "expected VAR two-down on the stack.\n");
                        die_unless(!stack[top].node->next && (stack[top].node->tok.type == TOK_INT
                                                              || stack[top].node->tok.type == TOK_FLOAT),
                                   "expected lonely INT or FLOAT expression on the stack.\n");
                        if (stack[top].node->tok.type == TOK_FLOAT)
                            stack[top-2].node->vector_index = (int)stack[top].node->tok.f;
                        else
                            stack[top-2].node->vector_index = stack[top].node->tok.i;
                        if (stack[top-2].node->vector_index > 0)
                            {FAIL("Vector indexing not yet implemented.");}
                        if (stack[top-2].node->vector_index < 0
                            || stack[top-2].node->vector_index >= vector_size)
                            {FAIL("Vector index outside input size.");}

                        exprnode_free(stack[top].node);
                        POP();
                    }
                }
                else {
                    // swap the expression down the stack
                    stack_obj_t tmp = stack[top-1];
                    stack[top-1] = stack[top];
                    stack[top] = tmp;
                }
            }

#if TRACING
            printstack(&stack[0], top);
#endif
            continue;
        }

        switch (stack[top].state) {
        case YEQUAL_Y:
            if (tok.type == TOK_VAR && tok.var == 'y')
                POP();
            else
                {FAIL("Error in y= prefix.");}
            next_token = 1;
            break;
        case YEQUAL_EQ:
            if (tok.type == TOK_OP && tok.op == '=') {
                POP();
            } else {
                {FAIL("Error in y= prefix.");}
            }
            next_token = 1;
            break;
        case EXPR:
            POP();
            PUSHSTATE(EXPR_RIGHT);
            PUSHSTATE(TERM);
            break;
        case EXPR_RIGHT:
            if (tok.type == TOK_OP) {
                POP();
                if (tok.op == '+' || tok.op == '-') {
                    APPEND_OP(tok);
                    PUSHSTATE(EXPR);
                    next_token = 1;
                }
            }
            else POP();
            break;
        case TERM:
            POP();
            PUSHSTATE(TERM_RIGHT);
            PUSHSTATE(VALUE);
            break;
        case TERM_RIGHT:
            if (tok.type == TOK_OP) {
                POP();
                if (tok.op == '*' || tok.op == '/') {
                    APPEND_OP(tok);
                    PUSHSTATE(TERM);
                    next_token = 1;
                }
            }
            else POP();
            break;
        case VALUE:
            if (tok.type == TOK_INT) {
                POP();
                PUSHEXPR(tok, 0);
                next_token = 1;
            } else if (tok.type == TOK_FLOAT) {
                POP();
                PUSHEXPR(tok, 1);
                next_token = 1;
            } else if (tok.type == TOK_VAR) {
                if (var_allowed) {
                    POP();
                    PUSHEXPR(tok, input_is_float);
                    PUSHSTATE(VAR_RIGHT);
                    next_token = 1;
                }
                else
                    {FAIL("Unexpected variable reference.");}
            } else if (tok.type == TOK_OPEN_PAREN) {
                POP();
                PUSHSTATE(CLOSE_PAREN);
                PUSHSTATE(EXPR);
                next_token = 1;
            } else if (tok.type == TOK_FUNC) {
                POP();
                if (tok.func == FUNC_UNKNOWN)
                    {FAIL("Unknown function.");}
                else {
                    PUSHEXPR(tok, 1);
                    int arity = function_table[tok.func].arity;
                    if (arity > 0) {
                        PUSHSTATE(CLOSE_PAREN);
                        PUSHSTATE(EXPR);
                        for (i=1; i < arity; i++) {
                            PUSHSTATE(COMMA);
                            PUSHSTATE(EXPR);
                        }
                        PUSHSTATE(OPEN_PAREN);
                    }
                    next_token = 1;
                }
            } else if (tok.type == TOK_OP && tok.op == '-') {
                POP();
                PUSHSTATE(NEGATE);
                PUSHSTATE(VALUE);
                next_token = 1;
            } else
                {FAIL("Expected value.");}
            break;
        case NEGATE:
            POP();
            // insert '0' before, and '-' after the expression.
            // set is_float according to trailing operator.
            if (stack[top].type == ST_NODE) {
                token_t t;
                t.type = TOK_INT;
                t.i = 0;
                exprnode e = exprnode_new(&t, 0);
                t.type = TOK_OP;
                t.op = '-';
                e->next = exprnode_new(&t, 0);
                collapse_expr_to_left(&e, stack[top].node, 1);
                stack[top].node = e;
            }
            else
                {FAIL("Expected to negate an expression.");}
            break;
        case VAR_RIGHT:
            if (tok.type == TOK_OPEN_SQUARE) {
                POP();
                PUSHSTATE(VAR_VECTINDEX);
            }
            else if (tok.type == TOK_OPEN_CURLY) {
                POP();
                PUSHSTATE(VAR_HISTINDEX);
            }
            else
                POP();
            break;
        case VAR_VECTINDEX:
            POP();
            if (tok.type == TOK_OPEN_SQUARE) {
                var_allowed = 0;
                PUSHSTATE(CLOSE_VECTINDEX);
                PUSHSTATE(EXPR);
                next_token = 1;
            }
            break;
        case VAR_HISTINDEX:
            POP();
            if (tok.type == TOK_OPEN_CURLY) {
                var_allowed = 0;
                PUSHSTATE(CLOSE_HISTINDEX);
                PUSHSTATE(EXPR);
                next_token = 1;
            }
            break;
        case CLOSE_VECTINDEX:
            if (tok.type == TOK_CLOSE_SQUARE) {
                var_allowed = 1;
                POP();
                PUSHSTATE(VAR_HISTINDEX);
                next_token = 1;
            }
            else
                {FAIL("Expected ']'.");}
            break;
        case CLOSE_HISTINDEX:
            if (tok.type == TOK_CLOSE_CURLY) {
                var_allowed = 1;
                POP();
                PUSHSTATE(VAR_VECTINDEX);
                next_token = 1;
            }
            else
                {FAIL("Expected '}'.");}
            break;
        case CLOSE_PAREN:
            if (tok.type == TOK_CLOSE_PAREN) {
                POP();
                next_token = 1;
                break;
            } else
                {FAIL("Expected ')'.");}
            break;
        case COMMA:
            if (tok.type == TOK_COMMA) {
                POP();
                // find previous expression on the stack
                for (i=top-1; i>=0 && stack[i].type!=ST_NODE; --i) {};
                if (i>=0) {
                    collapse_expr_to_left(&stack[i].node,
                                          stack[top].node, 0);
                    POP();
                }
                next_token = 1;
            } else
                {FAIL("Expected ','.");}
            break;
        case OPEN_PAREN:
            if (tok.type == TOK_OPEN_PAREN) {
                POP();
                next_token = 1;
            } else
                {FAIL("Expected '('.");}
            break;
        case END:
            if (tok.type == TOK_END) {
                POP();
                break;
            } else
                {FAIL("Expected END.");}
        default:
            FAIL("Unexpected parser state.");
            break;
        }

#if TRACING
        printstack(&stack[0], top);
#endif
    }

  done:
    if (!result) {
        if (error_message)
            printf("%s\n", error_message);
        goto cleanup;
    }

    // We need a limit, but this is a bit arbitrary.
    if (oldest_samps < -100) {
        trace("Expression contains history reference of %f\n", oldest_samps);
        goto cleanup;
    }

    // Coerce the final output if necessary
    exprnode e = result;
    while (e->next) e = e->next;
    if (e->is_float && !output_is_float) {
        token_t coerce;
        coerce.type = TOK_TOINT32;
        e->next = exprnode_new(&coerce, 0);
        e->next->is_float = 0;
    }
    else if (!e->is_float && output_is_float) {
        token_t coerce;
        coerce.type = TOK_TOFLOAT;
        e->next = exprnode_new(&coerce, 0);
        e->next->is_float = 1;
    }

    /* Special case: if this is a vector expression, we currently do
     * not completely support it.  However, we can "fake" vector
     * operations by performing the entire expression element-wise.
     * In this case, we have to disallow any vector indexing, so here
     * we scan the compiled expression and check for it.  This will be
     * removed in a future version. */
    if (vector_size > 1) {
        e = result;
        while (e) {
            if (e->tok.type == TOK_VAR && e->vector_index > 0) {
                trace("vector indexing not yet implemented\n");
                goto cleanup;
            }
            e = e->next;
        }
    }

    mapper_expr expr = malloc(sizeof(struct _mapper_expr));
    expr->node = result;
    expr->vector_size = vector_size;
    expr->history_size = (int)ceilf(-oldest_samps)+1;
    expr->history_pos = -1;
    expr->input_history = calloc(1, sizeof(mapper_signal_value_t)
                                    * vector_size * expr->history_size);
    expr->output_history = calloc(1, sizeof(mapper_signal_value_t)
                                     * expr->history_size);
    return expr;

  cleanup:
    for (i=0; i<top; i++) {
        if (stack[i].type == ST_NODE)
            exprnode_free(stack[i].node);
    }
    return 0;
}

#if TRACING
#define trace_eval printf
#else
static void trace_eval(const char *s,...) {}
#endif

int mapper_expr_evaluate(mapper_expr expr,
                         void* input_vector,
                         void* output_vector)
{
    mapper_signal_value_t stack[STACK_SIZE];
    mapper_signal_value_t left, right;
    int top = -1;
    exprnode node = expr->node;

    if (input_vector) {
        expr->history_pos = (expr->history_pos+1) % expr->history_size;
        memcpy(&expr->input_history[expr->history_pos*expr->vector_size],
               input_vector, expr->vector_size * sizeof(mapper_signal_value_t));
    }

    while (node) {
        switch (node->tok.type) {
        case TOK_INT:
            stack[++top].i32 = node->tok.i;
            break;
        case TOK_FLOAT:
            stack[++top].f = node->tok.f;
            break;
        case TOK_VAR:
            die_unless(input_vector,
                       "Input required but not provided for "
                       "expression evaluation.\n");
            {
                int idx = ((node->history_index + expr->history_pos
                            + expr->history_size) % expr->history_size);
                switch (node->tok.var) {
                case 'x':
                    idx = idx * expr->vector_size + node->vector_index;
                    stack[++top] = expr->input_history[idx];
                    break;
                case 'y':
                    stack[++top] = expr->output_history[idx];
                    break;
                default: goto error;
                }
            }
            break;
        case TOK_TOFLOAT:
            stack[top].f = (float)stack[top].i32;
            break;
        case TOK_TOINT32:
            stack[top].i32 = (int)stack[top].f;
            break;
        case TOK_OP:
            right = stack[top--];
            left = stack[top--];
            if (node->is_float) {
                trace_eval("%f %c %f = ", left.f, node->tok.op, right.f);
                switch (node->tok.op) {
                case '+': stack[++top].f = left.f + right.f; break;
                case '-': stack[++top].f = left.f - right.f; break;
                case '*': stack[++top].f = left.f * right.f; break;
                case '/': stack[++top].f = left.f / right.f; break;
                default: goto error;
                }
                trace_eval("%f\n", stack[top].f);
            } else {
                trace_eval("%d %c %d = ", left.i32, node->tok.op, right.i32);
                switch (node->tok.op) {
                case '+': stack[++top].i32 = left.i32 + right.i32; break;
                case '-': stack[++top].i32 = left.i32 - right.i32; break;
                case '*': stack[++top].i32 = left.i32 * right.i32; break;
                case '/': stack[++top].i32 = left.i32 / right.i32; break;
                default: goto error;
                }
                trace_eval("%d\n", stack[top].i32);
            }
            break;
        case TOK_FUNC:
            switch (function_table[node->tok.func].arity) {
            case 0:
                stack[++top].f = ((func_float_arity0*)function_table[node->tok.func].func)();
                trace_eval("%s = %f\n", function_table[node->tok.func].name,
                           stack[top].f);
                break;
            case 1:
                right = stack[top--];
                trace_eval("%s(%f) = ", function_table[node->tok.func].name, right.f);
                right.f = ((func_float_arity1*)function_table[node->tok.func].func)(right.f);
                trace_eval("%f\n", right.f);
                stack[++top].f = right.f;
                break;
            case 2:
                right = stack[top--];
                left = stack[top--];
                trace_eval("%s(%f,%f) = ", function_table[node->tok.func].name, left.f, right.f);
                right.f = ((func_float_arity2*)function_table[node->tok.func].func)(left.f, right.f);
                trace_eval("%f\n", right.f);
                stack[++top].f = right.f;
                break;
            default: goto error;
            }
            break;
        default: goto error;
        }
        node = node->next;
    }

    if (input_vector)
        expr->output_history[expr->history_pos] = stack[0];
    *(mapper_signal_value_t*)output_vector = stack[0];
    return 0;

  error:
    trace("Unexpected token in expression.");
    stack[0].i32 = 0;
    *(mapper_signal_value_t*)output_vector = stack[0];
    return 1;
}

```

### c/mapper_expr.h
```c

#ifndef __EXPR_H__
#define __EXPR_H__

/**** Expression parser/evaluator ****/

typedef struct _mapper_expr *mapper_expr;

mapper_expr mapper_expr_new_from_string(const char *str,
                                        int input_is_float,
                                        int output_is_float,
                                        int vector_size);

#ifdef DEBUG
void printexpr(const char*, mapper_expr);
#endif

int mapper_expr_evaluate(mapper_expr expr,
                         void* input_vector,
                         void* output_vector);

void mapper_expr_free(mapper_expr expr);

#endif // __EXPR_H__

```

### c/test.c
```c

#include <math.h>
#include <stdio.h>

#include "mapper_expr.h"

int test1()
{
    const char str[] = "y=26*2/2+log10(pi)+2.*pow(2,1*(3+7*.1)*1.1+x{-6*2+12})*3*4+cos(2.)";
    mapper_expr e = mapper_expr_new_from_string(str, 1, 1, 1);
    printf("Parsing %s\n", str);
    if (!e) { printf("Test FAILED.\n"); return 1; }
#ifdef DEBUG
    printexpr("Parser returned: ", e);
#endif
    printf("\n");

    float inp, outp;
    inp = 3.0;
    mapper_expr_evaluate(e, &inp, &outp);

    printf("Evaluate with x=%f: %f (expected: %f)\n",
           inp, outp,
           26*2/2+log10f(M_PI)+2.f*powf(2,1*(3+7*.1f)*1.1f+inp)*3*4+cosf(2.0f));

    mapper_expr_free(e);

    return 0;
}

int test2()
{
    const char str[] = "y=26*2/2+x*30/(20*1)";
    mapper_expr e = mapper_expr_new_from_string(str, 0, 0, 1);
    printf("\nParsing %s\n", str);
    if (!e) { printf("Test FAILED.\n"); return 1; }
#ifdef DEBUG
    printexpr("Parser returned: ", e);
#endif
    printf("\n");

    int inp, outp;
    inp = 3;
    mapper_expr_evaluate(e, &inp, &outp);

    printf("Evaluate with x=%d: %d (expected: %d)\n",
           inp, outp,
           26*2/2+inp*30/(20*1));

    inp = 321;
    mapper_expr_evaluate(e, &inp, &outp);

    printf("Evaluate with x=%d: %d (expected: %d)\n",
           inp, outp,
           26*2/2+inp*30/(20*1));

    mapper_expr_free(e);

    return 0;
}

int main()
{
    int rc=0;
    rc|=test1();
    rc|=test2();
    return rc;
}

```
