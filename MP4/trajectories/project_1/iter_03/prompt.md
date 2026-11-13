# Iteration 3/6: repair `expr`

The controller evaluated the crate independently after your previous iteration.

| Check | Result |
|---|---|
| Integrity | 1 violation(s) |
| Build | FAILED (1 error(s)) |
| Tests | 0/2 passed |
| Clippy (src) | n/a [n/a (does not build)] |
| Unsafe (primary total) | 0 [lines 0, calls 0, casts 0, ptr-arith 0] |
| #![forbid(unsafe_code)] | missing |



## Feedback from the evaluation

### Integrity checks
- public enum `state_t` missing

### Compiler (`cargo build`)
```
error: this file contains an unclosed delimiter
    --> src/mapper_expr.rs:1021:3
     |
485  | pub enum StateT {
     |                 - unclosed delimiter
...
1021 | }
     |  ^


```

### Tests (`cargo test`)
not run (build failed)

### Clippy (correctness / style / complexity / perf)
```
not run (build failed)
```

### Unsafe metrics
```
{"unsafe_lines": 0, "unsafe_calls": 0, "unsafe_casts": 0, "pointer_arithmetic": 0, "unsafe_blocks": 0, "unsafe_fns": 0, "unsafe_impls": 0, "raw_pointer_types": 0, "ffi": 0, "manual_alloc": 0, "transmute": 0, "forbid_unsafe_code": 0, "primary_total": 0}
Note: add `#![forbid(unsafe_code)]` at the top of src/lib.rs.
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
pub mod mapper_expr;
```

### rust/src/mapper_expr.rs
```rust
#![forbid(unsafe_code)]

use std::f32::consts::PI;
use std::collections::HashMap;
use std::sync::Arc;
use lazy_static::lazy_static;

macro_rules! trace_eval {
    ($($arg:tt)*) => {
        if TRACING {
            eprintln!("-- {}", format!($($arg)*));
        }
    };
}

const STACK_SIZE: usize = 256;
const TRACING: bool = false;

fn minf(x: f32, y: f32) -> f32 {
    if y < x { y } else { x }
}

fn maxf(x: f32, y: f32) -> f32 {
    if y > x { y } else { x }
}

fn pif() -> f32 {
    PI
}

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

lazy_static! {
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
        m.insert("logb", FunctionEntry { name: "logb", arity: 1, func: |x, _| x.log2().floor() });
        m.insert("exp2", FunctionEntry { name: "exp2", arity: 1, func: |x, _| 2.0_f32.powf(x) });
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
pub struct Token {
    pub token_type: TokenType,
    pub value: Option<f32>,
    pub int_value: Option<i32>,
    pub var: Option<char>,
    pub op: Option<char>,
    pub func: Option<ExprFunc>,
}

impl Token {
    fn new_float(f: f32) -> Self {
        Token { token_type: TokenType::Float, value: Some(f), int_value: None, var: None, op: None, func: None }
    }
    fn new_int(i: i32) -> Self {
        Token { token_type: TokenType::Int, value: None, int_value: Some(i), var: None, op: None, func: None }
    }
    fn new_op(op: char) -> Self {
        Token { token_type: TokenType::Op, value: None, int_value: None, var: None, op: Some(op), func: None }
    }
    fn new_var(var: char) -> Self {
        Token { token_type: TokenType::Var, value: None, int_value: None, var: Some(var), op: None, func: None }
    }
    fn new_func(func: ExprFunc) -> Self {
        Token { token_type: TokenType::Func, value: None, int_value: None, var: None, op: None, func: Some(func) }
    }
    fn open_paren() -> Self {
        Token { token_type: TokenType::OpenParen, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn close_paren() -> Self {
        Token { token_type: TokenType::CloseParen, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn open_square() -> Self {
        Token { token_type: TokenType::OpenSquare, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn close_square() -> Self {
        Token { token_type: TokenType::CloseSquare, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn open_curly() -> Self {
        Token { token_type: TokenType::OpenCurly, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn close_curly() -> Self {
        Token { token_type: TokenType::CloseCurly, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn comma() -> Self {
        Token { token_type: TokenType::Comma, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn end() -> Self {
        Token { token_type: TokenType::End, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn to_float() -> Self {
        Token { token_type: TokenType::ToFloat, value: None, int_value: None, var: None, op: None, func: None }
    }
    fn to_int32() -> Self {
        Token { token_type: TokenType::ToInt32, value: None, int_value: None, var: None, op: None, func: None }
    }
}

fn function_lookup(s: &str) -> Option<ExprFunc> {
    FUNCTION_TABLE.get(s).map(|_| {
        match s {
            "pow" => ExprFunc::Pow,
            "sin" => ExprFunc::Sin,
            "cos" => ExprFunc::Cos,
            "tan" => ExprFunc::Tan,
            "abs" => ExprFunc::Abs,
            "sqrt" => ExprFunc::Sqrt,
            "log" => ExprFunc::Log,
            "log10" => ExprFunc::Log10,
            "exp" => ExprFunc::Exp,
            "floor" => ExprFunc::Floor,
            "round" => ExprFunc::Round,
            "ceil" => ExprFunc::Ceil,
            "asin" => ExprFunc::Asin,
            "acos" => ExprFunc::Acos,
            "atan" => ExprFunc::Atan,
            "atan2" => ExprFunc::Atan2,
            "sinh" => ExprFunc::Sinh,
            "cosh" => ExprFunc::Cosh,
            "tanh" => ExprFunc::Tanh,
            "logb" => ExprFunc::Logb,
            "exp2" => ExprFunc::Exp2,
            "log2" => ExprFunc::Log2,
            "hypot" => ExprFunc::Hypot,
            "cbrt" => ExprFunc::Cbrt,
            "trunc" => ExprFunc::Trunc,
            "min" => ExprFunc::Min,
            "max" => ExprFunc::Max,
            "pi" => ExprFunc::Pi,
            _ => ExprFunc::Unknown,
        }
    })
}

struct Lexer<'a> {
    s: &'a str,
    pos: usize,
}

impl<'a> Lexer<'a> {
    fn new(s: &'a str) -> Self {
        Lexer { s, pos: 0 }
    }

    fn peek(&self) -> Option<char> {
        self.s.chars().nth(self.pos)
    }

    fn advance(&mut self) {
        if let Some(c) = self.peek() {
            self.pos += c.len_utf8();
        }
    }

    fn next_token(&mut self) -> Token {
        loop {
            let c = match self.peek() {
                Some(c) => c,
                None => return Token::end(),
            };

            if c.is_ascii_digit() {
                let start = self.pos;
                while let Some(c) = self.peek() {
                    if c.is_ascii_digit() {
                        self.advance();
                    } else {
                        break;
                    }
                }
                let int_str = &self.s[start..self.pos];
                let int_val: i32 = int_str.parse().unwrap();

                if self.peek() == Some('.') {
                    self.advance();
                    let frac_start = self.pos;
                    while let Some(c) = self.peek() {
                        if c.is_ascii_digit() {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    let frac_str = &self.s[frac_start..self.pos];
                    let float_str = format!("{}.{}", int_str, frac_str);
                    let float_val: f32 = float_str.parse().unwrap();
                    return Token::new_float(float_val);
                } else {
                    return Token::new_int(int_val);
                }
            }

            match c {
                '.' => {
                    self.advance();
                    let start = self.pos;
                    while let Some(c) = self.peek() {
                        if c.is_ascii_digit() {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    let frac_str = &self.s[start..self.pos];
                    let float_str = format!("0.{}", frac_str);
                    let float_val: f32 = float_str.parse().unwrap();
                    return Token::new_float(float_val);
                }
                '+' | '-' | '*' | '/' | '=' => {
                    self.advance();
                    return Token::new_op(c);
                }
                '(' => { self.advance(); return Token::open_paren(); }
                ')' => { self.advance(); return Token::close_paren(); }
                'x' | 'y' => { self.advance(); return Token::new_var(c); }
                '[' => { self.advance(); return Token::open_square(); }
                ']' => { self.advance(); return Token::close_square(); }
                '{' => { self.advance(); return Token::open_curly(); }
                '}' => { self.advance(); return Token::close_curly(); }
                ' ' | '\t' | '\r' | '\n' => { self.advance(); continue; }
                ',' => { self.advance(); return Token::comma(); }
                _ => {
                    if c.is_ascii_alphabetic() {
                        let start = self.pos;
                        while let Some(c) = self.peek() {
                            if c.is_ascii_alphanumeric() {
                                self.advance();
                            } else {
                                break;
                            }
                        }
                        let name = &self.s[start..self.pos];
                        if let Some(func) = function_lookup(name) {
                            return Token::new_func(func);
                        } else {
                            panic!("Unknown function: {}", name);
                        }
                    } else {
                        panic!("Unknown character '{}' in lexer", c);
                    }
                }
            }
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum MapperSignalValue {
    F(f32),
    I32(i32),
}

impl MapperSignalValue {
    pub fn as_f32(&self) -> Option<f32> {
        match self {
            MapperSignalValue::F(f) => Some(*f),
            MapperSignalValue::I32(i) => Some(*i as f32),
        }
    }

    pub fn as_i32(&self) -> Option<i32> {
        match self {
            MapperSignalValue::F(f) => Some(*f as i32),
            MapperSignalValue::I32(i) => Some(*i),
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

impl ExprNode {
    pub fn new() -> ExprNode {
        ExprNode {
            tok: Token::end(),
            is_float: 0,
            history_index: 0,
            vector_index: 0,
            next: None,
        }
    }

    pub fn expr_free(&self) {}
}

fn append_to_list(head: &mut ExprNode, tok: Token, is_float: i32) {
    let mut current = head;
    while let Some(next) = &current.next {
        current = Arc::get_mut(current.next.as_mut().unwrap()).unwrap();
    }
    let new_node = ExprNode {
        tok,
        is_float,
        history_index: 0,
        vector_index: 0,
        next: None,
    };
    current.next = Some(Arc::new(new_node));
}

fn collapse_expr_to_left(plhs: &mut ExprNode, rhs: &ExprNode, constant_folding: bool) {
    let mut refvar = false;

    let mut rhs_last = rhs.clone();
    if rhs_last.tok.token_type == TokenType::Var {
        refvar = true;
    }
    while let Some(next) = &rhs_last.next {
        if next.tok.token_type == TokenType::Var {
            refvar = true;
        }
        rhs_last = (**next).clone();
    }

    let mut plhs_last = plhs.clone();
    if plhs_last.tok.token_type == TokenType::Var {
        refvar = true;
    }
    while let Some(next) = &plhs_last.next {
        if next.tok.token_type == TokenType::Var {
            refvar = true;
        }
        plhs_last = (**next).clone();
    }

    let lhs_is_float = plhs_last.is_float != 0;
    let rhs_is_float = rhs_last.is_float != 0;
    let is_float = if lhs_is_float || rhs_is_float { 1 } else { 0 };

    let mut new_lhs = plhs.clone();
    if lhs_is_float && !rhs_is_float {
        let coerce = ExprNode {
            tok: Token::to_float(),
            is_float: 1,
            history_index: 0,
            vector_index: 0,
            next: None,
        };
        rhs_last.next = Some(Arc::new(coerce));
    } else if !lhs_is_float && rhs_is_float {
        let coerce = ExprNode {
            tok: Token::to_float(),
            is_float: 1,
            history_index: 0,
            vector_index: 0,
            next: Some(Arc::new(new_lhs)),
        };
        new_lhs = coerce;
    }

    rhs_last.next = Some(Arc::new(new_lhs));
    *plhs = rhs.clone();

    if constant_folding && !refvar {
        let mut expr = MapperExpr {
            node: plhs.clone(),
            vector_size: 1,
            history_size: 1,
            history_pos: 0,
            input_history: vec![],
            output_history: vec![],
        };
        let v = mapper_expr_evaluate(&mut expr, &MapperSignalValue::F(0.0));

        let mut current = plhs;
        while current.next.is_some() {
            current = Arc::get_mut(current.next.as_mut().unwrap()).unwrap();
        }
        current.next = None;
        current.is_float = is_float;
        if is_float != 0 {
            current.tok = Token::new_float(v.as_f32().unwrap());
        } else {
            current.tok = Token::new_int(v.as_i32().unwrap());
        }
    }
}

#[derive(Debug, Clone)]
pub struct MapperExpr {
    pub node: ExprNode,
    pub vector_size: i32,
    pub history_size: i32,
    pub history_pos: i32,
    pub input_history: Vec<MapperSignalValue>,
    pub output_history: Vec<MapperSignalValue>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub type state_t = StateT;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StateT {

#[derive(Debug, Clone)]
enum StackObj {
    State(StateT),
    Node(ExprNode),
}

pub fn mapper_expr_new_from_string(s: &str, input_is_float: i32, output_is_float: i32, vector_size: i32) -> MapperExpr {
    let mut lexer = Lexer::new(s);
    let mut stack: Vec<StackObj> = Vec::with_capacity(STACK_SIZE);
    let mut result: Option<ExprNode> = None;
    let _error_message: Option<String> = None;
    let mut next_token = true;
    let mut tok = Token::end();
    let mut var_allowed = true;
    let mut oldest_samps = 0.0f32;

    stack.push(StackObj::State(StateT::Expr));
    stack.push(StackObj::State(StateT::YequalEq));
    stack.push(StackObj::State(StateT::YequalY));

    loop {
        if stack.is_empty() {
            break;
        }

        if next_token {
            tok = lexer.next_token();
        }
        next_token = false;

        let is_node = matches!(stack.last(), Some(StackObj::Node(_)));
        if is_node {
            let node = match stack.pop().unwrap() {
                StackObj::Node(n) => n,
                _ => unreachable!(),
            };
            if stack.is_empty() {
                result = Some(node);
                break;
            }
            if let Some(&StackObj::State(state)) = stack.last() {
                stack.pop();
                if let Some(StackObj::Node(node2)) = stack.last().cloned() {
                    stack.pop();
                    if matches!(state, StateT::ExprRight | StateT::TermRight | StateT::CloseParen) {
                        let mut node2_mut = node2;
                        collapse_expr_to_left(&mut node2_mut, &node, true);
                        stack.push(StackObj::Node(node2_mut));
                    } else if state == StateT::CloseHistindex {
                        let mut node2_mut = node2;
                        if node.tok.token_type == TokenType::Float {
                            node2_mut.history_index = node.tok.value.unwrap() as i32;
                        } else {
                            node2_mut.history_index = node.tok.int_value.unwrap();
                        }
                        if oldest_samps > node2_mut.history_index as f32 {
                            oldest_samps = node2_mut.history_index as f32;
                        }
                        stack.push(StackObj::Node(node2_mut));
                    } else if state == StateT::CloseVectindex {
                        let mut node2_mut = node2;
                        if node.tok.token_type == TokenType::Float {
                            node2_mut.vector_index = node.tok.value.unwrap() as i32;
                        } else {
                            node2_mut.vector_index = node.tok.int_value.unwrap();
                        }
                        stack.push(StackObj::Node(node2_mut));
                    } else {
                        stack.push(StackObj::Node(node2));
                        stack.push(StackObj::Node(node));
                    }
                } else {
                    stack.push(StackObj::Node(node));
                }
            } else {
                stack.push(StackObj::Node(node));
            }
            continue;
        }

        let state = match stack.last() {
            Some(StackObj::State(s)) => *s,
            _ => break,
        };

        match state {
            StateT::YequalY => {
                if tok.token_type == TokenType::Var && tok.var == Some('y') {
                    stack.pop();
                } else {
                    break;
                }
                next_token = true;
            }
            StateT::YequalEq => {
                if tok.token_type == TokenType::Op && tok.op == Some('=') {
                    stack.pop();
                } else {
                    break;
                }
                next_token = true;
            }
            StateT::Expr => {
                stack.pop();
                stack.push(StackObj::State(StateT::ExprRight));
                stack.push(StackObj::State(StateT::Term));
            }
            StateT::ExprRight => {
                if tok.token_type == TokenType::Op {
                    stack.pop();
                    if tok.op == Some('+') || tok.op == Some('-') {
                        if let Some(StackObj::Node(node)) = stack.last_mut() {
                            let is_float = node.is_float;
                            append_to_list(node, tok, is_float);
                        }
                        stack.push(StackObj::State(StateT::Expr));
                        next_token = true;
                    }
                } else {
                    stack.pop();
                }
            }
            StateT::Term => {
                stack.pop();
                stack.push(StackObj::State(StateT::TermRight));
                stack.push(StackObj::State(StateT::Value));
            }
            StateT::TermRight => {
                if tok.token_type == TokenType::Op {
                    stack.pop();
                    if tok.op == Some('*') || tok.op == Some('/') {
                        if let Some(StackObj::Node(node)) = stack.last_mut() {
                            let is_float = node.is_float;
                            append_to_list(node, tok, is_float);
                        }
                        stack.push(StackObj::State(StateT::Term));
                        next_token = true;
                    }
                } else {
                    stack.pop();
                }
            }
            StateT::Value => {
                match tok.token_type {
                    TokenType::Int => {
                        stack.pop();
                        let node = ExprNode { tok, is_float: 0, history_index: 0, vector_index: 0, next: None };
                        stack.push(StackObj::Node(node));
                        next_token = true;
                    }
                    TokenType::Float => {
                        stack.pop();
                        let node = ExprNode { tok, is_float: 1, history_index: 0, vector_index: 0, next: None };
                        stack.push(StackObj::Node(node));
                        next_token = true;
                    }
                    TokenType::Var => {
                        if var_allowed {
                            stack.pop();
                            let node = ExprNode { tok, is_float: input_is_float, history_index: 0, vector_index: 0, next: None };
                            stack.push(StackObj::Node(node));
                            stack.push(StackObj::State(StateT::VarRight));
                            next_token = true;
                        } else {
                            break;
                        }
                    }
                    TokenType::OpenParen => {
                        stack.pop();
                        stack.push(StackObj::State(StateT::CloseParen));
                        stack.push(StackObj::State(StateT::Expr));
                        next_token = true;
                    }
                    TokenType::Func => {
                        stack.pop();
                        let node = ExprNode { tok, is_float: 1, history_index: 0, vector_index: 0, next: None };
                        stack.push(StackObj::Node(node));
                        let func_name = match tok.func {
                            Some(ExprFunc::Pow) => "pow",
                            Some(ExprFunc::Sin) => "sin",
                            Some(ExprFunc::Cos) => "cos",
                            Some(ExprFunc::Tan) => "tan",
                            Some(ExprFunc::Abs) => "abs",
                            Some(ExprFunc::Sqrt) => "sqrt",
                            Some(ExprFunc::Log) => "log",
                            Some(ExprFunc::Log10) => "log10",
                            Some(ExprFunc::Exp) => "exp",
                            Some(ExprFunc::Floor) => "floor",
                            Some(ExprFunc::Round) => "round",
                            Some(ExprFunc::Ceil) => "ceil",
                            Some(ExprFunc::Asin) => "asin",
                            Some(ExprFunc::Acos) => "acos",
                            Some(ExprFunc::Atan) => "atan",
                            Some(ExprFunc::Atan2) => "atan2",
                            Some(ExprFunc::Sinh) => "sinh",
                            Some(ExprFunc::Cosh) => "cosh",
                            Some(ExprFunc::Tanh) => "tanh",
                            Some(ExprFunc::Logb) => "logb",
                            Some(ExprFunc::Exp2) => "exp2",
                            Some(ExprFunc::Log2) => "log2",
                            Some(ExprFunc::Hypot) => "hypot",
                            Some(ExprFunc::Cbrt) => "cbrt",
                            Some(ExprFunc::Trunc) => "trunc",
                            Some(ExprFunc::Min) => "min",
                            Some(ExprFunc::Max) => "max",
                            Some(ExprFunc::Pi) => "pi",
                            _ => "",
                        };
                        let arity = FUNCTION_TABLE.get(func_name).map(|e| e.arity).unwrap_or(0);
                        if arity > 0 {
                            stack.push(StackObj::State(StateT::CloseParen));
                            stack.push(StackObj::State(StateT::Expr));
                            for _ in 1..arity {
                                stack.push(StackObj::State(StateT::Comma));
                                stack.push(StackObj::State(StateT::Expr));
                            }
                            stack.push(StackObj::State(StateT::OpenParen));
                        }
                        next_token = true;
                    }
                    TokenType::Op if tok.op == Some('-') => {
                        stack.pop();
                        stack.push(StackObj::State(StateT::Negate));
                        stack.push(StackObj::State(StateT::Value));
                        next_token = true;
                    }
                    _ => {
                        break;
                    }
                }
            }
            StateT::Negate => {
                stack.pop();
                if let Some(StackObj::Node(node)) = stack.last_mut() {
                    let zero_node = ExprNode { tok: Token::new_int(0), is_float: 0, history_index: 0, vector_index: 0, next: Some(Arc::new(ExprNode { tok: Token::new_op('-'), is_float: 0, history_index: 0, vector_index: 0, next: None })) };
                    let mut zero_node_mut = zero_node;
                    collapse_expr_to_left(&mut zero_node_mut, node, true);
                    *stack.last_mut().unwrap() = StackObj::Node(zero_node_mut);
                } else {
                    break;
                }
            }
            StateT::VarRight => {
                if tok.token_type == TokenType::OpenSquare {
                    stack.pop();
                    stack.push(StackObj::State(StateT::VarVectindex));
                } else if tok.token_type == TokenType::OpenCurly {
                    stack.pop();
                    stack.push(StackObj::State(StateT::VarHistindex));
                } else {
                    stack.pop();
                }
            }
            StateT::VarVectindex => {
                stack.pop();
                if tok.token_type == TokenType::OpenSquare {
                    var_allowed = false;
                    stack.push(StackObj::State(StateT::CloseVectindex));
                    stack.push(StackObj::State(StateT::Expr));
                    next_token = true;
                }
            }
            StateT::VarHistindex => {
                stack.pop();
                if tok.token_type == TokenType::OpenCurly {
                    var_allowed = false;
                    stack.push(StackObj::State(StateT::CloseHistindex));
                    stack.push(StackObj::State(StateT::Expr));
                    next_token = true;
                }
            }
            StateT::CloseVectindex => {
                if tok.token_type == TokenType::CloseSquare {
                    var_allowed = true;
                    stack.pop();
                    stack.push(StackObj::State(StateT::VarHistindex));
                    next_token = true;
                } else {
                    break;
                }
            }
            StateT::CloseHistindex => {
                if tok.token_type == TokenType::CloseCurly {
                    var_allowed = true;
                    stack.pop();
                    stack.push(StackObj::State(StateT::VarVectindex));
                    next_token = true;
                } else {
                    break;
                }
            }
            StateT::CloseParen => {
                if tok.token_type == TokenType::CloseParen {
                    stack.pop();
                    next_token = true;
                } else {
                    break;
                }
            }
            StateT::Comma => {
                if tok.token_type == TokenType::Comma {
                    stack.pop();
                    let mut i = stack.len();
                    while i > 0 {
                        i -= 1;
                        if matches!(stack[i], StackObj::Node(_)) {
                            break;
                        }
                    }
                    if i < stack.len() {
                        if let StackObj::Node(prev_node) = &stack[i] {
                            let prev_node = prev_node.clone();
                            if let StackObj::Node(top_node) = &stack[stack.len() - 1] {
                                let top_node = top_node.clone();
                                let mut prev_node_mut = prev_node;
                                collapse_expr_to_left(&mut prev_node_mut, &top_node, false);
                                stack[i] = StackObj::Node(prev_node_mut);
                            }
                            stack.pop();
                        }
                    }
                    next_token = true;
                } else {
                    break;
                }
            }
            StateT::OpenParen => {
                if tok.token_type == TokenType::OpenParen {
                    stack.pop();
                    next_token = true;
                } else {
                    break;
                }
            }
            StateT::End => {
                if tok.token_type == TokenType::End {
                    stack.pop();
                } else {
                    break;
                }
            }
        }
    }

    let mut result = result.unwrap_or_else(ExprNode::new);
    let mut last_node = &mut result;
    while let Some(next) = &last_node.next {
        last_node = Arc::get_mut(last_node.next.as_mut().unwrap()).unwrap();
    }
    if last_node.is_float != 0 && output_is_float == 0 {
        append_to_list(&mut result, Token::to_int32(), 0);
    } else if last_node.is_float == 0 && output_is_float != 0 {
        append_to_list(&mut result, Token::to_float(), 1);
    }

    let history_size = (oldest_samps.ceil() as i32).abs() + 1;
    let input_history = vec![MapperSignalValue::F(0.0); (vector_size * history_size) as usize];
    let output_history = vec![MapperSignalValue::F(0.0); history_size as usize];

    MapperExpr {
        node: result,
        vector_size,
        history_size,
        history_pos: -1,
        input_history,
        output_history,
    }
}

pub fn mapper_expr_evaluate<'a>(mapper: &mut MapperExpr, input: &'a MapperSignalValue) -> MapperSignalValue {
    let mut stack: Vec<MapperSignalValue> = Vec::with_capacity(STACK_SIZE);
    let mut node: Option<Arc<ExprNode>> = Some(Arc::new(mapper.node.clone()));

    mapper.history_pos = (mapper.history_pos + 1) % mapper.history_size;
    let start = (mapper.history_pos * mapper.vector_size) as usize;
    let end = start + mapper.vector_size as usize;
    if end <= mapper.input_history.len() {
        for i in start..end {
            mapper.input_history[i] = *input;
        }
    }

    while let Some(current) = node {
        match current.tok.token_type {
            TokenType::Int => {
                stack.push(MapperSignalValue::I32(current.tok.int_value.unwrap()));
            }
            TokenType::Float => {
                stack.push(MapperSignalValue::F(current.tok.value.unwrap()));
            }
            TokenType::Var => {
                let idx = ((current.history_index + mapper.history_pos + mapper.history_size) % mapper.history_size) as usize;
                match current.tok.var {
                    Some('x') => {
                        let idx = idx * mapper.vector_size as usize + current.vector_index as usize;
                        if idx < mapper.input_history.len() {
                            stack.push(mapper.input_history[idx]);
                        } else {
                            stack.push(MapperSignalValue::F(0.0));
                        }
                    }
                    Some('y') => {
                        if idx < mapper.output_history.len() {
                            stack.push(mapper.output_history[idx]);
                        } else {
                            stack.push(MapperSignalValue::F(0.0));
                        }
                    }
                    _ => {
                        stack.push(MapperSignalValue::F(0.0));
                    }
                }
            }
            TokenType::ToFloat => {
                if let Some(top) = stack.last_mut() {
                    *top = MapperSignalValue::F(top.as_f32().unwrap());
                }
            }
            TokenType::ToInt32 => {
                if let Some(top) = stack.last_mut() {
                    *top = MapperSignalValue::I32(top.as_i32().unwrap());
                }
            }
            TokenType::Op => {
                if stack.len() < 2 {
                    stack.push(MapperSignalValue::F(0.0));
                    node = current.next.clone();
                    continue;
                }
                let right = stack.pop().unwrap();
                let left = stack.pop().unwrap();
                let is_float = current.is_float != 0;
                if is_float {
                    let l = left.as_f32().unwrap();
                    let r = right.as_f32().unwrap();
                    let result = match current.tok.op {
                        Some('+') => l + r,
                        Some('-') => l - r,
                        Some('*') => l * r,
                        Some('/') => l / r,
                        _ => 0.0,
                    };
                    trace_eval!("{} {} {} = {}", l, current.tok.op.unwrap(), r, result);
                    stack.push(MapperSignalValue::F(result));
                } else {
                    let l = left.as_i32().unwrap();
                    let r = right.as_i32().unwrap();
                    let result = match current.tok.op {
                        Some('+') => l + r,
                        Some('-') => l - r,
                        Some('*') => l * r,
                        Some('/') => l / r,
                        _ => 0,
                    };
                    trace_eval!("{} {} {} = {}", l, current.tok.op.unwrap(), r, result);
                    stack.push(MapperSignalValue::I32(result));
                }
            }
            TokenType::Func => {
                if let Some(func) = current.tok.func {
                    let func_name = match func {
                        ExprFunc::Pow => "pow",
                        ExprFunc::Sin => "sin",
                        ExprFunc::Cos => "cos",
                        ExprFunc::Tan => "tan",
                        ExprFunc::Abs => "abs",
                        ExprFunc::Sqrt => "sqrt",
                        ExprFunc::Log => "log",
                        ExprFunc::Log10 => "log10",
                        ExprFunc::Exp => "exp",
                        ExprFunc::Floor => "floor",
                        ExprFunc::Round => "round",
                        ExprFunc::Ceil => "ceil",
                        ExprFunc::Asin => "asin",
                        ExprFunc::Acos => "acos",
                        ExprFunc::Atan => "atan",
                        ExprFunc::Atan2 => "atan2",
                        ExprFunc::Sinh => "sinh",
                        ExprFunc::Cosh => "cosh",
                        ExprFunc::Tanh => "tanh",
                        ExprFunc::Logb => "logb",
                        ExprFunc::Exp2 => "exp2",
                        ExprFunc::Log2 => "log2",
                        ExprFunc::Hypot => "hypot",
                        ExprFunc::Cbrt => "cbrt",
                        ExprFunc::Trunc => "trunc",
                        ExprFunc::Min => "min",
                        ExprFunc::Max => "max",
                        ExprFunc::Pi => "pi",
                        _ => "",
                    };
                    if let Some(entry) = FUNCTION_TABLE.get(func_name) {
                        match entry.arity {
                            0 => {
                                let result = (entry.func)(0.0, 0.0);
                                trace_eval!("{} = {}", entry.name, result);
                                stack.push(MapperSignalValue::F(result));
                            }
                            1 => {
                                if let Some(right) = stack.pop() {
                                    let r = right.as_f32().unwrap();
                                    let result = (entry.func)(r, 0.0);
                                    trace_eval!("{}({}) = {}", entry.name, r, result);
                                    stack.push(MapperSignalValue::F(result));
                                }
                            }
                            2 => {
                                if stack.len() >= 2 {
                                    let right = stack.pop().unwrap();
                                    let left = stack.pop().unwrap();
                                    let l = left.as_f32().unwrap();
                                    let r = right.as_f32().unwrap();
                                    let result = (entry.func)(l, r);
                                    trace_eval!("{}({},{}) = {}", entry.name, l, r, result);
                                    stack.push(MapperSignalValue::F(result));
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
            _ => {
                stack.push(MapperSignalValue::F(0.0));
            }
        }
        node = current.next.clone();
    }

    let result = stack.pop().unwrap_or(MapperSignalValue::F(0.0));
    if (mapper.history_pos as usize) < mapper.output_history.len() {
        mapper.output_history[mapper.history_pos as usize] = result;
    }
    result
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
