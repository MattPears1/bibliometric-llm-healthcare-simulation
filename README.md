# Large language models in healthcare simulation education

Publication resources for **Large language models in healthcare simulation education: a bibliometric analysis of simulation approaches and non-technical skills**, Global Surgical Education – Journal of the Association for Surgical Education.

**Version 3.0.0 · 16 October 2026 · frozen 483-study analysis.**

| Selection stage | Count |
| --- | ---: |
| Exact searches across six sources | 18 |
| Retrieval occurrences | 9,719 |
| Candidate records reviewed | 3,919 |
| Eligible publication records | 547 |
| Alternate publication versions | 64 |
| Unique studies | **483** |

The eligibility window is 1 January 2020–13 August 2026. Five sources were searched on 14 August and Scopus on 16 August 2026. The 2026 count is partial and is not annualised.

## The six Online Resources

| Resource | Contents |
| --- | --- |
| [1. Searches](online_resources/online_resource_1_search_strategy/) | All 18 exact searches, dates, source totals and candidate rule |
| [2. Selection and publication versions](online_resources/online_resource_2_selection_and_versions/) | All 3,919 screening decisions and 547 eligible publication records |
| [3. Complete results](online_resources/online_resource_3_complete_results/) | Descriptive and sensitivity results, with the corrected model-family audit |
| [4. Phrases and NTS](online_resources/online_resource_4_phrases/) | Dictionaries, per-study indicators, networks and fine-grained NTS concepts |
| [5. Study dataset and code](online_resources/online_resource_5_reduced_dataset/) | One row per study, current model identities, dictionary, provenance and analysis code |
| [6. Pilot and lead-author checks](online_resources/online_resource_6_validation/) | Recovered Pilot; both eligibility samples; disagreement recheck; NTS classification check |

[Download the six resource ZIP files](https://github.com/MattPears1/bibliometric-llm-healthcare-simulation/releases/tag/v3.0.0). [All seven article figures](results/figures/) and their captions are also included.

The Pilot contains 100 agent-generated workflow-test decisions. Its 23-record overlap with the August human sample has been verified from the original identifiers. It is not human validation. The two human eligibility samples share five records; these are a different pair of exercises.

There was one lead author performing human checks. Initial answers, later comparison-assisted answers and unresolved differences remain separate. The later checks do not replace the frozen 483-study classifications. See [validation limitations](online_resources/online_resource_6_validation/README.md).

## Verify and reuse

Run **python -B code/verify_public_release.py .** from the repository root. This offline command checks every released file hash and key scientific counts and joins. Run **python -B -m unittest discover -s code -p test_verify_public_release.py** for its regression tests.

The original derived material is under [CC BY 4.0](LICENSE-DATA.md); software is under the [MIT License](LICENSE). Raw provider responses, abstracts, source-keyword text, downloaded full texts and private workbooks are excluded. The public files support inspection and verification; a complete raw-data rerun requires the controlled source inputs. [Reproducibility guide](docs/REPRODUCIBILITY.md).

The earlier 485-study release remains in Git history and the v2.0.0 tag for provenance. It is superseded for the current article. Use the current corrected model-family fields rather than historical extraction wording.

Article identifier supplied in the publisher proof: [10.1007/s44186-026-00592-6](https://doi.org/10.1007/s44186-026-00592-6). Citation details are in [CITATION.cff](CITATION.cff).
