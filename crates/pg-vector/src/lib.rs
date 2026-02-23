//! pg-vector: HNSW vector index for personal-graph.
//!
//! A from-scratch implementation of Hierarchical Navigable Small World graphs
//! for approximate nearest neighbor search, with optimized distance metrics.

pub mod distance;
pub mod hnsw;

pub use hnsw::HnswIndex;
