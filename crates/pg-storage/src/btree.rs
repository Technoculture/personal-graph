//! In-memory B+Tree index over NodeId -> PageId mapping.
//!
//! This gives us O(log n) point lookups from a node's UUID to the data page
//! where its serialized NodeData lives. The tree itself is rebuilt from the
//! data file on startup (like a secondary index).

use crate::wal::PageId;
use pg_core::id::NodeId;
use std::collections::BTreeMap;

/// A B+Tree index mapping NodeId -> (PageId, CellIndex).
///
/// Uses Rust's std BTreeMap as the in-memory structure.
/// This is a secondary index — the source of truth is the data pages.
/// On startup, we scan all data pages and rebuild this index.
#[derive(Debug)]
pub struct NodeIndex {
    inner: BTreeMap<u128, Location>,
}

/// Where a node's data lives on disk.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Location {
    pub page_id: PageId,
    pub cell_idx: u16,
}

impl NodeIndex {
    pub fn new() -> Self {
        Self {
            inner: BTreeMap::new(),
        }
    }

    /// Insert or update a node's location.
    pub fn insert(&mut self, id: NodeId, loc: Location) {
        self.inner.insert(id.as_u128(), loc);
    }

    /// Look up a node's storage location.
    pub fn get(&self, id: NodeId) -> Option<Location> {
        self.inner.get(&id.as_u128()).copied()
    }

    /// Remove a node from the index.
    pub fn remove(&mut self, id: NodeId) -> Option<Location> {
        self.inner.remove(&id.as_u128())
    }

    /// Check if a node is indexed.
    pub fn contains(&self, id: NodeId) -> bool {
        self.inner.contains_key(&id.as_u128())
    }

    /// Number of indexed nodes.
    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    /// Iterate all indexed entries.
    pub fn iter(&self) -> impl Iterator<Item = (NodeId, Location)> + '_ {
        self.inner
            .iter()
            .map(|(&k, &v)| (NodeId::from_u128(k), v))
    }
}

impl Default for NodeIndex {
    fn default() -> Self {
        Self::new()
    }
}

/// Index for edges: (source, target) -> (PageId, CellIndex).
#[derive(Debug)]
pub struct EdgeIndex {
    /// Primary index: (source, target) -> Location
    by_pair: BTreeMap<(u128, u128), Location>,
    /// Secondary index: source -> list of targets
    by_source: BTreeMap<u128, Vec<u128>>,
    /// Secondary index: target -> list of sources
    by_target: BTreeMap<u128, Vec<u128>>,
}

impl EdgeIndex {
    pub fn new() -> Self {
        Self {
            by_pair: BTreeMap::new(),
            by_source: BTreeMap::new(),
            by_target: BTreeMap::new(),
        }
    }

    pub fn insert(&mut self, source: NodeId, target: NodeId, loc: Location) {
        let sk = source.as_u128();
        let tk = target.as_u128();

        self.by_pair.insert((sk, tk), loc);
        self.by_source.entry(sk).or_default().push(tk);
        self.by_target.entry(tk).or_default().push(sk);
    }

    pub fn get(&self, source: NodeId, target: NodeId) -> Option<Location> {
        self.by_pair
            .get(&(source.as_u128(), target.as_u128()))
            .copied()
    }

    pub fn remove(&mut self, source: NodeId, target: NodeId) -> Option<Location> {
        let sk = source.as_u128();
        let tk = target.as_u128();

        let loc = self.by_pair.remove(&(sk, tk));

        if let Some(targets) = self.by_source.get_mut(&sk) {
            targets.retain(|&t| t != tk);
        }
        if let Some(sources) = self.by_target.get_mut(&tk) {
            sources.retain(|&s| s != sk);
        }
        loc
    }

    /// All targets reachable from `source` (outgoing edges).
    pub fn out_targets(&self, source: NodeId) -> Vec<NodeId> {
        self.by_source
            .get(&source.as_u128())
            .map(|targets| targets.iter().map(|&t| NodeId::from_u128(t)).collect())
            .unwrap_or_default()
    }

    /// All sources pointing to `target` (incoming edges).
    pub fn in_sources(&self, target: NodeId) -> Vec<NodeId> {
        self.by_target
            .get(&target.as_u128())
            .map(|sources| sources.iter().map(|&s| NodeId::from_u128(s)).collect())
            .unwrap_or_default()
    }

    /// All edge locations originating from `source`.
    pub fn out_edges(&self, source: NodeId) -> Vec<(NodeId, Location)> {
        let sk = source.as_u128();
        self.by_source
            .get(&sk)
            .map(|targets| {
                targets
                    .iter()
                    .filter_map(|&tk| {
                        self.by_pair
                            .get(&(sk, tk))
                            .map(|&loc| (NodeId::from_u128(tk), loc))
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    /// All edge locations pointing to `target`.
    pub fn in_edges(&self, target: NodeId) -> Vec<(NodeId, Location)> {
        let tk = target.as_u128();
        self.by_target
            .get(&tk)
            .map(|sources| {
                sources
                    .iter()
                    .filter_map(|&sk| {
                        self.by_pair
                            .get(&(sk, tk))
                            .map(|&loc| (NodeId::from_u128(sk), loc))
                    })
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Remove all edges involving a node (both as source and target).
    pub fn remove_node(&mut self, id: NodeId) -> Vec<(NodeId, NodeId)> {
        let k = id.as_u128();
        let mut removed = Vec::new();

        // Remove outgoing edges
        if let Some(targets) = self.by_source.remove(&k) {
            for tk in &targets {
                self.by_pair.remove(&(k, *tk));
                if let Some(sources) = self.by_target.get_mut(tk) {
                    sources.retain(|&s| s != k);
                }
                removed.push((id, NodeId::from_u128(*tk)));
            }
        }

        // Remove incoming edges
        if let Some(sources) = self.by_target.remove(&k) {
            for sk in &sources {
                self.by_pair.remove(&(*sk, k));
                if let Some(targets) = self.by_source.get_mut(sk) {
                    targets.retain(|&t| t != k);
                }
                removed.push((NodeId::from_u128(*sk), id));
            }
        }

        removed
    }

    pub fn len(&self) -> usize {
        self.by_pair.len()
    }

    pub fn is_empty(&self) -> bool {
        self.by_pair.is_empty()
    }
}

impl Default for EdgeIndex {
    fn default() -> Self {
        Self::new()
    }
}

/// Label index: label string -> set of NodeIds.
#[derive(Debug, Default)]
pub struct LabelIndex {
    inner: BTreeMap<String, Vec<u128>>,
}

impl LabelIndex {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert(&mut self, label: &str, id: NodeId) {
        self.inner
            .entry(label.to_owned())
            .or_default()
            .push(id.as_u128());
    }

    pub fn remove(&mut self, label: &str, id: NodeId) {
        if let Some(ids) = self.inner.get_mut(label) {
            ids.retain(|&k| k != id.as_u128());
            if ids.is_empty() {
                self.inner.remove(label);
            }
        }
    }

    pub fn get(&self, label: &str) -> Vec<NodeId> {
        self.inner
            .get(label)
            .map(|ids| ids.iter().map(|&k| NodeId::from_u128(k)).collect())
            .unwrap_or_default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn node_index_crud() {
        let mut idx = NodeIndex::new();
        let id = NodeId::new();
        let loc = Location {
            page_id: 5,
            cell_idx: 3,
        };

        idx.insert(id, loc);
        assert_eq!(idx.get(id), Some(loc));
        assert!(idx.contains(id));
        assert_eq!(idx.len(), 1);

        idx.remove(id);
        assert_eq!(idx.get(id), None);
        assert_eq!(idx.len(), 0);
    }

    #[test]
    fn edge_index_adjacency() {
        let mut idx = EdgeIndex::new();
        let a = NodeId::new();
        let b = NodeId::new();
        let c = NodeId::new();

        let loc_ab = Location {
            page_id: 0,
            cell_idx: 0,
        };
        let loc_ac = Location {
            page_id: 0,
            cell_idx: 1,
        };
        let loc_ba = Location {
            page_id: 1,
            cell_idx: 0,
        };

        idx.insert(a, b, loc_ab);
        idx.insert(a, c, loc_ac);
        idx.insert(b, a, loc_ba);

        let out = idx.out_targets(a);
        assert_eq!(out.len(), 2);

        let in_a = idx.in_sources(a);
        assert_eq!(in_a.len(), 1);
        assert_eq!(in_a[0], b);

        assert_eq!(idx.len(), 3);
    }

    #[test]
    fn edge_index_remove_node() {
        let mut idx = EdgeIndex::new();
        let a = NodeId::new();
        let b = NodeId::new();
        let c = NodeId::new();

        let loc = Location {
            page_id: 0,
            cell_idx: 0,
        };
        idx.insert(a, b, loc);
        idx.insert(b, c, loc);
        idx.insert(c, a, loc);

        let removed = idx.remove_node(b);
        assert_eq!(removed.len(), 2); // a->b and b->c
        assert_eq!(idx.len(), 1); // only c->a remains
    }

    #[test]
    fn label_index() {
        let mut idx = LabelIndex::new();
        let a = NodeId::new();
        let b = NodeId::new();
        let c = NodeId::new();

        idx.insert("Person", a);
        idx.insert("Person", b);
        idx.insert("Event", c);

        assert_eq!(idx.get("Person").len(), 2);
        assert_eq!(idx.get("Event").len(), 1);
        assert_eq!(idx.get("Missing").len(), 0);

        idx.remove("Person", a);
        assert_eq!(idx.get("Person").len(), 1);
    }
}
