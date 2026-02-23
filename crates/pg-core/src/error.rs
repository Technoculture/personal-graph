use thiserror::Error;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug, Error)]
pub enum Error {
    #[error("node not found: {0}")]
    NodeNotFound(crate::id::NodeId),

    #[error("edge not found: {0} -> {1}")]
    EdgeNotFound(crate::id::NodeId, crate::id::NodeId),

    #[error("duplicate node: {0}")]
    DuplicateNode(crate::id::NodeId),

    #[error("storage error: {0}")]
    Storage(String),

    #[error("serialization error: {0}")]
    Serialization(String),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("page full")]
    PageFull,

    #[error("buffer pool exhausted")]
    BufferPoolExhausted,

    #[error("wal error: {0}")]
    Wal(String),

    #[error("checksum mismatch: expected {expected}, got {actual}")]
    ChecksumMismatch { expected: u32, actual: u32 },

    #[error("vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("index error: {0}")]
    Index(String),

    #[error("capacity exceeded: {0}")]
    CapacityExceeded(String),

    #[error("invalid data: {0}")]
    InvalidData(String),
}

impl From<serde_json::Error> for Error {
    fn from(e: serde_json::Error) -> Self {
        Error::Serialization(e.to_string())
    }
}
