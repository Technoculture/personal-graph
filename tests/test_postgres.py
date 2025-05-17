import pytest
from unittest.mock import patch

from personal_graph import GraphDB, Node, EdgeInput
from personal_graph.database.postgres.postgres import Postgres


@pytest.fixture
def mock_pg_connection_and_cursor():
    with patch(
        "personal_graph.database.postgres.postgres.Postgres.atomic"
    ) as mock_atomic:
        mock_connection = mock_atomic.return_value
        mock_cursor = mock_connection.cursor.return_value
        yield mock_connection, mock_cursor


@pytest.fixture
def pg_graph(mock_openai_client, mock_embeddings_model):
    with patch("openai.OpenAI", return_value=mock_openai_client):
        with patch(
            "personal_graph.embeddings.OpenAIEmbeddingsModel",
            return_value=mock_embeddings_model,
        ):
            graph = GraphDB(database=Postgres())
            yield graph


def test_pg_add_node(pg_graph, mock_pg_connection_and_cursor):
    node = Node(id=1, attributes={"name": "Alice"}, label="person")
    assert pg_graph.add_node(node) is None


def test_pg_add_edge(pg_graph, mock_pg_connection_and_cursor):
    n1 = Node(id=1, attributes={"name": "Alice"}, label="person")
    n2 = Node(id=2, attributes={"name": "Bob"}, label="person")
    edge = EdgeInput(source=n1, target=n2, label="knows", attributes={})
    assert pg_graph.add_edge(edge) is None


def test_pg_update_node(pg_graph, mock_pg_connection_and_cursor):
    node = Node(id=1, attributes={"name": "Alice"}, label="person")
    assert pg_graph.update_node(node) is None


def test_pg_remove_node(pg_graph, mock_pg_connection_and_cursor):
    assert pg_graph.remove_node(1) is None
