#!/usr/bin/env python3

"""
visualizers.py

Functions to enable visualizations of graph data, starting with graphviz,
and extensible to other libraries.

"""

import json
from graphviz import Digraph  # type: ignore
from libsql_graph_db import database as db
from typing import List, Dict, Any, Tuple, Optional


def _as_dot_label(
    body: Dict[str, Any],
    exclude_keys: List[str],
    hide_key_name: bool,
    kv_separator: str,
) -> str:
    keys = [k for k in body.keys() if k not in exclude_keys]
    fstring = (
        "\\n".join(["{" + k + "}" for k in keys])
        if hide_key_name
        else "\\n".join([k + kv_separator + "{" + k + "}" for k in keys])
    )
    return fstring.format(**body)


def _as_dot_node(
    body: Dict[str, Any],
    exclude_keys: List[str] = [],
    hide_key_name: bool = False,
    kv_separator: str = " ",
) -> Tuple[str, str]:
    name = body["id"]
    exclude_keys.append("id")
    label = _as_dot_label(body, exclude_keys, hide_key_name, kv_separator)
    return str(name), label


def graphviz_visualize(
    db_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    dot_file: Optional[str] = None,
    path: List[Any] = [],
    connections: Any = db.get_connections,
    format: str = "png",
    exclude_node_keys: List[str] = [],
    hide_node_key: bool = False,
    node_kv: str = " ",
    exclude_edge_keys: List[str] = [],
    hide_edge_key: bool = False,
    edge_kv: str = " ",
) -> None:
    ids = []
    for i in path:
        ids.append(str(i))
        for edge in db.atomic(connections(i), db_url, auth_token):  # type: ignore
            print("Here", edge)
            _, src, tgt, _ = edge
            if src not in ids:
                ids.append(src)
            if tgt not in ids:
                ids.append(tgt)

    dot = Digraph()

    visited = []
    edges = []
    for i in ids:
        if i not in visited:
            node = db.atomic(db.find_node(i), db_url, auth_token)  # type: ignore
            name, label = _as_dot_node(node, exclude_node_keys, hide_node_key, node_kv)
            dot.node(name, label=label)
            for edge in db.atomic(connections(i), db_url, auth_token):  # type: ignore
                if edge not in edges:
                    _, src, tgt, prps = edge
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


def graphviz_visualize_bodies(
    dot_file: str,
    path: List[Tuple[Any, str, str]] = [],
    format: str = "png",
    exclude_node_keys: List[str] = [],
    hide_node_key: bool = False,
    node_kv: str = " ",
    exclude_edge_keys: List[str] = [],
    hide_edge_key: bool = False,
    edge_kv: str = " ",
) -> None:
    dot = Digraph()
    current_id = None
    edges = []
    for identifier, obj, properties in path:
        body = json.loads(properties)
        if obj == "()":
            name, label = _as_dot_node(body, exclude_node_keys, hide_node_key, node_kv)
            dot.node(name, label=label)
            current_id = body["id"]
        else:
            edge = (
                (str(current_id), str(identifier), body)
                if obj == "->"
                else (str(identifier), str(current_id), body)
            )
            if edge not in edges:
                dot.edge(
                    edge[0],
                    edge[1],
                    label=_as_dot_label(body, exclude_edge_keys, hide_edge_key, edge_kv)
                    if body
                    else None,
                )
                edges.append(edge)
    dot.render(dot_file, format=format)
