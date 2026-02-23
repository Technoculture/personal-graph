//! pg-cypher — OpenCypher query parser and executor.
//!
//! Supports a production-practical subset of the openCypher specification:
//!
//!   MATCH  (n:Label {k:v})-[:TYPE]->(m:Label) WHERE expr RETURN expr
//!   CREATE (n:Label {k:v})-[:TYPE {k:v}]->(m:Label {k:v})
//!   MATCH  … DELETE n
//!   MATCH  … SET n.prop = expr
//!   MATCH  … RETURN … ORDER BY expr [ASC|DESC] SKIP n LIMIT n
//!   MATCH  … RETURN DISTINCT …
//!   shortestPath((a)-[*]->(b))

pub mod ast;
pub mod executor;
pub mod lexer;
pub mod parser;

pub use executor::{CypherEngine, QueryResult, Row};
pub use parser::Parser;

use thiserror::Error;

pub type Result<T> = std::result::Result<T, CypherError>;

#[derive(Debug, Error)]
pub enum CypherError {
    #[error("lex error at position {pos}: {msg}")]
    Lex { pos: usize, msg: String },

    #[error("parse error: {0}")]
    Parse(String),

    #[error("execution error: {0}")]
    Exec(String),

    #[error("type error: {0}")]
    Type(String),

    #[error("graph error: {0}")]
    Graph(String),
}

impl From<pg_core::Error> for CypherError {
    fn from(e: pg_core::Error) -> Self {
        CypherError::Graph(e.to_string())
    }
}
