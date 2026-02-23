//! pg-core: Core types and traits for personal-graph.
//!
//! This crate defines the fundamental data model (nodes, edges, properties),
//! storage traits, and error types that all other crates depend on.

pub mod error;
pub mod graph;
pub mod id;
pub mod mvcc;
pub mod property;
pub mod traits;

pub use error::{Error, Result};
pub use graph::{Edge, EdgeData, Node, NodeData};
pub use id::NodeId;
pub use property::{Property, PropertyMap};
