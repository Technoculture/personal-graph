//! Hierarchical Navigable Small World (HNSW) graph.
//!
//! Reference: Malkov & Yashunin, "Efficient and robust approximate nearest
//! neighbor search using Hierarchical Navigable Small World graphs" (2018).
//!
//! This is a from-scratch implementation. No wrappers.

use crate::distance::DistanceMetric;
use ordered_float::OrderedFloat;
use pg_core::id::NodeId;
use pg_core::traits::VectorIndex;
use pg_core::{Error, Result};
use rand::Rng;
use std::collections::{BinaryHeap, HashMap, HashSet};

/// HNSW configuration parameters.
#[derive(Debug, Clone)]
pub struct HnswConfig {
    /// Max number of connections per node per layer.
    pub m: usize,
    /// Max connections for layer 0 (typically 2*M).
    pub m_max0: usize,
    /// Number of candidates during construction.
    pub ef_construction: usize,
    /// Number of candidates during search.
    pub ef_search: usize,
    /// Distance metric.
    pub metric: DistanceMetric,
    /// Normalization factor for level generation.
    pub ml: f64,
}

impl Default for HnswConfig {
    fn default() -> Self {
        Self {
            m: 16,
            m_max0: 32,
            ef_construction: 200,
            ef_search: 50,
            metric: DistanceMetric::Cosine,
            ml: 1.0 / (16.0_f64.ln()),
        }
    }
}

#[derive(Clone)]
struct HnswNode {
    id: NodeId,
    vector: Vec<f32>,
    /// Neighbors at each layer. neighbors[layer] = vec of (NodeId, distance).
    neighbors: Vec<Vec<InternalId>>,
}

type InternalId = u32;

/// Min-heap entry for search candidates.
#[derive(Clone)]
struct Candidate {
    distance: OrderedFloat<f32>,
    internal_id: InternalId,
}

impl PartialEq for Candidate {
    fn eq(&self, other: &Self) -> bool {
        self.distance == other.distance
    }
}

impl Eq for Candidate {}

impl PartialOrd for Candidate {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Candidate {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // Reverse for min-heap behavior with BinaryHeap (which is a max-heap)
        other.distance.cmp(&self.distance)
    }
}

/// Max-heap entry (for tracking the worst candidate in the result set).
#[derive(Clone)]
struct FarCandidate {
    distance: OrderedFloat<f32>,
    internal_id: InternalId,
}

impl PartialEq for FarCandidate {
    fn eq(&self, other: &Self) -> bool {
        self.distance == other.distance
    }
}

impl Eq for FarCandidate {}

impl PartialOrd for FarCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for FarCandidate {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.distance.cmp(&other.distance)
    }
}

/// HNSW index for approximate nearest neighbor search.
pub struct HnswIndex {
    config: HnswConfig,
    dimensions: usize,
    nodes: Vec<HnswNode>,
    id_to_internal: HashMap<u128, InternalId>,
    entry_point: Option<InternalId>,
    max_layer: usize,
}

impl HnswIndex {
    pub fn new(dimensions: usize, config: HnswConfig) -> Self {
        Self {
            config,
            dimensions,
            nodes: Vec::new(),
            id_to_internal: HashMap::new(),
            entry_point: None,
            max_layer: 0,
        }
    }

    pub fn with_defaults(dimensions: usize) -> Self {
        Self::new(dimensions, HnswConfig::default())
    }

    fn random_level(&self) -> usize {
        let mut rng = rand::thread_rng();
        let r: f64 = rng.gen();
        (-r.ln() * self.config.ml).floor() as usize
    }

    fn distance(&self, a: InternalId, b_vec: &[f32]) -> f32 {
        self.config
            .metric
            .compute(&self.nodes[a as usize].vector, b_vec)
    }

    #[allow(dead_code)]
    fn distance_between(&self, a: InternalId, b: InternalId) -> f32 {
        self.config
            .metric
            .compute(&self.nodes[a as usize].vector, &self.nodes[b as usize].vector)
    }

    /// Search a single layer for the ef nearest neighbors to `query`.
    fn search_layer(
        &self,
        query: &[f32],
        entry_points: &[InternalId],
        ef: usize,
        layer: usize,
    ) -> Vec<(InternalId, f32)> {
        let mut visited = HashSet::new();
        let mut candidates: BinaryHeap<Candidate> = BinaryHeap::new();
        let mut results: BinaryHeap<FarCandidate> = BinaryHeap::new();

        for &ep in entry_points {
            let dist = self.distance(ep, query);
            visited.insert(ep);
            candidates.push(Candidate {
                distance: OrderedFloat(dist),
                internal_id: ep,
            });
            results.push(FarCandidate {
                distance: OrderedFloat(dist),
                internal_id: ep,
            });
        }

        while let Some(closest) = candidates.pop() {
            let worst_result = results.peek().map(|r| r.distance.0).unwrap_or(f32::MAX);
            if closest.distance.0 > worst_result {
                break;
            }

            let node = &self.nodes[closest.internal_id as usize];
            if layer < node.neighbors.len() {
                for &neighbor_id in &node.neighbors[layer] {
                    if visited.insert(neighbor_id) {
                        let dist = self.distance(neighbor_id, query);
                        let worst_result =
                            results.peek().map(|r| r.distance.0).unwrap_or(f32::MAX);

                        if results.len() < ef || dist < worst_result {
                            candidates.push(Candidate {
                                distance: OrderedFloat(dist),
                                internal_id: neighbor_id,
                            });
                            results.push(FarCandidate {
                                distance: OrderedFloat(dist),
                                internal_id: neighbor_id,
                            });
                            if results.len() > ef {
                                results.pop();
                            }
                        }
                    }
                }
            }
        }

        let mut result_vec: Vec<(InternalId, f32)> = results
            .into_iter()
            .map(|c| (c.internal_id, c.distance.0))
            .collect();
        result_vec.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
        result_vec
    }

    /// Select neighbors using the simple heuristic (select closest M).
    fn select_neighbors(
        &self,
        candidates: &[(InternalId, f32)],
        m: usize,
    ) -> Vec<InternalId> {
        let mut sorted = candidates.to_vec();
        sorted.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
        sorted.truncate(m);
        sorted.into_iter().map(|(id, _)| id).collect()
    }

    fn max_connections(&self, layer: usize) -> usize {
        if layer == 0 {
            self.config.m_max0
        } else {
            self.config.m
        }
    }

    fn insert_internal(&mut self, id: NodeId, vector: Vec<f32>) -> Result<()> {
        let level = self.random_level();
        let internal_id = self.nodes.len() as InternalId;

        self.id_to_internal.insert(id.as_u128(), internal_id);

        let mut neighbors = Vec::with_capacity(level + 1);
        for _ in 0..=level {
            neighbors.push(Vec::new());
        }

        self.nodes.push(HnswNode {
            id,
            vector,
            neighbors,
        });

        let entry_point = match self.entry_point {
            None => {
                self.entry_point = Some(internal_id);
                self.max_layer = level;
                return Ok(());
            }
            Some(ep) => ep,
        };

        let query = &self.nodes[internal_id as usize].vector.clone();

        // Phase 1: Traverse from top layer down to level+1, finding a single closest node.
        let mut current_ep = entry_point;
        for layer in (level + 1..=self.max_layer).rev() {
            let results = self.search_layer(query, &[current_ep], 1, layer);
            if let Some(&(closest, _)) = results.first() {
                current_ep = closest;
            }
        }

        // Phase 2: From level down to 0, find neighbors and connect.
        let top = level.min(self.max_layer);
        for layer in (0..=top).rev() {
            let results =
                self.search_layer(query, &[current_ep], self.config.ef_construction, layer);

            let m = self.max_connections(layer);
            let selected = self.select_neighbors(&results, m);

            // Set this node's neighbors at this layer
            self.nodes[internal_id as usize].neighbors[layer] = selected.clone();

            // Add bidirectional connections
            for &neighbor in &selected {
                let neighbor_idx = neighbor as usize;
                if layer >= self.nodes[neighbor_idx].neighbors.len() {
                    continue;
                }

                self.nodes[neighbor_idx].neighbors[layer].push(internal_id);

                // Prune if over max connections
                if self.nodes[neighbor_idx].neighbors[layer].len() > m {
                    let neighbor_vec = self.nodes[neighbor_idx].vector.clone();
                    let current_neighbors =
                        self.nodes[neighbor_idx].neighbors[layer].clone();
                    let metric = self.config.metric;
                    let mut candidates: Vec<(InternalId, f32)> = current_neighbors
                        .iter()
                        .map(|&n| {
                            let dist = metric.compute(
                                &neighbor_vec,
                                &self.nodes[n as usize].vector,
                            );
                            (n, dist)
                        })
                        .collect();
                    candidates.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
                    candidates.truncate(m);
                    self.nodes[neighbor_idx].neighbors[layer] =
                        candidates.into_iter().map(|(id, _)| id).collect();
                }
            }

            if let Some(&(closest, _)) = results.first() {
                current_ep = closest;
            }
        }

        // Update entry point if new node has higher level
        if level > self.max_layer {
            self.max_layer = level;
            self.entry_point = Some(internal_id);
        }

        Ok(())
    }
}

impl VectorIndex for HnswIndex {
    fn insert(&mut self, id: NodeId, embedding: &[f32]) -> Result<()> {
        if embedding.len() != self.dimensions {
            return Err(Error::DimensionMismatch {
                expected: self.dimensions,
                actual: embedding.len(),
            });
        }
        if self.id_to_internal.contains_key(&id.as_u128()) {
            // Update: remove old and re-insert
            let _ = self.remove(id);
        }
        self.insert_internal(id, embedding.to_vec())
    }

    fn remove(&mut self, id: NodeId) -> Result<bool> {
        // Lazy deletion: mark as removed. Full removal requires rebuild.
        // For now, just remove from the ID map so it won't appear in results.
        Ok(self.id_to_internal.remove(&id.as_u128()).is_some())
    }

    fn search(&self, query: &[f32], k: usize) -> Result<Vec<(NodeId, f32)>> {
        if query.len() != self.dimensions {
            return Err(Error::DimensionMismatch {
                expected: self.dimensions,
                actual: query.len(),
            });
        }

        let entry_point = match self.entry_point {
            Some(ep) => ep,
            None => return Ok(Vec::new()),
        };

        // Phase 1: Traverse from top to layer 1 with ef=1
        let mut current_ep = entry_point;
        for layer in (1..=self.max_layer).rev() {
            let results = self.search_layer(query, &[current_ep], 1, layer);
            if let Some(&(closest, _)) = results.first() {
                current_ep = closest;
            }
        }

        // Phase 2: Search layer 0 with ef_search
        let results = self.search_layer(query, &[current_ep], self.config.ef_search, 0);

        // Filter out removed nodes and take top k
        let valid_ids: HashSet<u128> = self.id_to_internal.keys().copied().collect();
        let mut filtered: Vec<(NodeId, f32)> = results
            .into_iter()
            .filter(|(internal_id, _)| {
                let node = &self.nodes[*internal_id as usize];
                valid_ids.contains(&node.id.as_u128())
            })
            .map(|(internal_id, dist)| (self.nodes[internal_id as usize].id, dist))
            .collect();

        filtered.truncate(k);
        Ok(filtered)
    }

    fn len(&self) -> usize {
        self.id_to_internal.len()
    }

    fn dimensions(&self) -> usize {
        self.dimensions
    }
}

// ── Persistence ──────────────────────────────────────────────────────────────

const MAGIC: &[u8; 8] = b"HNSWIDX1";

fn rd_u8(r: &mut impl std::io::Read) -> Result<u8> {
    let mut b = [0u8; 1];
    r.read_exact(&mut b)?;
    Ok(b[0])
}
fn rd_u32(r: &mut impl std::io::Read) -> Result<u32> {
    let mut b = [0u8; 4];
    r.read_exact(&mut b)?;
    Ok(u32::from_le_bytes(b))
}
fn rd_f32(r: &mut impl std::io::Read) -> Result<f32> {
    let mut b = [0u8; 4];
    r.read_exact(&mut b)?;
    Ok(f32::from_le_bytes(b))
}
fn rd_f64(r: &mut impl std::io::Read) -> Result<f64> {
    let mut b = [0u8; 8];
    r.read_exact(&mut b)?;
    Ok(f64::from_le_bytes(b))
}

impl HnswIndex {
    /// Persist the index to a binary file at `path`.
    ///
    /// ## Wire format (all little-endian)
    /// ```text
    /// magic[8] | version:u32 | dims:u32 | m:u32 | m_max0:u32
    /// ef_construction:u32 | ef_search:u32 | ml:f64 | metric:u8
    /// ep_valid:u8 | entry_point:u32 | max_layer:u32 | node_count:u32
    /// --- per node ---
    /// id:[u8;16] | live:u8 | dims×f32
    /// layer_count:u32 | --- per layer --- neighbor_count:u32 | neighbor_count×u32
    /// ```
    pub fn save(&self, path: impl AsRef<std::path::Path>) -> Result<()> {
        use std::io::{BufWriter, Write};
        let file = std::fs::File::create(path)?;
        let mut w = BufWriter::new(file);

        w.write_all(MAGIC)?;
        w.write_all(&1u32.to_le_bytes())?; // version

        w.write_all(&(self.dimensions as u32).to_le_bytes())?;
        w.write_all(&(self.config.m as u32).to_le_bytes())?;
        w.write_all(&(self.config.m_max0 as u32).to_le_bytes())?;
        w.write_all(&(self.config.ef_construction as u32).to_le_bytes())?;
        w.write_all(&(self.config.ef_search as u32).to_le_bytes())?;
        w.write_all(&self.config.ml.to_le_bytes())?;
        let metric_byte: u8 = match self.config.metric {
            DistanceMetric::L2 => 0,
            DistanceMetric::Cosine => 1,
            DistanceMetric::InnerProduct => 2,
        };
        w.write_all(&[metric_byte])?;

        match self.entry_point {
            None    => { w.write_all(&[0u8])?; w.write_all(&0u32.to_le_bytes())?; }
            Some(e) => { w.write_all(&[1u8])?; w.write_all(&e.to_le_bytes())?; }
        }
        w.write_all(&(self.max_layer as u32).to_le_bytes())?;
        w.write_all(&(self.nodes.len() as u32).to_le_bytes())?;

        let live_set: HashSet<InternalId> = self.id_to_internal.values().copied().collect();

        for (i, node) in self.nodes.iter().enumerate() {
            w.write_all(&node.id.to_bytes())?; // [u8; 16] LE u128
            w.write_all(&[live_set.contains(&(i as InternalId)) as u8])?;
            for &v in &node.vector { w.write_all(&v.to_le_bytes())?; }
            w.write_all(&(node.neighbors.len() as u32).to_le_bytes())?;
            for layer in &node.neighbors {
                w.write_all(&(layer.len() as u32).to_le_bytes())?;
                for &n in layer { w.write_all(&n.to_le_bytes())?; }
            }
        }

        w.flush()?;
        Ok(())
    }

    /// Restore an index from a file written by [`HnswIndex::save`].
    pub fn load(path: impl AsRef<std::path::Path>) -> Result<Self> {
        use std::io::{BufReader, Read};
        let file = std::fs::File::open(path)?;
        let mut r = BufReader::new(file);

        let mut magic = [0u8; 8];
        r.read_exact(&mut magic)?;
        if &magic != MAGIC {
            return Err(Error::Storage("invalid HNSW index magic".into()));
        }
        let _version = rd_u32(&mut r)?;

        let dimensions      = rd_u32(&mut r)? as usize;
        let m               = rd_u32(&mut r)? as usize;
        let m_max0          = rd_u32(&mut r)? as usize;
        let ef_construction = rd_u32(&mut r)? as usize;
        let ef_search       = rd_u32(&mut r)? as usize;
        let ml              = rd_f64(&mut r)?;
        let metric = match rd_u8(&mut r)? {
            0 => DistanceMetric::L2,
            1 => DistanceMetric::Cosine,
            _ => DistanceMetric::InnerProduct,
        };
        let config = HnswConfig { m, m_max0, ef_construction, ef_search, metric, ml };

        let ep_valid    = rd_u8(&mut r)?;
        let ep_raw      = rd_u32(&mut r)?;
        let entry_point = if ep_valid == 1 { Some(ep_raw) } else { None };
        let max_layer   = rd_u32(&mut r)? as usize;
        let node_count  = rd_u32(&mut r)? as usize;

        let mut nodes = Vec::with_capacity(node_count);
        let mut id_to_internal: HashMap<u128, InternalId> = HashMap::with_capacity(node_count);

        for i in 0..node_count {
            let mut id_bytes = [0u8; 16];
            r.read_exact(&mut id_bytes)?;
            let node_id = NodeId::from_bytes(id_bytes);
            let raw_id  = node_id.as_u128();

            let live = rd_u8(&mut r)?;
            if live == 1 {
                id_to_internal.insert(raw_id, i as InternalId);
            }

            let mut vector = Vec::with_capacity(dimensions);
            for _ in 0..dimensions { vector.push(rd_f32(&mut r)?); }

            let layer_count = rd_u32(&mut r)? as usize;
            let mut neighbors = Vec::with_capacity(layer_count);
            for _ in 0..layer_count {
                let nc = rd_u32(&mut r)? as usize;
                let mut layer = Vec::with_capacity(nc);
                for _ in 0..nc { layer.push(rd_u32(&mut r)?); }
                neighbors.push(layer);
            }

            nodes.push(HnswNode { id: node_id, vector, neighbors });
        }

        Ok(HnswIndex { config, dimensions, nodes, id_to_internal, entry_point, max_layer })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_vector(dims: usize, seed: f32) -> Vec<f32> {
        (0..dims).map(|i| (i as f32 + seed).sin()).collect()
    }

    #[test]
    fn insert_single() {
        let mut idx = HnswIndex::with_defaults(4);
        let id = NodeId::new();
        idx.insert(id, &[1.0, 0.0, 0.0, 0.0]).unwrap();
        assert_eq!(idx.len(), 1);
    }

    #[test]
    fn dimension_mismatch() {
        let mut idx = HnswIndex::with_defaults(4);
        let id = NodeId::new();
        assert!(idx.insert(id, &[1.0, 0.0]).is_err());
    }

    #[test]
    fn search_exact() {
        let mut idx = HnswIndex::with_defaults(4);
        let target = NodeId::new();
        idx.insert(target, &[1.0, 0.0, 0.0, 0.0]).unwrap();

        for i in 1..20 {
            let id = NodeId::new();
            idx.insert(id, &make_vector(4, i as f32)).unwrap();
        }

        let results = idx.search(&[1.0, 0.0, 0.0, 0.0], 1).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].0, target);
        assert!(results[0].1 < 1e-6); // distance should be ~0
    }

    #[test]
    fn search_returns_k_results() {
        let mut idx = HnswIndex::with_defaults(8);
        for i in 0..50 {
            let id = NodeId::new();
            idx.insert(id, &make_vector(8, i as f32)).unwrap();
        }

        let results = idx.search(&make_vector(8, 0.0), 10).unwrap();
        assert_eq!(results.len(), 10);

        // Results should be sorted by distance
        for w in results.windows(2) {
            assert!(w[0].1 <= w[1].1);
        }
    }

    #[test]
    fn remove_excludes_from_search() {
        let mut idx = HnswIndex::with_defaults(4);
        let target = NodeId::new();
        let decoy = NodeId::new();

        idx.insert(target, &[1.0, 0.0, 0.0, 0.0]).unwrap();
        idx.insert(decoy, &[0.99, 0.01, 0.0, 0.0]).unwrap();

        // Before removal, target should be closest
        let results = idx.search(&[1.0, 0.0, 0.0, 0.0], 1).unwrap();
        assert_eq!(results[0].0, target);

        // After removal
        idx.remove(target).unwrap();
        let results = idx.search(&[1.0, 0.0, 0.0, 0.0], 1).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].0, decoy);
    }

    #[test]
    fn empty_search() {
        let idx = HnswIndex::with_defaults(4);
        let results = idx.search(&[1.0, 0.0, 0.0, 0.0], 5).unwrap();
        assert!(results.is_empty());
    }

    #[test]
    fn recall_quality() {
        // Insert 200 random-ish vectors, verify recall is reasonable
        let dims = 32;
        let mut idx = HnswIndex::with_defaults(dims);
        let mut ids = Vec::new();

        for i in 0..200 {
            let id = NodeId::new();
            ids.push(id);
            idx.insert(id, &make_vector(dims, i as f32)).unwrap();
        }

        // Search for a vector we inserted
        let query = make_vector(dims, 42.0);
        let results = idx.search(&query, 5).unwrap();

        // The exact match should be in top-5
        assert!(results.iter().any(|(id, _)| *id == ids[42]));
    }

    #[test]
    fn save_and_load_roundtrip() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("hnsw.bin");

        let dims = 8;
        let mut original = HnswIndex::with_defaults(dims);
        let mut ids = Vec::new();

        for i in 0..30 {
            let id = NodeId::new();
            ids.push(id);
            original.insert(id, &make_vector(dims, i as f32)).unwrap();
        }

        // Remove one to test lazy-deletion survives reload
        original.remove(ids[5]).unwrap();

        original.save(&path).unwrap();
        let loaded = HnswIndex::load(&path).unwrap();

        // Same dimensions and live count
        assert_eq!(loaded.dimensions(), dims);
        assert_eq!(loaded.len(), original.len());

        // Removed id should still not appear
        let results = loaded.search(&make_vector(dims, 5.0), 30).unwrap();
        assert!(!results.iter().any(|(id, _)| *id == ids[5]));

        // Search quality preserved — exact match for query at index 10
        let query = make_vector(dims, 10.0);
        let results = loaded.search(&query, 5).unwrap();
        assert!(results.iter().any(|(id, _)| *id == ids[10]));
    }
}
