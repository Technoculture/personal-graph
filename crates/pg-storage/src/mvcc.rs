//! MVCC Transaction Manager.
//!
//! Provides snapshot-isolation read transactions and MVCC write transactions.
//! Every write stamps cells with a `CellVersion { created_at, deleted_at }`.
//!
//! Compaction uses `min_active()` to find the oldest live snapshot; any cell
//! whose `deleted_at <= min_active` is unreachable by all current and future
//! readers and may be reclaimed.

use pg_core::mvcc::{Snapshot, TxId};
use std::collections::BTreeSet;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU64, Ordering};

// ── Global monotonic counter ─────────────────────────────────────────────────

static NEXT_TX_ID: AtomicU64 = AtomicU64::new(1);

fn alloc_tx_id() -> TxId {
    NEXT_TX_ID.fetch_add(1, Ordering::SeqCst)
}

// ── TxManager ────────────────────────────────────────────────────────────────

struct Inner {
    /// Currently open (not yet committed or aborted) transactions.
    active: BTreeSet<TxId>,
    /// Highest committed TxId.  New snapshots read up to this point.
    committed_horizon: TxId,
}

/// Per-database transaction manager.
///
/// Clone is cheap — it's an `Arc` wrapper.
#[derive(Clone)]
pub struct TxManager {
    inner: Arc<Mutex<Inner>>,
}

impl TxManager {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(Inner {
                active: BTreeSet::new(),
                committed_horizon: 0,
            })),
        }
    }

    /// Begin a new read-write transaction. Returns its `TxId`.
    pub fn begin(&self) -> TxId {
        let tx = alloc_tx_id();
        self.inner.lock().unwrap().active.insert(tx);
        tx
    }

    /// Commit a transaction.
    ///
    /// Advances `committed_horizon` so its writes become visible to future
    /// snapshots.
    pub fn commit(&self, tx: TxId) {
        let mut g = self.inner.lock().unwrap();
        g.active.remove(&tx);
        if tx > g.committed_horizon {
            g.committed_horizon = tx;
        }
    }

    /// Abort a transaction.  Its writes remain invisible forever.
    pub fn abort(&self, tx: TxId) {
        self.inner.lock().unwrap().active.remove(&tx);
    }

    /// Snapshot valid right now — sees all committed writes so far.
    pub fn snapshot(&self) -> Snapshot {
        Snapshot(self.inner.lock().unwrap().committed_horizon)
    }

    /// The oldest TxId still active.
    ///
    /// Any cell with `deleted_at <= min_active()` is invisible to all current
    /// and future readers — safe to reclaim.
    pub fn min_active(&self) -> TxId {
        let g = self.inner.lock().unwrap();
        g.active
            .iter()
            .next()
            .copied()
            .unwrap_or(g.committed_horizon.saturating_add(1))
    }

    /// `true` if there are no open transactions.
    pub fn is_idle(&self) -> bool {
        self.inner.lock().unwrap().active.is_empty()
    }
}

impl Default for TxManager {
    fn default() -> Self {
        Self::new()
    }
}

// ── RAII transaction guard ────────────────────────────────────────────────────

/// Automatically aborts on drop if not explicitly committed.
pub struct Transaction<'a> {
    manager: &'a TxManager,
    pub id: TxId,
    committed: bool,
}

impl<'a> Transaction<'a> {
    pub fn begin(manager: &'a TxManager) -> Self {
        Self {
            id: manager.begin(),
            manager,
            committed: false,
        }
    }

    pub fn commit(mut self) {
        self.manager.commit(self.id);
        self.committed = true;
    }
}

impl Drop for Transaction<'_> {
    fn drop(&mut self) {
        if !self.committed {
            self.manager.abort(self.id);
        }
    }
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn begin_commit_advances_horizon() {
        let tm = TxManager::new();
        assert_eq!(tm.snapshot().0, 0);

        let tx = tm.begin();
        assert!(tx >= 1);
        tm.commit(tx);

        assert!(tm.snapshot().0 >= tx);
    }

    #[test]
    fn aborted_tx_not_visible() {
        let tm = TxManager::new();
        let tx = tm.begin();
        tm.abort(tx);
        // horizon stays at 0 because we aborted without committing
        assert_eq!(tm.snapshot().0, 0);
    }

    #[test]
    fn min_active_with_open_tx() {
        let tm = TxManager::new();
        let tx1 = tm.begin();
        let tx2 = tm.begin();
        // min_active must be the smaller of the two
        assert_eq!(tm.min_active(), tx1);
        tm.commit(tx1);
        assert_eq!(tm.min_active(), tx2);
        tm.commit(tx2);
        // no open txs: min_active should be > committed_horizon
        assert!(tm.is_idle());
    }

    #[test]
    fn raii_auto_abort() {
        let tm = TxManager::new();
        {
            let _guard = Transaction::begin(&tm);
            // dropped without commit → abort
        }
        assert!(tm.is_idle());
        assert_eq!(tm.snapshot().0, 0); // nothing committed
    }

    #[test]
    fn raii_commit() {
        let tm = TxManager::new();
        let snap_before = tm.snapshot();
        {
            let guard = Transaction::begin(&tm);
            let id = guard.id;
            guard.commit();
            assert!(tm.snapshot().0 >= id);
        }
        assert!(tm.snapshot().0 > snap_before.0);
    }
}
