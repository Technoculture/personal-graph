//! Write-Ahead Log for crash recovery.
//!
//! Every mutation is first written to the WAL before being applied to pages.
//! On crash, replay the WAL to recover to a consistent state.
//!
//! WAL record format:
//!   [0..8]   LSN (log sequence number, u64)
//!   [8..12]  page_id (u32)
//!   [12..14] record_type (u16)
//!   [14..16] payload_len (u16)
//!   [16..N]  payload
//!   [N..N+4] CRC32 of [0..N]

use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use pg_core::{Error, Result};

pub type Lsn = u64;
pub type PageId = u32;

const RECORD_HEADER_SIZE: usize = 16;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u16)]
pub enum RecordType {
    /// Full page image (for initial writes / checkpoints).
    PageImage = 1,
    /// Insert a cell into a page.
    InsertCell = 2,
    /// Logical insert of a node.
    InsertNode = 3,
    /// Logical insert of an edge.
    InsertEdge = 4,
    /// Logical delete of a node.
    DeleteNode = 5,
    /// Logical delete of an edge.
    DeleteEdge = 6,
    /// Checkpoint marker.
    Checkpoint = 7,
}

impl RecordType {
    fn from_u16(v: u16) -> Option<Self> {
        match v {
            1 => Some(RecordType::PageImage),
            2 => Some(RecordType::InsertCell),
            3 => Some(RecordType::InsertNode),
            4 => Some(RecordType::InsertEdge),
            5 => Some(RecordType::DeleteNode),
            6 => Some(RecordType::DeleteEdge),
            7 => Some(RecordType::Checkpoint),
            _ => None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct WalRecord {
    pub lsn: Lsn,
    pub page_id: PageId,
    pub record_type: RecordType,
    pub payload: Vec<u8>,
}

impl WalRecord {
    fn serialize(&self) -> Vec<u8> {
        let payload_len = self.payload.len() as u16;
        let total = RECORD_HEADER_SIZE + self.payload.len() + 4; // +4 for CRC
        let mut buf = Vec::with_capacity(total);

        buf.extend_from_slice(&self.lsn.to_le_bytes());
        buf.extend_from_slice(&self.page_id.to_le_bytes());
        buf.extend_from_slice(&(self.record_type as u16).to_le_bytes());
        buf.extend_from_slice(&payload_len.to_le_bytes());
        buf.extend_from_slice(&self.payload);

        let crc = crc32fast::hash(&buf);
        buf.extend_from_slice(&crc.to_le_bytes());
        buf
    }

    fn deserialize(data: &[u8]) -> Result<(Self, usize)> {
        if data.len() < RECORD_HEADER_SIZE + 4 {
            return Err(Error::Wal("record too short".into()));
        }

        let lsn = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let page_id = u32::from_le_bytes(data[8..12].try_into().unwrap());
        let record_type_raw = u16::from_le_bytes(data[12..14].try_into().unwrap());
        let payload_len = u16::from_le_bytes(data[14..16].try_into().unwrap()) as usize;

        let total = RECORD_HEADER_SIZE + payload_len + 4;
        if data.len() < total {
            return Err(Error::Wal("incomplete record".into()));
        }

        let record_type = RecordType::from_u16(record_type_raw)
            .ok_or_else(|| Error::Wal(format!("unknown record type: {record_type_raw}")))?;

        let payload = data[RECORD_HEADER_SIZE..RECORD_HEADER_SIZE + payload_len].to_vec();

        // Verify CRC
        let stored_crc = u32::from_le_bytes(
            data[RECORD_HEADER_SIZE + payload_len..total]
                .try_into()
                .unwrap(),
        );
        let computed_crc = crc32fast::hash(&data[..RECORD_HEADER_SIZE + payload_len]);
        if stored_crc != computed_crc {
            return Err(Error::ChecksumMismatch {
                expected: stored_crc,
                actual: computed_crc,
            });
        }

        Ok((
            WalRecord {
                lsn,
                page_id,
                record_type,
                payload,
            },
            total,
        ))
    }
}

/// Write-ahead log.
pub struct Wal {
    path: PathBuf,
    writer: BufWriter<File>,
    next_lsn: Lsn,
}

impl Wal {
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .append(true)
            .open(&path)?;

        // Determine the next LSN by scanning existing records
        let next_lsn = Self::find_max_lsn(&path)?.map_or(1, |lsn| lsn + 1);

        Ok(Wal {
            path,
            writer: BufWriter::new(file),
            next_lsn,
        })
    }

    fn find_max_lsn(path: &Path) -> Result<Option<Lsn>> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len == 0 {
            return Ok(None);
        }

        let mut data = Vec::new();
        file.read_to_end(&mut data)?;

        let mut max_lsn = None;
        let mut offset = 0;
        while offset < data.len() {
            match WalRecord::deserialize(&data[offset..]) {
                Ok((record, size)) => {
                    max_lsn = Some(record.lsn);
                    offset += size;
                }
                Err(_) => break,
            }
        }
        Ok(max_lsn)
    }

    /// Append a record to the WAL. Returns the assigned LSN.
    pub fn append(&mut self, page_id: PageId, record_type: RecordType, payload: Vec<u8>) -> Result<Lsn> {
        let lsn = self.next_lsn;
        self.next_lsn += 1;

        let record = WalRecord {
            lsn,
            page_id,
            record_type,
            payload,
        };

        let bytes = record.serialize();
        self.writer.write_all(&bytes)?;
        Ok(lsn)
    }

    /// Flush the WAL to disk (fdatasync).
    pub fn sync(&mut self) -> Result<()> {
        use std::io::Write;
        self.writer.flush()?;
        self.writer.get_ref().sync_data()?;
        Ok(())
    }

    /// Read all records from the WAL file (for recovery).
    pub fn read_all(path: impl AsRef<Path>) -> Result<Vec<WalRecord>> {
        let mut file = File::open(path.as_ref())?;
        let mut data = Vec::new();
        file.read_to_end(&mut data)?;

        let mut records = Vec::new();
        let mut offset = 0;
        while offset < data.len() {
            match WalRecord::deserialize(&data[offset..]) {
                Ok((record, size)) => {
                    records.push(record);
                    offset += size;
                }
                Err(_) => break, // partial write at tail — normal after crash
            }
        }
        Ok(records)
    }

    /// Truncate the WAL (after a successful checkpoint).
    pub fn truncate(&mut self) -> Result<()> {
        use std::io::Write;
        self.writer.flush()?;
        let file = OpenOptions::new()
            .write(true)
            .truncate(true)
            .open(&self.path)?;
        self.writer = BufWriter::new(file);
        self.next_lsn = 1;
        Ok(())
    }

    pub fn current_lsn(&self) -> Lsn {
        self.next_lsn
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_roundtrip() {
        let record = WalRecord {
            lsn: 42,
            page_id: 7,
            record_type: RecordType::InsertNode,
            payload: b"test payload".to_vec(),
        };
        let bytes = record.serialize();
        let (recovered, size) = WalRecord::deserialize(&bytes).unwrap();
        assert_eq!(size, bytes.len());
        assert_eq!(recovered.lsn, 42);
        assert_eq!(recovered.page_id, 7);
        assert_eq!(recovered.record_type, RecordType::InsertNode);
        assert_eq!(recovered.payload, b"test payload");
    }

    #[test]
    fn wal_append_and_read() {
        let dir = tempfile::tempdir().unwrap();
        let wal_path = dir.path().join("test.wal");

        {
            let mut wal = Wal::open(&wal_path).unwrap();
            wal.append(0, RecordType::InsertNode, b"node-1".to_vec())
                .unwrap();
            wal.append(1, RecordType::InsertEdge, b"edge-1".to_vec())
                .unwrap();
            wal.sync().unwrap();
        }

        let records = Wal::read_all(&wal_path).unwrap();
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].payload, b"node-1");
        assert_eq!(records[1].payload, b"edge-1");
    }

    #[test]
    fn wal_lsn_continuity() {
        let dir = tempfile::tempdir().unwrap();
        let wal_path = dir.path().join("test.wal");

        {
            let mut wal = Wal::open(&wal_path).unwrap();
            let lsn1 = wal
                .append(0, RecordType::InsertNode, vec![])
                .unwrap();
            let lsn2 = wal
                .append(0, RecordType::InsertNode, vec![])
                .unwrap();
            assert_eq!(lsn1 + 1, lsn2);
            wal.sync().unwrap();
        }

        // Reopen and check LSN continues
        {
            let mut wal = Wal::open(&wal_path).unwrap();
            let lsn3 = wal
                .append(0, RecordType::InsertNode, vec![])
                .unwrap();
            assert_eq!(lsn3, 3);
        }
    }

    #[test]
    fn corrupted_record_detected() {
        let record = WalRecord {
            lsn: 1,
            page_id: 0,
            record_type: RecordType::InsertNode,
            payload: b"data".to_vec(),
        };
        let mut bytes = record.serialize();
        bytes[18] ^= 0xFF; // corrupt payload
        assert!(WalRecord::deserialize(&bytes).is_err());
    }
}
