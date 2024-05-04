"""
Provide a higher level API to the database using Pydantic
"""

from __future__ import annotations

import json
import os
import pathlib
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, List, Optional, Union, Dict, Tuple, Callable

import instructor
import libsql_experimental as libsql  # type: ignore
from contextlib import AbstractContextManager

import networkx as nx  # type: ignore
from graphviz import Digraph  # type: ignore
from jinja2 import Environment, BaseLoader, select_autoescape
from litellm.llms import openai  # type: ignore
from matplotlib import pyplot as plt
from dotenv import load_dotenv

from personal_graph.embeddings import OpenAIEmbeddingsModel
from personal_graph.models import Node, EdgeInput, KnowledgeGraph, Edge
from personal_graph.visualizers import _as_dot_node, _as_dot_label

load_dotenv()

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


@dataclass
class OpenAIClient:
    client: openai.OpenAI = openai.OpenAI(
        api_key="",
        base_url=os.getenv("LITE_LLM_BASE_URL", ""),
        default_headers={"Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"},
    )


@dataclass
class EmbeddingClient(OpenAIClient):
    model_name: str = "openai/text-embedding-3-small"
    dimensions: int = 384


@dataclass
class LLMClient(OpenAIClient):
    model_name: str = "openai/gpt-3.5-turbo"


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


class Graph(AbstractContextManager):
    def __init__(
        self,
        *,
        db_url: Optional[str] = None,
        db_auth_token: Optional[str] = None,
        llm_client: LLMClient,
        embedding_model_client: EmbeddingClient,
    ):
        self.db_url = db_url
        self.db_auth_token = db_auth_token
        self.llm_client = llm_client

        self.embedding_model = OpenAIEmbeddingsModel(
            embedding_model_client.client,
            embedding_model_client.model_name,
            embedding_model_client.dimensions,
        )
        self.env = Environment(
            loader=SqlTemplateLoader(), autoescape=select_autoescape()
        )
        self.clause_template = self.env.get_template("search-where.template")
        self.search_template = self.env.get_template("search-node.template")
        self.traverse_template = self.env.get_template("traverse.template")

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return "Not of Graph Type"
        return self.db_url == other.db_url and self.db_auth_token == other.db_auth_token

    def __enter__(self, schema_file: str = "schema.sql") -> Graph:
        self._initialize(
            schema_file=schema_file,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    # Low level database apis
    def _atomic(
        self,
        cursor_exec_fn: CursorExecFunction,
    ) -> Any:
        connection = None
        try:
            if not self.db_url:
                connection = libsql.connect(":memory:")
            else:
                connection = libsql.connect(
                    database=self.db_url, auth_token=self.db_auth_token
                )

            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = TRUE;")
            results = cursor_exec_fn(cursor, connection)
            connection.commit()
        finally:
            if connection:
                pass
        return results

    def _initialize(
        self,
        schema_file: str = "schema.sql",
    ) -> Any:
        def _init(cursor, connection):
            schema_sql = read_sql(schema_file)
            connection.executescript(schema_sql)
            connection.commit()

        return self._atomic(_init)

    def _set_id(self, identifier: Any, data: Dict) -> Dict:
        if identifier is not None:
            data["id"] = identifier
        return data

    def _insert_node(
        self,
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
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0]
            + 1
        )

        set_data = self._set_id(identifier, data)

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
            (
                count,
                json.dumps(self.embedding_model.get_embedding(json.dumps(set_data))),
            ),
        )
        connection.commit()

    def _vector_search_node(
        self,
        data: Dict,
        threshold: Optional[float] = None,
        desc: Optional[bool] = False,
        k: int = 10,
        sort_by: Optional[str] = "",
    ) -> CursorExecFunction:
        def _search_node(cursor, connection):
            embed_json = json.dumps(
                self.embedding_model.get_embedding(json.dumps(data))
            )

            nodes = cursor.execute(
                read_sql("vector-search-node.sql"),
                (embed_json, k, sort_by, desc, sort_by, sort_by, desc, sort_by),
            ).fetchall()

            if not nodes:
                return None

            if threshold is not None:
                return [node for node in nodes if node[4] < threshold][:k]
            else:
                return nodes[:k]

        return _search_node

    def _vector_search_edge(
        self,
        data: Dict,
        threshold: Optional[float] = None,
        desc: bool = False,
        k: int = 10,
    ) -> CursorExecFunction:
        def _search_edge(cursor, connection):
            embed = json.dumps(self.embedding_model.get_embedding(json.dumps(data)))
            if desc:
                edges = cursor.execute(
                    read_sql("vector-search-edge-desc.sql"), (embed, k)
                ).fetchall()

            else:
                edges = cursor.execute(
                    read_sql("vector-search-edge.sql"), (embed, k)
                ).fetchall()

            if not edges:
                return None

            if threshold is not None:
                filtered_results = [edge for edge in edges if edge[5] < threshold]
                return filtered_results[:k]
            else:
                return edges[:k]

        return _search_edge

    def _add_node(
        self,
        label: str,
        data: Dict,
        identifier: Any = None,
    ) -> CursorExecFunction:
        def _add_single_node(cursor, connection):
            self._insert_node(cursor, connection, identifier, label, data)

        return _add_single_node

    def _add_nodes(
        self,
        nodes: List[Dict],
        labels: List[str],
        ids: List[Any],
    ) -> CursorExecFunction:
        def _add_multi_nodes(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(embed_id), 0) FROM nodes"
                ).fetchone()[0]
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
                        json.dumps(self._set_id(x[0], x[2])),
                    ),
                )
                cursor.execute(
                    read_sql("insert-node-embedding.sql"),
                    (
                        count + i,
                        json.dumps(
                            self.embedding_model.get_embedding(
                                json.dumps(self._set_id(x[0], x[2]))
                            )
                        ),
                    ),
                )

        return _add_multi_nodes

    def _upsert_single_node(
        self,
        cursor: libsql.Cursor,
        connection: libsql.Connection,
        identifier: Any,
        label: str,
        data: Dict,
    ) -> None:
        current_data = self._find_node(identifier)(cursor, connection)

        if not current_data:
            # no prior record exists, so regular insert
            self._insert_node(cursor, connection, identifier, label, data)
        else:
            current_id = current_data["id"]
            id_to_be_updated = cursor.execute(
                "SELECT embed_id from nodes where id=?", (current_id,)
            ).fetchone()[0]
            updated_data = {**current_data, **data}

            cursor.execute(read_sql("delete-node-embedding.sql"), (id_to_be_updated,))

            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(embed_id), 0) FROM nodes"
                ).fetchone()[0]
                + 1
            )

            cursor.execute(
                read_sql("insert-node-embedding.sql"),
                (
                    count,
                    json.dumps(
                        self.embedding_model.get_embedding(json.dumps(updated_data))
                    ),
                ),
            )
            cursor.execute(
                read_sql("update-node.sql"),
                (
                    label,
                    json.dumps(self._set_id(identifier, updated_data)),
                    count,
                    identifier,
                ),
            )

    def _upsert_node(
        self, identifier: Any, label: str, data: Dict
    ) -> CursorExecFunction:
        def _upsert(cursor, connection):
            self._upsert_single_node(cursor, connection, identifier, label, data)

        return _upsert

    def _upsert_nodes(
        self,
        nodes: List[Dict],
        labels: List[str],
        ids: List[Any],
    ) -> CursorExecFunction:
        def _upsert(cursor, connection):
            for id, label, node in zip(ids, labels, nodes):
                self._upsert_single_node(cursor, connection, id, label, node)

        return _upsert

    def _connect_nodes(
        self,
        source_id: Any,
        target_id: Any,
        label: str,
        attributes: Dict = {},
    ) -> CursorExecFunction:
        def _connect_single_nodes(cursor, connection):
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
                cursor.execute(
                    "SELECT COALESCE(MAX(embed_id), 0) FROM edges"
                ).fetchone()[0]
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
                (
                    count,
                    json.dumps(
                        self.embedding_model.get_embedding(json.dumps(edge_data))
                    ),
                ),
            )
            connection.commit()

        return _connect_single_nodes

    def _connect_many_nodes(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Dict],
    ) -> CursorExecFunction:
        def _connect_multi_nodes(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(embed_id), 0) FROM edges"
                ).fetchone()[0]
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

                if (
                    existing_edge
                    or not existing_source_node
                    or not existing_target_node
                ):
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
                            self.embedding_model.get_embedding(
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

        return _connect_multi_nodes

    def _remove_node(self, identifier: Any) -> CursorExecFunction:
        def _remove_single_node(cursor, connection):
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

        return _remove_single_node

    def _remove_nodes(self, identifiers: List[Any]) -> CursorExecFunction:
        def _remove_multi_node(cursor, connection):
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
                connection.commit()

        return _remove_multi_node

    def _generate_clause(
        self,
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
                return self.clause_template.render(
                    and_or=joiner, key=key, tree=tree, predicate=predicate
                )
            else:
                return self.clause_template.render(
                    and_or=joiner, tree=tree, predicate=predicate
                )

        return self.clause_template.render(
            and_or=joiner, key=key, predicate=predicate, key_value=True
        )

    def _generate_query(
        self,
        where_clauses: List[str],
        result_column: str | None = None,
        key: str | None = None,
        tree: bool = False,
    ) -> str:
        """Generate the search query, selecting either the id or the body,
        adding the json_tree function and optionally the key, as needed"""

        if result_column is None:
            result_column = "attributes"  # can also be 'id'

        if tree:
            if key:
                return self.search_template.render(
                    result_column=result_column,
                    tree=tree,
                    key=key,
                    search_clauses=where_clauses,
                )
            else:
                return self.search_template.render(
                    result_column=result_column, tree=tree, search_clauses=where_clauses
                )

        return self.search_template.render(
            result_column=result_column, search_clauses=where_clauses
        )

    def _find_node(self, identifier: Any) -> CursorExecFunction:
        def _find_single_node(cursor, connection):
            query = self._generate_query([self.clause_template.render(id_lookup=True)])
            result = cursor.execute(query, (identifier,)).fetchone()
            if result:
                if isinstance(result[0], str):
                    return json.loads(result[0])
                else:
                    return result[0]
            else:
                return {}

        return _find_single_node

    def _find_label(self, identifier: Any) -> CursorExecFunction:
        def _search_label(cursor, connection):
            node_label = cursor.execute(
                "SELECT label from nodes where id=?", (identifier,)
            ).fetchone()
            return node_label

        return _search_label

    def _parse_search_results(self, results: List[Tuple], idx: int = 0) -> List[Dict]:
        return [json.loads(item[idx]) for item in results]

    def _find_nodes(
        self,
        where_clauses: List[str],
        bindings: Tuple,
        tree_query: bool = False,
        key: str | None = None,
    ) -> CursorExecFunction:
        def _find_multi_nodes(cursor, connection):
            query = self._generate_query(where_clauses, key=key, tree=tree_query)
            return self._parse_search_results(
                cursor.execute(query, bindings).fetchall()
            )

        return _find_multi_nodes

    def _find_neighbors(self, with_bodies: bool = False) -> str:
        return self.traverse_template.render(
            with_bodies=with_bodies, inbound=True, outbound=True
        )

    def _find_outbound_neighbors(self, with_bodies: bool = False) -> str:
        return self.traverse_template.render(with_bodies=with_bodies, outbound=True)

    def _find_inbound_neighbors(self, with_bodies: bool = False) -> str:
        return self.traverse_template.render(with_bodies=with_bodies, inbound=True)

    def _traverse(
        self,
        src: Any = None,
        tgt: Any = None,
        neighbors_fn: Callable[[bool], str] = _find_neighbors,  # type: ignore
        with_bodies: bool = False,
    ) -> List:
        def _traverse_graph(cursor, connection):
            path = []
            target = json.dumps(tgt)
            rows = cursor.execute(
                neighbors_fn(with_bodies=with_bodies), (src,)
            ).fetchall()
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

        return self._atomic(_traverse_graph)  # type: ignore

    def _connections_in(self) -> str:
        return read_sql("search-edges-inbound.sql")

    def _connections_out(self) -> str:
        return read_sql("search-edges-outbound.sql")

    def _get_connections_one_way(
        self,
        identifier: Any,
        direction: Callable[[], str] = _connections_in,  # type: ignore
    ) -> CursorExecFunction:
        def _get_connections(cursor, connection):
            return cursor.execute(direction(), (identifier,)).fetchall()

        return _get_connections

    def _get_connections(self, identifier: Any) -> CursorExecFunction:
        def _get_all_connections(cursor, connection):
            return cursor.execute(
                read_sql("search-edges.sql"),
                (
                    identifier,
                    identifier,
                ),
            ).fetchall()

        return _get_all_connections

    def _pruning(self, threshold: float) -> CursorExecFunction:
        def _merge(cursor, connection):
            nodes = cursor.execute("SELECT id from nodes").fetchall()

            for node_id in nodes:
                node_data = self._find_node(node_id[0])(cursor, connection)

                if node_data is {}:
                    continue

                node = cursor.execute(
                    "SELECT label, attributes from nodes where id=?", (node_id[0],)
                ).fetchone()

                similar_nodes = self._vector_search_node(
                    node_data, threshold, False, 3
                )(cursor, connection)

                if similar_nodes is None:
                    continue

                if len(similar_nodes) < 1:
                    continue

                for rowid, _, _, _, _ in similar_nodes:
                    similar_node_id = cursor.execute(
                        "SELECT id from nodes where embed_id=?", (rowid,)
                    ).fetchone()

                    if similar_node_id is None:
                        continue

                    # Skip the similar nodes to be merged
                    if similar_node_id[0] == node_id[0]:
                        continue

                    in_degree_query = cursor.execute(
                        "SELECT source, label, attributes FROM edges WHERE target = ?",
                        (similar_node_id[0],),
                    )
                    out_degree_query = cursor.execute(
                        "SELECT target, label, attributes FROM edges WHERE source = ?",
                        (similar_node_id[0],),
                    )

                    in_degree = in_degree_query.fetchall() if in_degree_query else []
                    out_degree = out_degree_query.fetchall() if out_degree_query else []

                    concatenated_attributes = {}
                    concatenated_labels = ""

                    for data in in_degree:
                        for key, value in json.loads(data[2]).items():
                            if key in concatenated_attributes:
                                # If the key already exists, update its value
                                concatenated_attributes[key] += value
                            else:
                                # If the key doesn't exist, add a new key-value pair
                                concatenated_attributes[key] = value

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
                        connection.commit()

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
                                json.dumps(
                                    self.embedding_model.get_embedding(
                                        json.dumps(edge_data)
                                    )
                                ),
                            ),
                        )
                        connection.commit()

                    for data in out_degree:
                        for key, value in json.loads(data[2]).items():
                            if key in concatenated_attributes:
                                # If the key already exists, update its value
                                concatenated_attributes[key] += value
                            else:
                                # If the key doesn't exist, add a new key-value pair
                                concatenated_attributes[key] = value
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
                        connection.commit()

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
                                json.dumps(
                                    self.embedding_model.get_embedding(
                                        json.dumps(edge_data)
                                    )
                                ),
                            ),
                        )
                        connection.commit()

                    updated_attributes = json.loads(node[1]) if node[1] else {}
                    updated_attributes.update(concatenated_attributes)
                    self._upsert_node(
                        node_id[0],
                        node[0] + "," + concatenated_labels,
                        updated_attributes,
                    )(cursor, connection)
                    self._remove_node(similar_node_id[0])(cursor, connection)

                connection.commit()

        return _merge

    def _find_similar_nodes(
        self,
        label: str,
        threshold: Optional[float] = None,
    ):
        def _identical_nodes(cursor, connection):
            nodes = cursor.execute(
                "SELECT * FROM nodes WHERE label LIKE ?", ("%" + label + "%",)
            ).fetchall()

            similar_rows = []
            for node in nodes:
                similar_nodes = self._vector_search_node(node, threshold, False, 2)(
                    cursor, connection
                )

                if len(similar_nodes) < 1:
                    continue

                for rowid, _ in similar_nodes:
                    row = cursor.execute(
                        "SELECT id, label, attributes from nodes where embed_id=?",
                        (rowid,),
                    ).fetchone()

                    if row in similar_rows:
                        continue
                    similar_rows.append(row)
            return similar_rows

        return _identical_nodes

    def _nodes_list(self) -> CursorExecFunction:
        def _fetch_nodes_from_db(cursor, connection):
            nodes = cursor.execute("SELECT id from nodes").fetchall()
            ids = [id[0] for id in nodes]

            return ids

        return _fetch_nodes_from_db

    def _find_indegree_edges(self, target_id: Any) -> CursorExecFunction:
        def _indegree_edges(cursor, connection):
            indegree = cursor.execute(
                "SELECT source, label, attributes from edges where target=? ",
                (target_id,),
            )

            if indegree:
                indegree = indegree.fetchall()

            return indegree

        return _indegree_edges

    def _find_outdegree_edges(self, source_id: Any) -> CursorExecFunction:
        def _outdegree_edges(cursor, connection):
            outdegree = cursor.execute(
                "SELECT target, label, attributes from edges where source=? ",
                (source_id,),
            )

            if outdegree:
                outdegree = outdegree.fetchall()

            return outdegree

        return _outdegree_edges

    def _all_connected_nodes(
        self, node_or_edge: Union[Node | Edge]
    ) -> CursorExecFunction:
        def _connected_nodes(cursor, connection):
            nodes = None
            if isinstance(node_or_edge, Node):
                index = node_or_edge.id
                nodes = cursor.execute(
                    "SELECT source, target FROM edges WHERE source=? OR target=?",
                    (index, index),
                )
            elif isinstance(node_or_edge, Edge):
                index1, index2 = node_or_edge.source, node_or_edge.target
                nodes = cursor.execute(
                    "SELECT source, target FROM edges WHERE source=? OR target=? OR source=? OR target=?",
                    (index1, index1, index2, index2),
                )

            resultant_connected_nodes = []
            if nodes:
                connected_nodes = nodes.fetchall()
                for connected_node in connected_nodes:
                    for id in connected_node:
                        res = cursor.execute(
                            "SELECT id, label, attributes from nodes where id=?",
                            (id,),
                        ).fetchone()
                        if res not in resultant_connected_nodes:
                            resultant_connected_nodes.append(
                                Node(id=res[0], label=res[1], attributes=res[2])
                            )

                return resultant_connected_nodes

        return _connected_nodes

    # Network analysis libraries apis
    def to_networkx(self, post_visualize: bool) -> nx.Graph:
        """
        Convert the graph database to a NetworkX DiGraph object.
        """
        G = nx.Graph()  # Empty Graph with no nodes and edges

        node_ids = self.fetch_ids_from_db()
        # Add edges to networkX
        for source_id in node_ids:
            outdegree_edges = self.search_outdegree_edges(source_id)
            for target_id, edge_label, edge_data in outdegree_edges:
                edge_data = json.loads(edge_data)
                edge_data["label"] = edge_label
                G.add_edge(source_id, target_id, **edge_data)

        for target_id in node_ids:
            indegree_edges = self.search_indegree_edges(target_id)
            for source_id, edge_label, edge_data in indegree_edges:
                edge_data = json.loads(edge_data)
                edge_data["label"] = edge_label
                G.add_edge(source_id, target_id, **edge_data)

        for node_id in node_ids:
            node_data = self.search_node(node_id)
            node_label = self.search_node_label(node_id)
            node_data["label"] = node_label
            G.add_node(node_id, **node_data)

        if post_visualize:
            # Visualizing the NetworkX Graph
            plt.figure(
                figsize=(20, 20), dpi=100
            )  # Increase the figure size and resolution
            pos = nx.spring_layout(
                G, scale=6
            )  # Use spring layout for better node positioning

            nx.draw_networkx(
                G,
                pos,
                with_labels=True,
                nodelist=G.nodes(),
                edgelist=G.edges(),
                node_size=600,
                node_color="skyblue",
                edge_color="gray",
                width=1.5,
            )
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=nx.get_edge_attributes(G, "label")
            )
            plt.axis("off")  # Show the axes
            plt.savefig("networkX_graph.png")

        return G

    def from_networkx(
        self, network_graph: nx, post_visualize: bool, override: bool
    ) -> Graph:
        if override:
            node_ids = self.fetch_ids_from_db()
            self.remove_nodes(node_ids)

        node_ids_with_edges = set()
        kg = KnowledgeGraph()

        # Convert networkX edges to personal graph edges
        for source_id, target_id, edge_data in network_graph.edges(data=True):
            edge_attributes: Dict[str, Any] = edge_data
            edge_label: str = edge_attributes["label"]

            if not override:
                # Check if the node with the given id exists, if not then firstly add the node.
                source = self.search_node(source_id)
                if source is []:
                    self.add_node(
                        Node(
                            id=str(source_id),
                            label=edge_label if edge_label else "",
                            attributes=edge_attributes,
                        )
                    )
                else:
                    node_ids_with_edges.add(str(source_id))

                target = self.search_node(target_id)
                if target is []:
                    node_ids_with_edges.remove(str(target_id))
                    self.add_node(
                        Node(
                            id=str(target_id),
                            label=edge_label if edge_label else "",
                            attributes=edge_attributes,
                        )
                    )
                else:
                    node_ids_with_edges.add(str(target_id))

            # After adding the new nodes if exists , add an edge
            edge = Edge(
                source=str(source_id),
                target=str(target_id),
                label=edge_label if edge_label else "",
                attributes=edge_attributes,
            )
            kg.edges.append(edge)

        # Convert networkX nodes to personal graph nodes
        for node_id, node_data in network_graph.nodes(data=True):
            if str(node_id) not in node_ids_with_edges:
                node_attributes: Dict[str, Any] = node_data
                node_label: str = node_attributes.pop("label", "")
                node = Node(
                    id=str(node_id),
                    label=node_label[0],
                    attributes=json.dumps(node_attributes),
                )

                if not override:
                    # Check if the node exists
                    if_node_exists = self.search_node(node_id)

                    if if_node_exists:
                        self.update_node(node)
                    else:
                        self.add_node(node)
                else:
                    self.add_node(node)
                kg.nodes.append(node)

        for edge in kg.edges:
            source_node_attributes = self.search_node(edge.source)
            source_node_label = self.search_node_label(edge.source)
            target_node_attributes = self.search_node(edge.target)
            target_node_label = self.search_node_label(edge.target)
            final_edge_to_be_inserted = EdgeInput(
                source=Node(
                    id=edge.source,
                    label=source_node_label
                    if isinstance(source_node_label, str)
                    else "Sample label",
                    attributes=source_node_attributes
                    if isinstance(source_node_attributes, Dict)
                    else "Sample Attributes",
                ),
                target=Node(
                    id=edge.target,
                    label=target_node_label
                    if isinstance(target_node_label, str)
                    else "Sample label",
                    attributes=target_node_attributes
                    if isinstance(target_node_attributes, Dict)
                    else "Sample Attributes",
                ),
                label=edge.label if isinstance(edge.label, str) else "Sample label",
                attributes=edge.attributes
                if isinstance(edge.attributes, Dict)
                else "Sample Attributes",
            )
            self.add_edge(final_edge_to_be_inserted)

        if post_visualize:
            # Visualize the personal graph using graphviz
            dot = Digraph()

            for node in kg.nodes:
                dot.node(node.id, label=f"{node.label}: {node.id}")

            for edge in kg.edges:
                dot.edge(edge.source, edge.target, label=edge.label)

            dot.render("personal_graph.gv", view=True)

        return self

    # Natural Language apis
    def _generate_graph(self, query: str) -> KnowledgeGraph:
        client = instructor.from_openai(self.llm_client.client)
        knowledge_graph = client.chat.completions.create(
            model=self.llm_client.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a high quality knowledge graph generator based on the user query for the purpose of generating descriptive, informative, detailed and accurate knowledge graphs. You can generate proper nodes and edges as a knowledge graph.",
                },
                {
                    "role": "user",
                    "content": f"Help me describe this user query as a detailed knowledge graph with meaningful relationships that should provide some descriptive attributes(attribute is the detailed and proper information about the edge) and informative labels about the nodes and relationship. Try to make most of the relationships between similar nodes: {query}",
                },
            ],
            response_model=KnowledgeGraph,
        )
        return knowledge_graph

    def _visualize_knowledge_graph(self, kg: KnowledgeGraph) -> Digraph:
        dot = Digraph(comment="Knowledge Graph")

        # Add nodes
        for node in kg.nodes:
            dot.node(str(node.id), node.label, color="black")

        # Add edges
        for edge in kg.edges:
            dot.edge(str(edge.source), str(edge.target), edge.label, color="black")

        return dot

    def _insert_into_graph(self, text: str) -> KnowledgeGraph:
        uuid_dict = {}
        kg = self._generate_graph(text)

        try:
            for node in kg.nodes:
                uuid_dict[node.id] = str(uuid.uuid4())
                self._atomic(
                    self._add_node(
                        node.label,
                        {"body": node.attributes},
                        uuid_dict[node.id],
                    )
                )

            for edge in kg.edges:
                self._atomic(
                    self._connect_nodes(
                        uuid_dict[edge.source],
                        uuid_dict[edge.target],
                        edge.label,
                        {"body": edge.attributes},
                    )
                )
        except KeyError:
            return KnowledgeGraph()

        return kg

    def _search_from_graph(
        self, text: str, *, limit: int = 5, descending: bool = False
    ) -> KnowledgeGraph:
        try:
            similar_nodes = self._atomic(
                self._vector_search_node({"body": text}, 0.9, descending, limit)
            )
            similar_edges = self._atomic(
                self._vector_search_edge({"body": text}, 0.9, descending, limit)
            )

            resultant_subgraph = KnowledgeGraph()

            if similar_edges and similar_nodes is None or similar_nodes is None:
                return resultant_subgraph

            resultant_subgraph.nodes = [
                Node(id=node[1], label=node[2], attributes=node[3])
                for node in similar_nodes
            ]

            for node in similar_nodes:
                similar_node = Node(id=node[1], label=node[2], attributes=node[3])
                nodes = self._atomic(self._all_connected_nodes(similar_node))

                if not nodes:
                    continue

                for i in nodes:
                    if i not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(i)

            resultant_subgraph.edges = [
                Edge(source=edge[1], target=edge[2], label=edge[3], attributes=edge[4])
                for edge in similar_edges
            ]
            for edge in similar_edges:
                similar_edge = Edge(
                    source=edge[1],
                    target=edge[2],
                    label=edge[3],
                    attributes=edge[4],
                )
                nodes = self._atomic(self._all_connected_nodes(similar_edge))

                if not nodes:
                    continue

                for node in nodes:
                    if node not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(node)

        except KeyError:
            return KnowledgeGraph()

        return resultant_subgraph

    # Visualization api
    def _graphviz_visualize(
        self,
        dot_file: Optional[str] = None,
        path: List[Any] = [],
        connections: Any = _get_connections,
        format: str = "png",
        exclude_node_keys: List[str] = [],
        hide_node_key: bool = False,
        node_kv: str = " ",
        exclude_edge_keys: List[str] = [],
        hide_edge_key: bool = False,
        edge_kv: str = " ",
    ) -> Digraph:
        ids = []
        for i in path:
            ids.append(str(i))
            for edge in self._atomic(connections(self, i)):  # type: ignore
                _, src, tgt, _, _, _, _ = edge
                if src not in ids:
                    ids.append(src)
                if tgt not in ids:
                    ids.append(tgt)

        dot = Digraph()

        visited = []
        edges = []
        for i in ids:
            if i not in visited:
                node = self._atomic(self._find_node(i))  # type: ignore
                name, label = _as_dot_node(
                    node, exclude_node_keys, hide_node_key, node_kv
                )
                dot.node(name, label=label)
                for edge in self._atomic(connections(self, i)):  # type: ignore
                    if edge not in edges:
                        _, src, tgt, _, prps, _, _ = edge
                        props = json.loads(prps)
                        dot.edge(
                            str(src),
                            str(tgt),
                            label=_as_dot_label(
                                props, exclude_edge_keys, hide_edge_key, edge_kv
                            )
                            if props
                            else None,
                        )
                        edges.append(edge)
                visited.append(i)

        dot.render(dot_file, format=format)
        return dot

    def _attribute_search_node(
        self, text: str, limit: int, descending: bool, sort_by: Optional[str]
    ):
        try:
            similar_nodes = self._atomic(
                self._vector_search_node(
                    {"body": text}, 0.9, descending, limit, sort_by
                )
            )

        except KeyError:
            return []

        return similar_nodes

    # High level apis
    def add_node(self, node: Node) -> None:
        self._atomic(
            self._add_node(
                node.label,
                json.loads(node.attributes)
                if isinstance(node.attributes, str)
                else node.attributes,
                node.id,
            )
        )

    def add_nodes(self, nodes: List[Node]) -> None:
        labels: List[str] = [node.label for node in nodes]
        attributes: List[Union[Dict[str, str]]] = [
            json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes
            for node in nodes
        ]
        ids: List[Any] = [node.id for node in nodes]
        add_nodes_func = self._add_nodes(
            nodes=attributes,
            labels=labels,
            ids=ids,
        )
        self._atomic(add_nodes_func)

    def add_edge(self, edge: EdgeInput) -> None:
        connect_nodes_func = self._connect_nodes(
            edge.source.id,
            edge.target.id,
            edge.label,
            json.loads(edge.attributes)
            if isinstance(edge.attributes, str)
            else edge.attributes,
        )
        self._atomic(connect_nodes_func)

    def add_edges(self, edges: List[EdgeInput]) -> None:
        sources: List[Any] = [edge.source.id for edge in edges]
        targets: List[Any] = [edge.target.id for edge in edges]
        labels: List[str] = [edge.label for edge in edges]
        attributes: List[Union[Dict[str, str]]] = [
            json.loads(edge.attributes)
            if isinstance(edge.attributes, str)
            else edge.attributes
            for edge in edges
        ]
        connect_many_nodes_func = self._connect_many_nodes(
            sources=sources,
            targets=targets,
            labels=labels,
            attributes=attributes,
        )
        self._atomic(connect_many_nodes_func)

    def update_node(self, node: Node) -> None:
        upsert_node_func = self._upsert_node(
            identifier=node.id,
            label=node.label,
            data=json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
        )
        self._atomic(upsert_node_func)

    def update_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.update_node(node)

    def remove_node(self, id: Any) -> None:
        self._atomic(self._remove_node(id))

    def remove_nodes(self, ids: List[Any]) -> None:
        self._atomic(self._remove_nodes(ids))

    def search_node(self, node_id: Any) -> Any:
        return self._atomic(self._find_node(node_id))

    def search_node_label(self, node_id: Any) -> Any:
        return self._atomic(self._find_label(node_id))

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        neighbors_fn = (
            self._find_neighbors if with_bodies else self._find_outbound_neighbors
        )
        path = self._traverse(
            src=source,
            tgt=target,
            neighbors_fn=neighbors_fn,
            with_bodies=with_bodies,
        )
        return path

    def insert_into_graph(self, text: str) -> KnowledgeGraph:
        kg: KnowledgeGraph = self._insert_into_graph(text)
        return kg

    def search_from_graph(self, text: str) -> KnowledgeGraph:
        kg: KnowledgeGraph = self._search_from_graph(text)
        return kg

    def visualize_graph(self, kg: KnowledgeGraph) -> Digraph:
        return self._visualize_knowledge_graph(kg)

    def merge_by_similarity(self, threshold) -> None:
        self._atomic(self._pruning(threshold))

    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        return self._atomic(self._find_similar_nodes(label, threshold))

    def visualize(self, file: str, path: List[str]) -> Digraph:
        return self._graphviz_visualize(file, path)

    def fetch_ids_from_db(self) -> List[str]:
        return self._atomic(self._nodes_list())

    def search_indegree_edges(self, target) -> List[Any]:
        return self._atomic(self._find_indegree_edges(target))

    def search_outdegree_edges(self, source) -> List[Any]:
        return self._atomic(self._find_outdegree_edges(source))

    def is_unique_prompt(self, text: str, threshold: float) -> bool:
        similar_nodes = self._atomic(
            self._vector_search_node({"body": text}, threshold, False, 1)
        )

        if not similar_nodes:
            return True
        return False

    def pg_to_networkx(self, *, post_visualize: bool = False):
        nx = self.to_networkx(post_visualize=post_visualize)
        return nx

    def networkx_to_pg(
        self, networkx_graph: nx, *, post_visualize: bool = False, override: bool = True
    ):
        pg = self.from_networkx(
            networkx_graph, post_visualize=post_visualize, override=override
        )
        return pg

    def insert(
        self,
        text: str,
        attributes: Dict,
    ) -> None:
        node = Node(
            id=str(uuid.uuid4()),
            label=text,
            attributes=json.dumps(attributes),
        )
        self.add_node(node)

    def search(
        self,
        text: str,
        *,
        descending: bool = False,
        limit: int = 1,
        sort_by: Optional[str] = "",
    ):
        results = self._attribute_search_node(
            text, limit=limit, descending=descending, sort_by=sort_by
        )
        return results
