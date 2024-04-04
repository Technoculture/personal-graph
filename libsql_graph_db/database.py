#!/usr/bin/env python3

"""
database.py

A series of functions to leverage the (node, edge) schema of
json-based nodes, and edges with optional json properties,
using an atomic transaction wrapper function.

"""

import json
import pathlib
from dotenv import load_dotenv
from functools import lru_cache
import libsql_experimental as libsql  # type: ignore
from typing import Callable, Optional, Tuple, Dict, List, Any
from libsql_graph_db.embeddings import OpenAIEmbeddingsModel
from jinja2 import Environment, BaseLoader, select_autoescape

load_dotenv()
embed_obj = OpenAIEmbeddingsModel()
CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


@lru_cache(maxsize=None)
def read_sql(sql_file: str) -> str:
    with open(pathlib.Path(__file__).parent.resolve() / "sql" / sql_file) as f:
        return f.read()


class SqlTemplateLoader(BaseLoader):
    def get_source(
        self, environment: Environment, template: str
    ) -> Tuple[str, str, Callable[[], bool]]:
        def uptodate() -> bool:
            return True

        # Return the source code, the template name, and the uptodate function
        return read_sql(template), template, uptodate


env = Environment(loader=SqlTemplateLoader(), autoescape=select_autoescape())

clause_template = env.get_template("search-where.template")
search_template = env.get_template("search-node.template")
traverse_template = env.get_template("traverse.template")


def atomic(
    cursor_exec_fn: CursorExecFunction,
    db_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> Any:
    connection = None
    try:
        if not db_url:
            connection = libsql.connect(":memory:")
        else:
            connection = libsql.connect(database=db_url, auth_token=auth_token)

        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = TRUE;")
        results = cursor_exec_fn(cursor, connection)
        connection.commit()
    finally:
        if connection:
            pass
    return results


def initialize(
    db_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    schema_file: str = "schema.sql",
) -> Any:
    def _init(cursor, connection):
        schema_sql = read_sql(schema_file)
        connection.executescript(schema_sql)
        connection.commit()

    return atomic(_init, db_url, auth_token)


def _set_id(identifier: Any, data: Dict) -> Dict:
    if identifier is not None:
        data["id"] = identifier
    return data


def _insert_node(
    cursor: libsql.Cursor,
    connection: libsql.Connection,
    identifier: Any,
    label: str,
    data: Dict,
) -> None:
    existing_node = cursor.execute(
        read_sql("existing-node.sql"), (identifier,)
    ).fetchone()

    if existing_node:
        return

    count = (
        cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0] + 1
    )

    set_data = _set_id(identifier, data)

    cursor.execute(
        read_sql("insert-node.sql"),
        (
            count,
            label,
            json.dumps(set_data),
        ),
    )

    cursor.execute(
        read_sql("insert-node-embedding.sql"),
        (count, json.dumps(embed_obj.get_embedding(json.dumps(set_data)))),
    )


def vector_search_node(
    data: Dict, k: Optional[int] = 1, threshold: Optional[float] = None
) -> CursorExecFunction:
    def _search_node(cursor, connection):
        embed = json.dumps(embed_obj.get_embedding(json.dumps(data)))
        if k == 1:
            node = cursor.execute(
                read_sql("vector-search-node.sql"), (embed, k)
            ).fetchone()
            print(node)
            return node
        else:
            nodes = cursor.execute(
                read_sql("vector-search-node.sql"), (embed, k)
            ).fetchall()
            if threshold is not None:
                filtered_results = [
                    (node[0], node[4]) for node in nodes if node[4] < threshold
                ]
                return filtered_results[:k]
            else:
                return nodes[:k]

    return _search_node


def vector_search_edge(
    data: Dict, k: Optional[int] = 1, threshold: Optional[float] = None
) -> CursorExecFunction:
    def _search_edge(cursor, connection):
        embed = json.dumps(embed_obj.get_embedding(json.dumps(data)))
        if k == 1:
            edge = cursor.execute(
                read_sql("vector-search-edge.sql"), (embed, k)
            ).fetchone()
            return edge
        else:
            edges = cursor.execute(
                read_sql("vector-search-node.sql"), (embed, k)
            ).fetchall()
            if threshold is not None:
                filtered_results = [
                    (edge[0], edge[4]) for edge in edges if edge[4] < threshold
                ]
                return filtered_results[:k]
            else:
                return edges[:k]

    return _search_edge


def add_node(label: str, data: Dict, identifier: Any = None) -> CursorExecFunction:
    def _add_node(cursor, connection):
        _insert_node(cursor, connection, identifier, label, data)

    return _add_node


def add_nodes(
    nodes: List[Dict], labels: List[str], ids: List[Any]
) -> CursorExecFunction:
    def _add_nodes(cursor, connection):
        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0]
            + 1
        )

        for i, x in enumerate(zip(ids, labels, nodes)):
            existing_node = cursor.execute(
                read_sql("existing-node.sql"), (x[0],)
            ).fetchone()

            if existing_node:
                count -= 1
                continue

            cursor.execute(
                read_sql("insert-node.sql"),
                (
                    count + i,
                    x[1],
                    json.dumps(_set_id(x[0], x[2])),
                ),
            )
            cursor.execute(
                read_sql("insert-node-embedding.sql"),
                (
                    count + i,
                    json.dumps(
                        embed_obj.get_embedding(json.dumps(_set_id(x[0], x[2])))
                    ),
                ),
            )

    return _add_nodes


def _upsert_node(
    cursor: libsql.Cursor,
    connection: libsql.Connection,
    identifier: Any,
    label: str,
    data: Dict,
) -> None:
    current_data = find_node(identifier)(cursor, connection)
    if not current_data:
        # no prior record exists, so regular insert
        _insert_node(cursor, connection, identifier, label, data)
    else:
        current_id = current_data["id"]
        id_to_be_updated = cursor.execute(
            "SELECT embed_id from nodes where id=?", (current_id,)
        ).fetchone()[0]
        updated_data = {**current_data, **data}

        cursor.execute(read_sql("delete-node-embedding.sql"), (id_to_be_updated,))
        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0]
            + 1
        )

        cursor.execute(
            read_sql("insert-node-embedding.sql"),
            (count, json.dumps(embed_obj.get_embedding(json.dumps(updated_data)))),
        )
        cursor.execute(
            read_sql("update-node.sql"),
            (
                label,
                json.dumps(_set_id(identifier, updated_data)),
                count,
                identifier,
            ),
        )


def upsert_node(identifier: Any, label: str, data: Dict) -> CursorExecFunction:
    def _upsert(cursor, connection):
        _upsert_node(cursor, connection, identifier, label, data)

    return _upsert


def upsert_nodes(
    nodes: List[Dict], labels: List[str], ids: List[Any]
) -> CursorExecFunction:
    def _upsert(cursor, connection):
        for id, label, node in zip(ids, labels, nodes):
            _upsert_node(cursor, connection, id, label, node)

    return _upsert


def connect_nodes(
    source_id: Any, target_id: Any, label: str, attributes: Dict = {}
) -> CursorExecFunction:
    def _connect_nodes(cursor, connection):
        existing_edge = cursor.execute(
            read_sql("existing-edge.sql"),
            (source_id, target_id, label, json.dumps(attributes)),
        ).fetchone()

        existing_source_node = cursor.execute(
            read_sql("existing-node.sql"), (source_id,)
        ).fetchone()
        existing_target_node = cursor.execute(
            read_sql("existing-node.sql"), (target_id,)
        ).fetchone()

        if existing_edge or not existing_source_node or not existing_target_node:
            return

        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM edges").fetchone()[0]
            + 1
        )

        cursor.execute(
            read_sql("insert-edge.sql"),
            (
                count,
                source_id,
                target_id,
                label,
                json.dumps(attributes),
            ),
        )

        edge_data = {
            "source_id": source_id,
            "target_id": target_id,
            "label": label,
            "attributes": attributes,
        }

        cursor.execute(
            read_sql("insert-edge-embedding.sql"),
            (count, json.dumps(embed_obj.get_embedding(json.dumps(edge_data)))),
        )

    return _connect_nodes


def connect_many_nodes(
    sources: List[Any], targets: List[Any], labels: List[str], attributes: List[Dict]
) -> CursorExecFunction:
    def _connect_nodes(cursor, connection):
        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM edges").fetchone()[0]
            + 1
        )

        for i, x in enumerate(zip(sources, targets, labels, attributes)):
            existing_edge = cursor.execute(
                read_sql("existing-edge.sql"),
                (x[0], x[1], x[2], json.dumps(x[3])),
            ).fetchone()

            existing_source_node = cursor.execute(
                read_sql("existing-node.sql"), (x[0],)
            ).fetchone()
            existing_target_node = cursor.execute(
                read_sql("existing-node.sql"), (x[1],)
            ).fetchone()

            if existing_edge or not existing_source_node or not existing_target_node:
                count -= 1
                continue

            cursor.execute(
                read_sql("insert-edge.sql"),
                (
                    count + i,
                    x[0],
                    x[1],
                    x[2],
                    json.dumps(x[3]),
                ),
            )

            cursor.execute(
                read_sql("insert-edge-embedding.sql"),
                (
                    count + i,
                    json.dumps(
                        embed_obj.get_embedding(
                            json.dumps(
                                (
                                    x[0],
                                    x[1],
                                    x[2],
                                    json.dumps(x[3]),
                                )
                            )
                        )
                    ),
                ),
            )

    return _connect_nodes


def remove_node(identifier: Any) -> CursorExecFunction:
    def _remove_node(cursor, connection):
        node = cursor.execute(
            "SELECT embed_id FROM nodes WHERE id=?", (identifier,)
        ).fetchone()

        if node is None:
            return

        rows = cursor.execute(
            "SELECT embed_id FROM edges WHERE source=? OR target=?",
            (identifier, identifier),
        ).fetchall()

        edge_ids = []
        if rows is not None:
            edge_ids = [i[0] for i in rows]

        cursor.execute(
            read_sql("delete-edge.sql"),
            (
                identifier,
                identifier,
            ),
        )

        for id in edge_ids:
            cursor.execute(read_sql("delete-edge-embedding.sql"), (id,))

        cursor.execute(read_sql("delete-node.sql"), (identifier,))

        cursor.execute(read_sql("delete-node-embedding.sql"), (node[0],))

    return _remove_node


def remove_nodes(identifiers: List[Any]) -> CursorExecFunction:
    def _remove_node(cursor, connection):
        for identifier in identifiers:
            node = cursor.execute(
                "SELECT embed_id FROM nodes WHERE id=?", (identifier,)
            ).fetchone()

            if node is None:
                continue

            rows = cursor.execute(
                "SELECT embed_id FROM edges WHERE source=? OR target=?",
                (identifier, identifier),
            ).fetchall()
            edge_ids = [i[0] for i in rows]

            cursor.execute(
                read_sql("delete-edge.sql"),
                (
                    identifier,
                    identifier,
                ),
            )

            for id in edge_ids:
                cursor.execute(read_sql("delete-edge-embedding.sql"), (id,))

            cursor.execute(read_sql("delete-node.sql"), (identifier,))

            cursor.execute(read_sql("delete-node-embedding.sql"), (node[0],))

    return _remove_node


def _generate_clause(
    key: str,
    predicate: str | None = None,
    joiner: str | None = None,
    tree: bool = False,
    tree_with_key: bool = False,
) -> str:
    """Given at minimum a key in the body json, generate a query clause
    which can be bound to a corresponding value at point of execution"""

    if predicate is None:
        predicate = "="  # can also be 'LIKE', '>', '<'
    if joiner is None:
        joiner = ""  # 'AND', 'OR', 'NOT'

    if tree:
        if tree_with_key:
            return clause_template.render(
                and_or=joiner, key=key, tree=tree, predicate=predicate
            )
        else:
            return clause_template.render(and_or=joiner, tree=tree, predicate=predicate)

    return clause_template.render(
        and_or=joiner, key=key, predicate=predicate, key_value=True
    )


def _generate_query(
    where_clauses: List[str],
    result_column: str | None = None,
    key: str | None = None,
    tree: bool = False,
) -> str:
    """Generate the search query, selecting either the id or the body,
    adding the json_tree function and optionally the key, as needed"""

    if result_column is None:
        result_column = "attribute"  # can also be 'id'

    if tree:
        if key:
            return search_template.render(
                result_column=result_column,
                tree=tree,
                key=key,
                search_clauses=where_clauses,
            )
        else:
            return search_template.render(
                result_column=result_column, tree=tree, search_clauses=where_clauses
            )

    return search_template.render(
        result_column=result_column, search_clauses=where_clauses
    )


def find_node(identifier: Any) -> CursorExecFunction:
    def _find_node(cursor, connection):
        query = _generate_query([clause_template.render(id_lookup=True)])
        result = cursor.execute(query, (identifier,)).fetchone()
        if result:
            if isinstance(result[0], str):
                return json.loads(result[0])
            else:
                return result[0]
        else:
            return {}

    return _find_node


def _parse_search_results(results: List[Tuple], idx: int = 0) -> List[Dict]:
    return [json.loads(item[idx]) for item in results]


def find_nodes(
    where_clauses: List[str],
    bindings: Tuple,
    tree_query: bool = False,
    key: str | None = None,
) -> CursorExecFunction:
    def _find_nodes(cursor, connection):
        query = _generate_query(where_clauses, key=key, tree=tree_query)
        return _parse_search_results(cursor.execute(query, bindings).fetchall())

    return _find_nodes


def find_neighbors(with_bodies: bool = False) -> str:
    return traverse_template.render(
        with_bodies=with_bodies, inbound=True, outbound=True
    )


def find_outbound_neighbors(with_bodies: bool = False) -> str:
    return traverse_template.render(with_bodies=with_bodies, outbound=True)


def find_inbound_neighbors(with_bodies: bool = False) -> str:
    return traverse_template.render(with_bodies=with_bodies, inbound=True)


def traverse(
    db_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    src: Any = None,
    tgt: Any = None,
    neighbors_fn: Callable[[bool], str] = find_neighbors,
    with_bodies: bool = False,
) -> List:
    def _traverse(cursor, connection):
        path = []
        target = json.dumps(tgt)
        rows = cursor.execute(neighbors_fn(with_bodies=with_bodies), (src,)).fetchall()
        for row in rows:
            if row:
                if with_bodies:
                    identifier, obj, _ = row
                    path.append(row)
                    if identifier == target and obj == "()":
                        break
                else:
                    identifier = row[0]
                    if identifier not in path:
                        path.append(identifier)
                        if identifier == target:
                            break
        return path

    return atomic(_traverse, db_url, auth_token)  # type: ignore


def connections_in() -> str:
    return read_sql("search-edges-inbound.sql")


def connections_out() -> str:
    return read_sql("search-edges-outbound.sql")


def get_connections_one_way(
    identifier: Any, direction: Callable[[], str] = connections_in
) -> CursorExecFunction:
    def _get_connections(cursor, connection):
        return cursor.execute(direction(), (identifier,)).fetchall()

    return _get_connections


def get_connections(identifier: Any) -> CursorExecFunction:
    def _get_connections(cursor, connection):
        return cursor.execute(
            read_sql("search-edges.sql"),
            (
                identifier,
                identifier,
            ),
        ).fetchall()

    return _get_connections


def pruning(threshold: float, k: int) -> CursorExecFunction:
    def _merge(cursor, connection):
        nodes = cursor.execute("SELECT id from nodes").fetchall()

        for node_id in nodes:
            node_data = find_node(node_id[0])(cursor, connection)

            if node_data is {}:
                continue

            node = cursor.execute(
                "SELECT label, attribute from nodes where id=?", (node_id[0],)
            ).fetchone()

            similar_nodes = vector_search_node(node_data, k, threshold)(
                cursor, connection
            )

            if len(similar_nodes) < 1:
                continue

            for rowid, _ in similar_nodes:
                similar_node_id = cursor.execute(
                    "SELECT id from nodes where embed_id=?", (rowid,)
                ).fetchone()

                # Skip the similar nodes to be merged
                if similar_node_id[0] == node_id[0]:
                    continue

                in_degree_query = cursor.execute(
                    "SELECT source, label, attribute FROM edges WHERE target = ?",
                    (similar_node_id[0],),
                )
                out_degree_query = cursor.execute(
                    "SELECT target, label, attribute FROM edges WHERE source = ?",
                    (similar_node_id[0],),
                )

                in_degree = in_degree_query.fetchall() if in_degree_query else []
                out_degree = out_degree_query.fetchall() if out_degree_query else []

                concatenated_attributes = {}
                concatenated_labels = ""

                for data in in_degree:
                    concatenated_attributes.update(json.loads(data[2]))
                    concatenated_labels += data[1] + ","

                    count = (
                        cursor.execute(
                            "SELECT COALESCE(MAX(embed_id), 0) FROM edges"
                        ).fetchone()[0]
                        + 1
                    )
                    cursor.execute(
                        read_sql("insert-edge.sql"),
                        (count, data[0], node_id[0], data[1], data[2]),
                    )

                    edge_data = {
                        "source_id": data[0],
                        "target_id": node_id[0],
                        "label": data[1],
                        "attributes": data[2],
                    }
                    cursor.execute(
                        read_sql("insert-edge-embedding.sql"),
                        (
                            count,
                            json.dumps(embed_obj.get_embedding(json.dumps(edge_data))),
                        ),
                    )

                for data in out_degree:
                    concatenated_attributes.update(json.loads(data[2]))
                    concatenated_labels += data[1] + ","

                    count = (
                        cursor.execute(
                            "SELECT COALESCE(MAX(embed_id), 0) FROM edges"
                        ).fetchone()[0]
                        + 1
                    )
                    cursor.execute(
                        read_sql("insert-edge.sql"),
                        (count, node_id[0], data[0], data[1], data[2]),
                    )

                    edge_data = {
                        "source_id": node_id[0],
                        "target_id": data[0],
                        "label": data[1],
                        "attributes": data[2],
                    }
                    cursor.execute(
                        read_sql("insert-edge-embedding.sql"),
                        (
                            count,
                            json.dumps(embed_obj.get_embedding(json.dumps(edge_data))),
                        ),
                    )

                updated_attributes = json.loads(node[1]) if node[1] else {}
                updated_attributes.update(concatenated_attributes)
                upsert_node(
                    node_id[0], node[0] + "," + concatenated_labels, updated_attributes
                )(cursor, connection)
                remove_node(similar_node_id[0])(cursor, connection)

            connection.commit()

    return _merge


def find_similar_nodes(label: str, threshold: float):
    pass
