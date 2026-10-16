# Technical material

This folder holds the optional technical material outside the six reader ZIPs.

- [code](code/): original collection, screening, version consolidation, analysis, model-audit, figure and human-audit scripts, with their associated production tests.
- [methods](methods/): the analysis specification, identical reviewer protocol/prompts, and original Pilot protocol amendment. The operational eligibility codebook is in [Resource 2](../online_resources/Resource_2/Eligibility_and_selection.txt); the structured-extraction codebook is in [Resource 5](../online_resources/Resource_5/Data_dictionary.txt).
- [screening](screening/): original output schema, primary-source batch manifest and both review-comparison manifests.
- [provenance](provenance/): frozen integration/analysis references, analysis parameters, recovered Pilot-source hashes and the original v3.0.0 source-lineage ledger.
- [figures](figures/): the seven article figures as full-resolution PNGs, plus captions. SVG duplicates and repeated copies inside Resource 4 have been omitted.

These are historical production sources, not a standalone pipeline that can regenerate the paper from the reduced public CSV alone. Their controlled inputs include retained source text that is not redistributed. Absolute local paths in the supplied source copies were replaced by controlled-source basenames. Original manifests and the v3.0.0 lineage ledger retain original artifact names, stage settings and hashes: they describe their original inputs/exports, not current reader filenames. Some scripts and parameter files describe earlier figure layouts, denominators or model labels; the six current resources and article figures are the current output authority.

The V5 engine uses fresh_analysis_engine_v2.py, included beside it. Optional dependencies are in requirements.txt. The source files were syntax-checked; historical production tests and full raw-data analyses were not rerun to reorganize this release. Collection scripts can make external calls and require deliberately configured inputs/access; running them is unnecessary for reading these resources.

Frozen scientific references: integration manifest SHA-256 b64b01ae57aaca386cfdb07b08e322f515e75e3dc2b5ed0cff1701cae9028bea; analysis hash ledger SHA-256 12d9923ef1c68c3fbc511f0ab0fa22da49f5256119a279cf8d8fea099372f6aa. No new literature search, model call or study classification was made for this packaging revision. The complete phrase-pair table was deterministically derived from the unchanged binary indicators and checked against Figure 3 and the original saved pair counts.

Software is covered by the repository's MIT LICENSE. Data, figures and documentation use LICENSE-DATA.md, subject to its third-party boundary.
