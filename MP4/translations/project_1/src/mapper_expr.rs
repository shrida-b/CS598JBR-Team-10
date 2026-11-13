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

#[allow(non_camel_case_types)]
pub type state_t = StateT;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StateT {
    YequalY,
    YequalEq,
    Expr,
    ExprRight,
    Term,
    TermRight,
    Value,
    Negate,
    VarRight,
    VarVectindex,
    VarHistindex,
    CloseVectindex,
    CloseHistindex,
    OpenParen,
    CloseParen,
    Comma,
    End,
}

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
