import json
from pathlib import Path

import sqlean as sqlite3  # type: ignore
from functools import lru_cache

from graphviz import Digraph  # type: ignore
from typing import Any, Callable, Dict, Optional, List, Union, Tuple
from personal_graph.models import Node, Edge
from jinja2 import BaseLoader, Environment, select_autoescape

from personal_graph.visualizers import _as_dot_node, _as_dot_label
from personal_graph.database.db import DB

CursorExecFunction = Callable[[sqlite3.Cursor, sqlite3.Connection], Any]


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(Path(__file__).parent.resolve() / "raw-queries" / sql_file) as f:
        return f.read()


class SqlTemplateLoader(BaseLoader):
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def get_source(
        self, environment: Environment, template: str
    ) -> Tuple[str, str, Callable[[], bool]]:
        def uptodate() -> bool:
            return True

        template_path = self.templates_dir / template

        # Return the source code, the template name, and the uptodate function
        return read_sql(template_path), template, uptodate


class SQLite(DB):
    def __init__(
        self,
        *,
        use_in_memory: bool = False,
        local_path: Optional[str] = None,
        vector0_so_path: Optional[str] = None,
        vss0_so_path: Optional[str] = None,
    ):
        super().__init__()
        self.use_in_memory = use_in_memory
        self.vector0_so_path = vector0_so_path
        self.vss0_so_path = vss0_so_path
        self.local_path = local_path

        self.env = Environment(
            loader=SqlTemplateLoader(Path(__file__).parent / "raw-queries"),
            autoescape=select_autoescape(),
        )
        self.clause_template = self.env.get_template("search-where.template")
        self.search_template = self.env.get_template("search-node.template")
        self.traverse_template = self.env.get_template("traverse.template")

    def __eq__(self, other):
        return self.use_in_memory == other.use_in_memory

    def __repr__(self):
        return (
            f"SQLite(\n"
            f"    local_path={self.local_path},\n"
            f"    use_in_memory={self.use_in_memory},\n"
            f"    vector0_so_path='{self.vector0_so_path}',\n"
            f"    vss0_so_path='{self.vss0_so_path}'\n"
            f"  ),"
        )

    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        if not hasattr(self, "_connection"):
            if self.use_in_memory:
                self._connection = sqlite3.connect(":memory:")
            else:
                self._connection = sqlite3.connect(self.local_path)

            self._connection.enable_load_extension(True)
            if self.vector0_so_path and self.vss0_so_path:
                self._connection.load_extension(self.vector0_so_path)
                self._connection.load_extension(self.vss0_so_path)

        try:
            cursor = self._connection.cursor()
            results = cursor_exec_fn(cursor, self._connection)
            self._connection.commit()
        finally:
            pass
        return results

    def save(self):
        self._connection.commit()

    def initialize(self):
        def _init(cursor, connection):
            schema_sql = read_sql(Path("schema.sql"))
            connection.executescript(schema_sql)
            connection.commit()

        return self.atomic(_init)

    def _set_id(self, identifier: Any, data: Dict) -> Dict:
        if identifier is not None:
            data["id"] = identifier
        return data

    def _insert_node(
        self,
        cursor: sqlite3.Cursor,
        connection: sqlite3.Connection,
        identifier: Any,
        label: str,
        data: Dict,
    ) -> None:
        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0]
            + 1
        )

        set_data = self._set_id(identifier, data)

        cursor.execute(
            read_sql(Path("insert-node.sql")),
            (
                count,
                label,
                json.dumps(set_data),
            ),
        )
        connection.commit()

    def _add_node(
        self,
        label: str,
        data: Dict,
        identifier: Any = None,
    ) -> CursorExecFunction:
        def _add_single_node(cursor, connection):
            return self._insert_node(cursor, connection, identifier, label, data)

        return _add_single_node

    def _connect_nodes(
        self,
        source_id: Any,
        target_id: Any,
        label: str,
        attributes: Dict = {},
    ) -> CursorExecFunction:
        def _connect_single_nodes(cursor, connection):
            count = (
                cursor.execute(
                    "SELECT COALESCE(MAX(embed_id), 0) FROM edges"
                ).fetchone()[0]
                + 1
            )

            cursor.execute(
                read_sql(Path("insert-edge.sql")),
                (
                    count,
                    source_id,
                    target_id,
                    label,
                    json.dumps(attributes),
                ),
            )

        return _connect_single_nodes

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
                return None

        return _find_single_node

    def _find_edge(self, source: Any, target: Any, attributes: Dict, limit: int):
        def _search_edge(cursor, connection):
            new_edge = cursor.execute(
                "SELECT embed_id from edges where source=? AND target=? AND attributes = json(?) LIMIT ?",
                (source, target, json.dumps(attributes), limit),
            )
            result = new_edge.fetchone()

            if result is None:
                return
            else:
                return result[0]

        return _search_edge

    def _upsert_single_node(
        self,
        cursor: sqlite3.Cursor,
        connection: sqlite3.Connection,
        identifier: Any,
        label: str,
        data: Dict,
    ) -> None:
        current_data = self._find_node(identifier)(cursor, connection)

        updated_data = {**current_data, **data}

        count = (
            cursor.execute("SELECT COALESCE(MAX(embed_id), 0) FROM nodes").fetchone()[0]
            + 1
        )

        cursor.execute(
            read_sql(Path("update-node.sql")),
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

    def _remove_node(self, identifier: Any) -> CursorExecFunction:
        def _remove_single_node(cursor, connection):
            cursor.execute(
                read_sql(Path("delete-edge.sql")),
                (
                    identifier,
                    identifier,
                ),
            )

            cursor.execute(read_sql(Path("delete-node.sql")), (identifier,))

        return _remove_single_node

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

        return self.atomic(_traverse_graph)

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

    def _connections_in(self) -> str:
        return read_sql(Path("search-edges-inbound.sql"))

    def _connections_out(self) -> str:
        return read_sql(Path("search-edges-outbound.sql"))

    def _get_connections_one_way(
        self,
        identifier: Any,
        direction: Callable[[], str] = _connections_in,  # type: ignore
    ) -> CursorExecFunction:
        def _get_connections(cursor, connection):
            return cursor.execute(direction(), (identifier,)).fetchall()

        return self.atomic(_get_connections)

    def _fetch_node_id(self, node_id: Any, limit: int):
        def _get_node_id(cursor, connection):
            embed_id = cursor.execute(
                "SELECT embed_id from nodes where id=? LIMIT ?", (node_id, limit)
            )

            if embed_id is None:
                return

            return embed_id.fetchone()

        return _get_node_id

    def _fetch_edge_ids(self, id: Any, limit: int):
        def _get_edge_embed_ids(cursor, connection):
            ids = cursor.execute(
                "SELECT embed_id from edges where source=? or target=? LIMIT ?",
                (id, id, limit),
            )
            if ids is None:
                return

            return ids.fetchall()

        return _get_edge_embed_ids

    def all_connected_nodes(
        self, node_or_edge: Union[Node | Edge], limit: Optional[int] = 1
    ) -> Any:
        def _connected_nodes(cursor, connection):
            nodes = None
            if isinstance(node_or_edge, Node):
                index = node_or_edge.id
                nodes = cursor.execute(
                    "SELECT source, target FROM edges WHERE source=? OR target=? LIMIT ?",
                    (index, index, limit),
                )
            elif isinstance(node_or_edge, Edge):
                index1, index2 = node_or_edge.source, node_or_edge.target
                nodes = cursor.execute(
                    "SELECT source, target FROM edges WHERE source=? OR target=? OR source=? OR target=? LIMIT ?",
                    (index1, index1, index2, index2, limit),
                )

            resultant_connected_nodes = []
            if nodes:
                connected_nodes = nodes.fetchall()
                for connected_node in connected_nodes:
                    for id in connected_node:
                        res = cursor.execute(
                            "SELECT id, label, attributes from nodes where id=? LIMIT ?",
                            (id, limit),
                        ).fetchone()
                        if res not in resultant_connected_nodes:
                            resultant_connected_nodes.append(
                                Node(id=res[0], label=res[1], attributes=res[2])
                            )

                return resultant_connected_nodes

        return self.atomic(_connected_nodes)

    def get_connections(self, identifier: Any) -> CursorExecFunction:
        def _get_all_connections(cursor, connection):
            return cursor.execute(
                read_sql(Path("search-edges.sql")),
                (
                    identifier,
                    identifier,
                ),
            ).fetchall()

        return self.atomic(_get_all_connections)

    def fetch_node_embed_id(self, node_id: Any, limit: int = 1) -> None:
        return self.atomic(self._fetch_node_id(node_id, limit))

    def fetch_edge_embed_ids(self, id: Any, limit: int = 10):
        return self.atomic(self._fetch_edge_ids(id, limit))

    def search_edge(
        self, source: Any, target: Any, attributes: Dict, limit: int = 1
    ) -> Dict[Any, Any]:
        return self.atomic(self._find_edge(source, target, attributes, limit))

    def add_node(self, label: str, attribute: Dict, id: Any):
        self.atomic(
            self._add_node(
                label,
                attribute if isinstance(attribute, Dict) else attribute,
                id,
            )
        )

    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        connect_nodes_func = self._connect_nodes(
            source,
            target,
            label,
            attributes if isinstance(attributes, Dict) else attributes,
        )
        self.atomic(connect_nodes_func)

    def update_node(self, node: Node):
        upsert_node_func = self._upsert_node(
            identifier=node.id,
            label=node.label,
            data=json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
        )
        self.atomic(upsert_node_func)

    def remove_node(self, id: Any) -> None:
        self.atomic(self._remove_node(id))

    def search_node(self, node_id: Any) -> Any:
        return self.atomic(self._find_node(node_id))

    def search_node_label(self, node_id: Any, limit: Optional[int] = 1) -> Any:
        def _search_label(cursor, connection):
            node_label = cursor.execute(
                "SELECT label from nodes where id=? LIMIT ?", (node_id, limit)
            ).fetchone()

            return node_label

        return self.atomic(_search_label)

    def search_node_type(self, label: str):
        def _search_node_type(cursor, connection):
            node_type = cursor.execute(
                "SELECT label from nodes where label=?", (label,)
            ).fetchone()

            return node_type

        return self.atomic(_search_node_type)

    def search_id_by_node_type(self, node_type):
        def _find_node_type_id(cursor, connection):
            node_id = cursor.execute(
                "SELECT id from nodes where label=?", (node_type,)
            ).fetchone()
            return node_id

        return self.atomic(_find_node_type_id)

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

    def fetch_node_id(self, id: Any, limit: Optional[int] = 1):
        def _get_id(cursor, connection):
            similar_node_id = cursor.execute(
                "SELECT id from nodes where embed_id=? LIMIT ?", (id, limit)
            ).fetchone()
            return similar_node_id

        return self.atomic(_get_id)

    def find_nodes_by_label(self, label: str, limit: Optional[int] = 1):
        def search_node_like(cursor, connection):
            nodes = cursor.execute(
                "SELECT id, label, attributes FROM nodes WHERE label LIKE ? LIMIT ?",
                ("%" + label + "%", limit),
            )

            if nodes is None:
                return []

            return nodes.fetchall()

        return self.atomic(search_node_like)

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
        if connections is None:
            connections = self.get_connections
        ids = []
        for i in path:
            ids.append(str(i))
            for edge in connections(i):  # type: ignore
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
                node = self.search_node(i)  # type: ignore
                if node is []:
                    continue

                name, label = _as_dot_node(
                    node, exclude_node_keys, hide_node_key, node_kv
                )
                dot.node(name, label=label)
                for edge in connections(i):  # type: ignore
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

    def fetch_ids_from_db(self, limit: Optional[int] = 10) -> List[str]:
        def _fetch_nodes_from_db(cursor, connection):
            nodes = cursor.execute("SELECT id from nodes LIMIT ?", (limit,)).fetchall()
            ids = [id[0] for id in nodes]

            return ids

        return self.atomic(_fetch_nodes_from_db)

    def search_indegree_edges(
        self, target: Any, limit: Optional[int] = 10
    ) -> List[Any]:
        def _indegree_edges(cursor, connection):
            indegree = cursor.execute(
                "SELECT source, label, attributes from edges where target=? LIMIT ?",
                (target, limit),
            )

            if not indegree:
                return []
            else:
                return indegree.fetchall()

        return self.atomic(_indegree_edges)

    def search_outdegree_edges(
        self, source: Any, limit: Optional[int] = 10
    ) -> List[Any]:
        def _outdegree_edges(cursor, connection):
            outdegree = cursor.execute(
                "SELECT target, label, attributes from edges where source=? LIMIT ?",
                (source, limit),
            )

            if not outdegree:
                return []
            else:
                return outdegree.fetchall()

        return self.atomic(_outdegree_edges)

    def search_similar_nodes(
        self, embed_ids, *, desc: Optional[bool] = False, sort_by: Optional[str] = ""
    ):
        def _search_node(cursor, connection):
            nodes = cursor.execute(
                read_sql(Path("search-node-by-rowid.sql")),
                (embed_ids, sort_by, desc, sort_by, sort_by, desc, sort_by),
            )

            return nodes.fetchall()

        return self.atomic(_search_node)

    def search_similar_edges(self, embed_ids, *, desc: bool = False, sort_by: str = ""):
        def _search_edge(cursor, connection):
            edges = cursor.execute(
                read_sql(Path("search-edge-by-rowid.sql")),
                (embed_ids, sort_by, desc, sort_by, sort_by, desc, sort_by),
            )

            return edges.fetchall()

        return self.atomic(_search_edge)
