"""
Provide a higher level API to the database using Pydantic
"""

from __future__ import annotations

import json
import os
from typing import Any, List, Optional, Union, Dict
import libsql_experimental as libsql  # type: ignore
from contextlib import AbstractContextManager
from graphviz import Digraph  # type: ignore
from litellm.llms import openai  # type: ignore

from .embeddings import OpenAIEmbeddingsModel
from .models import Node, EdgeInput, KnowledgeGraph
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
    pruning,
    find_similar_nodes,
    nodes_list,
    vector_search_node,
    find_label,
    find_outdegree_edges,
    find_indegree_edges,
)
from .natural import insert_into_graph, search_from_graph, visualize_knowledge_graph
from .visualizers import graphviz_visualize


class Graph(AbstractContextManager):
    def __init__(
        self,
        *,
        db_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        llm_client: openai.OpenAI = openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", ""),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        ),
        embedding_model_client: openai.OpenAI = openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", ""),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        ),
        llm_model_name: str = "openai/gpt-3.5-turbo",
        embedding_model_name: str = "openai/text-embedding-3-small",
        embedding_dimensions: int = 384,
    ):
        self.db_url = db_url
        self.auth_token = auth_token
        self.llm_client = llm_client
        self.llm_model_name = llm_model_name

        self.embedding_model = OpenAIEmbeddingsModel(
            embedding_model_client,
            embedding_model_name,
            embedding_dimensions,
        )

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return "Not of Graph Type"
        return self.db_url == other.db_url and self.auth_token == other.auth_token

    def __enter__(self, schema_file: str = "schema.sql") -> Graph:
        if not self.db_url:
            # Support for local SQLite database
            self.connection = libsql.connect(":memory:")
        else:
            self.connection = libsql.connect(
                database=self.db_url, auth_token=self.auth_token
            )
        initialize(
            db_url=self.db_url, auth_token=self.auth_token, schema_file=schema_file
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.save()

    def save(self):
        self.connection.commit()

    def add_node(self, node: Node) -> None:
        atomic(
            add_node(
                self.embedding_model,
                node.label,
                json.loads(node.attributes)
                if isinstance(node.attributes, str)
                else node.attributes,
                node.id,
            ),
            self.db_url,
            self.auth_token,
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
        add_nodes_func = add_nodes(
            self.embedding_model,
            nodes=attributes,
            labels=labels,
            ids=ids,
        )
        atomic(add_nodes_func, self.db_url, self.auth_token)

    def add_edge(self, edge: EdgeInput) -> None:
        connect_nodes_func = connect_nodes(
            self.embedding_model,
            edge.source.id,
            edge.target.id,
            edge.label,
            json.loads(edge.attributes)
            if isinstance(edge.attributes, str)
            else edge.attributes,
        )
        atomic(connect_nodes_func, self.db_url, self.auth_token)

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
        connect_many_nodes_func = connect_many_nodes(
            self.embedding_model,
            sources=sources,
            targets=targets,
            labels=labels,
            attributes=attributes,
        )
        atomic(connect_many_nodes_func, self.db_url, self.auth_token)

    def update_node(self, node: Node) -> None:
        upsert_node_func = upsert_node(
            self.embedding_model,
            identifier=node.id,
            label=node.label,
            data=json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
        )
        atomic(upsert_node_func, self.db_url, self.auth_token)

    def update_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.update_node(node)

    def remove_node(self, id: Any) -> None:
        atomic(remove_node(id), self.db_url, self.auth_token)

    def remove_nodes(self, ids: List[Any]) -> None:
        atomic(remove_nodes(ids), self.db_url, self.auth_token)

    def search_node(self, node_id: Any) -> Any:
        return atomic(find_node(node_id), self.db_url, self.auth_token)

    def search_node_label(self, node_id: Any) -> Any:
        return atomic(find_label(node_id), self.db_url, self.auth_token)

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

    def insert(self, text: str) -> KnowledgeGraph:
        kg: KnowledgeGraph = insert_into_graph(
            text,
            self.llm_client,
            self.llm_model_name,
            self.embedding_model,
        )
        return kg

    def search_query(self, text: str) -> KnowledgeGraph:
        kg: KnowledgeGraph = search_from_graph(text, self.embedding_model)
        return kg

    def visualize_graph(self, kg: KnowledgeGraph) -> Digraph:
        return visualize_knowledge_graph(kg)

    def merge_by_similarity(self, threshold) -> None:
        atomic(
            pruning(self.embedding_model, threshold),
            self.db_url,
            self.auth_token,
        )

    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        return atomic(
            find_similar_nodes(self.embedding_model, label, threshold),
            self.db_url,
            self.auth_token,
        )

    def visualize(self, file: str, path: List[str]) -> Digraph:
        return graphviz_visualize(self.db_url, self.auth_token, file, path)

    def fetch_ids_from_db(self) -> List[str]:
        return atomic(nodes_list(), self.db_url, self.auth_token)

    def search_indegree_edges(self, target) -> List[Any]:
        return atomic(find_indegree_edges(target), self.db_url, self.auth_token)

    def search_outdegree_edges(self, source) -> List[Any]:
        return atomic(find_outdegree_edges(source), self.db_url, self.auth_token)

    def is_unique_prompt(self, text: str, threshold: float) -> bool:
        similar_nodes = atomic(
            vector_search_node(
                self.embedding_model,
                {"body": text},
                threshold,
                1,
            ),
            self.db_url,
            self.auth_token,
        )

        if not similar_nodes:
            return True
        return False
