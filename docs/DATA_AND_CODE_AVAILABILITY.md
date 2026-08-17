# Data and code availability

## Publicly released material

This repository publishes the material needed to inspect the reported selection flow and derived results without redistributing restricted source records:

- all 18 exact source-specific search strings and retrieval counts;
- the complete aggregate selection flow and model-stream comparison tables;
- a 547-row reduced publication-version ledger and 485-row family summary;
- a 485-row checked one-study dataset and 23-field data dictionary;
- complete descriptive and sensitivity tables as matched CSV/JSON pairs;
- all main and supplementary figures in publication and vector formats;
- the exact phrase dictionary, per-study phrase indicators, and co-occurrence data;
- the analysis claim-to-source register;
- collection, integration, analysis, validation, and regression-test code; and
- a release-wide SHA-256 checksum ledger.

## Material not redistributed

The release deliberately excludes:

- raw Scopus or other provider response payloads;
- abstracts, full text, and restricted provider metadata;
- the complete record-level screening corpus;
- API keys, access tokens, or other credentials; and
- internal execution or model-session logs.

These exclusions protect third-party rights and prevent credentials or internal operational material from becoming part of the research deposit. Where provider terms permit, additional verification material can be supplied confidentially to journal editors.

## Public audit versus full production rerun

The released reduced dataset is sufficient to audit the checked classifications and many study-level descriptive counts. The released result tables, claim register, and checksums permit exact verification of every published output file.

Re-executing the complete fail-closed V5 production engine from the beginning additionally requires the authorized hash-bound source corpus identified by the input contract. Those provider-derived inputs are not public redistributable data. The engine rejects missing or altered inputs rather than silently substituting them.

## Version authority

Use GitHub release `v2.0.0` or its corresponding Zenodo archive. The tag `v1.0-submission` is historical and does not contain the final six-source results.
