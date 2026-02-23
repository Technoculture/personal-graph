//! pg-storage: Custom storage engine for personal-graph.
//!
//! No SQLite. No wrappers. A page-oriented storage engine built from scratch:
//!
//! - **Pages**: Fixed-size 4KB pages as the unit of I/O.
//! - **Buffer Pool**: LRU-based page cache with dirty-page tracking.
//! - **WAL**: Write-ahead log for crash recovery.
//! - **B+Tree (in-memory)**: Fast in-memory ordered index (btree module).
//! - **B+Tree (on-disk)**: Durable ordered index over NodeId (disk_btree module).
//! - **MVCC**: Snapshot-isolation transaction manager (mvcc module).
//! - **Compaction**: Dead-cell reclamation for MVCC stores (compaction module).
//! - **Store**: The top-level `GraphStore` that ties it all together.

pub mod btree;
pub mod buffer;
pub mod compaction;
pub mod disk_btree;
pub mod mvcc;
pub mod page;
pub mod store;
pub mod wal;

pub use compaction::CompactionStats;
pub use mvcc::{TxManager, Transaction};
pub use store::GraphStore;
