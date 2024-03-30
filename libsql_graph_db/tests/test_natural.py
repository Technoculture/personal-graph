from libsql_graph_db.models import KnowledgeGraph
from libsql_graph_db.natural import insert_into_graph, search_from_graph


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
