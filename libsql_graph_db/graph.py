"""
Provide a higher level API to the database using Pydantic
"""

from __future__ import annotations

import json
from typing import Any, List, Optional
import libsql_experimental as libsql  # type: ignore
from contextlib import AbstractContextManager
from .models import Node, Edge
from .database import (
    atomic,
    connect_nodes,
    initialize,
    add_nodes,
    upsert_node,
    connect_many_nodes,
    add_node,
    remove_node,
    remove_nodes,
    find_node,
    find_neighbors,
    find_outbound_neighbors,
    traverse,
)


class Graph(AbstractContextManager):
    def __init__(self, db_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.db_url = db_url
        self.auth_token = auth_token

    def __enter__(self, schema_file: str = "schema.sql") -> Graph:
        self.connection = libsql.connect(
            database=self.db_url, auth_token=self.auth_token
        )
        initialize(
            db_url=self.db_url, auth_token=self.auth_token, schema_file=schema_file
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # TODO: graph.save()
        pass

    def add_node(self, node: Node):
        atomic(
            add_node(
                node.label,
                json.loads(node.attribute)
                if isinstance(node.attribute, str)
                else node.attribute,
                node.id,
            ),
            self.db_url,
            self.auth_token,
        )

    def add_nodes(self, nodes: List[Node]) -> None:
        labels = [node.label for node in nodes]
        attributes = [
            json.loads(node.attribute)
            if isinstance(node.attribute, str)
            else node.attribute
            for node in nodes
        ]
        ids = [node.id for node in nodes]
        add_nodes_func = add_nodes(nodes=attributes, labels=labels, ids=ids)
        atomic(add_nodes_func, self.db_url, self.auth_token)

    def add_edge(self, edge: Edge) -> None:
        connect_nodes_func = connect_nodes(
            edge.source,
            edge.target,
            edge.label,
            json.loads(edge.attribute)
            if isinstance(edge.attribute, str)
            else edge.attribute,
        )
        atomic(connect_nodes_func, self.db_url, self.auth_token)

    def add_edges(self, edges: List[Edge]) -> None:
        sources = [edge.source for edge in edges]
        targets = [edge.target for edge in edges]
        labels = [edge.label for edge in edges]
        attributes = [
            json.loads(edge.attribute)
            if isinstance(edge.attribute, str)
            else edge.attribute
            for edge in edges
        ]
        connect_many_nodes_func = connect_many_nodes(
            sources=sources, targets=targets, labels=labels, attributes=attributes
        )
        atomic(connect_many_nodes_func, self.db_url, self.auth_token)

    def upsert_node(self, node: Node) -> None:
        upsert_node_func = upsert_node(
            identifier=node.id,
            label=node.label,
            data=json.loads(node.attribute)
            if isinstance(node.attribute, str)
            else node.attribute,
        )
        atomic(upsert_node_func, self.db_url, self.auth_token)

    def upsert_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.upsert_node(node)

    def remove_node(self, id: Any) -> None:
        atomic(remove_node(id), self.db_url, self.auth_token)

    def remove_nodes(self, ids: List[Any]) -> None:
        atomic(remove_nodes(ids), self.db_url, self.auth_token)

    def search_node(self, node_id: Any) -> Any:
        return atomic(find_node(node_id), self.db_url, self.auth_token)

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        neighbors_fn = find_neighbors if with_bodies else find_outbound_neighbors
        path = traverse(
            db_url=self.db_url,
            auth_token=self.auth_token,
            src=source,
            tgt=target,
            neighbors_fn=neighbors_fn,
            with_bodies=with_bodies,
        )
        return path
