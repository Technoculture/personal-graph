import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from personal_graph.vector_store import SQLiteVSS
from personal_graph.database.db import CursorExecFunction


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(
        Path(__file__).parent.resolve() / "fhir-embedding-queries" / sql_file
    ) as f:
        return f.read()


class FhirSQLiteVSS(SQLiteVSS):
    def initialize(self):
        def _init(cursor, connection):
            vector_schema = read_sql(Path("fhir_4_vector_schema.sql"))
            vector_schema = vector_schema.replace("{{size}}", str(self.index_dimension))

            connection.executescript(vector_schema)
            connection.commit()

        return self.db.atomic(_init)

    def save(self):
        return self.db.save()

    def __repr__(self) -> str:
        return f"FhirSQLiteVSS(\n" f"  db={self.db}\n" f"  )"

    def _add_embedding(self, id: Any, label: str, data: Dict) -> CursorExecFunction:
        def _insert(cursor, connection):
            set_data = self._set_id(id, label, data)
            rt = label.lower()

            count = cursor.execute(
                f"""SELECT COALESCE(MAX(rowid), 0) FROM {rt}_embedding"""
            ).fetchone()[0]

            # To check whether status is recreated, if so then do not add the embedding
            status = cursor.execute(
                f"""SELECT status from {rt} WHERE id=?""", (id,)
            ).fetchone()[0]

            if status != "recreated":
                cursor.execute(
                    f"""INSERT INTO {rt}_embedding(rowid, vector_node) VALUES (?,?);""",
                    (
                        int(count) + 1,
                        json.dumps(
                            self.embedding_model.get_embedding(json.dumps(set_data))
                        ),
                    ),
                )
            connection.commit()

        return _insert

    def _add_edge_embedding(self, data: Dict):
        def _insert_edge_embedding(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(rowid), 0) FROM relations_embedding"
                ).fetchone()[0]
                + 1
            )

            cursor.execute(
                """INSERT INTO relations_embedding(rowid, vector_relations) VALUES(?, ?)""",
                (
                    count,
                    json.dumps(self.embedding_model.get_embedding(json.dumps(data))),
                ),
            )
            connection.commit()

        return _insert_edge_embedding

    def _remove_node(self, id: Any, node_type: Optional[str] = None):
        def _delete_node_embedding(cursor, connection):
            cursor.execute(
                f"""DELETE FROM {node_type.lower()}_embedding where rowid = (?)""",
                (id[0],),
            )

        return _delete_node_embedding

    def _remove_edge(self, ids: Any):
        def _delete_node_embedding(cursor, connection):
            for id in ids:
                cursor.execute(
                    """DELETE FROM relations_embedding where rowid = (?)""", (id[0],)
                )

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

    def delete_node_embedding(self, id: Any, node_type: Optional[str] = None) -> None:
        if not node_type:
            raise ValueError("Resource type not provided.")

        self.db.atomic(self._remove_node(id, node_type=node_type))

    def delete_edge_embedding(self, ids: Any) -> None:
        self.db.atomic(self._remove_edge(ids))
