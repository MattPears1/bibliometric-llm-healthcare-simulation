# 2. Methods

## 2.1 Study Design

This study employed a bibliometric analysis following established methodological frameworks (Donthu et al., 2021; Aria and Cuccurullo, 2017). The design was governed by two foundational principles: analytical rigour consistent with bibliometric best practice, and complete reproducibility using exclusively free, open-access data sources. The entire pipeline---data collection, processing, screening, and analysis---is publicly available on GitHub, enabling any researcher to replicate or update the study. Reporting followed PRISMA 2020 guidelines (Page et al., 2021), adapted for bibliometric analysis, and the PRISMA-trAIce checklist for transparent reporting of AI use in evidence synthesis (Holst et al., 2025).

## 2.2 Data Sources and Search Strategy

Seven electronic databases were systematically searched: OpenAlex, PubMed (via NCBI E-utilities), Europe PMC, Crossref, Semantic Scholar, CORE, and the Directory of Open Access Journals (DOAJ). These sources were selected for their complementary coverage of biomedical, clinical, and educational literature; free API access without institutional subscriptions; and sufficient metadata richness for bibliometric computation. The proprietary databases Web of Science and Scopus were deliberately excluded in favour of this open-access approach; the implications are addressed in the limitations.

A three-tier search strategy was employed to capture the full breadth of the literature while permitting analysis at increasing specificity:

- **Tier 1 (broadest):** LLM and generative AI terms combined with healthcare and medical terms.
- **Tier 2 (intermediate):** Tier 1 terms combined with simulation-specific terminology (e.g., simulation, virtual patient, debriefing, OSCE).
- **Tier 3 (focused):** Tier 2 terms combined with non-technical skills terminology (e.g., communication, teamwork, leadership, decision-making, situational awareness, crisis resource management).

A total of 35 query strategies were executed across the seven sources. PubMed queries employed MeSH terms and title-abstract field tags. OpenAlex and Semantic Scholar used full-text and topic-level search filters. The remaining databases used keyword-based search adapted to their respective API capabilities. The complete query strings are provided in Supplementary Appendix A. The search was restricted to English-language publications from January 2020 to March 2026, with the start date selected to capture the pre-LLM baseline period prior to GPT-3 (June 2020) and ChatGPT (November 2022).

## 2.3 Data Processing

Records from the seven databases were normalised to a common schema encompassing title, authors, year, DOI, abstract, journal, keywords, citation count, document type, and open-access status. Source-specific identifiers were retained for provenance tracking.

A three-stage deduplication algorithm was applied: exact DOI matching; fuzzy title matching (threshold of 90 on a 0--100 scale via the RapidFuzz library); and a fallback using author surname, publication year, and title fragment matching. When duplicates were identified, a source priority hierarchy (PubMed, OpenAlex, Europe PMC, Crossref, Semantic Scholar, CORE, DOAJ) determined which record was retained. The initial search yielded 100,277 records. After removing 13,642 duplicates (9,447 DOI-matched, 4,127 title-matched, 68 author-year-matched), 86,635 unique records remained (13.6% deduplication rate).

## 2.4 Screening Process

### 2.4.1 Stage 1: Keyword Pre-filter

Automated keyword matching across four categories (LLM, simulation, NTS, and medical terms) classified each paper as a definite include (at least five cross-category matches with at least one LLM term), definite exclude (zero LLM terms), or uncertain. This yielded 3,648 definite includes, 73,990 definite excludes, and 8,997 uncertain cases.

### 2.4.2 Stage 2: AI-Assisted Screening

Uncertain papers were screened using Claude (Anthropic, claude-sonnet-4-20250514), following PRISMA-trAIce (Holst et al., 2025) and RAISE recommendations (Version 2, 2025). This approach aligns with methodological guidance permitting AI as a second reviewer (Flemyng et al., 2025; Gartlehner et al., 2025) and has been validated in studies demonstrating human-comparable screening accuracy (Matsui et al., 2024; Sanghera et al., 2025; Insuk et al., 2025). Each paper's title and abstract were assessed against the inclusion criteria, returning a decision, confidence level, and rationale. Papers were processed in batches of ten. Complete prompts and model parameters are documented in the project repository.

### 2.4.3 Validation

Inter-rater reliability was assessed on a stratified random sample of 100 papers per reviewer, with 50 common papers reviewed independently by three human reviewers. The sample was stratified equally between included and excluded papers. Cohen's kappa was computed for all pairwise comparisons, following the benchmarks of Hanegraaf et al. (2024), who reported a mean human-human kappa of 0.82 for abstract screening. The human reviewer retained final authority in all disagreements.

Following screening, 7,893 papers were included: 4,308 at Tier 1 (LLMs in healthcare), 1,969 at Tier 2 (LLMs in healthcare simulation), and 1,309 at Tier 3 (LLMs in healthcare simulation and NTS), with 307 classified outside the tier structure. The PRISMA flow diagram (Figure 1) details the selection process.

## 2.5 Inclusion and Exclusion Criteria

Papers were included if they: (a) addressed LLMs, generative AI, or a named system (e.g., ChatGPT, GPT-4, Claude, Gemini); (b) were situated within a healthcare or clinical context; and (c) were published between January 2020 and March 2026 in English. Tier 2 additionally required a simulation or training dimension. Tier 3 additionally required at least one NTS domain. Papers were excluded if they addressed traditional machine learning without an LLM component, clinical AI without an educational dimension, purely technical topics without a healthcare context, or were editorials or commentaries without original data.

## 2.6 Bibliometric Analysis

All analyses were performed in Python. **Performance analysis** encompassed annual publication trends with compound annual growth rate; citation metrics (h-index, g-index, i10-index); author productivity assessed against Lotka's law (Lotka, 1926); and journal concentration assessed against Bradford's law (Bradford, 1934). **Science mapping** involved keyword co-occurrence network construction, filtered to retain pairs co-occurring in at least two papers and individual keywords appearing in at least three papers. Community detection used the Louvain algorithm (Blondel et al., 2008). Callon's strategic thematic diagram (Callon et al., 1991) was constructed by computing centrality (external cohesion) and density (internal cohesion) for each cluster, dividing the space into four quadrants at the mean values: motor themes, niche themes, basic themes, and emerging or declining themes. **NTS domain classification** used regular expression pattern matching across nine domains (including task management and professionalism in addition to the seven core domains), capturing both explicit terminology and implicit references (e.g., "empathy," "shared mental model"). **Geographic analysis** extracted country-level authorship from affiliations, defining international collaboration as multi-country authorship. **Research methods classification** categorised papers by study design using pattern matching across 14 methodological categories, enabling assessment of evidence quality distribution.

## 2.7 Open-Access Data Philosophy

This analysis was designed from inception to use only freely accessible data sources, tools, and infrastructure. We contend that bibliometric instruments should not be restricted to those with institutional subscriptions---a position particularly pertinent in healthcare simulation, where educators and researchers in low- and middle-income settings may lack access to proprietary platforms. The complete pipeline is publicly available on GitHub and designed for re-execution at six-month intervals, enabling longitudinal field monitoring without repeating manual effort.
