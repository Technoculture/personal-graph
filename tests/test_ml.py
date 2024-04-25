import json
import networkx as nx  # type: ignore
from personal_graph.ml import to_networkx, from_networkx
import personal_graph.graph as pg


def test_to_networkx(mock_personal_graph, mock_atomic, mock_db_connection_and_cursor):
    networkx_graph = to_networkx(mock_personal_graph)

    # Check if the returned object is a NetworkX graph
    assert isinstance(networkx_graph, nx.Graph)


def test_from_networkx(mock_personal_graph, mock_atomic, mock_db_connection_and_cursor):
    networkx_graph = nx.Graph()
    networkx_graph.add_node(
        "1", label="Sample Label", attribute=json.dumps({"Person": "scholar"})
    )
    networkx_graph.add_node(
        "2", label="Researching", attribute=json.dumps({"University": "Stanford"})
    )
    networkx_graph.add_edge(
        "1", "2", label="has", attribute=json.dumps({"Person": "University"})
    )

    personal_graph = from_networkx(networkx_graph)

    # Check if the returned object is a Personal Graph
    assert isinstance(personal_graph, pg.Graph)
