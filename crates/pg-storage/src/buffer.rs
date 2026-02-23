//! Buffer pool manager.
//!
//! Caches pages in memory with an LRU eviction policy.
//! Dirty pages are flushed to the data file on eviction or checkpoint.

use crate::page::{Page, PageType, PAGE_SIZE};
use crate::wal::PageId;
use parking_lot::Mutex;
use pg_core::{Error, Result};
use std::collections::{HashMap, VecDeque};
use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};

/// Manages a pool of in-memory page frames backed by a data file.
pub struct BufferPool {
    inner: Mutex<BufferPoolInner>,
}

struct BufferPoolInner {
    file: File,
    #[allow(dead_code)]
    path: PathBuf,
    frames: HashMap<PageId, Frame>,
    lru: VecDeque<PageId>,
    capacity: usize,
    next_page_id: PageId,
}

struct Frame {
    page: Page,
    dirty: bool,
    pin_count: u32,
}

impl BufferPool {
    pub fn open(path: impl AsRef<Path>, capacity: usize) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(&path)?;

        let file_len = file.metadata()?.len();
        let next_page_id = if file_len == 0 {
            0
        } else {
            (file_len / PAGE_SIZE as u64) as PageId
        };

        Ok(Self {
            inner: Mutex::new(BufferPoolInner {
                file,
                path,
                frames: HashMap::with_capacity(capacity),
                lru: VecDeque::with_capacity(capacity),
                capacity,
                next_page_id,
            }),
        })
    }

    /// Allocate a new page. Returns its page_id.
    pub fn allocate(&self, page_type: PageType) -> Result<PageId> {
        let mut inner = self.inner.lock();
        let page_id = inner.next_page_id;
        inner.next_page_id += 1;

        let page = Page::init(page_id, page_type);

        // Write initial page to disk
        inner.write_page_to_disk(page_id, &page)?;

        // Cache it
        inner.insert_frame(page_id, page, true)?;
        Ok(page_id)
    }

    /// Fetch a page into the buffer pool. Returns a clone for reading.
    pub fn fetch(&self, page_id: PageId) -> Result<Page> {
        let mut inner = self.inner.lock();

        // Check cache first
        if let Some(frame) = inner.frames.get(&page_id) {
            let page = frame.page.clone();
            inner.touch_lru(page_id);
            return Ok(page);
        }

        // Read from disk
        let page = inner.read_page_from_disk(page_id)?;
        inner.insert_frame(page_id, page.clone(), false)?;
        Ok(page)
    }

    /// Write a modified page back to the buffer pool (marks dirty).
    pub fn write(&self, page_id: PageId, page: Page) -> Result<()> {
        let mut inner = self.inner.lock();

        if let Some(frame) = inner.frames.get_mut(&page_id) {
            frame.page = page;
            frame.dirty = true;
            inner.touch_lru(page_id);
            return Ok(());
        }

        // Not in cache — insert it
        inner.insert_frame(page_id, page, true)?;
        Ok(())
    }

    /// Flush all dirty pages to disk.
    pub fn flush_all(&self) -> Result<()> {
        let mut inner = self.inner.lock();
        let dirty_ids: Vec<PageId> = inner
            .frames
            .iter()
            .filter(|(_, f)| f.dirty)
            .map(|(id, _)| *id)
            .collect();

        for page_id in dirty_ids {
            // Split borrow: seal the page first, then write to disk
            if let Some(frame) = inner.frames.get_mut(&page_id) {
                frame.page.seal();
                frame.dirty = false;
            }
            if let Some(frame) = inner.frames.get(&page_id) {
                inner.write_page_to_disk(page_id, &frame.page)?;
            }
        }
        inner.file.sync_data()?;
        Ok(())
    }

    /// Total number of pages allocated (on disk).
    pub fn page_count(&self) -> PageId {
        self.inner.lock().next_page_id
    }

    /// Number of pages currently cached.
    pub fn cached_count(&self) -> usize {
        self.inner.lock().frames.len()
    }
}

impl BufferPoolInner {
    fn touch_lru(&mut self, page_id: PageId) {
        self.lru.retain(|&id| id != page_id);
        self.lru.push_back(page_id);
    }

    fn insert_frame(&mut self, page_id: PageId, page: Page, dirty: bool) -> Result<()> {
        // Evict if at capacity
        while self.frames.len() >= self.capacity {
            self.evict_one()?;
        }

        self.frames.insert(
            page_id,
            Frame {
                page,
                dirty,
                pin_count: 0,
            },
        );
        self.lru.push_back(page_id);
        Ok(())
    }

    fn evict_one(&mut self) -> Result<()> {
        // Find the LRU page that isn't pinned
        let victim = self
            .lru
            .iter()
            .find(|id| {
                self.frames
                    .get(id)
                    .map_or(false, |f| f.pin_count == 0)
            })
            .copied();

        let victim = victim.ok_or_else(|| Error::BufferPoolExhausted)?;
        self.lru.retain(|&id| id != victim);

        if let Some(frame) = self.frames.remove(&victim) {
            if frame.dirty {
                self.write_page_to_disk(victim, &frame.page)?;
            }
        }
        Ok(())
    }

    fn read_page_from_disk(&mut self, page_id: PageId) -> Result<Page> {
        let offset = page_id as u64 * PAGE_SIZE as u64;
        self.file.seek(SeekFrom::Start(offset))?;

        let mut page = Page::new();
        self.file.read_exact(&mut page.data)?;
        Ok(page)
    }

    fn write_page_to_disk(&self, page_id: PageId, page: &Page) -> Result<()> {
        use std::os::unix::fs::FileExt;
        let offset = page_id as u64 * PAGE_SIZE as u64;
        self.file.write_all_at(&page.data, offset)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn allocate_and_fetch() {
        let dir = tempfile::tempdir().unwrap();
        let pool = BufferPool::open(dir.path().join("test.db"), 16).unwrap();

        let pid = pool.allocate(PageType::Data).unwrap();
        assert_eq!(pid, 0);

        let page = pool.fetch(pid).unwrap();
        assert_eq!(page.page_id(), 0);
        assert_eq!(page.page_type(), PageType::Data);
    }

    #[test]
    fn write_and_read_back() {
        let dir = tempfile::tempdir().unwrap();
        let pool = BufferPool::open(dir.path().join("test.db"), 16).unwrap();

        let pid = pool.allocate(PageType::Data).unwrap();
        let mut page = pool.fetch(pid).unwrap();
        page.insert_cell(b"hello").unwrap();
        pool.write(pid, page).unwrap();

        let page2 = pool.fetch(pid).unwrap();
        assert_eq!(page2.read_cell(0).unwrap(), b"hello");
    }

    #[test]
    fn flush_persists() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");

        {
            let pool = BufferPool::open(&db_path, 16).unwrap();
            let pid = pool.allocate(PageType::Data).unwrap();
            let mut page = pool.fetch(pid).unwrap();
            page.insert_cell(b"persist me").unwrap();
            pool.write(pid, page).unwrap();
            pool.flush_all().unwrap();
        }

        // Reopen
        {
            let pool = BufferPool::open(&db_path, 16).unwrap();
            let page = pool.fetch(0).unwrap();
            assert_eq!(page.read_cell(0).unwrap(), b"persist me");
        }
    }

    #[test]
    fn eviction() {
        let dir = tempfile::tempdir().unwrap();
        let pool = BufferPool::open(dir.path().join("test.db"), 4).unwrap();

        // Allocate more pages than the pool can hold
        for _ in 0..8 {
            pool.allocate(PageType::Data).unwrap();
        }

        assert!(pool.cached_count() <= 4);

        // All pages should still be readable (from disk after eviction)
        for i in 0..8 {
            let page = pool.fetch(i).unwrap();
            assert_eq!(page.page_id(), i);
        }
    }
}
