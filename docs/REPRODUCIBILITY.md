# Reproducibility

## Public checks

Use Python 3.10 or later:

    python -B code/verify_public_release.py .
    python -B -m unittest discover -s code -p test_verify_public_release.py

No credentials, network access or external Python packages are needed for these checks. The checker verifies file coverage, SHA-256 values, record counts, preferred-version joins, annual totals, current model-family totals, model-review disagreement counts, the two distinct sample overlaps and NTS comparison counts.

Each Online Resource also contains its own CONTENTS_SHA256.csv. The six ZIP archives contain their complete resource directory and the data licence. Resource 5 additionally includes the repository code and reproducibility guide. For the repository-wide checker, use the full repository download; an individual resource ZIP alone is not the complete repository.

## Production provenance

The frozen integration manifest has SHA-256 b64b01ae57aaca386cfdb07b08e322f515e75e3dc2b5ed0cff1701cae9028bea. The n483 analysis hash ledger has SHA-256 12d9923ef1c68c3fbc511f0ab0fa22da49f5256119a279cf8d8fea099372f6aa. These originals remain unchanged.

The V5 engine and its dependency fresh_analysis_engine_v2.py are supplied in code/. The later n483 reconciliation utility and model-audit/figure source scripts are retained as dated provenance. A full production rerun requires the hash-bound controlled inputs, including source text that cannot be included in a public release. No fresh search, external model call or production rerun was performed to prepare v3.0.0.

Historical scripts may contain earlier denominators, thresholds, stage names or figure numbering. They describe their original stages; they are not the authority for current labels. Public-path substitutions are recorded in audit/SOURCE_LINEAGE.csv. A path-redacted manifest preserves its original input hashes but is not a runnable input contract.

## Current analytical authority

Use Resource 5 CHECKED_STUDY_DATASET_N483.csv, especially model_families_current, model_identity_status and model_audit_description. Resource 3 contains the corrected model-family totals and the corrected 470-study exact-identifier sensitivity. The pre-audit model-family claims for the 464-study preprint/repository sensitivity have been removed because that cohort did not receive a separate model-name re-audit.

The claim-to-source register retains original production artifact labels and row hashes. These labels are provenance identifiers, not a list of files distributed in this repository. The register includes controlled-source claims and is not a claim that all source inputs are public.

The 2026 period ends on 13 August. Multiple-response fields can sum to more than 483. Agreement between model streams measures consistency. Later lead-author checks preserve initial and post-comparison stages and are reported separately from the frozen analysis.
