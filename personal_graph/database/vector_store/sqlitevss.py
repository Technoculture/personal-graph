import json
from functools import lru_cache
from pathlib import Path
import libsql_experimental as libsql  # type: ignore
from typing import Any, Dict, Optional, Union, Callable, List

from personal_graph.clients import EmbeddingClient
from personal_graph.embeddings import OpenAIEmbeddingsModel
from personal_graph.database.vector_store.vector_store import VectorStore
from personal_graph.database.database_store.turso import TursoDB
from personal_graph.database.database_store.sqlite import SQLite

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(Path(__file__).parent.resolve() / "sql" / sql_file) as f:
        return f.read()


class SQLiteVSS(VectorStore):
    def __init__(
        self, *, db: Union[TursoDB, SQLite], embedding_model_client: EmbeddingClient
    ):
        self.db = db
        self.embedding_model = OpenAIEmbeddingsModel(
            embedding_model_client.client,
            embedding_model_client.model_name,
            embedding_model_client.dimensions,
        )

    def initialize(self):
        def _init(cursor, connection):
            vector_schema = read_sql(Path("vector-store-schema.sql"))
            connection.executescript(vector_schema)
            connection.commit()

        return self.db.atomic(_init)

    def save(self):
        return self.db.save()

    def _set_id(self, identifier: Any, data: Dict) -> Dict:
        if identifier is not None:
            data["id"] = identifier
        return data

    def _add_embedding(self, id: Any, data: Dict) -> CursorExecFunction:
        def _insert(cursor, connection):
            set_data = self._set_id(id, data)

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
                                json.dumps(self._set_id(x[0], x[2]))
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

    def _vector_search_node(
        self,
        data: str,
        threshold: Optional[float] = None,
        desc: Optional[bool] = False,
        k: int = 10,
        sort_by: Optional[str] = "",
    ) -> CursorExecFunction:
        def _search_node(cursor, connection):
            embed_json = json.dumps(self.embedding_model.get_embedding(data))

            nodes = cursor.execute(
                read_sql(Path("vector-search-node.sql")),
                (embed_json, k, sort_by, desc, sort_by, sort_by, desc, sort_by),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[4] < threshold][:k]
            else:
                return nodes[:k]

        return _search_node

    def _similarity_search_node(
        self,
        data: str,
        *,
        threshold: Optional[float] = None,
        k: int = 10,
    ) -> CursorExecFunction:
        def _search_node(cursor, connection):
            embed_json = json.dumps(self.embedding_model.get_embedding(data))

            nodes = cursor.execute(
                read_sql(Path("similarity-search-node.sql")),
                (embed_json, k),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[1] < threshold][:k]
            else:
                return nodes[:k]

        return _search_node

    def _similarity_search_edge(
        self,
        data: str,
        *,
        threshold: Optional[float] = None,
        k: int = 10,
    ) -> CursorExecFunction:
        def _search_node(cursor, connection):
            embed_json = json.dumps(self.embedding_model.get_embedding(data))

            nodes = cursor.execute(
                read_sql(Path("similarity-search-edge.sql")),
                (embed_json, k),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[1] < threshold][:k]
            else:
                return nodes[:k]

        return _search_node

    def _vector_search_edge(
        self,
        data: str,
        threshold: Optional[float] = None,
        desc: bool = False,
        k: int = 10,
    ) -> CursorExecFunction:
        def _search_edge(cursor, connection):
            embed = json.dumps(self.embedding_model.get_embedding(data))
            if desc:
                edges = cursor.execute(
                    read_sql(Path("vector-search-edge-desc.sql")), (embed, k)
                ).fetchall()

            else:
                edges = cursor.execute(
                    read_sql(Path("vector-search-edge.sql")), (embed, k)
                ).fetchall()

            if not edges:
                return None

            if threshold is not None:
                filtered_results = [edge for edge in edges if edge[5] < threshold]
                return filtered_results[:k]
            else:
                return edges[:k]

        return _search_edge

    def add_node_embedding(self, id: Any, attribute: Dict[Any, Any]) -> None:
        self.db.atomic(self._add_embedding(id, attribute))

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
        data: str,
        *,
        threshold: Optional[float] = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        return self.db.atomic(
            self._vector_search_node(data, threshold, descending, limit)
        )

    # TODO: use auto in enum values auto() inside  Ordering(Enum)
    # TODO: check up the optional params, , mention default values, use enums Ordering(asc, desc): do ordering.asc
    def vector_search_edge(
        self,
        data: str,
        *,
        threshold: Optional[float] = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        return self.db.atomic(
            self._vector_search_edge(data, threshold, descending, limit)
        )

    def vector_search_node_from_multi_db(
        self, data: str, *, threshold: Optional[float] = None, limit: int = 1
    ):
        return self.db.atomic(
            self._similarity_search_node(data, threshold=threshold, k=limit)
        )

    def vector_search_edge_from_multi_db(
        self, data: str, *, threshold: Optional[float] = None, limit: int = 1
    ):
        return self.db.atomic(
            self._similarity_search_edge(data, threshold=threshold, k=limit)
        )
