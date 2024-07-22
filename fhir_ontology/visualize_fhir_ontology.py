"""
Visualising fhir ontology using python interactive tool i.e plotly
"""

import json
import logging
import argparse

import networkx as nx  # type: ignore
import plotly.graph_objects as go  # type: ignore
from plotly.io import write_html  # type: ignore


def visualise_fhir_with_plotly(args):
    # Load the JSON data
    with open(args.json_file, "r") as f:
        ontology_data = json.load(f)

    # Create a NetworkX graph
    G = nx.MultiGraph()

    # Add nodes and edges to the graph
    for node in ontology_data["nodes"]:
        G.add_node(node["id"], label=node["label"])

    for edge in ontology_data["edges"]:
        G.add_edge(edge["source"], edge["target"], label=edge["label"])

    # Get node positions using a layout algorithm
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Create edge trace
    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=0.5, color="#888"),
            hoverinfo="text",
            mode="lines+text",
            text=[edge[2]["label"]],
            textposition="middle center",
            textfont=dict(size=8),
        )
        edge_traces.append(edge_trace)

        # Add edge label
        edge_label_trace = go.Scatter(
            x=[(x0 + x1) / 2],
            y=[(y0 + y1) / 2],
            mode="text",
            text=[edge[2]["label"]],
            textposition="middle center",
            textfont=dict(size=8, color="red"),
            hoverinfo="none",
        )
        edge_traces.append(edge_label_trace)

    # Create node trace
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=[
            f"{node}<br># of connections: {len(list(G.edges(node)))}"
            for node in G.nodes()
        ],
        textposition="top center",
        textfont=dict(size=8),
        marker=dict(
            showscale=True,
            colorscale="YlGnBu",
            size=10,
            color=[len(list(G.neighbors(node))) for node in G.nodes()],
            colorbar=dict(
                thickness=15,
                title="Node Connections",
                xanchor="left",
                titleside="right",
            ),
        ),
    )

    # Create the figure
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title="FHIR Ontology Network Graph",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="FHIR Ontology",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    # Save as interactive HTML
    write_html(fig, file=args.output_html_file, auto_open=True)
    logging.info(f"Interactive graph saved as {args.output_html_file}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/fhir_ontology.log",
    )

    parser = argparse.ArgumentParser(description="Visualising entire fhir ontology")
    parser.add_argument(
        "--json-file", default="fhir_ontology/fhir_ontology.json", type=str
    )
    parser.add_argument(
        "--output-html-file", default="fhir_ontology/output.html", type=str
    )
    arguments = parser.parse_args()
    visualise_fhir_with_plotly(args=arguments)
