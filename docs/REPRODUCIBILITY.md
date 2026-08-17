# Reproducibility guide

## 1. Verify the downloaded release

From the repository root, run:

```bash
python code/verify_public_release.py .
```

The command recomputes every SHA-256 digest listed in `SHA256SUMS.csv`, checks ledger coverage, and verifies the frozen study cardinalities.

## 2. Inspect the reader-facing analysis

- The 18 exact searches are in `online_resources/online_resource_1_search_strategy/`.
- Selection, model-review comparison, and publication-version files are in `online_resources/online_resource_2_selection_and_versions/`.
- Complete descriptive and sensitivity outputs are in `online_resources/online_resource_3_complete_results/`.
- Phrase definitions, indicators, co-occurrence data, and the conditional network are in `online_resources/online_resource_4_phrases/`.
- The checked 485-study dataset and dictionary are in `online_resources/online_resource_5_reduced_dataset/`.

Each principal table is stored as both CSV and JSON. PNG figures are supplied at approximately 600 dpi and have EPS companions.

## 3. Software environment

The public integrity validator uses only the Python standard library and supports Python 3.10 or later. The production analysis engine additionally requires the packages in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

## 4. Collection and integration code

- `code/collect_metadata_snapshot.py` contains the completed non-Scopus collection workflow.
- `code/collect_scopus_snapshot.py` contains the Scopus collector. It expects an API key in an environment variable and never embeds credentials in source code.
- `code/SCOPUS_INTEGRATION_CODE/` contains the corrected integration and regression tests.
- `code/V5_ANALYSIS_CODE/combined_analysis_engine_v5.py` is the final analysis engine.
- The V5 engine's local dependency modules are supplied in `code/`.

Do not run collection scripts merely to validate this release: live service results can change. The frozen outputs and hashes are the publication authority.

## 5. Full fail-closed production rerun

The V5 engine was designed to consume an authorized input package whose paths, row counts, schemas, byte counts, and SHA-256 digests match the input contract. A full rerun requires reconstructing that rights-permitted input layout and updating only the path resolution while retaining all locked hashes and semantic gates. The engine must stop if any input differs.

Because raw provider data are not redistributed, a public clone alone is intentionally insufficient to repeat network acquisition byte-for-byte. It is sufficient to validate the released files and audit the published analysis outputs.

## 6. Fixed analytical cautions

- The 2026 count covers 1 January through 13 August and is not annualized.
- Model families, simulation modalities, NTS domains, and specialties are multiple-response fields where noted.
- Model-stream agreement measures consistency, not accuracy against an independent human reference standard.
- Bibliometric patterns are descriptive and do not establish educational effectiveness.
