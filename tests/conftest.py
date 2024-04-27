import pytest
from unittest.mock import patch

from personal_graph.embeddings import OpenAIEmbeddingsModel
from personal_graph.graph import Graph
from personal_graph.models import KnowledgeGraph, Node, Edge, EdgeInput


@pytest.fixture
def mock_atomic():
    with patch("personal_graph.database.atomic") as mock_atomic:
        yield mock_atomic


@pytest.fixture
def mock_db_connection_and_cursor():
    with patch("personal_graph.database.libsql.connect") as mock_connect:
        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value
        yield mock_connection, mock_cursor


@pytest.fixture
def embedding_model():
    return OpenAIEmbeddingsModel(None, "")


@pytest.fixture
def mock_find_node():
    with patch("personal_graph.visualizers.db.find_node") as mock_find_node:
        yield mock_find_node


@pytest.fixture
def mock_get_connections():
    with patch("personal_graph.visualizers.db.get_connections") as mock_get_connections:
        yield mock_get_connections


@pytest.fixture
def mock_dot_render():
    with patch(
        "personal_graph.visualizers.Digraph.render",
        new=lambda self, *args, **kwargs: None,
    ):
        yield


@pytest.fixture
def mock_openai_client():
    with patch("instructor.from_openai") as mock_client:
        yield mock_client


@pytest.fixture
def mock_generate_graph():
    mock_knowledge_graph = KnowledgeGraph(
        nodes=[
            Node(id=1, attributes="Mock Node 1", label="Label 1"),
            Node(id=2, attributes="Mock Node 2", label="Label 2"),
        ],
        edges=[
            Edge(
                source=1,
                target=2,
                label="Mock Edge",
                attributes={"body": "Sample body"},
            )
        ],
    )
    with patch(
        "personal_graph.natural.generate_graph", return_value=mock_knowledge_graph
    ):
        yield mock_knowledge_graph


@pytest.fixture
def mock_personal_graph(mock_atomic, mock_db_connection_and_cursor):
    graph = Graph()

    node1 = Node(id=1, label="Sample Label", attributes={"Person": "scholar"})
    node2 = Node(id=2, label="Researching", attributes={"University": "Stanford"})
    graph.add_nodes([node1, node2])

    edge1 = EdgeInput(
        source=node1, target=node2, label="has", attributes={"Person": "University"}
    )
    graph.add_edge(edge1)
    yield graph
