import argparse
import logging
import os
import fhir.resources as fhir
from fhir.resources.patient import Patient

from personal_graph import GraphDB, EdgeInput
from personal_graph.database import FhirDB, TursoDB
from personal_graph.helper import fhir_node
from personal_graph.vector_store.sqlitevss.fhirsqlitevss import FhirSQLiteVSS


def main(args):
    vs = FhirSQLiteVSS(
        db=TursoDB(url=args.db_url, auth_token=args.auth_token),
        index_dimension=384,
    )

    FhirGraphDB = GraphDB(
        vector_store=vs,
        database=FhirDB(db_url=args.db_url),
        ontologies=[fhir],
    )

    pd_1 = {
        "resourceType": "Patient",
        "id": "2291",
        "name": [{"family": "Jimmy", "given": ["Room"]}],
        "gender": "female",
        "birthDate": "2000-10-02",
    }
    pd_2 = {
        "resourceType": "Patient",
        "id": "2291",
        "name": [{"family": "Doe", "given": ["John"]}],
        "gender": "male",
        "birthDate": "1970-01-01",
    }

    # Convert to node type object
    node1 = fhir_node(Patient(**pd_1))
    node2 = fhir_node(Patient(**pd_2))

    FhirGraphDB.add_node(node1)

    # Searching a node
    logging.info(FhirGraphDB.search_node(2290, node_type="Patient"))

    # Adding edges
    edge1 = EdgeInput(
        source=node1, target=node2, label="knows", attributes={"since": "2012"}
    )
    edge2 = EdgeInput(
        source=node2, target=node1, label="knows", attributes={"since": "2012"}
    )
    FhirGraphDB.add_edge(edge1)
    FhirGraphDB.add_edges([edge1, edge2])

    # Updating nodes
    FhirGraphDB.update_node(node2)

    # Remove nodes
    FhirGraphDB.remove_node(2290, node_type="Patient")
    FhirGraphDB.remove_nodes([2290, 2291], node_types=["patient", "Patient"])

    # Fetch ids from db
    logging.info(FhirGraphDB.fetch_ids_from_db(node_type="patient"))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/fhirgraphdb.log",
    )

    parser = argparse.ArgumentParser(
        description="Shows simple example of high level apis."
    )

    parser.add_argument("--db-url", default=os.getenv("DB_URL", ""), type=str)
    parser.add_argument(
        "--auth-token",
        default=os.getenv("TURSO_PATIENTS_GROUP_AUTH_TOKEN", 0),
        type=str,
    )

    arguments = parser.parse_args()
    main(arguments)
