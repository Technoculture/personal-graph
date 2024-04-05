"""
Unit test for high level apis
"""

from personal_graph.models import Node
from personal_graph.graph import Graph


def test_add_node(mock_atomic, mock_db_connection_and_cursor):
    graph = Graph()
    node = Node(
        id=1,
        attribute={"name": "Jack", "body": "Jack is Joe's cousin brother"},
        label="relative",
    )
    assert graph.add_node(node) is None


def test_add_nodes(mock_atomic, mock_db_connection_and_cursor):
    graph = Graph()
    nodes = [
        Node(
            id=1,
            attribute={"body": "Jerry loses her weight 10kg last week."},
            label="Diabetes",
        ),
        Node(
            id=2,
            attribute={"name": "Bob", "body": "Bob is feeling stressed and tensed."},
            label="Stress",
        ),
    ]
    assert graph.add_nodes(nodes) is None
