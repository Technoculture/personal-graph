//! pg-graph: High-level graph engine for personal-graph.
//!
//! Combines the storage engine and vector index into a unified API
//! with graph traversal, pattern matching, and similarity search.

pub mod engine;
pub mod traverse;

pub use engine::PersonalGraph;
