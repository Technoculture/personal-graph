from fhir.resources import fhirtypes
from personal_graph.models import Node
from personal_graph.fhir_ontology import FhirOntoGraph


with FhirOntoGraph() as db:
    try:
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
        db.add_nodes([node1, node2], node_types=["Organization", "CarePlan"])

        text = "User is claustrophobic."
        attributes = {
            "category": [fhirtypes.CodeableConceptType(text="asthma")],
            "identifier": [fhirtypes.IdentifierType(value="1")],
            "intent": "proposal",
            "status": "active",
            "subject": fhirtypes.ReferenceType(reference="Patient/123"),
        }
        db.insert(text, attributes, node_type="CarePlan")
    except ValueError as e:
        print(f"Error adding node: {e}")
