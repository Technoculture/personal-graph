from personal_graph import Node
from personal_graph.database.fhirservice.fhirservice import FhirService

fhir_ontologies = ["Patient", "Observation", "Encounter", "Practitioner"]
fhir_service = FhirService(ontologies=fhir_ontologies)

# Connect to the FHIR server
fhir_service.connect("http://localhost/resource")
db_url = "libsql://db-919113317500-technoculture.turso.io"

# Create a patient
patient_data = {
    "resourceType": "Patient",
    "id": "2290",
    "name": [{"family": "Doe", "given": ["John"]}],
    "gender": "male",
    "birthDate": "1970-01-01",
}
patient_id = fhir_service.add_node(db_url, "Patient", patient_data)
print(f"Created patient with ID: {patient_id}")

# Search patient
patient = fhir_service.search_node(db_url, "2290", "Patient")
print(patient)

# Update patient data
updated_patient_data = {
    "resourceType": "Patient",
    "id": "2290",
    "name": [{"family": "US", "given": ["Person"]}],
    "gender": "female",
    "birthDate": "1970-01-01",
}
node = Node(id="2290", label="Patient", attributes=updated_patient_data)
fhir_service.update_node(db_url, node)

# Remove a patient
fhir_service.remove_node(db_url, "2290", "Patient")

fhir_service.disconnect()
