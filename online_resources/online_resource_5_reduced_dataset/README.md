# Online Resource 5. Checked 483-study dataset, code and provenance

CHECKED_STUDY_DATASET_N483.csv has one preferred record per unique study. DATA_DICTIONARY_N483.csv describes its fields. MODEL_AUDIT_RECORDS_N483.csv contains the separate model-name audit.

The authoritative model fields are model_families_current, model_identity_status and model_audit_description. extraction_rationale supports broader simulation, NTS, specialty and study-design classification and can retain historical model wording; it does not override the separate model audit.

CLAIM_TO_SOURCE_REGISTER_CURRENT_N483.csv preserves production artifact labels and row hashes. They are provenance identifiers, not a contents list for this archive. The 24 pre-audit model claims for the 464-study sensitivity cohort were removed because that cohort was not separately re-audited. Current model-family outputs are in Resource 3.

The repository code/ directory contains the analysis engine, its restored fresh_analysis_engine_v2.py dependency, n483 reconciliation and other historical scripts. The Resource 5 download includes that code directory. The provenance folder contains path-redacted frozen manifests with original source hashes.

The public offline checker verifies the full repository without external packages. Historical production code requires controlled inputs and does not by itself regenerate every current table from this reduced CSV. Raw provider responses, abstracts, source keywords and full texts are excluded. See the reproducibility guide for the distinction between verifying published outputs and repeating acquisition/analysis.
