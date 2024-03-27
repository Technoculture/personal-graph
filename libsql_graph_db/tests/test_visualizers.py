from libsql_graph_db.visualizers import graphviz_visualize, graphviz_visualize_bodies


def test_graphviz_visualize(
    mock_atomic,
    mock_db_connection_and_cursor,
    mock_find_node,
    mock_get_connections,
    mock_dot_render,
):
    mock_find_node.return_value = {"id": 1, "name": "Alice", "age": 30}
    mock_get_connections.return_value = [
        (1, 2, {"weight": 0.5}),
        (2, 3, {"weight": 0.7}),
    ]

    graphviz_visualize(
        db_url=None,
        auth_token=None,
        dot_file="mock_dot_file.dot",
        path=[1, 2, 3],
        format="png",
        exclude_node_keys=[],
        hide_node_key=False,
        node_kv=" ",
        exclude_edge_keys=[],
        hide_edge_key=False,
        edge_kv=" ",
    )


def test_graphviz_visualize_bodies(
    mock_atomic,
    mock_db_connection_and_cursor,
    mock_find_node,
    mock_get_connections,
    mock_dot_render,
):
    path_data = [
        (1, "()", '{"id": 1, "name": "Alice", "age": 30}'),
        (2, "->", '{"id": 2, "name": "Bob", "age": 35}'),
        (3, "->", '{"id": 3, "name": "Charlie", "age": 40}'),
    ]

    graphviz_visualize_bodies(
        dot_file="mock_file_with_bodies.dot",
        path=path_data,
        format="png",
        exclude_node_keys=[],
        hide_node_key=False,
        node_kv=" ",
        exclude_edge_keys=[],
        hide_edge_key=False,
        edge_kv=" ",
    )
