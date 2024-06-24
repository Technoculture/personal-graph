import json
import logging
import uuid
from typing import List, Optional, Dict

from fhir.resources import construct_fhir_element
from pydantic_core import ValidationError

from personal_graph import Node
from personal_graph.graph import GraphDB


class FhirOntoGraph(GraphDB):
    """
    This is a derived class that incorporates FHIR ontology.
    This class will override certain methods of OntoGraph Class to utilize FHIR resources.
    """

    def validate_fhir_resource(self, resource_type, resource_data):
        """Validate if the provided data conforms to a FHIR resource schema."""
        try:
            if resource_type:
                # Resource data must be a json_dict
                construct_fhir_element(resource_type, resource_data)
                return True

        except ValidationError as e:
            logging.info(f"Validation error: {e}")

        except Exception as e:
            logging.info(f"Error creating resource: {e}")

        return False

    def add_node(self, node, *, node_type=None, delete_if_properties_not_match=False):
        """Override add_node to incorporate FHIR resource validation."""

        if isinstance(node.attributes, str):
            attributes = json.loads(node.attributes)
        else:
            attributes = node.attributes

        if node_type and self.validate_fhir_resource(node_type, attributes):
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
                node_id = str(uuid.uuid4())

                # Check if node type not exists, then add a node_type
                if not self.db.search_node_type(node_type):
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
        else:
            raise ValueError("Invalid FHIR resource data.")

    def add_nodes(
        self,
        nodes: List[Node],
        *,
        node_types: Optional[List[str]] = None,
        delete_if_properties_not_match: Optional[List[bool]] = None,
    ) -> None:
        if len(nodes) != len(node_types):
            raise ValueError("The lengths of the input lists must be equal.")

        if delete_if_properties_not_match is None:
            delete_if_properties_not_match = [False] * len(nodes)

        elif len(delete_if_properties_not_match) != len(nodes):
            raise ValueError(
                "The length of delete_if_properties_not_match must match the length of nodes if provided."
            )

        for node, node_type, delete_flag in zip(
            nodes, node_types, delete_if_properties_not_match
        ):
            self.add_node(
                node, node_type=node_type, delete_if_properties_not_match=delete_flag
            )

    def insert(
        self,
        text: str,
        attributes: Dict,
        *,
        node_type: Optional[str] = None,
        delete_if_properties_not_match: Optional[bool] = False,
    ) -> None:
        node = Node(
            id=str(uuid.uuid4()),
            label=text,
            attributes=json.dumps(attributes),
        )

        self.add_node(
            node,
            node_type=node_type,
            delete_if_properties_not_match=delete_if_properties_not_match,
        )
