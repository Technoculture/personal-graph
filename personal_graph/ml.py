import json
from typing import Dict, Any

import networkx as nx  # type: ignore
from graphviz import Digraph  # type: ignore
from matplotlib import pyplot as plt

from personal_graph import GraphDB
from personal_graph import KnowledgeGraph, Node, Edge, EdgeInput


def pg_to_networkx(graph: GraphDB, *, post_visualize: bool = False):
    """
    Convert the graph database to a NetworkX DiGraph object.
    """
    G = nx.Graph()  # Empty Graph with no nodes and edges

    node_ids = graph.fetch_ids_from_db()
    # Add edges to networkX
    for source_id in node_ids:
        outdegree_edges = graph.search_outdegree_edges(source_id)
        if outdegree_edges is []:
            continue

        for target_id, edge_label, edge_data in outdegree_edges:
            if isinstance(edge_data, str):
                edge_data = json.loads(edge_data)

            edge_data["label"] = edge_label
            G.add_edge(source_id, target_id, **edge_data)

    for target_id in node_ids:
        indegree_edges = graph.search_indegree_edges(target_id)

        if indegree_edges is []:
            continue

        for source_id, edge_label, edge_data in indegree_edges:
            if isinstance(edge_data, str):
                edge_data = json.loads(edge_data)

            edge_data["label"] = edge_label
            G.add_edge(source_id, target_id, **edge_data)

    for node_id in node_ids:
        node_data = graph.search_node(node_id)
        if "label" not in node_data.keys():
            node_data["label"] = graph.db.search_node_label(node_id)

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


def networkx_to_pg(
    networkx_graph: nx,
    graph: GraphDB,
    *,
    post_visualize: bool = False,
    override: bool = True,
):
    if override:
        node_ids = graph.fetch_ids_from_db()
        graph.remove_nodes(node_ids)

    node_ids_with_edges = set()
    kg = KnowledgeGraph()

    # Convert networkX edges to personal graph edges
    for source_id, target_id, edge_data in networkx_graph.edges(data=True):
        edge_attributes: Dict[str, Any] = edge_data
        edge_label: str = edge_attributes["label"]

        if not override:
            # Check if the node with the given id exists, if not then firstly add the node.
            source = graph.search_node(source_id)
            if source is []:
                graph.add_node(
                    Node(
                        id=str(source_id),
                        label=edge_label if edge_label else "",
                        attributes=edge_attributes,
                    )
                )
            else:
                node_ids_with_edges.add(str(source_id))

            target = graph.search_node(target_id)
            if target is []:
                node_ids_with_edges.remove(str(target_id))
                graph.add_node(
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
                if_node_exists = graph.search_node(node_id)

                if if_node_exists:
                    graph.update_node(node)
                else:
                    graph.add_node(node)
            else:
                graph.add_node(node)
            kg.nodes.append(node)

    for edge in kg.edges:
        source_node_attributes = graph.search_node(edge.source)
        source_node_label = graph.search_node_label(edge.source)
        target_node_attributes = graph.search_node(edge.target)
        target_node_label = graph.search_node_label(edge.target)
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
        graph.add_edge(final_edge_to_be_inserted)

    if post_visualize:
        # Visualize the personal graph using graphviz
        dot = Digraph()

        for node in kg.nodes:
            dot.node(node.id, label=f"{node.label}: {node.id}")

        for edge in kg.edges:
            dot.edge(edge.source, edge.target, label=edge.label)

        dot.render("personal_graph.gv", view=True)

    return graph
