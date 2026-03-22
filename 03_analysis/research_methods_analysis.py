#!/usr/bin/env python3
"""
Research Methods Classification
Classifies papers by study design/methodology from title and abstract.
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

logger = logging.getLogger(__name__)

# Research method patterns (ordered by specificity - check specific first)
METHOD_PATTERNS = {
    "Randomised Controlled Trial": [
        r"\brandomis?ed controlled trial\b", r"\bRCT\b", r"\brandom\w* assign\w*\b",
        r"\brandomis?ed\b.*\bcontrol\b.*\btrial\b",
    ],
    "Quasi-experimental": [
        r"\bquasi.?experiment\w*\b", r"\bpre.?post\b", r"\bbefore.?after\b",
        r"\bnon.?randomis?ed\b.*\btrial\b", r"\bcontrolled study\b",
    ],
    "Mixed Methods": [
        r"\bmixed.?method\w*\b", r"\bqualitative and quantitative\b",
        r"\bquantitative and qualitative\b",
    ],
    "Qualitative": [
        r"\bqualitative\b", r"\bthematic analysis\b", r"\bgrounded theory\b",
        r"\bphenomenolog\w*\b", r"\bfocus group\b", r"\bethnograph\w*\b",
    ],
    "Cross-sectional Survey": [
        r"\bcross.?sectional\b", r"\bsurvey\b", r"\bquestionnaire\b",
    ],
    "Systematic Review": [
        r"\bsystematic review\b", r"\bmeta.?analysis\b", r"\bPRISMA\b",
    ],
    "Scoping Review": [
        r"\bscoping review\b", r"\bscoping study\b",
    ],
    "Narrative Review": [
        r"\bnarrative review\b", r"\bliterature review\b", r"\boverview\b.*\bliterature\b",
    ],
    "Development Study": [
        r"\bdevelop\w*\b.*\b(system|platform|tool|framework|prototype)\b",
        r"\bdesign\b.*\b(system|platform|tool)\b", r"\bprototype\b",
    ],
    "Feasibility Study": [
        r"\bfeasibility\b", r"\bpilot study\b", r"\bpilot\b.*\btrial\b",
        r"\bproof.?of.?concept\b",
    ],
    "Validation Study": [
        r"\bvalidat\w+\b", r"\breliability\b.*\bvalidity\b",
        r"\bpsychometric\b",
    ],
    "Case Study": [
        r"\bcase study\b", r"\bcase report\b", r"\bcase series\b",
    ],
    "Observational": [
        r"\bobservational\b", r"\bcohort\b", r"\bprospective\b", r"\bretrospective\b",
    ],
    "Comparative Study": [
        r"\bcompar\w+\b.*\b(study|analysis|evaluation)\b",
        r"\bhead.?to.?head\b", r"\bbenchmark\w*\b",
    ],
}

# Evidence hierarchy (higher = stronger evidence)
EVIDENCE_LEVELS = {
    "Randomised Controlled Trial": 1,
    "Systematic Review": 1,
    "Quasi-experimental": 2,
    "Observational": 3,
    "Mixed Methods": 3,
    "Cross-sectional Survey": 3,
    "Comparative Study": 3,
    "Validation Study": 3,
    "Qualitative": 4,
    "Feasibility Study": 4,
    "Development Study": 5,
    "Case Study": 5,
    "Scoping Review": 5,
    "Narrative Review": 6,
}


def classify_method(paper: Dict) -> List[str]:
    """Classify a paper's research method(s)."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    methods = []
    for method, patterns in METHOD_PATTERNS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            methods.append(method)
    return methods if methods else ["Unclassified"]


def analyze_research_methods(papers: List[Dict], output_dir: str = None) -> Dict:
    """Classify and visualize research methods."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    method_counts = Counter()
    evidence_dist = Counter()
    method_by_year = {}
    papers_classified = 0

    for paper in papers:
        methods = classify_method(paper)
        if methods != ["Unclassified"]:
            papers_classified += 1
        for m in methods:
            method_counts[m] += 1
            level = EVIDENCE_LEVELS.get(m, 7)
            evidence_dist[f"Level {level}"] += 1
            year = paper.get("year")
            if year:
                key = (m, year)
                method_by_year[key] = method_by_year.get(key, 0) + 1

    # Bar chart
    methods_sorted = method_counts.most_common()
    if methods_sorted:
        labels = [m for m, _ in methods_sorted if m != "Unclassified"]
        values = [c for m, c in methods_sorted if m != "Unclassified"]

        fig, ax = plt.subplots(figsize=(10, 7))
        colors = plt.cm.viridis([i / len(labels) for i in range(len(labels))])
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Number of Papers", fontsize=11)
        ax.set_title("Research Methods Distribution", fontsize=13, fontweight="bold")
        ax.invert_yaxis()
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=9, fontweight="bold")
        plt.tight_layout()
        plt.savefig(fig_dir / "research_methods.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Table
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_path = table_dir / f"research_methods_{timestamp}.md"
    with open(table_path, "w") as f:
        f.write("# Research Methods Classification\n\n")
        f.write(f"Papers classified: {papers_classified}/{len(papers)} ({papers_classified/len(papers)*100:.1f}%)\n\n")
        f.write("| Method | Count | % | Evidence Level |\n")
        f.write("|--------|-------|---|----------------|\n")
        for method, count in methods_sorted:
            pct = count / len(papers) * 100
            level = EVIDENCE_LEVELS.get(method, 7)
            f.write(f"| {method} | {count} | {pct:.1f}% | {level} |\n")

    results = {
        "classified": papers_classified,
        "total": len(papers),
        "methods": dict(method_counts),
    }
    logger.info(f"Research methods: {papers_classified}/{len(papers)} classified")
    return results


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    if len(sys.argv) < 2:
        print("Usage: python research_methods_analysis.py <analysis_dataset.json>")
        return
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)
    results = analyze_research_methods(papers)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
