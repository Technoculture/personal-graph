from personal_graph.models import Node
from personal_graph.onto_graph import OntoGraph
from personal_graph.ontology import from_rdf

ontologies = from_rdf("/path/to/rdffile")

with OntoGraph(ontologies=[ontologies]) as graph_db:
    try:
        node = Node(id="1", label="Pabelo", attributes={"age": 30})
        graph_db.add_node(node, "device")
        graph_db.visualize("sample.dot", ["1"])
    except ValueError as e:
        print(f"Error adding node: {e}")
