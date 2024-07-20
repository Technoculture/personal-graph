import os
import fhir.resources as fhir

from personal_graph import Node, GraphDB, EdgeInput
from personal_graph.database import FhirDB, TursoDB
from personal_graph.vector_store.sqlitevss.fhirsqlitevss import FhirSQLiteVSS

vs = FhirSQLiteVSS(
    db=TursoDB(
        url=os.getenv("DB_URL"),
        auth_token=os.getenv("TURSO_PATIENTS_GROUP_AUTH_TOKEN_2"),
    ),
    index_dimension=384,
)

FhirGraphDB = GraphDB(
    vector_store=vs,
    database=FhirDB(db_url=os.getenv("DB_URL", "")),
    ontologies=[fhir],
)

patient_data = {
    "resourceType": "Patient",
    "id": "2291",
    "name": [{"family": "Doe", "given": ["John"]}],
    "gender": "male",
    "birthDate": "1970-01-01",
}
pd_2 = {
    "resourceType": "Patient",
    "id": "2290",
    "name": [{"family": "Jimmy", "given": ["Room"]}],
    "gender": "male",
    "birthDate": "1999-10-02",
}
pd_3 = {
    "resourceType": "Patient",
    "id": "2291",
    "name": [{"family": "Jimmy", "given": ["Room"]}],
    "gender": "female",
    "birthDate": "2000-10-02",
}

node1 = Node(id="2290", label="patient", attributes=pd_2)
node2 = Node(id="2291", label="patient", attributes=pd_3)
node3 = Node(id="2291", label="patient", attributes=patient_data)

# Adding nodes
FhirGraphDB.add_node(node1, node_type="Patient")
FhirGraphDB.add_node(node2, node_type="Patient")

FhirGraphDB.add_nodes([node1, node2])

# Searching a node
print(FhirGraphDB.search_node(2290, node_type="Patient"))

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
FhirGraphDB.update_node(node1)
FhirGraphDB.update_nodes([node1, node2])

# Remove nodes
FhirGraphDB.remove_node(2290, node_type="Patient")
FhirGraphDB.remove_nodes([2290, 2291], node_types=["patient", "PaTient"])

# Fetch ids from db
print(FhirGraphDB.fetch_ids_from_db(node_type="patient"))
