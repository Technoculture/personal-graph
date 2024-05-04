"""
Unit test for high level apis
"""

import networkx as nx  # type: ignore

from personal_graph.models import Node, EdgeInput, KnowledgeGraph
from personal_graph.graph import Graph


def test_add_node(graph, mock_atomic, mock_db_connection_and_cursor):
    node = Node(
        id=1,
        attributes={"name": "Jack", "body": "Jack is Joe's cousin brother"},
        label="relative",
    )
    assert graph.add_node(node) is None


def test_add_nodes(graph, mock_atomic, mock_db_connection_and_cursor):
    nodes = [
        Node(
            id=1,
            attributes={"body": "Jerry loses her weight 10kg last week."},
            label="Diabetes",
        ),
        Node(
            id=2,
            attributes={"name": "Bob", "body": "Bob is feeling stressed and tensed."},
            label="Stress",
        ),
    ]

    assert graph.add_nodes(nodes) is None


def test_add_edge(graph, mock_atomic, mock_db_connection_and_cursor):
    node1 = Node(
        id=3,
        label="relative",
        attributes={
            "name": "Alice",
            "body": "Alice is Jack's cousin sister. She lives in CA.",
        },
    )
    node2 = Node(
        id=4, label="CA", attributes={"body": "CA has a lot of greenery and indians."}
    )

    edge = EdgeInput(
        source=node1, target=node2, label="KNOWS", attributes={"since": "2015"}
    )

    assert graph.add_edge(edge) is None


def test_add_edges(graph, mock_atomic, mock_db_connection_and_cursor):
    node1 = Node(id=3, label="Person", attributes={"name": "Alice", "age": "30"})
    node2 = Node(id=4, label="Person", attributes={"name": "Bob", "age": "25"})
    node3 = Node(
        id=1,
        label="Diabetes",
        attributes={"body": "Continuous urination and weight loss"},
    )
    node4 = Node(
        id=2,
        label="Dizziness",
        attributes={"body": "Jack is feeling stressed and feeling quite dizzy."},
    )

    edge1 = EdgeInput(
        source=node1, target=node2, label="KNOWS", attributes={"since": "2015"}
    )

    edge2 = EdgeInput(
        source=node3, target=node2, label="KNOWS", attributes={"since": "2015"}
    )
    edge3 = EdgeInput(
        source=node1, target=node4, label="KNOWS", attributes={"since": "2015"}
    )

    assert graph.add_edges([edge1, edge2, edge3]) is None


def test_update_node(graph, mock_atomic, mock_db_connection_and_cursor):
    node = Node(id=1, attributes={"name": "Alice", "age": "30"}, label="relative")

    assert graph.update_node(node) is None


def test_update_nodes(graph, mock_atomic, mock_db_connection_and_cursor):
    nodes = [
        Node(id=1, attributes={"name": "Peri", "age": "90"}, label="relative"),
        Node(id=2, attributes={"name": "Peri", "age": "90"}, label="relative"),
    ]

    assert graph.update_nodes(nodes) is None


def test_remove_node(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph.remove_node(1) is None


def test_remove_nodes(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph.remove_node([1, 6, 8]) is None


def test_search_node(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph.search_node(1) is not None


def test_traverse(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph.traverse(1, 2) is not None


def test_insert(
    graph,
    mock_openai_client,
    mock_generate_graph,
    mock_atomic,
    mock_db_connection_and_cursor,
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph

    test_add_nodes(graph, mock_atomic, mock_db_connection_and_cursor)

    result = graph.insert_into_graph("Alice has suffocation at night.")
    assert result == mock_generate_graph


def test_search_query(
    graph,
    mock_openai_client,
    mock_generate_graph,
    mock_atomic,
    mock_db_connection_and_cursor,
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph
    test_insert(
        graph,
        mock_openai_client,
        mock_generate_graph,
        mock_atomic,
        mock_db_connection_and_cursor,
    )

    result = graph.search_from_graph("Suffocation problem.")
    assert isinstance(result, KnowledgeGraph)


def test_merge_by_similarity(graph, mock_atomic, mock_db_connection_and_cursor):
    test_add_nodes(graph, mock_atomic, mock_db_connection_and_cursor)

    assert graph.merge_by_similarity(0.9) is None


def test_find_nodes_like(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph.find_nodes_like("relative", 0.9) is not None


def test_get_connections(graph, mock_atomic, mock_db_connection_and_cursor):
    assert graph._get_connections(1) is not None


def test_to_networkx(mock_personal_graph, mock_atomic, mock_db_connection_and_cursor):
    networkx_graph = mock_personal_graph.pg_to_networkx()

    # Check if the returned object is a NetworkX graph
    assert isinstance(networkx_graph, nx.Graph)

    return networkx_graph


def test_from_networkx(
    graph, mock_personal_graph, mock_atomic, mock_db_connection_and_cursor
):
    personal_graph = mock_personal_graph.networkx_to_pg(
        test_to_networkx(
            mock_personal_graph, mock_atomic, mock_db_connection_and_cursor
        )
    )

    # Check if the returned object is a Personal Graph
    assert isinstance(personal_graph, Graph)


def test_graphviz_visualize(
    graph,
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

    graph.visualize(
        file="mock_dot_file.dot",
        path=[1, 2, 3],
    )
