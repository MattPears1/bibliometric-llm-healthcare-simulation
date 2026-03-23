# 2. Methods

## 2.1 Study Design

This study employed a bibliometric design following established methodological frameworks [3,4]. The design was governed by two foundational principles: (a) analytical rigour consistent with contemporary bibliometric practice, and (b) full reproducibility using exclusively free, open-access data sources. The entire pipeline—data collection, processing, screening, and analysis—is publicly available on GitHub, enabling other researchers to replicate or update the study.

Reporting followed PRISMA 2020 guidelines [17], adapted for bibliometric analysis, and the PRISMA-trAIce checklist for transparent reporting of AI use in evidence synthesis [18]. Where applicable, these frameworks were interpreted pragmatically for a bibliometric (rather than clinical trial) context.

## 2.2 Data Sources and Search Strategy

Seven electronic databases were systematically queried: OpenAlex, PubMed (via NCBI E-utilities), Europe PMC, Crossref, Semantic Scholar, CORE, and the Directory of Open Access Journals (DOAJ). These sources were selected for their complementary coverage of biomedical, clinical, and educational literature; free API access without institutional subscriptions; and sufficient metadata richness for bibliometric computation. The proprietary databases Web of Science and Scopus were deliberately excluded to maintain an open-access approach; the implications of this choice are considered in the limitations.

A three-tier search strategy was employed to capture the breadth of the literature while permitting analysis at increasing specificity:

- **Tier 1 (broadest):** Large language model (LLM) and generative AI terms combined with healthcare and medical terms.
- **Tier 2 (intermediate):** Tier 1 terms combined with simulation-specific terminology (e.g., simulation, virtual patient, debriefing, OSCE).
- **Tier 3 (focused):** Tier 2 terms combined with non-technical skills (NTS) terminology (e.g., communication, teamwork, leadership, decision-making, situational awareness, crisis resource management).

A total of 35 query strategies were executed across the seven sources. PubMed queries employed MeSH terms and title–abstract field tags. OpenAlex and Semantic Scholar used full-text and topic-level search filters where available. The remaining databases used keyword-based search adapted to their respective API capabilities. The complete query strings are provided in Supplementary Appendix A. The search was restricted to English-language publications from January 2020 to March 2026, with the start date chosen to capture a pre-ChatGPT baseline period within the timeframe of rapid LLM development.

## 2.3 Data Processing

Records from the seven databases were normalised to a common schema encompassing title, authors, year, DOI, abstract, journal/source, keywords, citation count, document type, and open-access status. Source-specific identifiers were retained for provenance tracking.

A three-stage deduplication algorithm was applied: exact DOI matching; fuzzy title matching (threshold of 90 on a 0–100 scale via the RapidFuzz library); and a fallback using author surname, publication year, and title-fragment matching. When duplicates were identified, a source-priority hierarchy (PubMed, OpenAlex, Europe PMC, Crossref, Semantic Scholar, CORE, DOAJ) determined which record was retained.

The initial search yielded **100,277** records. After removing **13,642** duplicates (9,447 DOI-matched, 4,127 title-matched, 68 author–year–matched), **86,635** unique records remained, corresponding to a deduplication rate of approximately **13.6%** (13,642 / 100,277). These values derive from the programmatic log and are reported here to facilitate reproducibility; the downstream analytic corpus sizes are reported in Section 2.4 and in the Results.

## 2.4 Screening Process

### 2.4.1 Stage 1: Keyword Pre-filter

Automated keyword matching across four categories (LLM, simulation, NTS, and medical terms) provisionally classified each paper as a definite include, definite exclude, or uncertain. Papers were labelled as:

- **Definite include:** at least five cross-category keyword matches, including at least one LLM term;
- **Definite exclude:** zero LLM terms;
- **Uncertain:** all remaining records.

This procedure yielded **3,648** definite includes, **73,990** definite excludes, and **8,997** uncertain cases, based on the 86,635 unique records after deduplication.

### 2.4.2 Stage 2: Conservative Heuristic Screening

Uncertain papers were screened using a conservative heuristic algorithm that re-evaluated keyword evidence across all four categories with stricter thresholds. Papers were included only if they matched at least three of the four keyword categories, or at least two categories with a cumulative match score of six or higher. This approach was intended to err on the side of inclusion while filtering papers with weak evidence of relevance.

The pipeline also supports AI-assisted screening using Claude (Anthropic), in line with PRISMA-trAIce [18] and RAISE recommendations (Version 2, 2025), consistent with emerging methodological guidance permitting AI as a second reviewer [19,20]. In the present study, AI-assisted screening was implemented as an optional, logged step in the codebase; human reviewers retained final decision authority. This capability is documented in the project repository to facilitate use in future iterations of the analysis.

### 2.4.3 Validation

Inter-rater reliability was assessed on a stratified random sample of 100 papers per reviewer, with 50 common papers reviewed independently by three human reviewers. The sample was stratified equally between papers provisionally included and provisionally excluded by the automated stages. Cohen’s kappa was computed for all pairwise comparisons, following the benchmarks of Hanegraaf et al. (2024), who reported a mean human–human kappa of 0.82 for abstract screening. In all instances of disagreement, the human reviewers’ consensus classifications determined the final inclusion status.

Following screening, the results were organised into a corpus structure aligned with the final analytic dataset:

- **Core corpus (3,112 papers):** The primary analysis dataset, corresponding to all papers that passed the screening process and were assigned to Tier 2 or Tier 3. This corpus underpins all quantitative bibliometric findings. The core corpus comprises **1,797** Tier 2 papers (**57.7%**) and **1,315** Tier 3 papers (**42.3%**), as reported in the descriptive statistics.
- **Tier-based subsets:** Within the core corpus, Tier 2 papers focus on LLMs in healthcare simulation, while Tier 3 papers additionally include an explicit NTS component. These subsets are used for sensitivity analyses where relevant.

Earlier exploratory constructs (e.g., an “extended” or “primary” corpus including Tier 1 records) were not retained in the final analytic workflow; all reported results in the Results section are based on the **3,112-paper** core corpus unless explicitly stated otherwise. The PRISMA flow diagram (Figure 1) details the complete selection process from the initial 100,277 records to the final 3,112-paper corpus.

## 2.5 Inclusion and Exclusion Criteria

Papers were included if they met all of the following criteria:

a) addressed LLMs, generative AI, or a named system (e.g., ChatGPT, GPT‑4, Claude, Gemini, other proprietary or open-source LLMs);  
b) were situated within a healthcare or clinical context (including medical, nursing, allied health, dental, and related domains); and  
c) were published between January 2020 and March 2026 in English.

Tier 2 additionally required a simulation or training dimension (e.g., virtual patients, OSCEs, VR/AR/XR environments, scenario-based or mannequin-based simulation, debriefing). Tier 3 additionally required explicit reference to at least one NTS domain (e.g., communication, teamwork, leadership, decision-making, situational awareness, crisis resource management, stress management, professionalism, or task management).

Papers were excluded if they: addressed traditional machine learning without an LLM component; focused on clinical AI without an educational, training, or simulation dimension; addressed purely technical or computer science topics without a healthcare context; or were editorials or commentaries without original data or substantive methodological contribution. These criteria were applied consistently across all screening stages.

## 2.6 Bibliometric Analysis

All analyses were performed in Python using reproducible scripts. Unless otherwise indicated, all quantitative results in the Results section refer to the **3,112** papers in the core corpus, for which citation data were available for **100.0%** of records.

**Performance analysis** included:

- annual publication trends (2020–2026) with compound annual growth rate (CAGR) computed from the yearly counts (54, 56, 88, 367, 767, 1,415, 365; total **3,112** papers; overall CAGR **37.5%**);
- citation metrics computed on the full core corpus, including total citations (**46,823**), mean citations (**15.05**), median citations (**1**), maximum citations (**1,150**), and distribution of uncited papers (**1,267**, 40.7%);
- h‑index (**92**), g‑index (**166**), and i10‑index (**772**) for the corpus;
- author productivity and collaboration patterns, including total unique authors (**12,937**), collaboration index (mean authors per paper: **5.51**), and fit to Lotka’s law (Lotka exponent β = **2.559**, R² = **0.941**);
- journal and source concentration, including total unique journals/sources (**1,343**), papers with journal data (**2,407**), and Bradford’s law zones (Zone 1: 63 journals, 804 papers; Zone 2: 478 journals, 801 papers; Zone 3: 802 journals, 802 papers).

**Science mapping** involved:

- construction of keyword co-occurrence networks, filtered to retain pairs co-occurring in at least two papers and individual keywords appearing in at least three papers;
- community detection using the Louvain algorithm [27];
- computation of centrality (external cohesion) and density (internal cohesion) for each cluster, and placement in Callon’s strategic diagram [28], partitioned by mean centrality and mean density into motor, niche, basic, and emerging/declining themes. Cluster-level metrics (e.g., centrality and density values) are reported in the Results.

**NTS domain classification** used regular-expression pattern matching across nine domains (decision-making, communication, teamwork, leadership, stress management, professionalism, situational awareness, task management, and crisis resource management [CRM]). Both explicit terminology and closely related constructs (e.g., “empathy,” “clinical reasoning,” “shared mental model”) were included in the patterns. Across the core corpus:

- **1,730** papers (**55.6%**) were classified into at least one NTS domain;
- **563** papers (**18.1%**) were mapped to multiple domains;
- **1,382** papers (**44.4%**) had no NTS domain assignment under the applied patterns.

**Geographic analysis** extracted country-level authorship from affiliation strings where available. Of the 3,112 papers, **1,004** (**32.3%**) had identifiable country data, yielding **86** unique countries. International collaborations were defined as multi-country authorship and accounted for **215** papers (**21.4%** of papers with identifiable country data). Country- and continent-level distributions are reported in the Results.

**Research methods classification** categorised papers by study design using pattern matching across 14 methodological categories. Of the 3,112 papers, **2,040** (**65.6%**) were successfully classified, and **1,072** (**34.4%**) remained unclassified at this stage. The most frequent classified categories were development studies (653, 21.0%), comparative studies (604, 19.4%), validation studies (535, 17.2%), cross-sectional surveys (357, 11.5%), and qualitative studies (271, 8.7%). Evidence levels were assigned heuristically to each category (e.g., randomised controlled trials and systematic reviews as higher levels; narrative reviews and case studies as lower), and the distribution of methods and evidence levels is presented descriptively in the Results without implying formal grading of evidence quality.

## 2.7 Open-Access Data Philosophy

The analysis was designed from inception to use only freely accessible data sources, tools, and infrastructure. This reflects the view that bibliometric instruments should be available to researchers regardless of institutional subscriptions—a consideration that is particularly pertinent in healthcare simulation, where educators and researchers in low- and middle-income settings may lack access to proprietary platforms such as Web of Science or Scopus.

All raw and processed data (subject to database terms of use), code, and configuration files are hosted in a public GitHub repository. The pipeline is designed for re-execution at approximately six-month intervals, enabling longitudinal monitoring of this fast-evolving field with minimal additional manual effort. Where APIs or data sources change, versioning and change logs in the repository allow subsequent users to trace and adapt the workflow.