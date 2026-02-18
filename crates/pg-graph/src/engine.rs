//! The PersonalGraph engine — the top-level API.
//!
//! Wraps storage + vector index into a unified interface for
//! building knowledge graphs with semantic search.

use crate::traverse;
use pg_core::graph::{Edge, EdgeData, GraphBatch, Node, NodeData};
use pg_core::id::NodeId;
use pg_core::property::PropertyMap;
use pg_core::traits::{GraphStorage, VectorIndex};
use pg_core::{Error, Result};
use pg_storage::GraphStore;
use pg_vector::HnswIndex;
use std::path::Path;

/// Search result combining graph and vector information.
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub node: Node,
    pub distance: f32,
}

/// The main personal graph engine.
pub struct PersonalGraph {
    store: GraphStore,
    vector_index: Option<HnswIndex>,
}

impl PersonalGraph {
    /// Create a new graph persisted at `dir`.
    pub fn open(dir: impl AsRef<Path>) -> Result<Self> {
        let store = GraphStore::open(dir)?;
        Ok(Self {
            store,
            vector_index: None,
        })
    }

    /// Create an in-memory graph (for testing or ephemeral use).
    pub fn in_memory() -> Result<Self> {
        let store = GraphStore::in_memory()?;
        Ok(Self {
            store,
            vector_index: None,
        })
    }

    /// Enable vector search with the given embedding dimensions.
    pub fn with_vector_index(mut self, dimensions: usize) -> Self {
        self.vector_index = Some(HnswIndex::with_defaults(dimensions));
        self
    }

    /// Enable vector search with custom HNSW config.
    pub fn with_vector_index_config(
        mut self,
        dimensions: usize,
        config: pg_vector::hnsw::HnswConfig,
    ) -> Self {
        self.vector_index = Some(HnswIndex::new(dimensions, config));
        self
    }

    // ---- Node operations ----

    /// Add a node with a label and properties.
    pub fn add_node(
        &mut self,
        label: impl Into<String>,
        properties: PropertyMap,
    ) -> Result<NodeId> {
        let node = Node::new(label, properties);
        let id = node.id;
        self.store.insert_node(id, &node.data)?;
        Ok(id)
    }

    /// Add a node and also index its embedding vector for similarity search.
    pub fn add_node_with_embedding(
        &mut self,
        label: impl Into<String>,
        properties: PropertyMap,
        embedding: &[f32],
    ) -> Result<NodeId> {
        let id = self.add_node(label, properties)?;
        if let Some(ref mut vi) = self.vector_index {
            vi.insert(id, embedding)?;
        }
        Ok(id)
    }

    /// Get a node by ID.
    pub fn get_node(&self, id: NodeId) -> Result<Option<Node>> {
        self.store.get_node(id)
    }

    /// Update a node's data.
    pub fn update_node(
        &mut self,
        id: NodeId,
        label: impl Into<String>,
        properties: PropertyMap,
    ) -> Result<()> {
        let data = NodeData {
            label: label.into(),
            properties,
        };
        self.store.update_node(id, &data)
    }

    /// Delete a node and all its edges.
    pub fn delete_node(&mut self, id: NodeId) -> Result<()> {
        self.store.delete_node(id)?;
        if let Some(ref mut vi) = self.vector_index {
            vi.remove(id)?;
        }
        Ok(())
    }

    // ---- Edge operations ----

    /// Add a directed edge between two nodes.
    pub fn add_edge(
        &mut self,
        source: NodeId,
        target: NodeId,
        label: impl Into<String>,
        properties: PropertyMap,
    ) -> Result<()> {
        // Verify both nodes exist
        if self.store.get_node(source)?.is_none() {
            return Err(Error::NodeNotFound(source));
        }
        if self.store.get_node(target)?.is_none() {
            return Err(Error::NodeNotFound(target));
        }

        let data = EdgeData {
            label: label.into(),
            properties,
        };
        self.store.insert_edge(source, target, &data)
    }

    /// Get a specific edge.
    pub fn get_edge(&self, source: NodeId, target: NodeId) -> Result<Option<Edge>> {
        self.store.get_edge(source, target)
    }

    /// Delete an edge.
    pub fn delete_edge(&mut self, source: NodeId, target: NodeId) -> Result<()> {
        self.store.delete_edge(source, target)
    }

    /// Get all outgoing edges from a node.
    pub fn out_edges(&self, source: NodeId) -> Result<Vec<Edge>> {
        self.store.out_edges(source)
    }

    /// Get all incoming edges to a node.
    pub fn in_edges(&self, target: NodeId) -> Result<Vec<Edge>> {
        self.store.in_edges(target)
    }

    /// Get all neighbor node IDs (one hop from source).
    pub fn neighbors(&self, source: NodeId) -> Result<Vec<NodeId>> {
        self.store.neighbors(source)
    }

    // ---- Batch operations ----

    /// Insert a batch of nodes and edges atomically.
    pub fn insert_batch(&mut self, batch: &GraphBatch) -> Result<()> {
        self.store.insert_batch(batch)
    }

    // ---- Search operations ----

    /// Find nodes by label.
    pub fn find_by_label(&self, label: &str) -> Result<Vec<Node>> {
        self.store.nodes_by_label(label)
    }

    /// Vector similarity search. Returns the `k` nearest nodes to `query`.
    pub fn search_similar(&self, query: &[f32], k: usize) -> Result<Vec<SearchResult>> {
        let vi = self
            .vector_index
            .as_ref()
            .ok_or_else(|| Error::Index("vector index not enabled".into()))?;

        let neighbors = vi.search(query, k)?;

        let mut results = Vec::with_capacity(neighbors.len());
        for (node_id, distance) in neighbors {
            if let Some(node) = self.store.get_node(node_id)? {
                results.push(SearchResult { node, distance });
            }
        }
        Ok(results)
    }

    /// Vector similarity search with a distance threshold.
    pub fn search_within_distance(
        &self,
        query: &[f32],
        max_distance: f32,
        k: usize,
    ) -> Result<Vec<SearchResult>> {
        let results = self.search_similar(query, k)?;
        Ok(results
            .into_iter()
            .filter(|r| r.distance <= max_distance)
            .collect())
    }

    // ---- Traversal ----

    /// BFS traversal from a starting node up to `max_depth` hops.
    pub fn bfs(&self, start: NodeId, max_depth: usize) -> Result<Vec<(Node, usize)>> {
        traverse::bfs(&self.store, start, max_depth)
    }

    /// DFS traversal from a starting node up to `max_depth` hops.
    pub fn dfs(&self, start: NodeId, max_depth: usize) -> Result<Vec<(Node, usize)>> {
        traverse::dfs(&self.store, start, max_depth)
    }

    /// Find shortest path between two nodes.
    pub fn shortest_path(
        &self,
        source: NodeId,
        target: NodeId,
    ) -> Result<Option<traverse::Path>> {
        traverse::shortest_path(&self.store, source, target)
    }

    /// Find all nodes of a given label reachable within `max_depth` hops.
    pub fn find_reachable_by_label(
        &self,
        start: NodeId,
        label: &str,
        max_depth: usize,
    ) -> Result<Vec<Node>> {
        traverse::find_by_label(&self.store, start, label, max_depth)
    }

    // ---- Stats ----

    pub fn node_count(&self) -> Result<usize> {
        self.store.node_count()
    }

    pub fn edge_count(&self) -> Result<usize> {
        self.store.edge_count()
    }

    pub fn vector_count(&self) -> usize {
        self.vector_index.as_ref().map_or(0, |vi| vi.len())
    }

    /// Flush everything to disk.
    pub fn checkpoint(&mut self) -> Result<()> {
        self.store.checkpoint()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pg_core::props;

    #[test]
    fn basic_graph_operations() {
        let mut g = PersonalGraph::in_memory().unwrap();

        let alice = g.add_node("Person", props! { "name" => "Alice" }).unwrap();
        let bob = g.add_node("Person", props! { "name" => "Bob" }).unwrap();
        g.add_edge(alice, bob, "knows", props! { "since" => 2020i64 })
            .unwrap();

        assert_eq!(g.node_count().unwrap(), 2);
        assert_eq!(g.edge_count().unwrap(), 1);

        let alice_node = g.get_node(alice).unwrap().unwrap();
        assert_eq!(alice_node.data.label, "Person");

        let edge = g.get_edge(alice, bob).unwrap().unwrap();
        assert_eq!(edge.data.label, "knows");

        let neighbors = g.neighbors(alice).unwrap();
        assert_eq!(neighbors.len(), 1);
        assert_eq!(neighbors[0], bob);
    }

    #[test]
    fn edge_requires_existing_nodes() {
        let mut g = PersonalGraph::in_memory().unwrap();
        let alice = g.add_node("Person", props! {}).unwrap();
        let fake = NodeId::new();
        assert!(g.add_edge(alice, fake, "knows", props! {}).is_err());
    }

    #[test]
    fn vector_search() {
        let mut g = PersonalGraph::in_memory().unwrap().with_vector_index(4);

        let cat = g
            .add_node_with_embedding("Animal", props! { "name" => "cat" }, &[1.0, 0.0, 0.0, 0.0])
            .unwrap();
        let dog = g
            .add_node_with_embedding("Animal", props! { "name" => "dog" }, &[0.9, 0.1, 0.0, 0.0])
            .unwrap();
        let _car = g
            .add_node_with_embedding(
                "Vehicle",
                props! { "name" => "car" },
                &[0.0, 0.0, 1.0, 0.0],
            )
            .unwrap();

        let results = g.search_similar(&[1.0, 0.0, 0.0, 0.0], 2).unwrap();
        assert_eq!(results.len(), 2);
        // Cat should be closest (exact match)
        assert_eq!(results[0].node.id, cat);
        // Dog should be second
        assert_eq!(results[1].node.id, dog);
    }

    #[test]
    fn search_without_vector_index() {
        let g = PersonalGraph::in_memory().unwrap();
        assert!(g.search_similar(&[1.0], 1).is_err());
    }

    #[test]
    fn graph_traversal() {
        let mut g = PersonalGraph::in_memory().unwrap();

        let a = g.add_node("A", props! {}).unwrap();
        let b = g.add_node("B", props! {}).unwrap();
        let c = g.add_node("C", props! {}).unwrap();

        g.add_edge(a, b, "to", props! {}).unwrap();
        g.add_edge(b, c, "to", props! {}).unwrap();

        let path = g.shortest_path(a, c).unwrap().unwrap();
        assert_eq!(path.nodes.len(), 3);
        assert_eq!(path.edges.len(), 2);

        let bfs_results = g.bfs(a, 10).unwrap();
        assert_eq!(bfs_results.len(), 3);
    }

    #[test]
    fn find_by_label() {
        let mut g = PersonalGraph::in_memory().unwrap();

        g.add_node("Person", props! { "name" => "Alice" }).unwrap();
        g.add_node("Person", props! { "name" => "Bob" }).unwrap();
        g.add_node("Event", props! { "title" => "party" }).unwrap();

        let people = g.find_by_label("Person").unwrap();
        assert_eq!(people.len(), 2);
    }

    #[test]
    fn delete_cascades() {
        let mut g = PersonalGraph::in_memory().unwrap().with_vector_index(4);

        let a = g
            .add_node_with_embedding("X", props! {}, &[1.0, 0.0, 0.0, 0.0])
            .unwrap();
        let b = g.add_node("Y", props! {}).unwrap();
        g.add_edge(a, b, "rel", props! {}).unwrap();

        g.delete_node(a).unwrap();
        assert!(g.get_node(a).unwrap().is_none());
        assert_eq!(g.edge_count().unwrap(), 0);
        assert_eq!(g.vector_count(), 0);
    }

    #[test]
    fn batch_operations() {
        let mut g = PersonalGraph::in_memory().unwrap();

        let a = Node::new("A", props! {});
        let b = Node::new("B", props! {});
        let edge = Edge::new(a.id, b.id, "connects", props! {});

        let mut batch = GraphBatch::new();
        batch.add_node(a);
        batch.add_node(b);
        batch.add_edge(edge);

        g.insert_batch(&batch).unwrap();
        assert_eq!(g.node_count().unwrap(), 2);
        assert_eq!(g.edge_count().unwrap(), 1);
    }
}
