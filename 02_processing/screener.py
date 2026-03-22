#!/usr/bin/env python3
"""
Two-stage paper screener for bibliometric analysis.
Stage 1: Fast keyword-based pre-filter (immediate include/exclude for clear cases)
Stage 2: AI-assisted context screening via Claude API (for uncertain cases)

Implements three-tier scope:
  Tier 1: LLM + Medical (broadest)
  Tier 2: LLM + Medical + Simulation
  Tier 3: LLM + Medical + Simulation + NTS (most focused)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class PaperScreener:
    """Two-stage paper screening with keyword pre-filter and AI context screening."""

    # Keyword lists for Stage 1
    LLM_KEYWORDS = [
        "large language model", "llm", "chatgpt", "gpt-4", "gpt-3", "gpt-5",
        "gpt-4o", "claude", "gemini", "generative ai", "generative artificial intelligence",
        "natural language processing", "nlp", "transformer", "foundation model",
        "ai chatbot", "conversational ai", "biogpt", "med-palm", "medgpt",
        "artificial intelligence", "llama", "mistral",
    ]

    SIMULATION_KEYWORDS = [
        "simulation", "simulator", "simulated patient", "standardized patient",
        "standardised patient", "virtual patient", "high-fidelity", "low-fidelity",
        "scenario", "debriefing", "mannequin", "virtual reality", "vr",
        "mixed reality", "augmented reality", "immersive", "sim-based",
        "simulation-based", "training scenario", "osce",
        "objective structured clinical examination", "roleplay", "role-play",
    ]

    NTS_KEYWORDS = [
        "non-technical skills", "non technical skills", "nontechnical skills", "nts",
        "teamwork", "communication", "leadership", "decision making", "decision-making",
        "situational awareness", "situation awareness", "human factors",
        "crm", "crisis resource management", "crew resource management",
        "notss", "ants", "notechs", "soft skills", "interprofessional",
        "collaboration", "closed-loop communication", "cognitive load",
        "stress management", "team training", "team performance",
        "empathy", "clinical reasoning", "shared mental model",
    ]

    MEDICAL_KEYWORDS = [
        "healthcare", "health care", "medical", "clinical", "surgical",
        "surgery", "nursing", "hospital", "patient", "physician", "doctor",
        "resident", "trainee", "medical education", "surgical education",
        "emergency", "anesthesia", "anaesthesia", "intensive care",
        "critical care", "nursing education", "clinical training",
    ]

    EXCLUDE_TYPES = [
        "editorial", "letter to the editor", "commentary", "book review",
        "erratum", "correction", "retracted", "protocol only",
    ]

    # False positive indicators - these often match keywords but aren't relevant
    FALSE_POSITIVE_INDICATORS = [
        "cancer treatment outcome", "drug simulation", "monte carlo simulation",
        "computational fluid dynamics", "molecular simulation",
        "pharmacokinetic simulation", "weather simulation",
        "financial simulation", "traffic simulation",
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

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """Count keyword matches in text."""
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower)

    def _check_false_positive(self, text: str) -> bool:
        """Check if the paper is likely a false positive."""
        text_lower = text.lower()
        return any(fp in text_lower for fp in self.FALSE_POSITIVE_INDICATORS)

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

        # Check excluded document types
        for exc_type in self.EXCLUDE_TYPES:
            if exc_type in combined.lower():
                return ("exclude", "high", f"Document type: {exc_type}", "")

        # Check false positives
        if self._check_false_positive(combined):
            return ("exclude", "medium", "Likely false positive (non-educational simulation context)", "")

        # Count keyword matches
        llm_count = self._count_matches(combined, self.LLM_KEYWORDS)
        sim_count = self._count_matches(combined, self.SIMULATION_KEYWORDS)
        nts_count = self._count_matches(combined, self.NTS_KEYWORDS)
        med_count = self._count_matches(combined, self.MEDICAL_KEYWORDS)

        has_llm = llm_count >= 1
        has_sim = sim_count >= 1
        has_nts = nts_count >= 1
        has_med = med_count >= 1

        # No LLM keywords at all → definite exclude
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
                return ("include", "high", f"All 4 categories present (LLM:{llm_count}, Sim:{sim_count}, NTS:{nts_count}, Med:{med_count})", tier)
            else:
                return ("include", "medium", f"All 4 categories present but limited depth (total:{total_strength})", tier)

        # LLM + Simulation + Medical (Tier 2) but no NTS
        if has_llm and has_sim and has_med and not has_nts:
            return ("include", "medium", f"LLM+Simulation+Medical but no NTS keywords (Tier 2)", tier)

        # LLM + Medical (Tier 1) but no simulation
        if has_llm and has_med and not has_sim:
            if "education" in combined.lower() or "training" in combined.lower():
                return ("uncertain", "low", "LLM+Medical+Education but no simulation keywords - needs AI review", tier)
            return ("exclude", "medium", "LLM+Medical but no simulation or education context", "")

        # LLM + Simulation but no medical
        if has_llm and has_sim and not has_med:
            return ("uncertain", "low", "LLM+Simulation but no medical context - needs AI review", "")

        # LLM only
        if has_llm and not has_sim and not has_med:
            return ("exclude", "high", "LLM only - no medical or simulation context", "")

        # Abstract too short for reliable screening
        if len(abstract) < 50:
            if has_llm and (has_sim or has_med):
                return ("uncertain", "low", "Short/missing abstract - needs manual review", tier)
            return ("exclude", "low", "Short abstract, insufficient evidence for inclusion", "")

        return ("uncertain", "low", "Ambiguous - needs AI review", tier)

    def screen_stage2_ai(self, papers: List[Dict]) -> List[Dict]:
        """
        Stage 2: AI-assisted screening for uncertain papers.
        Uses Claude API to assess relevance based on title and abstract.
        """
        if not self.ai_enabled:
            logger.info("AI screening disabled. Marking uncertain papers as 'include' with low confidence.")
            for paper in papers:
                paper["screening_decision"] = "include"
                paper["screening_confidence"] = "low"
                paper["screening_rationale"] = "AI screening disabled - included for manual review"
                paper["screening_stage"] = "stage1_passthrough"
            return papers

        try:
            import anthropic
            client = anthropic.Anthropic()
        except (ImportError, Exception) as e:
            logger.error(f"Cannot initialize Claude API: {e}. Falling back to include-all.")
            for paper in papers:
                paper["screening_decision"] = "include"
                paper["screening_confidence"] = "low"
                paper["screening_rationale"] = f"AI screening unavailable ({e}) - included for manual review"
                paper["screening_stage"] = "stage2_fallback"
            return papers

        logger.info(f"Stage 2: AI screening {len(papers)} uncertain papers...")

        batch_size = self.config.get("processing", {}).get("screening", {}).get("ai_batch_size", 10)

        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]

            # Build prompt with batch of papers
            papers_text = ""
            for j, paper in enumerate(batch):
                title = paper.get("title", "No title")[:200]
                abstract = (paper.get("abstract", "") or "")[:500]
                papers_text += f"\n--- Paper {j+1} ---\nTitle: {title}\nAbstract: {abstract}\n"

            prompt = f"""You are screening papers for a bibliometric analysis about Large Language Models (LLMs) in healthcare simulation training, particularly for non-technical skills (NTS).

INCLUSION CRITERIA (paper must address ALL of these):
A) LLM/Generative AI component (ChatGPT, GPT, Claude, etc.) - must be primary focus or significant component
B) Simulation/training context (not purely clinical AI) - includes virtual patients, scenario-based training, debriefing, OSCE
C) Healthcare/medical context
D) Ideally addresses non-technical skills (communication, teamwork, leadership, decision-making, situational awareness)

EXCLUSION CRITERIA (exclude if ANY apply):
- Pure clinical AI (diagnosis, treatment) without education/training context
- Only technical/procedural skills without NTS component
- Non-healthcare simulation (aviation, business, etc.)
- Traditional ML only (no generative AI/LLM)
- Editorial, commentary, letter without original data

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
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    for item in result.get("papers", []):
                        idx = item.get("paper_num", 1) - 1
                        if 0 <= idx < len(batch):
                            batch[idx]["screening_decision"] = item.get("decision", "include")
                            batch[idx]["screening_confidence"] = item.get("confidence", "low")
                            batch[idx]["screening_tier"] = item.get("tier", "")
                            batch[idx]["screening_rationale"] = item.get("rationale", "AI screened")
                            batch[idx]["screening_stage"] = "stage2_ai"

                            if item.get("decision") == "include":
                                self.stats["stage2_include"] += 1
                            else:
                                self.stats["stage2_exclude"] += 1

                logger.info(f"AI screened batch {i//batch_size + 1}: {len(batch)} papers")

            except Exception as e:
                logger.error(f"AI screening error: {e}")
                for paper in batch:
                    paper["screening_decision"] = "include"
                    paper["screening_confidence"] = "low"
                    paper["screening_rationale"] = f"AI error: {e} - included for safety"
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
            f"Tiers: T1={self.stats['tier1_count']}, T2={self.stats['tier2_count']}, T3={self.stats['tier3_count']}"
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
