import json
import networkx as nx  # type: ignore
from typing import Dict, Any
import matplotlib.pyplot as plt
from graphviz import Digraph  # type: ignore

from personal_graph.graph import Graph
from personal_graph.models import Node, KnowledgeGraph, Edge


def to_networkx(graph: Graph, *, post_visualize: bool = False) -> nx.Graph:
    """
    Convert the graph database to a NetworkX DiGraph object.
    """
    G = nx.Graph()  # Empty Graph with no nodes and edges

    node_ids = graph.fetch_ids_from_db()
    # Add edges to networkX
    for source_id in node_ids:
        for target_id, edge_label, edge_data in graph.search_outdegree_edges(source_id):
            edge_data = json.loads(edge_data)
            edge_data["label"] = edge_label
            G.add_edge(source_id, target_id, **edge_data)

    for target_id in node_ids:
        for source_id, edge_label, edge_data in graph.search_indegree_edges(target_id):
            edge_data = json.loads(edge_data)
            edge_data["label"] = edge_label
            G.add_edge(source_id, target_id, **edge_data)

    node_ids_with_edges = set([node for edge in G.edges() for node in edge])
    for node_id in node_ids:
        if node_id not in node_ids_with_edges:
            node_data = graph.search_node(node_id)
            node_label = graph.search_node_label(node_id)
            node_data["label"] = node_label
            G.add_node(node_id, **node_data)

    if post_visualize:
        # Visualizing the NetworkX Graph
        plt.figure(figsize=(20, 20), dpi=100)  # Increase the figure size and resolution
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


def from_networkx(network_graph: nx, *, post_visualize: bool = False) -> KnowledgeGraph:
    graph = KnowledgeGraph()

    node_ids_with_edges = set()

    # Convert networkX edges to personal graph edges
    for source_id, target_id, edge_data in network_graph.edges(data=True):
        edge_attributes: Dict[str, Any] = edge_data
        edge_label: str = edge_attributes["label"]
        node_ids_with_edges.add(str(source_id))
        node_ids_with_edges.add(str(target_id))

        edge = Edge(
            source=str(source_id),
            target=str(target_id),
            label=edge_label if edge_label else "",
            attributes=json.dumps(edge_attributes),
        )
        graph.edges.append(edge)

    # Convert networkX nodes to personal graph nodes
    for node_id, node_data in network_graph.nodes(data=True):
        if str(node_id) not in node_ids_with_edges:
            node_attributes: Dict[str, Any] = node_data
            node_label: str = node_attributes.pop("label", "")
            node = Node(
                id=str(node_id),
                label=node_label if node_label else "",
                attributes=json.dumps(node_attributes),
            )
            graph.nodes.append(node)

    if post_visualize:
        # Visualize the personal graph using graphviz
        dot = Digraph()

        for node in graph.nodes:
            dot.node(node.id, label=f"{node.label}: {node.id}")

        for edge in graph.edges:
            dot.edge(edge.source, edge.target, label=edge.label)

        dot.render("personal_graph.gv", view=True)

    return graph
