from __future__ import annotations

import json
import instructor
import uuid
from typing import Any, List, Optional, Union, Dict, Callable

import libsql_experimental as libsql  # type: ignore
from contextlib import AbstractContextManager

import networkx as nx  # type: ignore
from graphviz import Digraph  # type: ignore
from matplotlib import pyplot as plt
from dotenv import load_dotenv

from personal_graph.clients import LLMClient
from personal_graph.models import Node, EdgeInput, KnowledgeGraph, Edge
from personal_graph.visualizers import _as_dot_node, _as_dot_label
from personal_graph.database.sqlitevss import SQLiteVSS
from personal_graph.database.vlitedatabase import VLiteDatabase

load_dotenv()
CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


class Graph(AbstractContextManager):
    def __init__(
        self, *, llm_client: LLMClient, vector_store: Union[SQLiteVSS, VLiteDatabase]
    ):
        self.llm_client = llm_client
        self.vector_store = vector_store

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return "Not of Graph Type"
        else:
            if isinstance(self.vector_store, SQLiteVSS):
                return (
                    self.vector_store.db_url == other.vector_store.db_url
                    and self.vector_store.db_auth_token
                    == other.vector_store.db_auth_token
                )
            else:
                return self.vector_store.collection == other.vector_store.collection

    def __enter__(self) -> Graph:
        self.vector_store.initialize()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

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

    # Visualization api
    def _graphviz_visualize(
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
            connections = self.vector_store.get_connections
        ids = []
        for i in path:
            ids.append(str(i))
            for edge in connections(i):  # type: ignore
                if isinstance(self.vector_store, SQLiteVSS):
                    _, src, tgt, _, _, _, _ = edge
                else:
                    src = edge[2]["source"]
                    tgt = edge[2]["target"]
                if src not in ids:
                    ids.append(src)
                if tgt not in ids:
                    ids.append(tgt)

        dot = Digraph()

        visited = []
        edges = []
        for i in ids:
            if i not in visited:
                node = self.vector_store.search_node(i)  # type: ignore
                if node is []:
                    continue

                if not isinstance(self.vector_store, SQLiteVSS):
                    node = node[0][2]

                name, label = _as_dot_node(
                    node, exclude_node_keys, hide_node_key, node_kv
                )
                dot.node(name, label=label)
                for edge in connections(i):  # type: ignore
                    if edge not in edges:
                        if isinstance(self.vector_store, SQLiteVSS):
                            _, src, tgt, _, prps, _, _ = edge
                            props = json.loads(prps)
                        else:
                            src, tgt, props = edge
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

    # High level apis
    def add_node(self, node: Node) -> None:
        self.vector_store.add_node(
            node.label,
            json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
            node.id,
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

        self.vector_store.add_nodes(
            attributes=attributes,
            labels=labels,
            ids=ids,
        )

    def add_edge(self, edge: EdgeInput) -> None:
        self.vector_store.add_edge(
            edge.source.id,
            edge.target.id,
            edge.label,
            json.loads(edge.attributes)
            if isinstance(edge.attributes, str)
            else edge.attributes,
        )

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

        self.vector_store.add_edges(
            sources=sources, targets=targets, labels=labels, attributes=attributes
        )

    def update_node(self, node: Node) -> None:
        self.vector_store.update_node(node)

    def update_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.update_node(node)

    def remove_node(self, id: Any) -> None:
        self.vector_store.remove_node(id)

    def remove_nodes(self, ids: List[Any]) -> None:
        self.vector_store.remove_nodes(ids)

    def search_node(self, node_id: Any) -> Any:
        return self.vector_store.search_node(node_id)

    def search_node_label(self, node_id: Any) -> Any:
        return self.vector_store.search_node_label(node_id)

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        return self.vector_store.traverse(source, target, with_bodies)

    def insert_into_graph(self, text: str) -> KnowledgeGraph:
        uuid_dict = {}
        kg = self._generate_graph(text)

        try:
            for node in kg.nodes:
                uuid_dict[node.id] = str(uuid.uuid4())
                self.vector_store.add_node(
                    node.label,
                    {"body": node.attributes},
                    uuid_dict[node.id],
                )

            for edge in kg.edges:
                self.vector_store.add_edge(
                    uuid_dict[edge.source],
                    uuid_dict[edge.target],
                    edge.label,
                    {"body": edge.attributes},
                )
        except KeyError:
            return KnowledgeGraph()

        return kg

    def search_from_graph(
        self, text: str, *, limit: int = 5, descending: bool = False, sort_by: str = ""
    ) -> KnowledgeGraph:
        try:
            similar_nodes = self.vector_store.vector_search_node(
                {"body": text}, descending=descending, limit=limit, sort_by=sort_by
            )

            similar_edges = self.vector_store.vector_search_edge(
                {"body": text}, descending=descending, limit=limit, sort_by=sort_by
            )

            resultant_subgraph = KnowledgeGraph()

            if similar_edges and similar_nodes is None or similar_nodes is None:
                return resultant_subgraph

            if isinstance(self.vector_store, SQLiteVSS):
                resultant_subgraph.nodes = [
                    Node(id=node[1], label=node[2], attributes=node[3])
                    for node in similar_nodes
                ]
            else:
                resultant_subgraph.nodes = [
                    Node(
                        id=node[0],
                        label=node[1],
                        attributes=node[2]["body"],
                    )
                    for node in similar_nodes
                ]

            for node in similar_nodes:
                if isinstance(self.vector_store, SQLiteVSS):
                    similar_node = Node(id=node[1], label=node[2], attributes=node[3])
                else:
                    similar_node = Node(
                        id=node[0],
                        label=json.loads(node[1])["label"],
                        attributes=json.loads(node[1])["body"],
                    )
                nodes = self.vector_store.all_connected_nodes(similar_node)

                if not nodes:
                    continue

                for i in nodes:
                    if i not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(i)

            if isinstance(self.vector_store, SQLiteVSS):
                resultant_subgraph.edges = [
                    Edge(
                        source=edge[1],
                        target=edge[2],
                        label=edge[3],
                        attributes=edge[4],
                    )
                    for edge in similar_edges
                ]
            else:
                resultant_subgraph.edges = [
                    Edge(
                        source=json.loads(edge[1])["source"],
                        target=json.loads(edge[1])["target"],
                        label=json.loads(edge[1])["label"],
                        attributes=json.loads(edge[1])["body"],
                    )
                    for edge in similar_edges
                ]
            for edge in similar_edges:
                if isinstance(self.vector_store, SQLiteVSS):
                    similar_edge = Edge(
                        source=edge[1],
                        target=edge[2],
                        label=edge[3],
                        attributes=edge[4],
                    )
                else:
                    similar_edge = Edge(
                        source=json.loads(edge[1])["source"],
                        target=json.loads(edge[1])["target"],
                        label=json.loads(edge[1])["label"],
                        attributes=json.loads(edge[1])["body"],
                    )

                nodes = self.vector_store.all_connected_nodes(similar_edge)
                if not nodes:
                    continue

                for node in nodes:
                    if node not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(node)

        except KeyError:
            return KnowledgeGraph()

        return resultant_subgraph

    def visualize_graph(self, kg: KnowledgeGraph) -> Digraph:
        dot = Digraph(comment="Knowledge Graph")

        # Add nodes
        for node in kg.nodes:
            dot.node(str(node.id), node.label, color="black")

        # Add edges
        for edge in kg.edges:
            dot.edge(str(edge.source), str(edge.target), edge.label, color="black")

        return dot

    def merge_by_similarity(self, threshold) -> None:
        self.vector_store.merge_by_similarity(threshold)

    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        return self.vector_store.find_nodes_like(label, threshold)

    def visualize(self, file: str, path: List[str]) -> Digraph:
        return self._graphviz_visualize(file, path)

    def fetch_ids_from_db(self) -> List[str]:
        return self.vector_store.fetch_ids_from_db()

    def search_indegree_edges(self, target: Any) -> List[Any]:
        return self.vector_store.search_indegree_edges(target)

    def search_outdegree_edges(self, source: Any) -> List[Any]:
        return self.vector_store.search_outdegree_edges(source)

    def is_unique_prompt(self, text: str) -> bool:
        similar_nodes = self.vector_store.vector_search_node(
            {"body": text}, descending=False, limit=1, sort_by=""
        )

        if not similar_nodes:
            return True
        return False

    def pg_to_networkx(self, *, post_visualize: bool = False):
        """
        Convert the graph database to a NetworkX DiGraph object.
        """
        G = nx.Graph()  # Empty Graph with no nodes and edges

        node_ids = self.fetch_ids_from_db()
        # Add edges to networkX
        for source_id in node_ids:
            outdegree_edges = self.search_outdegree_edges(source_id)
            if outdegree_edges is []:
                continue

            for target_id, edge_label, edge_data in outdegree_edges:
                if isinstance(self.vector_store, SQLiteVSS):
                    edge_data = json.loads(edge_data)

                edge_data["label"] = edge_label
                G.add_edge(source_id, target_id, **edge_data)

        for target_id in node_ids:
            indegree_edges = self.search_indegree_edges(target_id)

            if indegree_edges is []:
                continue

            for source_id, edge_label, edge_data in indegree_edges:
                if isinstance(self.vector_store, SQLiteVSS):
                    edge_data = json.loads(edge_data)

                edge_data["label"] = edge_label
                G.add_edge(source_id, target_id, **edge_data)

        for node_id in node_ids:
            node_data = self.search_node(node_id)

            if isinstance(self.vector_store, SQLiteVSS):
                node_label = self.search_node_label(node_id)
                node_data["label"] = node_label
            else:
                node_data = node_data[0][2]

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

    def networkx_to_pg(
        self, networkx_graph: nx, *, post_visualize: bool = False, override: bool = True
    ):
        if override:
            node_ids = self.fetch_ids_from_db()
            self.remove_nodes(node_ids)

        node_ids_with_edges = set()
        kg = KnowledgeGraph()

        # Convert networkX edges to personal graph edges
        for source_id, target_id, edge_data in networkx_graph.edges(data=True):
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
        for node_id, node_data in networkx_graph.nodes(data=True):
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
        sort_by: str = "",
    ):
        try:
            similar_nodes = self.vector_store.vector_search_node(
                {"body": text}, descending=descending, limit=limit, sort_by=sort_by
            )

        except KeyError:
            return []

        if similar_nodes is None:
            return None

        if limit == 1:
            if isinstance(self.vector_store, SQLiteVSS):
                return json.loads(similar_nodes[0][3])
            else:
                return similar_nodes[0][2]

        return similar_nodes
