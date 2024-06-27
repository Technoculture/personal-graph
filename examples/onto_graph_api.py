from personal_graph.models import Node
from personal_graph.graph import GraphDB
from personal_graph.ontology import from_rdf

ontologies1 = from_rdf("/path/to/ontology1")
ontologies2 = from_rdf("/path/to/ontology2")


with GraphDB(ontologies=[ontologies1, ontologies2]) as db:
    try:
        node1 = Node(
            id="1",
            label="Pabelo",
            attributes={
                "entity": "sample entity",
                "group": "management",
                "medication": "instant",
                "individual": "personality",
            },
        )
        node2 = Node(
            id="2",
            label="Praful",
            attributes={
                "careprovision": "sample provision",
                "diagnostics": "CT scan",
                "general": "ward",
                "medication": "long time",
            },
        )
        db.add_node(
            node1, node_type="administrative", delete_if_properties_not_match=True
        )
        db.add_nodes(
            [node1, node2],
            node_types=["administrative", "clinical"],
            delete_if_properties_not_match=[True, False],
        )
        db.insert(
            text="User mentioned their favorite hobbies and weekend activities.",
            attributes={
                "careprovision": "sample provision",
                "diagnostics": "CT scan",
                "general": "ward",
                "medication": "long time",
            },
            node_type="clinical",
            delete_if_properties_not_match=True,
        )
    except ValueError as e:
        print(f"Error adding node: {e}")
