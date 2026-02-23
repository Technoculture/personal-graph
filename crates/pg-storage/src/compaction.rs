//! Compaction — reclaim disk space used by dead (MVCC-deleted) cells.
//!
//! ## How it works
//!
//! Every on-disk cell written by the MVCC-aware store is prefixed with a
//! 16-byte [`CellVersion`] header (`created_at | deleted_at`).  When a node
//! or edge is logically deleted the header is updated in-place: `deleted_at`
//! is set to the deleting transaction's TxId.  The cell payload is left intact
//! so concurrent readers at earlier snapshots can still see it.
//!
//! Compaction scans every page and drops cells whose `deleted_at <= min_active`,
//! i.e. cells that no live or future snapshot will ever read again.  It then
//! writes back a fresh, compact page and updates the in-memory index.
//!
//! ## Integration with GraphStore
//!
//! `compact_page` is a low-level helper that operates on a single [`Page`].
//! `GraphStore::compact` calls it for every page and rebuilds affected indexes.

use crate::buffer::BufferPool;
use crate::page::{Page, PageType};
use crate::wal::{Wal, RecordType};
use pg_core::mvcc::{CellVersion, TxId};
use pg_core::error::Result;

// ── Page-level compaction ────────────────────────────────────────────────────

/// Result of compacting a single page.
pub struct CompactionResult {
    /// Number of dead cells removed.
    pub cells_removed: usize,
    /// Whether the page changed at all.
    pub modified: bool,
}

/// Compact one page in-place: remove all cells whose MVCC header marks them
/// dead relative to `min_active`.
///
/// A cell is considered MVCC-versioned if it is at least `CellVersion::SIZE`
/// bytes long (16 bytes). Cells shorter than that are treated as live.
///
/// Returns a [`CompactionResult`] indicating how many cells were pruned.
pub fn compact_page(page: &mut Page, min_active: TxId) -> CompactionResult {
    let cell_count = page.cell_count();
    let mut live_cells: Vec<Vec<u8>> = Vec::with_capacity(cell_count as usize);
    let mut cells_removed = 0usize;

    for i in 0..cell_count {
        if let Some(data) = page.read_cell(i) {
            if data.len() >= CellVersion::SIZE {
                let cv = CellVersion::from_bytes(&data[..CellVersion::SIZE]);
                if cv.is_dead(min_active) {
                    cells_removed += 1;
                    continue; // skip dead cell
                }
            }
            live_cells.push(data.to_vec());
        }
    }

    if cells_removed == 0 {
        return CompactionResult { cells_removed: 0, modified: false };
    }

    // Rebuild the page with only live cells.
    let page_type = page.page_type();
    let page_id = page.page_id();
    *page = Page::init(page_id, page_type);
    for cell in &live_cells {
        // insert_cell is infallible here because we started with a valid page
        // and we're writing back fewer bytes than were there before.
        let _ = page.insert_cell(cell);
    }

    CompactionResult { cells_removed, modified: true }
}

/// Statistics returned by a full-store compaction pass.
#[derive(Debug, Default, Clone)]
pub struct CompactionStats {
    pub pages_scanned: usize,
    pub pages_modified: usize,
    pub cells_removed: usize,
}

/// Compact all data and edge pages in the buffer pool.
///
/// Dirty modified pages are immediately flushed; a WAL sync is issued after
/// the pass completes.
///
/// The caller is responsible for rebuilding in-memory indexes after this
/// returns (since physical cell positions may change).  In practice
/// `GraphStore::compact` calls `rebuild_indexes` automatically.
pub fn compact_store(
    buffer: &BufferPool,
    wal: &mut Wal,
    min_active: TxId,
) -> Result<CompactionStats> {
    let mut stats = CompactionStats::default();
    let page_count = buffer.page_count();

    for pid in 0..page_count {
        let page_type = {
            let p = buffer.fetch(pid)?;
            p.page_type()
        };

        // Only compact data pages (nodes) and BTreeLeaf pages (edges).
        match page_type {
            PageType::Data | PageType::BTreeLeaf => {}
            _ => continue,
        }

        stats.pages_scanned += 1;

        let mut page = buffer.fetch(pid)?;
        let result = compact_page(&mut page, min_active);

        if result.modified {
            stats.pages_modified += 1;
            stats.cells_removed += result.cells_removed;

            // WAL: write a page-image record for crash safety before modifying.
            wal.append(pid, RecordType::PageImage, page.data.to_vec())?;

            buffer.write(pid, page)?;
        }
    }

    wal.sync()?;
    Ok(stats)
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::page::{Page, PageType};
    use pg_core::mvcc::CellVersion;

    fn make_versioned_cell(created_at: TxId, deleted_at: TxId, payload: &[u8]) -> Vec<u8> {
        let cv = CellVersion { created_at, deleted_at };
        let mut data = cv.to_bytes().to_vec();
        data.extend_from_slice(payload);
        data
    }

    #[test]
    fn compact_removes_dead_cells() {
        let mut page = Page::init(0, PageType::Data);

        // Live: created=1, not deleted
        let live = make_versioned_cell(1, 0, b"live-data");
        // Dead: deleted_at=3 <= min_active=5
        let dead = make_versioned_cell(1, 3, b"dead-data");
        // Live: deleted_at=6 > min_active=5
        let future_alive = make_versioned_cell(1, 6, b"future-data");

        page.insert_cell(&live).unwrap();
        page.insert_cell(&dead).unwrap();
        page.insert_cell(&future_alive).unwrap();
        assert_eq!(page.cell_count(), 3);

        let result = compact_page(&mut page, 5);
        assert_eq!(result.cells_removed, 1);
        assert!(result.modified);
        assert_eq!(page.cell_count(), 2);
    }

    #[test]
    fn compact_preserves_unversioned_cells() {
        let mut page = Page::init(0, PageType::Data);

        // Short cell — treated as live (no CellVersion header)
        page.insert_cell(b"short").unwrap();

        let result = compact_page(&mut page, 999);
        assert_eq!(result.cells_removed, 0);
        assert!(!result.modified);
        assert_eq!(page.cell_count(), 1);
    }

    #[test]
    fn compact_no_dead_cells_noop() {
        let mut page = Page::init(0, PageType::Data);
        let live = make_versioned_cell(1, 0, b"alive");
        page.insert_cell(&live).unwrap();

        let result = compact_page(&mut page, 100);
        assert!(!result.modified);
    }

    #[test]
    fn compact_all_dead_empties_page() {
        let mut page = Page::init(0, PageType::Data);
        let dead1 = make_versioned_cell(1, 2, b"dead-1");
        let dead2 = make_versioned_cell(1, 3, b"dead-2");
        page.insert_cell(&dead1).unwrap();
        page.insert_cell(&dead2).unwrap();

        let result = compact_page(&mut page, 10);
        assert_eq!(result.cells_removed, 2);
        assert!(result.modified);
        assert_eq!(page.cell_count(), 0);
    }
}
