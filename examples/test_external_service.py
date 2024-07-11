from personal_graph import Node
from personal_graph.database.fhirservice.fhirservice import FhirService

fhir_service = FhirService(url="http://127.0.0.1:9008/resource")

# Connect to the FHIR server
db_url = "libsql://db-919113317500-technoculture.turso.io"

# Create a patient
patient_data = {
    "resourceType": "Patient",
    "id": "2290",
    "name": [{"family": "Doe", "given": ["John"]}],
    "gender": "male",
    "birthDate": "1970-01-01",
}
patient_id = fhir_service.add_node("Patient", patient_data, db_url)
print(f"Created patient with ID: {patient_id}")

# Search patient
patient = fhir_service.search_node("2290", db_url, "Patient")
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
fhir_service.update_node(node, db_url)

# Remove a patient
fhir_service.remove_node("2290", db_url, "Patient")

fhir_service.disconnect()
