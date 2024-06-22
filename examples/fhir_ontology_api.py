from personal_graph.models import Node
from personal_graph.fhir_ontology import FhirOntoGraph


with FhirOntoGraph(ontologies=None) as db:
    try:
        node1 = Node(
            id="1",
            label="Pabelo",
            attributes={
                "resourceType": "Organization",
                "active": "False",
                "name": "John Doe",
                "id": "xyz",
            },
        )
        db.add_node(
            node1, node_type="Organization", delete_if_properties_not_match=True
        )
    except ValueError as e:
        print(f"Error adding node: {e}")
