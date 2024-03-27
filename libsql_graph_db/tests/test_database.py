from libsql_graph_db.database import (
    add_node,
    add_nodes,
    upsert_node,
    remove_nodes,
    find_node,
    get_connections,
    upsert_nodes,
    remove_node,
    connect_nodes,
    connect_many_nodes,
    traverse,
)


def test_add_node(mock_atomic, mock_db_connection_and_cursor, mock_embeddings_model):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    data = {"name": "Alice", "age": 30}
    add_node(data, 1)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_add_nodes(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    data = [{"name": "Peri", "age": "90"}, {"name": "Pema", "age": "66"}]
    ids = [1, 2]
    add_nodes(data, ids)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_upsert_node(mock_atomic, mock_db_connection_and_cursor, mock_embeddings_model):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    data = {"name": "Bob", "age": 35}
    upsert_node(1, data)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_upsert_nodes(
    mock_atomic, mock_db_connection_and_cursor, mock_embeddings_model
):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    data = [
        {"name": "Peri", "age": "90"},
        {"name": "Pema", "age": "66"},
        {"name": "Charlie", "age": 40},
    ]
    ids = [1, 2, 3]
    upsert_nodes(data, ids)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_connect_node(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    source_id = 1
    target_id = 2
    properties = {"weight": 0.5}
    connect_nodes(source_id, target_id, properties)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_connect_many_nodes(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    sources = [1, 2, 3]
    targets = [4, 5, 6]
    properties = [{"weight": 0.5}, {"weight": 0.8}, {"weight": 0.6}]
    connect_many_nodes(sources, targets, properties)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_remove_node(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    identifier = 1
    remove_node(identifier)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_remove_nodes(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    remove_nodes([1, 2, 3])(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_traverse_node(mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    traverse_path = traverse(src=1, tgt=2)
    mock_cursor.execute.assert_called()
    assert traverse_path == []


def test_find_node(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    mock_cursor.fetchone.return_value = '{"id": 1, "name": "Alice", "age": 30}'
    find_node(1)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()


def test_get_connections(mock_atomic, mock_db_connection_and_cursor):
    mock_connection, mock_cursor = mock_db_connection_and_cursor
    get_connections(1)(mock_cursor, mock_connection)
    mock_cursor.execute.assert_called()
