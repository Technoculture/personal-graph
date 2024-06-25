import fhir.resources as fhir
from fhir.resources import fhirtypes
from personal_graph import GraphDB, Node


with GraphDB(ontologies=[fhir]) as graph:
    # Define nodes
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
    graph.add_nodes([node1, node2], node_types=["Organization", "CarePlan"])

    text = "User is claustrophobic."
    attributes = {
        "category": [fhirtypes.CodeableConceptType(text="asthma")],
        "identifier": [fhirtypes.IdentifierType(value="1")],
        "intent": "proposal",
        "status": "active",
        "subject": fhirtypes.ReferenceType(reference="Patient/123"),
    }
    graph.insert(text, attributes, node_type="CarePlan")
