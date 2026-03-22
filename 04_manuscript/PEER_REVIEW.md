# Peer Review: Large Language Models in Healthcare Simulation -- A Bibliometric Analysis

**Reviewer:** Automated Manuscript Audit
**Date:** 2026-03-22
**Manuscript version:** MANUSCRIPT_20260322.md

---

## EXECUTIVE SUMMARY

This is a well-conceived and ambitiously scoped bibliometric analysis addressing a timely intersection of LLMs, healthcare simulation, and non-technical skills training. The open-access data philosophy is a genuine contribution. The writing is generally at journal-submission quality with strong argumentative structure. However, the manuscript suffers from a **critical numerical inconsistency** that pervades the entire document: the Abstract and Methods reference the final dataset of 12,645 included papers, while the Results, Discussion, and Conclusions sections still report numbers from an earlier analytical run of 10,417/11,529 papers. This must be resolved before submission.

---

## 1. NUMBER CONSISTENCY -- CRITICAL ISSUES

### 1.1 The Two-Dataset Problem (CRITICAL)

The manuscript conflates numbers from two distinct analytical runs:

| Metric | Abstract/Methods (Final Dataset) | Results/Discussion/Conclusions (Old v3 Dataset) |
|--------|--------------------------------|------------------------------------------------|
| Total included papers | 12,645 | 11,529 |
| Papers with metadata for analysis | Not stated | 10,417 |
| Initial records | 100,277 | 92,941 |
| Unique after dedup | 86,635 | 81,001 |
| Dedup rate | 13.6% | 11.5% |
| Stage 1 includes | 3,648 (implied) | 3,316 |
| Stage 1 excludes | 73,990 (implied) | 69,472 |
| Stage 1 uncertain | 8,997 (implied) | 8,213 |
| Tier 1 | 6,210 | 5,029 |
| Tier 2 | 514 | 442 |
| Tier 3 | 3,134 | 2,667 |
| Outside tiers | 2,787 | 2,279 |
| CAGR | 35.6% | 45.7% |
| h-index | 195 (Abstract) | 155 (Results) |
| Total citations | 245,388 (Abstract) | 168,407 (Results) |
| NTS papers | 3,134 (Abstract) | Referenced as Tier 3 |

**Root cause:** The detailed bibliometric analyses (citations, authors, journals, geography, NTS domains, LLM models, simulation types, keywords) were generated from the v3 dataset (10,417 papers) and were never re-executed on the final 12,645-paper dataset. Only publication trends, thematic clusters, and urology were re-run on the final dataset.

**Resolution required:** Either (a) re-run all analyses on the final 12,645-paper dataset and update all numbers, or (b) consistently frame the manuscript around the analysed corpus of 10,417 papers (with appropriate explanation of the metadata-completeness filter). Option (b) is implemented in the corrected sections below.

### 1.2 Specific Number Inconsistencies

| Location | Manuscript States | Source Table States | Discrepancy |
|----------|------------------|--------------------|----|
| Abstract: h-index | 195 | citation_summary: 155 | Mismatch; no table supports 195 |
| Abstract: total citations | 245,388 | citation_summary: 168,407 | Mismatch; no table supports 245,388 |
| Abstract: CAGR | 35.6% | pub_trends (v3): 45.7%; pub_trends (final): 35.6% | Abstract uses final; Results uses v3 |
| Abstract: "92.8% post-ChatGPT" | 92.8% | pub_trends (v3): 93.9%; pub_trends (final): ~92.8% | Abstract uses final; Results uses v3 |
| Introduction: "fifteen-fold" increase | Stated | Not directly verifiable | May not match either dataset |
| Introduction: CAGR 45.7% | 45.7% | v3 pub trends: 45.7% | Uses v3 number |
| Introduction: "Tier 1: 12,645 papers" | 12,645 | 12,645 is the TOTAL included, not Tier 1 | Tier 1 = 6,210; 12,645 = total |
| Results 3.1: "92,941 raw records" | 92,941 | Dedup report final2: 100,277 | Results uses wrong initial count |
| Results 3.1: "11.5% duplicates" | 11.5% | Dedup report final2: 13.6% | Results uses old dedup rate |
| Results 3.1: "81,001 unique" | 81,001 | Dedup report final2: 86,635 | Results uses old unique count |
| Results 3.1: "11,529 included" | 11,529 | Screened final2: 12,645 | Results uses old included count |
| Results 3.1: "10,417 with metadata" | 10,417 | descriptive_stats: 10,417 | Correct for v3 analysis |
| Results 3.2: "640 pre-ChatGPT" | 640 | pub_trends v3: 640; final: 906 | Uses v3 |
| Results 3.2: 2020 n=112 | 112 | pub_trends v3: 112; final: 194 | Uses v3 |
| Results 3.2: 2025 n=4,424 | 4,424 | pub_trends v3: 4,424; final: 5,211 | Uses v3 |
| Results 3.2: "42.5% in 2025" | 42.5% | v3: 4424/10412=42.5%; final: 5211/12634=41.2% | Uses v3 |
| Results 3.2: "4.5-fold 2022-2023" | 4.5x | v3: 1442/320=4.5x; final: 1793/426=4.2x | Uses v3 |
| Results 3.11: "291 urology papers" | 291 | urology_final: 319; urology_v3: 291 | Uses v3 |
| Results 3.11: "8 boot camp papers" | 8 | urology_final: 10; urology_v3: 8 | Uses v3 |
| Results 3.11: urology year counts | 15/40/97/118/21 | urology_v3: matches; urology_final: 17/44/103/129/26 | Uses v3 |
| Results 3.11: urology NTS counts | 67/46/35/22 | urology_v3: matches; urology_final: 74/51/35/25 | Uses v3 |
| Results 3.11: urology citations | 12.3, 3572 | urology_v3: 12.3; urology_final: 12.1, 3853 | Uses v3 |
| Results 3.11: urology LLM models | 135/41/29/22/11 | urology_v3: matches; urology_final: 145/44/33/26/12 | Uses v3 |
| Discussion: "54.5%" top 4 countries | 54.5% | Geo: USA+China+UK+Canada = 24.2+16.9+7.4+6.0 = 54.5% | Correct |
| Conclusions: "3,598 journals" | 3,598 | journal_summary: 3,598 | Correct for v3 |
| Results 3.7: Cluster descriptions | Mis-labelled | thematic_clusters_final: different cluster structure | Uses old v3 cluster data, not the final run |
| Methods: "3,316 definite includes" | 3,316 | v3 screening: 3,316; final2: 3,648 | Uses v3 |
| Methods: "69,472 definite excludes" | 69,472 | v3: 69,472; final2: 73,990 | Uses v3 |
| Methods: "8,213 uncertain" | 8,213 | v3: 8,213; final2: 8,997 | Uses v3 |

### 1.3 Introduction Error: Tier 1 vs Total

The Introduction states: "Tier 1: 12,645 papers." This is incorrect. 12,645 is the TOTAL included corpus across all tiers. Tier 1 alone is 6,210 papers. The sentence should read: "...the broadest intersection of LLMs and healthcare (12,645 papers total), through the addition of simulation-specific literature (Tier 2), to the most focused subset examining non-technical skills (Tier 3: 3,134 papers)."

### 1.4 Thematic Cluster Mismatch

The Results (Section 3.7) describe five clusters with labels like "simulation / generative / challenges" (Cluster 2), "patient / accuracy / tools" (Cluster 4), etc. However, the final thematic_clusters_20260322_215641.md table shows a completely different structure:

| Cluster | Final Table Label | Results Section Label |
|---------|------------------|-----------------------|
| 0 | "artificial intelligence / computer science / medicine" | Same |
| 1 | "artificial / intelligence / education" | "large language models / models / language" |
| 2 | "artificial intelligence / computer science / medicine" | "simulation / generative / challenges" |
| 3 | "models / large language models / language" | "artificial / intelligence / education" |
| 4 | "challenges / virtual reality / development" | "patient / accuracy / tools" |

The cluster labels, keyword counts, centrality, and density values in the Results are from the v3 analysis, not the final run. The final analysis shows THREE motor themes (clusters 0, 3, 4), not two, and TWO emerging/declining themes, not one basic + one niche.

### 1.5 Percentage Calculations Check

Where verifiable against source tables, percentages are calculated correctly within each dataset version:
- NTS: 1807/10417 = 17.35% (stated 17.3%) -- correct
- Communication: 1568/10417 = 15.05% (stated 15.1%) -- correct
- Geographic: 796/3294 = 24.2% -- correct
- Bradford zones: 2776/8296 = 33.5% -- correct
- Urology: 291/11529 = 2.5% -- correct within v3

---

## 2. LOGICAL FLOW

### 2.1 Strengths
- The Introduction effectively establishes three motivating observations that align with the study's objectives.
- The three-tier framework is well explained and logically structured.
- The Discussion moves beyond describing results to interpreting their implications, particularly the NTS gap analysis (Section 4.2) and the open-source deficit (Section 4.3).
- The urology boot camp argument is specific and actionable.

### 2.2 Weaknesses

**Introduction promises vs Results delivery:**
- The Introduction sets up four objectives. Objectives 1-3 are well addressed. Objective 4 (replicable pipeline) is mentioned but not analysed as a result -- it is more of a methodological claim.
- The Introduction mentions "companion studies" (Delphi, scoping review, Simuro platform) but this is never picked up in the Discussion. Either integrate these or remove the reference.

**Discussion gaps:**
- Section 4.1 largely restates the Results rather than interpreting them. The five-point summary is useful structurally but several points merely repeat numbers without adding analytical value.
- The Discussion does not engage with **why** the CAGR is as high as it is relative to other technology adoption curves. The claim that it "exceeds the typical diffusion curves" in Section 3.2 is unsupported by specific comparisons.
- There is no discussion of **document types** -- the corpus includes preprints (8.6%), books, dissertations, and editorials. This has implications for evidence quality that should be addressed.
- The Discussion does not interpret the keyword co-occurrence findings beyond cluster descriptions. What do the dominant co-occurrence pairs (AI + computer science, computer science + medicine) tell us about the intellectual structure?

**Conclusions:**
- Generally well supported by findings but introduce no new synthesis beyond what the Discussion provides. The five recommendations are practical and appropriate.
- The concluding paragraph could more forcefully articulate the study's unique contribution.

---

## 3. ACADEMIC QUALITY

### 3.1 Writing Quality
The writing is generally at journal-submission standard. The prose is clear, well-structured, and maintains appropriate academic register throughout. Sentence construction is varied and effective. The paper reads as a polished draft that is close to submission-ready pending the numerical corrections.

### 3.2 Issues Requiring Attention

**Hedging and claims:**
- "extraordinary expansion" (Discussion 4.1) -- slightly hyperbolic for academic prose; consider "rapid and substantial expansion"
- "explosively growing" (Abstract conclusions) -- informal; consider "rapidly expanding"
- "genuine promise" (Conclusions final para) -- appropriate hedging
- "urgent need" (Abstract background) -- acceptable but strong
- "ideally suited" (Discussion 4.4) -- should be hedged to "potentially well suited"

**Passive vs active voice:**
- Appropriately balanced. Methods use passive (standard). Discussion uses active voice for interpretive claims ("We argue," "We contend"). This is well done.

**Informal phrases to revise:**
- "pretty much" -- not found (good)
- "the very pace" (Introduction) -- slightly informal; acceptable
- "notable precisely for its absence" (Discussion 4.4) -- effective rhetorical device but may read as too literary for some journals
- "still in its early chapters" (Discussion 4.8 closing) -- metaphorical; consider "still in an early stage of development"

**Consistency issues:**
- British spellings used throughout ("characterised," "recognised," "practise") -- consistent and appropriate for UK-based authors
- "Standardized Patient" uses American spelling in Results 3.10 while the rest uses British spelling. Should be "Standardised Patient" for consistency.
- "ChatGPT" is referred to as both a model and a generic label. This dual usage should be explicitly noted when first introduced.

### 3.3 Structural Quality
- The Methods section is exemplary in its detail and transparency, particularly regarding AI-assisted screening.
- The Results section is well organised into discrete subsections covering all major analyses.
- The Discussion would benefit from consolidation. Eight subsections (4.1-4.8) is excessive; consider merging 4.1 with 4.2 and 4.5 with 4.6.

---

## 4. MISSING CONTENT

### 4.1 Important Findings Not Discussed
- **Document type distribution:** The corpus includes 8.6% preprints, 2.5% book chapters, 1.9% proceedings articles. This has significant implications for evidence quality but is not discussed.
- **Open-access rate of 76.7%:** This finding is reported but not interpreted. It is remarkably high and relevant to the paper's open-access thesis.
- **Median publication year of 2025:** Mentioned once but the implications (extreme recency, lack of citation maturity) deserve more emphasis.
- **The top citation being a 2022 preprint** (Kung et al. is dated 2022 in the table but described as 2023 in the text): This date discrepancy should be investigated and the citation corrected.
- **Data completeness disparities:** Journal data available for only 65.5% of papers significantly limits the Bradford's law analysis. This should be stated explicitly as a limitation of the journal analysis specifically, not just mentioned in passing.

### 4.2 Limitation Section Assessment
The limitations section is generally comprehensive but could be strengthened by adding:
- The limitation of regex-based NTS classification (mentioned) could note the specific false-positive risk -- "leadership" may capture papers about hospital leadership unrelated to NTS.
- The impossibility of validating AI screening decisions for the full 8,997 uncertain papers (only 100 per reviewer were sampled).
- The potential for language bias -- only English-language papers were included, excluding substantial non-English LLM research from China, Japan, South Korea, and European countries.
- The inability to assess study quality or risk of bias (inherent to bibliometric design but should be stated).
- The limitation that highly prolific Chinese-affiliated authors (top 20) may reflect name disambiguation challenges rather than true individual productivity.

### 4.3 Urology Section Depth
The urology sub-analysis is reasonably detailed but could be strengthened by:
- Comparing urology's adoption curve to other surgical specialties (if data available).
- Noting which specific urological applications dominate (e.g., prostate cancer diagnosis vs. surgical training vs. patient counselling).
- Addressing whether the zero boot camp finding might reflect terminology -- "boot camp" may not be universally used.

### 4.4 Missing Methodological Detail
- The kappa values from the IRR validation are not reported. The Methods describe the sampling strategy but never report the actual agreement statistics.
- The total number of papers included from AI screening (Stage 2) is not reported separately from Stage 1 includes.
- The threshold for "uncertain" classification in Stage 1 is described but the exact cut-off between "uncertain" and "exclude" is ambiguous.

---

## 5. CITATION GAPS

### 5.1 Placeholder Audit
No (Author, Year) placeholders were found in the manuscript -- all in-text citations appear to reference specific named works with years. This is satisfactory.

### 5.2 Claims Needing Citations That Lack Them

| Claim | Location | Needed |
|-------|----------|--------|
| "LLMs...moved from curiosity to consequential tool" | Introduction para 1 | Potentially a general claim, but a citation for institutional adoption rates would strengthen it |
| "failures in NTS implicated in a significant proportion of adverse events" | Section 1.2 | Reason, 2000 and Catchpole et al., 2008 are cited -- adequate |
| "growing overlap between OpenAlex and these sources" | Discussion 4.7 | Priem et al., 2022 is cited -- adequate |
| "exceeds the typical diffusion curves observed for other health technology innovations" | Results 3.2 | No citation provided for the comparison diffusion curves -- needs a reference |
| "a compound annual growth rate of 45.7%" attributed to "present study" | Introduction | Acceptable self-reference but the number does not match the final dataset (35.6%) |
| "human-comparable screening accuracy" | Methods 2.4.2 | Matsui et al., 2024; Sanghera et al., 2025; Insuk et al., 2025 cited -- adequate |
| "boot camps are an established training format" | Discussion 4.4 | No citation for urology boot camps specifically -- needs a reference (e.g., Golnari et al., Ahmed et al., or similar) |
| "its adaptation from aviation by Gaba and colleagues" | Discussion 4.2 | Gaba et al., 2001 cited -- adequate |
| RAISE recommendations "Version 2, 2025" | Methods 2.4.2 | Needs full citation details |

### 5.3 Citation Density
The Introduction has appropriate citation density (2-3 per paragraph). The Methods are well cited for frameworks and guidelines. The Discussion could benefit from more contextual citations comparing findings to other bibliometric studies in related fields.

### 5.4 Citation Date Discrepancy
The most-cited paper (Kung et al.) is listed as 2022 in the citation_top20 table (DOI: 10.1101/2022.12.19.22283643, which is a medRxiv preprint dated 2022) but is referred to as "Kung et al., 2023" in the text. The published journal version may be 2023, but the DOI is a 2022 preprint. This should be verified and made consistent.

---

## 6. FIGURE/TABLE REFERENCES

### 6.1 Figures Available (30 total)

1. prisma_flow.png -- PRISMA flow diagram
2. publication_trends.png -- Annual publication counts
3. cumulative_growth.png -- Cumulative growth curve
4. citation_distribution.png -- Citation distribution
5. citations_by_year.png -- Citations stratified by year
6. source_database_distribution.png -- Database contribution
7. tier_distribution.png -- Tier distribution
8. document_type_distribution.png -- Document types
9. data_completeness.png -- Metadata completeness
10. top_countries.png -- Geographic distribution (countries)
11. continent_distribution.png -- Continental distribution
12. top_keywords.png -- Keyword frequencies
13. keyword_cooccurrence_network.png -- Co-occurrence network
14. keyword_wordcloud.png -- Keyword word cloud
15. author_productivity.png -- Author productivity distribution
16. lotkas_law.png -- Lotka's law fit
17. top_authors.png -- Top 20 authors
18. collaboration_index.png -- Collaboration patterns
19. top_journals.png -- Top 20 journals
20. bradford_law.png -- Bradford's law zones
21. publication_types.png -- Publication type distribution
22. llm_model_frequencies.png -- LLM model frequencies
23. llm_proprietary_vs_opensource.png -- Proprietary vs open-source
24. llm_model_trends.png -- LLM temporal trends
25. simulation_type_frequencies.png -- Simulation modality frequencies
26. simulation_nts_crosstab.png -- Simulation x NTS cross-tabulation
27. strategic_diagram.png -- Callon's strategic diagram
28. nts_domain_frequencies.png -- NTS domain frequencies
29. nts_domain_year_heatmap.png -- NTS temporal heatmap
30. urology_trends.png -- Urology publication trends

### 6.2 Figures Referenced in the Manuscript Text

The manuscript references the following figures:
- Figure 1 (PRISMA flow) -- Section 2.4, 3.1
- Figure 2 (publication trends) -- Section 3.2
- Figure 3 (Bradford's law) -- Section 3.5
- Figure 4 (geographic) -- Section 3.6
- Figure 5 (strategic diagram) -- Section 3.7
- Figure 6 (NTS domains) -- Section 3.8
- Figure 7 (LLM models) -- Section 3.9
- Figure 8 (simulation types) -- Section 3.10

**Only 8 of 30 figures are referenced.** The remaining 22 are unreferenced.

### 6.3 Recommended Figure Allocation

**Main text (8-10 figures recommended):**

1. **Figure 1: PRISMA flow diagram** (prisma_flow.png) -- Essential for reporting
2. **Figure 2: Publication trends** (publication_trends.png) -- Core result
3. **Figure 3: NTS domain frequencies** (nts_domain_frequencies.png) -- Key finding, visually compelling
4. **Figure 4: Callon's strategic diagram** (strategic_diagram.png) -- Central to science mapping
5. **Figure 5: LLM model frequencies** (llm_model_frequencies.png) -- Key finding
6. **Figure 6: Proprietary vs open-source** (llm_proprietary_vs_opensource.png) -- Striking visual
7. **Figure 7: Bradford's law** (bradford_law.png) -- Classic bibliometric analysis
8. **Figure 8: Geographic distribution** (top_countries.png) -- Important for equity argument
9. **Figure 9: Simulation x NTS cross-tabulation** (simulation_nts_crosstab.png) -- Novel contribution
10. **Figure 10: Urology trends** (urology_trends.png) -- Supports sub-analysis

**Supplementary figures (remaining 20):**
- cumulative_growth.png, citation_distribution.png, citations_by_year.png
- source_database_distribution.png, tier_distribution.png
- document_type_distribution.png, data_completeness.png
- continent_distribution.png, top_keywords.png
- keyword_cooccurrence_network.png, keyword_wordcloud.png
- author_productivity.png, lotkas_law.png, top_authors.png
- collaboration_index.png, top_journals.png
- publication_types.png, llm_model_trends.png
- simulation_type_frequencies.png, nts_domain_year_heatmap.png

### 6.4 Tables Referenced
The manuscript references Tables 1-14 but these are not defined as formal tables in the text. Each should be formatted as a numbered table with title and notes. The mapping should be:

- Table 1: Publication trends by year
- Table 2: Citation summary statistics
- Table 3: Top 20 most-cited papers
- Table 4: Author analysis summary
- Table 5: Top 20 most prolific authors
- Table 6: Journal analysis summary
- Table 7: Bradford's law zones
- Table 8: Geographic distribution (top 20 countries)
- Table 9: Thematic cluster summary
- Table 10: NTS domain classification
- Table 11: Simulation type x NTS cross-tabulation
- Table 12: LLM model classification
- Table 13: Simulation type classification
- Table 14: Urology sub-analysis summary

---

## 7. OVERALL ASSESSMENT

### Strengths
1. Ambitious scope and timely topic
2. Novel open-access methodology with reproducibility by design
3. Strong three-tier analytical framework
4. Practical, actionable findings (NTS gaps, urology boot camp opportunity)
5. Well-structured argumentation
6. Excellent writing quality at near-submission standard
7. Comprehensive limitation section

### Weaknesses Requiring Revision
1. **CRITICAL:** Pervasive numerical inconsistency between sections (two-dataset problem)
2. **MAJOR:** Thematic cluster descriptions do not match final analysis tables
3. **MAJOR:** CAGR inconsistency (35.6% vs 45.7% used in different locations)
4. **MAJOR:** Introduction incorrectly equates Tier 1 with total corpus (12,645)
5. **MODERATE:** Inter-rater reliability results not reported
6. **MODERATE:** 22 of 30 figures unreferenced
7. **MODERATE:** Missing discussion of document type composition and evidence quality
8. **MINOR:** Spelling inconsistency (Standardized vs Standardised)
9. **MINOR:** Some claims lack supporting citations

### Recommendation
**Major revision required.** The numerical inconsistencies must be resolved before the paper can proceed to formal peer review. The corrected sections provided below align the manuscript consistently with the analysed dataset while acknowledging the full included corpus. All other issues identified above should also be addressed.

---

## CORRECTED SECTIONS

Corrected versions of the Results, Discussion, and Conclusions sections have been saved to 04_manuscript/sections/, resolving the numerical inconsistencies by:

1. Aligning all numbers with the final 12,645-paper included corpus where final-dataset tables exist (publication trends, thematic clusters, urology)
2. Clearly framing the analytical subset (those papers with sufficient metadata) where only v3 tables are available, noting the analytical corpus size alongside the total included corpus
3. Correcting the CAGR to 35.6% throughout (matching the final dataset)
4. Correcting the Introduction's Tier 1 error
5. Updating the thematic cluster descriptions to match the final analysis tables
6. Updating the urology sub-analysis to the final dataset numbers
7. Adding missing discussion of document types and evidence quality
8. Standardising British spelling throughout
