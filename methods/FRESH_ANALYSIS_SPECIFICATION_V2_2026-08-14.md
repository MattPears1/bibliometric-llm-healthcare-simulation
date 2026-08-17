# Fresh analysis specification for the search ending 13 August 2026

Version: 2.0  
Prepared: 14 August 2026  
Status: fixed before final screening, human audit, study-level extraction, or outcome analysis  
Applies to: the new search from 1 January 2020 through 13 August 2026, inclusive  
Does not apply to: the preserved March 2026 dataset or any earlier manuscript result

## Why this document exists

This document states, before the final eligible set is known, how the new data will be analysed and reported. Its purpose is to prevent the results from determining the methods. It also responds directly to the reviewers' concerns about inconsistent numbers, unclear non-technical-skills classifications, incorrect flow labels, incomplete screening validation, split-word topic artifacts, partial-year growth claims, narrow emphasis on urology, and missing geographic data.

The review question remains:

> What scholarly work published from 1 January 2020 through 13 August 2026 substantively concerns an explicit large or generative language model used in simulation-based education, training, or assessment for healthcare professionals or health-professions learners?

This is a descriptive mapping of the records found by the stated search. It is not an effectiveness review and will not be described as a complete census of all relevant research.

## Source documents used to fix this plan

The plan was based on the following material, without using fresh-run outcome counts:

- the authentic decision letter and both reviewer reports;
- the audit of the conservative revision based on the submitted manuscript;
- `SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md`;
- the fresh candidate, two-reviewer comparison, human-audit, finalization, and publication-version specifications;
- the structured-extraction adjudication codebook; and
- the March analysis programs, inspected only to identify useful methods and methods that should not be repeated.

The March dataset, decisions, and numerical results do not determine any expected fresh-run result.

## Fixed analysis principles

1. Every reported number will come from one final, checked data table or a named derivative of it.
2. Selection counts will follow the real workflow. The phrase “full-text screening” will not be used for title-and-abstract review.
3. The main unit of analysis will be one scholarly work after publication versions have been reviewed and linked.
4. Screening agreement will be measured before differences are resolved and will be called model-model agreement, not human inter-rater reliability or accuracy.
5. Non-technical-skills results will come from one checked study-level extraction. Search terms, phrase matches, screening flags, and publication tiers will not be used as alternative NTS counts.
6. Multi-word terms such as “large language model,” “virtual patient,” and “situational awareness” will remain intact in the topic analysis.
7. Complete calendar years and partial 2026 will not be combined in a growth statistic.
8. Missing information will be shown, not silently converted to zero or “no.”
9. Multiple-response variables will be labelled as such. Their column totals are allowed to exceed the number of works.
10. Descriptive differences will not be presented as causal effects, statistical proof, or evidence of educational effectiveness.

## Analysis populations and denominators

The report will keep these populations separate.

| Population | Unit | Purpose |
|---|---|---|
| Retrieval occurrences | One result returned by one source/query | Source-specific search totals and audit trail |
| Deduplicated records | One bibliographic record after exact duplicate review | Candidate identification |
| Candidate records | One deduplicated record sent to both reviewers | Screening and model-model agreement |
| Record-level inclusions | Eligible publication records before version linking | Transparent screening flow |
| Eligible publication versions | Every eligible version retained in the version ledger | Publication-version audit |
| Canonical works | One preferred, reviewed version per scholarly work | All main bibliometric and content analyses |
| Human-audit records | The prospectively selected blinded audit sample | Human-model checking, reported by sampling group |

The main denominator, written as **N**, is the number of canonical works in the final one-work corpus. It must not be filled in until all of the following are complete:

- source collection and source-status checks;
- exact-record deduplication and review of uncertain pairs;
- two independent reviews of every candidate;
- the planned prospective human audit and any required expansion;
- final resolution of all uncertain or differing eligibility decisions;
- systematic publication-version review; and
- checked study-level extraction for every canonical work.

Every table must name its denominator. The following denominator rules are fixed:

- annual, model-family, simulation-method, NTS, specialty, study-design, open-access, and broad source percentages use all canonical works (**N**), unless a second denominator is explicitly shown;
- country-specific percentages use works with at least one usable country affiliation, while coverage and missingness use **N**;
- citation summaries use works with a citation value from the one fixed citation snapshot, while citation coverage uses **N**;
- author productivity uses works with usable authorship data from the fixed metadata snapshot, while author coverage uses **N**;
- model-model agreement uses all candidate records before resolution;
- human-audit results use the relevant prespecified audit group, never the unweighted 100 records as if they were a simple random sample of the whole corpus; and
- phrase-frequency percentages use **N**, with a separate sensitivity table restricted to works with a retained abstract.

## Inputs that may be analysed

### Main work-level input

The analysis may start only from a publication-version package whose status is:

`publication_version_consolidation_finalized_analysis_unit_ready`

Its `ONE_WORK_ANALYSIS_CORPUS_V2.csv`, version ledger, manifest, and file hashes must agree. Each stable work family must contribute exactly one preferred record. The record-level inclusion total and the canonical-work total must be shown separately in the selection flow.

### Checked extraction input

Model families, simulation methods, NTS domains, specialties, and study designs must come from a final checked extraction table for the canonical works. The two screening reviewers' suggested labels may be evidence for that later check, but they are not final analysis values by themselves. Differences must be resolved using the complete retained title, abstract, source keywords, and, where necessary, the primary publication.

The extraction must preserve the allowed labels and evidence rules in the structured-extraction codebook. Blank multiple-response fields mean that no supported label was identified in the available evidence; they must be counted and shown as “no explicit label identified,” not silently omitted. `unclear` is retained for a single study-design value when the design cannot be established.

### Fixed metadata snapshot

Journal/source, authorship, affiliation, open-access, and citation data will be obtained from a single work-level metadata snapshot. OpenAlex is the only source for citation counts. The exact UTC date and time must be written into the snapshot manifest before the first work-level citation request is made. Every citation value in the analysis must come from that one snapshot; values from other databases or later checks must not be substituted or maximized.

If the complete work-level snapshot cannot be obtained on one UTC date, the collection must be restarted on a new stated date. The final manuscript will say, for example, “citation counts were taken from OpenAlex on [date].” A blank citation field is missing; an explicit returned value of zero is a true zero.

Crossref may supply exact DOI bibliographic details but will not supply citation counts. Source-specific search metadata will not be merged to create a larger citation value.

## Quality checks required before calculation

The analysis program must stop rather than produce partial tables when any of these checks fails:

1. The final corpus status and hashes do not match the publication-version manifest.
2. A canonical work ID is duplicated or a version family contributes other than one preferred work.
3. A final included record has an unresolved eligibility, language, or publication-date decision.
4. A 2026 work lacks evidence that it was published on or before 13 August 2026.
5. A required single-choice field contains more than one value or a value outside the codebook.
6. A multiple-response field contains an unrecognized label.
7. A citation value is negative, non-integer, from a different source, or from a different snapshot date.
8. A percentage denominator is zero or differs from the denominator recorded in the table metadata.
9. Mutually exclusive rows fail to sum to their stated total, allowing only displayed rounding difference.
10. Any main table, figure, abstract number, or manuscript result lacks a link to its machine-readable source row.

The program must also produce a coverage table for publication date, abstract, source/journal, authors, country affiliation, open-access status, citation value, and each checked extraction field.

## Prespecified analyses

### 1. Selection flow

The selection table and Figure 1 will show, in order:

1. retrieval occurrences from each discovery source and in total;
2. technical duplicate occurrences merged before screening, separating automatic exact matches from human-confirmed same-record matches;
3. deduplicated records available for candidate identification;
4. records entering the four-concept candidate frame;
5. records reviewed independently by both model reviewers using titles, full retained abstracts when available, and source keywords;
6. final record-level exclusions, with one primary reason per record;
7. final record-level inclusions;
8. eligible publication versions linked after screening; and
9. canonical unique works analysed.

The figure will distinguish the five primary discovery sources from CORE as a supplementary source. If CORE remains unavailable despite a valid request and documented attempts, the figure note and methods will state this plainly. Crossref will be shown as DOI enrichment, not as a discovery source.

No box will say that model screening was full-text screening. Primary sources consulted to resolve uncertain records will be reported as resolution checks, not as a separate full-text eligibility stage.

Exclusion reasons will use the final primary exclusion code. Records for which two reviewers originally chose different exclusion codes will receive one final reason after resolution; their original reasons remain in the audit file.

### 2. Screening consistency and prospective human audit

Before any resolution, two forms of model-model agreement will be calculated across all candidate records:

- three-choice agreement for `INCLUDE`, `EXCLUDE`, and `UNCERTAIN`; and
- binary agreement for `INCLUDE` versus non-include.

For each form, report the number assessed, the agreement count, raw agreement percentage, Cohen's kappa, and a two-sided 95% confidence interval. Raw-agreement intervals will use the Wilson method. Kappa intervals will use a record-level percentile bootstrap with 10,000 replicates and fixed seed `2026081306`. Undefined bootstrap replicates will be counted and omitted; if more than 5% are undefined, kappa will be reported with an explanation and without a misleading interval.

The prospective human audit will follow its already fixed 100-record sampling plan. Results will be reported separately for difficult records, model-agreed inclusions, model-agreed exclusions, and records just outside the candidate boundary. Exact two-sided Clopper-Pearson 95% intervals will be used for the error proportion in the randomly selected agreed-inclusion and agreed-exclusion groups. Difficult and boundary groups will be reported as counts and reasons because they deliberately over-represent hard cases.

If a second human reviews all audit records independently, human-human raw agreement and kappa will be reported before resolution, with the same three-choice and binary distinction and a 10,000-replicate bootstrap. If that does not occur, no human inter-rater reliability statistic will be reported. Human-model comparisons will be called audit agreement, not human reliability, sensitivity, or specificity.

### 3. Publications by year

Publication year is taken from the preferred canonical publication version. The main annual table and Figure 2 will show one count for every year from 2020 through 2025, including zero years. These are complete calendar years.

The period 1 January through 13 August 2026 will be shown separately as partial-year data, with different shading and the cutoff written in the figure, caption, table, Results, and Abstract wherever the value appears. It will not be annualized or extrapolated.

No compound annual growth rate, forecast, “doubling” claim, or percentage growth calculation using partial 2026 will be produced. No regression trend will be used as a central result. Given only six complete calendar-year observations and a rapidly changing field, the main analysis will remain the observed annual counts. Any later regression requested by the editor would require a dated amendment made before that model is run and would be labelled secondary.

### 4. Journals and publication sources

Each canonical work will count once in the journal/source of its preferred publication version. Sources will be normalized using OpenAlex source ID and ISSN-L where available. A retained normalized source name may be used when no OpenAlex source is available, but its fallback status must be shown. Name-only variants must not be treated as separate journals when a shared stable identifier establishes they are the same source.

Report:

- source coverage and missingness as n/**N** and percentage;
- the ten most frequent sources, ordered by count, then normalized name, then stable source key;
- all remaining named sources combined as “other named sources” in the main table; and
- unknown or unmatched source as a separate row; and
- the complete source list in an online resource.

These are descriptive counts. They do not establish journal quality, preferred publication venue, or formal conformity to Bradford's law.

### 5. Author productivity

Each author will count at most once per canonical work. OpenAlex author ID is the preferred identity key. A name without a stable ID will be retained as an unresolved name and will not be automatically merged with another author of the same or similar name.

Report:

- authorship coverage and missingness as n/**N** and percentage;
- the ten authors linked to the largest number of canonical works, with work counts;
- the number of authors associated with one, two, three, and four-or-more works; and
- a complete author table, with stable IDs and unresolved-name flags, in an online resource.

Ties will be ordered by normalized display name and then stable key. Author order, seniority, contribution, and collaboration quality will not be inferred. No Lotka-law fit or exponent will be calculated.

### 6. Predefined phrase analysis

This analysis replaces split-word keyword counting. It is descriptive and does not replace the checked study-level extraction.

The searchable text for each canonical work is the complete retained title, abstract, and source-supplied author keywords. Text is converted to Unicode NFKC, compared without regard to letter case, and normalized so ordinary spaces and hyphens match the listed variants. Matches must be whole words or whole phrases. There is no stemming, no automatic synonym generation, and no post-result addition of favorable terms.

Each phrase label counts at most once per work. Several labels may occur in one work. A co-occurrence means that two different predefined labels appear in the same work; it does not show a semantic, causal, or collaboration relationship.

The exact predefined phrase list is below. Singular/plural endings shown in parentheses are accepted. British and American spellings are mapped only where listed.

| Group | Reported phrase | Accepted wording |
|---|---|---|
| Scope check | large language model | large language model(s); LLM; LLMs |
| Scope check | generative artificial intelligence | generative artificial intelligence; generative AI; GenAI |
| Scope check | retrieval-augmented generation | retrieval-augmented generation; retrieval augmented generation |
| Interface | chatbot or conversational agent | chatbot(s); conversational agent(s); conversational AI |
| Simulation | virtual patient | virtual patient(s); digital patient(s) |
| Simulation | simulated patient | simulated patient(s) |
| Simulation | standardized patient | standardized patient(s); standardised patient(s) |
| Simulation | scenario-based simulation | scenario-based simulation; scenario-based training; clinical simulation scenario(s) |
| Simulation | objective structured clinical examination | objective structured clinical examination(s); OSCE; OSCEs |
| Simulation | role-play | role-play; role play; role-playing; role playing |
| Simulation | mannequin simulation | mannequin simulation; manikin simulation; high-fidelity mannequin; high-fidelity manikin |
| Simulation | task trainer | task trainer(s); part-task trainer(s) |
| Simulation | virtual reality | virtual reality |
| Simulation | augmented or extended reality | augmented reality; mixed reality; extended reality |
| Simulation | serious game | serious game(s); simulation game(s) |
| Simulation | debriefing | debrief; debriefing; debriefings |
| Educational method | automated feedback | automated feedback; AI-generated feedback |
| Educational context | medical or health-professions education | medical education; health-professions education; health professions education |
| Educational context | surgical education | surgical education; surgical training; surgery education |
| Educational context | nursing education | nursing education; nursing student(s) |
| Educational context | dental education | dental education; dental student(s) |
| Educational context | interprofessional education | interprofessional education; interprofessional learning; interprofessional training |
| Skill or outcome | communication skills | communication skill(s); patient communication; clinical communication |
| Skill or outcome | clinical reasoning | clinical reasoning; diagnostic reasoning |
| Skill or outcome | decision-making | decision-making; decision making; clinical decision(s) |
| Skill or outcome | teamwork | teamwork; team-based skill(s); interprofessional teamwork |
| Skill or outcome | leadership | leadership |
| Skill or outcome | situational awareness | situational awareness; situation awareness |
| Skill or outcome | task management | task management |
| Skill or outcome | stress management | stress management; coping with stress |
| Skill or outcome | professionalism | professionalism; professional behaviour; professional behavior |
| Skill or outcome | crisis resource management | crisis resource management; crew resource management |
| Skill or outcome | empathy | empathy; empathic communication; empathetic communication |
| Skill or outcome | assessment or scoring | assessment; scoring |

The main phrase table will report every phrase in the order above, with n, percentage of **N**, and the number of matching titles, abstracts, and keyword fields. Scope-check phrases will be labelled as search-context checks and will not be interpreted as substantive themes.

The supplementary co-occurrence table will show all pairs occurring in at least three works. A supplementary network may be drawn only when at least four non-scope phrase labels meet both of these fixed rules: the label occurs in at least five works, and the displayed pair occurs in at least three works. At most the 25 most frequent eligible pairs will be shown, ordered by pair count and then alphabetically. Node size will show work count and line width will show pair count. There will be no community-detection label, centrality score, or claim that the diagram reveals hidden themes.

The word cloud will be omitted. Exact counts and labels are easier to verify and do not give arbitrary visual prominence to long or repeated words.

Because a missing abstract reduces the opportunity to find a phrase, phrase counts will be repeated as a sensitivity analysis among works with a retained abstract. This sensitivity result cannot replace the all-work denominator.

### 7. Model families

Model-family counts will use the final checked extraction and the fixed names in the extraction codebook. “ChatGPT” will not be converted to GPT-3.5, GPT-4, or another version unless the publication identifies that version. An unspecified named or generative model remains unspecified.

This is a multiple-response analysis. A work using several model families counts once for each family, so counts and percentages can sum to more than **N** and 100%. Report every family with n and percentage of **N**, ordered by count and then the fixed label. Also report the number and percentage of works for which no exact model family could be established.

The result describes models used or examined in the works found. It is not market share, adoption prevalence across education, model quality, or proof that one provider is preferable.

### 8. Simulation methods

Simulation methods will use the final checked extraction labels: virtual patient, standardized patient, scenario, OSCE, role-play, mannequin, task trainer, virtual/augmented/extended reality, serious game, debriefing, and other.

This is a multiple-response analysis. Each method counts at most once per work; a work may contribute to several methods. Report n and percentage of **N** for every method, plus “no explicit method label identified” for blank final fields. The percentage denominator remains **N**. Do not infer method effectiveness from frequency.

### 9. Non-technical-skill domains

NTS domains will use only the final checked extraction. A domain is counted only when it is a stated educational aim, activity, assessment, or reported result. Ordinary dialogue is not automatically communication training, clinical reasoning is not automatically decision-making, and empathy is not automatically an NTS domain.

The fixed pooled labels are communication, teamwork, leadership, decision-making, situational awareness, task management, stress management, professionalism, and other clearly supported NTS. These plain labels are used across studies; they will not be described as a formal application of NOTSS or NoTSUS. If a publication names a specific framework, that name will be retained separately and not silently mapped to another framework.

This is a multiple-response analysis. Report:

- works with at least one explicit NTS domain, n and percentage of **N**;
- each domain, n and percentage of **N**;
- each domain's percentage among works with at least one explicit NTS, clearly labelled as a secondary denominator; and
- works with no explicit NTS domain identified, n and percentage of **N**.

The NTS table must reconcile exactly with the canonical extraction table. Phrase-list hits, screening reviewer suggestions, and any earlier tier or regular-expression result will not supply an alternative total. Low counts will be described as “less often represented in this corpus,” not as proof of an educational or patient-safety gap.

### 10. Surgical specialties and other clinical fields

Specialty/profession counts will use the final checked extraction and will cover the full corpus. Urology will not be a separate objective, case study, or privileged recommendation.

This is a multiple-response analysis. A work can count once in every explicitly supported specialty or profession. The main display will show:

- general or multi-professional education categories;
- every surgical specialty with at least one work; and
- the ten most frequent remaining clinical specialties or professions.

The complete list will appear in an online resource. Percentages use **N**. A predeclared surgical grouping may include general surgery, urology, orthopaedic surgery, neurosurgery, otolaryngology, plastic surgery, cardiothoracic surgery, vascular surgery, paediatric surgery, transplant surgery, and obstetrics and gynaecology when the work explicitly concerns operative training. Anaesthesia and perioperative medicine will be shown separately unless the publication explicitly labels a surgical learner group.

The manuscript will not infer a specialty “gap” from a small count, promote an author-owned platform, or recommend one product.

### 11. Study designs

Each canonical work will receive exactly one final study-design label: randomized trial, nonrandomized comparative study, pre-post study, observational study, survey, qualitative study, mixed-methods study, development/evaluation study, evidence review, methods/framework paper, other, or unclear.

Report n and percentage of **N** for every label, including zero rows and `unclear`. The rows must sum to **N**. Design frequency does not establish evidence quality, risk of bias, or intervention effectiveness. No pooled educational outcome or meta-analysis is planned.

### 12. Geography and missing affiliation data

Countries will come from structured author affiliations in the fixed metadata snapshot. No country will be inferred from author names, email domains, journal titles, or study setting text.

For each canonical work, duplicate occurrences of the same country are removed. Two counts will be produced:

- **whole count:** each represented country receives one count for the work; and
- **fractional count:** each represented country receives 1 divided by the number of different countries on the work.

Country-specific percentages in the main table use the number of works with at least one country affiliation. The same table and every geographic figure caption will also state country coverage and missingness as n/**N** and percentage. A second percentage of all canonical works will be provided in the complete online table.

International collaboration will mean more than one country affiliation on a work. Its percentage denominator is works with at least one country affiliation. Missing countries will not be imputed, and works without affiliation data will not be called domestic.

The main table will show the ten highest whole counts, with fractional counts alongside them; the complete list will be supplementary. Country results describe only works with usable affiliation metadata. They cannot support strong claims about worldwide research equity, national performance, population need, or lower-resource representation.

### 13. Open access

Open-access status will come from the fixed OpenAlex work snapshot and will use its mutually exclusive status for the preferred canonical version: gold, green, hybrid, bronze, diamond, closed, or unknown. Every canonical work contributes to exactly one row. Unknown/unmatched works remain unknown and are not counted as closed.

Report n and percentage of **N** for every status, plus total known and unknown coverage. Open-access status is a point-in-time metadata description. It will not be treated as proof of permanent availability, affordability, reuse permission, or accessibility in every country.

### 14. Citations

Citation counts will come only from the one fixed OpenAlex snapshot described above. Report:

- citation coverage and missingness as n/**N** and percentage;
- total, mean, median, first and third quartiles, minimum, maximum, and number with zero citations among works with a citation value; and
- the same descriptive values by publication year, with 2026 labelled partial.

Quartiles will use linear interpolation on the ordered values. No missing citation value will be replaced with zero. There will be no h-index, g-index, i10-index, citation-rate forecast, or test comparing years. Citations will not be used as a measure of study quality, educational value, or clinical importance.

## Placement of questioned analyses

The following choices are fixed without looking at the fresh outcomes.

| Analysis | Placement | Decision and reason |
|---|---|---|
| Bradford's law | Omitted | Simple normalized source counts answer the journal-distribution question directly. Formal law claims add complexity and are sensitive to source coverage and zone definitions. |
| Lotka's law | Omitted | Author counts will be shown, but identity gaps and name-only records make a fitted productivity law unnecessarily fragile. |
| Model licensing | Omitted | A model-family name does not reliably establish the licence for the exact version used, and terms change. The reviewer identified contradictory arithmetic in the submitted analysis. Access implications may be discussed qualitatively without inventing a legal licence classification. |
| Journal/source concentration | Main descriptive table | Top sources, complete source list, coverage, and missingness; no law claim. |
| Author productivity | Supplementary descriptive table, brief main-text summary | Stable-ID work counts and coverage; no exponent or law claim. |
| Predefined phrase frequencies | Main descriptive table | Direct response to the split-word artifact; exact phrase list and field coverage are published. |
| Phrase co-occurrence | Supplementary | Exact same-work pairs and a limited diagram; no centrality or hidden-theme claim. |
| Word cloud | Omitted | Exact tables and bar charts are clearer and auditable. |
| Urology-only analysis | Omitted | Urology is treated like every other specialty in the broad specialty table. |

## Sensitivity analyses

The following checks will be run after the primary tables and will not replace them:

1. repeat work-level descriptive counts after excluding standalone preprints or repository-only versions;
2. repeat metadata-dependent summaries after excluding records without an exact DOI, PMID, or stable work-ID match to OpenAlex;
3. repeat phrase frequencies among works with a retained abstract;
4. report how any prospective human-audit expansion changed record-level inclusion and the final one-work corpus; and
5. if the human audit or version review changes the corpus, regenerate every dependent table and figure rather than patching individual numbers.

These checks are descriptive. No “robust” result will be claimed merely because the rank order looks similar.

## Rounding, ordering, zeros, and missing values

- Counts are whole numbers.
- Percentages are calculated from unrounded counts and shown to one decimal place.
- A nonzero percentage that would display as 0.0% is shown as `<0.1%`.
- Mutually exclusive percentages may differ from 100.0% only because of displayed rounding; underlying counts must sum exactly to the denominator.
- Multiple-response tables carry a note that rows do not sum to **N** or 100%.
- A genuine zero is shown as `0` and `0.0%`.
- If a denominator is zero, the result is `not estimable`, never zero.
- Missing, unknown, unclear, unmatched, and no explicit label identified are kept distinct where the source fields allow.
- No missing value is imputed for the primary analysis.
- Ties are broken by the fixed label or normalized display name and then stable identifier; they are not manually reordered for presentation.

## Planned main tables and figures

### Main manuscript

- **Figure 1:** accurately labelled selection flow.
- **Figure 2:** annual publication counts for complete years 2020–2025, with partial 2026 shown separately.
- **Figure 3:** model families and simulation methods, two clearly labelled panels.
- **Figure 4:** NTS domains and study designs, two clearly labelled panels.
- **Figure 5:** broad specialty/profession distribution, with surgical specialties identified without singling out urology.
- **Table 1:** selection counts, pre-resolution model-model agreement with 95% intervals, and prospective human-audit results by group.
- **Table 2:** publication, source, open-access, citation, and metadata-coverage summary.
- **Table 3:** model-family, simulation-method, and study-design counts with explicit denominator notes.
- **Table 4:** one reconciled NTS analysis.
- **Table 5:** country results with coverage and missingness.
- **Table 6:** predefined phrase frequencies.

If journal space requires fewer items, panels or full category lists may move to an online resource without changing calculations, denominators, or the prespecified primary results.

### Online resources

- complete selection and exclusion-reason table;
- model-review comparison and human-audit summaries;
- publication-version ledger and sensitivity results;
- complete normalized source list;
- complete author-productivity table and descriptive frequency distribution;
- complete model, simulation, NTS, specialty, and study-design tables;
- complete country whole/fractional table and metadata coverage;
- complete open-access and citation-by-year tables;
- the exact predefined phrase list, per-work phrase indicators, complete co-occurrence table, and eligible co-occurrence diagram; and
- a claim-to-source register linking each manuscript number to a table cell and input hash.

## Claims that are not permitted

The revised manuscript, abstract, tables, figures, captions, response letter, and supplements must not claim that:

- the search found every eligible study or is an exhaustive systematic review;
- model-model agreement is human inter-rater reliability, screening accuracy, sensitivity, or specificity;
- a 100-record audit proves zero error in the whole corpus;
- unaudited records were human validated;
- title-and-abstract screening was full-text screening;
- a frequent model has greater market share, quality, safety, effectiveness, or educational value;
- sparse NTS or specialty counts prove a true educational, workforce, or patient-safety gap;
- geographic rankings prove global equity, national productivity, or lower-resource underrepresentation when affiliation data are incomplete;
- open-access metadata prove affordability, legal reuse, or practical access;
- citation counts measure study quality or educational impact;
- partial 2026 represents a full year, supports CAGR, or justifies a forecast;
- the source distribution follows Bradford's law;
- author productivity follows Lotka's law;
- model family alone establishes an open-source or proprietary licence;
- a phrase co-occurrence is a discovered causal or conceptual relationship;
- urology was a prespecified gap or deserves a product-specific recommendation; or
- the frequency of a simulation method shows that it works.

## Reviewer-response links

| Reviewer concern | Prespecified response |
|---|---|
| Conflicting numbers and labels | One canonical corpus, one derivative per result, denominator checks, and a claim-to-source register |
| Three conflicting NTS systems | One checked extraction; no tiers or regex-derived NTS total |
| Incorrect PRISMA wording | Title/abstract review labelled accurately; source checks separated from screening |
| One-pass model screening and overstated reliability | Two independent complete reviews, pre-resolution agreement with 95% intervals, prospective blinded human audit, and restricted claims |
| Split compound words | Exact predefined multi-word phrases; no split-word word cloud |
| Partial-2026 growth claim | Complete years shown separately; no CAGR, annualization, or forecast |
| Narrow urology emphasis and promotion | Broad specialty analysis; no separate urology claim or platform promotion |
| NOTSS/NoTSUS inconsistency | Plain pooled domain labels; named frameworks preserved without conflation |
| Model-name inconsistency | Fixed model-family labels; unspecified versions remain unspecified |
| Geographic missingness and equity | Coverage and missingness shown beside every geographic result; no strong equity inference |
| English-only restriction | Search and assessability restriction reported as a limitation; no claim of worldwide representativeness |

## Change control

This plan is complete before final fresh-run outcomes are known. Any later change must be recorded in a dated amendment stating:

1. what changed;
2. why it changed;
3. whether any outcome count had already been seen;
4. which outputs were affected; and
5. whether the change is a correction, required feasibility adjustment, or additional exploratory analysis.

An unplanned analysis may be reported only as exploratory. It may not silently replace a prespecified analysis.

## Internal consistency checklist

Before the specification is used, confirm all of the following:

- the date window is 1 January 2020 through 13 August 2026 inclusive everywhere;
- 2020–2025 are the only complete calendar years and 2026 is partial;
- the main unit is one canonical scholarly work;
- record-level and work-level inclusion counts remain separate;
- citations use OpenAlex only and one recorded snapshot date;
- NTS counts use checked extraction only;
- model, simulation, NTS, and specialty tables are marked multiple-response;
- study design and open-access tables are mutually exclusive and include unclear/unknown;
- country percentages state both covered-work and all-work denominators where required;
- Bradford, Lotka, licensing, word cloud, urology-only, CAGR, forecasting, and effectiveness analyses are absent;
- all model and framework names follow the fixed codebooks; and
- every planned manuscript number can be traced to a generated table row and immutable input hash.

The companion machine-readable contract is `FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json`.
