# personal-graph

A graph database and vector search engine built from scratch in Rust. No SQLite wrappers, no embedded databases — a custom storage engine designed for building memory systems for AI applications.

## Architecture

```
crates/
  pg-core/      Core types: Node, Edge, PropertyMap, traits
  pg-storage/   Custom storage engine: pages, buffer pool, WAL, B+tree indexes
  pg-vector/    HNSW vector index with distance metrics (L2, cosine, inner product)
  pg-graph/     Graph engine: traversal, shortest path, similarity search
  pg-server/    HTTP API server (axum)
```

### What's built from scratch

- **Page-oriented storage**: 4KB slotted pages with cell pointer arrays, checksums
- **Buffer pool**: LRU page cache with dirty-page tracking and disk flush
- **Write-ahead log**: CRC32-protected WAL records for crash recovery
- **B+tree indexes**: NodeId -> page location, edge adjacency, label index
- **HNSW vector index**: Hierarchical Navigable Small World graph for approximate nearest neighbor search
- **Graph engine**: BFS/DFS traversal, shortest path, label filtering, similarity search

## Quick start

```rust
use pg_graph::PersonalGraph;
use pg_core::props;

let mut g = PersonalGraph::open("./my_graph")?
    .with_vector_index(384); // embedding dimensions

// Add nodes
let alice = g.add_node("Person", props! { "name" => "Alice" })?;
let bob = g.add_node("Person", props! { "name" => "Bob" })?;

// Add edges
g.add_edge(alice, bob, "knows", props! { "since" => 2020i64 })?;

// Add nodes with embeddings for similarity search
let doc = g.add_node_with_embedding(
    "Document",
    props! { "title" => "Graph Databases" },
    &embedding_vector,
)?;

// Vector similarity search
let results = g.search_similar(&query_vector, 10)?;

// Graph traversal
let path = g.shortest_path(alice, bob)?;
let neighborhood = g.bfs(alice, 3)?;

// Persistence
g.checkpoint()?;
```

## HTTP API server

```sh
cargo run --bin pg-server

# Environment variables:
#   PG_DATA_DIR=./pg_data     (default: ./pg_data)
#   PG_VECTOR_DIMS=384        (0 = disabled)
#   PG_LISTEN=0.0.0.0:3000    (default)
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/nodes` | Create a node |
| `GET` | `/nodes/{id}` | Get a node |
| `PUT` | `/nodes/{id}` | Update a node |
| `DELETE` | `/nodes/{id}` | Delete a node (cascades edges) |
| `GET` | `/nodes/{id}/edges` | Get all edges for a node |
| `GET` | `/nodes/{id}/neighbors` | Get neighbor node IDs |
| `GET` | `/nodes/{id}/traverse?max_depth=3` | BFS traversal |
| `POST` | `/edges` | Create an edge |
| `POST` | `/batch` | Batch insert nodes and edges |
| `GET` | `/search/label/{label}` | Find nodes by label |
| `POST` | `/search/vector` | Vector similarity search |
| `POST` | `/search/path` | Shortest path between two nodes |
| `GET` | `/stats` | Node/edge/vector counts |
| `GET` | `/health` | Health check |

## Building

```sh
cargo build --release
cargo test
```

## Tests

62 tests across all crates covering:
- Page layout, checksums, cell operations
- Buffer pool allocation, eviction, persistence
- WAL append, read, corruption detection, LSN continuity
- B+tree index CRUD, edge adjacency, label lookup
- HNSW insert, search, recall quality, dimension validation
- Graph engine CRUD, traversal, shortest path, batch operations
- Vector similarity search with distance thresholds

## License

MIT
