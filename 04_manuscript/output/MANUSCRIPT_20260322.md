---
title: "Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape"
authors:
  - Matt Pears (First Author)
  - "[Colleague 1]"
  - "[Colleague 2]"
  - "Shekhar [Surname] (Corresponding Author)"
date: 2026-03-22
---

# Abstract

**Background:** The rapid proliferation of large language models (LLMs) in healthcare education since the release of ChatGPT in November 2022 has created an urgent need for systematic landscape mapping. No comprehensive bibliometric analysis has examined the intersection of LLMs, healthcare simulation, and non-technical skills (NTS) training. This study addresses that gap using exclusively free, open-access data sources to ensure full reproducibility.

**Methods:** Seven electronic databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ) were systematically searched using 35 query strategies across a three-tier framework: Tier 1 (LLM + medical), Tier 2 (+ simulation), and Tier 3 (+ non-technical skills). A two-stage screening process combined automated keyword pre-filtering with AI-assisted context screening. Bibliometric analyses included publication trends, Lotka's and Bradford's laws, Callon's strategic thematic diagram, citation analysis, geographic distribution, and NTS domain classification. The complete pipeline is publicly available on GitHub for six-monthly reproduction.

**Results:** From 100,277 initial records across seven databases, 86,635 unique papers were identified after three-tier deduplication (13.6% overlap rate). Following two-stage screening, 12,645 papers were included, of which 3,134 specifically addressed NTS. Publication growth followed a compound annual growth rate of 35.6%, with 92.8% of output occurring post-ChatGPT launch. The corpus demonstrated an h-index of 195 and 245,388 total citations. Author productivity closely followed Lotka's law (β = 2.06, R² = 0.908), while journal distribution conformed to Bradford's law with 75 core journals. ChatGPT dominated LLM mentions (29.7%), with proprietary models accounting for 34.8% of papers versus only 1.7% for open-source alternatives. Among NTS domains, decision-making and communication were most studied, while crisis resource management and situational awareness were critically under-researched. The urology sub-analysis identified 319 papers but zero combining LLMs with simulation boot camps, confirming a significant research gap. Five thematic clusters were identified on the strategic diagram, with simulation and generative applications emerging as the dominant motor theme.

**Conclusions:** This bibliometric analysis reveals an explosively growing but unevenly distributed research landscape. The field is characterised by proprietary model dominance, geographic concentration in the United States and China, and significant gaps in NTS domains critical to patient safety. The replicable, open-access pipeline presented here democratises bibliometric analysis for independent researchers and enables ongoing landscape monitoring as this rapidly evolving field matures.

**Keywords:** bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education; open access

# 1. Introduction

The release of ChatGPT in November 2022 marked an inflection point in the adoption of artificial intelligence across virtually every domain of professional practice, and healthcare education has been no exception. Large language models (LLMs)---deep neural networks trained on vast corpora of text to generate, summarise, and reason over natural language---have rapidly moved from curiosity to consequential tool in medical training, assessment, and clinical decision support (Thirunavukarasu et al., 2023; Lee et al., 2023). The speed of this transformation has been extraordinary: in the three years following the launch of ChatGPT, the volume of scholarly output examining LLMs in healthcare contexts has increased by more than fifteen-fold relative to the preceding period, with a compound annual growth rate of 45.7% (present study). Yet the very pace of this expansion poses a fundamental challenge for educators, policymakers, and researchers seeking to understand what is known, what remains uncertain, and where the field should direct its attention next.

Bibliometric analysis offers a systematic, quantitative approach to mapping scientific landscapes at scale (Donthu et al., 2021). By applying established bibliometric laws and indicators---including Lotka's law of author productivity, Bradford's law of journal scattering, and Callon's strategic thematic diagram---researchers can identify patterns in publication growth, intellectual structure, and thematic evolution that would be invisible to narrative review alone (Aria and Cuccurullo, 2017; Cobo et al., 2011). Bibliometric methods are particularly well suited to rapidly expanding fields where the literature is too voluminous for traditional synthesis yet too immature for definitive systematic review. The intersection of LLMs and healthcare simulation represents precisely such a field.

## 1.1 Background

Healthcare simulation has been a cornerstone of medical education for over two decades, providing learners with opportunities to practise clinical skills in controlled, low-risk environments (Issenberg et al., 2005; McGaghie et al., 2010). Simulation-based education encompasses a broad continuum of modalities, from low-fidelity bench models and standardised patient encounters to high-fidelity mannequin scenarios and immersive virtual reality environments. Its value is particularly well established in procedural disciplines---including surgery, emergency medicine, and anaesthesia---where it serves both as a formative training tool and a summative assessment platform, exemplified by the Objective Structured Clinical Examination.

The emergence of LLMs introduces new possibilities across this continuum. Generative AI systems can simulate realistic patient interactions for communication training, generate scenario content for debriefing exercises, provide automated feedback on clinical reasoning, and even serve as intelligent tutoring agents capable of adapting to individual learner performance (Han et al., 2024). Early applications have demonstrated the capacity of models such as GPT-4 and Claude to pass medical licensing examinations, generate clinically plausible case vignettes, and role-play standardised patients with sufficient fidelity to support meaningful educational encounters (Kung et al., 2023; Ayers et al., 2023). These capabilities have prompted considerable enthusiasm but also legitimate concern regarding accuracy, bias, hallucination, and the pedagogical implications of replacing human interaction with machine-generated dialogue.

## 1.2 Simulation-Based Education and Non-Technical Skills

While much early research on LLMs in healthcare has focused on knowledge retrieval and clinical reasoning---tasks closely aligned with technical competence---the role of these technologies in training non-technical skills (NTS) remains substantially less explored. Non-technical skills encompass the cognitive, social, and interpersonal competencies essential for safe, effective clinical practice, including communication, teamwork, leadership, decision-making, situational awareness, and stress management (Flin et al., 2008; Fletcher et al., 2003). These competencies are widely recognised as critical contributors to patient safety, with failures in NTS implicated in a significant proportion of adverse events and near-misses across healthcare settings (Reason, 2000; Catchpole et al., 2008).

Simulation-based training is the predominant method for developing NTS in healthcare professionals. Structured programmes---often incorporating crisis resource management principles, standardised patient encounters, and facilitated debriefing---have demonstrated measurable improvements in team performance, communication quality, and leadership behaviours (Salas et al., 2008; Cook et al., 2011). Validated assessment instruments such as the Non-Technical Skills for Surgeons (NOTSS), the Anaesthetists' Non-Technical Skills (ANTS) framework, and the NOTECHS system provide standardised means of evaluating these competencies in simulated and clinical environments.

The potential for LLMs to augment NTS training is conceptually compelling but empirically underdeveloped. An AI-generated simulated patient could provide unlimited opportunities for practising breaking bad news, conducting consent discussions, or managing difficult team dynamics. An LLM-powered debriefing assistant could offer structured post-scenario feedback aligned with established frameworks. Yet the literature examining these applications remains fragmented, and no comprehensive mapping of the research landscape currently exists.

## 1.3 Rationale and Objectives

This study was motivated by three observations. First, the research on LLMs in healthcare simulation is growing at a rate that outstrips the capacity of traditional narrative or systematic reviews to maintain currency. A bibliometric approach enables quantitative landscape mapping at a scale that is both comprehensive and reproducible. Second, despite growing interest in the intersection of AI and medical education, no published bibliometric analysis has specifically examined LLMs in the context of healthcare simulation for non-technical skills training. This represents a significant gap, given the centrality of NTS to patient safety and the potential for AI to transform how these skills are taught and assessed. Third, existing bibliometric studies in medical education overwhelmingly rely on proprietary databases such as Web of Science and Scopus, creating a paradox in which the tools for understanding the research landscape are themselves locked behind institutional paywalls. We argue that bibliometric infrastructure should be as open as the research it seeks to map.

This analysis forms one component of a broader research programme examining the integration of LLMs into healthcare simulation. Companion studies include a Delphi consensus study on LLM implementation in simulation-based education, a scoping review of specific LLM applications, and a platform evaluation of the Simuro simulation system. Together, these workstreams aim to provide an evidence base that is not only rigorous but practically actionable for educators, simulation centres, and curriculum designers.

To address these gaps, this study employs a three-tier analytical framework that progressively narrows the focus from the broadest intersection of LLMs and healthcare (Tier 1: 12,645 papers), through the addition of simulation-specific literature (Tier 2), to the most focused subset examining non-technical skills (Tier 3: 3,134 papers). This tiered approach permits simultaneous analysis of the macro-level research landscape and the micro-level dynamics of the NTS domain.

The specific objectives of this study are:

1. To map the publication landscape of LLMs in healthcare simulation from 2020 to 2026, characterising growth trajectories, geographic distribution, and journal concentration.
2. To identify the dominant research themes, intellectual clusters, and emergent topics through keyword co-occurrence analysis and Callon's strategic thematic diagram.
3. To analyse the distribution of research across seven non-technical skills domains---communication, teamwork, leadership, decision-making, situational awareness, stress management, and crisis resource management---identifying which competencies are well served by existing research and which represent critical gaps.
4. To provide a fully replicable, open-access bibliometric pipeline, built exclusively on free data sources, that any researcher can execute to reproduce or update this analysis without requiring institutional database subscriptions.

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

Automated keyword matching across four categories (LLM, simulation, NTS, and medical terms) classified each paper as a definite include (at least five cross-category matches with at least one LLM term), definite exclude (zero LLM terms), or uncertain. This yielded 3,316 definite includes, 69,472 definite excludes, and 8,213 uncertain cases.

### 2.4.2 Stage 2: AI-Assisted Screening

Uncertain papers were screened using Claude (Anthropic, claude-sonnet-4-20250514), following PRISMA-trAIce (Holst et al., 2025) and RAISE recommendations (Version 2, 2025). This approach aligns with methodological guidance permitting AI as a second reviewer (Flemyng et al., 2025; Gartlehner et al., 2025) and has been validated in studies demonstrating human-comparable screening accuracy (Matsui et al., 2024; Sanghera et al., 2025; Insuk et al., 2025). Each paper's title and abstract were assessed against the inclusion criteria, returning a decision, confidence level, and rationale. Papers were processed in batches of ten. Complete prompts and model parameters are documented in the project repository.

### 2.4.3 Validation

Inter-rater reliability was assessed on a stratified random sample of 100 papers per reviewer, with 50 common papers reviewed independently by three human reviewers. The sample was stratified equally between included and excluded papers. Cohen's kappa was computed for all pairwise comparisons, following the benchmarks of Hanegraaf et al. (2024), who reported a mean human-human kappa of 0.82 for abstract screening. The human reviewer retained final authority in all disagreements.

Following screening, 12,645 papers were included: 6,210 at Tier 1, 514 at Tier 2, and 3,134 at Tier 3, with 2,787 classified outside the tier structure. The PRISMA flow diagram (Figure 1) details the selection process.

## 2.5 Inclusion and Exclusion Criteria

Papers were included if they: (a) addressed LLMs, generative AI, or a named system (e.g., ChatGPT, GPT-4, Claude, Gemini); (b) were situated within a healthcare or clinical context; and (c) were published between January 2020 and March 2026 in English. Tier 2 additionally required a simulation or training dimension. Tier 3 additionally required at least one NTS domain. Papers were excluded if they addressed traditional machine learning without an LLM component, clinical AI without an educational dimension, purely technical topics without a healthcare context, or were editorials or commentaries without original data.

## 2.6 Bibliometric Analysis

All analyses were performed in Python. **Performance analysis** encompassed annual publication trends with compound annual growth rate; citation metrics (h-index, g-index, i10-index); author productivity assessed against Lotka's law (Lotka, 1926); and journal concentration assessed against Bradford's law (Bradford, 1934). **Science mapping** involved keyword co-occurrence network construction, filtered to retain pairs co-occurring in at least two papers and individual keywords appearing in at least three papers. Community detection used the Louvain algorithm (Blondel et al., 2008). Callon's strategic thematic diagram (Callon et al., 1991) was constructed by computing centrality (external cohesion) and density (internal cohesion) for each cluster, dividing the space into four quadrants at the mean values: motor themes, niche themes, basic themes, and emerging or declining themes. **NTS domain classification** used regular expression pattern matching across seven domains, capturing both explicit terminology and implicit references (e.g., "empathy," "shared mental model"). **Geographic analysis** extracted country-level authorship from affiliations, defining international collaboration as multi-country authorship.

## 2.7 Open-Access Data Philosophy

This analysis was designed from inception to use only freely accessible data sources, tools, and infrastructure. We contend that bibliometric instruments should not be restricted to those with institutional subscriptions---a position particularly pertinent in healthcare simulation, where educators and researchers in low- and middle-income settings may lack access to proprietary platforms. The complete pipeline is publicly available on GitHub and designed for re-execution at six-month intervals, enabling longitudinal field monitoring without repeating manual effort.

# 3. Results

## 3.1 Search Results and Study Selection

The systematic search across seven open-access databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ) yielded 92,941 raw records. After applying the three-stage deduplication algorithm---exact DOI matching, fuzzy title matching, and author-year-title fragment matching---11.5% of records were identified as duplicates, leaving 81,001 unique records for screening. The keyword pre-filter classified 3,316 papers as definite includes, 69,472 as definite excludes, and 8,213 as uncertain. AI-assisted screening of the uncertain cases, followed by human validation, produced a final included corpus of 11,529 papers. Of these, 10,417 contained sufficient metadata for full bibliometric analysis: 5,029 at Tier 1 (LLMs in healthcare), 442 at Tier 2 (LLMs in healthcare simulation), and 2,667 at Tier 3 (LLMs in healthcare simulation and NTS), with 2,279 classified outside the tier structure. The complete selection process is presented in the PRISMA flow diagram (Figure 1).

Data completeness across the included corpus was generally high: citation data were available for 100.0% of papers, year for 100.0%, author data for 99.0%, DOI for 97.2%, abstract for 93.6%, keywords for 81.1%, and journal information for 65.5%. OpenAlex contributed the largest share of records (62.2%), followed by Europe PMC (23.6%), Crossref (12.0%), and CORE (2.1%). Open-access papers accounted for 76.7% of the corpus (n = 7,993), consistent with the broader trend toward open publishing in biomedical fields.

## 3.2 Publication Trends

The corpus exhibited explosive growth over the study period, with a compound annual growth rate (CAGR) of 45.7% from 2020 to 2025 (Table 1; Figure 2). Publication volume followed a clear inflection point coinciding with the release of ChatGPT in November 2022. The pre-ChatGPT period (2020--2022) accounted for only 640 papers (6.1% of the corpus), while the post-ChatGPT period (2023--2026) contributed 9,772 papers (93.9%). Annual output nearly tripled between 2020 (n = 112) and 2022 (n = 320), but the post-ChatGPT acceleration was far steeper: 1,442 papers in 2023, 2,833 in 2024, and 4,424 in 2025---the peak year, accounting for 42.5% of all publications. Data for 2026 (n = 1,073 through March) suggest the trajectory may continue, though partial-year figures preclude definitive projection.

The transition from 2022 to 2023 represents a 4.5-fold increase in annual output, the single largest year-on-year surge in the dataset. This growth rate is consistent with broader bibliometric evidence on generative AI in biomedicine (Guo et al., 2024) and exceeds the typical diffusion curves observed for other health technology innovations, underscoring the disruptive character of LLM adoption in healthcare research. The median publication year across the corpus was 2025, confirming that the literature is overwhelmingly recent.

## 3.3 Citation Analysis

The 10,417 papers with citation data accumulated a total of 168,407 citations, yielding a mean of 16.17 citations per paper and a median of 1 (Table 2). The distribution was heavily right-skewed: 40.6% of papers (n = 4,225) remained uncited at the time of data extraction, while a small number of highly cited works exerted disproportionate influence. The corpus h-index was 155, meaning 155 papers received at least 155 citations each. The g-index was 287, and the i10-index (papers with 10 or more citations) was 2,696.

Citation intensity varied substantially by publication year. Papers published in 2020 achieved the highest mean citation count (97.0 per paper), reflecting both their longer citation window and their status as foundational contributions. The 2023 cohort accumulated the greatest total citations (73,500), driven by a combination of volume and the field's peak intensity of scholarly attention to generative AI. By contrast, the 2025 cohort (mean 2.9 citations) and 2026 cohort (mean 0.1 citations) had insufficient time to accrue citations, consistent with the well-established citation lag in biomedical publishing.

The most cited paper in the corpus was "Performance of ChatGPT on USMLE: Potential for AI-Assisted Medical Education" (Kung et al., 2023; 3,341 citations), closely followed by "So what if ChatGPT wrote it? Multidisciplinary perspectives on opportunities, challenges and implications" (Dwivedi et al., 2023; 3,325 citations). The top 20 papers were overwhelmingly published in 2023 and addressed foundational questions about ChatGPT's capabilities, limitations, and educational implications (Table 3). Notably, the highest-cited paper on simulation-specific methodology---"The impact of simulation-based training in medical education: A review" (2024; 598 citations)---appeared at rank 20, suggesting that simulation-focused studies have not yet achieved the citation prominence of broader AI-in-medicine contributions.

## 3.4 Author Analysis

A total of 40,100 unique authors contributed to the 11,426 papers with author data, yielding a collaboration index of 5.30 authors per paper (Table 4). This figure is consistent with contemporary norms in biomedical research and reflects the multidisciplinary nature of LLM research, which frequently requires expertise spanning computer science, clinical medicine, and education.

Author productivity followed Lotka's law with an exponent (beta) of 2.06 and an R-squared of 0.908, indicating an excellent fit to the inverse square distribution. The vast majority of contributors (82.2%; n = 32,981) published a single paper, while only 17.8% (n = 7,119) contributed two or more. This single-to-multi-paper author ratio of 4.63 is characteristic of a young, rapidly expanding field in which many researchers are entering for the first time rather than building sustained programmes of inquiry. The most prolific authors---Wang, Y (145 papers), Li, Y (130 papers), and Zhang, Y (119 papers)---were predominantly Chinese-affiliated researchers (Table 5), reflecting the substantial contribution of Chinese institutions to the global output.

## 3.5 Journal Distribution

The 8,296 papers with identifiable journal or source data were distributed across 3,598 unique outlets (Table 6). The mean output per journal was 2.31 papers, with a median of 1, and 72.7% of journals (n = 2,616) published only a single paper in the field. This high degree of scatter reflects the interdisciplinary nature of the topic, which spans medical education, informatics, clinical specialties, and computer science.

Bradford's law analysis partitioned the journals into three zones of approximately equal article yield (Table 7; Figure 3). Zone 1 (core) contained 75 journals producing 2,776 papers (33.5%), Zone 2 (middle) contained 833 journals producing 2,756 papers (33.2%), and Zone 3 (peripheral) contained 2,690 journals producing 2,764 papers (33.3%). The Bradford multiplier from Zone 1 to Zone 2 was 11.11 (833/75), indicating a high concentration ratio: a small core of journals produces a disproportionate share of the literature, while the vast majority of outlets contribute only marginally.

The single most prolific source was arXiv (462 papers; 5.6%), reflecting the field's substantial preprint culture and the influence of computer science publishing norms. Cureus ranked second (264 papers; 3.2%), followed by BMC Medical Education (100 papers; 1.2%), Scientific Reports (89 papers; 1.1%), and JMIR Medical Education (71 papers combined across variant name entries; 0.9%). The prominence of open-access and preprint platforms among the core journals is consistent with the field's rapid dissemination norms and the broader open-science ethos in AI research.

## 3.6 Geographic Distribution

Country-level authorship data were extractable for 3,294 papers (31.6% of the corpus). These papers originated from 116 countries, reflecting broad global engagement with LLMs in healthcare (Table 8; Figure 4). The United States led in absolute output (796 papers; 24.2% of identified papers), followed by China (558; 16.9%), India (266; 8.1%), the United Kingdom (243; 7.4%), and Canada (197; 6.0%). Collectively, the top five countries accounted for 62.6% of the geographically identified output.

Continental analysis revealed that Asia contributed the largest share of authorships (33.5%), followed by Europe (25.1%), North America (22.5%), and the Middle East (11.6%). Africa (2.7%), Oceania (2.6%), and South America (2.0%) were substantially underrepresented. International collaborations---defined as papers with authors from more than one country---accounted for 21.1% of geographically identified papers (n = 694), suggesting moderate but not dominant cross-border cooperation. The geographic concentration of output in high-income countries raises equity concerns regarding whose perspectives shape the evidence base for LLM integration in healthcare education.

## 3.7 Thematic Mapping

Keyword co-occurrence network analysis identified 14,277 unique keywords forming 267,027 co-occurrence pairs. Community detection via the Louvain algorithm resolved five thematic clusters, which were plotted on Callon's strategic diagram using centrality (external cohesion) and density (internal cohesion) as axes (Table 9; Figure 5).

**Motor themes (high centrality, high density):** Two clusters occupied this quadrant. Cluster 2 ("simulation / generative / challenges"; 923 keywords; centrality 2,142,954; density 1,076.3) represented the most well-developed and central theme in the field, encompassing simulation applications, generative AI challenges, and practical implementation considerations. Cluster 4 ("patient / accuracy / tools"; 774 keywords; centrality 1,706,676; density 638.5) reflected research on clinical accuracy, patient-facing tools, and evaluation methodologies. These motor themes are both internally coherent and strongly connected to the broader research network, indicating mature, driving research programmes.

**Basic themes (high centrality, low density):** Cluster 3 ("artificial / intelligence / education"; 2,111 keywords; centrality 1,432,021; density 130.7) was the largest cluster by keyword count and occupied the basic-theme quadrant, indicating high external relevance but low internal development. This cluster captures the broad, foundational discourse on AI in education---essential to the field but not yet crystallised into a tightly integrated research programme.

**Emerging or declining themes (low centrality, low density):** Cluster 1 ("large language models / models / language"; 809 keywords; centrality 964,720; density 174.9) sat in this quadrant, representing the specific LLM-focused literature that is still coalescing. Given the recency of LLM adoption, this positioning likely reflects emergence rather than decline.

**Niche themes (low centrality, high density):** Cluster 0 ("artificial intelligence / computer science / medicine"; 867 keywords; centrality 388,935; density 194.7) represented a self-contained cluster with strong internal links but limited external connections, suggesting a technically focused community that may benefit from greater integration with educational and clinical stakeholders.

## 3.8 Non-Technical Skills Domains

Regex-based classification across seven NTS domains captured 4,452 papers (42.7% of the corpus) in at least one domain, with 1,245 papers (12.0%) classified into multiple domains (Table 10; Figure 6). Decision-making was the most frequently addressed domain (1,807 papers; 17.3%), followed by Communication (1,568; 15.1%), Teamwork (1,322; 12.7%), and Leadership (1,043; 10.0%). These four domains collectively accounted for the vast majority of NTS-related research.

By contrast, the lower-frequency domains revealed striking gaps. Stress management appeared in only 231 papers (2.2%), Situational awareness in 52 (0.5%), and Crisis Resource Management (CRM) in merely 7 papers (0.1%). The 250-fold disparity between Decision-making and CRM is particularly notable given that CRM principles underpin the design and facilitation of high-fidelity simulation scenarios across emergency medicine, anaesthesia, and surgical disciplines. The near-absence of CRM from the LLM literature suggests that the most simulation-specific NTS domain has been almost entirely overlooked by AI researchers.

Cross-tabulation of simulation types and NTS domains (Table 11) revealed that VR/MR/XR simulations had the broadest NTS coverage, addressing Communication (309 papers), Teamwork (281), Decision-making (193), and Leadership (140). Scenario-based simulations showed a similar pattern at lower volumes. Mannequin-based simulation---the modality most amenable to LLM-powered voice interaction---was represented in only 139 papers total, with minimal CRM engagement (1 paper).

## 3.9 LLM Model Landscape

Named-model classification identified specific LLMs in the corpus, revealing pronounced dominance by proprietary systems (Table 12; Figure 7). ChatGPT (generic, unversioned references) appeared in 3,419 papers (29.7% of the corpus), making it by far the most studied model. GPT-4 followed at 689 papers (6.0%), Gemini at 550 (4.8%), Claude at 267 (2.3%), and GPT-3.5 at 266 (2.3%). The newer GPT-4o appeared in 225 papers (2.0%), and GPT-5 in 37 papers (0.3%), the latter reflecting early-access or speculative references.

The proprietary-open-source divide was stark. Papers mentioning at least one proprietary model numbered 4,016 (34.8%), while those mentioning any open-source model totalled only 201 (1.7%). Llama was the most cited open-source model (179 papers; 1.6%), followed by Mistral (40; 0.3%). Only 139 papers mentioned both proprietary and open-source models, indicating minimal comparative evaluation.

Temporal trends revealed that Gemini exhibited the steepest growth trajectory, rising from 1 paper in 2023 to 107 in 2024, 352 in 2025, and 88 in the first quarter of 2026. Claude showed a similar upward curve (5 in 2023 to 152 in 2025), while GPT-3.5 references declined from 104 in 2024 to 89 in 2025, consistent with model obsolescence. The generic LLM category grew steadily (75 in 2023 to 456 in 2025), suggesting an increasing proportion of studies that discuss LLMs conceptually without specifying a particular model.

## 3.10 Simulation Modalities

Simulation-type classification identified 3,114 papers (27.0% of the corpus) matching at least one simulation modality, with 350 papers (3.0%) addressing multiple types (Table 13; Figure 8). VR/MR/XR was the most prevalent modality (1,537 papers; 13.3%), reflecting the established synergy between immersive technologies and AI. Scenario-based simulation (739; 6.4%) and Virtual Patient/Chatbot (725; 6.3%) were nearly equivalent in representation, the latter capturing the natural application of conversational AI in simulated clinical encounters.

Standardized Patient encounters appeared in 180 papers (1.6%), Mannequin-based simulation in 139 (1.2%), Roleplay and OSCE in 77 each (0.7%), and Debriefing in 64 (0.6%). The relatively low representation of mannequin-based simulation is notable given that this is the modality where LLM-powered text-to-speech could most directly replace human operators, enabling scalable, consistent simulated patient voices without the logistical constraints of human standardized patients.

## 3.11 Urology Sub-Analysis

The urology-specific analysis identified 291 papers (2.5% of the total corpus), confirming that the specialty has engaged with LLM research but at a modest scale relative to the overall field (Table 14). Growth in urology mirrored the broader corpus: only 15 papers appeared during 2020--2022, expanding to 40 in 2023, 97 in 2024, and 118 in 2025 (21 in early 2026).

NTS domain distribution within urology papers followed the corpus-wide pattern, with Decision-making (67 papers; 23.0%), Communication (46; 15.8%), Teamwork (35; 12.0%), and Leadership (22; 7.6%) representing the most common domains. Citation performance was slightly below the corpus mean (12.3 vs. 16.17 citations per paper), possibly reflecting the specialty's later entry into LLM research.

ChatGPT dominated urology LLM mentions (135 papers), followed by Generic LLM (41), Gemini (29), GPT-4 (22), and Claude (11). The most salient finding was the complete absence of papers at the intersection of urology, LLMs, and simulation boot camps: although 8 boot camp papers appeared in the total corpus, none were urology-specific. Given that urology boot camps are an established training format---typically employing mannequin-based simulation with human operators providing simulated patient voices---this represents a clear and actionable research gap.

# 4. Discussion

## 4.1 Principal Findings

This bibliometric analysis mapped the research landscape of large language models in healthcare simulation and non-technical skills training from 2020 to 2026, encompassing 11,529 included papers drawn exclusively from open-access databases. The findings reveal a field undergoing extraordinary expansion---45.7% compound annual growth, a 15-fold post-ChatGPT surge, and contributions from 40,100 authors across 116 countries---yet one characterised by significant structural imbalances that warrant careful consideration.

Five principal findings emerge. First, the literature is overwhelmingly recent and concentrated: 93.9% of all papers were published after the release of ChatGPT in November 2022, with 2025 alone accounting for 42.5% of the corpus. This compressed timeline means the field is building its evidence base in real time, with limited opportunity for the longitudinal validation studies that typically underpin educational innovation. Second, citation analysis reveals a highly skewed distribution (h-index 155, g-index 287) in which a small number of foundational papers---predominantly addressing ChatGPT's performance on medical licensing examinations---attract disproportionate attention, while 40.6% of the literature remains uncited. Third, the NTS landscape is dominated by Decision-making and Communication, with Crisis Resource Management and Situational Awareness almost entirely absent from the discourse. Fourth, proprietary LLMs account for 34.8% of named-model mentions versus only 1.7% for open-source alternatives, creating a research ecosystem dependent on commercial platforms whose terms, capabilities, and pricing may change without notice. Fifth, urology simulation boot camps---an established training format that would appear ideally suited to LLM augmentation---have generated zero publications at this intersection, representing a specific and actionable research gap.

## 4.2 The Non-Technical Skills Gap

The distribution of NTS research across the seven classified domains reveals a hierarchy that reflects convenience rather than clinical importance. Decision-making (1,807 papers; 17.3%) and Communication (1,568; 15.1%) are well represented, likely because these competencies align most naturally with the text-based capabilities of LLMs: clinical reasoning tasks map onto question-answering paradigms, and communication training maps onto conversational interaction. Teamwork (1,322; 12.7%) and Leadership (1,043; 10.0%) occupy a middle ground, studied frequently but often in the context of interprofessional education rather than simulation-specific applications.

The critical deficits lie at the lower end. Stress management (231 papers; 2.2%) is studied infrequently despite its centrality to performance under pressure---the very conditions simulation is designed to replicate. Situational awareness (52 papers; 0.5%) is nearly invisible, despite decades of human factors research establishing it as a prerequisite for safe clinical practice (Endsley, 1995; Flin et al., 2008). Most striking is the near-total absence of Crisis Resource Management (7 papers; 0.1%), a domain that has been foundational to high-fidelity simulation training since its adaptation from aviation by Gaba and colleagues (Gaba et al., 2001). The 250-fold disparity between Decision-making and CRM papers cannot be explained by the relative importance of these competencies; rather, it reflects the fact that CRM is inherently team-based, dynamic, and context-dependent---qualities that current LLM architectures are poorly equipped to address in isolation.

This gap has practical implications. Simulation programmes that integrate LLMs for communication or clinical reasoning training may inadvertently neglect the team-based, systems-level competencies that CRM encompasses. Future research should explicitly address how LLMs might support CRM training---for example, through multi-agent systems that simulate team dynamics, or through intelligent debriefing tools that analyse team communication patterns against CRM frameworks.

## 4.3 The Open-Source Deficit

The dominance of proprietary models in the research literature raises concerns that extend beyond mere market share. With 34.8% of papers mentioning at least one proprietary LLM and only 1.7% mentioning open-source alternatives such as Llama (179 papers) or Mistral (40 papers), the field is constructing its evidence base on platforms over which researchers have no control. Commercial LLMs may be updated, deprecated, or repriced at any time; the GPT-3.5 decline observed in our data---from 104 mentions in 2024 to 89 in 2025---illustrates how model obsolescence can invalidate the specific conditions under which a study's findings were generated.

The reproducibility implications are significant. A study demonstrating that GPT-4 achieves a given performance level on a clinical reasoning task cannot be replicated if the model has been updated, retrained, or withdrawn. Open-source models, by contrast, can be version-locked, locally deployed, and independently audited. They also offer the possibility of fine-tuning on domain-specific corpora---a potentially transformative capability for healthcare simulation, where general-purpose models may lack the clinical specificity required for high-fidelity patient simulation.

The 139 papers mentioning both proprietary and open-source models represent a small but important comparative literature. Expanding this body of work is essential if the field is to make evidence-based decisions about which models to deploy in educational settings. The current default---selecting ChatGPT because it is the most familiar and accessible---is understandable but insufficient as a basis for institutional adoption.

## 4.4 Urology and Boot Camps: The Untapped Opportunity

The urology sub-analysis produced a finding that is notable precisely for its absence. Despite 291 urology-related papers in the corpus and 8 boot camp papers across all specialties, the intersection of these categories was empty: zero papers examine LLMs in the context of urology simulation boot camps. This null finding is significant because urology boot camps represent one of the most structured and well-established simulation training formats in surgical education. These programmes typically employ mannequin-based simulation stations at which human operators provide simulated patient voices, speaking through speakers embedded in the mannequin to guide learners through clinical encounters.

This operational model is precisely the configuration where LLM-powered text-to-speech technology could deliver immediate, practical benefit. An LLM could replace the human operator, generating contextually appropriate patient dialogue in real time, responding dynamically to learner actions, and maintaining consistent patient personas across training sessions. The advantages are substantial: scalability (multiple stations can run simultaneously without proportional increases in human staffing), consistency (every learner encounters the same patient baseline), availability (training is not constrained by facilitator schedules), multilingual support (patients can speak in the learner's language of choice), and automated assessment (conversational data can be analysed to provide structured feedback on communication quality, history-taking completeness, and empathetic responsiveness).

The absence of published research on this application---despite the clear alignment between the technology and the educational need---suggests that the urology simulation community and the LLM research community are operating in parallel without meaningful cross-pollination. Bridging this gap requires deliberate, interdisciplinary collaboration between urological educators who understand the pedagogical requirements of boot camp training and AI researchers who can develop, deploy, and evaluate LLM-powered simulation systems.

## 4.5 Implications for Practice

The findings of this analysis carry several implications for educators, researchers, and institutions.

For **simulation educators**, the data suggest that current LLM applications are most mature in Decision-making and Communication domains. Educators seeking to integrate LLMs should begin with these applications, where the evidence base is most developed, while recognising the need to maintain human-led facilitation for CRM and team-based competencies where AI capabilities remain limited. The dominance of VR/MR/XR (1,537 papers) and Virtual Patient/Chatbot (725 papers) as simulation modalities indicates that these are the formats most actively being studied for LLM integration.

For **researchers**, the analysis identifies several underserved areas warranting investigation: CRM and situational awareness training, open-source model evaluation, mannequin-based simulation augmentation, and longitudinal outcome studies. The concentration of 82.2% single-paper authors suggests that many contributors are conducting one-off explorations rather than sustained research programmes; the field would benefit from deeper, longitudinal engagement by dedicated research groups.

For **institutions** considering LLM adoption, the geographic analysis reveals that research is concentrated in high-income countries (the USA, China, UK, and Canada account for 54.5% of identified output), while regions that might benefit most from scalable AI-powered training---Africa (2.7%), South America (2.0%)---are substantially underrepresented. Investment in multilingual, locally deployable LLM solutions should be a priority for global health equity.

## 4.6 The Open-Access Imperative

This study was designed from its inception to use only freely accessible data sources, and the results validate this approach. Seven open-access databases yielded 11,529 included papers---a corpus of sufficient depth and breadth to support meaningful bibliometric analysis across all standard indicators. While we cannot directly compare our yield to what Web of Science or Scopus would have produced, the volume is comparable to or exceeds that of published bibliometric studies on similar topics that relied on proprietary databases (Guo et al., 2024; Wang et al., 2023).

The philosophical argument for open-access bibliometrics is straightforward: if the purpose of research synthesis is to inform practice and guide future inquiry, the tools for synthesis should not be restricted to those with expensive institutional subscriptions. This principle is particularly pertinent in healthcare simulation, where practitioners at community hospitals, low- and middle-income country institutions, and independent simulation centres may lack access to Web of Science or Scopus. The entire pipeline developed for this analysis---data collection, deduplication, screening, and analysis---is publicly available on GitHub, enabling any researcher to reproduce, update, or adapt the analysis at zero cost.

We note, however, that the open-access approach involves tradeoffs. Metadata completeness varied across sources (journal data were available for only 65.5% of papers), and country-level affiliation data were extractable for only 31.6% of the corpus. These limitations are acknowledged below and represent areas where open-access databases could improve their coverage.

## 4.7 Limitations

Several limitations should be considered when interpreting these results. First, the exclusion of Scopus and Web of Science means that some publications indexed exclusively in these proprietary databases may have been missed. However, the growing overlap between OpenAlex and these sources (Priem et al., 2022), combined with our use of seven complementary databases, mitigates this concern. Second, AI-assisted screening, while validated against human reviewers and compliant with PRISMA-trAIce guidelines, may introduce classification errors distinct from those of human reviewers. The validation protocol was designed to quantify this risk, but residual misclassification cannot be excluded. Third, NTS domain classification relied on keyword-based regular expression matching, which captures explicit terminology but may miss papers that address NTS concepts without using standard vocabulary. This approach likely underestimates the true prevalence of NTS research, particularly for domains such as Situational Awareness that may be discussed using non-standard language. Fourth, country-level geographic data were available for only 31.6% of the corpus, limiting the generalisability of geographic findings. Fifth, citation data represent a snapshot at the time of extraction (March 2026) and will change as the literature matures; papers published in 2025 and 2026 have had insufficient time to accumulate citations. Sixth, the high proportion of single-paper authors (82.2%) and uncited papers (40.6%) may partly reflect the inclusion of preprints, conference proceedings, and grey literature that would be excluded from proprietary database analyses. Finally, the three-tier search strategy, while designed to balance breadth and specificity, may introduce boundary effects at tier boundaries.

## 4.8 Future Directions

The landscape mapped in this analysis points to several priority areas for future research. First, the field urgently requires **randomised controlled trials** examining the educational effectiveness of LLM-integrated simulation compared to traditional approaches. The current literature is dominated by descriptive, cross-sectional, and proof-of-concept studies; without rigorous comparative evidence, the educational value proposition of LLMs in simulation remains theoretical. Second, the NTS gaps identified here---particularly in **CRM, Situational Awareness, and Stress Management**---demand targeted investigation. Multi-agent LLM systems that can simulate team dynamics, or real-time physiological monitoring integrated with LLM-driven scenarios, may offer pathways to addressing these complex competencies. Third, the **open-source deficit** should be addressed through systematic comparative studies evaluating open-source models (Llama, Mistral, and their successors) against proprietary alternatives in healthcare simulation contexts. If open-source models can achieve comparable performance, the implications for equity, reproducibility, and institutional autonomy are substantial. Fourth, the **boot camp opportunity** in urology and other procedural specialties warrants prospective studies examining whether LLM-powered mannequin voices can achieve educational equivalence or superiority compared to human operators. Fifth, the **replicable pipeline** developed for this analysis should be leveraged for longitudinal monitoring of the field, with planned re-execution at six-month intervals to track the evolution of research themes, model adoption, and NTS coverage. Such living bibliometric analyses could provide the research community with a continuously updated evidence map, replacing the static snapshots that characterise traditional bibliometric studies.

The convergence of LLMs and healthcare simulation is still in its early chapters. The data presented here suggest that the field has achieved breadth---11,529 papers from 116 countries in under four years---but has yet to achieve the depth, balance, and methodological rigour required to guide educational practice with confidence. Addressing the gaps identified in this analysis---in NTS coverage, model diversity, geographic equity, and study design---will be essential to realising the transformative potential of LLMs in healthcare simulation.

# 5. Conclusions

This bibliometric analysis provides the first comprehensive, open-access mapping of the research landscape at the intersection of large language models, healthcare simulation, and non-technical skills training. Drawing on 11,529 papers from seven freely accessible databases, the study reveals a field that has grown at a compound annual growth rate of 45.7%, with 93.9% of all publications appearing after the release of ChatGPT in November 2022. The corpus spans 116 countries, 3,598 journals, and 40,100 unique authors, confirming that LLMs in healthcare have rapidly become a global research priority.

Five key findings merit emphasis. First, the research landscape is characterised by significant thematic imbalance in non-technical skills coverage. Decision-making (1,807 papers) and Communication (1,568 papers) dominate the literature, while Crisis Resource Management (7 papers), Situational Awareness (52 papers), and Stress Management (231 papers) remain critically underexplored. Given the foundational role of CRM in high-fidelity simulation training and its direct relevance to patient safety, this 250-fold disparity between Decision-making and CRM represents the most consequential gap identified in this analysis.

Second, the field's dependence on proprietary LLMs---34.8% of papers referencing a commercial model versus 1.7% citing an open-source alternative---creates vulnerabilities in reproducibility, equity, and institutional autonomy. Research findings generated on commercial platforms that may be updated or withdrawn cannot be independently verified, and institutions in resource-limited settings may be unable to replicate reported implementations.

Third, the complete absence of publications at the intersection of LLMs, urology, and simulation boot camps identifies a specific, actionable research opportunity. LLM-powered text-to-speech technology is well suited to replace human operators at mannequin-based simulation stations, offering scalability, consistency, and availability advantages that could transform boot camp delivery.

Fourth, geographic analysis reveals that high-income countries produce the majority of the evidence base, with Africa (2.7%) and South America (2.0%) substantially underrepresented. Equitable access to LLM-powered educational tools requires deliberate investment in multilingual, locally deployable, open-source solutions.

Fifth, the open-access bibliometric pipeline developed for this study demonstrates that rigorous, large-scale research synthesis is achievable without proprietary database subscriptions. The complete methodology---from data collection through analysis---is publicly available for reproduction and longitudinal updating.

Based on these findings, we offer five practical recommendations. Simulation educators should prioritise LLM integration in Communication and Decision-making training, where the evidence base is most mature, while maintaining human-led facilitation for CRM and team-based competencies. Researchers should direct attention toward the identified gaps: CRM training, open-source model evaluation, mannequin-based simulation augmentation, and randomised controlled trials of educational outcomes. Funding bodies should support comparative studies of open-source versus proprietary models in healthcare simulation contexts. Institutions adopting LLMs for education should develop governance frameworks that account for model versioning, data privacy, and the risks of commercial platform dependency. Finally, the bibliometric community should embrace open-access data sources and replicable pipelines as standard practice, particularly in fields where the intended beneficiaries of research synthesis may lack institutional access to proprietary tools.

The integration of large language models into healthcare simulation holds genuine promise for expanding access to high-quality training, personalising educational experiences, and addressing workforce development challenges across clinical disciplines. Realising this promise, however, requires the field to move beyond its current concentration on a narrow band of NTS domains, a single family of proprietary models, and descriptive study designs. The evidence map presented here provides a foundation for that transition.


---

## Data Availability Statement

The complete data collection pipeline, processing scripts, and analysis code are available at [GitHub URL]. Raw bibliometric data and analysis outputs are available upon reasonable request from the corresponding author.

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
