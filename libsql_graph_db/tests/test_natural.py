from libsql_graph_db.natural import insert_into_graph


def test_insert_into_graph(
    mock_openai_client, mock_atomic, mock_generate_graph, mock_db_connection_and_cursor
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph

    query = "Mock Node"
    result = insert_into_graph(query)

    assert result == mock_generate_graph
