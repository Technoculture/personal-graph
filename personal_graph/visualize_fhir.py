import os
import pkgutil
import uuid
from typing import get_origin, get_args

import fhir.resources
import inspect
from importlib import import_module
from personal_graph import GraphDB, EdgeInput, Node
from personal_graph.database import TursoDB
from personal_graph.ml import pg_to_networkx
from personal_graph.vector_store import SQLiteVSS


def extract_classes_properties():
    """
    This method will fetch all the classes along with their properties and saves it in a dictionary
    @return: class_info: Dict
    """
    pkgpath = os.path.dirname(fhir.resources.__file__)

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


db = TursoDB(url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN"))
vs = SQLiteVSS(db=db, index_dimension=384)

with GraphDB(database=db, vector_store=vs, ontologies=[fhir]) as graph:
    node_types_info = extract_classes_properties()
    node_uuids = {}  # To store UUIDs for each node type

    # Add all node_types
    for node_type in node_types_info.keys():
        node_uuid = str(uuid.uuid4())
        graph.add_node_type(node_uuid, node_type=node_type)
        node_uuids[node_type] = node_uuid

    # Create edges between node_types with other related node_types
    for node_type, properties in node_types_info.items():
        for prop, prop_type in properties.items():
            type_name = get_type_name(prop_type)
            if type_name in node_types_info.keys():
                # This property is a FHIR resource type, create an edge of 'instance_of'
                target_id = graph.find_node_type_id(type_name)

                # Create an edge between node type and it's related node_type
                source = Node(id=node_uuids[node_type], label=node_type, attributes={})
                target = Node(id=target_id, label=type_name, attributes={})
                edge = EdgeInput(
                    source=source, target=target, label="instance_of", attributes={}
                )
                graph.add_edge(edge)

    # Visualize the personal graph
    nx_graph = pg_to_networkx(graph, post_visualize=True)
