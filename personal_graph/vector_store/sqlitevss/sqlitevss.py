import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Union, List

from personal_graph.clients import (
    OpenAIEmbeddingClient,
    LiteLLMEmbeddingClient,
    OllamaEmbeddingClient,
)
from personal_graph.vector_store.vector_store import VectorStore
from personal_graph.database import TursoDB
from personal_graph.database import SQLite
from personal_graph.database.db import CursorExecFunction


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(
        Path(__file__).parent.resolve() / "embeddings-raw-queries" / sql_file
    ) as f:
        return f.read()


class SQLiteVSS(VectorStore):
    def __init__(
        self,
        *,
        db: Union[TursoDB, SQLite],
        index_dimension: int,
        embedding_client: Union[
            OpenAIEmbeddingClient, LiteLLMEmbeddingClient, OllamaEmbeddingClient
        ] = OpenAIEmbeddingClient(),
    ):
        self.db = db
        self.embedding_model = embedding_client.get_embedding_model()

        if index_dimension is None:
            raise ValueError("index_dimension cannot be None")
        self.index_dimension = index_dimension

    def initialize(self):
        def _init(cursor, connection):
            vector_schema = read_sql(Path("vector-store-schema.sql"))
            vector_schema = vector_schema.replace("{{size}}", str(self.index_dimension))

            connection.executescript(vector_schema)
            connection.commit()

        return self.db.atomic(_init)

    def save(self):
        return self.db.save()

    def __repr__(self) -> str:
        return (
            f"SQLiteVSS(\n"
            f"  db={self.db}\n"
            f"  embedding_client={self.embedding_model}\n"
            f"  )"
        )

    def _set_id(self, identifier: Any, label: str, data: Dict) -> Dict:
        if identifier is not None:
            data["id"] = identifier
            data["label"] = label
        return data

    def _add_embedding(self, id: Any, label: str, data: Dict) -> CursorExecFunction:
        def _insert(cursor, connection):
            set_data = self._set_id(id, label, data)

            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(rowid), 0) FROM nodes_embedding"
                ).fetchone()[0]
                + 1
            )

            cursor.execute(
                read_sql(Path("insert-node-embedding.sql")),
                (
                    count,
                    json.dumps(
                        self.embedding_model.get_embedding(json.dumps(set_data))
                    ),
                ),
            )
            connection.commit()

        return _insert

    def _add_embeddings(self, nodes: List[Dict], labels: List[str], ids: List[Any]):
        def insert_nodes_embeddings(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(rowid), 0) FROM nodes_embedding"
                ).fetchone()[0]
                + 1
            )

            for i, x in enumerate(zip(ids, labels, nodes)):
                cursor.execute(
                    read_sql(Path("insert-node-embedding.sql")),
                    (
                        count + i,
                        json.dumps(
                            self.embedding_model.get_embedding(
                                json.dumps(self._set_id(x[0], x[1], x[2]))
                            )
                        ),
                    ),
                )

        return insert_nodes_embeddings

    def _add_edge_embedding(self, data: Dict):
        def _insert_edge_embedding(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(rowid), 0) FROM relationship_embedding"
                ).fetchone()[0]
                + 1
            )

            cursor.execute(
                read_sql(Path("insert-edge-embedding.sql")),
                (
                    count,
                    json.dumps(self.embedding_model.get_embedding(json.dumps(data))),
                ),
            )
            connection.commit()

        return _insert_edge_embedding

    def _remove_node(self, id: Any):
        def _delete_node_embedding(cursor, connection):
            cursor.execute(read_sql(Path("delete-node-embedding.sql")), (id[0],))

        return _delete_node_embedding

    def _remove_edge(self, ids: Any):
        def _delete_node_embedding(cursor, connection):
            for id in ids:
                cursor.execute(read_sql(Path("delete-edge-embedding.sql")), (id[0],))

        return _delete_node_embedding

    def add_node_embedding(
        self, id: Any, label: str, attribute: Dict[Any, Any]
    ) -> None:
        self.db.atomic(self._add_embedding(id, label, attribute))

    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None:
        edge_data = {
            "source_id": source,
            "target_id": target,
            "label": label,
            "attributes": json.dumps(attributes),
        }

        self.db.atomic(self._add_edge_embedding(edge_data))

    def add_edge_embeddings(self, sources, targets, labels, attributes):
        for i, x in enumerate(zip(sources, targets, labels, attributes)):
            edge_data = {
                "source_id": x[0],
                "target_id": x[1],
                "label": x[2],
                "attributes": json.dumps(x[3]),
            }
            self.db.atomic(self._add_edge_embedding(edge_data))

    def delete_node_embedding(self, id: Any) -> None:
        self.db.atomic(self._remove_node(id))

    def delete_edge_embedding(self, ids: Any) -> None:
        self.db.atomic(self._remove_edge(ids))

    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ):
        def _search_node(cursor, connection):
            embed_json = json.dumps(
                self.embedding_model.get_embedding(json.dumps(data))
            )

            nodes = cursor.execute(
                read_sql(Path("vector-search-node.sql")),
                (
                    embed_json,
                    limit,
                    sort_by,
                    descending,
                    sort_by,
                    sort_by,
                    descending,
                    sort_by,
                ),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[4] < threshold][:limit]
            else:
                return nodes[:limit]

        return self.db.atomic(_search_node)

    # TODO: use auto in enum values auto() inside  Ordering(Enum)
    # TODO: check up the optional params, , mention default values, use enums Ordering(asc, desc): do ordering.asc
    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ):
        def _search_edge(cursor, connection):
            embed = json.dumps(self.embedding_model.get_embedding(json.dumps(data)))
            if descending:
                edges = cursor.execute(
                    read_sql(Path("vector-search-edge-desc.sql")), (embed, limit)
                ).fetchall()

            else:
                edges = cursor.execute(
                    read_sql(Path("vector-search-edge.sql")), (embed, limit)
                ).fetchall()

            if not edges:
                return None

            if threshold is not None:
                filtered_results = [edge for edge in edges if edge[5] < threshold]
                return filtered_results[:limit]
            else:
                return edges[:limit]

        return self.db.atomic(_search_edge)

    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: float = 0.9, limit: int = 1
    ):
        def _search_node(cursor, connection):
            embed_json = json.dumps(
                self.embedding_model.get_embedding(json.dumps(data))
            )

            nodes = cursor.execute(
                read_sql(Path("similarity-search-node.sql")),
                (embed_json, limit),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[1] < threshold][:limit]
            else:
                return nodes[:limit]

        return self.db.atomic(_search_node)

    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: float = 0.9, limit: int = 1
    ):
        def _search_node(cursor, connection):
            embed_json = json.dumps(
                self.embedding_model.get_embedding(json.dumps(data))
            )

            nodes = cursor.execute(
                read_sql(Path("similarity-search-edge.sql")),
                (embed_json, limit),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[1] < threshold][:limit]
            else:
                return nodes[:limit]

        return self.db.atomic(_search_node)
