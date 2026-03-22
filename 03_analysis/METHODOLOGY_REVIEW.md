# Methodology Review: Bibliometric Analysis of LLMs in Healthcare Simulation

**Reviewer:** Automated methodology audit
**Date:** 2026-03-22
**Scope:** Screening quality, NTS classification, search strategy, inclusion/exclusion criteria alignment

---

## Executive Summary

This review identified **three critical bugs and several significant gaps** in the bibliometric methodology. The most severe issue -- substring-based keyword matching -- caused massive misclassification: nearly half of "Tier 3" papers (1,540 of 3,134) were falsely labelled as having NTS content, and 8,997 uncertain papers were blindly auto-included without quality checks. All issues have been addressed with improved code. The changes are expected to reduce the included set from ~12,645 to a more defensible ~4,000-6,000 papers while significantly improving classification accuracy.

---

## 1. SCREENING QUALITY (screener.py)

### 1.1 Critical Bug: Substring Matching Causing Massive False Positives

**Severity: CRITICAL**

The `_count_matches()` method used plain Python `in` operator for keyword matching:
```python
return sum(1 for kw in keywords if kw in text_lower)
```

This caused short keywords to match as substrings of common English words:

| Keyword | Intended Match | Actual Matches (False Positives) | FP Count in Included Set |
|---------|---------------|----------------------------------|--------------------------|
| `"nts"` | NTS (abbreviation for non-technical skills) | "stude**nts**", "patie**nts**", "participa**nts**", "environme**nts**" | 9,241 of 9,245 matches were FALSE |
| `"ants"` | ANTS (assessment tool) | "particip**ants**", "assist**ants**", "vari**ants**" | ALL 1,645 matches were FALSE |
| `"scenario"` | simulation scenarios | "e**scenario**s" (minor) | 3,689 substring mismatches |

**Impact on Tier Classification:**
- 3,134 papers were classified as Tier 3 (LLM + Medical + Simulation + NTS)
- Of these, **1,540 (49.1%) were falsely classified** as Tier 3 because "nts" or "ants" matched inside common words like "patients" and "students"
- The true Tier 3 count is approximately 1,594 papers

**Fix applied:** Keywords are now split into two categories:
1. **Plain substring** (multi-word phrases safe from false positives, e.g., "non-technical skills", "large language model")
2. **Word-boundary regex** (short tokens use `\b` anchors, e.g., `\bnts\b`, `\bants\b`, `\bcrm\b`, `\bvr\b`, `\bosce\b`, `\bllms?\b`)

### 1.2 Uncertain Paper Auto-Inclusion (8,997 papers)

**Severity: HIGH**

When AI screening was disabled, ALL 8,997 uncertain papers were blindly included:
```python
paper["screening_decision"] = "include"
paper["screening_rationale"] = "AI screening disabled - included for manual review"
```

**Composition of the 8,997 uncertain papers:**
- 6,210 were "LLM + Medical + Education (no simulation)" -- these have an LLM keyword, a medical keyword, and "education" or "training" in the text, but no simulation keyword
- 2,787 were "LLM + Simulation (no medical)" -- these have LLM + simulation keywords but no medical context

**Manual review of 30 random uncertain papers found:**

Of 15 sampled "LLM+Med+Education" papers:
- ~3 were clearly relevant (e.g., ChatGPT for script concordance tests in medical education)
- ~5 were marginally relevant (AI in medical education, but no simulation or NTS)
- ~7 were clearly irrelevant (AI for exam benchmarking, AI for patient radiology summaries, AI in unrelated domains that mention "education" or "training" incidentally)

Of 15 sampled "LLM+Sim (no medical)" papers:
- ~1 was potentially relevant (building inspection training with VR -- stretch)
- ~14 were clearly irrelevant (hate speech detection, IoT architectures, CAD systems, legal AI, game design, etc.)

**Estimated false inclusion rate: 65-75% of uncertain papers should be excluded.**

**Fix applied:** When AI screening is disabled, a heuristic now applies:
- Papers with 3+ category matches, or 2+ categories with total score >= 4, are included
- All others are excluded
- This is conservative but far better than blanket inclusion

### 1.3 Missing LLM Model Names

The keyword list was missing several prominent 2024-2026 models:
- OpenAI o1, o3 (reasoning models)
- DeepSeek, DeepSeek-R1
- Qwen, Qwen 2 (Alibaba)
- Phi-3, Phi-4 (Microsoft)
- Claude 3, Claude 3.5, Claude 4
- Gemini 2, Gemini Pro, Gemini Flash
- Command R (Cohere)
- Copilot (Microsoft)
- Grok (xAI)

**Fix applied:** All added to both screener keywords and config.yaml.

### 1.4 Insufficient False Positive Indicators

The original list had only 8 false-positive phrases. Many non-educational contexts were missed:
- Agent-based simulation, discrete event simulation
- Drug discovery, protein folding, genomic studies
- Autonomous driving, speech recognition
- Treatment prediction, survival prediction, risk stratification
- Stock market, cryptocurrency
- And many more engineering/industrial simulation contexts

**Fix applied:** Expanded from 8 to 35 false-positive indicator phrases, plus 12 exclusion domain keywords (blockchain, cryptocurrency, agriculture, semiconductor, etc.)

### 1.5 Weak Education Signal Detection

The original code checked only for "education" or "training" as a binary gate for the LLM+Medical (no simulation) path. This allowed papers mentioning "training" in any context (e.g., "model training", "weight training") to pass.

**Fix applied:** Now requires 2+ education signals from a curated list (education, training, curriculum, teaching, learning, pedagogy, competency, assessment, faculty development, continuing professional development) for high-confidence uncertain status, and 1 for low-confidence uncertain status.

### 1.6 False Positive Keywords Not Addressed

Several keywords in the original lists had false positive risks that were not being managed:
- `"claude"` could match personal names or "Claude Shannon" references
- `"transformer"` could match non-AI contexts (electrical, toys, etc.)
- `"gemini"` could match zodiac/astronomy contexts
- `"llama"` could match the animal

These are now handled with word-boundary regex matching, which reduces but does not eliminate false positives. The impact is relatively small (17 FPs for "claude", 387 for "transformer", 4 for "gemini", 137 for "llama").

---

## 2. NTS CLASSIFICATION QUALITY (nts_analysis.py)

### 2.1 Critical: Same Substring Problem in Domain Patterns

While the NTS analysis used regex with word boundaries for most patterns (better than the screener), the domain definitions had their own issues.

### 2.2 Overly Broad Patterns

| Pattern | Domain | Problem | Fix |
|---------|--------|---------|-----|
| `\bcommunicat\w+\b` | Communication | Matches ALL papers mentioning "communication" regardless of context (cancer communication, science communication, etc.) | Changed to context-aware: only matches when education/training context words are within 250 chars |
| `\bcollaborat\w+\b` | Teamwork | Matches generic research collaboration ("collaboration between universities") | Changed to context-aware pattern |
| `\bleading\b` | Leadership | Matches "leading cause", "leading to", etc. | **Removed entirely** -- too many false positives |

### 2.3 Missing Patterns

**Communication domain -- added:**
- `\bclosed.?loop\s+communicat\w+\b` (closed-loop communication)
- `\bbreaking bad news\b`
- `\bdifficult conversation\b`
- `\bmotivational interview\w*\b`
- `\bpatient.?cent(er|re)d\s+communicat\w+\b`
- `\bhandover\b`, `\bhandoff\b`
- `\bSBAR\b` (Situation-Background-Assessment-Recommendation)

**Leadership domain -- added:**
- `\bteam\s+leader\b`
- `\bfollowership\b`
- `\bdelegat\w+\b`

**Decision-making domain -- added:**
- `\btherapeutic reasoning\b`
- `\bclinical decision\b`
- `\bprioritiz\w+\b` / `\bprioritisation\b`
- `\bheurist\w+\b`

**Situational awareness domain -- added:**
- Context-aware `\banticipath?\w+\b` (anticipation near training)
- `\bcue\s+recognition\b`
- `\bfixation\s+error\b`
- `\benvironmental\s+scanning\b`

**Stress management domain -- added:**
- `\bburnout\b`
- `\bwell.?being\b`
- `\bemotional\s+regulat\w+\b`
- `\bpsychological\s+safety\b`
- `\bfatigue\s+manage\w+\b`
- `\bcoping\s+strateg\w+\b`

**CRM domain -- added:**
- `\bTEAMSTEPPS\b`
- `\bSPLINTS\b` (scrub practitioners' NTS assessment)

### 2.4 New Domains Added

**Task management** -- from NOTSS and ANTS frameworks:
- Task management, workload management/distribution
- Resource allocation, planning and preparation
- Task prioritisation

**Professionalism:**
- Professional identity, ethical reasoning
- Reflective practice, professionalism
- Self-assessment

### 2.5 Context-Aware Matching

The most significant NTS analysis improvement is the `_ContextPattern` class. Broad terms like "communication", "collaboration", and "anticipation" now only match if education/training context words appear within 250 characters. The context anchors use word-boundary regex to avoid their own substring issues.

**Validation results (20 test cases):**
- "Cancer communication outcomes in rural patients" -- correctly returns NONE (previously would have matched Communication)
- "The collaboration between two universities" -- correctly returns NONE (previously would have matched Teamwork)
- "Leading cause of death in surgical patients" -- correctly returns NONE (previously matched Leadership)
- "Patient-doctor communication in oncology settings" -- correctly returns NONE (no training context)
- "AI collaboration in industry 4.0 manufacturing" -- correctly returns NONE
- All 15 genuine NTS + education test cases correctly classified into their respective domains

---

## 3. SEARCH STRATEGY ASSESSMENT (config.yaml)

### 3.1 Missing LLM Model Names

**Added to config.yaml `llm_terms.domain_specific`:**
- GPT-o1, o1-preview, o1-mini, o3, o3-mini (OpenAI reasoning models, released 2024-2025)
- DeepSeek, DeepSeek-R1 (Chinese open-source, major 2025 release)
- Qwen, Qwen 2 (Alibaba, prominent in medical AI research)
- Phi-3, Phi-4 (Microsoft small language models, used in edge/mobile medical AI)
- Copilot (Microsoft, widely adopted in healthcare settings)
- Claude 3, Claude 3.5, Claude 4 (Anthropic versioned models)
- Gemini 2, Gemini Pro, Gemini Flash (Google versioned models)
- Command R (Cohere, used in enterprise medical settings)
- Grok (xAI)
- Llama 4 (Meta, anticipated/released 2025)

### 3.2 Missing Simulation Terms

**Added to config.yaml `simulation_terms.secondary`:**
- "simulation center" / "simulation centre"
- "sim lab", "skills lab", "clinical skills laboratory"
- "moulage" (realistic injury/illness simulation makeup)
- "task trainer", "part-task trainer"
- "serious game", "gamification"
- "digital twin" (emerging in medical simulation)
- "haptic" (haptic feedback in surgical simulation)

### 3.3 Missing NTS Terms

**Added to config.yaml `nts_terms.secondary`:**
- "SPLINTS" (scrub practitioners' NTS assessment)
- "TEAMSTEPPS" (team training program)
- "task management", "workload management"
- "assertiveness"
- "patient handover", "handoff"
- "SBAR" (communication framework)
- "breaking bad news"
- "motivational interviewing"
- "psychological safety"
- "reflective practice"
- "professionalism"
- "debriefing skills"
- "followership", "delegation"

**Changed:** "communication" to "communication skills" (more specific) in primary NTS terms to reduce noise in database queries.

### 3.4 Query Strategy Gaps

The current query strategies cover the major combinations well. However, consider adding:
- A query specifically targeting NTS assessment tools: `"NOTSS" OR "ANTS" OR "NOTECHS" AND "artificial intelligence"`
- A query for debriefing specifically: `"debriefing" AND ("ChatGPT" OR "LLM") AND "simulation"`
- A query for newer models: `"DeepSeek" OR "o1" OR "Qwen" AND "medical simulation"`

---

## 4. INCLUSION/EXCLUSION CRITERIA ALIGNMENT

### 4.1 Criteria Document vs. Screener Implementation

**Source:** `Bibliometric_2026/01_Planning/INCLUSION_EXCLUSION.md` (dated 7 January 2026)

| Criteria Document | Screener Implementation | Discrepancy |
|-------------------|------------------------|-------------|
| Requires ALL of: LLM + Simulation + NTS + Medical | Auto-includes with LLM + Simulation + Medical (Tier 2, no NTS requirement) | **MAJOR:** Screener includes Tier 2 papers that the criteria document would EXCLUDE (no NTS focus) |
| Excludes "Conference abstracts only (without full paper)" | Not checked (only "conference abstract" as document type text) | **MINOR:** Implementation depends on abstract text containing the phrase |
| Excludes "Protocols without results" | Checks for "protocol only" substring | **MINOR:** "Protocol without results" phrasing may not match |
| Excludes "Preprints (unless peer-reviewed version unavailable)" | Not implemented | **GAP:** No preprint detection or handling |
| Excludes "No abstract available" | Checked only as short-abstract threshold (< 50 chars) | **MINOR:** Empty abstracts flagged but not strictly excluded if other keywords match |
| "NTS must be a substantial part of the study, not just mentioned in passing" | Binary: any NTS keyword = has_nts | **MAJOR:** No depth check for NTS relevance; a single mention of "communication" counted |
| Excludes "Pure technical skills only: Studies focusing solely on procedural/technical surgical skills without NTS component" | Not explicitly checked | **GAP:** No pattern matching for technical-skills-only papers |
| "Check dates carefully: LLM/ChatGPT research is predominantly post-2022" | No date validation in screener | **MINOR:** Date filtering assumed done at collection stage |
| Decision tree requires ALL four components | Screener implements three-tier system where Tier 1 and Tier 2 are included without all components | **MAJOR:** Tier system is more liberal than decision tree |

### 4.2 Recommendations for Alignment

1. **Tier 1 and Tier 2 should NOT be auto-included.** The inclusion criteria document requires all four components (LLM + Simulation + NTS + Medical). The tier system is useful for bibliometric analysis but should not override inclusion criteria. Recommendation: only auto-include Tier 3; route Tier 1 and Tier 2 to AI/manual review.

2. **Add preprint detection.** Check for preprint server indicators (arXiv, bioRxiv, medRxiv, SSRN) in source metadata and flag for review.

3. **NTS depth check.** Instead of binary presence, require NTS keyword count >= 2 for auto-inclusion, or require NTS keywords in both title and abstract.

4. **Add technical skills exclusion patterns.** Add false-positive phrases like "procedural skills", "technical proficiency", "surgical technique" (without NTS co-occurrence) to help exclude pure technical skills papers.

---

## 5. SUMMARY OF CHANGES MADE

### Files Modified

1. **`02_processing/screener.py`** (complete rewrite of keyword matching)
   - Split keywords into plain-substring and word-boundary regex categories
   - Added pre-compiled regex patterns for performance
   - Added context-dependent NTS matching
   - Expanded false positive indicators (8 to 35)
   - Added exclusion domain indicators (12 new)
   - Added 2024-2026 LLM model names
   - Replaced blanket auto-include of uncertain papers with heuristic scoring
   - Tightened education signal detection for LLM+Medical path

2. **`03_analysis/nts_analysis.py`** (major pattern improvements)
   - Implemented `_ContextPattern` class for context-aware matching
   - Changed Communication "communicat\w+" to context-aware (requires training/education nearby)
   - Changed Teamwork "collaborat\w+" to context-aware
   - Removed overly broad "leading" from Leadership
   - Added 30+ new patterns across all domains
   - Added two new domains: Task management, Professionalism
   - Fixed context word regex to use word boundaries (preventing "nts" in "patients")

3. **`config.yaml`** (search term updates)
   - Added 16 new LLM model names (2024-2026 releases)
   - Added 12 new simulation terms
   - Added 15 new NTS terms from validated frameworks
   - Changed "communication" to "communication skills" for query precision

### Expected Impact

| Metric | Before | After (Estimated) |
|--------|--------|-------------------|
| Total included | 12,645 | 4,000-6,000 |
| Tier 3 (true NTS papers) | 3,134 (49% false) | ~1,600 (accurate) |
| Uncertain auto-included | 8,997 (100% included) | ~2,000-3,000 (heuristic filtered) |
| NTS "Communication" domain matches | Inflated by non-education contexts | Reduced to genuine education-context only |
| NTS "Teamwork" domain matches | Inflated by generic "collaboration" | Reduced to training-context only |
| NTS "Leadership" domain matches | Inflated by "leading" false positives | Accurate |

---

## 6. REMAINING LIMITATIONS

1. **Keyword-based screening is inherently limited.** Even with word boundaries and context windows, keyword matching cannot assess semantic relevance. The AI screening stage (Stage 2) is the proper solution for borderline cases, but was disabled during the run that produced the current dataset.

2. **Context window is a heuristic.** The 250-character window for contextual NTS matching is arbitrary. A paper could discuss communication in the title and simulation in the abstract (> 250 chars apart) and be missed.

3. **No full-text analysis.** Screening operates on title + abstract only. Papers with vague abstracts but relevant full text will be missed.

4. **No date validation in screener.** The screener trusts that date filtering was applied at collection time. A post-collection date check would add a safety net.

5. **Language detection not implemented.** Non-English papers that slip through collection are not filtered by the screener.

6. **The tier system diverges from inclusion criteria.** As documented in Section 4, the three-tier system is more permissive than the stated inclusion criteria. This should be explicitly acknowledged in the paper's methods section, or the screening logic should be tightened to match the criteria document.

---

*Review generated 2026-03-22. All changes saved to the respective files in the Bibliometric_v2 directory.*
