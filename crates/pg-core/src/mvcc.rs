/// Transaction ID — a monotonically increasing u64.
/// TxId 0 is reserved; first real transaction is 1.
pub type TxId = u64;

/// A read snapshot: all cells created_at <= this value are visible
/// (unless also deleted_at <= this value by a committed tx).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Snapshot(pub TxId);

impl Snapshot {
    /// Is this cell version visible under this snapshot?
    ///
    /// A cell is visible when:
    ///   created_at <= snapshot  AND  (deleted_at == 0 OR deleted_at > snapshot)
    #[inline]
    pub fn is_visible(&self, created_at: TxId, deleted_at: TxId) -> bool {
        created_at <= self.0 && (deleted_at == 0 || deleted_at > self.0)
    }
}

/// MVCC cell header prepended to every on-disk cell payload (16 bytes).
#[derive(Debug, Clone, Copy)]
pub struct CellVersion {
    pub created_at: TxId,
    pub deleted_at: TxId, // 0 = not deleted
}

impl CellVersion {
    pub const SIZE: usize = 16;

    pub fn new(tx: TxId) -> Self {
        Self { created_at: tx, deleted_at: 0 }
    }

    pub fn to_bytes(&self) -> [u8; 16] {
        let mut b = [0u8; 16];
        b[0..8].copy_from_slice(&self.created_at.to_le_bytes());
        b[8..16].copy_from_slice(&self.deleted_at.to_le_bytes());
        b
    }

    pub fn from_bytes(b: &[u8]) -> Self {
        Self {
            created_at: u64::from_le_bytes(b[0..8].try_into().unwrap()),
            deleted_at: u64::from_le_bytes(b[8..16].try_into().unwrap()),
        }
    }

    pub fn is_dead(&self, min_active: TxId) -> bool {
        self.deleted_at != 0 && self.deleted_at <= min_active
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn visibility() {
        let snap = Snapshot(10);
        // created before snapshot, not deleted → visible
        assert!(snap.is_visible(5, 0));
        // created after snapshot → not visible
        assert!(!snap.is_visible(11, 0));
        // created before, deleted before snapshot → not visible
        assert!(!snap.is_visible(5, 9));
        // created before, deleted after snapshot → visible
        assert!(snap.is_visible(5, 11));
    }

    #[test]
    fn cell_version_roundtrip() {
        let cv = CellVersion { created_at: 42, deleted_at: 99 };
        let bytes = cv.to_bytes();
        let back = CellVersion::from_bytes(&bytes);
        assert_eq!(back.created_at, 42);
        assert_eq!(back.deleted_at, 99);
    }

    #[test]
    fn dead_cell() {
        let cv = CellVersion { created_at: 1, deleted_at: 5 };
        assert!(cv.is_dead(5));
        assert!(cv.is_dead(6));
        assert!(!cv.is_dead(4));
        assert!(!cv.is_dead(0));
    }
}
