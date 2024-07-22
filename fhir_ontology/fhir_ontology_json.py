"""
This method will create a json file with all the nodes and edges that the fhir ontology has.
"""

import json
import os
import pickle
import logging
from personal_graph.helper import extract_classes_properties, get_type_name


def create_fhir_ontology_json(json_filename, pickle_filename):
    try:
        # Check if the pickle file exists
        if os.path.exists(pickle_filename):
            logging.info("Loading FHIR node data from pickle file...")
            with open(pickle_filename, "rb") as f:
                node_types_info = pickle.load(f)
        else:
            node_types_info = extract_classes_properties()

        ontology_data = {"nodes": [], "edges": []}

        # Add all node_types
        for node_type in node_types_info.keys():
            ontology_data["nodes"].append({"id": node_type, "label": node_type})

        # Create edges between node_types with other related node_types
        for node_type, properties in node_types_info.items():
            for prop, prop_type in properties.items():
                type_name = get_type_name(prop_type)
                if type_name in node_types_info.keys():
                    # This property is a FHIR resource type, create an edge of 'instance_of'
                    ontology_data["edges"].append(
                        {"source": node_type, "target": type_name, "label": prop}
                    )

        # Save the ontology data as JSON
        with open(json_filename, "w") as f:
            json.dump(ontology_data, f, indent=2)

        logging.info(f"FHIR ontology data saved to {json_filename}")
        return json_filename

    except Exception as e:
        logging.info(f"An error occurred: {e}")
        raise e
