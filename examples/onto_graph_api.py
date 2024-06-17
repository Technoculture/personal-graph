from personal_graph.models import Node
from personal_graph.onto_graph import OntoGraph
from personal_graph.ontology import from_rdf

ontologies = from_rdf("/path/to/rdffile")

with OntoGraph(ontologies=[ontologies]) as db:
    try:
        node = Node(
            id="1",
            label="Pabelo",
            attributes={
                "entity": "sample entity",
                "group": "management",
                "medication": "instant",
                "individual": "personality",
            },
        )
        db.add_node(node, node_type="administrative", delete_if_properties_not_match=True)
        db.visualize("sample.dot", ["1"])
    except ValueError as e:
        print(f"Error adding node: {e}")
