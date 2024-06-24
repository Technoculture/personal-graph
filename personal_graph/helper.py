import logging
from pydantic_core import ValidationError

try:
    from fhir.resources import construct_fhir_element
except ImportError:
    logging.info("fhir.resources module is not available.")


def validate_fhir_resource(resource_type, resource_data):
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
