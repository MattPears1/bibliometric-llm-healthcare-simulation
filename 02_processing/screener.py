#!/usr/bin/env python3
"""
Two-stage paper screener for bibliometric analysis.
Stage 1: Fast keyword-based pre-filter (immediate include/exclude for clear cases)
Stage 2: AI-assisted context screening via Claude API (for uncertain cases)

Implements three-tier scope:
  Tier 1: LLM + Medical (broadest)
  Tier 2: LLM + Medical + Simulation
  Tier 3: LLM + Medical + Simulation + NTS (most focused)

v2 IMPROVEMENTS (Methodology Review 2026-03-22):
  - Fixed critical substring matching bugs: short keywords (nts, ants, crm, vr,
    osce, llm, nlp) now use word-boundary regex to prevent false positives
    (e.g., "nts" was matching "students", "patients"; "ants" was matching
    "participants", "assistants")
  - Separated keywords into plain-substring and word-boundary categories
  - Added 2025-2026 LLM model names (o1, o3, DeepSeek, Qwen, Phi-3/4, etc.)
  - Expanded false positive indicators to catch non-educational AI/simulation
  - Added exclusion keywords for clearly off-topic domains
  - Tightened uncertain-zone logic: LLM+Med+Education papers now require
    stronger educational context signals before inclusion
  - Added context-aware NTS matching to reduce false positives on broad terms
    like "communication" and "collaboration"
"""

import json
import logging
import re
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class PaperScreener:
    """Two-stage paper screening with keyword pre-filter and AI context screening."""

    # -----------------------------------------------------------------------
    # Keyword lists for Stage 1
    # Split into PLAIN (safe for substring matching) and REGEX (need word
    # boundaries to avoid false positives on short tokens).
    # -----------------------------------------------------------------------

    # --- LLM/AI Keywords ---
    # Plain substring matches (multi-word phrases, safe from false positives)
    LLM_KEYWORDS_PLAIN = [
        "large language model", "chatgpt", "gpt-4", "gpt-3", "gpt-5",
        "gpt-4o", "gpt-4 turbo", "gpt-3.5",
        "generative ai", "generative artificial intelligence",
        "natural language processing", "foundation model",
        "ai chatbot", "conversational ai",
        "artificial intelligence",
        # Specific model names (multi-word or long enough to be safe)
        "biogpt", "med-palm", "med-palm 2", "medgpt",
        "transformer model",
        # 2024-2026 models
        "deepseek", "deep seek",
        "phi-3", "phi-4",
        "copilot",
    ]
    # Word-boundary regex matches (short tokens prone to substring FPs)
    LLM_KEYWORDS_REGEX = [
        r"\bllms?\b",           # "llm" or "llms" but not "enrollment"
        r"\bnlp\b",             # "nlp" but not part of other words
        r"\bclaude\b",          # "claude" the AI model (not names in text)
        r"\bgemini\b",          # "gemini" the AI model (not zodiac)
        r"\bllama\s*\d?\b",     # "llama", "llama 2", "llama 3" but not the animal easily
        r"\bmistral\b",         # "mistral" the AI model
        r"\btransformer\b",     # "transformer" but not "transformers" (the movie/toy)
        r"\bgpt\b",             # bare "gpt" (catches GPT references)
        # 2024-2026 model names
        r"\bo1\b",              # OpenAI o1
        r"\bo3\b",              # OpenAI o3
        r"\bqwen\b",            # Alibaba Qwen
        r"\byi\b",              # 01.AI Yi -- very short, may FP; kept for completeness
        r"\bcommand\s*r\b",     # Cohere Command R
    ]

    # --- Simulation Keywords ---
    SIMULATION_KEYWORDS_PLAIN = [
        "simulation", "simulator", "simulated patient", "standardized patient",
        "standardised patient", "virtual patient", "high-fidelity", "low-fidelity",
        "debriefing", "mannequin", "virtual reality", "mixed reality",
        "augmented reality", "immersive", "sim-based", "simulation-based",
        "training scenario", "in-situ simulation",
        "objective structured clinical examination",
        "roleplay", "role-play", "role play",
        "scenario-based",
    ]
    SIMULATION_KEYWORDS_REGEX = [
        r"\bvr\b",              # "vr" but not part of other words
        r"\bxr\b",              # extended reality
        r"\bosce\b",            # but not "osceo" etc.
        r"\bscenarios?\b",      # scenario/scenarios as whole words only
    ]

    # --- NTS Keywords ---
    # These are ESPECIALLY sensitive to false positives. Many short abbreviations
    # and common English words.
    NTS_KEYWORDS_PLAIN = [
        "non-technical skills", "non technical skills", "nontechnical skills",
        "teamwork", "decision making", "decision-making",
        "situational awareness", "situation awareness", "human factors",
        "crisis resource management", "crew resource management",
        "soft skills", "interprofessional",
        "closed-loop communication", "cognitive load",
        "stress management", "team training", "team performance",
        "clinical reasoning", "shared mental model",
        # Additional NTS terms from validated frameworks
        "task management", "workload management",
        "assertiveness", "patient handover", "handoff",
        "briefing", "prebriefing", "pre-briefing",
        "after action review",
        "professional identity",
    ]
    NTS_KEYWORDS_REGEX = [
        r"\bnts\b",             # "NTS" abbreviation only, not "students"/"patients"
        r"\bcrm\b",             # "CRM" abbreviation only
        r"\bnotss\b",           # NOTSS assessment tool
        r"\bants\b",            # ANTS assessment tool, not "participants"
        r"\bnotechs\b",         # NOTECHS assessment tool
        r"\bsplints\b",         # SPLINTS assessment tool (scrub practitioners)
    ]
    # Context-dependent NTS keywords: these common words only count as NTS
    # if they appear near education/training/simulation context words.
    NTS_KEYWORDS_CONTEXTUAL = [
        "communication", "leadership", "empathy", "collaboration",
    ]
    # Context words that must appear near contextual NTS keywords
    NTS_CONTEXT_ANCHORS = [
        "training", "simulation", "education", "skill", "competenc",
        "debrief", "assessment", "curriculum", "teach", "learn",
        "non-technical", "nontechnical", "workshop", "course",
        "faculty", "resident", "student", "trainee", "performance",
        "feedback", "scenario", "osce", "objective structured",
    ]

    # --- Medical Keywords ---
    MEDICAL_KEYWORDS_PLAIN = [
        "healthcare", "health care", "medical", "clinical", "surgical",
        "surgery", "nursing", "hospital", "physician", "doctor",
        "medical education", "surgical education",
        "anesthesia", "anaesthesia", "intensive care",
        "critical care", "nursing education", "clinical training",
        "healthcare education", "residency",
        "postgraduate", "nurse", "paramedic",
        "pharmacy", "pharmacist", "midwife", "midwifery",
        "dental", "dentist", "physiotherapy", "occupational therapy",
    ]
    MEDICAL_KEYWORDS_REGEX = [
        r"\bpatients?\b",       # "patient" / "patients" but not "impatient"
        r"\bresidents?\b",      # "resident" / "residents" not "presidential"
        r"\btrainees?\b",       # "trainee" / "trainees"
        r"\bemergency\b",       # "emergency" as whole word
        r"\bicu\b",             # ICU abbreviation
    ]

    EXCLUDE_TYPES = [
        "editorial", "letter to the editor", "commentary", "book review",
        "erratum", "correction", "retracted", "protocol only",
        "conference abstract",
    ]

    # False positive indicators - phrases that signal the paper is NOT about
    # LLMs in healthcare simulation education
    FALSE_POSITIVE_INDICATORS = [
        # Non-educational simulation contexts
        "cancer treatment outcome", "drug simulation", "monte carlo simulation",
        "computational fluid dynamics", "molecular simulation",
        "pharmacokinetic simulation", "weather simulation",
        "financial simulation", "traffic simulation",
        "agent-based simulation", "discrete event simulation",
        "fluid dynamics simulation", "electromagnetic simulation",
        "power system simulation", "circuit simulation",
        "network simulation", "structural simulation",
        "biomechanical simulation", "epidemiological simulation",
        "epidemic simulation", "climate simulation",
        "crash simulation", "flight simulation",
        "supply chain simulation", "manufacturing simulation",
        "reservoir simulation",
        # Non-educational AI contexts
        "drug discovery", "protein folding", "genomic",
        "image segmentation", "object detection",
        "autonomous driving", "self-driving",
        "speech recognition",
        "stock market", "cryptocurrency",
        "smart grid", "power grid",
        "sentiment analysis",  # NLP but not education
        "text mining",
        # Pure clinical AI (no education)
        "treatment prediction", "survival prediction",
        "risk stratification", "prognostic model",
    ]

    # Exclusion domain keywords - if these dominate the text, it's off-topic
    EXCLUDE_DOMAIN_INDICATORS = [
        "blockchain", "cryptocurrency", "internet of things",
        "smart city", "autonomous vehicle", "self-driving car",
        "agricultural", "agriculture", "crop", "livestock",
        "power plant", "solar panel", "wind turbine",
        "semiconductor", "quantum computing",
        "video game", "game design",
    ]

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        screen_config = self.config.get("processing", {}).get("screening", {})
        self.auto_include_threshold = screen_config.get("keyword_auto_include_threshold", 5)
        self.ai_enabled = screen_config.get("ai_screening_enabled", False)
        self.ai_rate_limit = screen_config.get("ai_rate_limit_seconds", 2.0)
        self.ai_model = screen_config.get("ai_model", "claude-sonnet-4-20250514")

        self.output_dir = Path(__file__).parent / "screened"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Pre-compile regex patterns for performance
        self._llm_regex = [re.compile(p, re.IGNORECASE) for p in self.LLM_KEYWORDS_REGEX]
        self._sim_regex = [re.compile(p, re.IGNORECASE) for p in self.SIMULATION_KEYWORDS_REGEX]
        self._nts_regex = [re.compile(p, re.IGNORECASE) for p in self.NTS_KEYWORDS_REGEX]
        self._med_regex = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_KEYWORDS_REGEX]

        # Stats
        self.stats = {
            "total": 0,
            "stage1_include": 0,
            "stage1_exclude": 0,
            "stage1_uncertain": 0,
            "stage2_include": 0,
            "stage2_exclude": 0,
            "tier1_count": 0,  # LLM + Medical
            "tier2_count": 0,  # + Simulation
            "tier3_count": 0,  # + NTS
        }

    def _count_plain_matches(self, text_lower: str, keywords: List[str]) -> int:
        """Count plain substring keyword matches in lowercased text."""
        return sum(1 for kw in keywords if kw in text_lower)

    def _count_regex_matches(self, text: str, compiled_patterns: List[re.Pattern]) -> int:
        """Count regex keyword matches in text."""
        return sum(1 for pat in compiled_patterns if pat.search(text))

    def _count_contextual_nts(self, text_lower: str) -> int:
        """
        Count contextual NTS keyword matches.
        These common words (communication, leadership, etc.) only count
        if they appear within ~200 chars of an education/training context anchor.
        """
        count = 0
        for kw in self.NTS_KEYWORDS_CONTEXTUAL:
            if kw not in text_lower:
                continue
            # Find all positions of this keyword
            start = 0
            found_in_context = False
            while True:
                pos = text_lower.find(kw, start)
                if pos == -1:
                    break
                # Check if any context anchor is within 200 chars
                window_start = max(0, pos - 200)
                window_end = min(len(text_lower), pos + len(kw) + 200)
                window = text_lower[window_start:window_end]
                if any(anchor in window for anchor in self.NTS_CONTEXT_ANCHORS):
                    found_in_context = True
                    break
                start = pos + 1
            if found_in_context:
                count += 1
        return count

    def _check_false_positive(self, text_lower: str) -> bool:
        """Check if the paper is likely a false positive."""
        return any(fp in text_lower for fp in self.FALSE_POSITIVE_INDICATORS)

    def _check_exclude_domain(self, text_lower: str) -> Optional[str]:
        """Check if the paper is clearly from an excluded domain."""
        for domain_kw in self.EXCLUDE_DOMAIN_INDICATORS:
            if domain_kw in text_lower:
                # Only exclude if domain keyword appears but medical context is weak
                med_count = self._count_plain_matches(text_lower, self.MEDICAL_KEYWORDS_PLAIN)
                med_count += self._count_regex_matches(text_lower, self._med_regex)
                if med_count < 2:
                    return domain_kw
        return None

    def screen_stage1(self, paper: Dict) -> Tuple[str, str, str, str]:
        """
        Stage 1: Keyword-based screening.
        Returns: (decision, confidence, rationale, tier)
        decision: "include", "exclude", or "uncertain"
        tier: "tier1", "tier2", "tier3", or ""
        """
        title = paper.get("title", "") or ""
        abstract = paper.get("abstract", "") or ""
        combined = f"{title} {abstract}"
        combined_lower = combined.lower()

        # Check excluded document types
        for exc_type in self.EXCLUDE_TYPES:
            if exc_type in combined_lower:
                return ("exclude", "high", f"Document type: {exc_type}", "")

        # Check false positives
        if self._check_false_positive(combined_lower):
            return ("exclude", "medium", "Likely false positive (non-educational simulation context)", "")

        # Check excluded domains
        excl_domain = self._check_exclude_domain(combined_lower)
        if excl_domain:
            return ("exclude", "medium", f"Off-topic domain detected: {excl_domain}", "")

        # Count keyword matches using both plain and regex strategies
        llm_count = (self._count_plain_matches(combined_lower, self.LLM_KEYWORDS_PLAIN)
                     + self._count_regex_matches(combined, self._llm_regex))
        sim_count = (self._count_plain_matches(combined_lower, self.SIMULATION_KEYWORDS_PLAIN)
                     + self._count_regex_matches(combined, self._sim_regex))
        # NTS: plain + regex + contextual
        nts_count = (self._count_plain_matches(combined_lower, self.NTS_KEYWORDS_PLAIN)
                     + self._count_regex_matches(combined, self._nts_regex)
                     + self._count_contextual_nts(combined_lower))
        med_count = (self._count_plain_matches(combined_lower, self.MEDICAL_KEYWORDS_PLAIN)
                     + self._count_regex_matches(combined, self._med_regex))

        has_llm = llm_count >= 1
        has_sim = sim_count >= 1
        has_nts = nts_count >= 1
        has_med = med_count >= 1

        # No LLM keywords at all -> definite exclude
        if not has_llm:
            return ("exclude", "high", "No LLM/AI keywords found", "")

        # Determine tier
        tier = ""
        if has_llm and has_med:
            tier = "tier1"
        if has_llm and has_med and has_sim:
            tier = "tier2"
        if has_llm and has_med and has_sim and has_nts:
            tier = "tier3"

        # Strong include: all 4 categories with good depth
        total_strength = llm_count + sim_count + nts_count + med_count
        if has_llm and has_sim and has_nts and has_med:
            if total_strength >= self.auto_include_threshold:
                return ("include", "high",
                        f"All 4 categories present (LLM:{llm_count}, Sim:{sim_count}, "
                        f"NTS:{nts_count}, Med:{med_count})", tier)
            else:
                return ("include", "medium",
                        f"All 4 categories present but limited depth (total:{total_strength})",
                        tier)

        # LLM + Simulation + Medical (Tier 2) but no NTS
        if has_llm and has_sim and has_med and not has_nts:
            if total_strength >= 4:
                return ("include", "medium",
                        f"LLM+Simulation+Medical but no NTS keywords (Tier 2)", tier)
            else:
                return ("uncertain", "low",
                        "LLM+Sim+Med weak signal (total:{}) - needs AI review".format(
                            total_strength), tier)

        # LLM + Medical (Tier 1) but no simulation
        if has_llm and has_med and not has_sim:
            # Check for education/training context more strictly
            edu_signals = ["education", "training", "curriculum", "teaching",
                           "learning", "pedagogy", "competency", "assessment",
                           "faculty development", "continuing professional development"]
            has_edu = sum(1 for s in edu_signals if s in combined_lower)
            if has_edu >= 2:
                # Strong education context: uncertain, worth AI review
                return ("uncertain", "low",
                        f"LLM+Medical+Education (edu_signals:{has_edu}) "
                        f"but no simulation keywords - needs AI review", tier)
            elif has_edu == 1:
                # Weak education context: also uncertain but lower priority
                return ("uncertain", "low",
                        f"LLM+Medical+weak Education (1 signal) "
                        f"but no simulation keywords - needs AI review", tier)
            return ("exclude", "medium",
                    "LLM+Medical but no simulation or education context", "")

        # LLM + Simulation but no medical
        if has_llm and has_sim and not has_med:
            return ("uncertain", "low",
                    "LLM+Simulation but no medical context - needs AI review", "")

        # LLM only
        if has_llm and not has_sim and not has_med:
            return ("exclude", "high", "LLM only - no medical or simulation context", "")

        # Abstract too short for reliable screening
        if len(abstract) < 50:
            if has_llm and (has_sim or has_med):
                return ("uncertain", "low",
                        "Short/missing abstract - needs manual review", tier)
            return ("exclude", "low",
                    "Short abstract, insufficient evidence for inclusion", "")

        return ("uncertain", "low", "Ambiguous - needs AI review", tier)

    def screen_stage2_ai(self, papers: List[Dict]) -> List[Dict]:
        """
        Stage 2: AI-assisted screening for uncertain papers.
        Uses Claude API to assess relevance based on title and abstract.
        """
        if not self.ai_enabled:
            logger.info(
                "AI screening disabled. Applying conservative heuristic to %d "
                "uncertain papers instead of blanket include.", len(papers))
            for paper in papers:
                # Instead of blindly including all uncertain papers, apply a
                # conservative heuristic: only include if we have reasonable
                # evidence of relevance (at least 2 category matches).
                title = paper.get("title", "") or ""
                abstract = paper.get("abstract", "") or ""
                combined = f"{title} {abstract}"
                combined_lower = combined.lower()

                llm_c = (self._count_plain_matches(combined_lower, self.LLM_KEYWORDS_PLAIN)
                         + self._count_regex_matches(combined, self._llm_regex))
                sim_c = (self._count_plain_matches(combined_lower, self.SIMULATION_KEYWORDS_PLAIN)
                         + self._count_regex_matches(combined, self._sim_regex))
                nts_c = (self._count_plain_matches(combined_lower, self.NTS_KEYWORDS_PLAIN)
                         + self._count_regex_matches(combined, self._nts_regex)
                         + self._count_contextual_nts(combined_lower))
                med_c = (self._count_plain_matches(combined_lower, self.MEDICAL_KEYWORDS_PLAIN)
                         + self._count_regex_matches(combined, self._med_regex))

                categories_hit = sum([llm_c >= 1, sim_c >= 1, nts_c >= 1, med_c >= 1])
                total = llm_c + sim_c + nts_c + med_c

                if categories_hit >= 3 or (categories_hit >= 2 and total >= 6):
                    paper["screening_decision"] = "include"
                    paper["screening_confidence"] = "low"
                    paper["screening_rationale"] = (
                        f"AI disabled - heuristic include ({categories_hit} categories, "
                        f"total:{total})")
                    paper["screening_stage"] = "stage1_heuristic_include"
                else:
                    paper["screening_decision"] = "exclude"
                    paper["screening_confidence"] = "low"
                    paper["screening_rationale"] = (
                        f"AI disabled - heuristic exclude ({categories_hit} categories, "
                        f"total:{total}, insufficient evidence)")
                    paper["screening_stage"] = "stage1_heuristic_exclude"
            return papers

        try:
            import anthropic
            client = anthropic.Anthropic()
        except (ImportError, Exception) as e:
            logger.error(f"Cannot initialize Claude API: {e}. Falling back to include-all.")
            for paper in papers:
                paper["screening_decision"] = "include"
                paper["screening_confidence"] = "low"
                paper["screening_rationale"] = (
                    f"AI screening unavailable ({e}) - included for manual review")
                paper["screening_stage"] = "stage2_fallback"
            return papers

        logger.info(f"Stage 2: AI screening {len(papers)} uncertain papers...")

        batch_size = self.config.get("processing", {}).get("screening", {}).get(
            "ai_batch_size", 10)

        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]

            # Build prompt with batch of papers
            papers_text = ""
            for j, paper in enumerate(batch):
                title = paper.get("title", "No title")[:200]
                abstract = (paper.get("abstract", "") or "")[:500]
                papers_text += (
                    f"\n--- Paper {j+1} ---\n"
                    f"Title: {title}\nAbstract: {abstract}\n")

            prompt = f"""You are screening papers for a bibliometric analysis about Large Language Models (LLMs) in healthcare simulation training, particularly for non-technical skills (NTS).

INCLUSION CRITERIA (paper must address ALL of these):
A) LLM/Generative AI component (ChatGPT, GPT, Claude, etc.) - must be primary focus or significant component
B) Simulation/training context (not purely clinical AI) - includes virtual patients, scenario-based training, debriefing, OSCE
C) Healthcare/medical context
D) Ideally addresses non-technical skills (communication, teamwork, leadership, decision-making, situational awareness)

EXCLUSION CRITERIA (exclude if ANY apply):
- Pure clinical AI (diagnosis, treatment) without education/training context
- Only technical/procedural skills without NTS component
- Non-healthcare simulation (aviation, business, engineering, etc.)
- Traditional ML only (no generative AI/LLM)
- Editorial, commentary, letter without original data
- LLM used only for exam question generation or MCQ writing (no simulation)
- LLM performance benchmarking on exams without educational intervention

TIER CLASSIFICATION:
- Tier 1: LLM + Medical (broadest - any LLM application in medical context)
- Tier 2: LLM + Medical + Simulation (adds simulation/training element)
- Tier 3: LLM + Medical + Simulation + NTS (most focused - includes non-technical skills)

For each paper, respond in this exact JSON format:
{{"papers": [
  {{"paper_num": 1, "decision": "include|exclude", "confidence": "high|medium|low", "tier": "tier1|tier2|tier3|none", "rationale": "1-2 sentence justification"}},
  ...
]}}

Here are the papers to screen:
{papers_text}"""

            try:
                response = client.messages.create(
                    model=self.ai_model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text

                # Parse JSON response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    for item in result.get("papers", []):
                        idx = item.get("paper_num", 1) - 1
                        if 0 <= idx < len(batch):
                            batch[idx]["screening_decision"] = item.get(
                                "decision", "include")
                            batch[idx]["screening_confidence"] = item.get(
                                "confidence", "low")
                            batch[idx]["screening_tier"] = item.get("tier", "")
                            batch[idx]["screening_rationale"] = item.get(
                                "rationale", "AI screened")
                            batch[idx]["screening_stage"] = "stage2_ai"

                            if item.get("decision") == "include":
                                self.stats["stage2_include"] += 1
                            else:
                                self.stats["stage2_exclude"] += 1

                logger.info(
                    f"AI screened batch {i//batch_size + 1}: {len(batch)} papers")

            except Exception as e:
                logger.error(f"AI screening error: {e}")
                for paper in batch:
                    paper["screening_decision"] = "include"
                    paper["screening_confidence"] = "low"
                    paper["screening_rationale"] = (
                        f"AI error: {e} - included for safety")
                    paper["screening_stage"] = "stage2_error"

            time.sleep(self.ai_rate_limit)

        return papers

    def screen_all(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Screen all records through both stages.
        Returns dict with keys: "included", "excluded", "all_screened"
        """
        self.stats["total"] = len(records)
        logger.info(f"Starting screening of {len(records)} records")

        included = []
        excluded = []
        uncertain = []

        # Stage 1: Keyword pre-filter
        for record in records:
            decision, confidence, rationale, tier = self.screen_stage1(record)
            record["screening_decision"] = decision
            record["screening_confidence"] = confidence
            record["screening_rationale"] = rationale
            record["screening_tier"] = tier
            record["screening_stage"] = "stage1"

            if decision == "include":
                self.stats["stage1_include"] += 1
                included.append(record)
            elif decision == "exclude":
                self.stats["stage1_exclude"] += 1
                excluded.append(record)
            else:
                self.stats["stage1_uncertain"] += 1
                uncertain.append(record)

        logger.info(
            f"Stage 1 results: {self.stats['stage1_include']} included, "
            f"{self.stats['stage1_exclude']} excluded, "
            f"{self.stats['stage1_uncertain']} uncertain"
        )

        # Stage 2: AI screening for uncertain papers
        if uncertain:
            screened_uncertain = self.screen_stage2_ai(uncertain)
            for paper in screened_uncertain:
                if paper.get("screening_decision") == "include":
                    included.append(paper)
                else:
                    excluded.append(paper)

        # Assign tier counts
        for paper in included:
            tier = paper.get("screening_tier", "")
            if tier == "tier3":
                self.stats["tier3_count"] += 1
            elif tier == "tier2":
                self.stats["tier2_count"] += 1
            elif tier == "tier1":
                self.stats["tier1_count"] += 1

        all_screened = included + excluded

        logger.info(
            f"Screening complete: {len(included)} included, {len(excluded)} excluded. "
            f"Tiers: T1={self.stats['tier1_count']}, T2={self.stats['tier2_count']}, "
            f"T3={self.stats['tier3_count']}"
        )

        return {
            "included": included,
            "excluded": excluded,
            "all_screened": all_screened,
        }

    def save(self, results: Dict[str, List[Dict]], prefix: str = "screened") -> Dict[str, Path]:
        """Save screening results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        paths = {}

        for key in ["included", "excluded", "all_screened"]:
            records = results[key]
            json_path = self.output_dir / f"{prefix}_{key}_{timestamp}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            paths[key] = json_path
            logger.info(f"Saved {len(records)} {key} papers to {json_path}")

        # Summary report
        report_path = self.output_dir / f"{prefix}_report_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write("# Screening Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Statistics\n\n")
            f.write("| Metric | Count |\n|--------|-------|\n")
            for key, val in self.stats.items():
                f.write(f"| {key} | {val} |\n")
            f.write(f"\n## Tier Distribution (Included Papers)\n\n")
            f.write(f"- Tier 1 (LLM + Medical): {self.stats['tier1_count']}\n")
            f.write(f"- Tier 2 (+ Simulation): {self.stats['tier2_count']}\n")
            f.write(f"- Tier 3 (+ NTS): {self.stats['tier3_count']}\n")

        return paths


def main():
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python screener.py <deduplicated_records.json>")
        return

    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    screener = PaperScreener()
    results = screener.screen_all(records)
    screener.save(results)


if __name__ == "__main__":
    main()
