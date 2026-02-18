//! Fixed-size page layout.
//!
//! Every page is PAGE_SIZE bytes. The first bytes are a header,
//! then a cell pointer array grows forward, and cell data grows backward
//! from the end of the page (slotted-page design, like Postgres/SQLite).

use crate::wal::PageId;
use pg_core::Error;

pub const PAGE_SIZE: usize = 4096;
const HEADER_SIZE: usize = 16;
// Header layout (16 bytes):
//   [0..4]   page_id (u32)
//   [4..6]   cell_count (u16)
//   [6..8]   free_start (u16) — offset where next cell pointer goes
//   [8..10]  free_end (u16)   — offset where next cell data starts (grows down)
//   [10..12] page_type (u16)  — 0=data, 1=btree_internal, 2=btree_leaf, 3=overflow
//   [12..16] checksum (u32)

const CELL_PTR_SIZE: usize = 4; // (offset: u16, length: u16)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u16)]
pub enum PageType {
    Data = 0,
    BTreeInternal = 1,
    BTreeLeaf = 2,
    Overflow = 3,
}

impl PageType {
    fn from_u16(v: u16) -> Self {
        match v {
            1 => PageType::BTreeInternal,
            2 => PageType::BTreeLeaf,
            3 => PageType::Overflow,
            _ => PageType::Data,
        }
    }
}

/// A fixed-size page with slotted layout.
#[derive(Clone)]
pub struct Page {
    pub data: [u8; PAGE_SIZE],
}

impl Default for Page {
    fn default() -> Self {
        Self::new()
    }
}

impl Page {
    pub fn new() -> Self {
        let mut page = Page {
            data: [0u8; PAGE_SIZE],
        };
        // Initialize free_start right after header
        page.set_free_start(HEADER_SIZE as u16);
        // Initialize free_end at the end of the page
        page.set_free_end(PAGE_SIZE as u16);
        page
    }

    pub fn init(page_id: PageId, page_type: PageType) -> Self {
        let mut page = Self::new();
        page.set_page_id(page_id);
        page.set_page_type(page_type);
        page
    }

    // --- Header accessors ---

    pub fn page_id(&self) -> PageId {
        u32::from_le_bytes(self.data[0..4].try_into().unwrap())
    }

    pub fn set_page_id(&mut self, id: PageId) {
        self.data[0..4].copy_from_slice(&id.to_le_bytes());
    }

    pub fn cell_count(&self) -> u16 {
        u16::from_le_bytes(self.data[4..6].try_into().unwrap())
    }

    fn set_cell_count(&mut self, n: u16) {
        self.data[4..6].copy_from_slice(&n.to_le_bytes());
    }

    pub fn free_start(&self) -> u16 {
        u16::from_le_bytes(self.data[6..8].try_into().unwrap())
    }

    fn set_free_start(&mut self, v: u16) {
        self.data[6..8].copy_from_slice(&v.to_le_bytes());
    }

    pub fn free_end(&self) -> u16 {
        u16::from_le_bytes(self.data[8..10].try_into().unwrap())
    }

    fn set_free_end(&mut self, v: u16) {
        self.data[8..10].copy_from_slice(&v.to_le_bytes());
    }

    pub fn page_type(&self) -> PageType {
        PageType::from_u16(u16::from_le_bytes(self.data[10..12].try_into().unwrap()))
    }

    fn set_page_type(&mut self, t: PageType) {
        self.data[10..12].copy_from_slice(&(t as u16).to_le_bytes());
    }

    pub fn stored_checksum(&self) -> u32 {
        u32::from_le_bytes(self.data[12..16].try_into().unwrap())
    }

    fn set_checksum(&mut self, c: u32) {
        self.data[12..16].copy_from_slice(&c.to_le_bytes());
    }

    // --- Free space ---

    pub fn free_space(&self) -> usize {
        let start = self.free_start() as usize;
        let end = self.free_end() as usize;
        if end > start {
            end - start
        } else {
            0
        }
    }

    /// Can this page fit a cell of `len` bytes?
    pub fn can_fit(&self, len: usize) -> bool {
        // Need space for both the cell pointer and the cell data
        self.free_space() >= len + CELL_PTR_SIZE
    }

    // --- Cell operations ---

    /// Insert a cell into this page. Returns the cell index.
    pub fn insert_cell(&mut self, payload: &[u8]) -> pg_core::Result<u16> {
        let needed = payload.len() + CELL_PTR_SIZE;
        if self.free_space() < needed {
            return Err(Error::PageFull);
        }

        // Allocate cell data from the end
        let new_end = self.free_end() as usize - payload.len();
        self.data[new_end..new_end + payload.len()].copy_from_slice(payload);
        self.set_free_end(new_end as u16);

        // Write cell pointer (offset, length) at free_start
        let ptr_offset = self.free_start() as usize;
        let cell_offset = new_end as u16;
        let cell_length = payload.len() as u16;
        self.data[ptr_offset..ptr_offset + 2].copy_from_slice(&cell_offset.to_le_bytes());
        self.data[ptr_offset + 2..ptr_offset + 4].copy_from_slice(&cell_length.to_le_bytes());
        self.set_free_start((ptr_offset + CELL_PTR_SIZE) as u16);

        let idx = self.cell_count();
        self.set_cell_count(idx + 1);
        Ok(idx)
    }

    /// Read a cell by its index.
    pub fn read_cell(&self, idx: u16) -> Option<&[u8]> {
        if idx >= self.cell_count() {
            return None;
        }
        let ptr_offset = HEADER_SIZE + (idx as usize) * CELL_PTR_SIZE;
        let cell_offset =
            u16::from_le_bytes(self.data[ptr_offset..ptr_offset + 2].try_into().unwrap()) as usize;
        let cell_length =
            u16::from_le_bytes(self.data[ptr_offset + 2..ptr_offset + 4].try_into().unwrap())
                as usize;
        Some(&self.data[cell_offset..cell_offset + cell_length])
    }

    /// Compute CRC32 over everything except the checksum field itself.
    pub fn compute_checksum(&self) -> u32 {
        let mut hasher = crc32fast::Hasher::new();
        hasher.update(&self.data[0..12]);
        hasher.update(&self.data[16..]);
        hasher.finalize()
    }

    /// Write the correct checksum into the header.
    pub fn seal(&mut self) {
        let ck = self.compute_checksum();
        self.set_checksum(ck);
    }

    /// Verify that the stored checksum matches.
    pub fn verify(&self) -> pg_core::Result<()> {
        let expected = self.stored_checksum();
        if expected == 0 {
            return Ok(()); // unsealed page
        }
        let actual = self.compute_checksum();
        if expected != actual {
            return Err(Error::ChecksumMismatch { expected, actual });
        }
        Ok(())
    }
}

impl std::fmt::Debug for Page {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Page")
            .field("page_id", &self.page_id())
            .field("type", &self.page_type())
            .field("cells", &self.cell_count())
            .field("free_space", &self.free_space())
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_page() {
        let page = Page::init(0, PageType::Data);
        assert_eq!(page.cell_count(), 0);
        assert_eq!(page.page_type(), PageType::Data);
        assert!(page.free_space() > 4000);
    }

    #[test]
    fn insert_and_read() {
        let mut page = Page::init(1, PageType::Data);
        let payload = b"hello world";
        let idx = page.insert_cell(payload).unwrap();
        assert_eq!(idx, 0);
        assert_eq!(page.cell_count(), 1);
        assert_eq!(page.read_cell(0).unwrap(), payload);
    }

    #[test]
    fn multiple_cells() {
        let mut page = Page::init(2, PageType::Data);
        for i in 0..10 {
            let data = format!("cell-{i}");
            page.insert_cell(data.as_bytes()).unwrap();
        }
        assert_eq!(page.cell_count(), 10);
        for i in 0..10 {
            let expected = format!("cell-{i}");
            assert_eq!(page.read_cell(i).unwrap(), expected.as_bytes());
        }
    }

    #[test]
    fn page_full() {
        let mut page = Page::init(3, PageType::Data);
        let big = vec![0xFFu8; PAGE_SIZE]; // too big
        assert!(page.insert_cell(&big).is_err());
    }

    #[test]
    fn checksum() {
        let mut page = Page::init(4, PageType::Data);
        page.insert_cell(b"test data").unwrap();
        page.seal();
        page.verify().unwrap();

        // Corrupt a byte
        page.data[100] ^= 0xFF;
        assert!(page.verify().is_err());
    }
}
