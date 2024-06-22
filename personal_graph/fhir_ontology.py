import json
import logging
from fhir.resources import construct_fhir_element
from pydantic_core import ValidationError

from personal_graph.onto_graph import OntoGraph


class FhirOntoGraph(OntoGraph):
    """
    This is a derived class that incorporates FHIR ontology.
    This class will override certain methods of OntoGraph Class to utilize FHIR resources.
    """

    def validate_fhir_resource(self, resource_data):
        """Validate if the provided data conforms to a FHIR resource schema."""
        try:
            # Dynamically create a FHIR resource instance to validate data
            resource_type = resource_data.get("resourceType")

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

        if node_type and self.validate_fhir_resource(attributes):
            # TODO: add node and create relation between node and node type(resourceType) of "instance_of"
            logging.info("Validated!!")
        else:
            raise ValueError("Invalid FHIR resource data.")
