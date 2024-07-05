"""
This script creates a .pkl file of all the classes along with their properties that fhir ontology has.
"""

import logging
import pickle
from personal_graph.helper import extract_classes_properties

# Dumping the fhir ontology's classes and properties
node_types_info = extract_classes_properties()
file = open("ontology_classes_and_properties.pkl", "wb")
pickled_data = pickle.dumps(node_types_info)
file.write(pickled_data)
file.close()


# Loading up the classes and properties of fhir ontology
with open("ontology_classes_and_properties.pkl", "rb") as pickle_file:
    loaded_data = pickle.load(pickle_file)

# loaded data (loaded_data)
logging.info(loaded_data)
