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
