//! Graph traversal algorithms.

use pg_core::graph::{Edge, Node};
use pg_core::id::NodeId;
use pg_core::traits::GraphStorage;
use pg_core::Result;
use std::collections::{HashSet, VecDeque};

/// Result of a path search.
#[derive(Debug, Clone)]
pub struct Path {
    pub nodes: Vec<NodeId>,
    pub edges: Vec<Edge>,
}

/// BFS traversal from `start`, visiting up to `max_depth` hops.
/// Returns all nodes reached.
pub fn bfs<S: GraphStorage>(
    store: &S,
    start: NodeId,
    max_depth: usize,
) -> Result<Vec<(Node, usize)>> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut results = Vec::new();

    visited.insert(start);
    queue.push_back((start, 0usize));

    while let Some((current, depth)) = queue.pop_front() {
        if let Some(node) = store.get_node(current)? {
            results.push((node, depth));
        }

        if depth >= max_depth {
            continue;
        }

        for neighbor_id in store.neighbors(current)? {
            if visited.insert(neighbor_id) {
                queue.push_back((neighbor_id, depth + 1));
            }
        }
    }

    Ok(results)
}

/// DFS traversal from `start`, visiting up to `max_depth` hops.
pub fn dfs<S: GraphStorage>(
    store: &S,
    start: NodeId,
    max_depth: usize,
) -> Result<Vec<(Node, usize)>> {
    let mut visited = HashSet::new();
    let mut stack = vec![(start, 0usize)];
    let mut results = Vec::new();

    while let Some((current, depth)) = stack.pop() {
        if !visited.insert(current) {
            continue;
        }

        if let Some(node) = store.get_node(current)? {
            results.push((node, depth));
        }

        if depth >= max_depth {
            continue;
        }

        for neighbor_id in store.neighbors(current)? {
            if !visited.contains(&neighbor_id) {
                stack.push((neighbor_id, depth + 1));
            }
        }
    }

    Ok(results)
}

/// Find shortest path from `source` to `target` using BFS.
/// Returns None if no path exists.
pub fn shortest_path<S: GraphStorage>(
    store: &S,
    source: NodeId,
    target: NodeId,
) -> Result<Option<Path>> {
    if source == target {
        return Ok(Some(Path {
            nodes: vec![source],
            edges: vec![],
        }));
    }

    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    // parent[node] = (parent_node, edge_from_parent_to_node)
    let mut parent: std::collections::HashMap<u128, (NodeId, Edge)> =
        std::collections::HashMap::new();

    visited.insert(source);
    queue.push_back(source);

    while let Some(current) = queue.pop_front() {
        let edges = store.out_edges(current)?;
        for edge in edges {
            let neighbor = edge.target;
            if visited.insert(neighbor) {
                parent.insert(neighbor.as_u128(), (current, edge));

                if neighbor == target {
                    // Reconstruct path
                    let mut path_nodes = vec![target];
                    let mut path_edges = Vec::new();
                    let mut cursor = target;

                    while cursor != source {
                        let (prev, edge) = parent.get(&cursor.as_u128()).unwrap().clone();
                        path_edges.push(edge);
                        path_nodes.push(prev);
                        cursor = prev;
                    }

                    path_nodes.reverse();
                    path_edges.reverse();
                    return Ok(Some(Path {
                        nodes: path_nodes,
                        edges: path_edges,
                    }));
                }

                queue.push_back(neighbor);
            }
        }
    }

    Ok(None) // No path found
}

/// Find all nodes reachable from `start` within `max_depth` hops
/// that match a label filter.
pub fn find_by_label<S: GraphStorage>(
    store: &S,
    start: NodeId,
    label: &str,
    max_depth: usize,
) -> Result<Vec<Node>> {
    let reachable = bfs(store, start, max_depth)?;
    Ok(reachable
        .into_iter()
        .filter(|(node, _)| node.data.label == label)
        .map(|(node, _)| node)
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pg_core::graph::EdgeData;
    use pg_core::props;
    use pg_storage::GraphStore;

    fn build_test_graph() -> (GraphStore, NodeId, NodeId, NodeId, NodeId) {
        let mut store = GraphStore::in_memory().unwrap();
        let a = NodeId::new();
        let b = NodeId::new();
        let c = NodeId::new();
        let d = NodeId::new();

        // a -> b -> c -> d
        //      b -> d (shortcut)
        for (id, label) in [
            (a, "Start"),
            (b, "Middle"),
            (c, "Middle"),
            (d, "End"),
        ] {
            store
                .insert_node(
                    id,
                    &pg_core::graph::NodeData {
                        label: label.into(),
                        properties: props! {},
                    },
                )
                .unwrap();
        }

        let rel = EdgeData {
            label: "next".into(),
            properties: props! {},
        };
        store.insert_edge(a, b, &rel).unwrap();
        store.insert_edge(b, c, &rel).unwrap();
        store.insert_edge(c, d, &rel).unwrap();
        store.insert_edge(b, d, &rel).unwrap(); // shortcut

        (store, a, b, c, d)
    }

    #[test]
    fn bfs_traversal() {
        let (store, a, _, _, _) = build_test_graph();
        let results = bfs(&store, a, 10).unwrap();
        assert_eq!(results.len(), 4);
        // First result should be the start node at depth 0
        assert_eq!(results[0].0.id, a);
        assert_eq!(results[0].1, 0);
    }

    #[test]
    fn bfs_depth_limit() {
        let (store, a, _, _, _) = build_test_graph();
        let results = bfs(&store, a, 1).unwrap();
        // Only a (depth 0) and b (depth 1)
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn dfs_traversal() {
        let (store, a, _, _, _) = build_test_graph();
        let results = dfs(&store, a, 10).unwrap();
        assert_eq!(results.len(), 4);
    }

    #[test]
    fn shortest_path_found() {
        let (store, a, _b, _c, d) = build_test_graph();
        let path = shortest_path(&store, a, d).unwrap().unwrap();
        // Shortest: a -> b -> d (2 edges, through shortcut)
        assert_eq!(path.nodes.len(), 3);
        assert_eq!(path.nodes[0], a);
        assert_eq!(path.nodes[2], d);
        assert_eq!(path.edges.len(), 2);
    }

    #[test]
    fn shortest_path_self() {
        let (store, a, _, _, _) = build_test_graph();
        let path = shortest_path(&store, a, a).unwrap().unwrap();
        assert_eq!(path.nodes, vec![a]);
        assert!(path.edges.is_empty());
    }

    #[test]
    fn shortest_path_not_found() {
        let (store, _a, _b, _c, d) = build_test_graph();
        // d has no outgoing edges, so no path from d to a
        let a = NodeId::new();
        let node_data = pg_core::graph::NodeData {
            label: "Isolated".into(),
            properties: props! {},
        };
        let mut store = store;
        store.insert_node(a, &node_data).unwrap();
        let path = shortest_path(&store, d, a).unwrap();
        assert!(path.is_none());
    }

    #[test]
    fn find_by_label_traversal() {
        let (store, a, _, _, _) = build_test_graph();
        let middles = find_by_label(&store, a, "Middle", 10).unwrap();
        assert_eq!(middles.len(), 2);
    }
}
