begin;

CREATE VIRTUAL TABLE IF NOT EXISTS devicerequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS servicerequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS devicemetric_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS careplan_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS observation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS enrollmentrequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS group_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS messagedefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS appointment_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS biologicallyderivedproduct_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS questionnaireresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS effectevidencesynthesis_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductcontraindication_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS episodeofcare_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS evidence_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substancepolymer_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS supplydelivery_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substancenucleicacid_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS adverseevent_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS endpoint_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substancereferenceinformation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substancesourcematerial_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS compartmentdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS detectedissue_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicationadministration_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS evidencevariable_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS implementationguide_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS goal_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS communication_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS schedule_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS documentreference_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS organizationaffiliation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS devicedefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS coverage_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS auditevent_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS messageheader_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS contract_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS testreport_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS codesystem_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS plandefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS invoice_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS claimresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS chargeitem_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS coverageeligibilityresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS bodystructure_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS parameters_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS clinicalimpression_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS familymemberhistory_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductauthorization_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS binary_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS composition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS practitionerrole_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS healthcareservice_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS patient_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicationdispense_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS deviceusestatement_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS structuremap_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS immunizationevaluation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS library_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS basic_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS slot_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS activitydefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductinteraction_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS molecularsequence_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS specimen_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS diagnosticreport_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS subscription_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS requestgroup_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS provenance_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproduct_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS chargeitemdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS practitioner_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductpackaged_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS flag_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS explanationofbenefit_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS linkage_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS operationoutcome_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductpharmaceutical_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS immunization_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicationknowledge_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS researchsubject_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductindication_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS paymentnotice_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS namingsystem_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicationstatement_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS enrollmentresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS nutritionorder_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS questionnaire_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS account_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS eventdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductundesirableeffect_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substancespecification_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS communicationrequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS specimendefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS verificationresult_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS documentmanifest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS task_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS riskevidencesynthesis_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS valueset_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS claim_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS insuranceplan_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS examplescenario_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS researchstudy_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicationrequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS measure_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS list_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS capabilitystatement_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS visionprescription_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS riskassessment_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substanceprotein_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS immunizationrecommendation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS relatedperson_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medication_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS appointmentresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS researchelementdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS substance_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS paymentreconciliation_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS conceptmap_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS person_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS condition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS careteam_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS catalogentry_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS structuredefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS procedure_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS consent_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS observationdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS attribute_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS location_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS organization_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS device_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS supplyrequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS allergyintolerance_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS researchdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS operationdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductmanufactured_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS imagingstudy_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS coverageeligibilityrequest_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS medicinalproductingredient_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS guidanceresponse_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS media_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS measurereport_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS graphdefinition_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS terminologycapabilities_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS metadataresource_embedding USING vss0(
    vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS relations_embedding USING vss0(
    vector_relations({{size}})
);

commit;