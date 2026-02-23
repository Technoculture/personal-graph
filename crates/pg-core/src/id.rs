use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

/// A globally unique node identifier.
///
/// Internally a 128-bit UUID stored as two u64s for cache-friendly comparison.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NodeId(u128);

impl NodeId {
    pub fn new() -> Self {
        Self(Uuid::new_v4().as_u128())
    }

    pub fn from_u128(v: u128) -> Self {
        Self(v)
    }

    pub fn as_u128(&self) -> u128 {
        self.0
    }

    pub fn to_bytes(&self) -> [u8; 16] {
        self.0.to_le_bytes()
    }

    pub fn from_bytes(bytes: [u8; 16]) -> Self {
        Self(u128::from_le_bytes(bytes))
    }
}

impl Default for NodeId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Debug for NodeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "NodeId({})", Uuid::from_u128(self.0))
    }
}

impl fmt::Display for NodeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", Uuid::from_u128(self.0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_bytes() {
        let id = NodeId::new();
        let bytes = id.to_bytes();
        let recovered = NodeId::from_bytes(bytes);
        assert_eq!(id, recovered);
    }

    #[test]
    fn uniqueness() {
        let a = NodeId::new();
        let b = NodeId::new();
        assert_ne!(a, b);
    }
}
