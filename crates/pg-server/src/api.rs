//! REST API handlers.

use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{delete, get, post, put},
    Json, Router,
};
use pg_core::graph::{Edge, Node};
use pg_core::id::NodeId;
use pg_core::property::PropertyMap;
use serde::{Deserialize, Serialize};

use crate::SharedGraph;

pub fn router(state: SharedGraph) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/nodes", post(create_node))
        .route("/nodes/{id}", get(get_node))
        .route("/nodes/{id}", put(update_node))
        .route("/nodes/{id}", delete(delete_node))
        .route("/nodes/{id}/edges", get(get_node_edges))
        .route("/nodes/{id}/neighbors", get(get_neighbors))
        .route("/nodes/{id}/traverse", get(traverse_bfs))
        .route("/edges", post(create_edge))
        .route("/batch", post(insert_batch))
        .route("/search/label/{label}", get(search_by_label))
        .route("/search/vector", post(search_vector))
        .route("/search/path", post(search_path))
        .route("/stats", get(stats))
        .with_state(state)
}

async fn health() -> &'static str {
    "ok"
}

// ---- Request/Response types ----

#[derive(Deserialize)]
struct CreateNodeRequest {
    label: String,
    properties: PropertyMap,
    embedding: Option<Vec<f32>>,
}

#[derive(Serialize)]
struct CreateNodeResponse {
    id: String,
}

#[derive(Deserialize)]
struct UpdateNodeRequest {
    label: String,
    properties: PropertyMap,
}

#[derive(Deserialize)]
struct CreateEdgeRequest {
    source: String,
    target: String,
    label: String,
    properties: PropertyMap,
}

#[derive(Deserialize)]
struct VectorSearchRequest {
    query: Vec<f32>,
    k: usize,
    max_distance: Option<f32>,
}

#[derive(Serialize)]
struct VectorSearchResult {
    node: NodeResponse,
    distance: f32,
}

#[derive(Serialize)]
struct NodeResponse {
    id: String,
    label: String,
    properties: PropertyMap,
}

#[derive(Serialize)]
struct EdgeResponse {
    source: String,
    target: String,
    label: String,
    properties: PropertyMap,
}

#[derive(Deserialize)]
struct PathRequest {
    source: String,
    target: String,
}

#[derive(Serialize)]
struct PathResponse {
    found: bool,
    nodes: Vec<String>,
    edges: Vec<EdgeResponse>,
}

#[derive(Serialize)]
struct StatsResponse {
    node_count: usize,
    edge_count: usize,
    vector_count: usize,
}

#[derive(Deserialize)]
struct TraverseQuery {
    max_depth: Option<usize>,
}

#[derive(Serialize)]
struct TraverseResult {
    node: NodeResponse,
    depth: usize,
}

#[derive(Deserialize)]
struct BatchRequest {
    nodes: Vec<CreateNodeRequest>,
    edges: Vec<CreateEdgeRequest>,
}

#[derive(Serialize)]
struct BatchResponse {
    node_ids: Vec<String>,
}

// ---- Helpers ----

fn parse_node_id(s: &str) -> Result<NodeId, StatusCode> {
    let uuid: u128 = uuid::Uuid::parse_str(s)
        .map_err(|_| StatusCode::BAD_REQUEST)?
        .as_u128();
    Ok(NodeId::from_u128(uuid))
}

fn node_to_response(node: &Node) -> NodeResponse {
    NodeResponse {
        id: node.id.to_string(),
        label: node.data.label.clone(),
        properties: node.data.properties.clone(),
    }
}

fn edge_to_response(edge: &Edge) -> EdgeResponse {
    EdgeResponse {
        source: edge.source.to_string(),
        target: edge.target.to_string(),
        label: edge.data.label.clone(),
        properties: edge.data.properties.clone(),
    }
}

// ---- Handlers ----

async fn create_node(
    State(graph): State<SharedGraph>,
    Json(req): Json<CreateNodeRequest>,
) -> Result<(StatusCode, Json<CreateNodeResponse>), StatusCode> {
    let mut g = graph.lock().await;
    let id = if let Some(embedding) = req.embedding {
        g.add_node_with_embedding(req.label, req.properties, &embedding)
    } else {
        g.add_node(req.label, req.properties)
    }
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok((
        StatusCode::CREATED,
        Json(CreateNodeResponse {
            id: id.to_string(),
        }),
    ))
}

async fn get_node(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
) -> Result<Json<NodeResponse>, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let g = graph.lock().await;
    let node = g
        .get_node(node_id)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .ok_or(StatusCode::NOT_FOUND)?;
    Ok(Json(node_to_response(&node)))
}

async fn update_node(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
    Json(req): Json<UpdateNodeRequest>,
) -> Result<StatusCode, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let mut g = graph.lock().await;
    g.update_node(node_id, req.label, req.properties)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(StatusCode::NO_CONTENT)
}

async fn delete_node(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let mut g = graph.lock().await;
    g.delete_node(node_id)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(StatusCode::NO_CONTENT)
}

async fn get_node_edges(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
) -> Result<Json<Vec<EdgeResponse>>, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let g = graph.lock().await;
    let mut edges = g
        .out_edges(node_id)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    edges.extend(
        g.in_edges(node_id)
            .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?,
    );
    Ok(Json(edges.iter().map(edge_to_response).collect()))
}

async fn get_neighbors(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
) -> Result<Json<Vec<String>>, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let g = graph.lock().await;
    let neighbors = g
        .neighbors(node_id)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(Json(neighbors.iter().map(|n| n.to_string()).collect()))
}

async fn traverse_bfs(
    State(graph): State<SharedGraph>,
    Path(id): Path<String>,
    axum::extract::Query(query): axum::extract::Query<TraverseQuery>,
) -> Result<Json<Vec<TraverseResult>>, StatusCode> {
    let node_id = parse_node_id(&id)?;
    let max_depth = query.max_depth.unwrap_or(3);
    let g = graph.lock().await;
    let results = g
        .bfs(node_id, max_depth)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(Json(
        results
            .iter()
            .map(|(node, depth)| TraverseResult {
                node: node_to_response(node),
                depth: *depth,
            })
            .collect(),
    ))
}

async fn create_edge(
    State(graph): State<SharedGraph>,
    Json(req): Json<CreateEdgeRequest>,
) -> Result<StatusCode, StatusCode> {
    let source = parse_node_id(&req.source)?;
    let target = parse_node_id(&req.target)?;
    let mut g = graph.lock().await;
    g.add_edge(source, target, req.label, req.properties)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(StatusCode::CREATED)
}

async fn insert_batch(
    State(graph): State<SharedGraph>,
    Json(req): Json<BatchRequest>,
) -> Result<(StatusCode, Json<BatchResponse>), StatusCode> {
    let mut g = graph.lock().await;
    let mut node_ids = Vec::new();

    // Insert nodes first to get their IDs
    for node_req in &req.nodes {
        let id = if let Some(ref embedding) = node_req.embedding {
            g.add_node_with_embedding(
                node_req.label.clone(),
                node_req.properties.clone(),
                embedding,
            )
        } else {
            g.add_node(node_req.label.clone(), node_req.properties.clone())
        }
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
        node_ids.push(id.to_string());
    }

    // Then insert edges
    for edge_req in &req.edges {
        let source = parse_node_id(&edge_req.source)?;
        let target = parse_node_id(&edge_req.target)?;
        g.add_edge(
            source,
            target,
            edge_req.label.clone(),
            edge_req.properties.clone(),
        )
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    }

    Ok((StatusCode::CREATED, Json(BatchResponse { node_ids })))
}

async fn search_by_label(
    State(graph): State<SharedGraph>,
    Path(label): Path<String>,
) -> Result<Json<Vec<NodeResponse>>, StatusCode> {
    let g = graph.lock().await;
    let nodes = g
        .find_by_label(&label)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(Json(nodes.iter().map(node_to_response).collect()))
}

async fn search_vector(
    State(graph): State<SharedGraph>,
    Json(req): Json<VectorSearchRequest>,
) -> Result<Json<Vec<VectorSearchResult>>, StatusCode> {
    let g = graph.lock().await;
    let results = if let Some(max_dist) = req.max_distance {
        g.search_within_distance(&req.query, max_dist, req.k)
    } else {
        g.search_similar(&req.query, req.k)
    }
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(
        results
            .iter()
            .map(|r| VectorSearchResult {
                node: node_to_response(&r.node),
                distance: r.distance,
            })
            .collect(),
    ))
}

async fn search_path(
    State(graph): State<SharedGraph>,
    Json(req): Json<PathRequest>,
) -> Result<Json<PathResponse>, StatusCode> {
    let source = parse_node_id(&req.source)?;
    let target = parse_node_id(&req.target)?;
    let g = graph.lock().await;
    match g
        .shortest_path(source, target)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
    {
        Some(path) => Ok(Json(PathResponse {
            found: true,
            nodes: path.nodes.iter().map(|n| n.to_string()).collect(),
            edges: path.edges.iter().map(edge_to_response).collect(),
        })),
        None => Ok(Json(PathResponse {
            found: false,
            nodes: vec![],
            edges: vec![],
        })),
    }
}

async fn stats(State(graph): State<SharedGraph>) -> Result<Json<StatsResponse>, StatusCode> {
    let g = graph.lock().await;
    Ok(Json(StatsResponse {
        node_count: g.node_count().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?,
        edge_count: g.edge_count().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?,
        vector_count: g.vector_count(),
    }))
}
