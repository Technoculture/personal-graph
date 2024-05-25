import json
import pytest
from unittest.mock import patch, Mock

from personal_graph import (
    Graph,
    KnowledgeGraph,
    Node,
    Edge,
    EdgeInput,
    OpenAIEmbeddingsModel,
)
from personal_graph.clients import LiteLLMEmbeddingClient
from personal_graph.persistence_layer.database import SQLite
from personal_graph.persistence_layer.vector_store import SQLiteVSS


@pytest.fixture
def mock_db_connection_and_cursor():
    with patch(
        "personal_graph.persistence_layer.database.sqlite.sqlite.SQLite.atomic"
    ) as mock_connect:
        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value
        yield mock_connection, mock_cursor


@pytest.fixture
def embedding_model():
    return OpenAIEmbeddingsModel(None, "", 384)


@pytest.fixture
def mock_find_node():
    with patch(
        "personal_graph.persistence_layer.database.sqlite.sqlite.SQLite._find_node"
    ) as mock_find_node:
        yield mock_find_node


@pytest.fixture
def mock_get_connections():
    with patch(
        "personal_graph.persistence_layer.database.sqlite.sqlite.SQLite.get_connections"
    ) as mock_get_connections:
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


class MockEmbeddingsModel(Mock):
    def get_embedding(self, data):
        fixed_embeddings = {
            '{"name": "Alice", "age": "30"}': [0.1, 0.2, 0.3],
            '{"name": "Peri", "age": "90"}': [0.4, 0.5, 0.6],
            '{"name": "Pema", "age": "66"}': [0.7, 0.8, 0.9],
            '{"name": "Bob", "age": 35}': [0.11, 0.22, 0.33],
        }
        return fixed_embeddings.get(json.dumps(data), [])


@pytest.fixture
def mock_embeddings_model():
    mock_embeddings_model = MockEmbeddingsModel()
    with patch(
        "personal_graph.embeddings.OpenAIEmbeddingsModel",
        return_value=mock_embeddings_model,
    ):
        yield mock_embeddings_model


@pytest.fixture
def graph(mock_openai_client, mock_embeddings_model):
    with patch("openai.OpenAI", return_value=mock_openai_client):
        with patch(
            "personal_graph.embeddings.OpenAIEmbeddingsModel",
            return_value=mock_embeddings_model,
        ):
            vector_store = SQLiteVSS(
                db=SQLite(use_in_memory=True),
                embedding_client=LiteLLMEmbeddingClient(),
            )
            graph = Graph(vector_store=vector_store)
            yield graph


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
        "personal_graph.graph_generator.OpenAITextToGraphParser.generate",
        return_value=mock_knowledge_graph,
    ):
        yield mock_knowledge_graph


@pytest.fixture
def mock_personal_graph(mock_openai_client, mock_db_connection_and_cursor):
    vector_store = SQLiteVSS(
        db=SQLite(use_in_memory=True),
        embedding_client=LiteLLMEmbeddingClient(),
    )
    graph = Graph(vector_store=vector_store)

    node1 = Node(id=1, label="Sample Label", attributes={"Person": "scholar"})
    node2 = Node(id=2, label="Researching", attributes={"University": "Stanford"})
    graph.add_nodes([node1, node2])

    edge1 = EdgeInput(
        source=node1, target=node2, label="has", attributes={"Person": "University"}
    )
    graph.add_edge(edge1)
    yield graph
