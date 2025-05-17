# Minimal stub resources package
from . import fhirtypes

VALID_RESOURCES = {"CarePlan", "Organization"}

def construct_fhir_element(resource_type, resource_data):
    return {"resource_type": resource_type, **resource_data}
