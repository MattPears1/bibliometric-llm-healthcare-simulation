# Code

verify_public_release.py is the portable offline checker for v3.0.0; test_verify_public_release.py contains its regression tests.

The remaining scripts preserve the collection, review, version consolidation, n483 reconciliation, analysis and model-audit chronology. V5_ANALYSIS_CODE/combined_analysis_engine_v5.py depends on fresh_analysis_engine_v2.py in this directory, which is included. Historical production tests are retained with their engines.

Historical code requires controlled input files and is not executed by the public checker. It may encode earlier stage counts or model identities. The corrected public dataset and model-family outputs are the current analytical authority. Do not execute collection scripts merely to check a download: external results can change and may require separately configured service access.

See ../docs/REPRODUCIBILITY.md for scope, dependencies and limitations.

model_audit/ contains the corrected model-inventory and figure scripts; figure_builders/ contains the fine-grained NTS source; human_audit/ contains the original sampling/finalization helpers. Absolute path constants in these copies were replaced by controlled-source basenames. Their private inputs must be supplied deliberately before execution. These source copies were syntax-checked but historical production tests and full analysis were not rerun for this publication update.
