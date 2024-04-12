from personal_graph.models import KnowledgeGraph, Node, Edge
from personal_graph.natural import (
    insert_into_graph,
    search_from_graph,
    visualize_knowledge_graph,
)


def test_insert_into_graph(
    mock_openai_client, mock_atomic, mock_generate_graph, mock_db_connection_and_cursor
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph

    query = "Mock Node Insert"
    result = insert_into_graph(query)

    assert result == mock_generate_graph
    assert isinstance(result, KnowledgeGraph)


def test_search_from_graph(
    mock_openai_client, mock_atomic, mock_generate_graph, mock_db_connection_and_cursor
):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph

    query = "Mock Node Search"
    result = search_from_graph(query)

    assert isinstance(result, KnowledgeGraph)
    mock_cursor.execute.assert_called()


def test_visualize_knowledge_graph(mock_dot_render):
    kg = KnowledgeGraph()
    kg.nodes = [
        Node(id="1", label="Node1", attributes="Attribute1"),
        Node(id="2", label="Node2", attributes="Attribute2"),
    ]
    kg.edges = [
        Edge(source="1", target="2", label="Edge1", attributes="Attribute1"),
        Edge(source="2", target="3", label="Edge2", attributes="Attribute2"),
    ]

    visualize_knowledge_graph(kg)
