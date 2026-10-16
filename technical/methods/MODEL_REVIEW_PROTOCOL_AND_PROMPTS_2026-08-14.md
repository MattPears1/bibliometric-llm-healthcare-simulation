# Model-review protocol and prompt record

Date locked: 14 August 2026  
Scope: corrected candidate screening and structured extraction  
Status: reporting artifact; it does not replace the row-level reviewer files

## Tool identity and limits

The corrected screening and extraction used isolated OpenAI Codex model-agent sessions operating on local files. The deployment identifier, sampling temperature, top-p, and maximum-token setting were not exported into the project by the host application and are therefore reported as unavailable rather than inferred. Every row-level input, output, evidence statement, comparison, adjudication, codebook, and production script is preserved locally.

The earlier 2026 screening artifacts labelled `claude-code-sonnet` are retained only as historical evidence and were not treated as the corrected screen. No claim is made that the earlier run used a direct Anthropic API or a specific Claude deployment.

## Screening input

Each reviewer received, per candidate:

- stable `paper_id`;
- complete retained title;
- complete retained abstract (not a 500-character excerpt); and
- normalized source keywords.

Reviewers did not receive the submitted/legacy decision, the other corrected reviewer's decision, a comparison file, an adjudication file, or the emerging consensus. The candidate frame and batch order were fixed before review. Batches 1–39 contained 50 records, batch 40 contained 7, batches 41–55 contained 50, and batch 56 contained 3 (2,710 total).

## Governing screening prompt

The invariant task instruction was:

> Review only the assigned batch(es) under `03_PIPELINE/SCREENING_CODEBOOK.md` version 1.0. Decide whether each scholarly work substantively concerns an explicit large/generative language model used in simulation-based education or training for healthcare or health-professions learners. Assess the complete retained title, abstract, and source keywords. Do not inspect legacy decisions, the other reviewer, comparisons, adjudications, consensus, or downstream analyses. Use a primary publisher/full-text lookup only to resolve genuine ambiguity and retain the URL in `evidence`. Write one row per input `paper_id`, in exact input order, using the exact 14-column schema and controlled vocabularies. Do not guess: use the applicable `UNCERTAIN` code when evidence is insufficient. Validate schema, row count, identifiers, controlled values, decision/code gates, and nonblank record-specific evidence before returning the file.

The full eligibility, exclusion, uncertainty, modality, NTS, specialty, model-family, and study-design definitions supplied to both agents are preserved verbatim in `03_PIPELINE/SCREENING_CODEBOOK.md`.

## Isolation and review sequence

1. Reviewer A and Reviewer B were assigned disjoint agent sessions.
2. Each session was expressly prohibited from opening the other reviewer's directory or any comparison, adjudication, consensus, legacy-decision, or downstream file.
3. Outputs were validated against the input IDs/order and controlled schema.
4. `03_PIPELINE/compare_independent_reviews.py` generated pre-adjudication agreement and a queue containing every decision disagreement or `UNCERTAIN` record.
5. A separate adjudication pass inspected both rationales and, where needed, complete primary sources.
6. `03_PIPELINE/finalize_screening.py` failed closed unless all queued disagreements were resolved and all 2,710 records had one final decision.

## Adjudication prompt

The invariant adjudication instruction was:

> Apply the locked screening codebook to every queued conflict. Inspect both independent decisions, the complete retained record, and an authoritative primary/publisher/full-text source when the conflict cannot be resolved from retained text. Record one final decision and primary code, a concise evidence-led rationale, and up to two source URLs. Do not change either independent review. Resolve every uncertainty; do not emit `UNCERTAIN` in the locked consensus. Check preprint/final or other version relationships separately and record them in `VERSION_RELATIONSHIPS_LEDGER.csv` without double-counting a work.

## Structured-extraction prompt

All 324 final inclusions were queued for a second field-level review. The invariant instruction was:

> Follow `03_PIPELINE/EXTRACTION_ADJUDICATION_CODEBOOK.md` version 1.1. For every assigned included record—including fields on which the screeners initially agreed—verify the complete retained record and a primary/publisher/full-text source where available. Resolve final simulation modalities, NTS domains, specialty, model families, and study design; preserve the exact model wording in `model_description_raw`; give a record-specific rationale; and retain at least one evidence URL. Use only the controlled values, do not infer unsupported detail, preserve input IDs/order and all invariant source columns, and validate the exact 34-column schema before return.

`03_PIPELINE/finalize_extractions.py --require-all-reviewed` fails unless every included ID has exactly one reviewed extraction record and every final field satisfies the locked vocabulary and evidence rules.

## Output and post-processing

- Screening output: exact 14-column CSV files, one per reviewer/batch.
- Comparison output: paired decisions and field values plus pre-adjudication agreement.
- Adjudication output: final decision/code/rationale and primary URLs.
- Consensus output: source metadata, both immutable reviews, adjudication, and final decision in one CSV.
- Extraction output: exact 34-column reviewed batch files merged into a final included corpus and field-level provenance ledger.
- Automated post-processing is limited to schema validation, controlled-token validation, exact joins by `paper_id`, deterministic counts, version canonicalization from the explicit ledger, hashes, and generation of tables/figures. No unrecorded model decision is inserted by a post-processing script.

## Performance interpretation

Agreement between the two independent model-review passes is a consistency measure, not a human-reference performance estimate. The final corrected screen had binary raw agreement 0.9760147601 (Cohen kappa 0.8874531507) and three-way raw agreement 0.9649446494 (kappa 0.8525071211) before adjudication. A separate 150-record domain near-miss sample produced 150 exclusions, but it likewise does not establish human sensitivity or specificity.

No preserved, independently blinded human reference-standard dataset supports the submitted kappa claims. Human authors must review and accept responsibility for the final corpus and manuscript before resubmission; any future human validation should be prospectively locked and reported separately.

## Data governance

All input/output CSV and JSON files were kept in the local revision workspace. API keys were not written into reviewer prompts, outputs, manuscripts, manifests, or the public/reviewer bundle. The OpenAlex key remains in an external ignored plaintext env file under the local email-tool secret store; DPAPI was not used. Primary-source URLs, rather than copied copyrighted full text, are retained as evidence wherever possible. Redistribution rights for the large raw source snapshot remain an author confirmation item.
