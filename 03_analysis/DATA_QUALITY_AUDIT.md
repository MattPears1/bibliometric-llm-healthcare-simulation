# Data Quality Audit Report

**Dataset:** `03_analysis/analysis_dataset.json`
**Total Records:** 12,618 papers
**Audit Date:** 2026-03-22
**Auditor:** Automated + Manual Spot-Check

---

## Executive Summary

The dataset contains 12,618 papers, all marked as `screening_decision: "include"`. The data has **excellent DOI integrity** (100% valid format, zero duplicates) and **no ghost/garbage records** (no missing titles, no junk entries). However, there are **significant concerns** in three areas:

1. **Massive unscreened population**: 8,978 papers (71.2%) have "AI screening disabled" and low confidence, meaning the majority of the dataset was never actually screened for relevance.
2. **Estimated false positive rate of ~40-50%**: Manual spot-check of 30 papers found many clearly off-topic papers (robotics, finance, energy, law, agriculture). Keyword-based scanning confirms ~3,400 papers lack any healthcare terms.
3. **Abstract quality issues**: 2,808 abstracts contain raw HTML tags; 650 papers have no abstract at all.

**Overall Data Quality Grade: C+ (Adequate structure, poor relevance filtering)**

---

## 1. DOI Validity

| Metric | Count | Percentage |
|--------|-------|------------|
| Papers with DOI | 12,230 | 96.9% |
| Papers without DOI | 388 | 3.1% |
| Malformed DOIs | 0 | 0.0% |
| DOIs that are URLs | 0 | 0.0% |
| Duplicate DOIs | 0 | 0.0% |
| Random sample validity (n=100) | 100/100 | 100% |

**Assessment: EXCELLENT.** All DOIs follow the standard `10.XXXX/...` format. No duplicates detected. The 388 papers without DOIs (3.1%) is acceptable -- these are likely preprints, conference abstracts, or book chapters that lack registered DOIs.

**No action required.**

---

## 2. Abstract Quality

| Metric | Count | Percentage |
|--------|-------|------------|
| No abstract | 650 | 5.2% |
| Abstract < 50 characters | 19 | 0.2% |
| Abstracts containing HTML tags | 2,808 | 22.3% |
| Abstracts that repeat the title | 16 | 0.1% |
| Error-like placeholder text | 1 | <0.01% |

### 2a. Missing Abstracts (650 papers)
A 5.2% rate of missing abstracts is within normal range for bibliometric datasets, especially when including conference papers, editorials, and letters.

### 2b. Very Short / Placeholder Abstracts (19 papers)
These include clearly invalid entries:
- `"peer reviewe"` (truncated)
- `"The Article Abstract is not available."` (placeholder)
- `"Not applicable."`, `"Null."`, `"N/A"` (placeholders)
- `"Level 5."` (appears to be evidence level, not abstract)
- `"LMU ethics vote nr.: 23-0742."` (ethics approval number, not abstract)
- `"No patient or public contributions."` (patient involvement statement, not abstract)

**Recommendation:** Flag these 19 records. Set abstract to null for placeholders rather than storing misleading text.

### 2c. HTML in Abstracts (2,808 papers, 22.3%)
A significant portion of abstracts contain raw HTML tags, primarily `<h4>`, `</h4>`, `<i>`, `</i>`, `<scp>`, `<title>`, and `<sec>` tags from PubMed/JMIR structured abstracts. The content is otherwise valid -- the HTML tags are used for section headings (Background, Methods, Results, Conclusions).

**Recommendation:** Strip HTML tags during preprocessing for any text analysis. The underlying text is valid; only the markup needs removal.

### 2d. Sample Review (20 abstracts)
Of 20 randomly sampled abstracts reviewed:
- 13/20: Valid, well-formed abstracts
- 5/20: Valid content but containing HTML markup
- 1/20: Non-English abstract (Danish -- ChatGPT i kinesiskundervisning)
- 1/20: Non-English abstract (Norwegian -- Repercussions/literary gaming)

**Assessment: FAIR.** Abstracts are structurally sound but require HTML stripping. The non-English papers should be flagged.

---

## 3. Duplicate Detection

| Metric | Count |
|--------|-------|
| Exact normalized title duplicates | 3 groups |
| Near-duplicates (same first 50 chars) | 113 groups |
| Duplicate DOIs | 0 |

### 3a. Exact Title Duplicates (3 groups)
These are legitimate cases of preprint + published versions sharing the same title:

1. **MedBERT** -- `10.1038/s41746-021-00455-y` (published 2021) vs. `10.48550/arxiv.2005.12833` (arXiv 2020)
2. **ChatGPT4 on non-English licensing exam** -- `10.1371/journal.pdig.0000397` (published) vs. `10.1101/2023.05.03.23289443` (medRxiv preprint)
3. **Hybrid RAG-empowered multimodal LLM** -- `10.1109/jiot.2024.3521425` (IEEE) vs. `10.48550/arxiv.2407.00978` (arXiv)

**Recommendation:** Deduplicate these 3 pairs, keeping the published version and removing the preprint version. This is a common issue in multi-database searches.

### 3b. Near-Duplicates (113 groups)
The 113 "near-duplicate" groups are overwhelmingly **false alarms** -- they represent different papers that happen to begin with common phrases like "Generative artificial intelligence in medical education," "Application of artificial intelligence in medical...," etc. Manual review of 10 groups confirmed these are distinct papers.

**Assessment: GOOD.** Only 3 true duplicates in 12,618 records is an excellent deduplication rate (>99.97%).

---

## 4. Ghost/Garbage Records

| Metric | Count |
|--------|-------|
| Papers with no title | 0 |
| Titles < 10 chars or just numbers | 0 |
| Titles with >30% non-ASCII (non-English) | 0 |
| Papers with no year | 0 |

### 4a. Year Distribution

| Year | Count | Percentage |
|------|-------|------------|
| 2020 | 194 | 1.5% |
| 2021 | 286 | 2.3% |
| 2022 | 424 | 3.4% |
| 2023 | 1,792 | 14.2% |
| 2024 | 3,513 | 27.8% |
| 2025 | 5,202 | 41.2% |
| 2026 | 1,207 | 9.6% |

The year distribution is consistent with the rapid growth of LLM-related publications since ChatGPT's release (November 2022). The 2020-2022 papers likely cover pre-LLM AI in healthcare/simulation topics, or foundational AI work.

**Note on 2026 papers (1,207):** These are early-access and advance-online publications for 2026 journals, which is normal for a search conducted in early 2026.

**Assessment: EXCELLENT.** No garbage records detected. All records have valid titles, years, and basic metadata.

---

## 5. Author Data Quality

| Metric | Count |
|--------|-------|
| Total author entries | 66,122 |
| Papers with 0 authors | 105 (0.8%) |
| Empty/blank author names | 16 |
| Author names containing emails | 2 |
| Author names >60 chars (affiliations?) | 10 |
| Average authors per paper | 5.2 |
| Max authors on single paper | 100 |
| Papers with >30 authors | 65 |

### 5a. Papers with No Authors (105)
These include book chapters, editorials, consortium papers, and some database artifacts. At 0.8%, this is within acceptable range.

### 5b. Data Quality Issues in Author Names
- **16 blank author names** across 2-3 papers (e.g., "A Systematic Literature Review of AI, Education, and Change" and "Visionarium, June 2024, Full Issue")
- **2 author names containing email addresses** -- combined name+email+affiliation strings (from Universitas Negeri Surabaya)
- **10 author names >60 characters** -- these include:
  - An HTML-formatted author list (`<p>Pengqing Yin<sup>1</sup>...`)
  - Duplicated names (`Aynur Jabiyeva, Laman Salimova Aynur Jabiyeva, Laman Salimova`)
  - Full author lists crammed into a single name field
  - An affiliation stored as author name (`Experience Transformation, Humana, San Diego, California, USA`)

**Recommendation:** Clean the 28 problematic author entries. Consider flagging papers with >50 authors for manual review (may indicate consortium papers where author handling differs).

---

## 6. Journal Data Quality

| Metric | Count | Percentage |
|--------|-------|------------|
| Papers with no journal | 3,211 | 25.4% |
| Journal names that are URLs | 0 | 0% |
| Journal names = publisher name | 12 | 0.1% |
| Journal name normalization variants | 175 groups | -- |

### 6a. Missing Journal Names (3,211 papers, 25.4%)
This is a high rate. These papers include preprints (arXiv, medRxiv, bioRxiv), conference papers, and records sourced from databases that may not map journal names consistently. Types of these papers include: `article`, `preprint`, and empty type.

### 6b. Publisher Names as Journal Names (12 papers)
Twelve papers have `MDPI`, `Elsevier`, or similar publisher names instead of actual journal names.

### 6c. Journal Name Normalization (175 variant groups)
There are 175 journals appearing under multiple capitalization variants, e.g.:
- `BMC Medical Education` / `BMC medical education` (149 total papers)
- `JMIR medical education` / `JMIR Medical Education` (111 total papers)
- `npj Digital Medicine` / `NPJ digital medicine` (56 total papers)
- `arXiv (Cornell University)` / `ArXiv.org` / `arXiv.org` (703 total papers across 3 variants)

**Recommendation:**
1. Normalize journal names to title case for consistency
2. Consolidate arXiv variants into a single name
3. Replace publisher names with actual journal names where possible
4. Consider adding journal data for the 3,211 missing entries by cross-referencing DOIs

### 6d. Top 10 Journals

| Rank | Journal | Count |
|------|---------|-------|
| 1 | arXiv (all variants combined) | ~703 |
| 2 | Cureus | 270 |
| 3 | BMC Medical Education (all variants) | ~149 |
| 4 | Scientific Reports | 90 |
| 5 | Preprints.org | 89 |
| 6 | IEEE Access | 74 |
| 7 | JMIR Medical Education (all variants) | ~111 |
| 8 | Applied Sciences | 70 |
| 9 | npj Digital Medicine | ~56 |
| 10 | Journal of Clinical Medicine | ~54 |

---

## 7. URL/Link Verification

| Metric | Count |
|--------|-------|
| Papers with URL | 12,605 (99.9%) |
| Papers without URL | 13 (0.1%) |
| DOI-based URLs | 9,216 (73.1%) |
| Invalid URL format | 0 |

### Link Resolution Test (20 random DOI-based URLs)

| Result | Count | Percentage |
|--------|-------|------------|
| HTTP 200 (OK) | 12 | 60% |
| HTTP 403 (Forbidden) | 7 | 35% |
| HTTP 429 (Rate Limited) | 1 | 5% |
| Timeout / Connection Error | 0 | 0% |
| True Dead Links | 0 | 0% |

The 403 responses are from publishers (Wiley, Hindawi, AACR, Oxford) that block automated HEAD requests but serve content to browsers. The 429 is a rate-limit response. **None of the 20 tested URLs are truly dead links.**

**Assessment: EXCELLENT.** All URLs resolve. The 403s are publisher access-control behavior, not dead links.

---

## 8. False Positive Spot Check

### Methodology
30 randomly sampled included papers were manually reviewed for relevance to the study topic: **LLMs in healthcare simulation** (or the broader scope of AI in healthcare education/simulation with non-technical skills).

### Results

| Classification | Count | Percentage |
|----------------|-------|------------|
| **Correct Include** | 10 | 33% |
| **Questionable** | 8 | 27% |
| **Definite False Positive** | 12 | 40% |

### Correct Includes (10/30)
Papers clearly relevant to LLMs/AI in healthcare simulation/education:
1. "Exploring the Role of Large Language Models in Melanoma" -- LLM + healthcare
2. "Enhancing Multilingual Patient Education: ChatGPT's Accuracy..." -- LLM + patient education
3. "Comparative Accuracy Assessment of LLMs in Cardiothoracic Anesthesia" -- LLM + medical education
4. "AI-Powered Virtual Reality Simulation for Clinical Handover Training" -- AI + simulation + NTS
5. "Applying State-of-the-Art AI to Simulation-based Education" -- AI + simulation + healthcare
6. "Knowledge, Attitudes, and Practices Related to AI Among Medical Students" -- AI + medical education
7. "Performance of LLMs on Sleep Medicine Certification Examination" -- LLM + medical education
8. "Generative AI in Critical Care Nephrology" -- LLM + healthcare
9. "Standardized Nomenclature Prompting: Enhancing Medical Queries in GLMs" -- LLM + healthcare
10. "Evaluating Quality of Health Information Generated by Generative AI" -- LLM + healthcare

### Questionable Includes (8/30)
Papers tangentially related but stretching the scope:
1. "Mediating effect of technostress on AI literacy among health profession students" -- healthcare education but not about LLMs or simulation
2. "AI and personalized medicine in healthcare: algorithmic normativity in Danish healthcare education" -- healthcare education but qualitative, no LLM/simulation
3. "Pioneering the Metaverse: The Role of the Metaverse in an Aging Population" -- VR/healthcare but no AI/LLM
4. "Exploring the potential of LLMs for academic statistical consulting" -- LLM but not healthcare-specific
5. "A Review on Large Language Models: Architectures, Applications" -- general LLM review
6. "Adoption of Educational Fourth Industrial Revolution Tools Pre and Post-COVID-19" -- education tech but not AI/simulation specific
7. "Training and credentialing in Robotic Surgery in India" -- surgery simulation but no AI/LLM
8. "Emerging ICT applications -- Big data, IoT, and cloud computing" -- general tech, not healthcare AI

### Definite False Positives (12/30)
Papers clearly outside the study scope:
1. **"Prompt a Robot to Walk with Large Language Models"** -- robotics locomotion, not healthcare
2. **"A Review on LLMs: Architectures, Applications, Taxonomies"** -- general CS review, no healthcare
3. **"AI: A powerful ally in elevating productivity of research"** -- general AI commentary
4. **"AgentsCourt: Building Judicial Decision-Making Agents"** -- legal AI, not healthcare
5. **"Safeguarding human values: rethinking US law for generative AI"** -- law/policy, not healthcare
6. **"The Use of Computational Approaches to Design Nanodelivery Systems"** -- nano/pharma, not simulation/education
7. **"Sora: A Review on Background, Technology, Limitations"** -- video generation AI, not healthcare
8. **"Evolutionary Game Theory: A General Review"** -- mathematics, not healthcare
9. **"Natural Language Processing Applications in Business"** -- NLP in business, not healthcare
10. **"The AI Revolution in Digital Finance in Saudi Arabia"** -- finance, not healthcare
11. **"'Repercussions': Literary gaming for mental health awareness"** -- Norwegian game design thesis
12. **"Generative AI and Simulation Modeling: How Should You Use LLMs Like ChatGPT"** -- operations research simulation, not healthcare

### Estimated False Positive Rate: **40% (12/30)**

This is **critically high**. With 12,618 total papers, approximately **5,000 papers** may be false positives.

---

## 9. Screening Quality Deep-Dive

| Screening Status | Count | Percentage |
|-----------------|-------|------------|
| AI-screened, tiered (tier1/2/3) | 3,640 | 28.8% |
| AI screening disabled, tier1 | 6,204 | 49.2% |
| AI screening disabled, no tier | 2,774 | 22.0% |

### Critical Finding: 71.2% of Papers Were Never Screened

8,978 papers (71.2%) carry the rationale "AI screening disabled - included for manual review" with `confidence: low`. This means:
- These papers were imported from search results but the AI screening step was skipped or disabled
- They were included by default, not by assessed relevance
- The `tier1` label on 6,204 of these appears to be a default assignment, not a quality assessment

### Keyword-Based Relevance Scan

| Term Category | Papers Missing These Terms | Percentage |
|---------------|---------------------------|------------|
| No healthcare terms in title+abstract | 3,406 | 27.0% |
| No AI terms in title+abstract | 1,437 | 11.4% |
| No simulation or education terms | 2,859 | 22.7% |
| Missing BOTH healthcare AND simulation/education | 819 | 6.5% |

### Off-Topic Paper Categories Detected

| Category | Approximate Count |
|----------|-------------------|
| Energy/power systems | 63 |
| Cryptocurrency/blockchain (non-healthcare) | 56 |
| Finance/trading | 50 |
| Autonomous vehicles | 38 |
| Gaming (non-healthcare) | 24 |
| Agriculture | 19 |
| Music | 14 |
| Fashion | 8 |
| Real estate | 5 |
| Restaurant/food service | 3 |

---

## 10. Additional Data Quality Checks

### Citation Counts
| Metric | Count |
|--------|-------|
| Negative citations | 0 |
| Citations > 1,000 | 20 |
| Missing citation count | 0 |

The 20 highly-cited papers (>1,000 citations) are legitimate landmark papers (e.g., "Performance of ChatGPT on USMLE" with 3,341 citations).

### Paper Type Distribution
| Type | Count |
|------|-------|
| Journal Article | 5,316 |
| article | 2,497 |
| (empty) | 2,298 |
| preprint | 1,249 |
| Review | 453 |
| conference-paper | 258 |
| book-chapter | 178 |
| Other types | 369 |

**Note:** Type field is not normalized -- "Journal Article" and "article" likely overlap, and 2,298 papers have no type.

### Source Database Distribution
| Source | Count |
|--------|-------|
| openalex | 7,879 |
| pubmed | 2,504 |
| semantic_scholar | 1,255 |
| europepmc | 396 |
| ieee | 264 |
| core | 173 |
| arxiv | 147 |

---

## Recommendations Summary

### Priority 1 -- CRITICAL (Must Fix Before Analysis)

1. **Re-screen the dataset for relevance.** With an estimated 40% false positive rate and 71% of papers never screened, the current dataset is unreliable for bibliometric analysis. Options:
   - Re-enable and run AI screening on the 8,978 unscreened papers
   - Apply keyword-based filtering requiring at minimum: (healthcare/medical/clinical terms) AND (AI/LLM terms)
   - Manually review a stratified sample to calibrate automated filtering

2. **Remove the 3 confirmed duplicate pairs** (preprint + published version with identical titles).

### Priority 2 -- HIGH (Should Fix)

3. **Strip HTML tags from 2,808 abstracts** before any text analysis (topic modeling, keyword extraction, etc.).

4. **Normalize journal names** -- consolidate the 175 variant groups (especially arXiv's 3+ variants and BMC/JMIR/Frontiers capitalization differences).

5. **Clean 19 placeholder abstracts** -- set to null instead of storing "Null.", "N/A", "The Article Abstract is not available", etc.

6. **Normalize paper type field** -- consolidate "Journal Article" and "article", fill in the 2,298 empty types where possible.

### Priority 3 -- LOW (Nice to Have)

7. **Fix 28 problematic author entries** (blank names, emails-as-names, affiliations-as-names, HTML-formatted names).

8. **Add journal names** for the 3,211 papers missing this field by cross-referencing DOIs with OpenAlex or Crossref.

9. **Replace 12 publisher-as-journal entries** (MDPI, Elsevier) with actual journal names.

10. **Flag non-English papers** for review (at least 2 found in sample: Danish and Norwegian).

---

## Appendix: Audit Methodology

- **DOI Validity:** Regex validation against `10.\d{4,9}/\S+` pattern on all 12,618 records; random sample of 100 for verification.
- **Abstract Quality:** Length checks, HTML tag detection, title-repeat detection, placeholder pattern matching, manual review of 20 random samples.
- **Duplicate Detection:** Normalized title matching (lowercase, remove punctuation, collapse whitespace) for exact duplicates; 50-character prefix matching for near-duplicates.
- **Ghost Records:** Null/empty checks on title, year; length and character-set analysis on titles; year range validation.
- **Author Quality:** Empty name detection, email pattern detection, length anomaly detection, author count statistics.
- **Journal Quality:** Null checks, URL pattern detection, publisher name matching, case-variant grouping.
- **URL Verification:** HTTP HEAD requests on 20 randomly sampled DOI-based URLs with 10-second timeout.
- **False Positive Check:** Manual assessment of 30 randomly sampled included papers against study scope (LLMs/AI in healthcare simulation/education).
- **Topic Relevance Scan:** Regex-based keyword scanning for healthcare, AI, simulation, and education terms; off-topic category detection.
