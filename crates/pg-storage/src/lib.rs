//! pg-storage: Custom storage engine for personal-graph.
//!
//! No SQLite. No wrappers. A page-oriented storage engine built from scratch:
//!
//! - **Pages**: Fixed-size 4KB pages as the unit of I/O.
//! - **Buffer Pool**: LRU-based page cache with dirty-page tracking.
//! - **WAL**: Write-ahead log for crash recovery.
//! - **B+Tree**: Ordered index over NodeId for O(log n) point lookups.
//! - **Store**: The top-level `GraphStore` that ties it all together.

pub mod btree;
pub mod buffer;
pub mod page;
pub mod store;
pub mod wal;

pub use store::GraphStore;
