#![forbid(unsafe_code)]

use std::f32::consts::PI;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum MapperSignalValue {
    F(f32),
    I32(i32),
}

impl MapperSignalValue {
    pub fn as_f32(&self) -> Option<f32> {
        match *self {
            MapperSignalValue::F(v) => Some(v),
            MapperSignalValue::I32(v) => Some(v as f32),
        }
    }
    pub fn as_i32(&self) -> Option<i32> {
        match *self {
            MapperSignalValue::F(v) => Some(v as i32),
            MapperSignalValue::I32(v) => Some(v),
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
    PI
}

#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExprFunc {
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
pub struct FunctionEntry {
    pub name: &'static str,
    pub arity: u32,
    pub func: ExprFunc,
}

lazy_static::lazy_static! {
    static ref FUNCTION_TABLE: Vec<FunctionEntry> = vec![
        FunctionEntry { name: "pow", arity: 2, func: ExprFunc::Pow },
        FunctionEntry { name: "sin", arity: 1, func: ExprFunc::Sin },
        FunctionEntry { name: "cos", arity: 1, func: ExprFunc::Cos },
        FunctionEntry { name: "tan", arity: 1, func: ExprFunc::Tan },
        FunctionEntry { name: "abs", arity: 1, func: ExprFunc::Abs },
        FunctionEntry { name: "sqrt", arity: 1, func: ExprFunc::Sqrt },
        FunctionEntry { name: "log", arity: 1, func: ExprFunc::Log },
        FunctionEntry { name: "log10", arity: 1, func: ExprFunc::Log10 },
        FunctionEntry { name: "exp", arity: 1, func: ExprFunc::Exp },
        FunctionEntry { name: "floor", arity: 1, func: ExprFunc::Floor },
        FunctionEntry { name: "round", arity: 1, func: ExprFunc::Round },
        FunctionEntry { name: "ceil", arity: 1, func: ExprFunc::Ceil },
        FunctionEntry { name: "asin", arity: 1, func: ExprFunc::Asin },
        FunctionEntry { name: "acos", arity: 1, func: ExprFunc::Acos },
        FunctionEntry { name: "atan", arity: 1, func: ExprFunc::Atan },
        FunctionEntry { name: "atan2", arity: 2, func: ExprFunc::Atan2 },
        FunctionEntry { name: "sinh", arity: 1, func: ExprFunc::Sinh },
        FunctionEntry { name: "cosh", arity: 1, func: ExprFunc::Cosh },
        FunctionEntry { name: "tanh", arity: 1, func: ExprFunc::Tanh },
        FunctionEntry { name: "logb", arity: 1, func: ExprFunc::Logb },
        FunctionEntry { name: "exp2", arity: 1, func: ExprFunc::Exp2 },
        FunctionEntry { name: "log2", arity: 1, func: ExprFunc::Log2 },
        FunctionEntry { name: "hypot", arity: 2, func: ExprFunc::Hypot },
        FunctionEntry { name: "cbrt", arity: 1, func: ExprFunc::Cbrt },
        FunctionEntry { name: "trunc", arity: 1, func: ExprFunc::Trunc },
        FunctionEntry { name: "min", arity: 2, func: ExprFunc::Min },
        FunctionEntry { name: "max", arity: 2, func: ExprFunc::Max },
        FunctionEntry { name: "pi", arity: 0, func: ExprFunc::Pi },
    ];
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TokenType {
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
    pub value: f32,
    pub int_value: i32,
    pub var: char,
    pub op: char,
    pub func: ExprFunc,
}

impl Token {
    pub fn new_float(f: f32) -> Self {
        Token {
            token_type: TokenType::Float,
            value: f,
            int_value: 0,
            var: '\0',
            op: '\0',
            func: ExprFunc::Unknown,
        }
    }
    pub fn new_int(i: i32) -> Self {
        Token {
            token_type: TokenType::Int,
            value: 0.0,
            int_value: i,
            var: '\0',
            op: '\0',
            func: ExprFunc::Unknown,
        }
    }
    pub fn new_op(op: char) -> Self {
        Token {
            token_type: TokenType::Op,
            value: 0.0,
            int_value: 0,
            var: '\0',
            op,
            func: ExprFunc::Unknown,
        }
    }
    pub fn new_var(var: char) -> Self {
        Token {
            token_type: TokenType::Var,
            value: 0.0,
            int_value: 0,
            var,
            op: '\0',
            func: ExprFunc::Unknown,
        }
    }
    pub fn new_func(func: ExprFunc) -> Self {
        Token {
            token_type: TokenType::Func,
            value: 0.0,
            int_value: 0,
            var: '\0',
            op: '\0',
            func,
        }
    }
    pub fn new_simple(token_type: TokenType) -> Self {
        Token {
            token_type,
            value: 0.0,
            int_value: 0,
            var: '\0',
            op: '\0',
            func: ExprFunc::Unknown,
        }
    }
}

fn function_lookup(s: &str, len: usize) -> ExprFunc {
    if len > s.len() {
        return ExprFunc::Unknown;
    }
    let sub = &s[..len];
    for (i, entry) in FUNCTION_TABLE.iter().enumerate() {
        if entry.name == sub {
            return match i {
                0 => ExprFunc::Pow,
                1 => ExprFunc::Sin,
                2 => ExprFunc::Cos,
                3 => ExprFunc::Tan,
                4 => ExprFunc::Abs,
                5 => ExprFunc::Sqrt,
                6 => ExprFunc::Log,
                7 => ExprFunc::Log10,
                8 => ExprFunc::Exp,
                9 => ExprFunc::Floor,
                10 => ExprFunc::Round,
                11 => ExprFunc::Ceil,
                12 => ExprFunc::Asin,
                13 => ExprFunc::Acos,
                14 => ExprFunc::Atan,
                15 => ExprFunc::Atan2,
                16 => ExprFunc::Sinh,
                17 => ExprFunc::Cosh,
                18 => ExprFunc::Tanh,
                19 => ExprFunc::Logb,
                20 => ExprFunc::Exp2,
                21 => ExprFunc::Log2,
                22 => ExprFunc::Hypot,
                23 => ExprFunc::Cbrt,
                24 => ExprFunc::Trunc,
                25 => ExprFunc::Min,
                26 => ExprFunc::Max,
                27 => ExprFunc::Pi,
                _ => ExprFunc::Unknown,
            };
        }
    }
    ExprFunc::Unknown
}

struct Lexer;

impl Lexer {
    fn new() -> Self {
        Lexer
    }

    fn lex(&mut self, tok: &mut Token, str_ptr: &mut &str) -> i32 {
        let c = match str_ptr.chars().next() {
            Some(ch) => ch,
            None => {
                tok.token_type = TokenType::End;
                return 0;
            }
        };

        if c == '\0' {
            tok.token_type = TokenType::End;
            return 0;
        }

        let mut integer_found = 0;
        let mut n = 0i32;

        if c.is_ascii_digit() {
            let mut val = 0i32;
            let mut cur_rem = *str_ptr;
            while let Some(ch) = cur_rem.chars().next() {
                if ch.is_ascii_digit() {
                    val = val * 10 + (ch as i32 - '0' as i32);
                    cur_rem = &cur_rem[ch.len_utf8()..];
                } else {
                    break;
                }
            }
            *str_ptr = cur_rem;
            n = val;
            integer_found = 1;

            if let Some(ch) = str_ptr.chars().next() {
                let next_c = ch;
                if next_c != '.' {
                    tok.token_type = TokenType::Int;
                    tok.int_value = n;
                    return 0;
                }
            } else {
                tok.token_type = TokenType::Int;
                tok.int_value = n;
                return 0;
            }
        }

        let c = match str_ptr.chars().next() {
            Some(ch) => ch,
            None => {
                tok.token_type = TokenType::End;
                return 0;
            }
        };

        match c {
            '.' => {
                let s_dot = *str_ptr;
                *str_ptr = &str_ptr[c.len_utf8()..];
                if str_ptr.is_empty() {
                    tok.token_type = TokenType::Float;
                    tok.value = n as f32;
                    return 0;
                }
                let next_c = str_ptr.chars().next().unwrap();
                if !next_c.is_ascii_digit() && integer_found == 1 {
                    tok.token_type = TokenType::Float;
                    tok.value = n as f32;
                    return 0;
                }
                if !next_c.is_ascii_digit() {
                    // break
                } else {
                    let mut cur_rem = *str_ptr;
                    while let Some(ch) = cur_rem.chars().next() {
                        if ch.is_ascii_digit() {
                            cur_rem = &cur_rem[ch.len_utf8()..];
                        } else {
                            break;
                        }
                    }
                    let float_str = &s_dot[..s_dot.len() - cur_rem.len()];
                    let f_val = float_str.parse::<f32>().unwrap_or(0.0);
                    *str_ptr = cur_rem;
                    tok.token_type = TokenType::Float;
                    tok.value = n as f32 + f_val;
                    return 0;
                }
            }
            '+' | '-' | '/' | '*' | '=' => {
                tok.token_type = TokenType::Op;
                tok.op = c;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            '(' => {
                tok.token_type = TokenType::OpenParen;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            ')' => {
                tok.token_type = TokenType::CloseParen;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            'x' | 'y' => {
                tok.token_type = TokenType::Var;
                tok.var = c;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            '[' => {
                tok.token_type = TokenType::OpenSquare;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            ']' => {
                tok.token_type = TokenType::CloseSquare;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            '{' => {
                tok.token_type = TokenType::OpenCurly;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            '}' => {
                tok.token_type = TokenType::CloseCurly;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            ' ' | '\t' | '\r' | '\n' => {
                *str_ptr = &str_ptr[c.len_utf8()..];
                return self.lex(tok, str_ptr);
            }
            ',' => {
                tok.token_type = TokenType::Comma;
                *str_ptr = &str_ptr[c.len_utf8()..];
                return 0;
            }
            _ => {
                if !c.is_ascii_alphabetic() {
                    println!("unknown character '{}' in lexer", c);
                    *str_ptr = &str_ptr[c.len_utf8()..];
                    return 1;
                }
                let s_func = *str_ptr;
                let mut cur_rem = *str_ptr;
                while let Some(ch) = cur_rem.chars().next() {
                    if ch.is_ascii_alphabetic() || ch.is_ascii_digit() {
                        cur_rem = &cur_rem[ch.len_utf8()..];
                    } else {
                        break;
                    }
                }
                let func_str_len = s_func.len() - cur_rem.len();
                tok.token_type = TokenType::Func;
                tok.func = function_lookup(s_func, func_str_len);
                *str_ptr = cur_rem;
                return 0;
            }
        }
        1
    }
}

#[derive(Debug, Clone)]
pub struct ExprNode {
    pub tok: Token,
    pub is_float: i32,
    pub history_index: i32,
    pub vector_index: i32,
    pub next: Option<Box<ExprNode>>,
}

pub struct MapperExpr {
    pub node: Option<Box<ExprNode>>,
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
#[derive(Debug)]
enum stack_obj_t {
    State(state_t),
    Node(Box<ExprNode>),
}

impl ExprNode {
    pub fn new(tok: &Token, is_float: i32) -> Box<ExprNode> {
        Box::new(ExprNode {
            tok: *tok,
            is_float,
            history_index: 0,
            vector_index: 0,
            next: None,
        })
    }
    pub fn expr_free(mut e: Option<Box<ExprNode>>) {
        while let Some(mut node) = e {
            e = node.next.take();
        }
    }
}

fn collapse_expr_to_left(plhs: &mut Box<ExprNode>, rhs: Box<ExprNode>, constant_folding: i32, vector_size: i32, _input_is_float: i32, _output_is_float: i32) {
    let mut refvar = 0;

    let mut rhs_last_is_float = rhs.is_float;
    let mut r_ref = &rhs;
    if r_ref.tok.token_type == TokenType::Var {
        refvar = 1;
    }
    while let Some(ref next_node) = r_ref.next {
        if next_node.tok.token_type == TokenType::Var {
            refvar = 1;
        }
        r_ref = next_node;
        rhs_last_is_float = r_ref.is_float;
    }

    let plhs_is_float = plhs.is_float;
    let mut last_is_float = plhs_is_float;
    {
        let mut curr_ptr = &**plhs;
        if curr_ptr.tok.token_type == TokenType::Var {
            refvar = 1;
        }
        while let Some(ref next_node) = curr_ptr.next {
            if next_node.tok.token_type == TokenType::Var {
                refvar = 1;
            }
            curr_ptr = next_node;
            last_is_float = curr_ptr.is_float;
        }
    }

    let coerce = Token::new_simple(TokenType::ToFloat);
    let is_float = last_is_float | rhs_last_is_float;

    let mut new_rhs = rhs;
    if last_is_float != 0 && rhs_last_is_float == 0 {
        let mut curr = &mut new_rhs;
        while curr.next.is_some() {
            curr = curr.next.as_mut().unwrap();
        }
        curr.next = Some(ExprNode::new(&coerce, 1));
    } else if last_is_float == 0 && rhs_last_is_float != 0 {
        let mut e_node = ExprNode::new(&coerce, 1);
        e_node.next = plhs.next.take();
        plhs.next = Some(e_node);
        plhs.next.as_mut().unwrap().is_float = 1;
    }

    let mut last_ptr = plhs;
    while let Some(ref mut next_node) = last_ptr.next {
        last_ptr = next_node;
    }
    last_ptr.next = Some(new_rhs);

    if constant_folding != 0 && refvar == 0 {
        let dummy_node = plhs.clone();
        let dummy_expr = MapperExpr {
            node: Some(dummy_node),
            vector_size,
            history_size: 1,
            history_pos: 0,
            input_history: vec![],
            output_history: vec![],
        };
        let mut v = MapperSignalValue::I32(0);
        mapper_expr_evaluate_internal(&dummy_expr, None, &mut v);

        let next_take = plhs.next.take();
        ExprNode::expr_free(next_take);
        plhs.is_float = is_float;
        if is_float != 0 {
            plhs.tok = Token::new_float(v.as_f32().unwrap());
        } else {
            plhs.tok = Token::new_int(v.as_i32().unwrap());
        }
    }
}

fn mapper_expr_evaluate_internal(
    expr: &MapperExpr,
    input_vector: Option<&MapperSignalValue>,
    output_val: &mut MapperSignalValue,
) -> i32 {
    let mut stack: Vec<MapperSignalValue> = Vec::with_capacity(STACK_SIZE);
    let mut node_opt = expr.node.as_ref();

    while let Some(node) = node_opt {
        match node.tok.token_type {
            TokenType::Int => {
                stack.push(MapperSignalValue::I32(node.tok.int_value));
            }
            TokenType::Float => {
                stack.push(MapperSignalValue::F(node.tok.value));
            }
            TokenType::Var => {
                die_unless!(input_vector.is_some(), "Input required but not provided for expression evaluation.\n");
                let idx = ((node.history_index + expr.history_pos + expr.history_size) % expr.history_size) as usize;
                match node.tok.var {
                    'x' => {
                        let flat_idx = idx * expr.vector_size as usize + node.vector_index as usize;
                        stack.push(expr.input_history[flat_idx]);
                    }
                    'y' => {
                        stack.push(expr.output_history[idx]);
                    }
                    _ => return 1,
                }
            }
            TokenType::ToFloat => {
                let top = stack.pop().unwrap();
                stack.push(MapperSignalValue::F(top.as_f32().unwrap()));
            }
            TokenType::ToInt32 => {
                let top = stack.pop().unwrap();
                stack.push(MapperSignalValue::I32(top.as_i32().unwrap()));
            }
            TokenType::Op => {
                let right = stack.pop().unwrap();
                let left = stack.pop().unwrap();
                if node.is_float != 0 {
                    let lf = left.as_f32().unwrap();
                    let rf = right.as_f32().unwrap();
                    let res = match node.tok.op {
                        '+' => lf + rf,
                        '-' => lf - rf,
                        '*' => lf * rf,
                        '/' => lf / rf,
                        _ => return 1,
                    };
                    stack.push(MapperSignalValue::F(res));
                } else {
                    let li = left.as_i32().unwrap();
                    let ri = right.as_i32().unwrap();
                    let res = match node.tok.op {
                        '+' => li + ri,
                        '-' => li - ri,
                        '*' => li * ri,
                        '/' => li / ri,
                        _ => return 1,
                    };
                    stack.push(MapperSignalValue::I32(res));
                }
            }
            TokenType::Func => {
                let func = node.tok.func;
                let entry = FUNCTION_TABLE.iter().find(|e| e.func == func).unwrap();
                match entry.arity {
                    0 => {
                        let val = match func {
                            ExprFunc::Pi => pif(),
                            _ => 0.0,
                        };
                        stack.push(MapperSignalValue::F(val));
                    }
                    1 => {
                        let right = stack.pop().unwrap().as_f32().unwrap();
                        let res = match func {
                            ExprFunc::Sin => right.sin(),
                            ExprFunc::Cos => right.cos(),
                            ExprFunc::Tan => right.tan(),
                            ExprFunc::Abs => right.abs(),
                            ExprFunc::Sqrt => right.sqrt(),
                            ExprFunc::Log => right.ln(),
                            ExprFunc::Log10 => right.log10(),
                            ExprFunc::Exp => right.exp(),
                            ExprFunc::Floor => right.floor(),
                            ExprFunc::Round => right.round(),
                            ExprFunc::Ceil => right.ceil(),
                            ExprFunc::Asin => right.asin(),
                            ExprFunc::Acos => right.acos(),
                            ExprFunc::Atan => right.atan(),
                            ExprFunc::Sinh => right.sinh(),
                            ExprFunc::Cosh => right.cosh(),
                            ExprFunc::Tanh => right.tanh(),
                            ExprFunc::Logb => right.log2(),
                            ExprFunc::Exp2 => right.exp2(),
                            ExprFunc::Log2 => right.log2(),
                            ExprFunc::Cbrt => right.cbrt(),
                            ExprFunc::Trunc => right.trunc(),
                            _ => right,
                        };
                        stack.push(MapperSignalValue::F(res));
                    }
                    2 => {
                        let right = stack.pop().unwrap().as_f32().unwrap();
                        let left = stack.pop().unwrap().as_f32().unwrap();
                        let res = match func {
                            ExprFunc::Pow => left.powf(right),
                            ExprFunc::Atan2 => left.atan2(right),
                            ExprFunc::Hypot => left.hypot(right),
                            ExprFunc::Min => minf(left, right),
                            ExprFunc::Max => maxf(left, right),
                            _ => left,
                        };
                        stack.push(MapperSignalValue::F(res));
                    }
                    _ => return 1,
                }
            }
            _ => return 1,
        }
        node_opt = node.next.as_ref();
    }

    if let Some(val) = stack.pop() {
        *output_val = val;
    }
    0
}

pub fn mapper_expr_new_from_string(
    str_val: &str,
    input_is_float: i32,
    output_is_float: i32,
    vector_size: i32,
) -> MapperExpr {
    let mut s = str_val;
    let mut stack: Vec<stack_obj_t> = Vec::with_capacity(STACK_SIZE);
    let mut result: Option<Box<ExprNode>> = None;
    let mut error_message: Option<&str> = None;

    let mut tok = Token::new_simple(TokenType::End);
    let mut next_token = 1;
    let mut var_allowed = 1;
    let mut oldest_samps = 0.0f32;

    stack.push(stack_obj_t::State(state_t::EXPR));
    stack.push(stack_obj_t::State(state_t::YEQUAL_EQ));
    stack.push(stack_obj_t::State(state_t::YEQUAL_Y));

    let mut lexer = Lexer::new();

    while !stack.is_empty() {
        let top = stack.len() - 1;
        if next_token != 0 && lexer.lex(&mut tok, &mut s) != 0 {
            error_message = Some("Error in lexical analysis.");
            break;
        }
        next_token = 0;

        let is_node = matches!(stack[top], stack_obj_t::Node(_));
        if is_node {
            if top == 0 {
                if let stack_obj_t::Node(node) = stack.pop().unwrap() {
                    result = Some(node);
                    break;
                }
            }
            let prev_is_state = matches!(stack[top - 1], stack_obj_t::State(_));
            if prev_is_state {
                if top >= 2 && matches!(stack[top - 2], stack_obj_t::Node(_)) {
                    let state_val = match stack[top - 1] {
                        stack_obj_t::State(st) => st,
                        _ => unreachable!(),
                    };
                    if state_val == state_t::EXPR_RIGHT
                        || state_val == state_t::TERM_RIGHT
                        || state_val == state_t::CLOSE_PAREN
                    {
                        let rhs = match stack.pop().unwrap() {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        stack.pop();
                        let lhs_node = match &mut stack[top - 2] {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        collapse_expr_to_left(lhs_node, rhs, 1, vector_size, input_is_float, output_is_float);
                    } else if state_val == state_t::CLOSE_HISTINDEX {
                        let top_node = match stack.pop().unwrap() {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        stack.pop();
                        let var_node = match &mut stack[top - 2] {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        die_unless!(var_node.tok.token_type == TokenType::Var, "expected VAR two-down on the stack.\n");
                        die_unless!(top_node.next.is_none() && (top_node.tok.token_type == TokenType::Int || top_node.tok.token_type == TokenType::Float), "expected lonely INT or FLOAT expression on the stack.\n");
                        if top_node.tok.token_type == TokenType::Float {
                            var_node.history_index = top_node.tok.value as i32;
                        } else {
                            var_node.history_index = top_node.tok.int_value;
                        }
                        if oldest_samps > var_node.history_index as f32 {
                            oldest_samps = var_node.history_index as f32;
                        }
                    } else if state_val == state_t::CLOSE_VECTINDEX {
                        let top_node = match stack.pop().unwrap() {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        stack.pop();
                        let var_node = match &mut stack[top - 2] {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        die_unless!(var_node.tok.token_type == TokenType::Var, "expected VAR two-down on the stack.\n");
                        die_unless!(top_node.next.is_none() && (top_node.tok.token_type == TokenType::Int || top_node.tok.token_type == TokenType::Float), "expected lonely INT or FLOAT expression on the stack.\n");
                        if top_node.tok.token_type == TokenType::Float {
                            var_node.vector_index = top_node.tok.value as i32;
                        } else {
                            var_node.vector_index = top_node.tok.int_value;
                        }
                        if var_node.vector_index > 0 {
                            error_message = Some("Vector indexing not yet implemented.");
                            break;
                        }
                        if var_node.vector_index < 0 || var_node.vector_index >= vector_size {
                            error_message = Some("Vector index outside input size.");
                            break;
                        }
                    } else {
                        let tmp = stack.remove(top - 1);
                        stack.push(tmp);
                    }
                } else {
                    let tmp = stack.remove(top - 1);
                    stack.push(tmp);
                }
            }
            continue;
        }

        let state = match stack.pop().unwrap() {
            stack_obj_t::State(st) => st,
            _ => unreachable!(),
        };

        match state {
            state_t::YEQUAL_Y => {
                if tok.token_type == TokenType::Var && tok.var == 'y' {
                    // popped
                } else {
                    error_message = Some("Error in y= prefix.");
                    break;
                }
                next_token = 1;
            }
            state_t::YEQUAL_EQ => {
                if tok.token_type == TokenType::Op && tok.op == '=' {
                    // popped
                } else {
                    error_message = Some("Error in y= prefix.");
                    break;
                }
                next_token = 1;
            }
            state_t::EXPR => {
                stack.push(stack_obj_t::State(state_t::EXPR_RIGHT));
                stack.push(stack_obj_t::State(state_t::TERM));
            }
            state_t::EXPR_RIGHT => {
                if tok.token_type == TokenType::Op {
                    if tok.op == '+' || tok.op == '-' {
                        if let stack_obj_t::Node(node) = stack.last_mut().unwrap() {
                            let mut e = node;
                            while e.next.is_some() {
                                e = e.next.as_mut().unwrap();
                            }
                            let mut new_n = ExprNode::new(&tok, 0);
                            new_n.is_float = e.is_float;
                            e.next = Some(new_n);
                        }
                        stack.push(stack_obj_t::State(state_t::EXPR));
                        next_token = 1;
                    }
                }
            }
            state_t::TERM => {
                stack.push(stack_obj_t::State(state_t::TERM_RIGHT));
                stack.push(stack_obj_t::State(state_t::VALUE));
            }
            state_t::TERM_RIGHT => {
                if tok.token_type == TokenType::Op {
                    if tok.op == '*' || tok.op == '/' {
                        if let stack_obj_t::Node(node) = stack.last_mut().unwrap() {
                            let mut e = node;
                            while e.next.is_some() {
                                e = e.next.as_mut().unwrap();
                            }
                            let mut new_n = ExprNode::new(&tok, 0);
                            new_n.is_float = e.is_float;
                            e.next = Some(new_n);
                        }
                        stack.push(stack_obj_t::State(state_t::TERM));
                        next_token = 1;
                    }
                }
            }
            state_t::VALUE => {
                if tok.token_type == TokenType::Int {
                    stack.push(stack_obj_t::Node(ExprNode::new(&tok, 0)));
                    next_token = 1;
                } else if tok.token_type == TokenType::Float {
                    stack.push(stack_obj_t::Node(ExprNode::new(&tok, 1)));
                    next_token = 1;
                } else if tok.token_type == TokenType::Var {
                    if var_allowed != 0 {
                        stack.push(stack_obj_t::Node(ExprNode::new(&tok, input_is_float)));
                        stack.push(stack_obj_t::State(state_t::VAR_RIGHT));
                        next_token = 1;
                    } else {
                        error_message = Some("Unexpected variable reference.");
                        break;
                    }
                } else if tok.token_type == TokenType::OpenParen {
                    stack.push(stack_obj_t::State(state_t::CLOSE_PAREN));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = 1;
                } else if tok.token_type == TokenType::Func {
                    if tok.func == ExprFunc::Unknown {
                        error_message = Some("Unknown function.");
                        break;
                    } else {
                        stack.push(stack_obj_t::Node(ExprNode::new(&tok, 1)));
                        let entry = FUNCTION_TABLE.iter().find(|e| e.func == tok.func).unwrap();
                        let arity = entry.arity;
                        if arity > 0 {
                            stack.push(stack_obj_t::State(state_t::CLOSE_PAREN));
                            stack.push(stack_obj_t::State(state_t::EXPR));
                            for _ in 1..arity {
                                stack.push(stack_obj_t::State(state_t::COMMA));
                                stack.push(stack_obj_t::State(state_t::EXPR));
                            }
                            stack.push(stack_obj_t::State(state_t::OPEN_PAREN));
                        }
                        next_token = 1;
                    }
                } else if tok.token_type == TokenType::Op && tok.op == '-' {
                    stack.push(stack_obj_t::State(state_t::NEGATE));
                    stack.push(stack_obj_t::State(state_t::VALUE));
                    next_token = 1;
                } else {
                    error_message = Some("Expected value.");
                    break;
                }
            }
            state_t::NEGATE => {
                if let Some(stack_obj_t::Node(node)) = stack.last_mut() {
                    let t_zero = Token::new_int(0);
                    let mut e = ExprNode::new(&t_zero, 0);
                    let t_sub = Token::new_op('-');
                    e.next = Some(ExprNode::new(&t_sub, 0));
                    collapse_expr_to_left(&mut e, node.clone(), 1, vector_size, input_is_float, output_is_float);
                    *node = e;
                } else {
                    error_message = Some("Expected to negate an expression.");
                    break;
                }
            }
            state_t::VAR_RIGHT => {
                if tok.token_type == TokenType::OpenSquare {
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                } else if tok.token_type == TokenType::OpenCurly {
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                }
            }
            state_t::VAR_VECTINDEX => {
                if tok.token_type == TokenType::OpenSquare {
                    var_allowed = 0;
                    stack.push(stack_obj_t::State(state_t::CLOSE_VECTINDEX));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = 1;
                }
            }
            state_t::VAR_HISTINDEX => {
                if tok.token_type == TokenType::OpenCurly {
                    var_allowed = 0;
                    stack.push(stack_obj_t::State(state_t::CLOSE_HISTINDEX));
                    stack.push(stack_obj_t::State(state_t::EXPR));
                    next_token = 1;
                }
            }
            state_t::CLOSE_VECTINDEX => {
                if tok.token_type == TokenType::CloseSquare {
                    var_allowed = 1;
                    stack.push(stack_obj_t::State(state_t::VAR_HISTINDEX));
                    next_token = 1;
                } else {
                    error_message = Some("Expected ']'.");
                    break;
                }
            }
            state_t::CLOSE_HISTINDEX => {
                if tok.token_type == TokenType::CloseCurly {
                    var_allowed = 1;
                    stack.push(stack_obj_t::State(state_t::VAR_VECTINDEX));
                    next_token = 1;
                } else {
                    error_message = Some("Expected '}'.");
                    break;
                }
            }
            state_t::CLOSE_PAREN => {
                if tok.token_type == TokenType::CloseParen {
                    next_token = 1;
                } else {
                    error_message = Some("Expected ')'.");
                    break;
                }
            }
            state_t::COMMA => {
                if tok.token_type == TokenType::Comma {
                    let mut i = (stack.len() as i32) - 1;
                    while i >= 0 && !matches!(stack[i as usize], stack_obj_t::Node(_)) {
                        i -= 1;
                    }
                    if i >= 0 {
                        let rhs = match stack.pop().unwrap() {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        let lhs_node = match &mut stack[i as usize] {
                            stack_obj_t::Node(n) => n,
                            _ => unreachable!(),
                        };
                        collapse_expr_to_left(lhs_node, rhs, 0, vector_size, input_is_float, output_is_float);
                    }
                    next_token = 1;
                } else {
                    error_message = Some("Expected ','.");
                    break;
                }
            }
            state_t::OPEN_PAREN => {
                if tok.token_type == TokenType::OpenParen {
                    next_token = 1;
                } else {
                    error_message = Some("Expected '('.");
                    break;
                }
            }
            state_t::END => {
                if tok.token_type == TokenType::End {
                    // done
                } else {
                    error_message = Some("Expected END.");
                    break;
                }
            }
        }
    }

    if result.is_none() {
        if let Some(msg) = error_message {
            println!("{}", msg);
        }
        return MapperExpr {
            node: None,
            vector_size,
            history_size: 1,
            history_pos: -1,
            input_history: vec![],
            output_history: vec![],
        };
    }

    if oldest_samps < -100.0 {
        return MapperExpr {
            node: None,
            vector_size,
            history_size: 1,
            history_pos: -1,
            input_history: vec![],
            output_history: vec![],
        };
    }

    let mut res_node = result.unwrap();
    let mut e_last = &mut res_node;
    while e_last.next.is_some() {
        e_last = e_last.next.as_mut().unwrap();
    }

    if e_last.is_float != 0 && output_is_float == 0 {
        let coerce = Token::new_simple(TokenType::ToInt32);
        e_last.next = Some(ExprNode::new(&coerce, 0));
        e_last.next.as_mut().unwrap().is_float = 0;
    } else if e_last.is_float == 0 && output_is_float != 0 {
        let coerce = Token::new_simple(TokenType::ToFloat);
        e_last.next = Some(ExprNode::new(&coerce, 0));
        e_last.next.as_mut().unwrap().is_float = 1;
    }

    let history_size = (-oldest_samps).ceil() as i32 + 1;
    let input_history = vec![MapperSignalValue::I32(0); (vector_size * history_size) as usize];
    let output_history = vec![MapperSignalValue::I32(0); history_size as usize];

    MapperExpr {
        node: Some(res_node),
        vector_size,
        history_size,
        history_pos: -1,
        input_history,
        output_history,
    }
}

pub fn mapper_expr_evaluate<'a>(
    expr: &mut MapperExpr,
    input: &'a MapperSignalValue,
) -> MapperSignalValue {
    if expr.node.is_none() {
        return MapperSignalValue::I32(0);
    }

    expr.history_pos = (expr.history_pos + 1) % expr.history_size;
    let hist_offset = (expr.history_pos * expr.vector_size) as usize;
    for i in 0..expr.vector_size as usize {
        expr.input_history[hist_offset + i] = *input;
    }

    let mut out_val = MapperSignalValue::I32(0);
    mapper_expr_evaluate_internal(expr, Some(input), &mut out_val);

    expr.output_history[expr.history_pos as usize] = out_val;
    out_val
}
