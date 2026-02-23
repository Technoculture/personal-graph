//! GraphStore — the top-level storage engine.
//!
//! Ties together pages, buffer pool, WAL, and indexes into a coherent
//! GraphStorage implementation.

use crate::btree::{EdgeIndex, LabelIndex, Location, NodeIndex};
use crate::buffer::BufferPool;
use crate::compaction::{compact_store, CompactionStats};
use crate::mvcc::TxManager;
use crate::page::{Page, PageType};
use crate::wal::{PageId, RecordType, Wal};
use pg_core::error::Result;
use pg_core::graph::{Edge, EdgeData, GraphBatch, Node, NodeData};
use pg_core::id::NodeId;
use pg_core::traits::GraphStorage;
use pg_core::Error;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// On-disk cell format for a node.
#[derive(Serialize, Deserialize)]
struct NodeCell {
    id: NodeId,
    data: NodeData,
}

/// On-disk cell format for an edge.
#[derive(Serialize, Deserialize)]
struct EdgeCell {
    source: NodeId,
    target: NodeId,
    data: EdgeData,
}

/// The main storage engine.
pub struct GraphStore {
    buffer: BufferPool,
    wal: Wal,
    /// MVCC transaction manager — tracks active transactions and snapshots.
    pub tx_manager: TxManager,
    node_index: NodeIndex,
    edge_index: EdgeIndex,
    label_index: LabelIndex,
    /// Current page for appending node data.
    current_node_page: Option<PageId>,
    /// Current page for appending edge data.
    current_edge_page: Option<PageId>,
    #[allow(dead_code)]
    data_dir: PathBuf,
}

impl GraphStore {
    /// Open or create a graph store at the given directory.
    pub fn open(dir: impl AsRef<Path>) -> Result<Self> {
        let dir = dir.as_ref();
        std::fs::create_dir_all(dir)?;

        let data_path = dir.join("graph.db");
        let wal_path = dir.join("graph.wal");

        let buffer = BufferPool::open(&data_path, 1024)?;
        let wal = Wal::open(&wal_path)?;

        let mut store = GraphStore {
            buffer,
            wal,
            tx_manager: TxManager::new(),
            node_index: NodeIndex::new(),
            edge_index: EdgeIndex::new(),
            label_index: LabelIndex::new(),
            current_node_page: None,
            current_edge_page: None,
            data_dir: dir.to_path_buf(),
        };

        // Rebuild indexes from existing data
        store.rebuild_indexes()?;
        Ok(store)
    }

    /// Open an in-memory store backed by a temporary directory.
    pub fn in_memory() -> Result<Self> {
        let path = std::env::temp_dir().join(format!("pg-{}", uuid::Uuid::new_v4()));
        Self::open(path)
    }

    fn rebuild_indexes(&mut self) -> Result<()> {
        let page_count = self.buffer.page_count();
        for pid in 0..page_count {
            let page = self.buffer.fetch(pid)?;
            match page.page_type() {
                PageType::Data => self.index_node_page(pid, &page)?,
                PageType::BTreeLeaf => self.index_edge_page(pid, &page)?,
                _ => {}
            }
        }
        Ok(())
    }

    fn index_node_page(&mut self, page_id: PageId, page: &Page) -> Result<()> {
        for i in 0..page.cell_count() {
            if let Some(cell_data) = page.read_cell(i) {
                if let Ok(cell) = serde_json::from_slice::<NodeCell>(cell_data) {
                    let loc = Location {
                        page_id,
                        cell_idx: i,
                    };
                    self.node_index.insert(cell.id, loc);
                    self.label_index.insert(&cell.data.label, cell.id);
                }
            }
        }
        Ok(())
    }

    fn index_edge_page(&mut self, page_id: PageId, page: &Page) -> Result<()> {
        for i in 0..page.cell_count() {
            if let Some(cell_data) = page.read_cell(i) {
                if let Ok(cell) = serde_json::from_slice::<EdgeCell>(cell_data) {
                    let loc = Location {
                        page_id,
                        cell_idx: i,
                    };
                    self.edge_index.insert(cell.source, cell.target, loc);
                }
            }
        }
        Ok(())
    }

    fn allocate_or_reuse_node_page(&mut self) -> Result<PageId> {
        if let Some(pid) = self.current_node_page {
            let page = self.buffer.fetch(pid)?;
            if page.free_space() > 256 {
                return Ok(pid);
            }
        }
        let pid = self.buffer.allocate(PageType::Data)?;
        self.current_node_page = Some(pid);
        Ok(pid)
    }

    fn allocate_or_reuse_edge_page(&mut self) -> Result<PageId> {
        if let Some(pid) = self.current_edge_page {
            let page = self.buffer.fetch(pid)?;
            if page.free_space() > 256 {
                return Ok(pid);
            }
        }
        // Using BTreeLeaf page type to distinguish edge pages
        let pid = self.buffer.allocate(PageType::BTreeLeaf)?;
        self.current_edge_page = Some(pid);
        Ok(pid)
    }

    /// Force flush everything to disk.
    pub fn checkpoint(&mut self) -> Result<()> {
        self.buffer.flush_all()?;
        self.wal.sync()?;
        self.wal.truncate()?;
        Ok(())
    }

    /// Run a compaction pass: remove dead (MVCC-deleted) cells from all pages,
    /// then rebuild in-memory indexes to reflect the new physical layout.
    ///
    /// Should be called when there are no active writer transactions, though it
    /// is safe to call at any time — live cells are never touched.
    pub fn compact(&mut self) -> Result<CompactionStats> {
        let min_active = self.tx_manager.min_active();
        let stats = compact_store(&self.buffer, &mut self.wal, min_active)?;
        if stats.pages_modified > 0 {
            // Physical cell offsets changed — rebuild in-memory indexes.
            self.node_index = NodeIndex::new();
            self.edge_index = EdgeIndex::new();
            self.label_index = LabelIndex::new();
            self.current_node_page = None;
            self.current_edge_page = None;
            self.rebuild_indexes()?;
        }
        Ok(stats)
    }

    fn read_node_at(&self, loc: Location) -> Result<Node> {
        let page = self.buffer.fetch(loc.page_id)?;
        let cell_data = page
            .read_cell(loc.cell_idx)
            .ok_or_else(|| Error::Storage("cell not found".into()))?;
        let cell: NodeCell = serde_json::from_slice(cell_data)?;
        Ok(Node {
            id: cell.id,
            data: cell.data,
        })
    }

    fn read_edge_at(&self, loc: Location) -> Result<Edge> {
        let page = self.buffer.fetch(loc.page_id)?;
        let cell_data = page
            .read_cell(loc.cell_idx)
            .ok_or_else(|| Error::Storage("cell not found".into()))?;
        let cell: EdgeCell = serde_json::from_slice(cell_data)?;
        Ok(Edge {
            source: cell.source,
            target: cell.target,
            data: cell.data,
        })
    }
}

impl GraphStorage for GraphStore {
    fn insert_node(&mut self, id: NodeId, data: &NodeData) -> Result<()> {
        if self.node_index.contains(id) {
            return Err(Error::DuplicateNode(id));
        }

        let cell = NodeCell {
            id,
            data: data.clone(),
        };
        let payload = serde_json::to_vec(&cell)?;

        // WAL first
        self.wal
            .append(0, RecordType::InsertNode, payload.clone())?;

        // Find or allocate a page
        let page_id = self.allocate_or_reuse_node_page()?;

        // Insert into page
        let mut page = self.buffer.fetch(page_id)?;
        let cell_idx = match page.insert_cell(&payload) {
            Ok(idx) => idx,
            Err(Error::PageFull) => {
                // Allocate a new page
                let new_pid = self.buffer.allocate(PageType::Data)?;
                self.current_node_page = Some(new_pid);
                let mut new_page = self.buffer.fetch(new_pid)?;
                let idx = new_page.insert_cell(&payload)?;
                self.buffer.write(new_pid, new_page)?;
                self.node_index.insert(
                    id,
                    Location {
                        page_id: new_pid,
                        cell_idx: idx,
                    },
                );
                self.label_index.insert(&data.label, id);
                return Ok(());
            }
            Err(e) => return Err(e),
        };
        self.buffer.write(page_id, page)?;

        // Update indexes
        self.node_index
            .insert(id, Location { page_id, cell_idx });
        self.label_index.insert(&data.label, id);
        Ok(())
    }

    fn get_node(&self, id: NodeId) -> Result<Option<Node>> {
        match self.node_index.get(id) {
            Some(loc) => Ok(Some(self.read_node_at(loc)?)),
            None => Ok(None),
        }
    }

    fn update_node(&mut self, id: NodeId, data: &NodeData) -> Result<()> {
        // Remove old entry from label index
        if let Some(loc) = self.node_index.get(id) {
            let old = self.read_node_at(loc)?;
            self.label_index.remove(&old.data.label, id);
        }

        // Delete and re-insert (append-only strategy — old cell becomes garbage)
        self.node_index.remove(id);

        let cell = NodeCell {
            id,
            data: data.clone(),
        };
        let payload = serde_json::to_vec(&cell)?;

        self.wal
            .append(0, RecordType::InsertNode, payload.clone())?;

        let page_id = self.allocate_or_reuse_node_page()?;
        let mut page = self.buffer.fetch(page_id)?;
        let cell_idx = match page.insert_cell(&payload) {
            Ok(idx) => idx,
            Err(Error::PageFull) => {
                let new_pid = self.buffer.allocate(PageType::Data)?;
                self.current_node_page = Some(new_pid);
                let mut new_page = self.buffer.fetch(new_pid)?;
                let idx = new_page.insert_cell(&payload)?;
                self.buffer.write(new_pid, new_page)?;
                self.node_index.insert(
                    id,
                    Location {
                        page_id: new_pid,
                        cell_idx: idx,
                    },
                );
                self.label_index.insert(&data.label, id);
                return Ok(());
            }
            Err(e) => return Err(e),
        };
        self.buffer.write(page_id, page)?;

        self.node_index
            .insert(id, Location { page_id, cell_idx });
        self.label_index.insert(&data.label, id);
        Ok(())
    }

    fn delete_node(&mut self, id: NodeId) -> Result<()> {
        if let Some(loc) = self.node_index.get(id) {
            let node = self.read_node_at(loc)?;
            self.label_index.remove(&node.data.label, id);
        }

        self.node_index.remove(id);
        self.edge_index.remove_node(id);

        self.wal
            .append(0, RecordType::DeleteNode, id.to_bytes().to_vec())?;
        Ok(())
    }

    fn insert_edge(&mut self, source: NodeId, target: NodeId, data: &EdgeData) -> Result<()> {
        let cell = EdgeCell {
            source,
            target,
            data: data.clone(),
        };
        let payload = serde_json::to_vec(&cell)?;

        self.wal
            .append(0, RecordType::InsertEdge, payload.clone())?;

        let page_id = self.allocate_or_reuse_edge_page()?;
        let mut page = self.buffer.fetch(page_id)?;
        let cell_idx = match page.insert_cell(&payload) {
            Ok(idx) => idx,
            Err(Error::PageFull) => {
                let new_pid = self.buffer.allocate(PageType::BTreeLeaf)?;
                self.current_edge_page = Some(new_pid);
                let mut new_page = self.buffer.fetch(new_pid)?;
                let idx = new_page.insert_cell(&payload)?;
                self.buffer.write(new_pid, new_page)?;
                self.edge_index.insert(
                    source,
                    target,
                    Location {
                        page_id: new_pid,
                        cell_idx: idx,
                    },
                );
                return Ok(());
            }
            Err(e) => return Err(e),
        };
        self.buffer.write(page_id, page)?;

        self.edge_index
            .insert(source, target, Location { page_id, cell_idx });
        Ok(())
    }

    fn get_edge(&self, source: NodeId, target: NodeId) -> Result<Option<Edge>> {
        match self.edge_index.get(source, target) {
            Some(loc) => Ok(Some(self.read_edge_at(loc)?)),
            None => Ok(None),
        }
    }

    fn delete_edge(&mut self, source: NodeId, target: NodeId) -> Result<()> {
        self.edge_index.remove(source, target);
        let mut payload = source.to_bytes().to_vec();
        payload.extend_from_slice(&target.to_bytes());
        self.wal
            .append(0, RecordType::DeleteEdge, payload)?;
        Ok(())
    }

    fn out_edges(&self, source: NodeId) -> Result<Vec<Edge>> {
        self.edge_index
            .out_edges(source)
            .into_iter()
            .map(|(_, loc)| self.read_edge_at(loc))
            .collect()
    }

    fn in_edges(&self, target: NodeId) -> Result<Vec<Edge>> {
        self.edge_index
            .in_edges(target)
            .into_iter()
            .map(|(_, loc)| self.read_edge_at(loc))
            .collect()
    }

    fn neighbors(&self, source: NodeId) -> Result<Vec<NodeId>> {
        Ok(self.edge_index.out_targets(source))
    }

    fn insert_batch(&mut self, batch: &GraphBatch) -> Result<()> {
        for node in &batch.nodes {
            self.insert_node(node.id, &node.data)?;
        }
        for edge in &batch.edges {
            self.insert_edge(edge.source, edge.target, &edge.data)?;
        }
        Ok(())
    }

    fn nodes_by_label(&self, label: &str) -> Result<Vec<Node>> {
        self.label_index
            .get(label)
            .into_iter()
            .filter_map(|id| {
                self.node_index
                    .get(id)
                    .and_then(|loc| self.read_node_at(loc).ok())
            })
            .map(Ok)
            .collect()
    }

    fn node_count(&self) -> Result<usize> {
        Ok(self.node_index.len())
    }

    fn edge_count(&self) -> Result<usize> {
        Ok(self.edge_index.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pg_core::props;

    fn test_store() -> GraphStore {
        GraphStore::in_memory().unwrap()
    }

    #[test]
    fn insert_and_get_node() {
        let mut store = test_store();
        let node = Node::new("Person", props! { "name" => "Alice" });
        store.insert_node(node.id, &node.data).unwrap();

        let got = store.get_node(node.id).unwrap().unwrap();
        assert_eq!(got.data.label, "Person");
        assert_eq!(got.data.properties.get("name").unwrap().as_str(), Some("Alice"));
    }

    #[test]
    fn duplicate_node_rejected() {
        let mut store = test_store();
        let node = Node::new("X", props! {});
        store.insert_node(node.id, &node.data).unwrap();
        assert!(store.insert_node(node.id, &node.data).is_err());
    }

    #[test]
    fn update_node() {
        let mut store = test_store();
        let node = Node::new("Person", props! { "name" => "Alice" });
        store.insert_node(node.id, &node.data).unwrap();

        let updated = NodeData {
            label: "Person".into(),
            properties: props! { "name" => "Bob" },
        };
        store.update_node(node.id, &updated).unwrap();

        let got = store.get_node(node.id).unwrap().unwrap();
        assert_eq!(got.data.properties.get("name").unwrap().as_str(), Some("Bob"));
    }

    #[test]
    fn delete_node_cascades_edges() {
        let mut store = test_store();
        let a = Node::new("A", props! {});
        let b = Node::new("B", props! {});
        store.insert_node(a.id, &a.data).unwrap();
        store.insert_node(b.id, &b.data).unwrap();

        let edge_data = EdgeData {
            label: "knows".into(),
            properties: props! {},
        };
        store.insert_edge(a.id, b.id, &edge_data).unwrap();
        assert_eq!(store.edge_count().unwrap(), 1);

        store.delete_node(a.id).unwrap();
        assert!(store.get_node(a.id).unwrap().is_none());
        assert_eq!(store.edge_count().unwrap(), 0);
    }

    #[test]
    fn edges_and_adjacency() {
        let mut store = test_store();
        let a = Node::new("A", props! {});
        let b = Node::new("B", props! {});
        let c = Node::new("C", props! {});
        store.insert_node(a.id, &a.data).unwrap();
        store.insert_node(b.id, &b.data).unwrap();
        store.insert_node(c.id, &c.data).unwrap();

        let rel = EdgeData {
            label: "link".into(),
            properties: props! {},
        };
        store.insert_edge(a.id, b.id, &rel).unwrap();
        store.insert_edge(a.id, c.id, &rel).unwrap();

        let out = store.out_edges(a.id).unwrap();
        assert_eq!(out.len(), 2);

        let neighbors = store.neighbors(a.id).unwrap();
        assert_eq!(neighbors.len(), 2);

        let incoming = store.in_edges(b.id).unwrap();
        assert_eq!(incoming.len(), 1);
        assert_eq!(incoming[0].source, a.id);
    }

    #[test]
    fn nodes_by_label() {
        let mut store = test_store();
        store
            .insert_node(NodeId::new(), &NodeData {
                label: "Person".into(),
                properties: props! { "name" => "Alice" },
            })
            .unwrap();
        store
            .insert_node(NodeId::new(), &NodeData {
                label: "Person".into(),
                properties: props! { "name" => "Bob" },
            })
            .unwrap();
        store
            .insert_node(NodeId::new(), &NodeData {
                label: "Event".into(),
                properties: props! { "title" => "party" },
            })
            .unwrap();

        assert_eq!(store.nodes_by_label("Person").unwrap().len(), 2);
        assert_eq!(store.nodes_by_label("Event").unwrap().len(), 1);
        assert_eq!(store.nodes_by_label("Missing").unwrap().len(), 0);
    }

    #[test]
    fn batch_insert() {
        let mut store = test_store();
        let a = Node::new("A", props! {});
        let b = Node::new("B", props! {});
        let edge = Edge::new(a.id, b.id, "link", props! {});

        let mut batch = GraphBatch::new();
        batch.add_node(a);
        batch.add_node(b);
        batch.add_edge(edge);

        store.insert_batch(&batch).unwrap();
        assert_eq!(store.node_count().unwrap(), 2);
        assert_eq!(store.edge_count().unwrap(), 1);
    }

    #[test]
    fn persistence_across_reopen() {
        let dir = tempfile::tempdir().unwrap();

        let a_id;
        {
            let mut store = GraphStore::open(dir.path()).unwrap();
            let a = Node::new("Persistent", props! { "value" => 42i64 });
            a_id = a.id;
            store.insert_node(a.id, &a.data).unwrap();
            store.checkpoint().unwrap();
        }

        {
            let store = GraphStore::open(dir.path()).unwrap();
            let node = store.get_node(a_id).unwrap().unwrap();
            assert_eq!(node.data.label, "Persistent");
            assert_eq!(node.data.properties.get("value").unwrap().as_i64(), Some(42));
        }
    }

    #[test]
    fn many_nodes() {
        let mut store = test_store();
        for i in 0..500 {
            let node = Node::new("Item", props! { "idx" => i as i64 });
            store.insert_node(node.id, &node.data).unwrap();
        }
        assert_eq!(store.node_count().unwrap(), 500);
        assert_eq!(store.nodes_by_label("Item").unwrap().len(), 500);
    }
}
