import logging
import os
import pkgutil

from pydantic_core import ValidationError
import inspect
from importlib import import_module
from typing import get_origin, get_args

from personal_graph.models import Node

try:
    import fhir.resources as fhir  # type: ignore
except ImportError:
    logging.info("fhir module is not available.")


def validate_fhir_resource(resource_type, resource_data):
    """Validate if the provided data conforms to a FHIR resource schema."""
    try:
        if resource_type:
            # Resource data must be a json_dict
            fhir.construct_fhir_element(resource_type, resource_data)
            return True

    except ValidationError as e:
        logging.info(f"Validation error: {e}")

    except Exception as e:
        logging.info(f"Error creating resource: {e}")

    return False


def extract_classes_properties():
    """
    This method will fetch all the classes along with their properties and saves it in a dictionary
    @return: class_info: Dict
    """
    pkgpath = os.path.dirname(fhir.__file__)

    class_info = {}
    for _, module_name, is_dir in pkgutil.iter_modules([pkgpath]):
        if not is_dir:
            try:
                module = import_module(f"fhir.resources.{module_name}")
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and not obj.__module__.startswith(
                        "pydantic"
                    ):
                        class_properties = (
                            {k: v for k, v in obj.__annotations__.items()}
                            if hasattr(obj, "__annotations__")
                            else {}
                        )
                        class_info[name] = class_properties

            except ModuleNotFoundError:
                pass

    return class_info


def get_type_name(prop_type):
    """
    Helper function to get the name of the type, handling List types
    """
    if get_origin(prop_type) is list:
        return get_args(prop_type)[0].__name__
    return prop_type.__name__


def fhir_node(fhir_data) -> Node:
    """
    Helper function that will convert fhir data to Node Type
    @param fhir_data: Dict
    @return: Node
    """

    return Node(
        id=fhir_data.id,
        attributes=fhir_data.__dict__,
        label=type(fhir_data).__name__,
    )
