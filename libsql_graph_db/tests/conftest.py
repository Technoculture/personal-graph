import pytest
from unittest.mock import patch


@pytest.fixture
def mock_atomic():
    with patch("libsql_graph_db.database.atomic") as mock_atomic:
        yield mock_atomic


@pytest.fixture
def mock_db_connection_and_cursor():
    with patch("libsql_graph_db.database.libsql.connect") as mock_connect:
        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value
        yield mock_connection, mock_cursor


@pytest.fixture
def mock_embeddings_model():
    with patch(
        "libsql_graph_db.database.embed_obj.get_embedding"
    ) as mock_get_embedding:
        # Define fixed embeddings for testing
        fixed_embeddings = {
            '{"name": "Alice", "age": 30}': [0.1, 0.2, 0.3],
            '{"name": "Peri", "age": "90"}': [0.4, 0.5, 0.6],
            '{"name": "Pema", "age": "66"}': [0.7, 0.8, 0.9],
            '{"name": "Bob", "age": 35}': [0.11, 0.22, 0.33],
        }
        # Mock the get_embedding function to return fixed embeddings
        mock_get_embedding.side_effect = lambda x: fixed_embeddings.get(x, [])

        yield mock_get_embedding


@pytest.fixture
def mock_find_node():
    with patch("libsql_graph_db.visualizers.db.find_node") as mock_find_node:
        yield mock_find_node


@pytest.fixture
def mock_get_connections():
    with patch(
        "libsql_graph_db.visualizers.db.get_connections"
    ) as mock_get_connections:
        yield mock_get_connections


@pytest.fixture
def mock_dot_render():
    with patch(
        "libsql_graph_db.visualizers.Digraph.render",
        new=lambda self, *args, **kwargs: None,
    ):
        yield
