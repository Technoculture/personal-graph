//! pg-server: HTTP API server for personal-graph.

mod api;

use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing_subscriber::EnvFilter;

use pg_graph::PersonalGraph;

pub type SharedGraph = Arc<Mutex<PersonalGraph>>;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("pg_server=info".parse()?))
        .init();

    let data_dir = std::env::var("PG_DATA_DIR").unwrap_or_else(|_| "./pg_data".into());
    let dimensions: usize = std::env::var("PG_VECTOR_DIMS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);

    let mut graph = PersonalGraph::open(&data_dir)?;
    if dimensions > 0 {
        graph = graph.with_vector_index(dimensions);
    }

    let state: SharedGraph = Arc::new(Mutex::new(graph));

    let app = api::router(state);

    let addr: SocketAddr = std::env::var("PG_LISTEN")
        .unwrap_or_else(|_| "0.0.0.0:3000".into())
        .parse()?;

    tracing::info!("personal-graph listening on {addr}");
    tracing::info!("data directory: {data_dir}");
    if dimensions > 0 {
        tracing::info!("vector index enabled: {dimensions} dimensions");
    }

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
