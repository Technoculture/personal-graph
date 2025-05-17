import json
from typing import Any, Callable, Dict, List, Optional, Union

from personal_graph.embeddings import EmbeddingsModel, OpenAIEmbeddingClient
from personal_graph.models import Edge, Node
from personal_graph.database.db import DB

try:
    import psycopg
except Exception:  # pragma: no cover - dependency not available in tests
    psycopg = None  # type: ignore

CursorExecFunction = Callable[[Any, Any], Any]


class Postgres(DB):
    """Simple PostgreSQL backend storing embeddings via pgvector."""

    def __init__(
        self,
        *,
        dsn: str = "",
        embedding_dimension: int = 384,
        embedding_model: Optional[EmbeddingsModel] = None,
    ) -> None:
        super().__init__()
        self.dsn = dsn
        if embedding_model is None:
            embedding_model = OpenAIEmbeddingClient(
                dimensions=embedding_dimension
            ).get_embedding_model()
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

    def __eq__(self, other: object) -> bool:  # pragma: no cover - simple
        return isinstance(other, Postgres) and self.dsn == other.dsn

    def __repr__(self) -> str:  # pragma: no cover - simple
        return f"Postgres(dsn='{self.dsn}', embedding_dimension={self.embedding_dimension})"

    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        if psycopg is None:  # pragma: no cover - library missing in tests
            raise ImportError("psycopg package is required for Postgres backend")
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                result = cursor_exec_fn(cur, conn)
                conn.commit()
        return result

    def save(self) -> None:
        if hasattr(self, "_connection"):
            self._connection.commit()

    def initialize(self) -> None:
        def _init(cur, conn) -> None:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT,
                    attributes JSONB,
                    embedding vector(%s),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                (self.embedding_dimension,),
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    id SERIAL PRIMARY KEY,
                    source TEXT REFERENCES nodes(id) ON DELETE CASCADE,
                    target TEXT REFERENCES nodes(id) ON DELETE CASCADE,
                    label TEXT,
                    attributes JSONB,
                    embedding vector(%s),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                (self.embedding_dimension,),
            )
            conn.commit()

        self.atomic(_init)

    def _node_embedding(self, attribute: Dict[str, Any]) -> List[float]:
        return self.embedding_model.get_embedding(json.dumps(attribute))

    def _edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict[str, Any]
    ) -> List[float]:
        data = {
            "source": source,
            "target": target,
            "label": label,
            "attributes": attributes,
        }
        return self.embedding_model.get_embedding(json.dumps(data))

    def fetch_node_embed_id(self, node_id: Any):
        def _fetch(cur, conn):
            cur.execute("SELECT embedding FROM nodes WHERE id=%s", (node_id,))
            row = cur.fetchone()
            return row[0] if row else None

        return self.atomic(_fetch)

    def fetch_edge_embed_ids(self, id: Any):
        def _fetch(cur, conn):
            cur.execute(
                "SELECT embedding FROM edges WHERE source=%s OR target=%s",
                (id, id),
            )
            return [r[0] for r in cur.fetchall()]

        return self.atomic(_fetch)

    def all_connected_nodes(self, node_or_edge: Union[Node, Edge]) -> Any:
        def _fetch(cur, conn):
            node_id = (
                node_or_edge.id
                if isinstance(node_or_edge, Node)
                else node_or_edge.source
            )
            cur.execute(
                "SELECT id, label, attributes FROM nodes WHERE id IN ("
                "SELECT source FROM edges WHERE target=%s UNION SELECT target FROM edges WHERE source=%s)",
                (node_id, node_id),
            )
            return [Node(id=r[0], label=r[1], attributes=r[2]) for r in cur.fetchall()]

        return self.atomic(_fetch)

    def get_connections(self, identifier: Any) -> CursorExecFunction:
        def _conn(cur, conn):
            cur.execute(
                "SELECT * FROM edges WHERE source=%s OR target=%s",
                (identifier, identifier),
            )
            return cur.fetchall()

        return self.atomic(_conn)

    def search_edge(self, source: Any, target: Any, attributes: Dict) -> Any:
        def _search(cur, conn):
            cur.execute(
                "SELECT id FROM edges WHERE source=%s AND target=%s AND attributes=%s",
                (source, target, json.dumps(attributes)),
            )
            row = cur.fetchone()
            return row[0] if row else None

        return self.atomic(_search)

    def add_node(self, label: str, attribute: Dict, id: Any) -> None:
        def _add(cur, conn) -> None:
            embed = self._node_embedding(attribute)
            cur.execute(
                """
                INSERT INTO nodes (id, label, attributes, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    label=EXCLUDED.label,
                    attributes=EXCLUDED.attributes,
                    embedding=EXCLUDED.embedding,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (id, label, json.dumps(attribute), embed),
            )
            conn.commit()

        self.atomic(_add)

    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        def _add(cur, conn) -> None:
            embed = self._edge_embedding(source, target, label, attributes)
            cur.execute(
                "INSERT INTO edges (source, target, label, attributes, embedding) VALUES (%s, %s, %s, %s, %s)",
                (source, target, label, json.dumps(attributes), embed),
            )
            conn.commit()

        self.atomic(_add)

    def update_node(self, node: Node) -> None:
        self.add_node(
            node.label,
            node.attributes if isinstance(node.attributes, dict) else node.attributes,
            node.id,
        )

    def remove_node(self, id: Any) -> None:
        def _remove(cur, conn) -> None:
            cur.execute("DELETE FROM edges WHERE source=%s OR target=%s", (id, id))
            cur.execute("DELETE FROM nodes WHERE id=%s", (id,))
            conn.commit()

        self.atomic(_remove)

    def search_node(self, node_id: Any) -> Any:
        def _search(cur, conn):
            cur.execute(
                "SELECT id, label, attributes FROM nodes WHERE id=%s", (node_id,)
            )
            row = cur.fetchone()
            return (
                {"id": row[0], "label": row[1], "attributes": row[2]} if row else None
            )

        return self.atomic(_search)

    def search_node_label(self, node_id: Any) -> Any:
        def _search(cur, conn):
            cur.execute("SELECT label FROM nodes WHERE id=%s", (node_id,))
            return cur.fetchone()

        return self.atomic(_search)

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        def _traverse(cur, conn):
            cur.execute("SELECT target FROM edges WHERE source=%s", (source,))
            return [r[0] for r in cur.fetchall()]

        return self.atomic(_traverse)

    def fetch_node_id(self, id: Any):
        return self.search_node(id)

    def find_nodes_by_label(self, label: str):
        def _search(cur, conn):
            cur.execute(
                "SELECT id, label, attributes FROM nodes WHERE label LIKE %s",
                (f"%{label}%",),
            )
            return cur.fetchall()

        return self.atomic(_search)

    def graphviz_visualize(
        self,
        dot_file: Optional[str] = None,
        path: List[Any] = [],
        connections: Any = None,
        format: str = "png",
        exclude_node_keys: List[str] = [],
        hide_node_key: bool = False,
        node_kv: str = " ",
        exclude_edge_keys: List[str] = [],
        hide_edge_key: bool = False,
        edge_kv: str = " ",
    ) -> Any:
        raise NotImplementedError("Visualization not implemented for Postgres")

    def fetch_ids_from_db(self) -> List[str]:
        def _fetch(cur, conn):
            cur.execute("SELECT id FROM nodes")
            return [r[0] for r in cur.fetchall()]

        return self.atomic(_fetch)

    def search_indegree_edges(self, target: Any) -> List[Any]:
        def _search(cur, conn):
            cur.execute(
                "SELECT source, label, attributes FROM edges WHERE target=%s",
                (target,),
            )
            return cur.fetchall()

        return self.atomic(_search)

    def search_outdegree_edges(self, source: Any) -> List[Any]:
        def _search(cur, conn):
            cur.execute(
                "SELECT target, label, attributes FROM edges WHERE source=%s",
                (source,),
            )
            return cur.fetchall()

        return self.atomic(_search)

    def search_similar_nodes(self, embed_id, *, desc: bool, sort_by: str):
        raise NotImplementedError

    def search_similar_edges(self, embed_id, *, desc: bool, sort_by: str):
        raise NotImplementedError

    def search_node_type(self, label: str):
        raise NotImplementedError

    def search_id_by_node_type(self, node_type: str):
        raise NotImplementedError
