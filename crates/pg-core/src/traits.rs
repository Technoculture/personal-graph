use crate::error::Result;
use crate::graph::{Edge, EdgeData, GraphBatch, Node, NodeData};
use crate::id::NodeId;

/// Core storage engine trait.
///
/// Implementations own the physical representation of the graph:
/// page layout, buffer management, WAL, indexes — everything.
pub trait GraphStorage: Send + Sync {
    // --- Node operations ---

    fn insert_node(&mut self, id: NodeId, data: &NodeData) -> Result<()>;

    fn get_node(&self, id: NodeId) -> Result<Option<Node>>;

    fn update_node(&mut self, id: NodeId, data: &NodeData) -> Result<()>;

    fn delete_node(&mut self, id: NodeId) -> Result<()>;

    // --- Edge operations ---

    fn insert_edge(&mut self, source: NodeId, target: NodeId, data: &EdgeData) -> Result<()>;

    fn get_edge(&self, source: NodeId, target: NodeId) -> Result<Option<Edge>>;

    fn delete_edge(&mut self, source: NodeId, target: NodeId) -> Result<()>;

    // --- Adjacency queries ---

    /// All edges originating from `source`.
    fn out_edges(&self, source: NodeId) -> Result<Vec<Edge>>;

    /// All edges pointing to `target`.
    fn in_edges(&self, target: NodeId) -> Result<Vec<Edge>>;

    /// All neighbor node IDs reachable from `source` in one hop.
    fn neighbors(&self, source: NodeId) -> Result<Vec<NodeId>>;

    // --- Bulk operations ---

    fn insert_batch(&mut self, batch: &GraphBatch) -> Result<()> {
        for node in &batch.nodes {
            self.insert_node(node.id, &node.data)?;
        }
        for edge in &batch.edges {
            self.insert_edge(edge.source, edge.target, &edge.data)?;
        }
        Ok(())
    }

    // --- Scan ---

    /// Return all nodes whose label matches exactly.
    fn nodes_by_label(&self, label: &str) -> Result<Vec<Node>>;

    /// Return total node count.
    fn node_count(&self) -> Result<usize>;

    /// Return total edge count.
    fn edge_count(&self) -> Result<usize>;
}

/// Vector index trait for similarity search.
pub trait VectorIndex: Send + Sync {
    /// Insert a vector associated with a node.
    fn insert(&mut self, id: NodeId, embedding: &[f32]) -> Result<()>;

    /// Remove a vector.
    fn remove(&mut self, id: NodeId) -> Result<bool>;

    /// Find the `k` nearest neighbors to `query`.
    fn search(&self, query: &[f32], k: usize) -> Result<Vec<(NodeId, f32)>>;

    /// Number of vectors in the index.
    fn len(&self) -> usize;

    fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// The dimensionality of vectors in this index.
    fn dimensions(&self) -> usize;
}
