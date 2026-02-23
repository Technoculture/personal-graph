//! Cypher AST — typed representation of a parsed query.

use std::collections::BTreeMap;

// ── Top level ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct Query {
    pub clauses: Vec<Clause>,
}

#[derive(Debug, Clone)]
pub enum Clause {
    Match(MatchClause),
    OptionalMatch(MatchClause),
    Create(CreateClause),
    Merge(CreateClause),
    Delete(DeleteClause),
    DetachDelete(DeleteClause),
    Set(SetClause),
    Remove(RemoveClause),
    Return(ReturnClause),
    With(WithClause),
    Unwind(UnwindClause),
}

// ── MATCH ────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct MatchClause {
    pub patterns: Vec<Pattern>,
    pub where_expr: Option<Expr>,
}

/// A graph pattern: a linear chain of alternating node and edge patterns.
/// (n1)-[r1]->(n2)-[r2]-(n3) etc.
#[derive(Debug, Clone)]
pub struct Pattern {
    pub start: NodePattern,
    pub hops: Vec<(EdgePattern, NodePattern)>,
    /// variable capturing entire path (used by shortestPath)
    pub path_var: Option<String>,
}

#[derive(Debug, Clone)]
pub struct NodePattern {
    pub var: Option<String>,
    pub labels: Vec<String>,
    pub props: PropMap,
}

#[derive(Debug, Clone)]
pub struct EdgePattern {
    pub var: Option<String>,
    pub types: Vec<String>,
    pub props: PropMap,
    pub direction: Direction,
    /// variable hop depth: None = 1, Some((min, max))
    pub hops: HopSpec,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Outgoing,  // -[r]->
    Incoming,  // <-[r]-
    Either,    // -[r]-
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HopSpec {
    One,                         // default  -[r]->
    Variable(Option<u32>, Option<u32>), // [*], [*2], [*2..5]
}

/// Property literal map: {key: Expr}
pub type PropMap = BTreeMap<String, Expr>;

// ── CREATE / MERGE ───────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct CreateClause {
    pub patterns: Vec<Pattern>,
}

// ── DELETE ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct DeleteClause {
    pub exprs: Vec<Expr>,
}

// ── SET ──────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct SetClause {
    pub items: Vec<SetItem>,
}

#[derive(Debug, Clone)]
pub enum SetItem {
    /// n.prop = expr
    Property { var: String, key: String, value: Expr },
    /// n = {map}
    Labels { var: String, labels: Vec<String> },
}

// ── REMOVE ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct RemoveClause {
    pub items: Vec<RemoveItem>,
}

#[derive(Debug, Clone)]
pub enum RemoveItem {
    Property { var: String, key: String },
    Label    { var: String, label: String },
}

// ── RETURN / WITH ────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ReturnClause {
    pub distinct: bool,
    pub items: Vec<ReturnItem>,
    pub order_by: Vec<OrderItem>,
    pub skip: Option<Expr>,
    pub limit: Option<Expr>,
}

#[derive(Debug, Clone)]
pub struct WithClause {
    pub items: Vec<ReturnItem>,
    pub where_expr: Option<Expr>,
    pub order_by: Vec<OrderItem>,
    pub skip: Option<Expr>,
    pub limit: Option<Expr>,
}

#[derive(Debug, Clone)]
pub struct ReturnItem {
    pub expr: Expr,
    pub alias: Option<String>,
}

#[derive(Debug, Clone)]
pub struct OrderItem {
    pub expr: Expr,
    pub descending: bool,
}

// ── UNWIND ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct UnwindClause {
    pub expr: Expr,
    pub var: String,
}

// ── Expressions ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    /// Bare variable reference: `n`
    Var(String),
    /// Property access: `n.name`
    Prop(String, String),
    /// Integer literal
    Int(i64),
    /// Float literal
    Float(f64),
    /// String literal
    Str(String),
    /// Boolean
    Bool(bool),
    /// NULL
    Null,
    /// List literal: [1, 2, 3]
    List(Vec<Expr>),
    /// Map literal: {a: 1, b: "x"}
    Map(BTreeMap<String, Expr>),
    /// Binary operator
    BinOp(BinOp, Box<Expr>, Box<Expr>),
    /// Unary NOT
    Not(Box<Expr>),
    /// IS NULL / IS NOT NULL
    IsNull(Box<Expr>, bool),
    /// x IN list
    In(Box<Expr>, Box<Expr>),
    /// string CONTAINS / STARTS WITH / ENDS WITH
    StringOp(StringOp, Box<Expr>, Box<Expr>),
    /// Function call: count(n), id(n), type(r), labels(n), …
    Call(String, Vec<Expr>),
    /// CASE WHEN cond THEN val … ELSE val END
    Case { input: Option<Box<Expr>>, branches: Vec<(Expr, Expr)>, default: Option<Box<Expr>> },
    /// `*` in RETURN *
    Star,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BinOp {
    And, Or, Xor,
    Eq, Neq, Lt, Gt, Lte, Gte,
    Add, Sub, Mul, Div, Mod, Pow,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StringOp { Contains, StartsWith, EndsWith }
