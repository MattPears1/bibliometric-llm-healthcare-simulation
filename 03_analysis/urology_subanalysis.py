#!/usr/bin/env python3
"""
Urology Sub-Analysis
=====================
Dedicated analysis of urology-related papers within the bibliometric dataset.
Covers: publication trends, LLM models, simulation types, NTS focus,
boot camp landscape, and future vision for LLM-enhanced mannequin training.
"""

import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# Urology-related terms
UROLOGY_TERMS = [
    r"\burology\b", r"\burological\b", r"\burologist\b",
    r"\bkidney\b", r"\brenal\b", r"\bnephro\w+\b",
    r"\bprostate\b", r"\bprostatic\b", r"\bBPH\b",
    r"\bbladder\b", r"\bcystoscop\w+\b",
    r"\bendourology\b", r"\buretero\w+\b", r"\bureter\b",
    r"\bBAUS\b", r"\bAUA\b", r"\bEAU\b",
    r"\brobotic surgery\b", r"\bda Vinci\b",
    r"\bTURP\b", r"\bnephrectom\w+\b",
    r"\bpenile\b", r"\btesticular\b", r"\bscrotal\b",
    r"\burinary\b", r"\bincontinence\b",
]

# Simulation boot camp terms
BOOTCAMP_TERMS = [
    r"\bboot\s*camp\b", r"\bbootcamp\b",
    r"\bimmersion\s+course\b", r"\bintensive\s+training\b",
    r"\bskills\s+lab\b", r"\bsurgical\s+skills\s+course\b",
]


def is_urology_paper(paper: Dict) -> bool:
    """Check if paper is urology-related."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    return any(re.search(term, text, re.IGNORECASE) for term in UROLOGY_TERMS)


def is_bootcamp_paper(paper: Dict) -> bool:
    """Check if paper mentions boot camps."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    return any(re.search(term, text, re.IGNORECASE) for term in BOOTCAMP_TERMS)


def analyze_urology(papers: List[Dict], output_dir: str = None) -> Dict:
    """Run urology sub-analysis."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # Filter urology papers
    uro_papers = [p for p in papers if is_urology_paper(p)]
    bootcamp_papers = [p for p in papers if is_bootcamp_paper(p)]
    uro_bootcamp = [p for p in uro_papers if is_bootcamp_paper(p)]

    logger.info(f"Urology papers: {len(uro_papers)} / {len(papers)} ({len(uro_papers)/len(papers)*100:.1f}%)")
    logger.info(f"Boot camp papers: {len(bootcamp_papers)}")
    logger.info(f"Urology + boot camp: {len(uro_bootcamp)}")

    results = {
        "total_papers": len(papers),
        "urology_papers": len(uro_papers),
        "urology_percentage": round(len(uro_papers) / len(papers) * 100, 1) if papers else 0,
        "bootcamp_papers": len(bootcamp_papers),
        "urology_bootcamp_papers": len(uro_bootcamp),
    }

    if not uro_papers:
        logger.warning("No urology papers found in dataset")
        # Save empty report
        report_path = table_dir / f"urology_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w") as f:
            f.write("# Urology Sub-Analysis\n\n")
            f.write(f"No urology-related papers found in the dataset of {len(papers)} papers.\n")
            f.write("This finding itself is notable and should be discussed.\n")
        return results

    # Year distribution
    year_counts = Counter(p.get("year") for p in uro_papers if p.get("year"))

    # NTS domains in urology papers
    nts_patterns = {
        "Communication": [r"\bcommunicat\w+\b", r"\bempathy\b", r"\bcounsell?ing\b"],
        "Decision-making": [r"\bdecision.?making\b", r"\bclinical reasoning\b"],
        "Teamwork": [r"\bteamwork\b", r"\binterprofessional\b", r"\bcollaborat\w+\b"],
        "Leadership": [r"\bleadership\b", r"\bsupervis\w+\b"],
        "Situational awareness": [r"\bsituation\w*\s*awareness\b"],
    }

    nts_counts = Counter()
    for paper in uro_papers:
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        for domain, patterns in nts_patterns.items():
            if any(re.search(p, text) for p in patterns):
                nts_counts[domain] += 1

    # LLM models in urology
    llm_patterns = {
        "ChatGPT": r"\bChatGPT\b",
        "GPT-4": r"\bGPT-?4\b",
        "Claude": r"\bClaude\b",
        "Gemini": r"\bGemini\b",
        "Generic LLM": r"\blarge language model\b|\bLLM\b",
    }

    llm_counts = Counter()
    for paper in uro_papers:
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        for model, pattern in llm_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                llm_counts[model] += 1

    # Citation analysis for urology papers
    citations = [p.get("citation_count", 0) or 0 for p in uro_papers]
    results.update({
        "year_distribution": dict(year_counts),
        "nts_domains": dict(nts_counts),
        "llm_models": dict(llm_counts),
        "mean_citations": round(np.mean(citations), 1) if citations else 0,
        "total_citations": sum(citations),
    })

    # --- Figure: Urology publication trends ---
    if year_counts:
        years = sorted(year_counts.keys())
        counts = [year_counts[y] for y in years]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(years, counts, color="#9C27B0", edgecolor="white")
        for y, c in zip(years, counts):
            ax.text(y, c + 0.3, str(c), ha="center", fontweight="bold", fontsize=10)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Papers", fontsize=12)
        ax.set_title("Urology-Related LLM Simulation Papers by Year", fontsize=13, fontweight="bold")
        ax.set_xticks(years)
        plt.tight_layout()
        plt.savefig(fig_dir / "urology_trends.png", dpi=300, bbox_inches="tight")
        plt.close()

    # --- Report ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = table_dir / f"urology_results_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write("# Urology Sub-Analysis\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Overview\n\n")
        f.write(f"- Total papers in dataset: {len(papers)}\n")
        f.write(f"- Urology-related papers: {len(uro_papers)} ({results['urology_percentage']}%)\n")
        f.write(f"- Boot camp papers (all specialties): {len(bootcamp_papers)}\n")
        f.write(f"- Urology + boot camp papers: {len(uro_bootcamp)}\n\n")

        f.write(f"## Year Distribution\n\n")
        f.write("| Year | Count |\n|------|-------|\n")
        for y in sorted(year_counts.keys()):
            f.write(f"| {y} | {year_counts[y]} |\n")

        f.write(f"\n## NTS Domains in Urology Papers\n\n")
        f.write("| Domain | Count | % of Urology Papers |\n|--------|-------|--------------------|\n")
        for domain, count in nts_counts.most_common():
            f.write(f"| {domain} | {count} | {count/len(uro_papers)*100:.1f}% |\n")

        f.write(f"\n## LLM Models in Urology Papers\n\n")
        f.write("| Model | Count |\n|-------|-------|\n")
        for model, count in llm_counts.most_common():
            f.write(f"| {model} | {count} |\n")

        f.write(f"\n## Citation Metrics\n\n")
        f.write(f"- Mean citations: {results['mean_citations']}\n")
        f.write(f"- Total citations: {results['total_citations']}\n")

        f.write(f"\n## Key Finding: The Boot Camp Opportunity\n\n")
        f.write("The intersection of LLMs, urology, and simulation boot camps represents\n")
        f.write("a significant research gap. Current boot camps rely on human standardized\n")
        f.write("patients or mannequins with human operators speaking through speakers.\n")
        f.write("LLM-powered text-to-speech could replace the human operator, enabling:\n")
        f.write("- Scalable, location-independent training\n")
        f.write("- Consistent patient responses across sessions\n")
        f.write("- 24/7 availability without human scheduling constraints\n")
        f.write("- Multilingual support\n")
        f.write("- Automated assessment and feedback\n")

    logger.info(f"Urology report saved to {report_path}")
    return results


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python urology_subanalysis.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = analyze_urology(papers)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
