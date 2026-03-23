---
title: "Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape"
authors:
  - Matt Pears (First Author)
  - "[Colleague 1]"
  - "[Colleague 2]"
  - "Shekhar [Surname] (Corresponding Author)"
date: 2026-03-23
---

**Background**  
Large language models (LLMs) are increasingly examined within healthcare simulation, yet their specific contribution to non‑technical skills (NTS) training and specialty boot camps remains only partially characterised. We therefore conducted a bibliometric analysis to map this rapidly expanding field, with particular attention to NTS domains and urology boot camp–relevant applications.

**Methods**  
A core corpus of 3,112 records on LLMs in healthcare simulation was assembled from seven open databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, DOAJ) for 2020–2026 using a two‑stage screening strategy restricted to high‑ and medium‑confidence Tier 2/3 records [1]. Descriptive bibliometrics, Lotka‑ and Bradford‑law analyses, and text‑mining–based classifications of NTS domains, simulation modalities, research methods, LLM models, and clinical specialties were applied [1–5].

**Results**  
The final corpus comprised 3,112 papers, with an overall compound annual growth rate of 37.5% [1]. Publication volume accelerated after the public release of ChatGPT, with 2,914 papers (93.6%) appearing in 2023–2026 compared with 198 papers (6.4%) in 2020–2022 [1]. Output peaked in 2025 with 1,415 papers (45.5% of the corpus) [1]. Across all years, the papers accrued 46,823 citations (mean 15.05; median 1; maximum 1,150) with an h‑index of 92 [2].  

There were 12,937 unique authors, with author data available for 3,093 papers and a mean of 5.51 authors per paper (collaboration index) [3]. Most authors (11,171; 86.3%) contributed to only one paper, and Lotka’s law was well approximated with an exponent of 2.559 (R²=0.941), indicating a highly skewed productivity distribution [3]. Publications were dispersed across 1,343 journals/sources, with 2,407 papers having journal data; 1,061 journals (79.0%) were single‑paper venues [4]. Bradford zone 1 (63 core journals) accounted for 804 papers (33.4% of papers with journal data) [4]. Country information was identifiable for 1,004 papers spanning 86 countries; among these, the United States contributed 249 papers (24.8%) and China 173 papers (17.2%) [5].  

NTS domains were assigned to 1,730 papers (55.6% of the corpus), leaving 1,382 papers (44.4%) unclassified for NTS content [6]. Decision‑making was the most frequently coded domain (931 papers; 29.9% of the corpus), whereas crisis resource management (CRM) was identified in only 4 papers (0.1%), suggesting a pronounced CRM gap relative to other NTS domains [6].  

Simulation work most often involved VR/MR/XR modalities (766 papers; 24.6%), followed by scenario‑based designs (416; 13.4%) and virtual patient/chatbot simulations (304; 9.8%) [7]. At least one simulation type was coded in 1,585 papers (50.9%), with 280 papers (9.0%) spanning multiple modalities and 1,527 papers (49.1%) remaining unclassified by simulation type [7].  

Research methods could be classified for 2,040 papers (65.6%) [8]. Development studies were most frequent (653; 21.0%), followed by validation studies (535; 17.2%) and comparative studies (604; 19.4%) [8]. Only 35 randomised controlled trials (1.1% of the corpus) were identified, indicating that higher‑level experimental evidence remains relatively sparse [8].  

Within urology, 117 papers (3.8% of the corpus) were identified [9]. Although manual supplementary searching identified isolated examples of LLM use for NTS feedback in urology simulation [36], no studies were found evaluating LLM-powered mannequin voices or conversational agents within urology boot camp formats specifically, despite the apparent feasibility of such applications.

**Conclusions**  
LLM‑enabled healthcare simulation related to NTS training is expanding rapidly but appears methodologically immature, with relatively few randomised controlled trials and marked under‑representation of CRM. Urology is represented within the broader corpus, yet LLM-powered boot camp applications remain unreported. Targeted, high‑quality experimental work—particularly around team‑based CRM and specialty boot camps using LLM‑powered patient surrogates—seems strongly warranted.

**Keywords:** large language models; healthcare simulation; non‑technical skills; crisis resource management; medical education; urology; boot camp; bibliometrics.

# 1. Introduction

The release of ChatGPT in November 2022 marked an inflection point in the adoption of artificial intelligence across many domains of professional practice, and healthcare education has been no exception. Large language models (LLMs)—deep neural networks trained on vast corpora of text to generate, summarise, and reason over natural language—have rapidly moved from curiosity to consequential tool in medical training, assessment, and clinical decision support [1,2]. In the period following the launch of ChatGPT, the volume of scholarly output examining LLMs in healthcare contexts has increased substantially. In the present study’s core corpus of 3,112 papers published between 2020 and 2026, we observe a compound annual growth rate of 37.5% in publications related to LLMs and healthcare simulation, alongside a marked acceleration in output after 2022. However, the speed of this expansion poses a challenge for educators, policymakers, and researchers seeking to understand what is known, what remains uncertain, and where the field should direct its attention next.

Bibliometric analysis offers a systematic, quantitative approach to mapping scientific landscapes at scale [3]. By applying established bibliometric laws and indicators—including Lotka’s law of author productivity, Bradford’s law of journal scattering, and Callon’s strategic thematic diagram—researchers can identify patterns in publication growth, intellectual structure, and thematic evolution that would be difficult to discern through narrative review alone [4,5]. Bibliometric methods are particularly well suited to rapidly expanding fields where the literature is too voluminous for traditional qualitative synthesis yet too immature for definitive systematic review. The intersection of LLMs and healthcare simulation appears to represent such a field.

## 1.1 Background

Healthcare simulation has been a cornerstone of medical education for over two decades, providing learners with opportunities to practise clinical skills in controlled, lower-risk environments [6,7]. Simulation-based education encompasses a broad continuum of modalities, from low-fidelity bench models and standardised patient encounters to high-fidelity mannequin scenarios and immersive virtual reality environments. Its value is particularly well established in procedural disciplines—including surgery, emergency medicine, and anaesthesia—where it serves both as a formative training tool and a summative assessment platform, exemplified by the Objective Structured Clinical Examination.

The emergence of LLMs introduces new possibilities across this continuum. Generative AI systems can simulate realistic patient interactions for communication training, generate scenario content for debriefing exercises, provide automated feedback on clinical reasoning, and potentially serve as intelligent tutoring agents capable of adapting to individual learner performance [8]. Early applications have suggested that models such as GPT‑4 and Claude can pass medical licensing examinations, generate clinically plausible case vignettes, and role‑play standardised patients with sufficient fidelity to support meaningful educational encounters [9,10]. These capabilities have prompted considerable enthusiasm but also legitimate concern regarding accuracy, bias, hallucination, and the pedagogical implications of supplementing or partially replacing human interaction with machine-generated dialogue.

## 1.2 Simulation-Based Education and Non-Technical Skills

While much early research on LLMs in healthcare has focused on knowledge retrieval and clinical reasoning—tasks closely aligned with technical competence—the role of these technologies in training non-technical skills (NTS) remains substantially less explored. Non-technical skills encompass the cognitive, social, and interpersonal competencies essential for safe, effective clinical practice, including communication, teamwork, leadership, decision-making, situational awareness, and stress management [11,12]. These competencies are widely recognised as critical contributors to patient safety, with failures in NTS implicated in a substantial proportion of adverse events and near-misses across healthcare settings (Reason, 2000; Catchpole et al., 2008).

Simulation-based training is currently the predominant method for developing NTS in healthcare professionals. Structured programmes—often incorporating crisis resource management principles, standardised patient encounters, and facilitated debriefing—have demonstrated measurable improvements in team performance, communication quality, and leadership behaviours [15,16]. Validated assessment instruments such as the Non-Technical Skills for Surgeons (NOTSS), the Anaesthetists’ Non-Technical Skills (ANTS) framework, and the NOTECHS system provide standardised means of evaluating these competencies in simulated and clinical environments.

The potential for LLMs to augment NTS training is conceptually compelling but, to date, empirically underdeveloped. An AI-generated simulated patient could, in principle, provide repeated opportunities for practising breaking bad news, conducting consent discussions, or managing difficult team dynamics. An LLM-powered debriefing assistant could offer structured post-scenario feedback aligned with established frameworks. Yet the literature examining these applications remains fragmented, and, to our knowledge, no comprehensive mapping of the research landscape currently exists.

## 1.3 Rationale and Objectives

This study was motivated by three observations. First, research on LLMs in healthcare simulation appears to be growing at a rate that challenges the capacity of traditional narrative or systematic reviews to remain current. A bibliometric approach enables quantitative landscape mapping at a scale that is both comprehensive and reproducible. Second, despite growing interest in the intersection of AI and medical education, no published bibliometric analysis has, to our knowledge, specifically examined LLMs in the context of healthcare simulation for non-technical skills training. This represents a potentially important gap, given the centrality of NTS to patient safety and the plausible potential for AI to transform how these skills are taught and assessed. Third, existing bibliometric studies in medical education frequently rely on proprietary databases such as Web of Science and Scopus, creating a paradox in which the tools for understanding the research landscape are themselves locked behind institutional paywalls. We contend that bibliometric infrastructure should, as far as possible, be as open as the research it seeks to map.

This analysis forms one component of a broader research programme examining the integration of LLMs into healthcare simulation. Companion studies include a Delphi consensus study on LLM implementation in simulation-based education, a scoping review of specific LLM applications, and a platform evaluation of the Simuro simulation system. Together, these workstreams aim to provide an evidence base that is both methodologically rigorous and practically actionable for educators, simulation centres, and curriculum designers.

To address these gaps, this study employs a three-tier analytical framework with a three-level corpus structure. The screening process produces an extended corpus of 7,893 records spanning all identified LLM and healthcare literature in the source databases, providing the broadest landscape context (present study workflow). Within this, a primary corpus of 3,587 records is defined by the addition of simulation-specific terminology. The main bibliometric analysis is conducted on a core corpus of 3,112 papers—corresponding to all included items in the final dataset, restricted to high- and medium-confidence classifications at Tier 2 (LLM + healthcare simulation) and Tier 3 (LLM + healthcare simulation + NTS)—ensuring that all quantitative findings are grounded in the most relevant and rigorously screened literature. This layered approach is intended to provide both transparency in the narrowing process and methodological rigour in the final analysis.

The specific objectives of this study are:

1. To map the publication landscape of LLMs in healthcare simulation from 2020 to 2026, characterising growth trajectories, geographic distribution, and journal concentration. In particular, we examine the increase from 54 papers in 2020 to 1,415 in 2025, and the shift from 198 pre‑ChatGPT publications (2020–2022) to 2,914 in the post‑ChatGPT period (2023–2026) in the core corpus.
2. To identify the dominant research themes, intellectual clusters, and emergent topics through keyword co-occurrence analysis and Callon’s strategic thematic diagram.
3. To analyse, within the 3,112-paper corpus, the distribution of research across non-technical skills domains—including communication, teamwork, leadership, decision-making, situational awareness, stress management, and related constructs such as professionalism and crisis resource management—identifying which competencies are comparatively well represented (e.g. decision-making in 29.9% and communication in 19.9% of papers) and which remain relatively underexplored (e.g. situational awareness in 1.7% and explicit crisis resource management in 0.1% of papers).
4. To provide a fully replicable, open-access bibliometric pipeline, built exclusively on free data sources, that other researchers can execute to reproduce or update this analysis without requiring institutional database subscriptions.

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

# 3. Results

## 3.1 Search Results and Study Selection

The systematic search across seven open-access databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ) yielded 100,277 raw records. After applying the three-stage deduplication algorithm—exact DOI matching, fuzzy title matching, and author–year–title fragment matching—13,642 records were identified as duplicates (13.6% overlap rate), leaving 86,635 unique records for screening. The keyword pre-filter classified 3,648 papers as definite includes, 73,990 as definite excludes, and 8,997 as uncertain. AI-assisted screening of the uncertain cases, followed by human validation, produced the three-level corpus structure: an extended corpus of 7,893 papers (all LLM + healthcare literature), a primary corpus of 3,587 papers (adding simulation terms), and a core corpus of 3,112 papers (high/medium confidence, Tier 2/3 only). The core corpus—comprising 1,797 Tier 2 papers (57.7%) and 1,315 Tier 3 papers (42.3%)—forms the basis for all analyses reported below. The complete selection process is presented in the PRISMA flow diagram (Figure 1).

Data completeness across the core corpus was generally high (Table S1). Citation and year data were available for 100.0% of papers, author data for 99.4%, DOIs for 96.9%, abstracts for 98.7%, keywords for 80.4%, and journal or source information for 77.3%. Open-access papers accounted for 1,999 of 3,112 records (64.2%), consistent with broader trends toward open publishing in biomedical and AI-related research.

## 3.2 Publication Trends

The core corpus exhibited rapid growth over the study period, with a compound annual growth rate (CAGR) of 37.5% from 2020 to 2025 (Table 1; Figure 2). Publication volume showed a marked inflection coinciding with the release of ChatGPT in November 2022. The pre-ChatGPT period (2020–2022) accounted for 198 papers (6.4% of the corpus), while the post-ChatGPT period (2023–2026) contributed 2,914 papers (93.6%).

Annual output increased from 54 papers in 2020 to 56 in 2021 and 88 in 2022. Growth then accelerated substantially: 367 papers in 2023, 767 in 2024, and 1,415 in 2025—the peak year, accounting for 45.5% of all publications. Data for 2026 (n = 365 through March) indicate continued high output; however, the partial-year figures preclude reliable extrapolation to the full year.

The transition from 2022 to 2023 represents a 4.2-fold increase in annual output (88 to 367 papers), the largest year-on-year surge in the dataset. This acceleration is broadly consistent with other bibliometric reports on generative AI in biomedicine [32] and appears steeper than typical diffusion curves observed for many prior health technology innovations [31], suggesting a particularly rapid uptake of LLMs in healthcare-related research. The median publication year across the corpus was 2025, indicating that the literature is overwhelmingly recent.

## 3.3 Citation Analysis

The core corpus accumulated a total of 46,823 citations, with a mean of 15.05 citations per paper and a median of 1 (Table 2). The citation distribution was heavily right-skewed: 1,267 papers (40.7%) were uncited at the time of data extraction, while a relatively small number of highly cited works exerted disproportionate influence. The corpus h-index was 92 (92 papers with at least 92 citations each), the g-index was 166, and the i10-index (papers with 10 or more citations) was 772. The most cited paper in the corpus received 1,150 citations.

Citation intensity varied substantially by publication year (Table 2). Papers published in the earliest years achieved the highest mean citation counts, reflecting both a longer citation window and their role as foundational contributions to digital and AI-enabled approaches in healthcare and education. For example, papers from 2020 and 2021 had mean citation counts of 77.2 and 81.3, respectively, compared with 3.5 for 2025 and 0.2 for 2026. The more recent 2025 and 2026 cohorts have had limited time to accrue citations, consistent with well-established citation lags in biomedical publishing.

## 3.4 Author Analysis

A total of 12,937 unique authors contributed to the core corpus, yielding a collaboration index of 5.51 authors per paper among papers with author data (Table 4). This level of co-authorship aligns with contemporary norms in biomedical and health informatics research and likely reflects the multidisciplinary nature of LLM work, which often requires combined expertise in computer science, clinical practice, and education.

Author productivity followed Lotka’s law with an exponent (beta) of 2.559 and an R-squared of 0.941, indicating an excellent fit to an inverse-square-type distribution. The vast majority of contributors (11,171 authors; 86.3%) published a single paper, while 1,766 authors (13.7%) contributed two or more. This high proportion of single-paper authors is characteristic of a young and rapidly expanding area, in which many researchers appear to be entering the field rather than yet maintaining long-term, highly prolific programmes of inquiry.

## 3.5 Journal Distribution

Among the 3,112 core corpus papers, 2,407 (77.3%) had identifiable journal or source data, spanning 1,343 unique outlets (Table 6). The degree of dispersion was high: 1,061 outlets (79.0%) were represented by a single paper, underscoring the interdisciplinary nature of the topic, which cuts across medical education, clinical specialties, health informatics, computer science, and related domains.

Bradford’s law analysis partitioned the journals into three zones of approximately equal article yield (Table 7; Figure 3). Zone 1 (core) comprised 63 journals contributing 804 papers (33.4% of papers with journal data), Zone 2 comprised 478 journals with 801 papers (33.3%), and Zone 3 comprised 802 journals with 802 papers (33.3%). The most prolific source was Cureus (88 papers), followed closely by arXiv (Cornell University) with 86 papers. The prominence of open-access and preprint platforms among core sources is consistent with the field’s rapid dissemination norms and the broader open-science ethos in AI research.

## 3.6 Geographic Distribution

Country-level authorship data were available for 1,004 papers (32.3% of the corpus), revealing contributions from 86 countries (Table 8; Figure 4). The United States led in absolute output (249 papers; 24.8% of papers with identified country), followed by China (173; 17.2%), the United Kingdom (77; 7.7%), India (65; 6.5%), and Canada (59; 5.9%). International collaborations—defined as papers with authors from more than one country—accounted for 215 of the 1,004 geographically identified papers (21.4%), suggesting moderate but not dominant levels of cross-border cooperation. The concentration of output in high-income and upper-middle-income countries raises potential equity concerns regarding whose perspectives and contexts shape the emerging evidence base for LLM integration in healthcare and health professions education.

## 3.7 Thematic Mapping

Keyword co-occurrence network analysis identified six thematic clusters, which were plotted on Callon’s strategic diagram using centrality (external cohesion) and density (internal cohesion) as axes (Table 9; Figure 5). Clusters were interpreted with reference to their predominant keywords and positions in the strategic diagram.

**Motor themes (high centrality, high density).** Two clusters occupied the motor quadrant: (i) an education/learning/training cluster (Cluster 5; 1,011 keywords; centrality 998,063.0; density 328.0) capturing simulation applications, training methodologies, and practical implementation issues; and (ii) an artificial/medical/intelligence cluster (Cluster 4; 1,003 keywords; centrality 907,637.0; density 203.9) focusing on system-level applications and evaluation within clinical and educational settings. These motor themes are both internally coherent and strongly connected to the broader research network, indicating relatively mature, driving research programmes.

**Basic and niche themes (moderate-to-high centrality, variable density).** The large-language-models/healthcare/models cluster (Cluster 0; 990 keywords; centrality 776,289.0; density 177.3) was positioned as a basic theme, representing the core LLM-focused discourse that underpins diverse applications. A clinical/patient/performance cluster (Cluster 1; 637 keywords; centrality 747,071.0; density 229.9) appeared as a niche theme, denoting more specialised work around performance assessment and patient-related outcomes that, while cohesive, remains somewhat more peripheral to the central LLM-in-education discourse.

**Emerging or declining themes (low centrality, low-to-moderate density).** Two clusters fell in the emerging/declining quadrant: an artificial-intelligence/computer-science/medicine cluster (Cluster 2; 644 keywords; centrality 206,694.0; density 96.6) bridging technical and biomedical perspectives, and a small com/para/que cluster (Cluster 3; 41 keywords; centrality 8,554.0; density 52.2) representing a technically oriented community that is relatively weakly connected to mainstream themes. Given the recency of LLM adoption, these positions are more plausibly interpreted as reflecting emerging areas that have not yet fully integrated into the dominant networks, rather than declining lines of work.

## 3.8 Non-Technical Skills Domains

Regex-based classification across nine non-technical skills (NTS) domains identified 1,730 of 3,112 papers (55.6%) as addressing at least one NTS domain, with 563 papers (18.1%) classified into multiple domains (Table 10; Figure 6). Decision-making was the most frequently addressed domain (931 papers; 29.9% of the corpus), followed by Communication (620; 19.9%), Teamwork (383; 12.3%), and Leadership (238; 7.6%). These four domains collectively accounted for the majority of NTS-related research.

By contrast, several domains were markedly underrepresented. Stress management appeared in 152 papers (4.9%), Professionalism in 94 (3.0%), Situational awareness in 54 (1.7%), Task management in 38 (1.2%), and Crisis Resource Management (CRM) in only 4 papers (0.1%). Given that CRM principles underpin the design and facilitation of many high-fidelity simulation scenarios in emergency medicine, anaesthesia, and surgery, the limited explicit presence of CRM terminology is notable. The substantial disparity between the frequency of Decision-making and the rarity of CRM-related terms suggests that the most simulation-specific NTS constructs are only minimally represented—and often not labelled explicitly as such—in the current LLM literature.

Cross-tabulation of simulation types and NTS domains (Table 11) indicated that VR/MR/XR simulations had the broadest NTS coverage overall, including 178 Communication, 152 Decision-making, 104 Leadership, 28 Stress management, 7 Situational awareness, 165 Teamwork, and 2 CRM-related instances. Virtual Patient/Chatbot simulations showed strong coverage of Communication (123) and Decision-making (73), alongside substantial Teamwork (40) and Leadership (46) representation. Scenario-based simulation also featured prominently, particularly for Decision-making (119), Communication (112), and Teamwork (75). In contrast, mannequin-based simulation—arguably the modality most amenable to LLM-powered voice interaction—was relatively less represented (98 papers overall) and showed minimal explicit CRM engagement (1 CRM-coded instance), suggesting an underexplored opportunity at the intersection of LLMs, high-fidelity simulation, and advanced NTS training.

## 3.9 LLM Model Landscape

Named-model classification identified specific LLMs in the corpus, revealing pronounced dominance by proprietary systems (Table 12; Figure 7). ChatGPT was the most frequently mentioned model (788 papers; 25.3% of the corpus). Generic references to “LLMs” without specifying a particular model appeared in 282 papers (9.1%). Among explicitly named models, GPT-4 (217; 7.0%) and Gemini (145; 4.7%) were the next most common proprietary systems, followed by Claude (89; 2.9%), GPT-3.5 (74; 2.4%), GPT-4o (73; 2.3%), GPT-5 (13; 0.4%), and Med-PaLM (10; 0.3%). Llama (49; 1.6%) was the most frequently mentioned open-source model, followed by Mistral (7; 0.2%).

Overall, 1,004 papers (32.3%) mentioned at least one proprietary model, whereas only 52 papers (1.7%) mentioned at least one open-source model. A small subset of 37 papers mentioned both proprietary and open-source models, indicating relatively limited direct comparative evaluation across licensing paradigms to date.

Temporal trends showed that Gemini exhibited one of the steepest growth trajectories (0 mentions in 2023, 21 in 2024, and 95 in 2025, with 29 already in early 2026), while references to GPT-3.5 appeared to decline after an initial rise (10 in 2023, 24 in 2024, 36 in 2025, and 4 in 2026), consistent with gradual model obsolescence or replacement by newer versions. References to GPT-4 increased substantially over time (30 in 2023, 69 in 2024, 101 in 2025), with some moderation in early 2026 (17). The “generic LLM” category grew steadily (14 in 2023, 71 in 2024, 151 in 2025, and 46 in 2026), suggesting an increasing proportion of studies that discuss LLMs conceptually or at a systems level without specifying a particular model.

## 3.10 Simulation Modalities

Simulation-type classification identified 1,585 of 3,112 papers (50.9%) as matching at least one simulation modality, with 280 papers (9.0%) mapped to multiple types (Table 13; Figure 8). VR/MR/XR was the most prevalent modality (766 papers; 24.6% of the corpus), reflecting the established synergy between immersive technologies and AI. Scenario-based simulation was the second most common modality (416; 13.4%), followed by Virtual Patient/Chatbot simulations (304; 9.8%). Standardised patient simulations (173; 5.6%), mannequin-based simulation (98; 3.1%), OSCEs (86; 2.8%), debriefing-focused studies (53; 1.7%), and roleplay (39; 1.3%) were less frequently represented.

The relatively low representation of mannequin-based simulation is notable given that this modality is well suited to LLM-powered text-to-speech and conversational interfaces that could, in principle, replace or augment human operators, thereby enabling more scalable and consistent simulated patient voices.

## 3.11 Research Methods

Research methods classification covered 2,040 of 3,112 papers (65.6%), leaving 1,072 papers (34.4%) unclassified by method (Table 14). Among classified studies, Development Studies were most common (653; 21.0% of the corpus), followed by Comparative Studies (604; 19.4%), Validation Studies (535; 17.2%), and Cross-sectional Surveys (357; 11.5%). Other designs included Qualitative studies (271; 8.7%), Narrative Reviews (249; 8.0%), Feasibility Studies (231; 7.4%), Observational studies (211; 6.8%), Systematic Reviews (204; 6.6%), Scoping Reviews (127; 4.1%), Mixed Methods designs (119; 3.8%), Case Studies (66; 2.1%), and Quasi-experimental studies (56; 1.8%).

Randomised controlled trials (RCTs) accounted for 35 papers (1.1% of the corpus), underscoring that, at the time of analysis, the evidence base for LLMs in healthcare and simulation was still in an early stage, with relatively few high-level comparative effectiveness studies.

## 3.12 Urology Sub-Analysis

The urology-specific analysis identified 117 urology-related papers (3.8% of the core corpus of 3,112 papers), indicating that the specialty has engaged with LLM research but at a modest scale relative to the overall field (Table 15). Within this subset, 26 papers (22.2%) were classified under Decision-making, 24 (20.5%) under Communication, 15 (12.8%) under Teamwork, and 10 (8.5%) under Leadership, suggesting a focus on core NTS domains similar to the broader corpus.

The intersection of urology, LLMs, and simulation boot camps was extremely sparse in the automated dataset: although 6 boot camp papers were identified across all specialties, none were urology-specific. Manual supplementary searching identified one notable exception---a double-blinded study benchmarking ChatGPT-4 against consultant interaction for NTS feedback to urology trainees in simulated scenarios [36], alongside emerging work on UroBot (a urology-specific LLM) and VR-based NTS training for urology trainees. However, no studies were identified examining LLM-powered mannequin voices or conversational agents deployed within the intensive boot camp format specifically. Given that urology boot camps are an established training format---typically employing mannequin-based simulation with human operators providing simulated patient voices [35]---this near-absence points to a clear and actionable research gap. LLM-powered text-to-speech could, in principle, support more scalable, consistent, and multilingual boot camp formats, but empirical studies evaluating such applications remain lacking.

# 4. Discussion

## 4.1 Principal Findings

This bibliometric analysis mapped the research landscape of large language models in healthcare simulation and non-technical skills training from 2020 to 2026. From an extended corpus of 7,893 papers, a rigorously screened core corpus of 3,112 papers---restricted to high and medium confidence classifications at Tier 2 and Tier 3---was used for the main analysis. The findings reveal a field undergoing rapid and substantial expansion---37.5% compound annual growth, a post-ChatGPT surge that concentrated 93.6% of all output in fewer than four years, and contributions from 12,937 authors across 86 countries---yet one characterised by significant structural imbalances that warrant careful consideration.

Five principal findings emerge. First, the literature is overwhelmingly recent and concentrated: 93.6% of all papers were published after the release of ChatGPT in November 2022, with 2025 alone accounting for 45.5% of the corpus (1,415 papers). This compressed timeline means the field is building its evidence base in real time, with limited opportunity for the longitudinal validation studies that typically underpin educational innovation. Second, citation analysis reveals a highly skewed distribution (h-index 92, g-index 166) in which a small number of foundational papers attract disproportionate attention, while approximately 35% of the literature remains uncited. Third, the NTS landscape is dominated by Decision-making and Communication, with Crisis Resource Management and Situational Awareness almost entirely absent from the discourse. Fourth, proprietary LLMs dominate the named-model landscape, creating a research ecosystem dependent on commercial platforms whose terms, capabilities, and pricing may change without notice. Fifth, urology simulation boot camps---an established training format that would appear well suited to LLM augmentation---have generated zero publications at this intersection, representing a specific and actionable research gap.

## 4.2 The Non-Technical Skills Gap

The distribution of NTS research across the classified domains reveals a hierarchy that appears to reflect convenience rather than clinical importance. Decision-making and Communication are well represented, likely because these competencies align most naturally with the text-based capabilities of LLMs: clinical reasoning tasks map onto question-answering paradigms, and communication training maps onto conversational interaction. Teamwork and Leadership occupy a middle ground, studied frequently but often in the context of interprofessional education rather than simulation-specific applications.

The critical deficits lie at the lower end. Stress management is studied infrequently despite its centrality to performance under pressure---the very conditions simulation is designed to replicate. Situational awareness receives limited attention, despite decades of human factors research establishing it as a prerequisite for safe clinical practice (Endsley, 1995; Flin et al., 2008). Most striking is the near-total absence of Crisis Resource Management, a domain that has been foundational to high-fidelity simulation training since its adaptation from aviation by Gaba and colleagues [30]. The vast disparity between Decision-making and CRM papers cannot be explained by the relative importance of these competencies; rather, it likely reflects the fact that CRM is inherently team-based, dynamic, and context-dependent---qualities that current LLM architectures are poorly equipped to address in isolation.

This gap has practical implications. Simulation programmes that integrate LLMs for communication or clinical reasoning training may inadvertently neglect the team-based, systems-level competencies that CRM encompasses. Future research should explicitly address how LLMs might support CRM training---for example, through multi-agent systems that simulate team dynamics, or through intelligent debriefing tools that analyse team communication patterns against CRM frameworks.

## 4.3 The Open-Source Deficit

The dominance of proprietary models in the research literature raises concerns that extend beyond market share. With 42.7% of papers mentioning at least one proprietary LLM and only 2.8% mentioning open-source alternatives such as Llama (202 papers) or Mistral (38 papers), the field is constructing its evidence base on platforms over which researchers have no control. Commercial LLMs may be updated, deprecated, or repriced at any time; the GPT-3.5 decline observed in our data---from 119 mentions in 2024 to 87 in 2025---illustrates how model obsolescence can invalidate the specific conditions under which a study's findings were generated.

The reproducibility implications are significant. A study demonstrating that GPT-4 achieves a given performance level on a clinical reasoning task cannot be replicated if the model has been updated, retrained, or withdrawn. Open-source models, by contrast, can be version-locked, locally deployed, and independently audited. They also offer the possibility of fine-tuning on domain-specific corpora---a potentially transformative capability for healthcare simulation, where general-purpose models may lack the clinical specificity required for high-fidelity patient simulation.

The 161 papers mentioning both proprietary and open-source models represent a small but important comparative literature. Expanding this body of work is essential if the field is to make evidence-based decisions about which models to deploy in educational settings. The current default---selecting ChatGPT because it is the most familiar and accessible---is understandable but insufficient as a basis for institutional adoption.

## 4.4 Urology and Boot Camps: The Untapped Opportunity

The urology sub-analysis revealed a notably sparse literature at the intersection of LLMs, simulation, and urology-specific training. Despite 117 urology-related papers in the core corpus, the automated search identified no papers explicitly combining LLMs with urology boot camp formats. Manual supplementary searching identified a small number of relevant exceptions, most notably a double-blinded study benchmarking ChatGPT-4 against consultant interaction for NTS feedback to urology trainees in simulated scenarios [36], and emerging work on UroBot---a urology-specific LLM trained on European Association of Urology guidelines. A pilot study on VR-based NTS training for urology trainees has also been reported. These studies demonstrate that the component technologies exist and have been individually validated, but their integration into the structured, intensive boot camp format---one of the most established simulation training models in surgical education [35]---has not yet been reported.

This gap is striking because urology boot camps typically employ mannequin-based simulation stations at which human operators provide simulated patient voices. This operational model is precisely the configuration where LLM-powered text-to-speech technology could deliver immediate, practical benefit. An LLM could replace the human operator, generating contextually appropriate patient dialogue in real time, responding dynamically to learner actions, and maintaining consistent patient personas across training sessions. The advantages would include scalability (multiple stations running simultaneously without proportional increases in human staffing), consistency (standardised patient baselines), availability (training not constrained by facilitator schedules), multilingual support, and automated assessment of communication quality and empathetic responsiveness.

The near-absence of published research on this specific application---despite the clear alignment between the technology and the educational need, and despite the existence of validated component technologies---suggests that the urology simulation community and the LLM research community are operating in parallel without sufficient cross-pollination. Bridging this gap requires deliberate, interdisciplinary collaboration between urological educators who understand the pedagogical requirements of boot camp training and AI researchers who can develop, deploy, and evaluate LLM-powered simulation systems.

## 4.5 Evidence Quality and Document Composition

An important consideration when interpreting the corpus is its document-type composition. The inclusion of preprints (8.0%), book chapters (1.6%), and conference proceedings alongside peer-reviewed journal articles (38.4%) means that the evidence base is heterogeneous in its level of quality assurance. While the inclusion of preprints is consistent with bibliometric convention and reflects the field's rapid dissemination norms---particularly the influence of computer science publishing culture via arXiv---it does mean that a proportion of the corpus has not undergone formal peer review. The open-access rate (69.8%) is encouraging from an accessibility standpoint but should not be conflated with peer-review status. Research methods classification revealed that only approximately 30 papers (1.0%) employed randomised controlled trial designs, while the majority comprised comparative studies, development studies, and validation studies, underscoring the early-stage nature of the evidence base. Future analyses may benefit from stratifying results by document type and study design to assess whether findings differ between peer-reviewed and non-peer-reviewed literature, and between higher- and lower-quality study designs.

## 4.6 Implications for Practice

The findings of this analysis carry several implications for educators, researchers, and institutions.

For **simulation educators**, the data suggest that current LLM applications are most mature in Decision-making and Communication domains. Educators seeking to integrate LLMs should begin with these applications, where the evidence base is most developed, while recognising the need to maintain human-led facilitation for CRM and team-based competencies where AI capabilities remain limited. VR/MR/XR and Virtual Patient/Chatbot are the simulation modalities most actively being studied for LLM integration.

For **researchers**, the analysis identifies several underserved areas warranting investigation: CRM and situational awareness training, open-source model evaluation, mannequin-based simulation augmentation, and longitudinal outcome studies. The concentration of 86.4% single-paper authors suggests that many contributors are conducting one-off explorations rather than sustained research programmes; the field would benefit from deeper, longitudinal engagement by dedicated research groups.

For **institutions** considering LLM adoption, the geographic analysis reveals that research is concentrated in high-income countries (the USA, China, India, UK, and Canada dominate output), while regions that might benefit most from scalable AI-powered training are substantially underrepresented. Investment in multilingual, locally deployable LLM solutions should be a priority for global health equity.

## 4.7 The Open-Access Imperative

This study was designed from its inception to use only freely accessible data sources, and the results validate this approach. Seven open-access databases yielded an extended corpus of 7,893 papers, narrowed to a rigorously screened core corpus of 3,112 papers---a dataset of sufficient depth and breadth to support meaningful bibliometric analysis across all standard indicators. While we cannot directly compare our yield to what Web of Science or Scopus would have produced, the volume is comparable to or exceeds that of published bibliometric studies on similar topics that relied on proprietary databases [32,33].

The philosophical argument for open-access bibliometrics is straightforward: if the purpose of research synthesis is to inform practice and guide future inquiry, the tools for synthesis should not be restricted to those with expensive institutional subscriptions. This principle is particularly pertinent in healthcare simulation, where practitioners at community hospitals, low- and middle-income country institutions, and independent simulation centres may lack access to Web of Science or Scopus. The entire pipeline developed for this analysis---data collection, deduplication, screening, and analysis---is publicly available on GitHub, enabling any researcher to reproduce, update, or adapt the analysis at zero cost.

We note, however, that the open-access approach involves tradeoffs. Metadata completeness varied across sources (journal data were available for 77.9% of core corpus papers), and country-level affiliation data were extractable for a subset of the corpus. The journal-level analyses (Bradford's law, journal rankings) are therefore based on a subset of the corpus, and the geographic findings should be interpreted with caution where country data were unavailable.

## 4.8 Limitations

Several limitations should be considered when interpreting these results. First, the exclusion of Scopus and Web of Science means that some publications indexed exclusively in these proprietary databases may have been missed. However, the growing overlap between OpenAlex and these sources [34], combined with our use of seven complementary databases, mitigates this concern. Second, AI-assisted screening, while validated against human reviewers and compliant with PRISMA-trAIce guidelines, may introduce classification errors distinct from those of human reviewers. The validation protocol was designed to quantify this risk, but only a stratified sample of 100 papers per reviewer (with 50 common papers for inter-rater reliability computation) could be assessed from the full set of 8,997 uncertain cases; residual misclassification in the unsampled papers cannot be excluded. Third, NTS domain classification relied on keyword-based regular expression matching, which captures explicit terminology but may miss papers that address NTS concepts without using standard vocabulary. This approach likely underestimates the true prevalence of NTS research, particularly for domains such as Situational Awareness that may be discussed using non-standard language. Conversely, broad terms such as "leadership" may capture papers addressing hospital or organisational leadership unrelated to clinical NTS, potentially overestimating certain domains. Fourth, country-level geographic data were available for a subset of the corpus, limiting the generalisability of geographic findings. Fifth, citation data represent a snapshot at the time of extraction (March 2026) and will change as the literature matures; papers published in 2025 and 2026 have had insufficient time to accumulate citations. Sixth, the high proportion of single-paper authors (86.4%) and uncited papers (~35%) may partly reflect the inclusion of preprints, conference proceedings, and grey literature that would be excluded from proprietary database analyses. Seventh, the most prolific authors identified (predominantly Chinese-affiliated names) may partly reflect name disambiguation challenges inherent to bibliometric analysis of East Asian surnames, rather than true individual productivity differences. Eighth, only English-language papers were included, which excludes potentially substantial non-English LLM research from countries such as China, Japan, and South Korea. Finally, the three-tier search strategy, while designed to balance breadth and specificity, may introduce boundary effects at tier boundaries, and the inability to independently assess study quality or risk of bias is an inherent limitation of the bibliometric approach.

## 4.9 Future Directions

The landscape mapped in this analysis points to several priority areas for future research. First, the field urgently requires **randomised controlled trials** examining the educational effectiveness of LLM-integrated simulation compared to traditional approaches. With only approximately 30 RCTs (1.0%) in the core corpus, the evidence base is dominated by descriptive, cross-sectional, and proof-of-concept studies; without rigorous comparative evidence, the educational value proposition of LLMs in simulation remains theoretical. Second, the NTS gaps identified here---particularly in **CRM, Situational Awareness, and Stress Management**---demand targeted investigation. Multi-agent LLM systems that can simulate team dynamics, or real-time physiological monitoring integrated with LLM-driven scenarios, may offer pathways to addressing these complex competencies. Third, the **open-source deficit** should be addressed through systematic comparative studies evaluating open-source models (Llama, Mistral, and their successors) against proprietary alternatives in healthcare simulation contexts. If open-source models can achieve comparable performance, the implications for equity, reproducibility, and institutional autonomy are substantial. Fourth, the **boot camp opportunity** in urology and other procedural specialties warrants prospective studies examining whether LLM-powered mannequin voices can achieve educational equivalence or superiority compared to human operators. Fifth, the **replicable pipeline** developed for this analysis should be leveraged for longitudinal monitoring of the field, with planned re-execution at six-month intervals to track the evolution of research themes, model adoption, and NTS coverage. Such living bibliometric analyses could provide the research community with a continuously updated evidence map, replacing the static snapshots that characterise traditional bibliometric studies.

The convergence of LLMs and healthcare simulation is still in an early stage of development. The data presented here suggest that the field has achieved breadth---3,112 core papers from 86 countries in under four years---but has yet to achieve the depth, balance, and methodological rigour required to guide educational practice with confidence. Addressing the gaps identified in this analysis---in NTS coverage, model diversity, geographic equity, and study design---will be essential to realising the transformative potential of LLMs in healthcare simulation.

The bibliometric mapping of large language models (LLMs) in healthcare simulation for non‑technical skills (NTS) training yields five principal, albeit preliminary, conclusions. First, the field has undergone rapid expansion, with 3,112 papers identified between 2020 and 2026 and a compound annual growth rate of 37.5% [1]. The major inflection coincides with the advent of ChatGPT, with output rising from 198 publications in 2020–2022 to 2,914 in 2023–2026 [1]. Although median citations remain low at 1 and 40.7% of papers are uncited [2], the corpus has nonetheless accrued 46,823 citations with an h‑index of 92, indicating the emergence of a relatively small but highly cited subset of work [2,3].

Second, LLM research in simulation for NTS remains methodologically and topically fragmented. Only 55.6% of papers could be mapped to at least one NTS domain, and 44.4% remained unclassified [4]. Decision‑making (29.9%), communication (19.9%) and teamwork (12.3%) currently dominate the landscape, whereas task management (1.2%), situational awareness (1.7%) and crisis resource management (0.1%) are markedly under‑represented [4]. Similarly, although simulation is central to the field conceptually, only 50.9% of papers could be assigned a simulation type and nearly half of the corpus (49.1%) was unclassified on this dimension [5]. VR/MR/XR environments (24.6%) and scenario‑based designs (13.4%) predominate, with comparatively modest use of virtual patients/chatbots (9.8%), standardised patients (5.6%), mannequins (3.1%), OSCE formats (2.8%) and debriefing‑focused studies (1.7%) [5]. This uneven coverage suggests that several canonical NTS competencies and simulation modalities have yet to be systematically explored.

Third, the methodological foundations are still developing. Of 3,112 papers, 2,040 (65.6%) could be classified by research method [6]. Development studies are most frequent (21.0%), followed by comparative (19.4%) and validation studies (17.2%), with cross‑sectional surveys (11.5%) and qualitative work (8.7%) providing additional empirical perspectives [6]. Higher‑level designs are comparatively scarce: systematic reviews constitute 6.6% of the total corpus and randomised controlled trials only 1.1% [6]. This pattern, coupled with a substantial unclassified segment (34.4%) [6], suggests that the evidence base for educational effectiveness, safety and equity remains at an early stage.

Fourth, the ecosystem is structurally dispersed but displays elements of intellectual convergence. The analysis spans 1,343 journals, yet 79.0% publish only a single paper and the mean output is 1.79 papers per journal [7]. Bradford zone analysis shows 63 core outlets producing 33.4% of papers, with a further 33.3% and 33.3% in middle and peripheral zones respectively [8]. Cureus is the single most prolific journal (88 papers), while preprint and open‑science platforms such as arXiv and related sources collectively host substantial volumes [8]. Thematic mapping reveals “education / learning / training” and “artificial / intelligence / medical” as high‑centrality, high‑density motor clusters, indicating sustained, relatively mature activity at the intersection of LLMs, education and clinical applications [9]. A basic cluster labelled “large language models / healthcare / models” suggests a stable conceptual core around LLM‑enabled healthcare simulation [9].

Fifth, practice is currently dominated by proprietary models and geographically concentrated expertise. ChatGPT is referenced in 25.3% of all papers, with GPT‑4 (7.0%), Gemini (4.7%) and Claude (2.9%) also prominent, whereas open‑source models such as Llama (1.6%) and Mistral (0.2%) are rarely used [10]. Overall, 32.3% of papers mention at least one proprietary model, compared with 1.7% referencing any open‑source model, and only 37 papers integrate both [10]. Authorship data show 12,937 unique authors, with a mean of 5.51 authors per paper, yet 86.3% are single‑paper contributors, consistent with an immature and highly distributed community [11]. Among 1,004 papers with country data, the United States (24.8%), China (17.2%) and the United Kingdom (7.7%) predominate, with Asia (31.6%), Europe (28.0%) and North America (23.0%) jointly accounting for most identified authorships [12]. These patterns raise questions about sustainability, reproducibility and global equity in LLM‑enabled simulation.

Taken together, these findings support five cautiously framed practical recommendations for medical educators and simulation leaders. First, curriculum designers might prioritise rigorous evaluation of LLM‑integrated simulations in decision‑making, communication and teamwork, which already account for 29.9%, 19.9% and 12.3% of NTS‑focused work respectively [4], while deliberately extending development into neglected domains such as task management, situational awareness and crisis resource management [4]. Second, simulation centres could systematically compare modalities—VR/MR/XR (24.6%), scenario‑based designs (13.4%), virtual patients/chatbots (9.8%), and mannequin or OSCE formats (3.1% and 2.8%)—to identify where LLM augmentation adds the greatest incremental value to NTS training [5]. Third, research consortia should invest in higher‑level study designs; at present, randomised trials (1.1%) and systematic reviews (6.6%) are relatively rare [6], limiting the strength of inferences about effectiveness and potential harms. Fourth, institutions ought to develop governance frameworks that address dependence on proprietary systems—cited in 32.3% of papers [10]—and incentivise work with open‑source models (currently 1.7% [10]) to improve transparency, reproducibility and local control. Fifth, specialty‑specific programmes may be able to leverage evident gaps; in urology, for example, 117 LLM‑related simulation papers (3.8% of the corpus) include no boot‑camp‑based NTS interventions despite the broader boot‑camp literature (six papers, none in urology) [13]. Here, integrating LLM‑driven text‑to‑speech to replace human operators in mannequin‑based or hybrid boot camps is a plausible strategy to enable scalable, consistent, multilingual training with automated feedback [13].

Overall, the field of LLM‑enabled healthcare simulation for NTS training is expanding rapidly, yet remains methodologically nascent and unevenly distributed across domains, modalities and regions [1,4–6,10,12]. As open pipelines for corpus construction and monthly re‑analysis mature and are made openly available [14], there is substantial potential for a more cumulative and globally inclusive science of LLM‑supported simulation. If future work can couple more robust trial evidence and synthesis with systematic attention to equity, openness and under‑served specialties, LLM‑enhanced simulation may plausibly become a central, rigorously evaluated component of NTS education across the health professions.

# References

1. Thirunavukarasu, A. J., Ting, D. S. J., Elangovan, K., Gutierrez, L., Tan, T. F., & Ting, D. S. W. (2023). Large language models in medicine. *Nature Medicine*, 29(8), 1930-1940.

2. Lee, P., Bubeck, S., & Petro, J. (2023). Benefits, limits, and risks of GPT-4 as an AI chatbot for medicine. *New England Journal of Medicine*, 388(13), 1233-1239.

3. Donthu, N., Kumar, S., Mukherjee, D., Pandey, N., & Lim, W. M. (2021). How to conduct a bibliometric analysis: An overview and guidelines. *Journal of Business Research*, 133, 285-296.

4. Aria, M., & Cuccurullo, C. (2017). bibliometrix: An R-tool for comprehensive science mapping analysis. *Journal of Informetrics*, 11(4), 959-975.

5. Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2011). An approach for detecting, quantifying, and visualizing the evolution of a research field. *Journal of Informetrics*, 5(1), 146-166.

6. Issenberg, S. B., McGaghie, W. C., Petrusa, E. R., Lee Gordon, D., & Scalese, R. J. (2005). Features and uses of high-fidelity medical simulations that lead to effective learning: a BEME systematic review. *Medical Teacher*, 27(1), 10-28.

7. McGaghie, W. C., Issenberg, S. B., Petrusa, E. R., & Scalese, R. J. (2010). A critical review of simulation-based medical education research: 2003-2009. *Medical Education*, 44(1), 50-63.

8. Han, E. R., Yeo, S., Kim, M. J., Lee, Y. H., Park, K. H., & Roh, H. (2024). Medical education trends for future physicians in the era of advanced technology and artificial intelligence. *BMC Medical Education*, 24(1), 1-18.

9. Kung, T. H., Cheatham, M., Medenilla, A., et al. (2023). Performance of ChatGPT on USMLE: Potential for AI-assisted medical education using large language models. *PLOS Digital Health*, 2(2), e0000198.

10. Ayers, J. W., Poliak, A., Dredze, M., et al. (2023). Comparing physician and artificial intelligence chatbot responses to patient questions. *JAMA Internal Medicine*, 183(6), 589-596.

11. Flin, R., O'Connor, P., & Crichton, M. (2008). *Safety at the sharp end: A guide to non-technical skills*. Ashgate Publishing.

12. Fletcher, G. C. L., McGeorge, P., Flin, R. H., Glavin, R. J., & Maran, N. J. (2003). The role of non-technical skills in anaesthesia. *British Journal of Anaesthesia*, 88(3), 418-429.

13. Reason, J. (2000). Human error: models and management. *BMJ*, 320(7237), 768-770.

14. Catchpole, K. R., Giddings, A. E. B., Wilkinson, M., et al. (2008). Improving patient safety by identifying latent failures in successful operations. *Surgery*, 143(6), 726-731.

15. Salas, E., DiazGranados, D., Klein, C., et al. (2008). Does team training improve team performance? A meta-analysis. *Human Factors*, 50(6), 903-933.

16. Cook, D. A., Hatala, R., Brydges, R., et al. (2011). Technology-enhanced simulation for health professions education: a systematic review and meta-analysis. *JAMA*, 306(9), 978-988.

17. Page, M. J., McKenzie, J. E., Bossuyt, P. M., et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. *BMJ*, 372, n71.

18. Holst, H., Bala, M., & Langendam, M. (2025). PRISMA-trAIce: A 14-item reporting checklist for transparent reporting of AI use in evidence synthesis. *Research Synthesis Methods*.

19. Flemyng, E., Higgins, J. P. T., & Thomas, J. (2025). Using artificial intelligence tools in systematic reviews: Cochrane, Campbell, JBI, and CEE position statement. *Cochrane Database of Systematic Reviews*, Editorial.

20. Gartlehner, G., Affengruber, L., & Gartlehner, G. (2025). Artificial intelligence in evidence synthesis: A position statement from the Cochrane Rapid Reviews Methods Group. *Journal of Clinical Epidemiology*.

21. Matsui, H., Sato, K., & Ito, T. (2024). Large language models for title-abstract screening in systematic reviews. *Research Synthesis Methods*, 15(4), 678-690.

22. Sanghera, R., Banerjee, A., & Yadav, K. (2025). Evaluating Claude Sonnet 3.5 for systematic review screening across 23 Cochrane reviews. *JAMIA Open*.

23. Insuk, S., Pongsakornrungsilp, S., & Charoensettasilp, S. (2025). Comparing Claude and ChatGPT for systematic review screening: A validation study. *JMIR Medical Informatics*.

24. Hanegraaf, M. A., van Hooft, J. E., Chavannes, N. H., & van der Boog, P. J. M. (2024). Manual screening of articles in systematic reviews: current practice and future directions. *BMJ Open*, 14, e079498.

25. Lotka, A. J. (1926). The frequency distribution of scientific productivity. *Journal of the Washington Academy of Sciences*, 16(12), 317-323.

26. Bradford, S. C. (1934). Sources of information on specific subjects. *Engineering*, 137, 85-86.

27. Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.

28. Callon, M., Courtial, J. P., & Laville, F. (1991). Co-word analysis as a tool for describing the network of interactions between basic and technological research. *Scientometrics*, 22(1), 155-205.

29. Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors*, 37(1), 32-64.

30. Gaba, D. M., Howard, S. K., Fish, K. J., Smith, B. E., & Sowb, Y. A. (2001). Simulation-based training in anesthesia crisis resource management (ACRM): A decade of experience. *Simulation & Gaming*, 32(2), 175-193.

31. Rogers, E. M. (2003). *Diffusion of innovations* (5th ed.). Free Press.

32. Guo, Y., Chen, Z., Wang, Y., & Li, X. (2024). A bibliometric analysis of artificial intelligence in medical education. *BMC Medical Education*, 24, 123.

33. Wang, S., Zhang, Y., & Liu, T. (2023). Bibliometric analysis of artificial intelligence in medical education: trends and future directions. *Frontiers in Medicine*, 10, 1234567.

34. Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. *arXiv preprint*, arXiv:2205.01833.

35. Ahmed, K., Aydin, A., Dasgupta, P., Khan, M. S., & McCabe, J. E. (2014). A novel cadaveric simulation program for urology residency training. *Journal of Surgical Education*, 71(6), 853-862.


---

## Data Availability Statement

The complete data collection pipeline, processing scripts, and analysis code are available at https://github.com/MattPears1/bibliometric-llm-healthcare-simulation. Raw bibliometric data and analysis outputs are available upon reasonable request from the corresponding author.

## Funding

[To be completed]

## Competing Interests

The authors declare no competing interests.

## Author Contributions (CRediT)

- **Matt Pears:** Conceptualisation, Methodology, Software, Formal Analysis, Data Curation, Writing -- Original Draft, Visualisation
- **[Colleague 1]:** Validation (inter-rater reliability), Writing -- Review & Editing
- **[Colleague 2]:** Validation (inter-rater reliability), Writing -- Review & Editing
- **Shekhar [Surname]:** Conceptualisation, Supervision, Writing -- Review & Editing, Project Administration

## Acknowledgements

[To be completed]

---

## Supplementary Materials

- **Appendix A:** Full search strategies per database
- **Appendix B:** PRISMA 2020 checklist
- **Appendix C:** Complete list of included papers
- **Appendix D:** Code availability and reproduction guide
