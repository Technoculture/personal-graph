import json
import networkx as nx  # type: ignore
from typing import Dict, Any
import matplotlib.pyplot as plt
from personal_graph.graph import Graph
from personal_graph.models import Node, KnowledgeGraph, Edge


def to_networkx(graph: Graph, post_visualize: bool = False) -> nx.Graph:
    """
    Convert the graph database to a NetworkX DiGraph object.
    """
    G = nx.Graph()  # Empty Graph with no nodes and edges

    node_ids = graph.fetch_ids_from_db()
    # Add edges to networkX
    for source_id in node_ids:
        for target_id, _, edge_data in graph.traverse(source_id, with_bodies=True):
            edge_label = graph.search_edge_label(source_id, target_id)
            G.add_edge(
                source_id, target_id, label=edge_label, **(json.loads(edge_data))
            )

    node_ids_with_edges = set([node for edge in G.edges() for node in edge])
    for node_id in node_ids:
        if node_id not in node_ids_with_edges:
            node_data = graph.search_node(node_id)
            node_label = graph.search_node_label(node_id)
            G.add_node(node_id, label=node_label, **node_data)

    if post_visualize:
        # Visualizing the NetworkX Graph
        plt.figure(figsize=(10, 8), dpi=100)  # Increase the figure size and resolution
        pos = nx.spring_layout(G)  # Use spring layout for better node positioning
        nx.draw(
            G,
            pos,
            with_labels=True,  # Show node labels
            node_color="skyblue",
            edge_color="gray",
            font_size=10,  # Adjust font size as needed
            node_size=500,  # Adjust node size as needed
            font_weight="bold",  # Make node labels bold
            font_color="black",  # Set node label color
        )
        plt.axis("on")  # Show the axes
        plt.show()

    return G


def from_networkx(network_graph: nx) -> KnowledgeGraph:
    graph = KnowledgeGraph()

    node_ids_with_edges = set()

    # Convert networkX edges to personal graph edges
    for source_id, target_id, edge_data in network_graph.edges(data=True):
        edge_attributes: Dict[str, Any] = edge_data
        edge_label: str = edge_attributes.pop("label", "")
        node_ids_with_edges.add(str(source_id))
        node_ids_with_edges.add(str(target_id))

        edge = Edge(
            source=str(source_id),
            target=str(target_id),
            label=edge_label[0] if edge_label else "",
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
                label=node_label[0] if node_label else "",
                attributes=json.dumps(node_attributes),
            )
            graph.nodes.append(node)

    return graph
