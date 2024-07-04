from pathlib import Path

from personal_graph.visualize_fhir_bundle import insert_from_fhir_json_bundle
from personal_graph.visualize_fhir import extract_classes_properties

node_types_info = extract_classes_properties()
insert_from_fhir_json_bundle(
    Path("./sam.json"),
    node_types_info,
)
