use std::collections::HashMap;
use std::sync::Arc;

#[derive(Clone, Copy, Debug)]
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
    if y < x { y } else { x }
}
fn maxf(x: f32, y: f32) -> f32 {
    if y > x { y } else { x }
}
fn pif() -> f32 {
    std::f32::consts::PI
}

#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExprFunc {
    Unknown = -1,
    Pow = 0, Sin, Cos, Tan, Abs, Sqrt, Log, Log10, Exp, Floor, Round, Ceil,
    Asin, Acos, Atan, Atan2, Sinh, Cosh, Tanh, Logb, Exp2, Log2, Hypot, Cbrt,
    Trunc, Min, Max, Pi,
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
        m.insert("logb", FunctionEntry { name: "logb", arity: 1, func: |x, _| x.abs().log2().floor() });
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
pub enum TokenType {
    Float, Int, Op, OpenParen, CloseParen, Var, OpenSquare, CloseSquare,
    OpenCurly, CloseCurly, Func, Comma, End, ToFloat, ToInt32,
}

#[derive(Debug, Clone, Copy)]
pub struct Token {
    pub token_type: TokenType,
    pub value: Option<f32>,
    pub int_value: Option<i32>,
    pub var: Option<char>,
    pub op: Option<char>,
}

fn function_lookup(s: &str) -> Option<&'static FunctionEntry> {
    FUNCTION_TABLE.get(s)
}

const FUNCTIONS: &[&str] = &[
    "pow", "sin", "cos", "tan", "abs", "sqrt", "log", "log10", "exp", "floor",
    "round", "ceil", "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh",
    "logb", "exp2", "log2", "hypot", "cbrt", "trunc", "min", "max", "pi",
];

fn expr_lex(s: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let mut chars = s.chars().peekable();

    while let Some(&c) = chars.peek() {
        if c.is_whitespace() {
            chars.next();
            continue;
        }

        if c.is_ascii_digit() {
            let mut num_str = String::new();
            while let Some(&c) = chars.peek() {
                if c.is_ascii_digit() {
                    num_str.push(chars.next().unwrap());
                } else {
                    break;
                }
            }
            
            if chars.peek() == Some(&'.') {
                chars.next();
                let mut float_str = num_str.clone();
                float_str.push('.');
                while let Some(&c) = chars.peek() {
                    if c.is_ascii_digit() {
                        float_str.push(chars.next().unwrap());
                    } else {
                        break;
                    }
                }
                let f = float_str.parse::<f32>().unwrap_or(0.0);
                tokens.push(Token {
                    token_type: TokenType::Float,
                    value: Some(f),
                    int_value: None,
                    var: None,
                    op: None,
                });
            } else {
                let i = num_str.parse::<i32>().unwrap_or(0);
                tokens.push(Token {
                    token_type: TokenType::Int,
                    value: None,
                    int_value: Some(i),
                    var: None,
                    op: None,
                });
            }
            continue;
        }

        match c {
            '.' => {
                chars.next();
                let mut float_str = String::from("0.");
                let mut has_digits = false;
                while let Some(&c) = chars.peek() {
                    if c.is_ascii_digit() {
                        float_str.push(chars.next().unwrap());
                        has_digits = true;
                    } else {
                        break;
                    }
                }
                if has_digits {
                    let f = float_str.parse::<f32>().unwrap_or(0.0);
                    tokens.push(Token {
                        token_type: TokenType::Float,
                        value: Some(f),
                        int_value: None,
                        var: None,
                        op: None,
                    });
                }
            }
            '+' | '-' | '*' | '/' | '=' => {
                tokens.push(Token {
                    token_type: TokenType::Op,
                    value: None,
                    int_value: None,
                    var: None,
                    op: Some(chars.next().unwrap()),
                });
            }
            '(' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::OpenParen,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            ')' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::CloseParen,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            'x' | 'y' => {
                tokens.push(Token {
                    token_type: TokenType::Var,
                    value: None,
                    int_value: None,
                    var: Some(chars.next().unwrap()),
                    op: None,
                });
            }
            '[' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::OpenSquare,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            ']' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::CloseSquare,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            '{' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::OpenCurly,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            '}' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::CloseCurly,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            ',' => {
                chars.next();
                tokens.push(Token {
                    token_type: TokenType::Comma,
                    value: None,
                    int_value: None,
                    var: None,
                    op: None,
                });
            }
            _ => {
                if c.is_ascii_alphabetic() {
                    let mut name = String::new();
                    while let Some(&c) = chars.peek() {
                        if c.is_ascii_alphanumeric() {
                            name.push(chars.next().unwrap());
                        } else {
                            break;
                        }
                    }
                    if let Some(_entry) = function_lookup(&name) {
                        let idx = FUNCTIONS.iter().position(|&f| f == name).unwrap();
                        tokens.push(Token {
                            token_type: TokenType::Func,
                            value: None,
                            int_value: Some(idx as i32),
                            var: None,
                            op: None,
                        });
                    }
                } else {
                    chars.next();
                }
            }
        }
    }
    tokens.push(Token {
        token_type: TokenType::End,
        value: None,
        int_value: None,
        var: None,
        op: None,
    });
    tokens
}

#[derive(Clone)]
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
            tok: Token {
                token_type: TokenType::End,
                value: None,
                int_value: None,
                var: None,
                op: None,
            },
            is_float: 0,
            history_index: 0,
            vector_index: 0,
            next: None,
        }
    }
    pub fn expr_free(&self) {}
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
    YEQUAL_Y, YEQUAL_EQ, EXPR, EXPR_RIGHT, TERM, TERM_RIGHT, VALUE, NEGATE,
    VAR_RIGHT, VAR_VECTINDEX, VAR_HISTINDEX, CLOSE_VECTINDEX, CLOSE_HISTINDEX,
    OPEN_PAREN, CLOSE_PAREN, COMMA, END,
}

enum stack_obj_t {
    State(state_t),
    Node(Arc<ExprNode>),
}

fn list_to_vec(head: Arc<ExprNode>) -> Vec<Arc<ExprNode>> {
    let mut v = Vec::new();
    let mut curr = Some(head);
    while let Some(n) = curr {
        v.push(n.clone());
        curr = n.next.clone();
    }
    v
}

fn vec_to_list(v: Vec<Arc<ExprNode>>) -> Arc<ExprNode> {
    let mut next = None;
    for n in v.into_iter().rev() {
        let mut new_node = (*n).clone();
        new_node.next = next;
        next = Some(Arc::new(new_node));
    }
    next.unwrap()
}

fn collapse_expr_to_left(plhs: &mut Arc<ExprNode>, rhs: Arc<ExprNode>, constant_folding: bool, vector_size: i32, history_size: i32) {
    let mut lhs_v = list_to_vec(plhs.clone());
    let rhs_v = list_to_vec(rhs);
    
    let mut refvar = false;
    for n in &lhs_v { if n.tok.token_type == TokenType::Var { refvar = true; } }
    for n in &rhs_v { if n.tok.token_type == TokenType::Var { refvar = true; } }
    
    let last_lhs = lhs_v.pop().unwrap();
    let last_rhs_is_float = rhs_v.last().unwrap().is_float;
    
    let is_float = last_lhs.is_float != 0 || last_rhs_is_float != 0;
    
    let mut final_rhs_v = rhs_v;
    let mut final_last_lhs = (*last_lhs).clone();
    
    if last_lhs.is_float != 0 && last_rhs_is_float == 0 {
        final_rhs_v.push(Arc::new(ExprNode {
            tok: Token { token_type: TokenType::ToFloat, value: None, int_value: None, var: None, op: None },
            is_float: 1, history_index: 0, vector_index: 0, next: None,
        }));
    } else if last_lhs.is_float == 0 && last_rhs_is_float != 0 {
        lhs_v.push(Arc::new(ExprNode {
            tok: Token { token_type: TokenType::ToFloat, value: None, int_value: None, var: None, op: None },
            is_float: 1, history_index: 0, vector_index: 0, next: None,
        }));
        final_last_lhs.is_float = 1;
    }
    
    let mut result_v = lhs_v;
    result_v.extend(final_rhs_v);
    result_v.push(Arc::new(final_last_lhs));
    
    let mut result_list = vec_to_list(result_v);
    
    if constant_folding && !refvar {
        let mut dummy_expr = MapperExpr {
            node: (*result_list).clone(),
            vector_size,
            history_size,
            history_pos: -1,
            input_history: vec![MapperSignalValue::I32(0); (vector_size * history_size) as usize],
            output_history: vec![MapperSignalValue::I32(0); history_size as usize],
        };
        let val = mapper_expr_evaluate(&mut dummy_expr, &MapperSignalValue::I32(0));
        
        let new_tok = if is_float {
            Token { token_type: TokenType::Float, value: Some(val.as_f32().unwrap()), int_value: None, var: None, op: None }
        } else {
            Token { token_type: TokenType::Int, value: None, int_value: Some(val.as_i32().unwrap()), var: None, op: None }
        };
        
        result_list = Arc::new(ExprNode {
            tok: new_tok,
            is_float: if is_float { 1 } else { 0 },
            history_index: 0,
            vector_index: 0,
            next: None,
        });
    }
    
    *plhs = result_list;
}

pub fn mapper_expr_new_from_string(s: &str, input_is_float: i32, output_is_float: i32, vector_size: i32) -> MapperExpr {
    let tokens = expr_lex(s);
    let mut tok_idx = 0;
    let mut stack: Vec<stack_obj_t> = Vec::new();
    let mut oldest_samps = 0.0f32;
    let mut var_allowed = true;

    stack.push(stack_obj_t::State(state_t::EXPR));
    stack.push(stack_obj_t::State(state_t::YEQUAL_EQ));
    stack.push(stack_obj_t::State(state_t::YEQUAL_Y));

    while !stack.is_empty() {
        let top = stack.len() - 1;
        let mut next_token = false;
        let tok = tokens[tok_idx];

        if let stack_obj_t::Node(node) = &stack[top] {
            let node = node.clone();
            if top == 0 {
                let mut final_list = list_to_vec(node);
                let last = final_list.last().unwrap();
                if last.is_float != 0 && output_is_float == 0 {
                    final_list.push(Arc::new(ExprNode {
                        tok: Token { token_type: TokenType::ToInt32, value: None, int_value: None, var: None, op: None },
                        is_float: 0, history_index: 0, vector_index: 0, next: None,
                    }));
                } else if last.is_float == 0 && output_is_float != 0 {
                    final_list.push(Arc::new(ExprNode {
                        tok: Token { token_type: TokenType::ToFloat, value: None, int_value: None, var: None, op: None },
                        is_float: 1, history_index: 0, vector_index: 0, next: None,
                    }));
                }
                
                let history_size = ((-oldest_samps).ceil() as i32) + 1;
                let node = (*vec_to_list(final_list)).clone();
                return MapperExpr {
                    node,
                    vector_size,
                    history_size,
                    history_pos: -1,
                    input_history: vec![MapperSignalValue::I32(0); (vector_size * history_size) as usize],
                    output_history: vec![MapperSignalValue::I32(0); history_size as usize],
                };
            }
            
            if top >= 2 {
                let state_idx = top - 1;
                let prev_node_idx = top - 2;
                let mut collapsed = false;
                if let (stack_obj_t::Node(_), stack_obj_t::State(state)) = (&stack[prev_node_idx], &stack[state_idx]) {
                    let state = *state;
                    if state == state_t::EXPR_RIGHT || state == state_t::TERM_RIGHT || state == state_t::CLOSE_PAREN {
                        let node = if let stack_obj_t::Node(n) = stack.pop().unwrap() { n } else { panic!() };
                        if let stack_obj_t::Node(mut prev_node) = stack.remove(prev_node_idx) {
                            collapse_expr_to_left(&mut prev_node, node, true, vector_size, 100);
                            stack.insert(prev_node_idx, stack_obj_t::Node(prev_node));
                        }
                        collapsed = true;
                    } else if state == state_t::CLOSE_HISTINDEX {
                        stack.pop(); // pop node
                        if let stack_obj_t::Node(prev_node) = &mut stack[prev_node_idx] {
                            let mut new_prev = (**prev_node).clone();
                            let idx = if node.tok.token_type == TokenType::Float { node.tok.value.unwrap() as i32 } else { node.tok.int_value.unwrap() };
                            new_prev.history_index = idx;
                            if (idx as f32) < oldest_samps { oldest_samps = idx as f32; }
                            *prev_node = Arc::new(new_prev);
                        }
                        collapsed = true;
                    } else if state == state_t::CLOSE_VECTINDEX {
                        stack.pop(); // pop node
                        if let stack_obj_t::Node(prev_node) = &mut stack[prev_node_idx] {
                            let mut new_prev = (**prev_node).clone();
                            let idx = if node.tok.token_type == TokenType::Float { node.tok.value.unwrap() as i32 } else { node.tok.int_value.unwrap() };
                            new_prev.vector_index = idx;
                            *prev_node = Arc::new(new_prev);
                        }
                        collapsed = true;
                    }
                }
                if collapsed { continue; }
            }
            
            let node_obj = stack.pop().unwrap();
            let state_obj = stack.pop().unwrap();
            stack.push(node_obj);
            stack.push(state_obj);
            continue;
        }
        
        let state = if let stack_obj_t::State(s) = stack.pop().unwrap() { s } else { panic!() };
        match state {
            state_t::YEQUAL_Y => {
                if tok.token_type == TokenType::Var && tok.var == Some('y') { next_token = true; }
            }
            state_t::YEQUAL_EQ => {
                if tok.token_type == TokenType::Op && tok.op == Some('=') { next_token = true; }
            }
            state_t::EXPR => {
                stack.push(stack_obj_t::State(state_t::EXPR_RIGHT));
                stack.push(stack_obj_t::State(state_t::TERM));
            }
            state_t::EXPR_RIGHT => {
                if tok.token_type == TokenType::Op && (tok.op == Some('+') || tok.op == Some('-')) {
                    if let Some(stack_obj_t::Node(mut node)) = stack.pop() {
                        let mut v = list_to_vec(node);
                        v.push(Arc::new(ExprNode {
                            tok, is_float: v.last().unwrap().is_float, history_index: 0, vector_index: 0, next: None,
                        }));
                        node = vec_to_list(v);
                        stack.push(stack_obj_t::Node(node));
                        stack.push(stack_obj_t::State(state_t::EXPR));
                        next_token = true;
                    }
                }
            }
            state_t::TERM => {
                stack.push(stack_obj_t::State(state_t::TERM_RIGHT));
                stack.push(stack_obj_t::State(state_t::VALUE));
            }
            state_t::TERM_RIGHT => {
                if tok.token_type == TokenType::Op && (tok.op == Some('*') || tok.op == Some('/')) {
                    if let Some(stack_obj_t::Node(mut node)) = stack.pop() {
                        let mut v = list_to_vec(node);
                        v.push(Arc::new(ExprNode {
                            tok, is_float: v.last().unwrap().is_float, history_index: 0, vector_index: 0, next: None,
                        }));
                        node = vec_to_list(v);
                        stack.push(stack_obj_t::Node(node));
                        stack.push(stack_obj_t::State(state_t::TERM));
                        next_token = true;
                    }
                }
            }
            state_t::VALUE => {
                if tok.token_type == TokenType::Int {
                    stack.push(stack_obj_t::Node(Arc::new(ExprNode {
                        tok, is_float: 0, history_index: 0, vector_index: 0, next: None,
                    })));
                    next_token = true;
                } else if tok.token_type == TokenType::Float {
                    stack.push(stack_obj_t::Node(Arc::new(ExprNode {
                        tok, is_float: 1, history_index: 0, vector_index: 0, next: None,
                    })));
                    next_token = true;
                } else if tok.token_type == TokenType::Var {
                    if var_allowed {
                        stack.push(stack_obj_t::Node(Arc::new(ExprNode {
                            tok, is_float: input_is_float, history_index: 0, vector_index: 0, next: None,
                        })));
                        stack.push(stack_obj_t::State(state_t::VAR_RIGHT));
                        next_token = true;
                    }
                } else if tok.token_type == TokenType::OpenParen {
                    stack.push(stack_obj_t::State(state_t::CLOSE_PAREN));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                } else if tok.token_type == TokenType::Func {
                    let func_idx = tok.int_value.unwrap() as usize;
                    let entry = FUNCTION_TABLE.get(FUNCTIONS[func_idx]).unwrap();
                    stack.push(stack_obj_t::Node(Arc::new(ExprNode {
                        tok, is_float: 1, history_index: 0, vector_index: 0, next: None,
                    })));
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
                } else if tok.token_type == TokenType::Op && tok.op == Some('-') {
                    stack.push(stack_obj_t::State(state_t::NEGATE));
                    stack.push(stack_obj_t::State(state_t::VALUE));
                    next_token = true;
                }
            }
            state_t::NEGATE => {
                if let Some(stack_obj_t::Node(node)) = stack.pop() {
                    let mut plhs = Arc::new(ExprNode {
                        tok: Token { token_type: TokenType::Int, value: None, int_value: Some(0), var: None, op: None },
                        is_float: 0, history_index: 0, vector_index: 0, next: None,
                    });
                    let mut v = list_to_vec(plhs);
                    v.push(Arc::new(ExprNode {
                        tok: Token { token_type: TokenType::Op, value: None, int_value: None, var: None, op: Some('-') },
                        is_float: 0, history_index: 0, vector_index: 0, next: None,
                    }));
                    plhs = vec_to_list(v);
                    collapse_expr_to_left(&mut plhs, node, true, vector_size, 100);
                    stack.push(stack_obj_t::Node(plhs));
                }
            }
            state_t::VAR_RIGHT => {
                if tok.token_type == TokenType::OpenSquare {
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                    next_token = true;
                } else if tok.token_type == TokenType::OpenCurly {
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                    next_token = true;
                }
            }
            state_t::VAR_VECTINDEX => {
                if tok.token_type == TokenType::OpenSquare {
                    var_allowed = false;
                    stack.push(stack_obj_t::State(state_t::CLOSE_VECTINDEX));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = true;
                }
            }
            state_t::VAR_HISTINDEX => {
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
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                    next_token = true;
                }
            }
            state_t::CLOSE_HISTINDEX => {
                if tok.token_type == TokenType::CloseCurly {
                    var_allowed = true;
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                    next_token = true;
                }
            }
            state_t::CLOSE_PAREN => {
                if tok.token_type == TokenType::CloseParen { next_token = true; }
            }
            state_t::COMMA => {
                if tok.token_type == TokenType::Comma {
                    let node = if let Some(stack_obj_t::Node(n)) = stack.pop() { n } else { panic!() };
                    let mut i = stack.len();
                    while i > 0 {
                        i -= 1;
                        if let stack_obj_t::Node(_) = &stack[i] {
                            if let stack_obj_t::Node(mut prev) = stack.remove(i) {
                                collapse_expr_to_left(&mut prev, node, false, vector_size, 100);
                                stack.insert(i, stack_obj_t::Node(prev));
                            }
                            break;
                        }
                    }
                    next_token = true;
                }
            }
            state_t::OPEN_PAREN => {
                if tok.token_type == TokenType::OpenParen { next_token = true; }
            }
            _ => {}
        }
        if next_token { tok_idx += 1; }
    }

    MapperExpr {
        node: ExprNode::new(),
        vector_size,
        history_size: 1,
        history_pos: -1,
        input_history: vec![MapperSignalValue::I32(0); vector_size as usize],
        output_history: vec![MapperSignalValue::I32(0); 1],
    }
}

pub fn mapper_expr_evaluate(mapper: &mut MapperExpr, input: &MapperSignalValue) -> MapperSignalValue {
    let mut stack: Vec<MapperSignalValue> = Vec::with_capacity(STACK_SIZE);
    
    if mapper.history_size > 0 {
        mapper.history_pos = (mapper.history_pos + 1) % mapper.history_size;
        let pos = mapper.history_pos as usize;
        let vec_size = mapper.vector_size as usize;
        
        if mapper.input_history.len() < (pos + 1) * vec_size {
            mapper.input_history.resize((pos + 1) * vec_size, MapperSignalValue::I32(0));
        }
        mapper.input_history[pos * vec_size] = *input;
    }

    let mut curr = Some(Arc::new(mapper.node.clone()));
    while let Some(node) = curr {
        match node.tok.token_type {
            TokenType::Int => {
                stack.push(MapperSignalValue::I32(node.tok.int_value.unwrap()));
            }
            TokenType::Float => {
                stack.push(MapperSignalValue::F(node.tok.value.unwrap()));
            }
            TokenType::Var => {
                let h_idx = (node.history_index + mapper.history_pos + mapper.history_size) % mapper.history_size;
                let v_idx = node.vector_index;
                match node.tok.var {
                    Some('x') => {
                        let idx = (h_idx * mapper.vector_size + v_idx) as usize;
                        stack.push(mapper.input_history[idx]);
                    }
                    Some('y') => {
                        let idx = h_idx as usize;
                        stack.push(mapper.output_history[idx]);
                    }
                    _ => stack.push(MapperSignalValue::I32(0)),
                }
            }
            TokenType::ToFloat => {
                if let Some(val) = stack.pop() {
                    stack.push(MapperSignalValue::F(val.as_f32().unwrap()));
                }
            }
            TokenType::ToInt32 => {
                if let Some(val) = stack.pop() {
                    stack.push(MapperSignalValue::I32(val.as_i32().unwrap()));
                }
            }
            TokenType::Op => {
                let right = stack.pop().unwrap();
                let left = stack.pop().unwrap();
                if node.is_float != 0 {
                    let l = left.as_f32().unwrap();
                    let r = right.as_f32().unwrap();
                    let res = match node.tok.op {
                        Some('+') => l + r,
                        Some('-') => l - r,
                        Some('*') => l * r,
                        Some('/') => l / r,
                        _ => 0.0,
                    };
                    stack.push(MapperSignalValue::F(res));
                } else {
                    let l = left.as_i32().unwrap();
                    let r = right.as_i32().unwrap();
                    let res = match node.tok.op {
                        Some('+') => l.wrapping_add(r),
                        Some('-') => l.wrapping_sub(r),
                        Some('*') => l.wrapping_mul(r),
                        Some('/') => if r != 0 { l / r } else { 0 },
                        _ => 0,
                    };
                    stack.push(MapperSignalValue::I32(res));
                }
            }
            TokenType::Func => {
                let func_idx = node.tok.int_value.unwrap() as usize;
                let entry = FUNCTION_TABLE.get(FUNCTIONS[func_idx]).unwrap();
                match entry.arity {
                    0 => {
                        stack.push(MapperSignalValue::F((entry.func)(0.0, 0.0)));
                    }
                    1 => {
                        let r = stack.pop().unwrap().as_f32().unwrap();
                        stack.push(MapperSignalValue::F((entry.func)(r, 0.0)));
                    }
                    2 => {
                        let r = stack.pop().unwrap().as_f32().unwrap();
                        let l = stack.pop().unwrap().as_f32().unwrap();
                        stack.push(MapperSignalValue::F((entry.func)(l, r)));
                    }
                    _ => {}
                }
            }
            _ => {}
        }
        curr = node.next.clone();
    }

    let result = stack[0];
    if mapper.history_size > 0 {
        let pos = mapper.history_pos as usize;
        if mapper.output_history.len() < pos + 1 {
            mapper.output_history.resize(pos + 1, MapperSignalValue::I32(0));
        }
        mapper.output_history[pos] = result;
    }
    result
}

fn printtoken(_t: &Token) {}
fn printexprnode(_s: &str, _list: &ExprNode) {}
fn printexpr(_s: &str, _list: &MapperExpr) {}
fn printstack(_stack: &stack_obj_t, _stack_size: i32) {}
