import fhir.resources as fhir  # type: ignore
from fhir.resources import fhirtypes

from personal_graph import GraphDB, Node
from personal_graph.ontology import from_rdf


biography_ontology = from_rdf("./biography_schema.rdf")
with GraphDB(ontologies=[fhir, biography_ontology]) as graph:
    node1 = Node(
        id="1",
        label="Pabelo",
        attributes={
            "active": "False",
            "name": "John Doe",
            "id": "xyz",
        },
    )
    node2 = Node(
        id="1",
        label="Pabelo",
        attributes={
            "entity": "sample entity",
            "device": "mobile",
            "group": "management",
            "medication": "instant",
            "individual": "personality",
        },
    )
    node3 = Node(
        id="3", label="close relative", attributes={"name": "Alice", "age": "30"}
    )
    node4 = Node(
        id="2",
        label="xyz",
        attributes={
            "category": [fhirtypes.CodeableConceptType(text="asthma")],
            "identifier": [fhirtypes.IdentifierType(value="1")],
            "intent": "proposal",
            "status": "active",
            "subject": fhirtypes.ReferenceType(reference="Patient/123"),
        },
    )
    node5 = Node(
        id="2",
        label="pop",
        attributes={
            "participant": "True",
            "interval": "John Doe",
        },
    )

    # Test w5_ontology which is loaded from rdf file
    graph.add_node(node5, node_type="Relationship")

    # Test fhir ontology
    graph.add_node(node2, node_type="Organization")

    # Add node without ontology
    graph.add_node(node3)

    graph.add_nodes([node1, node4], node_types=["Organization", "CarePlan"])
