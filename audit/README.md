# Public audit controls

- `PUBLIC_RELEASE_FREEZE_V2.json` records the final study window, cardinalities, source-authority hashes, and redistribution boundary.
- `COMBINED_ANALYSIS_SUMMARY_V5.json` is the path-free summary emitted by the authoritative V5 run02 analysis.
- `SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5.*` maps every tabular or figure claim to its analysis source and denominator.
- The root `RELEASE_MANIFEST.json` and `SHA256SUMS.csv` replace the internal path-bearing production manifest for public distribution.

The internal production manifest is intentionally not published because it contains machine-local paths and bindings to nonredistributable provider inputs.
