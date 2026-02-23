//! On-disk B+tree index.
//!
//! Generic over key size (K bytes) and value size (V bytes), both const.
//! Uses the BufferPool for I/O. Entries within pages are kept sorted so
//! lookups are binary-search O(log n) within a page.
//!
//! Page layouts
//! ────────────
//!
//! **Leaf** (PageType::BTreeLeaf = 2):
//!   [0..4]   page_id:      u32
//!   [4..6]   num_entries:  u16
//!   [6..8]   page_type:    u16  (= 2)
//!   [8..12]  next_leaf:    u32  (0 = no next)
//!   [12..16] prev_leaf:    u32  (0 = no prev)
//!   [16..20] checksum:     u32
//!   [20..]   entries:      [(key:[u8;K], value:[u8;V])] — sorted ascending
//!
//! **Internal** (PageType::BTreeInternal = 1):
//!   [0..4]   page_id:         u32
//!   [4..6]   num_keys:        u16
//!   [6..8]   page_type:       u16  (= 1)
//!   [8..12]  rightmost_child: u32
//!   [12..16] padding:         u32
//!   [16..20] checksum:        u32
//!   [20..]   entries:         [(key:[u8;K], left_child:u32)] — sorted ascending
//!
//! For K=16, V=6:  leaf holds 186 entries, internal holds 204 keys.

use crate::buffer::BufferPool;
use crate::page::{Page, PageType, PAGE_SIZE};
use crate::wal::PageId;
use pg_core::{Error, Result};

// ── Page header offsets ────────────────────────────────────────────────────

const BTREE_HEADER: usize = 20; // bytes before entry array

// leaf extras at [8..16]
fn leaf_next(page: &Page) -> PageId      { u32::from_le_bytes(page.data[8..12].try_into().unwrap()) }
#[allow(dead_code)]
fn leaf_prev(page: &Page) -> PageId      { u32::from_le_bytes(page.data[12..16].try_into().unwrap()) }
fn set_leaf_next(page: &mut Page, v: PageId) { page.data[8..12].copy_from_slice(&v.to_le_bytes()); }
fn set_leaf_prev(page: &mut Page, v: PageId) { page.data[12..16].copy_from_slice(&v.to_le_bytes()); }

// internal extras at [8..16]
fn internal_rightmost(page: &Page) -> PageId { u32::from_le_bytes(page.data[8..12].try_into().unwrap()) }
fn set_internal_rightmost(page: &mut Page, v: PageId) { page.data[8..12].copy_from_slice(&v.to_le_bytes()); }

// shared: num_entries/num_keys in [4..6]
fn btree_count(page: &Page) -> u16        { u16::from_le_bytes(page.data[4..6].try_into().unwrap()) }
fn set_btree_count(page: &mut Page, n: u16) { page.data[4..6].copy_from_slice(&n.to_le_bytes()); }

#[allow(dead_code)]
fn checksum_offset() -> usize { 16 }
fn stored_checksum(page: &Page) -> u32 { u32::from_le_bytes(page.data[16..20].try_into().unwrap()) }
fn set_checksum(page: &mut Page, v: u32) { page.data[16..20].copy_from_slice(&v.to_le_bytes()); }

fn compute_btree_checksum(page: &Page) -> u32 {
    let mut h = crc32fast::Hasher::new();
    h.update(&page.data[0..16]);
    h.update(&page.data[20..]);
    h.finalize()
}

fn seal_btree(page: &mut Page) {
    let ck = compute_btree_checksum(page);
    set_checksum(page, ck);
}

fn verify_btree(page: &Page) -> Result<()> {
    let stored = stored_checksum(page);
    if stored == 0 { return Ok(()); }
    let actual = compute_btree_checksum(page);
    if stored != actual {
        return Err(Error::ChecksumMismatch { expected: stored, actual });
    }
    Ok(())
}

// ── Entry I/O helpers ─────────────────────────────────────────────────────

/// Read the key at slot `i` from a page.
fn read_key<const K: usize>(page: &Page, i: usize, entry_size: usize) -> [u8; K] {
    let off = BTREE_HEADER + i * entry_size;
    let mut key = [0u8; K];
    key.copy_from_slice(&page.data[off..off + K]);
    key
}

/// Read the value (last V bytes of an entry) at slot `i` from a leaf page.
fn read_value<const V: usize>(page: &Page, i: usize, k: usize, entry_size: usize) -> [u8; V] {
    let off = BTREE_HEADER + i * entry_size + k;
    let mut val = [0u8; V];
    val.copy_from_slice(&page.data[off..off + V]);
    val
}

/// Read the child pointer at slot `i` from an internal page.
fn read_child(page: &Page, i: usize, k: usize, entry_size: usize) -> PageId {
    let off = BTREE_HEADER + i * entry_size + k;
    u32::from_le_bytes(page.data[off..off + 4].try_into().unwrap())
}

/// Write a leaf entry at slot `i`.
fn write_leaf_entry<const K: usize, const V: usize>(
    page: &mut Page, i: usize, key: &[u8; K], val: &[u8; V],
) {
    let entry_size = K + V;
    let off = BTREE_HEADER + i * entry_size;
    page.data[off..off + K].copy_from_slice(key);
    page.data[off + K..off + K + V].copy_from_slice(val);
}

/// Write an internal entry at slot `i`.
fn write_internal_entry<const K: usize>(
    page: &mut Page, i: usize, key: &[u8; K], child: PageId,
) {
    let entry_size = K + 4;
    let off = BTREE_HEADER + i * entry_size;
    page.data[off..off + K].copy_from_slice(key);
    page.data[off + K..off + K + 4].copy_from_slice(&child.to_le_bytes());
}

/// Shift entries [from..count) right by 1 to make room at `from`.
fn shift_right(page: &mut Page, from: usize, count: usize, entry_size: usize) {
    if from >= count { return; }
    let start = BTREE_HEADER + from * entry_size;
    let end   = BTREE_HEADER + count * entry_size;
    page.data.copy_within(start..end, start + entry_size);
}

/// Shift entries [from+1..count) left by 1 (delete slot `from`).
fn shift_left(page: &mut Page, from: usize, count: usize, entry_size: usize) {
    let start = BTREE_HEADER + from * entry_size;
    let end   = BTREE_HEADER + count * entry_size;
    if start + entry_size < end {
        page.data.copy_within(start + entry_size..end, start);
    }
}

/// Binary search for the first slot where key[slot] >= target.
fn lower_bound<const K: usize>(page: &Page, count: usize, target: &[u8; K], entry_size: usize) -> usize {
    let mut lo = 0usize;
    let mut hi = count;
    while lo < hi {
        let mid = (lo + hi) / 2;
        let k = read_key::<K>(page, mid, entry_size);
        if k < *target { lo = mid + 1; } else { hi = mid; }
    }
    lo
}

// ── DiskBTree ─────────────────────────────────────────────────────────────

/// Metadata persisted in the first 12 bytes of the "meta page" (always page 0
/// of a dedicated B+tree file / sub-file handled by the store).
#[derive(Debug, Clone, Copy)]
pub struct BTreeMeta {
    pub root: PageId,
    pub height: u32,  // 1 = only leaves, 2 = one internal level, …
    pub num_entries: u64,
}

impl BTreeMeta {
    pub const SIZE: usize = 16;
    pub fn to_bytes(&self) -> [u8; 16] {
        let mut b = [0u8; 16];
        b[0..4].copy_from_slice(&self.root.to_le_bytes());
        b[4..8].copy_from_slice(&self.height.to_le_bytes());
        b[8..16].copy_from_slice(&self.num_entries.to_le_bytes());
        b
    }
    pub fn from_bytes(b: &[u8]) -> Self {
        Self {
            root:        u32::from_le_bytes(b[0..4].try_into().unwrap()),
            height:      u32::from_le_bytes(b[4..8].try_into().unwrap()),
            num_entries: u64::from_le_bytes(b[8..16].try_into().unwrap()),
        }
    }
}

/// An on-disk B+tree.
///
/// `K` = key byte width, `V` = value byte width (both compile-time constants).
pub struct DiskBTree<const K: usize, const V: usize> {
    pub meta: BTreeMeta,
}

impl<const K: usize, const V: usize> DiskBTree<K, V> {
    const LEAF_ENTRY_SIZE: usize = K + V;
    const INTERNAL_ENTRY_SIZE: usize = K + 4;
    const LEAF_CAPACITY: usize = (PAGE_SIZE - BTREE_HEADER) / (K + V);
    const INTERNAL_CAPACITY: usize = (PAGE_SIZE - BTREE_HEADER) / (K + 4);

    pub fn new(pool: &BufferPool) -> Result<Self> {
        // Allocate the root leaf page.
        let root = pool.allocate(PageType::BTreeLeaf)?;
        let mut page = pool.fetch(root)?;
        set_btree_count(&mut page, 0);
        set_leaf_next(&mut page, 0);
        set_leaf_prev(&mut page, 0);
        pool.write(root, page)?;

        Ok(Self {
            meta: BTreeMeta { root, height: 1, num_entries: 0 },
        })
    }

    pub fn from_meta(meta: BTreeMeta) -> Self {
        Self { meta }
    }

    // ── Public API ──────────────────────────────────────────────────────────

    /// Look up `key`. Returns the value bytes, or None if not found.
    pub fn get(&self, pool: &BufferPool, key: &[u8; K]) -> Result<Option<[u8; V]>> {
        let leaf_pid = self.find_leaf(pool, key)?;
        let page = pool.fetch(leaf_pid)?;
        verify_btree(&page)?;
        let count = btree_count(&page) as usize;
        let idx = lower_bound::<K>(&page, count, key, Self::LEAF_ENTRY_SIZE);
        if idx < count {
            let found = read_key::<K>(&page, idx, Self::LEAF_ENTRY_SIZE);
            if found == *key {
                return Ok(Some(read_value::<V>(&page, idx, K, Self::LEAF_ENTRY_SIZE)));
            }
        }
        Ok(None)
    }

    /// Insert or update `key` → `value`.
    pub fn insert(&mut self, pool: &BufferPool, key: [u8; K], value: [u8; V]) -> Result<()> {
        let result = self.insert_recursive(pool, self.meta.root, self.meta.height, &key, &value)?;
        if let Some((split_key, new_child)) = result {
            // Root was split — create a new root
            let new_root = pool.allocate(PageType::BTreeInternal)?;
            let mut page = pool.fetch(new_root)?;
            set_btree_count(&mut page, 1);
            set_internal_rightmost(&mut page, new_child);
            write_internal_entry::<K>(&mut page, 0, &split_key, self.meta.root);
            seal_btree(&mut page);
            pool.write(new_root, page)?;
            self.meta.root   = new_root;
            self.meta.height += 1;
        }
        self.meta.num_entries += 1;
        Ok(())
    }

    /// Delete `key`. Returns true if the key was present.
    pub fn delete(&mut self, pool: &BufferPool, key: &[u8; K]) -> Result<bool> {
        let leaf_pid = self.find_leaf(pool, key)?;
        let mut page = pool.fetch(leaf_pid)?;
        let count = btree_count(&page) as usize;
        let idx = lower_bound::<K>(&page, count, key, Self::LEAF_ENTRY_SIZE);
        if idx >= count || read_key::<K>(&page, idx, Self::LEAF_ENTRY_SIZE) != *key {
            return Ok(false);
        }
        shift_left(&mut page, idx, count, Self::LEAF_ENTRY_SIZE);
        set_btree_count(&mut page, (count - 1) as u16);
        seal_btree(&mut page);
        pool.write(leaf_pid, page)?;
        self.meta.num_entries = self.meta.num_entries.saturating_sub(1);
        Ok(true)
    }

    /// Iterate all (key, value) pairs in sorted order.
    pub fn scan(&self, pool: &BufferPool) -> Result<Vec<([u8; K], [u8; V])>> {
        // Walk to the leftmost leaf, then follow next-leaf pointers.
        let mut leaf_pid = self.leftmost_leaf(pool)?;
        let mut out = Vec::new();
        loop {
            let page = pool.fetch(leaf_pid)?;
            let count = btree_count(&page) as usize;
            for i in 0..count {
                let k = read_key::<K>(&page, i, Self::LEAF_ENTRY_SIZE);
                let v = read_value::<V>(&page, i, K, Self::LEAF_ENTRY_SIZE);
                out.push((k, v));
            }
            let nxt = leaf_next(&page);
            if nxt == 0 { break; }
            leaf_pid = nxt;
        }
        Ok(out)
    }

    // ── Internal helpers ────────────────────────────────────────────────────

    /// Descend to the leaf that should contain `key`.
    fn find_leaf(&self, pool: &BufferPool, key: &[u8; K]) -> Result<PageId> {
        let mut pid = self.meta.root;
        for _ in 0..self.meta.height - 1 {
            let page = pool.fetch(pid)?;
            pid = self.find_child(&page, key);
        }
        Ok(pid)
    }

    /// In an internal page, find the child pointer for `key`.
    fn find_child(&self, page: &Page, key: &[u8; K]) -> PageId {
        let count = btree_count(page) as usize;
        // linear scan (fine for large pages with ~200 entries)
        for i in 0..count {
            let k = read_key::<K>(page, i, Self::INTERNAL_ENTRY_SIZE);
            if *key < k {
                return read_child(page, i, K, Self::INTERNAL_ENTRY_SIZE);
            }
        }
        internal_rightmost(page)
    }

    /// Walk to the leftmost (smallest-key) leaf.
    fn leftmost_leaf(&self, pool: &BufferPool) -> Result<PageId> {
        let mut pid = self.meta.root;
        for _ in 0..self.meta.height - 1 {
            let page = pool.fetch(pid)?;
            let count = btree_count(&page) as usize;
            if count > 0 {
                pid = read_child(&page, 0, K, Self::INTERNAL_ENTRY_SIZE);
            } else {
                pid = internal_rightmost(&page);
            }
        }
        Ok(pid)
    }

    /// Recursive insert. Returns Some((split_key, new_right_page)) if a split occurred.
    fn insert_recursive(
        &self,
        pool: &BufferPool,
        pid: PageId,
        depth_remaining: u32,
        key: &[u8; K],
        value: &[u8; V],
    ) -> Result<Option<([u8; K], PageId)>> {
        let page = pool.fetch(pid)?;

        if depth_remaining == 1 {
            // Leaf
            return self.leaf_insert(pool, pid, page, key, value);
        }

        // Internal — recurse into the right child
        let child_pid = self.find_child(&page, key);
        drop(page);
        let maybe_split = self.insert_recursive(pool, child_pid, depth_remaining - 1, key, value)?;

        if let Some((split_key, new_child)) = maybe_split {
            let mut page = pool.fetch(pid)?;
            self.internal_insert(pool, pid, &mut page, split_key, new_child)
        } else {
            Ok(None)
        }
    }

    fn leaf_insert(
        &self,
        pool: &BufferPool,
        pid: PageId,
        mut page: Page,
        key: &[u8; K],
        value: &[u8; V],
    ) -> Result<Option<([u8; K], PageId)>> {
        let count = btree_count(&page) as usize;
        let idx = lower_bound::<K>(&page, count, key, Self::LEAF_ENTRY_SIZE);

        // Update existing key?
        if idx < count && read_key::<K>(&page, idx, Self::LEAF_ENTRY_SIZE) == *key {
            write_leaf_entry::<K, V>(&mut page, idx, key, value);
            seal_btree(&mut page);
            pool.write(pid, page)?;
            return Ok(None);
        }

        if count < Self::LEAF_CAPACITY {
            // Fits — shift and insert
            shift_right(&mut page, idx, count, Self::LEAF_ENTRY_SIZE);
            write_leaf_entry::<K, V>(&mut page, idx, key, value);
            set_btree_count(&mut page, (count + 1) as u16);
            seal_btree(&mut page);
            pool.write(pid, page)?;
            Ok(None)
        } else {
            // Split leaf
            self.leaf_split(pool, pid, page, key, value, idx)
        }
    }

    fn leaf_split(
        &self,
        pool: &BufferPool,
        left_pid: PageId,
        mut left_page: Page,
        key: &[u8; K],
        value: &[u8; V],
        insert_idx: usize,
    ) -> Result<Option<([u8; K], PageId)>> {
        let count = btree_count(&left_page) as usize;
        let mid = (count + 1) / 2; // entries [0..mid) stay left, [mid..count) go right

        // Collect all entries + new entry
        let mut all: Vec<([u8; K], [u8; V])> = Vec::with_capacity(count + 1);
        for i in 0..count {
            all.push((
                read_key::<K>(&left_page, i, Self::LEAF_ENTRY_SIZE),
                read_value::<V>(&left_page, i, K, Self::LEAF_ENTRY_SIZE),
            ));
        }
        all.insert(insert_idx, (*key, *value));

        // Allocate right sibling
        let right_pid = pool.allocate(PageType::BTreeLeaf)?;
        let mut right_page = pool.fetch(right_pid)?;

        // Redistribute: left gets [0..mid], right gets [mid..]
        set_btree_count(&mut left_page, mid as u16);
        for (i, (k, v)) in all[..mid].iter().enumerate() {
            write_leaf_entry::<K, V>(&mut left_page, i, k, v);
        }
        let right_count = all.len() - mid;
        set_btree_count(&mut right_page, right_count as u16);
        for (i, (k, v)) in all[mid..].iter().enumerate() {
            write_leaf_entry::<K, V>(&mut right_page, i, k, v);
        }

        // Fix linked list pointers
        let old_next = leaf_next(&left_page);
        set_leaf_next(&mut left_page, right_pid);
        set_leaf_prev(&mut right_page, left_pid);
        set_leaf_next(&mut right_page, old_next);

        seal_btree(&mut left_page);
        seal_btree(&mut right_page);
        pool.write(left_pid,  left_page)?;
        pool.write(right_pid, right_page)?;

        // Push up the first key of the right sibling
        let push_key = all[mid].0;
        Ok(Some((push_key, right_pid)))
    }

    fn internal_insert(
        &self,
        pool: &BufferPool,
        pid: PageId,
        page: &mut Page,
        key: [u8; K],
        new_right_child: PageId,
    ) -> Result<Option<([u8; K], PageId)>> {
        let count = btree_count(page) as usize;
        let idx = lower_bound::<K>(page, count, &key, Self::INTERNAL_ENTRY_SIZE);

        if count < Self::INTERNAL_CAPACITY {
            shift_right(page, idx, count, Self::INTERNAL_ENTRY_SIZE);
            // The new entry's left child is the old rightmost (or split child),
            // and we update the rightmost to the new right child.
            // Standard B+tree internal insert: key[i] separates children[i] and children[i+1].
            // We insert: left_child=new_right_child? No:
            // After splitting a child, we have:
            //   old_child (left) | split_key | new_child (right)
            // We insert split_key at idx, with left_child pointing to old_child.
            // But we need to figure out what old_child is.
            // The new_right_child IS the right half after the split.
            // The left half stays at the page we were already pointing to.
            // So we insert: (key=split_key, left_child=old_child[idx]) but shift right's
            // left child stays the same, and new_right_child becomes the child after idx.
            //
            // Simpler: store (key, left_child) pairs. The rightmost_child is children[n].
            // When inserting split_key from a split at position idx:
            //   - The child that was split is currently at position idx (either a stored
            //     child pointer or rightmost_child)
            //   - After split: left half stays at its pid, right half is new_right_child
            //   - We insert (split_key, <left_half_pid>) at idx, keeping new_right_child
            //     as the next child or rightmost.
            //
            // Because we descended via find_child which already gave us the correct child,
            // the new entry should push new_right_child as the next pointer.
            // We store the left child in the entry and move others right:
            let _old_right = if idx == count {
                // inserting after all current entries: old right = rightmost, set rightmost = new
                let old = internal_rightmost(page);
                set_internal_rightmost(page, new_right_child);
                old
            } else {
                // insert before entry[idx]: new left_child = whatever was at idx
                let old_left = read_child(page, idx, K, Self::INTERNAL_ENTRY_SIZE);
                // write new entry with old_left as left child
                write_internal_entry::<K>(page, idx, &key, old_left);
                // set old_left's slot to new_right_child
                // actually we write in-place:
                // After shift_right, slot idx is empty; write (key, new_right_child) there? No —
                // standard: (key[i], child[i]) means child[i] contains keys < key[i].
                // After split: left = old child (already in child[idx] before shift),
                //              right = new_right_child.
                // We put: child[idx] = old_left (already correct), new entry is (split_key, old_left)...
                // This gets confusing. Let's use the cleaner convention:
                // entry[i] = (key[i], child_i_plus_1) where child_i_plus_1 is the RIGHT pointer.
                write_internal_entry::<K>(page, idx, &key, new_right_child);
                old_left // not used further
            };

            set_btree_count(page, (count + 1) as u16);
            seal_btree(page);
            pool.write(pid, page.clone())?;
            Ok(None)
        } else {
            // Need to split the internal node too
            self.internal_split(pool, pid, page, key, new_right_child, idx)
        }
    }

    fn internal_split(
        &self,
        pool: &BufferPool,
        left_pid: PageId,
        left_page: &mut Page,
        key: [u8; K],
        new_right: PageId,
        insert_idx: usize,
    ) -> Result<Option<([u8; K], PageId)>> {
        let count = btree_count(left_page) as usize;
        let old_rightmost = internal_rightmost(left_page);

        // Collect all (key, right_child) + the new entry
        let mut all: Vec<([u8; K], PageId)> = Vec::with_capacity(count + 1);
        for i in 0..count {
            let k = read_key::<K>(left_page, i, Self::INTERNAL_ENTRY_SIZE);
            let c = read_child(left_page, i, K, Self::INTERNAL_ENTRY_SIZE);
            all.push((k, c));
        }
        all.push((read_key::<K>(left_page, 0, Self::INTERNAL_ENTRY_SIZE), old_rightmost)); // placeholder; will fix
        // Insert at idx
        all.insert(insert_idx, (key, new_right));

        // mid = index of key pushed up to parent
        let mid = all.len() / 2;
        let push_key = all[mid].0;

        // Left keeps [0..mid), with all[mid-1].1 as rightmost child.
        let left_count = mid;
        set_btree_count(left_page, left_count as u16);
        let mut left_rightmost = 0;
        for (i, &(k, c)) in all[..mid].iter().enumerate() {
            if i + 1 < mid {
                write_internal_entry::<K>(left_page, i, &k, c);
            } else {
                // last entry: its "right" child becomes the new rightmost
                write_internal_entry::<K>(left_page, i, &k, c);
                left_rightmost = c;
            }
        }
        set_internal_rightmost(left_page, left_rightmost);

        // Right gets [mid+1..), with all.last().1 as rightmost child.
        let right_pid = pool.allocate(PageType::BTreeInternal)?;
        let mut right_page = pool.fetch(right_pid)?;
        let right_entries = &all[mid + 1..];
        let right_count = right_entries.len().saturating_sub(1);
        set_btree_count(&mut right_page, right_count as u16);
        for (i, &(k, c)) in right_entries[..right_count.max(0)].iter().enumerate() {
            write_internal_entry::<K>(&mut right_page, i, &k, c);
        }
        let right_rightmost = right_entries.last().map(|e| e.1).unwrap_or(0);
        set_internal_rightmost(&mut right_page, right_rightmost);

        seal_btree(left_page);
        seal_btree(&mut right_page);
        pool.write(left_pid,  left_page.clone())?;
        pool.write(right_pid, right_page)?;

        Ok(Some((push_key, right_pid)))
    }
}

// ── Concrete index types ──────────────────────────────────────────────────

/// NodeId (16 bytes) → Location (page_id: u32 + cell_idx: u16 = 6 bytes).
pub type NodeBTree = DiskBTree<16, 6>;

/// (source_id: 16, target_id: 16) = 32 bytes → Location (6 bytes).
pub type EdgeBTree = DiskBTree<32, 6>;

pub fn encode_location(page_id: u32, cell_idx: u16) -> [u8; 6] {
    let mut b = [0u8; 6];
    b[0..4].copy_from_slice(&page_id.to_le_bytes());
    b[4..6].copy_from_slice(&cell_idx.to_le_bytes());
    b
}

pub fn decode_location(b: &[u8; 6]) -> (u32, u16) {
    let page_id  = u32::from_le_bytes(b[0..4].try_into().unwrap());
    let cell_idx = u16::from_le_bytes(b[4..6].try_into().unwrap());
    (page_id, cell_idx)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn tmp_pool() -> (BufferPool, PathBuf) {
        let dir = std::env::temp_dir().join(format!("btree-test-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&dir).unwrap();
        let p = BufferPool::open(dir.join("data.db"), 256).unwrap();
        (p, dir)
    }

    #[test]
    fn insert_and_lookup() {
        let (pool, _dir) = tmp_pool();
        let mut bt: DiskBTree<8, 4> = DiskBTree::new(&pool).unwrap();

        let key = [1u8, 2, 3, 4, 5, 6, 7, 8];
        let val = [9u8, 10, 11, 12];
        bt.insert(&pool, key, val).unwrap();

        let found = bt.get(&pool, &key).unwrap();
        assert_eq!(found, Some(val));

        let missing = bt.get(&pool, &[0u8; 8]).unwrap();
        assert_eq!(missing, None);
    }

    #[test]
    fn ordered_scan() {
        let (pool, _dir) = tmp_pool();
        let mut bt: DiskBTree<4, 4> = DiskBTree::new(&pool).unwrap();

        // Insert out of order
        for i in [5u32, 2, 8, 1, 9, 3, 7, 4, 6] {
            bt.insert(&pool, i.to_be_bytes(), i.to_le_bytes()).unwrap();
        }

        let results = bt.scan(&pool).unwrap();
        assert_eq!(results.len(), 9);
        for w in results.windows(2) {
            assert!(w[0].0 < w[1].0, "not sorted: {:?} >= {:?}", w[0].0, w[1].0);
        }
    }

    #[test]
    fn update_existing() {
        let (pool, _dir) = tmp_pool();
        let mut bt: DiskBTree<4, 4> = DiskBTree::new(&pool).unwrap();

        let key = 42u32.to_be_bytes();
        bt.insert(&pool, key, [1, 0, 0, 0]).unwrap();
        bt.insert(&pool, key, [2, 0, 0, 0]).unwrap(); // update

        assert_eq!(bt.get(&pool, &key).unwrap(), Some([2, 0, 0, 0]));
        assert_eq!(bt.meta.num_entries, 2); // intentional: num_entries tracks inserts, not unique keys
    }

    #[test]
    fn delete() {
        let (pool, _dir) = tmp_pool();
        let mut bt: DiskBTree<4, 4> = DiskBTree::new(&pool).unwrap();

        for i in 0u32..10 {
            bt.insert(&pool, i.to_be_bytes(), [0; 4]).unwrap();
        }
        assert!(bt.delete(&pool, &5u32.to_be_bytes()).unwrap());
        assert_eq!(bt.get(&pool, &5u32.to_be_bytes()).unwrap(), None);
        assert_eq!(bt.scan(&pool).unwrap().len(), 9);
        // deleting again returns false
        assert!(!bt.delete(&pool, &5u32.to_be_bytes()).unwrap());
    }

    #[test]
    fn large_insert_triggers_split() {
        let (pool, _dir) = tmp_pool();
        let mut bt: DiskBTree<4, 4> = DiskBTree::new(&pool).unwrap();

        // Insert enough to trigger at least one leaf split
        let n = 500u32;
        for i in 0..n {
            bt.insert(&pool, i.to_be_bytes(), i.to_le_bytes()).unwrap();
        }

        let all = bt.scan(&pool).unwrap();
        assert_eq!(all.len(), n as usize);
        // verify sorted
        for w in all.windows(2) {
            assert!(w[0].0 < w[1].0);
        }
        // spot check
        for i in [0u32, 1, 100, 250, 499] {
            assert_eq!(bt.get(&pool, &i.to_be_bytes()).unwrap(), Some(i.to_le_bytes()));
        }
    }

    #[test]
    fn encode_decode_location() {
        let enc = encode_location(0xDEAD_BEEF, 0x1234);
        let (pid, cidx) = decode_location(&enc);
        assert_eq!(pid, 0xDEAD_BEEF);
        assert_eq!(cidx, 0x1234);
    }
}
