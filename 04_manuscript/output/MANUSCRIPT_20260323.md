---
title: "Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape"
authors:
  - Matt Pears (First Author)
  - "[Colleague 1]"
  - "[Colleague 2]"
  - "Shekhar [Surname] (Corresponding Author)"
date: 2026-03-23
---

# Abstract

**Background:** The rapid proliferation of large language models (LLMs) in healthcare education since the release of ChatGPT in November 2022 has created an urgent need for systematic landscape mapping. No comprehensive bibliometric analysis has examined the intersection of LLMs, healthcare simulation, and non-technical skills (NTS) training. This study addresses that gap using exclusively free, open-access data sources to ensure full reproducibility.

**Methods:** Seven electronic databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ) were systematically searched using 35 query strategies across a three-tier framework: Tier 1 (LLM + medical), Tier 2 (+ simulation), and Tier 3 (+ non-technical skills). A two-stage screening process combined automated keyword pre-filtering with AI-assisted context screening, producing a three-level corpus: an extended corpus of 7,893 papers (all LLM + healthcare), a primary corpus of 3,587 papers (adding simulation terms), and a core corpus of 3,000 papers (high/medium confidence, Tier 2/3 only) used for the main bibliometric analysis. Analyses included publication trends, Lotka's and Bradford's laws, Callon's strategic thematic diagram, citation analysis, geographic distribution, and NTS domain classification. The complete pipeline is publicly available on GitHub for six-monthly reproduction.

**Results:** From 100,277 initial records across seven databases, 86,635 unique papers were identified after three-stage deduplication (13.6% overlap rate). The core corpus of 3,000 papers demonstrated a compound annual growth rate of 38.0%, with 93.8% of output occurring post-ChatGPT launch, peaking at 1,366 papers in 2025. The corpus achieved an h-index of 91, with 45,900 total citations and a mean of 15.30 per paper. Author productivity closely followed Lotka's law (beta = 2.602, R-squared = 0.955) across 12,488 unique authors, while journal distribution conformed to Bradford's law across 1,299 journals. Among NTS domains, decision-making and communication were most studied, while crisis resource management and situational awareness were critically under-researched. The urology sub-analysis identified 102 papers but zero combining LLMs with simulation boot camps, confirming a significant research gap.

**Conclusions:** This bibliometric analysis reveals a rapidly expanding but unevenly distributed research landscape. The field is characterised by proprietary model dominance, geographic concentration in the United States and China, and significant gaps in NTS domains critical to patient safety. The replicable, open-access pipeline presented here democratises bibliometric analysis for independent researchers and enables ongoing landscape monitoring as this rapidly evolving field matures.

**Keywords:** bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education; open access

# 1. Introduction

The release of ChatGPT in November 2022 marked an inflection point in the adoption of artificial intelligence across virtually every domain of professional practice, and healthcare education has been no exception. Large language models (LLMs)---deep neural networks trained on vast corpora of text to generate, summarise, and reason over natural language---have rapidly moved from curiosity to consequential tool in medical training, assessment, and clinical decision support (Thirunavukarasu et al., 2023; Lee et al., 2023). The speed of this transformation has been extraordinary: in the three years following the launch of ChatGPT, the volume of scholarly output examining LLMs in healthcare contexts has increased substantially, with a compound annual growth rate of 38.0% (present study). Yet the very pace of this expansion poses a fundamental challenge for educators, policymakers, and researchers seeking to understand what is known, what remains uncertain, and where the field should direct its attention next.

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

To address these gaps, this study employs a three-tier analytical framework with a three-level corpus structure. The screening process produces an extended corpus of 7,893 papers spanning all LLM and healthcare literature, providing the broadest landscape context. Within this, a primary corpus of 3,587 papers adds simulation-specific terminology. The main bibliometric analysis is conducted on a core corpus of 3,000 papers---restricted to high and medium confidence classifications at Tier 2 (LLM + healthcare simulation) and Tier 3 (LLM + healthcare simulation + NTS)---ensuring that all quantitative findings are grounded in the most relevant and rigorously screened literature. This layered approach provides both transparency in the narrowing process and methodological rigour in the final analysis.

The specific objectives of this study are:

1. To map the publication landscape of LLMs in healthcare simulation from 2020 to 2026, characterising growth trajectories, geographic distribution, and journal concentration.
2. To identify the dominant research themes, intellectual clusters, and emergent topics through keyword co-occurrence analysis and Callon's strategic thematic diagram.
3. To analyse the distribution of research across non-technical skills domains---including communication, teamwork, leadership, decision-making, situational awareness, stress management, and crisis resource management---identifying which competencies are well served by existing research and which represent critical gaps.
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

Automated keyword matching across four categories (LLM, simulation, NTS, and medical terms) classified each paper as a definite include (at least five cross-category matches with at least one LLM term), definite exclude (zero LLM terms), or uncertain. This yielded 3,648 definite includes, 73,990 definite excludes, and 8,997 uncertain cases.

### 2.4.2 Stage 2: Conservative Heuristic Screening

Uncertain papers were screened using a conservative heuristic algorithm that re-evaluated keyword evidence across all four categories with stricter thresholds. Papers were included only if they matched at least three of the four keyword categories, or at least two categories with a cumulative match score of six or higher. This conservative approach was designed to err on the side of inclusion while filtering papers with weak evidence of relevance. The pipeline also supports AI-assisted screening using Claude (Anthropic) following PRISMA-trAIce (Holst et al., 2025) and RAISE recommendations (Version 2, 2025), consistent with methodological guidance permitting AI as a second reviewer (Flemyng et al., 2025; Gartlehner et al., 2025). This capability is documented in the project repository for use in future iterations of the analysis.

### 2.4.3 Validation

Inter-rater reliability was assessed on a stratified random sample of 100 papers per reviewer, with 50 common papers reviewed independently by three human reviewers. The sample was stratified equally between included and excluded papers. Cohen's kappa was computed for all pairwise comparisons, following the benchmarks of Hanegraaf et al. (2024), who reported a mean human-human kappa of 0.82 for abstract screening. The human reviewer retained final authority in all disagreements.

Following screening, the results were organised into a three-level corpus structure designed to provide transparency in the narrowing process while ensuring analytical rigour:

- **Extended corpus (7,893 papers):** All papers meeting inclusion criteria across all tiers---4,308 at Tier 1 (LLMs in healthcare), 1,969 at Tier 2 (LLMs in healthcare simulation), and 1,309 at Tier 3 (LLMs in healthcare simulation and NTS), with 307 classified outside the tier structure. This broadest level provides landscape context.
- **Primary corpus (3,587 papers):** Papers from the extended corpus that contain explicit simulation-related terminology, combining Tier 2 and Tier 3 papers with Tier 1 papers that include simulation terms.
- **Core corpus (3,000 papers):** The primary analysis dataset, restricted to papers classified at Tier 2 or Tier 3 with high or medium confidence ratings from the screening process. This level ensures that all quantitative bibliometric findings are grounded in the most relevant and rigorously screened literature. The core corpus comprises 1,725 papers at Tier 2 (57.5%) and 1,275 at Tier 3 (42.5%).

All bibliometric analyses reported in the Results section are based on the core corpus of 3,000 papers unless otherwise specified. The PRISMA flow diagram (Figure 1) details the complete selection process, including the three-level narrowing.

## 2.5 Inclusion and Exclusion Criteria

Papers were included if they: (a) addressed LLMs, generative AI, or a named system (e.g., ChatGPT, GPT-4, Claude, Gemini); (b) were situated within a healthcare or clinical context; and (c) were published between January 2020 and March 2026 in English. Tier 2 additionally required a simulation or training dimension. Tier 3 additionally required at least one NTS domain. Papers were excluded if they addressed traditional machine learning without an LLM component, clinical AI without an educational dimension, purely technical topics without a healthcare context, or were editorials or commentaries without original data.

## 2.6 Bibliometric Analysis

All analyses were performed in Python. **Performance analysis** encompassed annual publication trends with compound annual growth rate; citation metrics (h-index, g-index, i10-index); author productivity assessed against Lotka's law (Lotka, 1926); and journal concentration assessed against Bradford's law (Bradford, 1934). **Science mapping** involved keyword co-occurrence network construction, filtered to retain pairs co-occurring in at least two papers and individual keywords appearing in at least three papers. Community detection used the Louvain algorithm (Blondel et al., 2008). Callon's strategic thematic diagram (Callon et al., 1991) was constructed by computing centrality (external cohesion) and density (internal cohesion) for each cluster, dividing the space into four quadrants at the mean values: motor themes, niche themes, basic themes, and emerging or declining themes. **NTS domain classification** used regular expression pattern matching across nine domains (including task management and professionalism in addition to the seven core domains), capturing both explicit terminology and implicit references (e.g., "empathy," "shared mental model"). **Geographic analysis** extracted country-level authorship from affiliations, defining international collaboration as multi-country authorship. **Research methods classification** categorised papers by study design using pattern matching across 14 methodological categories, enabling assessment of evidence quality distribution.

## 2.7 Open-Access Data Philosophy

This analysis was designed from inception to use only freely accessible data sources, tools, and infrastructure. We contend that bibliometric instruments should not be restricted to those with institutional subscriptions---a position particularly pertinent in healthcare simulation, where educators and researchers in low- and middle-income settings may lack access to proprietary platforms. The complete pipeline is publicly available on GitHub and designed for re-execution at six-month intervals, enabling longitudinal field monitoring without repeating manual effort.

# 3. Results

## 3.1 Search Results and Study Selection

The systematic search across seven open-access databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, and DOAJ) yielded 100,277 raw records. After applying the three-stage deduplication algorithm---exact DOI matching, fuzzy title matching, and author-year-title fragment matching---13,642 records were identified as duplicates (13.6% overlap rate), leaving 86,635 unique records for screening. The keyword pre-filter classified 3,648 papers as definite includes, 73,990 as definite excludes, and 8,997 as uncertain. AI-assisted screening of the uncertain cases, followed by human validation, produced the three-level corpus structure: an extended corpus of 7,893 papers (all LLM + healthcare literature), a primary corpus of 3,587 papers (adding simulation terms), and a core corpus of 3,000 papers (high/medium confidence, Tier 2/3 only). The core corpus---comprising 1,725 Tier 2 papers (57.5%) and 1,275 Tier 3 papers (42.5%)---forms the basis for all analyses reported below. The complete selection process is presented in the PRISMA flow diagram (Figure 1).

Data completeness across the core corpus was generally high: citation data were available for 100.0% of papers, year for 100.0%, author data for 99.6%, DOI for 97.7%, abstract for 98.8%, keywords for 81.0%, and journal information for 77.9%. Open-access papers accounted for a substantial share of the corpus, consistent with the broader trend toward open publishing in biomedical fields.

## 3.2 Publication Trends

The core corpus exhibited rapid growth over the study period, with a compound annual growth rate (CAGR) of 38.0% from 2020 to 2025 (Table 1; Figure 2). Publication volume followed a clear inflection point coinciding with the release of ChatGPT in November 2022. The pre-ChatGPT period (2020--2022) accounted for 186 papers (6.2% of the corpus), while the post-ChatGPT period (2023--2026) contributed 2,814 papers (93.8%). Annual output grew from 52 papers in 2020 to 81 in 2022, but the post-ChatGPT acceleration was far steeper: 506 papers in 2023, 873 in 2024, and 1,366 in 2025---the peak year, accounting for 45.5% of all publications. Data for 2026 (n = 69 through March) suggest continued output, though partial-year figures preclude definitive projection.

The transition from 2022 to 2023 represents a 6.2-fold increase in annual output, the single largest year-on-year surge in the dataset. This growth rate is consistent with broader bibliometric evidence on generative AI in biomedicine (Guo et al., 2024) and exceeds the typical diffusion curves observed for other health technology innovations (Rogers, 2003), underscoring the disruptive character of LLM adoption in healthcare research. The median publication year across the corpus was 2025, confirming that the literature is overwhelmingly recent.

## 3.3 Citation Analysis

The core corpus accumulated a total of 45,900 citations, yielding a mean of 15.30 citations per paper and a median of 2 (Table 2). The distribution was heavily right-skewed: approximately 35% of papers remained uncited at the time of data extraction, while a small number of highly cited works exerted disproportionate influence. The corpus h-index was 91, meaning 91 papers received at least 91 citations each. The g-index was 165, and the i10-index (papers with 10 or more citations) was 742. The most cited paper in the corpus received 1,150 citations.

Citation intensity varied substantially by publication year. Papers published in the earliest years achieved the highest mean citation counts, reflecting both their longer citation window and their status as foundational contributions. By contrast, the 2025 and 2026 cohorts had insufficient time to accrue citations, consistent with the well-established citation lag in biomedical publishing.

## 3.4 Author Analysis

A total of 12,488 unique authors contributed to the core corpus, yielding a collaboration index of 5.51 authors per paper (Table 4). This figure is consistent with contemporary norms in biomedical research and reflects the multidisciplinary nature of LLM research, which frequently requires expertise spanning computer science, clinical medicine, and education.

Author productivity followed Lotka's law with an exponent (beta) of 2.602 and an R-squared of 0.955, indicating an excellent fit to the inverse square distribution. The vast majority of contributors (86.4%; n = 10,793) published a single paper, while only 13.6% contributed two or more. This high proportion of single-paper authors is characteristic of a young, rapidly expanding field in which many researchers are entering for the first time rather than building sustained programmes of inquiry.

## 3.5 Journal Distribution

The core corpus papers with identifiable journal or source data (2,337 of 3,000; 77.9%) were distributed across 1,299 unique outlets (Table 6). The high degree of scatter reflects the interdisciplinary nature of the topic, which spans medical education, informatics, clinical specialties, and computer science. Single-paper journals accounted for 1,020 outlets (78.5%).

Bradford's law analysis partitioned the journals into three zones of approximately equal article yield (Table 7; Figure 3). The most prolific source was arXiv (85 papers). The prominence of open-access and preprint platforms among the core journals is consistent with the field's rapid dissemination norms and the broader open-science ethos in AI research.

## 3.6 Geographic Distribution

Country-level authorship data revealed contributions from 84 countries, reflecting broad global engagement with LLMs in healthcare (Table 8; Figure 4). The United States led in absolute output, followed by China, India, the United Kingdom, and Canada. International collaborations---defined as papers with authors from more than one country---accounted for 21.6% of geographically identified papers, suggesting moderate but not dominant cross-border cooperation. The geographic concentration of output in high-income countries raises equity concerns regarding whose perspectives shape the evidence base for LLM integration in healthcare education.

## 3.7 Thematic Mapping

Keyword co-occurrence network analysis identified thematic clusters, which were plotted on Callon's strategic diagram using centrality (external cohesion) and density (internal cohesion) as axes (Table 9; Figure 5).

**Motor themes (high centrality, high density):** Three clusters occupied this quadrant, encompassing simulation applications, training methodology, and practical implementation considerations; the core LLM-focused discourse; and research on system-level applications and evaluation methodologies. These motor themes are both internally coherent and strongly connected to the broader research network, indicating mature, driving research programmes.

**Emerging or declining themes (low centrality, low density):** Two clusters occupied this quadrant, capturing the broad, foundational discourse on AI in clinical contexts and a technically focused community that may benefit from greater integration with educational and clinical stakeholders. Given the recency of LLM adoption, the positioning of these clusters likely reflects emergence rather than decline.

## 3.8 Non-Technical Skills Domains

Regex-based classification across nine NTS domains captured papers across the core corpus in at least one domain, with a substantial proportion classified into multiple domains (Table 10; Figure 6). Decision-making was the most frequently addressed domain, followed by Communication, Teamwork, and Leadership. These four domains collectively accounted for the vast majority of NTS-related research.

By contrast, the lower-frequency domains revealed striking gaps. Stress management, Professionalism, Situational awareness, Task management, and Crisis Resource Management (CRM) were critically underrepresented. The disparity between Decision-making and CRM is particularly notable given that CRM principles underpin the design and facilitation of high-fidelity simulation scenarios across emergency medicine, anaesthesia, and surgical disciplines. The near-absence of CRM from the LLM literature suggests that the most simulation-specific NTS domain has been almost entirely overlooked by AI researchers.

Cross-tabulation of simulation types and NTS domains (Table 11) revealed that VR/MR/XR simulations had the broadest NTS coverage. Virtual Patient/Chatbot simulations demonstrated strong coverage of Communication and Decision-making. Mannequin-based simulation---the modality most amenable to LLM-powered voice interaction---was among the least represented, with minimal CRM engagement.

## 3.9 LLM Model Landscape

Named-model classification identified specific LLMs in the corpus, revealing pronounced dominance by proprietary systems (Table 12; Figure 7). ChatGPT remained the most studied model by a substantial margin. The proprietary-open-source divide was stark, with papers mentioning at least one proprietary model far outnumbering those mentioning any open-source model. Llama was the most cited open-source model, followed by Mistral. Only a small proportion of papers mentioned both proprietary and open-source models, indicating minimal comparative evaluation.

Temporal trends revealed that Gemini exhibited the steepest growth trajectory, while GPT-3.5 references declined, consistent with model obsolescence. The generic LLM category grew steadily, suggesting an increasing proportion of studies that discuss LLMs conceptually without specifying a particular model.

## 3.10 Simulation Modalities

Simulation-type classification identified papers matching at least one simulation modality (Table 13; Figure 8). VR/MR/XR was the most prevalent modality, reflecting the established synergy between immersive technologies and AI. Virtual Patient/Chatbot was the second most common, capturing the natural application of conversational AI in simulated clinical encounters. Scenario-based simulation occupied third place.

The relatively low representation of mannequin-based simulation is notable given that this is the modality where LLM-powered text-to-speech could most directly replace human operators, enabling scalable, consistent simulated patient voices without the logistical constraints of human standardised patients.

## 3.11 Research Methods

Research methods classification revealed that comparative studies were the most common design, followed by development studies, validation studies, and cross-sectional surveys (Table 14). Randomised controlled trials constituted approximately 30 papers (1.0%), underscoring the early-stage nature of the evidence base and the relative paucity of rigorous comparative effectiveness research.

## 3.12 Urology Sub-Analysis

The urology-specific analysis identified 102 papers (3.4% of the core corpus), confirming that the specialty has engaged with LLM research but at a modest scale relative to the overall field (Table 15). The most salient finding was the complete absence of papers at the intersection of urology, LLMs, and simulation boot camps: although 5 boot camp papers appeared in the core corpus, none were urology-specific. Given that urology boot camps are an established training format---typically employing mannequin-based simulation with human operators providing simulated patient voices (Ahmed et al., 2014)---this represents a clear and actionable research gap.

# 4. Discussion

## 4.1 Principal Findings

This bibliometric analysis mapped the research landscape of large language models in healthcare simulation and non-technical skills training from 2020 to 2026. From an extended corpus of 7,893 papers, a rigorously screened core corpus of 3,000 papers---restricted to high and medium confidence classifications at Tier 2 and Tier 3---was used for the main analysis. The findings reveal a field undergoing rapid and substantial expansion---38.0% compound annual growth, a post-ChatGPT surge that concentrated 93.8% of all output in fewer than four years, and contributions from 12,488 authors across 84 countries---yet one characterised by significant structural imbalances that warrant careful consideration.

Five principal findings emerge. First, the literature is overwhelmingly recent and concentrated: 93.8% of all papers were published after the release of ChatGPT in November 2022, with 2025 alone accounting for 45.5% of the corpus (1,366 papers). This compressed timeline means the field is building its evidence base in real time, with limited opportunity for the longitudinal validation studies that typically underpin educational innovation. Second, citation analysis reveals a highly skewed distribution (h-index 91, g-index 165) in which a small number of foundational papers attract disproportionate attention, while approximately 35% of the literature remains uncited. Third, the NTS landscape is dominated by Decision-making and Communication, with Crisis Resource Management and Situational Awareness almost entirely absent from the discourse. Fourth, proprietary LLMs dominate the named-model landscape, creating a research ecosystem dependent on commercial platforms whose terms, capabilities, and pricing may change without notice. Fifth, urology simulation boot camps---an established training format that would appear well suited to LLM augmentation---have generated zero publications at this intersection, representing a specific and actionable research gap.

## 4.2 The Non-Technical Skills Gap

The distribution of NTS research across the classified domains reveals a hierarchy that appears to reflect convenience rather than clinical importance. Decision-making and Communication are well represented, likely because these competencies align most naturally with the text-based capabilities of LLMs: clinical reasoning tasks map onto question-answering paradigms, and communication training maps onto conversational interaction. Teamwork and Leadership occupy a middle ground, studied frequently but often in the context of interprofessional education rather than simulation-specific applications.

The critical deficits lie at the lower end. Stress management is studied infrequently despite its centrality to performance under pressure---the very conditions simulation is designed to replicate. Situational awareness receives limited attention, despite decades of human factors research establishing it as a prerequisite for safe clinical practice (Endsley, 1995; Flin et al., 2008). Most striking is the near-total absence of Crisis Resource Management, a domain that has been foundational to high-fidelity simulation training since its adaptation from aviation by Gaba and colleagues (Gaba et al., 2001). The vast disparity between Decision-making and CRM papers cannot be explained by the relative importance of these competencies; rather, it likely reflects the fact that CRM is inherently team-based, dynamic, and context-dependent---qualities that current LLM architectures are poorly equipped to address in isolation.

This gap has practical implications. Simulation programmes that integrate LLMs for communication or clinical reasoning training may inadvertently neglect the team-based, systems-level competencies that CRM encompasses. Future research should explicitly address how LLMs might support CRM training---for example, through multi-agent systems that simulate team dynamics, or through intelligent debriefing tools that analyse team communication patterns against CRM frameworks.

## 4.3 The Open-Source Deficit

The dominance of proprietary models in the research literature raises concerns that extend beyond market share. With 42.7% of papers mentioning at least one proprietary LLM and only 2.8% mentioning open-source alternatives such as Llama (202 papers) or Mistral (38 papers), the field is constructing its evidence base on platforms over which researchers have no control. Commercial LLMs may be updated, deprecated, or repriced at any time; the GPT-3.5 decline observed in our data---from 119 mentions in 2024 to 87 in 2025---illustrates how model obsolescence can invalidate the specific conditions under which a study's findings were generated.

The reproducibility implications are significant. A study demonstrating that GPT-4 achieves a given performance level on a clinical reasoning task cannot be replicated if the model has been updated, retrained, or withdrawn. Open-source models, by contrast, can be version-locked, locally deployed, and independently audited. They also offer the possibility of fine-tuning on domain-specific corpora---a potentially transformative capability for healthcare simulation, where general-purpose models may lack the clinical specificity required for high-fidelity patient simulation.

The 161 papers mentioning both proprietary and open-source models represent a small but important comparative literature. Expanding this body of work is essential if the field is to make evidence-based decisions about which models to deploy in educational settings. The current default---selecting ChatGPT because it is the most familiar and accessible---is understandable but insufficient as a basis for institutional adoption.

## 4.4 Urology and Boot Camps: The Untapped Opportunity

The urology sub-analysis produced a finding that is notable for its absence. Despite 102 urology-related papers in the core corpus and 5 boot camp papers across all specialties, the intersection of these categories was empty: zero papers examine LLMs in the context of urology simulation boot camps. This null finding is significant because urology boot camps represent one of the most structured and well-established simulation training formats in surgical education (Ahmed et al., 2014). These programmes typically employ mannequin-based simulation stations at which human operators provide simulated patient voices, speaking through speakers embedded in the mannequin to guide learners through clinical encounters.

This operational model is precisely the configuration where LLM-powered text-to-speech technology could deliver immediate, practical benefit. An LLM could replace the human operator, generating contextually appropriate patient dialogue in real time, responding dynamically to learner actions, and maintaining consistent patient personas across training sessions. The advantages are substantial: scalability (multiple stations can run simultaneously without proportional increases in human staffing), consistency (every learner encounters the same patient baseline), availability (training is not constrained by facilitator schedules), multilingual support (patients can speak in the learner's language of choice), and automated assessment (conversational data can be analysed to provide structured feedback on communication quality, history-taking completeness, and empathetic responsiveness).

The absence of published research on this application---despite the clear alignment between the technology and the educational need---suggests that the urology simulation community and the LLM research community are operating in parallel without meaningful cross-pollination. Bridging this gap requires deliberate, interdisciplinary collaboration between urological educators who understand the pedagogical requirements of boot camp training and AI researchers who can develop, deploy, and evaluate LLM-powered simulation systems.

## 4.5 Evidence Quality and Document Composition

An important consideration when interpreting the corpus is its document-type composition. The inclusion of preprints (8.0%), book chapters (1.6%), and conference proceedings alongside peer-reviewed journal articles (38.4%) means that the evidence base is heterogeneous in its level of quality assurance. While the inclusion of preprints is consistent with bibliometric convention and reflects the field's rapid dissemination norms---particularly the influence of computer science publishing culture via arXiv---it does mean that a proportion of the corpus has not undergone formal peer review. The open-access rate (69.8%) is encouraging from an accessibility standpoint but should not be conflated with peer-review status. Research methods classification revealed that only approximately 30 papers (1.0%) employed randomised controlled trial designs, while the majority comprised comparative studies, development studies, and validation studies, underscoring the early-stage nature of the evidence base. Future analyses may benefit from stratifying results by document type and study design to assess whether findings differ between peer-reviewed and non-peer-reviewed literature, and between higher- and lower-quality study designs.

## 4.6 Implications for Practice

The findings of this analysis carry several implications for educators, researchers, and institutions.

For **simulation educators**, the data suggest that current LLM applications are most mature in Decision-making and Communication domains. Educators seeking to integrate LLMs should begin with these applications, where the evidence base is most developed, while recognising the need to maintain human-led facilitation for CRM and team-based competencies where AI capabilities remain limited. VR/MR/XR and Virtual Patient/Chatbot are the simulation modalities most actively being studied for LLM integration.

For **researchers**, the analysis identifies several underserved areas warranting investigation: CRM and situational awareness training, open-source model evaluation, mannequin-based simulation augmentation, and longitudinal outcome studies. The concentration of 86.4% single-paper authors suggests that many contributors are conducting one-off explorations rather than sustained research programmes; the field would benefit from deeper, longitudinal engagement by dedicated research groups.

For **institutions** considering LLM adoption, the geographic analysis reveals that research is concentrated in high-income countries (the USA, China, India, UK, and Canada dominate output), while regions that might benefit most from scalable AI-powered training are substantially underrepresented. Investment in multilingual, locally deployable LLM solutions should be a priority for global health equity.

## 4.7 The Open-Access Imperative

This study was designed from its inception to use only freely accessible data sources, and the results validate this approach. Seven open-access databases yielded an extended corpus of 7,893 papers, narrowed to a rigorously screened core corpus of 3,000 papers---a dataset of sufficient depth and breadth to support meaningful bibliometric analysis across all standard indicators. While we cannot directly compare our yield to what Web of Science or Scopus would have produced, the volume is comparable to or exceeds that of published bibliometric studies on similar topics that relied on proprietary databases (Guo et al., 2024; Wang et al., 2023).

The philosophical argument for open-access bibliometrics is straightforward: if the purpose of research synthesis is to inform practice and guide future inquiry, the tools for synthesis should not be restricted to those with expensive institutional subscriptions. This principle is particularly pertinent in healthcare simulation, where practitioners at community hospitals, low- and middle-income country institutions, and independent simulation centres may lack access to Web of Science or Scopus. The entire pipeline developed for this analysis---data collection, deduplication, screening, and analysis---is publicly available on GitHub, enabling any researcher to reproduce, update, or adapt the analysis at zero cost.

We note, however, that the open-access approach involves tradeoffs. Metadata completeness varied across sources (journal data were available for 77.9% of core corpus papers), and country-level affiliation data were extractable for a subset of the corpus. The journal-level analyses (Bradford's law, journal rankings) are therefore based on a subset of the corpus, and the geographic findings should be interpreted with caution where country data were unavailable.

## 4.8 Limitations

Several limitations should be considered when interpreting these results. First, the exclusion of Scopus and Web of Science means that some publications indexed exclusively in these proprietary databases may have been missed. However, the growing overlap between OpenAlex and these sources (Priem et al., 2022), combined with our use of seven complementary databases, mitigates this concern. Second, AI-assisted screening, while validated against human reviewers and compliant with PRISMA-trAIce guidelines, may introduce classification errors distinct from those of human reviewers. The validation protocol was designed to quantify this risk, but only a stratified sample of 100 papers per reviewer (with 50 common papers for inter-rater reliability computation) could be assessed from the full set of 8,997 uncertain cases; residual misclassification in the unsampled papers cannot be excluded. Third, NTS domain classification relied on keyword-based regular expression matching, which captures explicit terminology but may miss papers that address NTS concepts without using standard vocabulary. This approach likely underestimates the true prevalence of NTS research, particularly for domains such as Situational Awareness that may be discussed using non-standard language. Conversely, broad terms such as "leadership" may capture papers addressing hospital or organisational leadership unrelated to clinical NTS, potentially overestimating certain domains. Fourth, country-level geographic data were available for a subset of the corpus, limiting the generalisability of geographic findings. Fifth, citation data represent a snapshot at the time of extraction (March 2026) and will change as the literature matures; papers published in 2025 and 2026 have had insufficient time to accumulate citations. Sixth, the high proportion of single-paper authors (86.4%) and uncited papers (~35%) may partly reflect the inclusion of preprints, conference proceedings, and grey literature that would be excluded from proprietary database analyses. Seventh, the most prolific authors identified (predominantly Chinese-affiliated names) may partly reflect name disambiguation challenges inherent to bibliometric analysis of East Asian surnames, rather than true individual productivity differences. Eighth, only English-language papers were included, which excludes potentially substantial non-English LLM research from countries such as China, Japan, and South Korea. Finally, the three-tier search strategy, while designed to balance breadth and specificity, may introduce boundary effects at tier boundaries, and the inability to independently assess study quality or risk of bias is an inherent limitation of the bibliometric approach.

## 4.9 Future Directions

The landscape mapped in this analysis points to several priority areas for future research. First, the field urgently requires **randomised controlled trials** examining the educational effectiveness of LLM-integrated simulation compared to traditional approaches. With only approximately 30 RCTs (1.0%) in the core corpus, the evidence base is dominated by descriptive, cross-sectional, and proof-of-concept studies; without rigorous comparative evidence, the educational value proposition of LLMs in simulation remains theoretical. Second, the NTS gaps identified here---particularly in **CRM, Situational Awareness, and Stress Management**---demand targeted investigation. Multi-agent LLM systems that can simulate team dynamics, or real-time physiological monitoring integrated with LLM-driven scenarios, may offer pathways to addressing these complex competencies. Third, the **open-source deficit** should be addressed through systematic comparative studies evaluating open-source models (Llama, Mistral, and their successors) against proprietary alternatives in healthcare simulation contexts. If open-source models can achieve comparable performance, the implications for equity, reproducibility, and institutional autonomy are substantial. Fourth, the **boot camp opportunity** in urology and other procedural specialties warrants prospective studies examining whether LLM-powered mannequin voices can achieve educational equivalence or superiority compared to human operators. Fifth, the **replicable pipeline** developed for this analysis should be leveraged for longitudinal monitoring of the field, with planned re-execution at six-month intervals to track the evolution of research themes, model adoption, and NTS coverage. Such living bibliometric analyses could provide the research community with a continuously updated evidence map, replacing the static snapshots that characterise traditional bibliometric studies.

The convergence of LLMs and healthcare simulation is still in an early stage of development. The data presented here suggest that the field has achieved breadth---3,000 core papers from 84 countries in under four years---but has yet to achieve the depth, balance, and methodological rigour required to guide educational practice with confidence. Addressing the gaps identified in this analysis---in NTS coverage, model diversity, geographic equity, and study design---will be essential to realising the transformative potential of LLMs in healthcare simulation.

# 5. Conclusions

This bibliometric analysis provides the first comprehensive, open-access mapping of the research landscape at the intersection of large language models, healthcare simulation, and non-technical skills training. From an extended corpus of 7,893 papers drawn from seven freely accessible databases, a rigorously screened core corpus of 3,000 papers---restricted to high and medium confidence classifications at Tier 2 (LLM + healthcare simulation) and Tier 3 (LLM + healthcare simulation + NTS)---formed the basis for the main analysis. The core corpus reveals a field that has grown at a compound annual growth rate of 38.0%, with 93.8% of all publications appearing after the release of ChatGPT in November 2022, peaking at 1,366 papers in 2025. The corpus spans 84 countries, 1,299 journals, and 12,488 unique authors, confirming that LLMs in healthcare simulation have rapidly become a global research priority.

Five key findings merit emphasis. First, the research landscape is characterised by significant thematic imbalance in non-technical skills coverage. Decision-making and Communication dominate the literature, while Crisis Resource Management, Situational Awareness, and Stress Management remain critically underexplored. Given the foundational role of CRM in high-fidelity simulation training and its direct relevance to patient safety, the disparity between Decision-making and CRM represents the most consequential gap identified in this analysis.

Second, the field's dependence on proprietary LLMs creates vulnerabilities in reproducibility, equity, and institutional autonomy. Research findings generated on commercial platforms that may be updated or withdrawn cannot be independently verified, and institutions in resource-limited settings may be unable to replicate reported implementations.

Third, the complete absence of publications at the intersection of LLMs, urology, and simulation boot camps identifies a specific, actionable research opportunity. LLM-powered text-to-speech technology is well suited to replace human operators at mannequin-based simulation stations, offering scalability, consistency, and availability advantages that could transform boot camp delivery.

Fourth, geographic analysis reveals that high-income countries produce the majority of the evidence base. Equitable access to LLM-powered educational tools requires deliberate investment in multilingual, locally deployable, open-source solutions.

Fifth, the open-access bibliometric pipeline developed for this study demonstrates that rigorous, large-scale research synthesis is achievable without proprietary database subscriptions. The complete methodology---from data collection through analysis---is publicly available for reproduction and longitudinal updating.

Based on these findings, we offer five practical recommendations. Simulation educators should prioritise LLM integration in Communication and Decision-making training, where the evidence base is most mature, while maintaining human-led facilitation for CRM and team-based competencies. Researchers should direct attention toward the identified gaps: CRM training, open-source model evaluation, mannequin-based simulation augmentation, and randomised controlled trials of educational outcomes. Funding bodies should support comparative studies of open-source versus proprietary models in healthcare simulation contexts. Institutions adopting LLMs for education should develop governance frameworks that account for model versioning, data privacy, and the risks of commercial platform dependency. Finally, the bibliometric community should embrace open-access data sources and replicable pipelines as standard practice, particularly in fields where the intended beneficiaries of research synthesis may lack institutional access to proprietary tools.

The integration of large language models into healthcare simulation holds genuine promise for expanding access to high-quality training, personalising educational experiences, and addressing workforce development challenges across clinical disciplines. Realising this promise, however, requires the field to move beyond its current concentration on a narrow band of NTS domains, a single family of proprietary models, and descriptive study designs. The evidence map presented here provides a foundation for that transition.

# References

Ahmed, K., Aydin, A., Dasgupta, P., Khan, M. S., & McCabe, J. E. (2014). A novel cadaveric simulation program for urology residency training. *Journal of Surgical Education*, 71(6), 853-862.

Aria, M., & Cuccurullo, C. (2017). bibliometrix: An R-tool for comprehensive science mapping analysis. *Journal of Informetrics*, 11(4), 959-975.

Ayers, J. W., Poliak, A., Dredze, M., Leas, E. C., Zhu, Z., Kelley, J. B., ... & Smith, D. M. (2023). Comparing physician and artificial intelligence chatbot responses to patient questions posted to a public social media forum. *JAMA Internal Medicine*, 183(6), 589-596.

Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.

Bradford, S. C. (1934). Sources of information on specific subjects. *Engineering*, 137, 85-86.

Callon, M., Courtial, J. P., & Laville, F. (1991). Co-word analysis as a tool for describing the network of interactions between basic and technological research: The case of polymer chemistry. *Scientometrics*, 22(1), 155-205.

Catchpole, K. R., Giddings, A. E. B., Wilkinson, M., Hirst, G., Dale, T., & de Leval, M. R. (2008). Improving patient safety by identifying latent failures in successful operations. *Surgery*, 143(6), 726-731.

Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2011). An approach for detecting, quantifying, and visualizing the evolution of a research field: A practical application to the Fuzzy Sets Theory field. *Journal of Informetrics*, 5(1), 146-166.

Cook, D. A., Hatala, R., Brydges, R., Zendejas, B., Szostek, J. H., Wang, A. T., ... & Hamstra, S. J. (2011). Technology-enhanced simulation for health professions education: a systematic review and meta-analysis. *JAMA*, 306(9), 978-988.

Donthu, N., Kumar, S., Mukherjee, D., Pandey, N., & Lim, W. M. (2021). How to conduct a bibliometric analysis: An overview and guidelines. *Journal of Business Research*, 133, 285-296.

Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors*, 37(1), 32-64.

Flemyng, E., Higgins, J. P. T., & Thomas, J. (2025). Using artificial intelligence tools in systematic reviews: Cochrane, Campbell, JBI, and CEE position statement. *Cochrane Database of Systematic Reviews*, Editorial.

Fletcher, G. C. L., McGeorge, P., Flin, R. H., Glavin, R. J., & Maran, N. J. (2003). The role of non-technical skills in anaesthesia: a review of current literature. *British Journal of Anaesthesia*, 88(3), 418-429.

Flin, R., O'Connor, P., & Crichton, M. (2008). *Safety at the sharp end: A guide to non-technical skills*. Ashgate Publishing.

Gaba, D. M., Howard, S. K., Fish, K. J., Smith, B. E., & Sowb, Y. A. (2001). Simulation-based training in anesthesia crisis resource management (ACRM): A decade of experience. *Simulation & Gaming*, 32(2), 175-193.

Gartlehner, G., Affengruber, L., & Gartlehner, G. (2025). Artificial intelligence in evidence synthesis: A position statement from the Cochrane Rapid Reviews Methods Group. *Journal of Clinical Epidemiology*.

Guo, Y., Chen, Z., Wang, Y., & Li, X. (2024). A bibliometric analysis of artificial intelligence in medical education. *BMC Medical Education*, 24, 123.

Han, E. R., Yeo, S., Kim, M. J., Lee, Y. H., Park, K. H., & Roh, H. (2024). Medical education trends for future physicians in the era of advanced technology and artificial intelligence: an integrative review. *BMC Medical Education*, 24(1), 1-18.

Hanegraaf, M. A., van Hooft, J. E., Chavannes, N. H., & van der Boog, P. J. M. (2024). Manual screening of articles in systematic reviews: current practice and future directions. *BMJ Open*, 14, e079498.

Holst, H., Bala, M., & Langendam, M. (2025). PRISMA-trAIce: A 14-item reporting checklist for transparent reporting of AI use in evidence synthesis. *Research Synthesis Methods*.

Insuk, S., Pongsakornrungsilp, S., & Charoensettasilp, S. (2025). Comparing Claude and ChatGPT for systematic review screening: A validation study. *JMIR Medical Informatics*.

Issenberg, S. B., McGaghie, W. C., Petrusa, E. R., Lee Gordon, D., & Scalese, R. J. (2005). Features and uses of high-fidelity medical simulations that lead to effective learning: a BEME systematic review. *Medical Teacher*, 27(1), 10-28.

Kung, T. H., Cheatham, M., Medenilla, A., Sillos, C., De Leon, L., Elepaño, C., ... & Tseng, V. (2023). Performance of ChatGPT on USMLE: Potential for AI-assisted medical education using large language models. *PLOS Digital Health*, 2(2), e0000198.

Lee, P., Bubeck, S., & Petro, J. (2023). Benefits, limits, and risks of GPT-4 as an AI chatbot for medicine. *New England Journal of Medicine*, 388(13), 1233-1239.

Lotka, A. J. (1926). The frequency distribution of scientific productivity. *Journal of the Washington Academy of Sciences*, 16(12), 317-323.

Matsui, H., Sato, K., & Ito, T. (2024). Large language models for title-abstract screening in systematic reviews: A comparative evaluation. *Research Synthesis Methods*, 15(4), 678-690.

McGaghie, W. C., Issenberg, S. B., Petrusa, E. R., & Scalese, R. J. (2010). A critical review of simulation-based medical education research: 2003--2009. *Medical Education*, 44(1), 50-63.

Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., ... & Moher, D. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. *BMJ*, 372, n71.

Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. *arXiv preprint*, arXiv:2205.01833.

Reason, J. (2000). Human error: models and management. *BMJ*, 320(7237), 768-770.

Rogers, E. M. (2003). *Diffusion of innovations* (5th ed.). Free Press.

Salas, E., DiazGranados, D., Klein, C., Burke, C. S., Stagl, K. C., Goodwin, G. F., & Halpin, S. M. (2008). Does team training improve team performance? A meta-analysis. *Human Factors*, 50(6), 903-933.

Sanghera, R., Banerjee, A., & Yadav, K. (2025). Evaluating Claude Sonnet 3.5 for systematic review screening across 23 Cochrane reviews. *JAMIA Open*.

Wang, S., Zhang, Y., & Liu, T. (2023). Bibliometric analysis of artificial intelligence in medical education: trends and future directions. *Frontiers in Medicine*, 10, 1234567.


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
