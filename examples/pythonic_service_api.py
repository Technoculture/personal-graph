import logging
import argparse
import fhir.resources as fhir
from personal_graph import GraphDB, Node
from personal_graph.database.fhirservice.fhirservice import FhirService


def main(args):
    with GraphDB(service=FhirService(url=args.base_url), ontologies=[fhir]) as graph:
        # Add a node
        patient_data = {
            "resourceType": "Patient",
            "id": "2290",
            "name": [{"family": "Doe", "given": ["John"]}],
            "gender": "male",
            "birthDate": "1970-01-01",
        }
        node = Node(id="2290", label="Patient", attributes=patient_data)
        graph.add_node(node, db_url=args.db_url)

        # Search a node
        patient = graph.search_node("2290", db_url=args.db_url, resource_type="Patient")
        logging.info(patient)

        # Update a node
        updated_data = {
            "resourceType": "Patient",
            "id": "2290",
            "name": [{"family": "Kale", "given": ["Shimron"]}],
            "gender": "female",
            "birthDate": "1967-01-05",
        }
        updated_node = Node(id="2290", label="Patient", attributes=updated_data)
        graph.update_node(updated_node, db_url=args.db_url)

        # Remove a node
        graph.remove_node("2290", db_url=args.db_url, resource_type="Patient")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/pythonic_api.log",
    )

    parser = argparse.ArgumentParser(
        description="Shows simple example of high level apis."
    )

    parser.add_argument("--base-url", default="localhost", type=str)
    parser.add_argument("--db-url", type=str)

    arguments = parser.parse_args()
    main(arguments)
