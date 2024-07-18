CREATE TABLE IF NOT EXISTS resource_status (status TEXT PRIMARY KEY );
INSERT OR IGNORE INTO resource_status (status) VALUES('created'),('updated'),('deleted'),('recreated');


CREATE TABLE IF NOT EXISTS "transaction"(
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource JSON
);

CREATE TABLE IF NOT EXISTS "devicerequest"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "devicerequest_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "servicerequest"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ServiceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);



CREATE TABLE IF NOT EXISTS "servicerequest_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ServiceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);



CREATE TABLE IF NOT EXISTS "devicemetric"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ServiceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);



CREATE TABLE IF NOT EXISTS "devicemetric_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ServiceRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);




CREATE TABLE IF NOT EXISTS "careplan"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CarePlan',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "careplan_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CarePlan',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "observation"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Observation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "observation_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Observation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "enrollmentrequest"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EnrollmentRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "enrollmentrequest_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EnrollmentRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "group"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Group',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "group_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Group',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "messagedefinition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MessageDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "messagedefinition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MessageDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "appointment"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Appointment',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "appointment_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Appointment',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "biologicallyderivedproduct"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'BiologicallyDerivedProduct',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "biologicallyderivedproduct_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'BiologicallyDerivedProduct',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "questionnaireresponse"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'QuestionnaireResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "questionnaireresponse_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'QuestionnaireResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "effectevidencesynthesis"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EffectEvidenceSynthesis',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "effectevidencesynthesis_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EffectEvidenceSynthesis',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "medicinalproductcontraindication"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductContraindication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);


CREATE TABLE IF NOT EXISTS "episodeofcare"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EpisodeOfCare',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "episodeofcare_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EpisodeOfCare',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "evidence"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Evidence',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "evidence_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Evidence',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "substancepolymer"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstancePolymer',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "substancepolymer_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstancePolymer',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);



CREATE TABLE IF NOT EXISTS "supplydelivery"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SupplyDelivery',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "supplydelivery_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SupplyDelivery',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "substancenucleicacid"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceNucleicAcid',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "substancenucleicacid_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceNucleicAcid',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "adverseevent"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AdverseEvent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "adverseevent_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AdverseEvent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS "endpoint"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Endpoint',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "endpoint_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Endpoint',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "substancereferenceinformation"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceReferenceInformation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "substancereferenceinformation_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceReferenceInformation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "substancesourcematerial"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceSourceMaterial',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "substancesourcematerial_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceSourceMaterial',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "compartmentdefinition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CompartmentDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "compartmentdefinition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CompartmentDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "detectedissue"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DetectedIssue',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "detectedissue_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DetectedIssue',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS "medicationadministration"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationAdministration',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "medicationadministration_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationAdministration',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "evidencevariable"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EvidenceVariable',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "evidencevariable_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EvidenceVariable',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "implementationguide"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImplementationGuide',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "implementationguide_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImplementationGuide',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "goal"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Goal',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "goal_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Goal',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS "communication"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Communication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "communication_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Communication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "schedule"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Schedule',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "schedule_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Schedule',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "documentreference"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DocumentReference',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "documentreference_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DocumentReference',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS "organizationaffiliation"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OrganizationAffiliation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "organizationaffiliation_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OrganizationAffiliation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "devicedefinition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "devicedefinition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "coverage"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Coverage',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "coverage_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Coverage',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "auditevent"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AuditEvent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "auditevent_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AuditEvent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS resource_status (
    status TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS "messageheader"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MessageHeader',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "messageheader_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MessageHeader',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "contract"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Contract',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "contract_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Contract',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "testreport"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'TestReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "testreport_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'TestReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "codesystem"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CodeSystem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "codesystem_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CodeSystem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "plandefinition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PlanDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "plandefinition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PlanDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "invoice"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Invoice',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "invoice_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Invoice',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "claimresponse"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ClaimResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "claimresponse_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ClaimResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "chargeitem"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ChargeItem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "chargeitem_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ChargeItem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "coverageeligibilityresponse"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CoverageEligibilityResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "coverageeligibilityresponse_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CoverageEligibilityResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "bodystructure"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'BodyStructure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "bodystructure_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'BodyStructure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "parameters"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Parameters',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "parameters_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Parameters',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "clinicalimpression"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ClinicalImpression',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "clinicalimpression_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ClinicalImpression',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);






CREATE TABLE IF NOT EXISTS "familymemberhistory"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'FamilyMemberHistory',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "familymemberhistory_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'FamilyMemberHistory',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "medicinalproductauthorization"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductAuthorization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "medicinalproductauthorization_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductAuthorization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "binary"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Binary',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "binary_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Binary',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "composition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Composition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "composition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Composition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "practitionerrole"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PractitionerRole',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "practitionerrole_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PractitionerRole',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "healthcareservice"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'HealthcareService',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "healthcareservice_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'HealthcareService',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "patient"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Patient',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "patient_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Patient',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "medicationdispense"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationDispense',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "medicationdispense_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationDispense',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "deviceusestatement"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceUseStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);



CREATE TABLE IF NOT EXISTS "deviceusestatement_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DeviceUseStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "structuremap"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'StructureMap',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "structuremap_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'StructureMap',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "immunizationevaluation"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImmunizationEvaluation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "immunizationevaluation_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImmunizationEvaluation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "library"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Library',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "library_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Library',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "basic"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Basic',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "basic_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Basic',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "slot"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Slot',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "slot_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Slot',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "activitydefinition"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ActivityDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "activitydefinition_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ActivityDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS "medicinalproductinteraction"(
    embed_id TEXT NOT NULL UNIQUE,
    id  TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductInteraction',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS "medicinalproductinteraction_history"(
    id  TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductInteraction',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

 CREATE TABLE IF NOT EXISTS molecularsequence(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MolecularSequence',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS molecularsequence_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MolecularSequence',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS specimen(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Specimen',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS specimen_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Specimen',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS diagnosticreport(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DiagnosticReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS diagnosticreport_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DiagnosticReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS subscription(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Subscription',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS subscription_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Subscription',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS requestgroup(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RequestGroup',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS requestgroup_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RequestGroup',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS provenance(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Provenance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS provenance_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Provenance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproduct(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProduct',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproduct_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProduct',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS chargeitemdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ChargeItemDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);
CREATE TABLE IF NOT EXISTS chargeitemdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ChargeItemDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS chargeitemdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ChargeItemDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS practitioner(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Practitioner',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS practitioner_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Practitioner',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproductpackaged(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductPackaged',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductpackaged_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductPackaged',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS flag(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Flag',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS flag_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Flag',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS explanationofbenefit(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ExplanationOfBenefit',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS explanationofbenefit_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ExplanationOfBenefit',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS linkage(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Linkage',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS linkage_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Linkage',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS operationoutcome(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OperationOutcome',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS operationoutcome_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OperationOutcome',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproductpharmaceutical(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductPharmaceutical',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductpharmaceutical_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductPharmaceutical',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);



CREATE TABLE IF NOT EXISTS immunization(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Immunization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS immunization_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Immunization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicationknowledge(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationKnowledge',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicationknowledge_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationKnowledge',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS researchsubject(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchSubject',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS researchsubject_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchSubject',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproductindication(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductIndication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductindication_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductIndication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS paymentnotice(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PaymentNotice',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS paymentnotice_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PaymentNotice',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS namingsystem(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'NamingSystem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS namingsystem_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'NamingSystem',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicationstatement(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicationstatement_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS enrollmentresponse(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EnrollmentResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS enrollmentresponse_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EnrollmentResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS nutritionorder(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'NutritionOrder',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS nutritionorder_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'NutritionOrder',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS questionnaire(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Questionnaire',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS questionnaire_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Questionnaire',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS account(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Account',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS account_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Account',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS eventdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EventDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS eventdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'EventDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproductundesirableeffect(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductUndesirableEffect',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductundesirableeffect_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductUndesirableEffect',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS substancespecification(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceSpecification',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS substancespecification_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceSpecification',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS communicationrequest(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CommunicationRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS communicationrequest_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CommunicationRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS specimendefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SpecimenDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS specimendefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SpecimenDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS verificationresult(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'VerificationResult',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS verificationresult_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'VerificationResult',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS documentmanifest(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DocumentManifest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS documentmanifest_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'DocumentManifest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS task(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Task',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS task_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Task',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS riskevidencesynthesis(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RiskEvidenceSynthesis',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS riskevidencesynthesis_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RiskEvidenceSynthesis',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS valueset(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ValueSet',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS valueset_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ValueSet',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS claim(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Claim',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS claim_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Claim',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS insuranceplan(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'InsurancePlan',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS insuranceplan_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'InsurancePlan',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS examplescenario(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ExampleScenario',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS examplescenario_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ExampleScenario',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS researchstudy(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchStudy',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS researchstudy_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchStudy',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicationrequest(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicationrequest_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicationRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS measure(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Measure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS measure_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Measure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS list(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'List',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS list_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'List',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS encounter_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Encounter',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS capabilitystatement(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CapabilityStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS capabilitystatement_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CapabilityStatement',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS visionprescription(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'VisionPrescription',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS visionprescription_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'VisionPrescription',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS riskassessment(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RiskAssessment',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS riskassessment_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RiskAssessment',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS substanceprotein(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceProtein',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS substanceprotein_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SubstanceProtein',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS immunizationrecommendation(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImmunizationRecommendation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS immunizationrecommendation_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImmunizationRecommendation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS relatedperson(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RelatedPerson',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS relatedperson_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'RelatedPerson',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medication(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Medication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medication_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Medication',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS appointmentresponse(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AppointmentResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS appointmentresponse_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AppointmentResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS researchelementdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchElementDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS researchelementdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchElementDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);


CREATE TABLE IF NOT EXISTS substance(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Substance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS substance_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Substance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS paymentreconciliation(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PaymentReconciliation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS paymentreconciliation_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'PaymentReconciliation',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS conceptmap(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ConceptMap',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS conceptmap_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ConceptMap',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS person(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Person',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS person_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Person',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS condition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Condition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS condition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Condition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS careteam(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CareTeam',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS careteam_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CareTeam',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS catalogentry(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CatalogEntry',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS catalogentry_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CatalogEntry',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    PRIMARY KEY (id, txid),
    FOREIGN KEY (status) REFERENCES resource_status(status)
);


CREATE TABLE IF NOT EXISTS structuredefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'StructureDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS structuredefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'StructureDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS procedure(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Procedure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS procedure_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Procedure',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS consent(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Consent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS consent_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Consent',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS observationdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ObservationDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS observationdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ObservationDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS attribute(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Attribute',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS attribute_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Attribute',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS location(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Location',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS location_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Location',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS organization(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Organization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS organization_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Organization',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS device(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Device',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);



CREATE TABLE IF NOT EXISTS device_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Device',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS supplyrequest(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SupplyRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS supplyrequest_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'SupplyRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS allergyintolerance(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AllergyIntolerance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS allergyintolerance_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'AllergyIntolerance',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS researchdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS researchdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ResearchDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS operationdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OperationDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS operationdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'OperationDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS medicinalproductmanufactured(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductManufactured',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductmanufactured_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductManufactured',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS imagingstudy(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImagingStudy',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS imagingstudy_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'ImagingStudy',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS coverageeligibilityrequest(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CoverageEligibilityRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS coverageeligibilityrequest_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'CoverageEligibilityRequest',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);




CREATE TABLE IF NOT EXISTS medicinalproductingredient(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductIngredient',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS medicinalproductingredient_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MedicinalProductIngredient',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS guidanceresponse(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'GuidanceResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS guidanceresponse_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'GuidanceResponse',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS media(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Media',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS media_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'Media',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS measurereport(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MeasureReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS measurereport_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MeasureReport',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS graphdefinition(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'GraphDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS graphdefinition_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'GraphDefinition',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS terminologycapabilities(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'TerminologyCapabilities',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS terminologycapabilities_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'TerminologyCapabilities',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS metadataresource(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MetadataResource',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status)
);

CREATE TABLE IF NOT EXISTS metadataresource_history(
    id TEXT,
    txid INTEGER NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    resource_type TEXT DEFAULT 'MetadataResource',
    status TEXT NOT NULL,
    resource JSON NOT NULL,
    FOREIGN KEY (status) REFERENCES resource_status(status),
    PRIMARY KEY (id, txid)
);

CREATE TABLE IF NOT EXISTS relations(
    embed_id TEXT NOT NULL UNIQUE,
    id TEXT,
    source_id  TEXT,
    source_type TEXT,
    target_id  TEXT UNIQUE,
    target_type TEXT,
    relation TEXT,
    resource JSON NOT NULL,
    UNIQUE(source_id, source_type, target_id, target_type, resource) ON CONFLICT REPLACE
);
