import json
import networkx as nx  # type: ignore
import matplotlib.pyplot as plt
from personal_graph.graph import Graph


def to_networkx(graph: Graph) -> nx.Graph:
    """
    Convert the graph database to a NetworkX DiGraph object.
    """
    G = nx.Graph()  # Empty Graph with no nodes and edges

    # Add nodes
    node_ids = graph.fetch_ids_from_db()
    for node_id in node_ids:
        node_data = graph.search_node(node_id)
        G.add_node(node_id, **node_data)

    # Add edges
    for source_id in node_ids:
        for target_id, _, edge_data in graph.traverse(source_id, with_bodies=True):
            G.add_edge(source_id, target_id, **(json.loads(edge_data)))

    # Visualizing the NetworkX Graph
    plt.figure(figsize=(10, 8))
    nx.draw(
        G,
        with_labels=True,
        node_color="skyblue",
        edge_color="gray",
        font_size=8,
        node_size=500,
    )
    plt.axis("off")
    plt.show()

    return G
