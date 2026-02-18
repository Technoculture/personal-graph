use ordered_float::OrderedFloat;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// A typed property value stored on nodes and edges.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Property {
    Null,
    Bool(bool),
    Int(i64),
    Float(OrderedFloat<f64>),
    String(String),
    Bytes(Vec<u8>),
    List(Vec<Property>),
    Map(PropertyMap),
}

/// An ordered map of string keys to property values.
pub type PropertyMap = BTreeMap<String, Property>;

impl Property {
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Property::String(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Property::Int(n) => Some(*n),
            _ => None,
        }
    }

    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Property::Float(f) => Some(f.into_inner()),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Property::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn is_null(&self) -> bool {
        matches!(self, Property::Null)
    }
}

impl From<&str> for Property {
    fn from(s: &str) -> Self {
        Property::String(s.to_owned())
    }
}

impl From<String> for Property {
    fn from(s: String) -> Self {
        Property::String(s)
    }
}

impl From<i64> for Property {
    fn from(n: i64) -> Self {
        Property::Int(n)
    }
}

impl From<f64> for Property {
    fn from(f: f64) -> Self {
        Property::Float(OrderedFloat(f))
    }
}

impl From<bool> for Property {
    fn from(b: bool) -> Self {
        Property::Bool(b)
    }
}

impl From<Vec<u8>> for Property {
    fn from(b: Vec<u8>) -> Self {
        Property::Bytes(b)
    }
}

/// Convenience macro for building a PropertyMap inline.
#[macro_export]
macro_rules! props {
    ($($key:expr => $val:expr),* $(,)?) => {{
        let mut map = $crate::property::PropertyMap::new();
        $(map.insert($key.to_string(), $crate::property::Property::from($val));)*
        map
    }};
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn property_conversions() {
        assert_eq!(Property::from("hello").as_str(), Some("hello"));
        assert_eq!(Property::from(42i64).as_i64(), Some(42));
        assert_eq!(Property::from(3.14f64).as_f64(), Some(3.14));
        assert_eq!(Property::from(true).as_bool(), Some(true));
    }

    #[test]
    fn props_macro() {
        let map = props! {
            "name" => "alice",
            "age" => 30i64,
        };
        assert_eq!(map.get("name").unwrap().as_str(), Some("alice"));
        assert_eq!(map.get("age").unwrap().as_i64(), Some(30));
    }

    #[test]
    fn json_roundtrip() {
        let prop = Property::from("test");
        let json = serde_json::to_string(&prop).unwrap();
        let back: Property = serde_json::from_str(&json).unwrap();
        assert_eq!(prop, back);
    }
}
