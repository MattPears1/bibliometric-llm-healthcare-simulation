# Screening codebook for the fresh full rerun

Version: 2.0  
Status: locked for the de-novo full rerun  
Locked: 14 August 2026, before independent screening  
Publication window: 1 January 2020 through 13 August 2026, inclusive  
Screening unit: one deduplicated bibliographic record  
Later analysis unit: one canonical scholarly work after publication-version review  
Independent-review evidence: the complete retained title, abstract, source keywords, and neutral bibliographic fields in the frozen reviewer file

This codebook applies only to the fresh full rerun. It is not an amendment to the March 2026 corpus and contains no legacy paper IDs, decisions, or counts. Search-query matches are candidates for review, not automatic inclusions.

## Review question

Does this record substantively concern an explicit large language model or generative language model used in simulation-based education, training, or assessment for healthcare or health-professions learners?

## Decision rule

Select `INCLUDE` only when all five inclusion criteria are satisfied. Select `EXCLUDE` when the retained evidence clearly fails at least one criterion. Select `UNCERTAIN` rather than guessing when the evidence is insufficient; state what must be checked.

## Inclusion criteria

1. **Date and assessable language.** The record was published from 1 January 2020 through the end of 13 August 2026, and enough of the title and abstract is available in English to judge eligibility. The observed record or source page must support this; do not infer language from a database setting. A 2026 record with only a year and no exact date is `UNCERTAIN` until its date is checked.
2. **Explicit language-model component.** The title or abstract identifies a large language model, a generative language model, generative AI, or a named model family. Examples include ChatGPT/GPT, Claude, Gemini/Bard, Llama, Mistral/Mixtral, Med-PaLM, BioGPT, Meditron, DeepSeek, Qwen, Phi, or another system explicitly described as a generative, pretrained, foundation, or large language model. Generic artificial intelligence, machine learning, natural-language processing, chatbot, conversational-agent, or transformer wording alone is not enough unless the retained text makes the generative language-model basis clear.
3. **Health-professions education.** The main context is education, training, assessment, or skill development for healthcare professionals or learners. This includes medical, surgical, nursing, dental, pharmacy, paramedic, midwifery, allied-health, and interprofessional education. Patient education alone and general education outside the health professions do not qualify.
4. **Simulation is central.** Simulation-based education is a main subject, intervention, method, or evaluated use—not a passing background reference. Eligible examples include interactive virtual or simulated patients, standardized patients, clinical scenario simulation, OSCEs or educational role-play, mannequin or task-training simulation, immersive/VR/AR/XR simulation, serious-game simulation, and simulation-linked feedback or debriefing. Static examination benchmarking, ordinary question answering, noninteractive case or vignette generation, and general teaching assistance do not qualify unless the work explicitly embeds them in a simulation activity.
5. **Substantive scholarly contribution.** The item is primary research, a substantive evidence review, or a methods/framework paper with enough information to judge the work. A conference paper may qualify if it contains sufficient substantive information; a bare or very short conference abstract does not.

Non-technical skills, surgery, and urology are variables to describe later. They are not required for inclusion.

### Publication-date convention

Use the first verifiable date on which that specific record version was publicly published (including a formal online-first date). Do not use a database indexing, deposit, or update date as the publication date. When sources disagree, preserve the values and resolve them against the publisher or repository record. A 2026 year without a month and day is not enough to establish that publication occurred by 13 August.

## Exclusion criteria and primary codes

Choose the one code that most directly explains why the record is ineligible. Add a short plain-language reason.

| Code | Use when |
|---|---|
| `E1_NOT_LLM` | No explicit large/generative language-model component is supported; the item uses only generic AI/ML/NLP/chatbot language or a non-generative system. |
| `E2_NOT_HEALTH_ED` | The work is not about education, training, assessment, or skill development for health-professions learners. |
| `E3_NOT_SIMULATION` | Simulation-based education is absent, peripheral, or merely mentioned. This includes static exam benchmarking, ordinary question answering, and noninteractive vignette generation. |
| `E4_CLINICAL_ONLY` | The work concerns clinical decision support, diagnosis, treatment, documentation, workflow, or patient information without a health-professions simulation-training purpose. |
| `E5_INELIGIBLE_TYPE` | The item is an editorial, letter, correction, retraction, protocol without results, dataset or supplement, inadequately reported conference abstract, or another non-substantive item. |
| `E6_OUT_OF_RANGE` | The verified publication date is before 1 January 2020 or after 13 August 2026. |
| `E7_NOT_ASSESSABLE_IN_ENGLISH` | The available title and abstract do not provide enough English-language information to judge the record after the permitted source check. |
| `E9_OTHER` | The record clearly fails the stated review question for another reason; the reviewer must explain the reason. |

`E8_DUPLICATE_VERSION` from the earlier codebook is deliberately not used during independent eligibility review. Publication versions are handled only after record-level eligibility has been decided, as described below.

## When the answer is uncertain

Use `UNCERTAIN` and one primary resolution request:

| Code | What must be checked |
|---|---|
| `U1_NEED_FULL_TEXT` | The title/abstract does not show enough about the educational activity or simulation. |
| `U2_NEED_MODEL_DETAIL` | It is unclear whether the system is an explicit large/generative language model. |
| `U3_NEED_DOCUMENT_TYPE` | It is unclear whether the item is a substantive scholarly contribution. |
| `U4_NEED_VERSION_CHECK` | The record may be another publication version, but eligibility must still be judged on its own evidence first. |
| `U5_NEED_LANGUAGE_CHECK` | More English-language information is needed. |
| `U6_NEED_DATE_CHECK` | The precise publication date, especially for a 2026 record, must be confirmed. |

Every uncertain record must be resolved using a logged metadata, source-page, or full-text check before the final corpus is locked. The original independent decisions must remain unchanged in the audit trail.

## Record eligibility and later publication-version handling

The two stages answer different questions and must not be combined.

### Stage 1: judge each record

- Before screening, exact technical duplicates of the same database record may be merged using stable identifiers and recorded in the retrieval ledger.
- Each remaining screening record receives an eligibility decision on its own evidence.
- A reviewer must not exclude a record merely because it appears to be a preprint, conference version, or later journal version of another record.
- Reviewers may flag a possible relationship with `U4_NEED_VERSION_CHECK`, but they must still answer the substantive eligibility criteria as far as the evidence allows.

### Stage 2: link versions of the same scholarly work

Only after record-level decisions are resolved, compare eligible records for publication-version relationships. Use DOI, registry identifiers, title, authors, dates, sample, intervention, and reported content; title similarity alone is insufficient.

- If a preprint and final journal publication are substantively the same report, retain both in a version ledger and use the final, most complete publication as the canonical work.
- If no final publication is found, retain an eligible standalone preprint and flag it for sensitivity analysis.
- A correction, supplement, or conference-to-journal version is linked rather than silently deleted when it reports the same substantive work.
- Companion papers using the same project or dataset remain separate scholarly works when they report materially different questions, analyses, or educational interventions.
- Possible relationships that cannot be resolved remain flagged; they are not collapsed by assumption.

Report the counts separately: raw records retrieved, technical duplicates removed before screening, records screened, record-level inclusions, eligible versions linked after screening, and canonical unique works analysed.

## What each independent model reviewer records

The saved field names support reproducibility, but each field has a simple meaning.

| Field | Plain-language instruction |
|---|---|
| `paper_id` | Copy the neutral record ID exactly. |
| `decision` | Choose `INCLUDE`, `EXCLUDE`, or `UNCERTAIN`. |
| `primary_code` | Use `INCLUDE`, one exclusion code, or one uncertainty code from this codebook. |
| `confidence` | Choose `high`, `medium`, or `low`; confidence does not replace evidence. |
| `date_eligible` | Say `yes`, `no`, or `unclear` for the date window. |
| `language_assessable` | Say `yes`, `no`, or `unclear` for adequate English-language evidence. |
| `llm_explicit` | Say `yes`, `no`, or `unclear` for an explicit large/generative language model. |
| `health_professions_education` | Say `yes`, `no`, or `unclear` for a health-professions learner purpose. |
| `simulation_central` | Say `yes`, `no`, or `unclear` for simulation being a main part of the work. |
| `eligible_document_type` | Say `yes`, `no`, or `unclear` for a substantive scholarly contribution. |
| `evidence` | Explain the decision in one or two ordinary-language sentences tied to the record. Do not quote long passages. |
| `simulation_modalities` | List only simulation forms explicitly supported by the record: `virtual_patient`, `standardized_patient`, `scenario`, `osce`, `roleplay`, `mannequin`, `task_trainer`, `vr_ar_xr`, `serious_game`, `debriefing`, or `other`. Leave blank if excluded or unsupported. |
| `nts_domains` | List a domain only if it is an explicit educational aim, activity, assessment, or result: `communication`, `teamwork`, `leadership`, `decision_making`, `situational_awareness`, `task_management`, `stress_management`, `professionalism`, or `other`. A broad word such as “empathy” or “reasoning” is not automatically an NTS classification. |
| `specialty` | Record a named clinical specialty only when explicit; otherwise leave blank. |
| `model_families` | Record only model families actually used, evaluated, or centrally examined; ignore background mentions. |
| `study_design` | Choose the best-supported design: `randomized_trial`, `nonrandomized_comparative`, `pre_post`, `observational`, `survey`, `qualitative`, `mixed_methods`, `development_evaluation`, `evidence_review`, `methods_framework`, `other`, or `unclear`. |
| `possible_version_of` | If a version relationship is suspected, give the other neutral record ID; otherwise leave blank. This flag is not an exclusion decision. |

## Independent model review and resolution

- Two model reviewers assess every frozen candidate independently under this same codebook.
- Neither reviewer sees legacy membership or decisions, the candidate-trigger flags, the other model's output, or later human decisions.
- Reviewers use the complete retained title, abstract, and source keywords; they do not receive shortened snippets. They do not browse during the independent pass.
- Record the model and version, exact reviewer instructions, input and output hashes, date/time, settings, and any failed or repeated calls.
- Calculate model-model agreement before any decision is resolved, both for the three choices and for `INCLUDE` versus non-include.
- Preserve both original decisions. After both outputs are locked, complete the prospective human audit described below while the human reviewer remains blind. Human-audited conflicts may then use that judgement in final adjudication; any remaining disagreements and uncertain cases are resolved separately using logged source evidence.
- Agreement between models measures consistency, not correctness. It must not be called human inter-rater reliability or proof of screening accuracy.

## Prospective human audit

The human audit occurs only after both independent model-review files have been completed, frozen, and hashed.

1. A separate human-audit plan fixes the sampling rules and random seed before the review workbook is generated.
2. The audit should cover the difficult boundary: model disagreements and uncertain decisions, plus pre-specified random samples of agreed inclusions and agreed exclusions. The sample size and strata are reported from the actual fresh-run counts, not copied from an earlier run.
3. The human workbook shows the same bibliographic evidence but hides both model decisions, confidence labels, trigger categories, and legacy status. It also hides why a record was sampled.
4. The human reviewer applies this codebook prospectively and records a decision, reason, confidence, and any request for full text. The completed human file is frozen before comparisons are revealed.
5. Only then compare human and model decisions. Report agreement and errors for the audited records, with stratum-specific or properly weighted estimates where sampling was unequal.
6. Human decisions may inform final adjudication for records actually reviewed. Do not describe unreviewed records as human-validated, and do not claim that a sampled audit is the same as two humans independently screening the complete corpus.

## Study-level extraction after eligibility

Detailed model, simulation, learner, specialty, non-technical-skill, design, and outcome fields are extracted only from the canonical eligible works under a separately versioned extraction codebook. A model reviewer may suggest these fields during screening, but final study-level counts must come from the later checked extraction table, not from keyword hits alone.

## Change from version 1.0

- The end date is now the last complete day before the rerun: 13 August 2026.
- The codebook applies to a wholly fresh search and contains no inherited records, decisions, or numerical expectations.
- Record-level eligibility is explicitly separated from later publication-version consolidation; the former `E8_DUPLICATE_VERSION` screening exclusion is retired.
- Date and language judgements are explicit outputs, and records with an unresolved 2026 date cannot be assumed eligible.
- Model-review outputs are explained in ordinary language.
- A blinded prospective human audit is required after the two independent model outputs are locked.
