import json
import os
from functools import lru_cache
from pathlib import Path

import libsql_experimental as libsql
from typing import List, Any, Dict, Optional, Callable, Union

from graphviz import Digraph
from jsonschema import Draft7Validator, exceptions

from personal_graph import Node, Edge
from personal_graph.database.db import DB

JSON_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "fhir_4.schema.json")
CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(Path(__file__).parent.resolve() / "fhir-schema" / sql_file) as f:
        return f.read()


class FhirService:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def __eq__(self, other):
        return self.db_url == other.db_url

    def __repr__(self) -> str:
        return f"  FhirService(\n" f"  url={self.db_url},\n" f"  )"

    def set_ontologies(self, ontologies: Optional[List[Any]] = None):
        if not ontologies:
            raise ValueError("Ontology not provided")
        self.ontologies = ontologies

    def initialize(self):
        def _init(cursor, connection):
            schema_sql = read_sql(Path("fhir_4.sql"))
            connection.executionscript(schema_sql)
            connection.commit()

        return self._atomic(_init)

    def save(self):
        self._connection.commit()

    def _atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        self._connection = libsql.connect(
            database=self.db_url,
            auth_token=os.getenv("TURSO_PATIENTS_GROUP_AUTH_TOKEN"),
        )

        cursor = self._connection.cursor()
        cursor.execute("PRAGMA foreign_keys = TRUE;")
        results = cursor_exec_fn(cursor, self._connection)
        self._connection.commit()
        return results

    def _validate_data(self, json_data: Dict) -> bool:
        with open(JSON_SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
        try:
            Draft7Validator.check_schema(schema)
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(json_data))
            if errors:
                return False
            else:
                return True
        except exceptions.SchemaError:
            return False

    def add_node(self, label: str, attribute: Dict, id: Any) -> None:
        def _add_node(cursor, connection):
            if self._validate_data(attribute):
                resource_type = label.lower()
                cursor.execute(
                    f"""
                            INSERT OR IGNORE INTO {resource_type}_history (id, txid, ts, resource_type, status, resource)
                            SELECT id, ?, current_timestamp, resource_type, 'created', resource
                            FROM {resource_type}
                            WHERE id = ?
                        """,
                    (123, id),
                )

                cursor.execute(
                    f"""
                        INSERT OR IGNORE INTO {resource_type} (id, txid, ts, resource_type, status, resource)
                        VALUES (?, ?, current_timestamp, ?, 'created', ?)
                        ON CONFLICT(id) DO UPDATE SET
                        txid = excluded.txid,
                        ts = excluded.ts,
                        status = 'recreated',
                        resource = excluded.resource
                    """,
                    (id, 123, resource_type, json.dumps(attribute)),
                )
                connection.commit()

        return self._atomic(_add_node)

    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        def _add_edge(cursor, connection):
            count = cursor.execute("SELECT COALESCE(MAX(id), 0) FROM relations").fetchone()[
                    0
                ]

            cursor.execute(
                "INSERT INTO relations VALUES(?, ?, ?, ?, ?, ?, json(?))",
                (
                    int(count) + 1,
                    source.id,
                    source.label,
                    target.id,
                    target.label,
                    label,
                    json.dumps(attributes),
                ),
            )

        if not self.search_node(source.id, resource_type=source.label):
            return

        if not self.search_node(target.id, resource_type=target.label):
            return

        return self._atomic(_add_edge)

    def update_node(self, node: Node):
        def _update(cursor, connection):
            resource_type = node.label.lower()

            cursor.execute(
                f"""
                        INSERT OR IGNORE INTO {resource_type}_history (id, txid, ts, resource_type, status, resource)
                        SELECT id, txid, current_timestamp, resource_type, 'updated', resource
                        FROM {resource_type}
                        WHERE id = ?
                    """,
                (node.id,),
            )

            cursor.execute(
                f"""
                    INSERT OR IGNORE INTO {resource_type} (id, txid, ts, resource_type, status, resource)
                    VALUES (?, ?, current_timestamp, ?, 'updated', ?)
                    ON CONFLICT(id) DO UPDATE SET
                    txid = excluded.txid,
                    ts = excluded.ts,
                    status = 'updated',
                    resource = excluded.resource
                """,
                (node.id, 123, resource_type, json.dumps(node.attributes)),
            )
            connection.commit()

        return self._atomic(_update)

    def remove_node(self, id: Any, *, resource_type: str) -> None:
        def _remove(cursor, connection):
            if not resource_type:
                raise ValueError("Resource type not provided")

            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {resource_type}_history (id, txid, ts, resource_type, status, resource)
                SELECT id, txid, current_timestamp, resource_type, 'deleted', resource
                FROM {resource_type}
                WHERE id = ?
                """,
                (id,),
            )

            cursor.execute(
                f"""
                    DELETE FROM {resource_type.lower()} WHERE id = ?
                """,
                (id,),
            )

            cursor.execute(
                "DELETE FROM relations WHERE source_id = ? OR target_id = ?", (id, id)
            )

        return self._atomic(_remove)

    def search_node(self, node_id: Any, *, resource_type: str) -> Any:
        def _search_node(cursor, connection):
            if not resource_type:
                raise ValueError("Resource type not provided.")

            node = cursor.execute(
                f"SELECT * from {resource_type.lower()} WHERE id = ?", (node_id,)
            )
            if node:
                return node.fetchone()
            return None

        return self._atomic(_search_node)

    def search_edge(self, source: Any, target: Any, attributes: Dict):
        def _search_edge(cursor, connection):
            edge = cursor.execute(
                "SELECT id from relations WHERE source_id=? AND source_type=? AND target_id=? AND target_type=? AND resource = json(?)",
                (
                    source.id,
                    source.label,
                    target.id,
                    target.label,
                    json.dumps(attributes),
                ),
            ).fetchone()

            if edge:
                return edge[0]

            return None

        return self._atomic(_search_edge)

    def search_indegree_edges(self, target: Any) -> List[Any]:
        def _indegree_edges(cursor, connection):
            indegree = cursor.execute(
                "SELECT source_id, source_type, resource from relations where target_id=?",
                (target.id, ),
            )

            if not indegree:
                return []
            else:
                return indegree.fetchall()

        return self._atomic(_indegree_edges)

    def search_outdegree_edges(self, source: Any) -> List[Any]:
        def _outdegree_edges(cursor, connection):
            outdegree = cursor.execute(
                "SELECT target_id, target_type, resource from relations where source_id=?",
                (source.id, ),
            )

            if not outdegree:
                return []
            else:
                return outdegree.fetchall()

        return self._atomic(_outdegree_edges)

    def fetch_ids_from_db(
        self, limit: Optional[int] = 10, *, resource_type: str
    ) -> List[str]:
        def _fetch_ids_from_db(cursor, connection):
            nodes = cursor.execute(
                f"SELECT id from {resource_type.lower()} LIMIT ?", (limit,)
            ).fetchall()
            ids = [id[0] for id in nodes]

            return ids

        return self._atomic(_fetch_ids_from_db)

    def all_connected_nodes(self, node_or_edge: Union[Node | Edge]) -> Any:
        def _all_connected_nodes(cursor, connection):
            if isinstance(node_or_edge, Node):
                node_id = node_or_edge.id
            elif isinstance(node_or_edge, Edge):
                node_id = node_or_edge.source.id
            else:
                raise ValueError("Invalid input: must be Node or Edge")

            connected_nodes = set()
            to_visit = [node_id]

            while to_visit:
                current = to_visit.pop(0)
                if current not in connected_nodes:
                    connected_nodes.add(current)
                    neighbors = cursor.execute(
                        "SELECT target_id FROM relations WHERE source_id = ? "
                        "UNION SELECT source_id FROM relations WHERE target_id = ?",
                        (current, current),
                    ).fetchall()
                    to_visit.extend(
                        [n[0] for n in neighbors if n[0] not in connected_nodes]
                    )

            return list(connected_nodes)

        return self._atomic(_all_connected_nodes)

    def search_similar_nodes(
        self, embed_ids, *, desc: Optional[bool] = False, sort_by: Optional[str] = ""
    ):
        raise NotImplementedError("search_similar_nodes method is not yet implemented")

    def search_similar_edges(self, embed_ids, *, desc: bool = False, sort_by: str = ""):
        raise NotImplementedError("search_similar_edges method is not yet implemented")

    def fetch_node_embed_id(self, node_id: Any):
        raise NotImplementedError("fetch_node_embed_ids method is not yet implemented")

    def fetch_edge_embed_ids(self, id: Any):
        raise NotImplementedError("fetch_edge_embed_ids method is not yet implemented")

    def find_nodes_by_label(self, label: str):
        raise NotImplementedError("find_nodes_by_label method is not yet implemented")

    def search_node_label(self, node_id: Any) -> Any:
        raise NotImplementedError("search_node_label method is not yet implemented")

    def fetch_node_id(self, id: Any):
        raise NotImplementedError("fetch_node_id method is not yet implemented")
