use crate::id::NodeId;
use crate::property::PropertyMap;
use serde::{Deserialize, Serialize};

/// The payload stored for each node in the graph.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NodeData {
    /// Semantic label (e.g., "Person", "Concept", "Event").
    pub label: String,
    /// Arbitrary key-value properties.
    pub properties: PropertyMap,
}

/// A node with its identity resolved.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Node {
    pub id: NodeId,
    pub data: NodeData,
}

/// The payload stored for each edge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EdgeData {
    /// Relationship type (e.g., "knows", "contains", "instance_of").
    pub label: String,
    /// Arbitrary key-value properties.
    pub properties: PropertyMap,
}

/// A fully resolved edge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Edge {
    pub source: NodeId,
    pub target: NodeId,
    pub data: EdgeData,
}

impl Node {
    pub fn new(label: impl Into<String>, properties: PropertyMap) -> Self {
        Self {
            id: NodeId::new(),
            data: NodeData {
                label: label.into(),
                properties,
            },
        }
    }

    pub fn with_id(id: NodeId, label: impl Into<String>, properties: PropertyMap) -> Self {
        Self {
            id,
            data: NodeData {
                label: label.into(),
                properties,
            },
        }
    }
}

impl Edge {
    pub fn new(
        source: NodeId,
        target: NodeId,
        label: impl Into<String>,
        properties: PropertyMap,
    ) -> Self {
        Self {
            source,
            target,
            data: EdgeData {
                label: label.into(),
                properties,
            },
        }
    }
}

/// A batch of nodes and edges for bulk insertion.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct GraphBatch {
    pub nodes: Vec<Node>,
    pub edges: Vec<Edge>,
}

impl GraphBatch {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_node(&mut self, node: Node) {
        self.nodes.push(node);
    }

    pub fn add_edge(&mut self, edge: Edge) {
        self.edges.push(edge);
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::props;

    #[test]
    fn create_node() {
        let node = Node::new("Person", props! { "name" => "Alice" });
        assert_eq!(node.data.label, "Person");
        assert_eq!(
            node.data.properties.get("name").unwrap().as_str(),
            Some("Alice")
        );
    }

    #[test]
    fn create_edge() {
        let a = Node::new("Person", props! { "name" => "Alice" });
        let b = Node::new("Person", props! { "name" => "Bob" });
        let edge = Edge::new(a.id, b.id, "knows", props! {});
        assert_eq!(edge.data.label, "knows");
        assert_eq!(edge.source, a.id);
        assert_eq!(edge.target, b.id);
    }

    #[test]
    fn graph_batch() {
        let mut batch = GraphBatch::new();
        let a = Node::new("X", props! {});
        let b = Node::new("Y", props! {});
        let edge = Edge::new(a.id, b.id, "rel", props! {});
        batch.add_node(a);
        batch.add_node(b);
        batch.add_edge(edge);
        assert_eq!(batch.node_count(), 2);
        assert_eq!(batch.edge_count(), 1);
    }
}
