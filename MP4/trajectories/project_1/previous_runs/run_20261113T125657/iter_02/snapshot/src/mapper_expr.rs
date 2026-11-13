use std::f32::consts::PI;
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
/*
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
*/
fn minf(x: f32, y: f32) -> f32 {
    x.min(y)
}
fn maxf(x: f32, y: f32) -> f32 {
    x.max(y)
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
}
fn function_lookup(_s: &str) -> Option<&'static FunctionEntry> {
    None
}
fn expr_lex(_s: Vec<&str>) -> Vec<Token>{
    Vec::new()
}
pub struct ExprNode{
    pub tok: Token,
    pub is_float: i32,
    pub history_index: i32,
    pub vector_index: i32,
    pub next: Option<Arc<ExprNode>>,
}
pub struct MapperExpr{
    pub node: ExprNode,
    pub vector_size: i32,
    pub history_size: i32,
    pub history_pos: i32,
    pub input_history: Vec<MapperSignalValue>,
    pub output_history: Vec<MapperSignalValue>,
}
#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StateT {
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
enum StackObjT {
    State(StateT),
    Node(ExprNode),
}
impl Default for ExprNode {
    fn default() -> Self {
        Self::new()
    }
}

impl ExprNode{
    pub fn new() -> ExprNode{
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
    pub fn expr_free(&self){
        unimplemented!();
    }
}
fn printtoken(t: &Token){
    unimplemented!();
}
fn printexprnode(s: &str, list: &ExprNode){
    unimplemented!();
}
fn printexpr(s: &str, list: &MapperExpr){
    unimplemented!();
}
fn printstack(stack: &stack_obj_t, stack_size: i32){
    unimplemented!();
}
fn collapse_expr_to_left(plhs: &mut ExprNode, constant_folding: i32){
    unimplemented!();
}
pub fn mapper_expr_new_from_string(s: &str, 
                                input_is_float: i32,
                                output_is_float: i32,
                                vector_size: i32)-> MapperExpr{
    unimplemented!();
}
pub fn mapper_expr_evaluate(mapper: &mut MapperExpr, 
                         input: &MapperSignalValue) -> MapperSignalValue{
    unimplemented!();
}