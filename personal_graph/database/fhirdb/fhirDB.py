import json
import os
from functools import lru_cache
from pathlib import Path

from typing import List, Any, Dict, Optional, Callable, Union

from graphviz import Digraph  # type: ignore
from jsonschema import Draft7Validator, exceptions

from personal_graph.models import Node, Edge
from personal_graph.database.db import DB

try:
    import libsql_experimental as libsql  # type: ignore

    CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]

except ImportError:
    pass


JSON_SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "fhir_4.schema.json")


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(Path(__file__).parent.resolve() / "fhir_schema" / sql_file) as f:
        return f.read()


class FhirDB(DB):
    def __init__(self, db_url: str):
        self.db_url = db_url

    def __eq__(self, other):
        return self.db_url == other.db_url

    def __repr__(self) -> str:
        return f"  FhirFB(\n" f"  url={self.db_url},\n" f"  )"

    def set_ontologies(self, ontologies: Optional[List[Any]] = None):
        if not ontologies:
            raise ValueError("Ontology not provided")

    def initialize(self):
        def _init(cursor, connection):
            schema_sql = read_sql(Path("fhir_4.sql"))
            connection.executescript(schema_sql)
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

                count = cursor.execute(
                    f"SELECT COALESCE(MAX(embed_id), 0) FROM {resource_type}"
                ).fetchone()[0]

                cursor.execute(
                    f"""
                        INSERT OR IGNORE INTO {resource_type} (embed_id, id, txid, ts, resource_type, status, resource)
                        VALUES (?, ?, ?, current_timestamp, ?, 'created', ?)
                        ON CONFLICT(id) DO UPDATE SET
                        txid = excluded.txid,
                        ts = excluded.ts,
                        status = 'recreated',
                        resource = excluded.resource
                    """,
                    (int(count) + 1, id, 123, resource_type, json.dumps(attribute)),
                )

                cursor.execute(
                    f"""
                        INSERT OR IGNORE INTO {resource_type}_history (id, txid, ts, resource_type, status, resource)
                        SELECT id, ?, current_timestamp, resource_type, 'created', resource
                        FROM {resource_type}
                        WHERE id = ?
                    """,
                    (123, id),
                )
                connection.commit()

        return self._atomic(_add_node)

    def add_edge(
        self,
        source: Any,
        target: Any,
        label: str,
        attributes: Dict,
        source_rt: Optional[str] = None,
        target_rt: Optional[str] = None,
    ) -> None:
        def _add_edge(cursor, connection):
            if not source_rt or not target_rt:
                raise ValueError("source or target node types not given.")

            count = cursor.execute(
                "SELECT COALESCE(MAX(embed_id), 0) FROM relations"
            ).fetchone()[0]

            cursor.execute(
                "INSERT INTO relations VALUES(?, ?, ?, ?, ?, ?, json(?))",
                (
                    int(count) + 1,
                    source,
                    source_rt,
                    target,
                    target_rt,
                    label,
                    json.dumps(attributes),
                ),
            )

        return self._atomic(_add_edge)

    def update_node(self, node: Node):
        def _update(cursor, connection):
            resource_type = node.label.lower()

            if not self._validate_data(node.attributes):
                raise ValueError("Fhir Validation Error")

            count = cursor.execute(
                f"SELECT COALESCE(MAX(embed_id), 0) FROM {resource_type}"
            ).fetchone()[0]

            cursor.execute(
                f"""
                    INSERT OR IGNORE INTO {resource_type}_history (id, txid, ts, resource_type, status, resource)
                    VALUES (?, ?, current_timestamp, ?, 'updated', ?)
                    ON CONFLICT(id, txid) DO UPDATE SET
                    txid = excluded.txid,
                    ts = excluded.ts,
                    status = 'updated',
                    resource = excluded.resource
                """,
                (node.id, 123, resource_type, json.dumps(node.attributes)),
            )

            cursor.execute(
                f"""
                    INSERT OR IGNORE INTO {resource_type} (embed_id, id, txid, ts, resource_type, status, resource)
                    VALUES (?, ?, ?, current_timestamp, ?, 'updated', ?)
                    ON CONFLICT(id) DO UPDATE SET
                    embed_id = excluded.embed_id,
                    txid = excluded.txid,
                    ts = excluded.ts,
                    status = 'updated',
                    resource = excluded.resource
                """,
                (
                    int(count) + 1,
                    node.id,
                    123,
                    resource_type,
                    json.dumps(node.attributes),
                ),
            )

            connection.commit()

        return self._atomic(_update)

    def remove_node(self, id: Any, node_type: Optional[str] = None) -> None:
        def _remove(cursor, connection):
            if not node_type:
                raise ValueError("Resource type not provided")

            cursor.execute(
                f"""
                    UPDATE {node_type}_history SET status='deleted' WHERE id=? AND txid=?
                """,
                (id, 123),
            )

            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {node_type} (id, txid, ts, resource_type, status, resource)
                SELECT id, txid, current_timestamp, resource_type, 'deleted', resource
                FROM {node_type}
                WHERE id = ?
                """,
                (id,),
            )

            cursor.execute(
                f"""
                    DELETE FROM {node_type.lower()} WHERE id = ?
                """,
                (id,),
            )

            cursor.execute(
                "DELETE FROM relations WHERE source_id = ? OR target_id = ?", (id, id)
            )

        return self._atomic(_remove)

    def search_node(self, node_id: Any, *, node_type: Optional[str] = None) -> Any:
        def _search_node(cursor, connection):
            if not node_type:
                raise ValueError("Resource type not provided.")

            node = cursor.execute(
                f"SELECT resource from {node_type.lower()} WHERE id = ?", (node_id,)
            ).fetchone()

            if node:
                return json.loads(node[0])
            return None

        return self._atomic(_search_node)

    def search_edge(
        self,
        source: Any,
        target: Any,
        attributes: Dict,
        limit: int = 1,
    ) -> Any:
        def _search_edge(cursor, connection):
            result = cursor.execute(
                "SELECT embed_id from relations where source_id=? AND source_type=? AND target_id = ? AND target_type=? AND resource=json(?) LIMIT ?",
                (
                    source.id,
                    source.label,
                    target.id,
                    target.label,
                    json.dumps(attributes),
                    limit,
                ),
            ).fetchone()

            if result:
                return result[0]

            return None

        return self._atomic(_search_edge)

    def search_indegree_edges(self, target: Any) -> List[Any]:
        def _indegree_edges(cursor, connection):
            indegree = cursor.execute(
                "SELECT source_id, source_type, resource from relations where target_id=?",
                (target,),
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
                (source,),
            )

            if not outdegree:
                return []
            else:
                return outdegree.fetchall()

        return self._atomic(_outdegree_edges)

    def fetch_ids_from_db(
        self, limit: Optional[int] = 10, node_type: Optional[str] = None
    ) -> List[str]:
        def _fetch_ids_from_db(cursor, connection):
            if not node_type:
                raise ValueError("Resource type not provided.")

            nodes = cursor.execute(
                f"SELECT id from {node_type.lower()} LIMIT ?", (limit,)
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

    def get_connections(self, identifier: Any) -> CursorExecFunction:
        def _get_all_connections(cursor, connection):
            return cursor.execute(
                "SELECT * from relations WHERE source_id=? OR target_id=?",
                (identifier, identifier),
            ).fetchall()

        return self._atomic(_get_all_connections)

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        def _traverse(cursor, connection):
            visited = set()
            path = []

            def dfs(current, target):
                visited.add(current)
                path.append(current)

                if current == target:
                    return True

                neighbors = cursor.execute(
                    "SELECT target_id FROM relations WHERE source_id = ?", (current,)
                ).fetchall()

                for neighbor in neighbors:
                    if neighbor[0] not in visited:
                        if dfs(neighbor[0], target):
                            return True
                path.pop()
                return False

            dfs(source, target)

            if with_bodies:
                return [self.search_node(node, resource_type="") for node in path]
            return path

        return self._atomic(_traverse)

    def search_node_type(self, label: str) -> bool:
        def _search_node_type(cursor, connection):
            cursor.execute(
                """
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name=?;
            """,
                (label.lower(),),
            )

            result = cursor.fetchone()
            return result is not None

        return self._atomic(_search_node_type)

    def fetch_node_embed_id(
        self, node_id: Any, limit: int = 1, node_type: Optional[str] = None
    ):
        def _fetch_embed_id(cursor, connection):
            if not node_type:
                raise ValueError("Resource type not provided.")

            embed_id = cursor.execute(
                f"SELECT embed_id from {node_type} WHERE id=? LIMIT ?", (node_id, limit)
            ).fetchone()

            return embed_id

        return self._atomic(_fetch_embed_id)

    def fetch_edge_embed_ids(self, id: Any, limit: int = 10):
        def _fetch_edge_embed_id(cursor, connection):
            embed_id = cursor.execute(
                "SELECT embed_id from relations WHERE source_id=? OR target_id=? LIMIT ?",
                (id, id, limit),
            ).fetchall()

            return embed_id

        return self._atomic(_fetch_edge_embed_id)

    def search_similar_nodes(
        self, embed_ids, *, desc: Optional[bool] = False, sort_by: Optional[str] = ""
    ):
        raise NotImplementedError("search_similar_nodes method is not yet implemented")

    def search_similar_edges(self, embed_ids, *, desc: bool = False, sort_by: str = ""):
        raise NotImplementedError("search_similar_edges method is not yet implemented")

    def find_nodes_by_label(self, label: str):
        raise NotImplementedError("find_nodes_by_label method is not yet implemented")

    def search_node_label(self, node_id: Any) -> Any:
        raise NotImplementedError("search_node_label method is not yet implemented")

    def fetch_node_id(self, id: Any):
        raise NotImplementedError("fetch_node_id method is not yet implemented")

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
    ) -> Digraph:
        raise NotImplementedError("graphviz_visualize method is not yet implemented")

    def search_id_by_node_type(self, node_type: str):
        raise NotImplementedError(
            "search_id_by_node_type method is not yet implemented"
        )
