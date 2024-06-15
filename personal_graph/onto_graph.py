import json
from typing import Optional

from personal_graph import GraphDB, Node


class OntoGraph(GraphDB):
    def __init__(self, ontologies):
        super().__init__()
        self.ontologies = ontologies

    def add_node(self, node: Node, node_type: Optional[str] = None) -> None:
        if self.ontologies is not None:
            if node_type is not None:
                # Check if the node type matches a concept in the ontology
                concept = None
                for ontology in self.ontologies:
                    concept = ontology.search_one(label=node_type)
                    if concept is not None:
                        break

                if concept is None:
                    raise ValueError(
                        f"Node concept '{node_type}' is not a valid concept in the ontology."
                    )

            else:
                raise ValueError("Node type not provided.")

        if self.db.search_node(node_id=node.id) is None:
            self.db.add_node(
                node.label,
                json.loads(node.attributes)
                if isinstance(node.attributes, str)
                else node.attributes,
                node.id,
            )

            self.vector_store.add_node_embedding(
                node.id,
                node.label,
                json.loads(node.attributes)
                if isinstance(node.attributes, str)
                else node.attributes,
            )

            # TODO: Create an edge with an ontology node type
