import json
import os
import uuid
from pathlib import Path
from typing import Dict

from personal_graph import Node, EdgeInput, GraphDB
from personal_graph.database import TursoDB
from personal_graph.ml import pg_to_networkx
from personal_graph.vector_store import SQLiteVSS
from personal_graph.visualize_fhir import get_type_name


def insert_from_fhir_json_bundle(bundle_file: Path, nodes_type_info: Dict) -> None:
    with open(bundle_file, "r") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        raise ValueError("The provided JSON file is not a FHIR Bundle")

    db = TursoDB(url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN"))
    vs = SQLiteVSS(db=db, index_dimension=384)

    with GraphDB(database=db, vector_store=vs) as graph:
        # Add Bundle node
        bundle_resourceType = bundle.get("resourceType")
        bundle_id = str(uuid.uuid4())
        graph.add_node_type(bundle_id, bundle_resourceType)

        for bundle_prop in bundle.keys():
            try:
                bundle_type = get_type_name(
                    nodes_type_info[bundle_resourceType][bundle_prop]
                )
            except KeyError:
                continue

            if bundle_type in nodes_type_info.keys():
                target_id = str(uuid.uuid4())
                graph.add_node_type(target_id, bundle_type)

                # Create an edge between node type and it's related node_type
                source = Node(id=bundle_id, label=bundle_resourceType, attributes={})
                target = Node(id=target_id, label=bundle_type, attributes={})
                edge = EdgeInput(
                    source=source, target=target, label=bundle_prop, attributes={}
                )
                graph.add_edge(edge)

        for entry in bundle.get("entry", []):
            resource = entry.get("resource")
            if resource:
                resource_type = resource.get("resourceType")
                if resource_type and resource_type in nodes_type_info.keys():
                    # Add the node to the graph
                    graph.add_node_type(
                        resource["id"], node_type=resource_type, attributes=resource
                    )

                    # Create edges
                    for prop in resource.keys():
                        try:
                            type_name = get_type_name(
                                nodes_type_info[resource_type][prop]
                            )
                        except KeyError:
                            continue

                        if type_name in nodes_type_info.keys():
                            # This property is a FHIR resource type, create an edge of 'instance_of'
                            target_id = str(uuid.uuid4())
                            graph.add_node_type(target_id, node_type=type_name)

                            # Create an edge between node type and it's related node_type
                            source = Node(
                                id=resource["id"], label=resource_type, attributes={}
                            )
                            target = Node(id=target_id, label=type_name, attributes={})
                            edge = EdgeInput(
                                source=source, target=target, label=prop, attributes={}
                            )
                            graph.add_edge(edge)

                            # Create an edge between bundle property and entry type
                            bundle_node = Node(
                                id=bundle_id, label=bundle_resourceType, attributes={}
                            )

                            edge = EdgeInput(
                                source=bundle_node,
                                target=source,
                                label="instance_of",
                                attributes={},
                            )
                            graph.add_edge(edge)

        pg_to_networkx(graph, post_visualize=True)
