"""
Provide a higher level API to the database using Pydantic
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, List, Optional, Union, Dict
import libsql_experimental as libsql  # type: ignore
from contextlib import AbstractContextManager

import networkx as nx  # type: ignore
from graphviz import Digraph  # type: ignore
from litellm.llms import openai  # type: ignore
from matplotlib import pyplot as plt

from personal_graph.embeddings import OpenAIEmbeddingsModel
from personal_graph.models import Node, EdgeInput, KnowledgeGraph, Edge
from personal_graph.database import (
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
from personal_graph.natural import (
    insert_into_graph,
    search_from_graph,
    visualize_knowledge_graph,
)
from personal_graph.visualizers import graphviz_visualize


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

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return "Not of Graph Type"
        return self.db_url == other.db_url and self.db_auth_token == other.db_auth_token

    def __enter__(self, schema_file: str = "schema.sql") -> Graph:
        if not self.db_url:
            # Support for local SQLite database
            self.connection = libsql.connect(":memory:")
        else:
            self.connection = libsql.connect(
                database=self.db_url, auth_token=self.db_auth_token
            )
        initialize(
            db_url=self.db_url,
            db_auth_token=self.db_auth_token,
            schema_file=schema_file,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.save()

    def save(self):
        self.connection.commit()

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
                    id=str(node_id), label=node_label[0], attributes=node_attributes
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
            self.db_auth_token,
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
        atomic(add_nodes_func, self.db_url, self.db_auth_token)

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
        atomic(connect_nodes_func, self.db_url, self.db_auth_token)

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
        atomic(connect_many_nodes_func, self.db_url, self.db_auth_token)

    def update_node(self, node: Node) -> None:
        upsert_node_func = upsert_node(
            self.embedding_model,
            identifier=node.id,
            label=node.label,
            data=json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
        )
        atomic(upsert_node_func, self.db_url, self.db_auth_token)

    def update_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.update_node(node)

    def remove_node(self, id: Any) -> None:
        atomic(remove_node(id), self.db_url, self.db_auth_token)

    def remove_nodes(self, ids: List[Any]) -> None:
        atomic(remove_nodes(ids), self.db_url, self.db_auth_token)

    def search_node(self, node_id: Any) -> Any:
        return atomic(find_node(node_id), self.db_url, self.db_auth_token)

    def search_node_label(self, node_id: Any) -> Any:
        return atomic(find_label(node_id), self.db_url, self.db_auth_token)

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        neighbors_fn = find_neighbors if with_bodies else find_outbound_neighbors
        path = traverse(
            db_url=self.db_url,
            db_auth_token=self.db_auth_token,
            src=source,
            tgt=target,
            neighbors_fn=neighbors_fn,
            with_bodies=with_bodies,
        )
        return path

    def insert(self, text: str) -> KnowledgeGraph:
        kg: KnowledgeGraph = insert_into_graph(
            text,
            self.llm_client.client,
            self.llm_client.model_name,
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
            self.db_auth_token,
        )

    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        return atomic(
            find_similar_nodes(self.embedding_model, label, threshold),
            self.db_url,
            self.db_auth_token,
        )

    def visualize(self, file: str, path: List[str]) -> Digraph:
        return graphviz_visualize(self.db_url, self.db_auth_token, file, path)

    def fetch_ids_from_db(self) -> List[str]:
        return atomic(nodes_list(), self.db_url, self.db_auth_token)

    def search_indegree_edges(self, target) -> List[Any]:
        return atomic(find_indegree_edges(target), self.db_url, self.db_auth_token)

    def search_outdegree_edges(self, source) -> List[Any]:
        return atomic(find_outdegree_edges(source), self.db_url, self.db_auth_token)

    def is_unique_prompt(self, text: str, threshold: float) -> bool:
        similar_nodes = atomic(
            vector_search_node(
                self.embedding_model,
                {"body": text},
                threshold,
                1,
            ),
            self.db_url,
            self.db_auth_token,
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
