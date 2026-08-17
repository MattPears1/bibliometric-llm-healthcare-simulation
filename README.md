# Large Language Models in Healthcare Simulation Education

Reproducibility package for **Large Language Models in Healthcare Simulation Education: A Bibliometric Analysis with AI-Assisted Screening**.

This is the corrected, six-source `v2.0.0` release. It is the authoritative public package for the study window **1 January 2020 through 13 August 2026**. The earlier computational material preserved under the Git tag `v1.0-submission` is historical and must not be used for the final manuscript's results.

## Frozen study snapshot

| Measure | Count |
|---|---:|
| Completed discovery sources | 6 |
| Retrieval occurrences | 9,719 |
| Candidate records screened by both model streams | 3,919 |
| Eligible publication records | 547 |
| Alternate publication versions | 62 |
| Canonical unique studies | 485 |

The six completed discovery services were OpenAlex, PubMed, Europe PMC, Semantic Scholar, DOAJ, and Scopus. Crossref was used only for exact-DOI metadata checking. Search matches were candidates, not automatic inclusions. Counts for 2026 are partial through 13 August and were not annualized.

The results describe publication activity, reported applications, and research coverage. They do not by themselves establish educational effectiveness.

## Repository contents

- [`online_resources/`](online_resources/) contains the five reader-facing Online Resource groups cited by the manuscript.
- [`results/tables/`](results/tables/) contains all six main tables as matched CSV/JSON pairs.
- [`results/figures/`](results/figures/) contains five main figures as 600-dpi PNG and vector EPS files.
- [`methods/`](methods/) contains the locked screening codebook, model-review protocol, analysis specification, and final integration amendment.
- [`code/`](code/) contains collection, integration, analysis, validation, and regression-test code.
- [`audit/`](audit/) contains the frozen public release record, analysis summary, and claim-to-source register.
- [`SHA256SUMS.csv`](SHA256SUMS.csv) binds every released file by relative path, SHA-256 digest, and byte count.

The exact file-to-manuscript mapping is in [`docs/ONLINE_RESOURCE_MAP.md`](docs/ONLINE_RESOURCE_MAP.md).

## Quick verification

Python 3.10 or later is sufficient for the public integrity check:

```bash
python code/verify_public_release.py .
```

The complete V5 production engine additionally requires NumPy and Matplotlib and the authorized, hash-bound provider inputs described in the input contract. Raw provider responses and other restricted inputs are intentionally not redistributed. See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Rights-conscious release

This repository includes derived aggregate outputs, exact query strings, checked study-level classifications, a reduced publication-version audit, figures, and code. It excludes raw Scopus or other provider responses, abstracts and full text, the complete record-level screening corpus, credentials, and internal execution logs.

See [`docs/DATA_AND_CODE_AVAILABILITY.md`](docs/DATA_AND_CODE_AVAILABILITY.md) for the detailed inclusion/exclusion boundary.

## Citation and archival status

Use the citation metadata in [`CITATION.cff`](CITATION.cff). The GitHub release `v2.0.0` is the current versioned source. A Zenodo-ready metadata record is supplied in [`.zenodo.json`](.zenodo.json); when the GitHub repository is enabled in Zenodo, the release can be archived and assigned a DOI without changing the research files.

An earlier manuscript version is available as a medRxiv preprint at [https://doi.org/10.64898/2026.06.02.26354722](https://doi.org/10.64898/2026.06.02.26354722). Its earlier numerical results are superseded by this six-source package.

## Licence

- Code is licensed under the [MIT License](LICENSE).
- Original derived data, tables, figures, and documentation are licensed under [CC BY 4.0](LICENSE-DATA.md).
- Third-party identifiers and source-linked material remain subject to the rights and terms of their originating services.
