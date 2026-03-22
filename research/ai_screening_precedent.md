# Literature Precedent Report: AI/LLM-Assisted Screening in Systematic Reviews and Bibliometric Analyses

**Compiled:** 2026-03-22
**Purpose:** Evidence base for justifying and documenting AI-assisted screening in a bibliometric analysis

---

## Table of Contents

1. [Published Papers Using AI/LLM for Screening](#1-published-papers-using-aillm-for-screening)
2. [Methodological Guidelines and Frameworks](#2-methodological-guidelines-and-frameworks)
3. [Inter-Rater Reliability Approaches with AI](#3-inter-rater-reliability-approaches-with-ai)
4. [Criticisms, Limitations, and Failure Modes](#4-criticisms-limitations-and-failure-modes)
5. [Publisher Editorial Policies on AI Use](#5-publisher-editorial-policies-on-ai-use)
6. [Practical Recommendations for Our Methods Section](#6-practical-recommendations-for-our-methods-section)
7. [Summary of Key Findings](#7-summary-of-key-findings)

---

## 1. Published Papers Using AI/LLM for Screening

### 1.1. Matsui et al. (2024) — 3-Layer GPT Strategy for Systematic Reviews

- **Title:** "Human-Comparable Sensitivity of Large Language Models in Identifying Eligible Studies Through Title and Abstract Screening: 3-Layer Strategy Using GPT-3.5 and GPT-4 for Systematic Reviews"
- **Authors:** Kentaro Matsui, Tomohiro Utsumi, Yumi Aoki, Taku Maruki, Masahiro Takeshima, Yoshikazu Takaesu
- **Journal:** Journal of Medical Internet Research (JMIR), 2024
- **DOI:** [10.2196/52758](https://doi.org/10.2196/52758)
- **URL:** https://www.jmir.org/2024/1/e52758
- **Key Findings:**
  - Evaluated on two bipolar disorder systematic reviews (1,381 and 3,146 records)
  - GPT-4 in Study 1: sensitivity 0.806 (adjusted to 0.962), specificity 0.996
  - GPT-4 in Study 2: sensitivity 0.875 (adjusted to 0.943), specificity 0.855
  - GPT-3.5 showed higher sensitivity but much lower specificity
  - Processing speed: ~110 records per minute per screening layer
  - **Relevance:** Demonstrates that a structured, multi-layer prompting approach with GPT-4 can achieve human-comparable sensitivity for title/abstract screening

### 1.2. Oami et al. (2025) — GPT-3.5 Turbo vs GPT-4 Turbo Screening

- **Title:** "GPT-3.5 Turbo and GPT-4 Turbo in Title and Abstract Screening for Systematic Reviews"
- **Authors:** Takehiko Oami, Yohei Okada, Taka-aki Nakada
- **Journal:** JMIR Medical Informatics, 2025
- **DOI:** [10.2196/64682](https://medinform.jmir.org/2025/1/e64682)
- **URL:** https://medinform.jmir.org/2025/1/e64682
- **Key Findings:**
  - GPT-4 Turbo: sensitivity 0.85, specificity 0.98
  - GPT-3.5 Turbo: sensitivity 0.83, specificity 0.51
  - GPT-3.5 was faster (0.9 min vs 1.6 min per 100 studies)
  - **Relevance:** Shows GPT-4 Turbo has both high sensitivity AND high specificity, supporting its use as a reliable screening tool

### 1.3. Khraisha et al. (2024) — GPT-4 Efficacy Across Languages

- **Title:** "Can large language models replace humans in systematic reviews? Evaluating GPT-4's efficacy in screening and extracting data from peer-reviewed and grey literature in multiple languages"
- **Authors:** Qusai Khraisha, Sophie Put, Johanna Kappenberg, Azza Warraitch, Kristin Hadfield
- **Journal:** Research Synthesis Methods, 15(4), 616-626
- **DOI:** [10.1002/jrsm.1715](https://doi.org/10.1002/jrsm.1715)
- **URL:** https://pubmed.ncbi.nlm.nih.gov/38484744/
- **Key Findings:**
  - Pre-registered evaluation of GPT-4 across title/abstract screening, full-text review, and data extraction
  - After adjusting for chance agreement and dataset imbalance, performance dropped across all stages
  - Screening performance ranged from "none" (in balanced datasets) to "moderate"
  - Full-text screening with well-designed prompts achieved "almost perfect" human-like performance
  - **Relevance:** Strikes a cautionary note — "substantial caution should be exercised if LLMs are being used to conduct systematic reviews" — while acknowledging conditional success. Prompt quality is critical.

### 1.4. Landschaft et al. (2024) — GPT-4 as Additional Reviewer (PRISMA-Based)

- **Title:** "Implementation and evaluation of an additional GPT-4-based reviewer in PRISMA-based medical systematic literature reviews"
- **Authors:** Assaf Landschaft, Dario Antweiler, Sina Mackay, Sabine Kugler, Stefan Rüping, Stefan Wrobel, Timm Höres, Hector Allende-Cid
- **Journal:** International Journal of Medical Informatics, 189, 105531
- **DOI:** [10.1016/j.ijmedinf.2024.105531](https://doi.org/10.1016/j.ijmedinf.2024.105531)
- **URL:** https://pubmed.ncbi.nlm.nih.gov/38943806/
- **Key Findings:**
  - **Cohen's kappa > 0.9** between GPT-4 and human reviewers for abstract screening (almost perfect agreement)
  - Lower agreement for full-text parameter extraction
  - Used RAG methodology with LangChain for full-text processing
  - **Relevance:** Directly demonstrates that GPT-4 can function as a reliable "second reviewer" with near-perfect agreement with humans in abstract screening. This is the most relevant precedent for using AI as one rater in an IRR framework.

### 1.5. Rubinstein et al. (2025) — GPT-4 for Policy Literature Screening

- **Title:** "Using GPT-4 for Title and Abstract Screening in a Literature Review of Public Policies: A Feasibility Study"
- **Authors:** Rubinstein et al. (RAND Corporation)
- **Journal:** Cochrane Evidence Synthesis and Methods, 3(3), e70031
- **DOI:** [10.1002/cesm.70031](https://doi.org/10.1002/cesm.70031)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1002/cesm.70031
- **Key Findings:**
  - First known use of LLMs for title/abstract screening in a public policy literature review
  - False exclusion rate of only 0.01 (1%)
  - Published in a Cochrane journal — indicating methodological acceptance
  - Recommends building performance evaluations into the workflow
  - **Relevance:** Published in a Cochrane-affiliated journal, establishing legitimacy for AI screening outside of clinical reviews. Directly applicable to our policy/social science context.

### 1.6. Sanghera et al. (2025) — LLM Ensembles for Abstract Screening

- **Title:** "High-performance automated abstract screening with large language model ensembles"
- **Authors:** Rohan Sanghera, Arun James Thirunavukarasu, Marc El Khoury, Jessica O'Logbon, Yuqing Chen, Archie Watt, Mustafa Mahmood, Hamid Butt, George Nishimura, Andrew A S Soltan
- **Journal:** Journal of the American Medical Informatics Association (JAMIA), 32(5), 893-904
- **DOI:** [10.1093/jamia/ocaf050](https://doi.org/10.1093/jamia/ocaf050)
- **URL:** https://academic.oup.com/jamia/article/32/5/893/8090299
- **Key Findings:**
  - Tested GPT-3.5 Turbo, GPT-4 Turbo, GPT-4o, Llama 3 70B, Gemini 1.5 Pro, and **Claude Sonnet 3.5** across 23 Cochrane reviews
  - Claude Sonnet 3.5: sensitivity 0.819, specificity 0.966, precision 0.925 (development dataset)
  - LLMs exhibited superior sensitivity to human researchers (LLMmax=1.000 vs humanmax=0.775)
  - 66 LLM-human and LLM-LLM ensembles achieved perfect sensitivity
  - Workload reductions: 37.55%-99.13%
  - **Relevance:** Directly tests Claude and demonstrates its strong specificity/precision. Establishes Claude as a validated screening tool in systematic reviews. The ensemble approach (AI + human) is directly analogous to our methodology.

### 1.7. Insuk et al. (2025) — ChatGPT and Claude for Obstetrics Screening

- **Title:** "How Well Do ChatGPT and Claude Perform in Study Selection for Systematic Review in Obstetrics"
- **Authors:** Suppachai Insuk, Kansak Boonpattharatthiti, Chimbun Booncharoen, Panitnan Chaipitak, Muhammed Rashid, Sajesh K Veettil, Nai Ming Lai, Nathorn Chaiyakunapruk, Teerapon Dhippayom
- **Journal:** Journal of Medical Systems, 49(1), 110
- **DOI:** [10.1007/s10916-025-02246-4](https://doi.org/10.1007/s10916-025-02246-4)
- **URL:** https://pubmed.ncbi.nlm.nih.gov/40906005/
- **Key Findings:**
  - Title/abstract screening accuracy: Human 0.9593, Claude 0.9448, ChatGPT 0.9138
  - Both models achieved very high negative predictive value: ChatGPT 0.9959, Claude 0.9961
  - "Generative AI models perform close to human levels in study selection"
  - **Relevance:** Head-to-head comparison of Claude vs ChatGPT in screening, published in 2025. Claude slightly outperformed ChatGPT and was very close to human accuracy.

### 1.8. Kim et al. (2025) — Systematic Review and Meta-Analysis of LLM Screening

- **Title:** "Evaluating large language models for title/abstract screening: a systematic review and meta-analysis & development of new tool"
- **Authors:** Jin Kyu Kim, Mandy Rickard, Pankaj Dangle, Nikhil Batra, Michael E. Chua, Adree Khondker, Korand M. Szymanski, Rosalia Misseri, Armando J. Lorenzo
- **Journal:** Journal of Medical Artificial Intelligence (JMAI), 2025
- **DOI:** [10.21037/jmai-24-408](https://doi.org/10.21037/jmai-24-408)
- **URL:** https://jmai.amegroups.org/article/view/10102/html
- **Key Findings:**
  - Meta-analysis of 14 LLM-based screening models
  - **Pooled sensitivity: 0.812 (95% CI: 0.617-0.920)**
  - **SROC AUC: 0.922** (excellent overall performance)
  - Authors' GPT-4o-mini model: 100% sensitivity, 81% specificity, cost $0.00008/entry
  - **Relevance:** The most comprehensive meta-analytic evidence to date. SROC AUC of 0.922 confirms "excellent" diagnostic performance of LLMs for screening. Establishes the evidence base for the field.

---

## 2. Methodological Guidelines and Frameworks

### 2.1. PRISMA-trAIce Checklist (Holst et al., 2025)

- **Title:** "Transparent Reporting of AI in Systematic Literature Reviews: Development of the PRISMA-trAIce Checklist"
- **Authors:** Dirk Holst, Keno Moenck, Julian Koch, Ole Schmedemann, Thorsten Schüppstuhl
- **Journal:** JMIR AI, 2025
- **DOI:** [10.2196/80247](https://doi.org/10.2196/80247)
- **URL:** https://ai.jmir.org/2025/1/e80247
- **Key Contribution:** 14-item checklist extension to PRISMA 2020 for transparent reporting of AI in systematic reviews

**The 14 Checklist Items:**

| Item | Code | Requirement |
|------|------|-------------|
| Title | P-trAIce T1 | Indicate AI assistance in title when tools played substantial roles |
| Abstract | P-trAIce A1 | Summarize which AI tools were used, at what stages, and their functions |
| Introduction | P-trAIce I1 | Rationale for selecting AI tools for specific tasks |
| Protocol | P-trAIce M1 | Document whether AI methods were pre-specified; disclose deviations |
| Tool ID | P-trAIce M2 | Report tool names, versions, developers, access methods |
| Purpose/Stage | P-trAIce M3 | Specify which review stages used AI and intended tasks |
| Input Data | P-trAIce M4 | Detail data sources, preparation, training/fine-tuning datasets |
| Output Data | P-trAIce M5 | Characterize output formats and post-processing before human review |
| Prompts | P-trAIce M6 | Provide complete prompts, temperature, token limits |
| Operations | P-trAIce M7 | Describe algorithms, settings, configurations |
| Human-AI | P-trAIce M8 | Document validation procedures, verification proportions, discrepancy resolution |
| Performance (Methods) | P-trAIce M9 | Describe evaluation approaches, reference standards, metrics |
| Data Governance | P-trAIce M10 | Address data privacy, security, compliance |
| Study Selection | P-trAIce R1 | Distinguish AI vs human exclusions in flow diagrams |
| Performance (Results) | P-trAIce R2 | Report quantitative performance and agreement measures |
| Limitations | P-trAIce D1 | Discuss AI limitations, biases, technical issues |
| Implications | P-trAIce D2 | Reflect on efficiency gains/challenges and future implications |

- **Relevance:** This is the most detailed reporting framework for documenting AI use in systematic reviews. We should follow items M2, M3, M6, M8, R1, and D1 at minimum.

### 2.2. Cochrane/Campbell/JBI/CEE Position Statement (Flemyng et al., 2025)

- **Title:** "Position Statement on Artificial Intelligence (AI) Use in Evidence Synthesis Across Cochrane, the Campbell Collaboration, JBI, and the Collaboration for Environmental Evidence 2025"
- **Lead Author:** Ella Flemyng (Cochrane, London), with 13 co-authors
- **Journal:** Campbell Systematic Reviews (also published in Cochrane Database of Systematic Reviews and Environmental Evidence)
- **DOI:** [10.1002/cl2.70074](https://doi.org/10.1002/cl2.70074)
- **Published:** November 10, 2025
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12603384/
- **Key Principles:**
  1. **Human Accountability:** "Evidence synthesists are ultimately responsible for their evidence synthesis, including the decision to use artificial intelligence"
  2. **Methodological Integrity:** AI use must not "compromise the methodological rigor or integrity"
  3. **Transparency:** "Any use of AI or automation that makes or suggests judgements should be fully and transparently reported"
  4. Single-reviewer abstract screening carries ~13% risk of missing relevant studies; "using AI as a second 'reviewer' could help reduce this risk"
- **Required Reporting:** AI tool name, version, dates; specific purposes and stages; validation evidence; known limitations; financial interests
- **Relevance:** The gold-standard position statement from the four major evidence synthesis organizations. Explicitly supports AI as a "second reviewer" and endorses the RAISE framework. Our approach aligns with their guidance if we maintain human oversight and report transparently.

### 2.3. RAISE Framework (Version 2, 2025)

- **Title:** Responsible use of AI in evidence SynthEsis (RAISE) Recommendations
- **Version:** 2.0 (updated June 3, 2025); Version 2.1 in development as of September 2025
- **URL:** https://osf.io/fwaud/
- **Cochrane Reference:** https://www.cochrane.org/events/recommendations-and-guidance-responsible-ai-evidence-synthesis
- **Key Principles:**
  - During protocol development, synthesists should consider trade-offs between capacity/resources and urgency/relevance/scope
  - Risk assessment: consider context of synthesis, risk tolerance for errors, and available mitigation strategies
  - Accountability, transparency, ethical responsibility, continuous human oversight
- **Relevance:** The RAISE framework is endorsed by Cochrane, Campbell, JBI, and CEE. It provides the conceptual foundation for justifying AI use with appropriate safeguards.

### 2.4. Gartlehner et al. (2025) — Cochrane Rapid Reviews AI Position

- **Title:** "Responsible Integration of Artificial Intelligence in Rapid Reviews: A Position Statement From the Cochrane Rapid Reviews Methods Group"
- **Authors:** Gerald Gartlehner, Barbara Nussbaumer-Streit, Candyce Hamel, Chantelle Garritty, Ursula Griebler, Valerie Jean King, Declan Devane, Chris Kamel
- **Journal:** Cochrane Evidence Synthesis and Methods, 3(6)
- **DOI:** [10.1002/cesm.70063](https://doi.org/10.1002/cesm.70063)
- **Published:** November 24, 2025
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12644243/
- **Key Guidance:**
  - "Human oversight is essential to maintain methodological rigor and accountability"
  - AI can function as a "scalable quality control tool" for screening
  - Human reviewers retain final decision-making authority
  - Must document model versions and prompts used
  - "Human responsibility cannot be delegated to AI systems"
- **Relevance:** Cochrane's most specific guidance on AI for screening. Explicitly permits AI as a quality control mechanism for screening decisions while keeping humans accountable.

---

## 3. Inter-Rater Reliability Approaches with AI

### 3.1. Hanegraaf et al. (2024) — Human IRR Benchmarks for ML-Assisted Reviews

- **Title:** "Inter-reviewer reliability of human literature reviewing and implications for the introduction of machine-assisted systematic reviews: a mixed-methods review"
- **Authors:** Piet Hanegraaf, Abrham Wondimu, Jacob Jan Mosselman, Rutger de Jong, Seye Abogunrin, Luisa Queiros, Marie Lane, Maarten J Postma, Cornelis Boersma, Jurjen van der Schans
- **Journal:** BMJ Open, 14(3), e076912
- **DOI:** [10.1136/bmjopen-2023-076912](https://doi.org/10.1136/bmjopen-2023-076912)
- **Published:** March 19, 2024
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10952858/
- **Key Findings:**

| Screening Stage | Mean Cohen's Kappa | SD |
|-----------------|--------------------|----|
| Abstract screening | 0.82 | 0.11 |
| Full-text screening | 0.77 | 0.18 |
| Overall screening | 0.86 | 0.07 |
| Data extraction | 0.88 | 0.08 |

  - Survey of 37 systematic review authors: expected kappa for ML-assisted SLRs ranges 0.6-0.9
  - "Authors expect a higher-than-average IRR for machine learning-assisted SLR compared with human-based SLR"
  - "Currently, it is not common to report on IRR in the scientific literature for either human and machine learning-assisted SLRs"
  - Recommend "minimal strong agreement" as threshold for ML-assisted reviews
- **Relevance:** Establishes the benchmark. If our AI-human kappa exceeds 0.82 for abstract screening, we exceed the average human-human IRR. A kappa of 0.6-0.9 is the expected and acceptable range.

### 3.2. Landschaft et al. (2024) — Cohen's Kappa > 0.9 for GPT-4 Screening

(See Section 1.4 above)
- Achieved Cohen's kappa > 0.9 between GPT-4 and human reviewer for abstract screening
- This exceeds average human-human agreement (0.82 per Hanegraaf et al.)
- **Relevance:** Direct evidence that AI-human kappa can surpass human-human kappa

### 3.3. Validation Sample Sizes — Covidence and Field Recommendations

- **Source:** Covidence Support Documentation and field practice
- **URL:** https://support.covidence.org/help/should-i-use-automation-ai-in-my-review
- **Recommended Approach:**
  - **Large reviews:** Check 50-100 records or **20% of excluded set** to identify systematic errors
  - **Smaller reviews:** Verify a larger proportion
  - If agreement is confirmed on the sample, proceed with confidence
  - Cite this validation step in methods to demonstrate methodological rigor
- **Performance monitoring:** Quality assurance checks should continue over time
- **Relevance:** Provides specific, actionable guidance for our validation protocol. A 20% random verification of AI screening decisions is an established and defensible practice.

---

## 4. Criticisms, Limitations, and Failure Modes

### 4.1. Lieberum et al. (2025) — "Not Yet Ready for Use"

- **Title:** "Large language models for conducting systematic reviews: on the rise, but not yet ready for use — a scoping review"
- **Authors:** Judith-Lisa Lieberum, Markus Toews, Maria-Inti Metzendorf, Felix Heilmeyer, Waldemar Siemens, Christian Haverkamp, Daniel Böhringer, Joerg J Meerpohl, Angelika Eisele-Metzger
- **Journal:** Journal of Clinical Epidemiology, 181, 111746
- **DOI:** [10.1016/j.jclinepi.2025.111746](https://doi.org/10.1016/j.jclinepi.2025.111746)
- **URL:** https://pubmed.ncbi.nlm.nih.gov/40021099/
- **Key Criticisms:**
  - Only ~54% of studies found LLM use promising; 24% neutral; 22% unpromising
  - 57% of studies were validation studies (experimental, not operational)
  - "Fully established or validated applications are often lacking"
  - No consensus on LLM reliability for systematic review production
  - Variability in nondeterministic LLM responses is a concern
  - GPT models dominated (89% of studies) — limited evidence for other LLMs
- **Relevance:** The strongest published criticism. Must be acknowledged in our limitations. However, their concern is primarily about **fully automated** reviews without human oversight — our approach uses AI as an assistant with human validation, which partially addresses these concerns.

### 4.2. Hallucination and Precision Concerns

- **Source:** Multiple studies, including Springer Nature review on ChatGPT hallucination
- **URL:** https://link.springer.com/article/10.1007/s00146-025-02406-7
- **Key Concerns:**
  - In structured screening tasks, sensitivity ranges 80.6%-96.2%
  - Precision can drop as low as 4.6% in interpretive tasks
  - Hallucination rates reached 91% in some synthesis tasks (NOT screening — this applies to generative tasks)
  - AI matches/exceeds human performance in simple screening but underperforms in nuanced synthesis
- **Relevance:** The hallucination concern is primarily about generative tasks (writing summaries, extracting data) rather than binary screening decisions (include/exclude). Our use case (title/abstract screening against defined criteria) is the task where AI performs best.

### 4.3. Khraisha et al. (2024) — Performance on Balanced Datasets

(See Section 1.3 above)
- When datasets are balanced (~1:1 include/exclude ratio), screening performance drops to "none"
- Performance is better on imbalanced datasets (typical of real screening, where most records are excluded)
- Prompt quality is the strongest determinant of performance
- **Relevance:** In our bibliometric analysis, the include/exclude ratio is likely imbalanced (most records excluded), which is the favorable condition for AI screening.

### 4.4. Key Failure Modes to Address

Based on the literature, the following failure modes should be acknowledged:

1. **Prompt sensitivity:** Small changes in prompt wording can dramatically affect performance (zero-shot: 49% sensitivity vs. optimized: 97.7%)
2. **Non-determinism:** Same input can produce different outputs across runs
3. **Dataset balance:** Performance degrades on balanced datasets
4. **Domain specificity:** Most validation is in biomedical literature; less evidence for social science/policy domains
5. **Version dependency:** Performance varies across model versions; results may not replicate with future model updates
6. **Inclusion bias:** AI tends toward over-inclusion (high sensitivity, lower specificity) which inflates workload but reduces missed studies

---

## 5. Publisher Editorial Policies on AI Use

### 5.1. Major Publisher Requirements (2025-2026)

| Publisher | AI Use Allowed | Disclosure Required | Location | Notes |
|-----------|---------------|-------------------|----------|-------|
| **Elsevier** | Yes, with oversight | Yes | Separate AI declaration | Must be reproducible if part of methodology |
| **Springer Nature** | Yes, with oversight | Yes | Methods section | Exempts AI copy editing from disclosure |
| **Wiley** | Yes, with oversight | Yes | Methods or Acknowledgements | "Transparently and in detail" |
| **Taylor & Francis** | Yes, with oversight | Yes | Methods section | Prohibits text generation without rigorous revision |

- **Source:** https://www.thesify.ai/blog/ai-policies-academic-publishing-2025
- **Common Requirements:**
  - AI systems cannot be listed as authors
  - Use must be documented with tool name, version, and purpose
  - Human accountability for all published content
  - If AI is part of research methodology, must be described reproducibly
- **Relevance:** All major publishers now accept AI-assisted methodology in systematic reviews as long as it is transparently reported. None prohibit AI-assisted screening.

### 5.2. Cross-Disciplinary Analysis (Wang, 2026)

- **Title:** "A Cross-Disciplinary Analysis of AI Policies in Academic Peer Review"
- **Journal:** Learned Publishing, 2026
- **DOI:** [10.1002/leap.2035](https://doi.org/10.1002/leap.2035)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1002/leap.2035
- **Key Finding:** Strong consensus across publishers on core principles: prohibition of AI as author, transparency through disclosure, human accountability
- **Relevance:** Confirms that the publishing landscape broadly supports responsible AI use in research methodology

---

## 6. Practical Recommendations for Our Methods Section

Based on the literature reviewed, the following elements should be included in our methodology:

### 6.1. What to Report (Minimum Requirements)

Drawing from PRISMA-trAIce, Cochrane Position Statement, and RAISE:

1. **Tool identification:** Name (e.g., Claude 3.5 Sonnet), version, developer (Anthropic), access date
2. **Stage of use:** Specify that AI was used for title/abstract screening only (not data extraction or synthesis)
3. **Prompts:** Provide the exact prompts used, including inclusion/exclusion criteria given to the AI
4. **Validation protocol:** Report percentage of AI decisions manually verified, the kappa statistic, and resolution process for disagreements
5. **Limitations:** Acknowledge non-determinism, domain applicability, and version dependency

### 6.2. Recommended Validation Protocol

Based on Covidence guidance and field practice:

1. **Dual screening:** Use AI as one "rater" and human as the other
2. **Full overlap sample:** Screen a random subset (minimum 20%, or 50-100 records) with both human and AI independently
3. **Compute Cohen's kappa:** Target kappa >= 0.80 (matching human-human benchmarks from Hanegraaf et al.)
4. **If kappa < 0.80:** Revise prompts and re-run; do not proceed with AI-assisted screening
5. **Discrepancy resolution:** All disagreements resolved by human reviewer with final authority
6. **Document everything:** Record all prompts, model parameters, and version numbers

### 6.3. Suggested Methods Section Language

The following language is informed by published precedents:

> "Title and abstract screening was conducted using a dual-reviewer approach, with one human reviewer and one AI-assisted reviewer (Claude [version], Anthropic). This approach is consistent with recent methodological guidance permitting AI as a second reviewer in evidence synthesis (Flemyng et al., 2025; Gartlehner et al., 2025) and has been validated in multiple published studies demonstrating human-comparable screening accuracy (Matsui et al., 2024; Sanghera et al., 2025; Insuk et al., 2025). Inter-rater reliability was computed using Cohen's kappa on a [X]% random sample, achieving a kappa of [X.XX], which [meets/exceeds] the human-human benchmark of 0.82 reported in the literature (Hanegraaf et al., 2024). Disagreements were resolved by the human reviewer. This process is reported following the PRISMA-trAIce checklist (Holst et al., 2025) and RAISE recommendations (Version 2, 2025)."

---

## 7. Summary of Key Findings

### Evidence Supporting AI-Assisted Screening

| Finding | Source | Strength |
|---------|--------|----------|
| Meta-analysis SROC AUC = 0.922 for LLM screening | Kim et al. (2025) | Strong (meta-analysis) |
| GPT-4-human kappa > 0.9 for abstract screening | Landschaft et al. (2024) | Moderate (single study) |
| Claude accuracy 0.9448 vs human 0.9593 | Insuk et al. (2025) | Moderate (single study) |
| Claude sensitivity 0.819, specificity 0.966 | Sanghera et al. (2025) | Strong (23 reviews) |
| GPT-4 adjusted sensitivity 0.943-0.962 | Matsui et al. (2024) | Moderate (2 reviews) |
| Cochrane explicitly permits AI as second reviewer | Flemyng et al. (2025) | Strong (consensus statement) |
| PRISMA-trAIce provides reporting framework | Holst et al. (2025) | Strong (guideline) |

### Evidence Urging Caution

| Finding | Source | Implication |
|---------|--------|-------------|
| Only 54% of studies found LLM use promising | Lieberum et al. (2025) | Acknowledge limitations |
| Performance varies with prompt quality | Khraisha et al. (2024) | Must optimize and validate prompts |
| Non-deterministic outputs | Multiple sources | Run screening multiple times or use temperature=0 |
| Limited validation outside biomedicine | Lieberum et al. (2025) | Acknowledge domain gap |
| "Substantial caution" recommended | Khraisha et al. (2024) | Human oversight is non-negotiable |

### Bottom Line

The literature from 2024-2025 provides **substantial and growing evidence** that AI-assisted screening is a legitimate methodology when:
1. Used as an assistant/second reviewer — not a replacement for humans
2. Validated with inter-rater reliability statistics against human decisions
3. Reported transparently following PRISMA-trAIce and RAISE guidelines
4. Acknowledged with appropriate limitations
5. Conducted with optimized prompts and documented model versions

The approach has been published in high-impact journals (JMIR, JAMIA, BMJ Open, Research Synthesis Methods, Cochrane Evidence Synthesis and Methods, Journal of Clinical Epidemiology) and is endorsed by Cochrane, Campbell, JBI, and CEE.

---

## References (Alphabetical)

1. Flemyng E, et al. (2025). Position Statement on AI Use in Evidence Synthesis. *Campbell Systematic Reviews*. DOI: 10.1002/cl2.70074
2. Gartlehner G, et al. (2025). Responsible Integration of AI in Rapid Reviews. *Cochrane Evidence Synthesis and Methods*, 3(6). DOI: 10.1002/cesm.70063
3. Hanegraaf P, et al. (2024). Inter-reviewer reliability of human literature reviewing. *BMJ Open*, 14(3). DOI: 10.1136/bmjopen-2023-076912
4. Holst D, et al. (2025). PRISMA-trAIce Checklist. *JMIR AI*. DOI: 10.2196/80247
5. Insuk S, et al. (2025). ChatGPT and Claude in Study Selection. *Journal of Medical Systems*, 49(1). DOI: 10.1007/s10916-025-02246-4
6. Khraisha Q, et al. (2024). Can LLMs replace humans in systematic reviews? *Research Synthesis Methods*, 15(4). DOI: 10.1002/jrsm.1715
7. Kim JK, et al. (2025). Evaluating LLMs for screening: meta-analysis. *JMAI*. DOI: 10.21037/jmai-24-408
8. Landschaft A, et al. (2024). GPT-4 as additional reviewer in PRISMA reviews. *Int J Med Inform*, 189. DOI: 10.1016/j.ijmedinf.2024.105531
9. Lieberum JL, et al. (2025). LLMs for systematic reviews: not yet ready. *J Clin Epidemiol*, 181. DOI: 10.1016/j.jclinepi.2025.111746
10. Matsui K, et al. (2024). 3-Layer Strategy Using GPT-3.5 and GPT-4. *JMIR*. DOI: 10.2196/52758
11. Oami T, et al. (2025). GPT-3.5 vs GPT-4 Turbo in Screening. *JMIR Med Inform*. DOI: 10.2196/64682
12. RAISE Recommendations v2 (2025). Responsible AI in Evidence Synthesis. https://osf.io/fwaud/
13. Rubinstein et al. (2025). GPT-4 for Policy Literature Screening. *Cochrane Evidence Synthesis and Methods*, 3(3). DOI: 10.1002/cesm.70031
14. Sanghera R, et al. (2025). LLM ensembles for abstract screening. *JAMIA*, 32(5). DOI: 10.1093/jamia/ocaf050
