import json
import uuid
from typing import Optional, List

from personal_graph import GraphDB, Node


class OntoGraph(GraphDB):
    def __init__(self, ontologies):
        super().__init__()
        self.ontologies = ontologies

    def add_node(
        self,
        node: Node,
        *,
        node_type: Optional[str] = None,
        delete_if_properties_not_match: Optional[bool] = False,
    ) -> None:
        node_properties = (
            list(node.attributes.keys())
            if isinstance(node.attributes, dict)
            else list(json.loads(node.attributes).keys())
        )
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

            # Fetch ontology properties of the particular node type
            node_type_properties = []
            fetch_properties = False
            for ontology in self.ontologies:
                if not fetch_properties:
                    for cls in ontology.classes():
                        if node_type in cls.name and node_type != cls.name:
                            node_type_properties.append(cls.label[0])
                            fetch_properties = True

                if sorted(node_type_properties) == sorted(node_properties):
                    # Create instance_of edge if properties matches with the attribute
                    node_id = str(uuid.uuid4())

                    # Check if node type not exists, then add a node_type
                    if not self.db.search_node(node_id):
                        self.db.add_node(node_type, {}, node_id)  # type: ignore
                        self.vector_store.add_node_embedding(node_id, node_type, {})  # type: ignore

                    # Establish an instance_of relation between node and node_type
                    self.db.add_edge(
                        source=node.id,
                        target=node_id,
                        label="instance_of",
                        attributes=node.attributes
                        if isinstance(node.attributes, dict)
                        else json.loads(node.attributes),
                    )

                    self.vector_store.add_edge_embedding(
                        source=node.id,
                        target=node_id,
                        label="instance_of",
                        attributes=node.attributes
                        if isinstance(node.attributes, dict)
                        else json.loads(node.attributes),
                    )
                else:
                    # Delete the node if node attributes do not match with node_type properties
                    if delete_if_properties_not_match:
                        self.db.remove_node(node.id)
                    else:
                        raise ValueError(
                            "Properties do not match with the node attributes."
                        )

    def add_nodes(
        self,
        nodes: List[Node],
        *,
        node_types: List[str],
        delete_if_properties_not_match: List[bool],
    ) -> None:
        if len(nodes) != len(node_types) != len(delete_if_properties_not_match):
            raise ValueError("The lengths of the input lists must be equal.")

        for node, node_type, delete_flag in zip(
            nodes, node_types, delete_if_properties_not_match
        ):
            self.add_node(
                node, node_type=node_type, delete_if_properties_not_match=delete_flag
            )
