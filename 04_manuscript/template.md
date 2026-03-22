# Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape

**Authors:** Matt Pears^1^, [Colleague 1]^2^, [Colleague 2]^3^, Shekhar [Surname]^4*^

*^*^ Corresponding author*

---

## Abstract

**Background:** {{abstract_background}}

**Methods:** {{abstract_methods}}

**Results:** {{abstract_results}}

**Conclusions:** {{abstract_conclusions}}

**Keywords:** bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education

---

## 1. Introduction

{{introduction}}

### 1.1 Background

The emergence of large language models (LLMs), particularly following the release of ChatGPT in November 2022, has fundamentally transformed the landscape of healthcare education and simulation-based training. {{intro_llm_context}}

### 1.2 Simulation-Based Education and Non-Technical Skills

{{intro_simulation_nts}}

### 1.3 Rationale and Objectives

{{intro_rationale}}

**Objectives:**
1. To map the publication landscape of LLMs in healthcare simulation (2020–2026)
2. To identify key research themes, trends, and gaps
3. To analyse the distribution of research across non-technical skills domains
4. To provide a replicable, open-access bibliometric pipeline for ongoing landscape monitoring

---

## 2. Methods

### 2.1 Study Design

This study employed a bibliometric analysis following established methodological frameworks (Donthu et al., 2021; Aria & Cuccurullo, 2017). The analysis was conducted using exclusively free, open-access data sources to ensure full reproducibility without institutional database subscriptions. The complete pipeline — including data collection scripts, processing code, and analysis tools — is publicly available at {{github_url}}.

### 2.2 Data Sources and Search Strategy

Seven electronic databases were systematically searched: OpenAlex, PubMed (via E-utilities), Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ. These databases were selected for their complementary coverage of biomedical, clinical, and educational literature, and their provision of free API access.

A three-tier search strategy was employed:
- **Tier 1 (broadest):** LLM/AI terms AND medical/healthcare terms
- **Tier 2 (core):** Tier 1 AND simulation/training terms
- **Tier 3 (focused):** Tier 2 AND non-technical skills terms

Multiple query strategies were used per database ({{n_query_strategies}} total across all sources) to maximise recall while accounting for database-specific query syntax limitations.

**Date range:** January 2020 – December 2026
**Language:** English

### 2.3 Inclusion and Exclusion Criteria

{{inclusion_exclusion_criteria}}

### 2.4 Screening Process

A two-stage screening process was employed:

**Stage 1 (keyword pre-filter):** Automated keyword matching across four categories (LLM terms, simulation terms, NTS terms, medical terms) classified papers as definite include, definite exclude, or uncertain.

**Stage 2 (AI-assisted screening):** Papers classified as uncertain in Stage 1 were screened using Claude (Anthropic), following the PRISMA-trAIce reporting framework (Holst et al., 2025). The AI screener assessed title and abstract against inclusion criteria, providing a decision, confidence level, and rationale for each paper.

**Validation:** Inter-rater reliability was assessed using a stratified random sample of {{irr_sample_size}} papers reviewed independently by {{n_reviewers}} human reviewers. Cohen's kappa was computed for pairwise agreement. {{irr_results}}

### 2.5 Data Extraction and Analysis

Bibliometric analyses were performed using Python (version {{python_version}}) with the following analytical approaches:

- **Publication trends:** Annual output with compound annual growth rate (CAGR)
- **Author productivity:** Lotka's law analysis
- **Journal distribution:** Bradford's law of scattering
- **Citation analysis:** h-index, g-index, citation distribution
- **Geographic distribution:** Country-level analysis from author affiliations
- **Keyword co-occurrence:** Network analysis with Louvain community detection
- **Thematic mapping:** Callon's strategic diagram (centrality × density)
- **NTS domain classification:** Regex-based classification across seven NTS domains

### 2.6 Open-Access Philosophy

This analysis deliberately uses only freely accessible data sources. We argue that the tools for understanding the research landscape should not be restricted to those with institutional database subscriptions. Our complete pipeline is available on GitHub, enabling any researcher to reproduce or update this analysis.

---

## 3. Results

### 3.1 Search Results and Study Selection

The initial search across seven databases yielded {{n_raw}} records. After removing {{n_duplicates}} duplicates ({{dedup_rate}}% deduplication rate), {{n_unique}} unique records remained. Following two-stage screening, {{n_included}} papers were included for analysis ({{inclusion_rate}}% inclusion rate).

*[Insert PRISMA flow diagram - Figure 1]*

### 3.2 Publication Trends

{{results_publication_trends}}

*[Insert Figure: Publication trends by year]*

### 3.3 Citation Analysis

{{results_citation_analysis}}

### 3.4 Author Analysis

{{results_author_analysis}}

### 3.5 Journal Distribution

{{results_journal_analysis}}

### 3.6 Geographic Distribution

{{results_geographic}}

### 3.7 Thematic Mapping

{{results_thematic_mapping}}

*[Insert Figure: Strategic diagram]*

### 3.8 Non-Technical Skills Analysis

{{results_nts_analysis}}

### 3.9 Urology Sub-Analysis

{{results_urology}}

---

## 4. Discussion

### 4.1 Principal Findings

{{discussion_principal}}

### 4.2 Comparison with Existing Literature

{{discussion_comparison}}

### 4.3 The NTS Gap

{{discussion_nts_gap}}

### 4.4 Implications for Practice

{{discussion_implications}}

### 4.5 The Open-Access Imperative

{{discussion_open_access}}

### 4.6 Limitations

{{discussion_limitations}}

### 4.7 Future Directions

{{discussion_future}}

---

## 5. Conclusions

{{conclusions}}

---

## Data Availability Statement

The complete data collection pipeline, processing scripts, and analysis code are available at {{github_url}}. Raw bibliometric data and analysis outputs are available upon reasonable request from the corresponding author.

## Funding

{{funding}}

## Competing Interests

The authors declare no competing interests.

## Author Contributions (CRediT)

{{credit_statement}}

## Acknowledgements

{{acknowledgements}}

---

## References

{{references}}

---

## Supplementary Materials

- **Appendix A:** Full search strategies per database
- **Appendix B:** PRISMA 2020 checklist
- **Appendix C:** Full list of included papers
- **Appendix D:** Code availability and reproduction guide
