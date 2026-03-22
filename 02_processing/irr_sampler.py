#!/usr/bin/env python3
"""
Inter-Rater Reliability Sample Generator
=========================================
Generates stratified random samples for human validation of AI screening decisions.
- 100 papers per reviewer (Matt + 2 colleagues)
- 50-paper overlap between all reviewers for IRR computation
- Exports as CSV for easy review
"""

import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_irr_samples(
    screened_file: str,
    output_dir: str = None,
    sample_per_reviewer: int = 100,
    overlap: int = 50,
    seed: int = 42,
):
    """
    Generate stratified IRR samples from screened papers.

    Stratification: 50% included, 50% excluded (to test both directions)
    Within each: proportional by confidence level (high/medium/low)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "irr_samples"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load screened data
    with open(screened_file, "r", encoding="utf-8") as f:
        all_papers = json.load(f)

    logger.info(f"Loaded {len(all_papers)} screened papers")

    # Split by decision
    included = [p for p in all_papers if p.get("screening_decision") == "include"]
    excluded = [p for p in all_papers if p.get("screening_decision") == "exclude"]

    logger.info(f"Included: {len(included)}, Excluded: {len(excluded)}")

    random.seed(seed)

    # Stratified sampling: 50% included, 50% excluded
    half = sample_per_reviewer // 2

    # Sample included papers (stratified by confidence)
    included_sample = _stratified_sample(included, half)
    excluded_sample = _stratified_sample(excluded, half)

    # Common overlap pool (papers all reviewers see)
    overlap_included = included_sample[:overlap // 2]
    overlap_excluded = excluded_sample[:overlap // 2]
    common_pool = overlap_included + overlap_excluded

    # Reviewer-specific papers (different for each)
    remaining_included = included_sample[overlap // 2:]
    remaining_excluded = excluded_sample[overlap // 2:]
    remaining_pool = remaining_included + remaining_excluded
    random.shuffle(remaining_pool)

    unique_per_reviewer = sample_per_reviewer - overlap
    n_reviewers = 3  # Matt + 2 colleagues

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reviewer_names = ["matt", "colleague_1", "colleague_2"]

    for i, name in enumerate(reviewer_names):
        # Each reviewer gets: common pool + their unique slice
        start = i * unique_per_reviewer
        end = start + unique_per_reviewer
        unique_papers = remaining_pool[start:end] if end <= len(remaining_pool) else remaining_pool[start:]

        reviewer_sample = common_pool + unique_papers
        random.shuffle(reviewer_sample)

        # Export CSV
        csv_path = output_dir / f"irr_sample_{name}_{timestamp}.csv"
        _export_csv(reviewer_sample, csv_path, include_ai_decision=(name == "matt"))

        logger.info(f"Reviewer '{name}': {len(reviewer_sample)} papers -> {csv_path}")

    # Export common pool separately
    common_path = output_dir / f"irr_common_pool_{timestamp}.csv"
    _export_csv(common_pool, common_path, include_ai_decision=True)
    logger.info(f"Common pool: {len(common_pool)} papers -> {common_path}")

    # Summary
    summary_path = output_dir / f"irr_sampling_summary_{timestamp}.md"
    with open(summary_path, "w") as f:
        f.write("# Inter-Rater Reliability Sampling Summary\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total screened papers:** {len(all_papers)}\n")
        f.write(f"**Included:** {len(included)}\n")
        f.write(f"**Excluded:** {len(excluded)}\n\n")
        f.write(f"## Sample Design\n\n")
        f.write(f"- Papers per reviewer: {sample_per_reviewer}\n")
        f.write(f"- Common overlap: {overlap} papers (for IRR computation)\n")
        f.write(f"- Stratification: 50% included / 50% excluded\n")
        f.write(f"- Reviewers: {', '.join(reviewer_names)}\n\n")
        f.write(f"## Instructions for Reviewers\n\n")
        f.write("For each paper, please review the title and abstract and indicate:\n")
        f.write("1. **Your decision**: Include or Exclude\n")
        f.write("2. **Your confidence**: High, Medium, or Low\n")
        f.write("3. **Brief rationale** (1 sentence)\n\n")
        f.write("### Inclusion Criteria\n")
        f.write("Include if the paper addresses ALL of:\n")
        f.write("- A) LLM/Generative AI component\n")
        f.write("- B) Simulation/training context (not clinical AI)\n")
        f.write("- C) Healthcare/medical context\n")
        f.write("- D) Ideally non-technical skills (communication, teamwork, etc.)\n\n")
        f.write("### Exclusion Criteria\n")
        f.write("Exclude if ANY of: pure clinical AI, technical skills only, non-healthcare, traditional ML only, editorial/commentary\n")

    return {
        "total_screened": len(all_papers),
        "sample_per_reviewer": sample_per_reviewer,
        "overlap": overlap,
        "output_dir": str(output_dir),
    }


def _stratified_sample(papers: List[Dict], n: int) -> List[Dict]:
    """Stratified sample by confidence level."""
    by_conf = {"high": [], "medium": [], "low": []}
    for p in papers:
        conf = p.get("screening_confidence", "low").lower()
        by_conf.get(conf, by_conf["low"]).append(p)

    # Proportional allocation
    total = len(papers)
    sample = []
    for conf, pool in by_conf.items():
        if total > 0:
            k = max(1, int(n * len(pool) / total))
            k = min(k, len(pool))
            sample.extend(random.sample(pool, k))

    # Top up if needed
    remaining = [p for p in papers if p not in sample]
    while len(sample) < n and remaining:
        sample.append(remaining.pop(random.randint(0, len(remaining) - 1)))

    return sample[:n]


def _export_csv(papers: List[Dict], path: Path, include_ai_decision: bool = False):
    """Export papers to CSV for reviewer."""
    fieldnames = ["paper_id", "title", "year", "journal", "abstract"]
    if include_ai_decision:
        fieldnames.extend(["ai_decision", "ai_confidence", "ai_rationale"])
    fieldnames.extend(["your_decision", "your_confidence", "your_rationale"])

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, p in enumerate(papers):
            row = {
                "paper_id": p.get("id", p.get("doi", f"paper_{i}")),
                "title": (p.get("title", "") or "")[:300],
                "year": p.get("year", ""),
                "journal": (p.get("journal", "") or "")[:100],
                "abstract": (p.get("abstract", "") or "")[:500],
                "your_decision": "",
                "your_confidence": "",
                "your_rationale": "",
            }
            if include_ai_decision:
                row["ai_decision"] = p.get("screening_decision", "")
                row["ai_confidence"] = p.get("screening_confidence", "")
                row["ai_rationale"] = p.get("screening_rationale", "")
            writer.writerow(row)


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python irr_sampler.py <screened_all.json>")
        return

    results = generate_irr_samples(sys.argv[1])
    print(f"\nIRR samples generated: {results}")


if __name__ == "__main__":
    main()
