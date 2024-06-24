from fhir.resources import fhirtypes
from personal_graph.models import Node
from personal_graph.fhir_ontology import FhirOntoGraph


with FhirOntoGraph() as db:
    try:
        node2 = Node(
            id="2",
            label="xyz",
            attributes={
                "category": [fhirtypes.CodeableConceptType(text="asthma")],
                "identifier": [
                    fhirtypes.IdentifierType(value="1")
                ],
                "intent": "proposal",
                "status": "active",
                "subject": fhirtypes.ReferenceType(reference="Patient/123")
            },
        )
        db.add_node(
            node2, node_type="CarePlan", delete_if_properties_not_match=True
        )
    except ValueError as e:
        print(f"Error adding node: {e}")
