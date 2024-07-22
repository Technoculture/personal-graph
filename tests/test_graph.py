"""
Unit test for high level apis
"""

import networkx as nx  # type: ignore
import pytest
from fhir.resources import fhirtypes  # type: ignore

from personal_graph import GraphDB, Node, EdgeInput, KnowledgeGraph
from personal_graph.ml import networkx_to_pg, pg_to_networkx
from personal_graph.text import text_to_graph


def test_add_node(graph, mock_db_connection_and_cursor):
    node = Node(
        id=1,
        attributes={"name": "Jack", "body": "Jack is Joe's cousin brother"},
        label="relative",
    )
    assert graph.add_node(node) is None


def test_add_nodes(graph, mock_db_connection_and_cursor):
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


def test_add_edge(graph, mock_db_connection_and_cursor):
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


def test_add_edges(graph, mock_db_connection_and_cursor):
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


def test_update_node(graph, mock_db_connection_and_cursor):
    node = Node(id=1, attributes={"name": "Alice", "age": "30"}, label="relative")

    assert graph.update_node(node) is None


def test_update_nodes(graph, mock_db_connection_and_cursor):
    nodes = [
        Node(id=1, attributes={"name": "Peri", "age": "90"}, label="relative"),
        Node(id=2, attributes={"name": "Peri", "age": "90"}, label="relative"),
    ]

    assert graph.update_nodes(nodes) is None


def test_remove_node(graph, mock_db_connection_and_cursor):
    assert graph.remove_node(1) is None


def test_remove_nodes(graph, mock_db_connection_and_cursor):
    assert graph.remove_node([1, 6, 8]) is None


def test_search_node(graph, mock_db_connection_and_cursor):
    assert graph.search_node(1) is not None


def test_traverse(graph, mock_db_connection_and_cursor):
    assert graph.traverse(1, 2) is not None


def test_insert(
    graph,
    mock_openai_client,
    mock_generate_graph,
    mock_db_connection_and_cursor,
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph

    test_add_nodes(graph, mock_db_connection_and_cursor)

    query = "Alice has suffocation at night"
    kg = text_to_graph(query)
    result = graph.insert_graph(kg)
    assert result == mock_generate_graph


def test_search_query(
    graph,
    mock_openai_client,
    mock_generate_graph,
    mock_db_connection_and_cursor,
):
    mock_openai_client.chat.completions.create.return_value = mock_generate_graph
    test_insert(
        graph,
        mock_openai_client,
        mock_generate_graph,
        mock_db_connection_and_cursor,
    )

    result = graph.search_from_graph("Suffocation problem.")
    assert isinstance(result, KnowledgeGraph)


def test_merge_by_similarity(graph, mock_db_connection_and_cursor):
    test_add_nodes(graph, mock_db_connection_and_cursor)

    assert graph.merge_by_similarity(threshold=0.9) is None


def test_find_nodes_like(graph, mock_db_connection_and_cursor):
    assert graph.find_nodes_like("relative", threshold=0.9) is not None


def test_to_networkx(mock_personal_graph, mock_db_connection_and_cursor):
    networkx_graph = pg_to_networkx(mock_personal_graph)

    # Check if the returned object is a NetworkX graph
    assert isinstance(networkx_graph, nx.Graph)

    return networkx_graph


def test_from_networkx(graph, mock_personal_graph, mock_db_connection_and_cursor):
    personal_graph = networkx_to_pg(
        test_to_networkx(mock_personal_graph, mock_db_connection_and_cursor),
        mock_personal_graph,
    )

    # Check if the returned object is a Personal Graph
    assert isinstance(personal_graph, GraphDB)


def test_graphviz_visualize(
    graph,
    mock_db_connection_and_cursor,
    mock_find_node,
    mock_get_connections,
    mock_dot_render,
):
    mock_find_node.return_value = {"id": 1, "name": "Alice", "age": 30}
    mock_get_connections.return_value = [
        (
            1,
            2,
            2,
            "sample label",
            '{"weight": 0.5}',
            "2024-05-14 09:45:47",
            "2024-05-14 09:45:47",
        ),
        (
            2,
            2,
            3,
            "sample label",
            '{"weight": 0.7}',
            "2024-05-14 09:45:47",
            "2024-05-14 09:45:47",
        ),
    ]

    graph.visualize(
        file="mock_dot_file.dot",
        id=[1, 2, 3],
    )


def test_add_node_with_ontology(
    graph_with_fhir_ontology, mock_db_connection_and_cursor
):
    """
    Test adding a single node with specific attributes to the ontology graph.

    @param graph_with_fhir_ontology: A fixture providing an instance of the graph with the FHIR ontology.
    @param mock_db_connection_and_cursor: A fixture providing a mock database connection and cursor.
    @return: None
    """
    node = Node(
        id="1",
        label="Person",
        attributes={
            "active": "False",
            "name": "John Doe",
            "id": "xyz",
        },
    )
    assert graph_with_fhir_ontology.add_node(node, node_type="Organization") is None


def test_invalid_fhir_resource_type(
    graph_with_fhir_ontology, mock_db_connection_and_cursor
):
    """
    Test adding a node with an invalid FHIR resource type.

    @param graph_with_fhir_ontology: A fixture providing an instance of the graph with the FHIR ontology.
    @param mock_db_connection_and_cursor: A fixture providing a mock database connection and cursor.
    @return: None
    """
    node = Node(
        id="1",
        label="Person",
        attributes={
            "name": "John Doe",
            "id": "xyz",
        },
    )
    with pytest.raises(ValueError) as excinfo:
        graph_with_fhir_ontology.add_node(node, node_type="CareTaker")
    assert (
        str(excinfo.value)
        == "Node type or attributes does not match any of the provided ontologies."
    )


def test_add_nodes_with_ontology(
    graph_with_fhir_ontology, mock_db_connection_and_cursor
):
    """
    Test adding multiple nodes with specific attributes to the ontology graph.

    @param graph_with_fhir_ontology: A fixture providing an instance of the graph with the FHIR ontology.
    @param mock_db_connection_and_cursor: A fixture providing a mock database connection and cursor.
    @return: None
    """
    nodes = [
        Node(
            id=1,
            attributes={
                "active": "True",
                "name": "Messi",
                "id": "29",
            },
            label="Player",
        ),
        Node(
            id=2,
            attributes={"name": "Alzheimer", "active": "False", "id": "xyz"},
            label="Disease",
        ),
    ]

    assert (
        graph_with_fhir_ontology.add_nodes(
            nodes,
            node_types=["Organization", "Organization"],
            delete_if_properties_not_match=[True, False],
        )
        is None
    )


def test_insert_with_ontology(graph_with_fhir_ontology, mock_db_connection_and_cursor):
    """
    Test inserting a node with FHIR attributes into the ontology graph.

    @param graph_with_fhir_ontology: A fixture providing an instance of the graph with the FHIR ontology.
    @param mock_db_connection_and_cursor: A fixture providing a mock database connection and cursor.
    @return: None
    """
    text = "User is claustrophobic."
    attributes = {
        "category": [fhirtypes.CodeableConceptType(text="asthma")],
        "identifier": [fhirtypes.IdentifierType(value="1")],
        "intent": "proposal",
        "status": "active",
        "subject": fhirtypes.ReferenceType(reference="Patient/123"),
    }
    assert (
        graph_with_fhir_ontology.insert(text, attributes, node_type="CarePlan") is None
    )
