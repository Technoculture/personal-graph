import networkx as nx  # type: ignore
from personal_graph.ml import to_networkx, from_networkx
from personal_graph.models import KnowledgeGraph


def test_to_networkx(mock_personal_graph, mock_atomic, mock_db_connection_and_cursor):
    networkx_graph = to_networkx(mock_personal_graph)

    # Check if the returned object is a NetworkX graph
    assert isinstance(networkx_graph, nx.Graph)


def test_from_networkx(mock_personal_graph, mock_atomic, mock_db_connection_and_cursor):
    networkx_graph = nx.Graph()
    networkx_graph.add_node("1", label="Sample Label", attribute={"Person": "scholar"})
    networkx_graph.add_node(
        "2", label="Researching", attribute={"University": "Stanford"}
    )
    networkx_graph.add_node("3", label="value", attribute={"Body": "Sample Body"})
    networkx_graph.add_edge("1", "2", label="has", attribute={"Person": "University"})

    personal_graph = from_networkx(networkx_graph)

    # Check if the returned object is a KnowledgeGraph
    assert isinstance(personal_graph, KnowledgeGraph)
    assert len(personal_graph.edges) == 1

    # Isolated Nodes
    assert len(personal_graph.nodes) == 1
