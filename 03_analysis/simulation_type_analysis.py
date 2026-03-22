#!/usr/bin/env python3
"""
Simulation Type Analysis
- Classify simulation types from title + abstract
- Horizontal bar chart of frequencies
- Cross-tab with NTS domains
"""

import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simulation type definitions: type_name -> list of compiled regex patterns
# ---------------------------------------------------------------------------
SIM_TYPES: Dict[str, List[re.Pattern]] = {
    "Virtual Patient / Chatbot": [
        re.compile(r"\bvirtual patient\b", re.IGNORECASE),
        re.compile(r"\bchatbot\b", re.IGNORECASE),
        re.compile(r"\bconversational agent\b", re.IGNORECASE),
    ],
    "Standardized Patient": [
        re.compile(r"\bstandardized patient\b", re.IGNORECASE),
        re.compile(r"\bstandardised patient\b", re.IGNORECASE),
        re.compile(r"\bsimulated patient\b", re.IGNORECASE),
        re.compile(r"\bSP\b"),
    ],
    "VR / MR / XR": [
        re.compile(r"\bvirtual reality\b", re.IGNORECASE),
        re.compile(r"\bVR\b"),
        re.compile(r"\bmixed reality\b", re.IGNORECASE),
        re.compile(r"\bXR\b"),
        re.compile(r"\baugmented reality\b", re.IGNORECASE),
        re.compile(r"\bAR\b"),
        re.compile(r"\bimmersive\b", re.IGNORECASE),
    ],
    "OSCE": [
        re.compile(r"\bOSCE\b"),
        re.compile(r"\bobjective structured clinical\b", re.IGNORECASE),
    ],
    "Mannequin": [
        re.compile(r"\bmannequin\b", re.IGNORECASE),
        re.compile(r"\bmanikin\b", re.IGNORECASE),
        re.compile(r"\bhigh-?fidelity\b", re.IGNORECASE),
        re.compile(r"\bSimMan\b", re.IGNORECASE),
    ],
    "Debriefing": [
        re.compile(r"\bdebriefing\b", re.IGNORECASE),
        re.compile(r"\bdebrief\b", re.IGNORECASE),
    ],
    "Roleplay": [
        re.compile(r"\brole-?play\b", re.IGNORECASE),
        re.compile(r"\broleplay\b", re.IGNORECASE),
    ],
    "Scenario-based": [
        re.compile(r"\bscenario\b", re.IGNORECASE),
        re.compile(r"\bcase.?based\b", re.IGNORECASE),
    ],
}

# NTS domains (duplicated from nts_analysis.py for cross-tab)
NTS_DOMAINS: Dict[str, List[re.Pattern]] = {
    "Communication": [
        re.compile(r"\bcommunicat\w+\b", re.IGNORECASE),
        re.compile(r"\bempathy\b", re.IGNORECASE),
        re.compile(r"\bhistory.?taking\b", re.IGNORECASE),
        re.compile(r"\bcounselling\b", re.IGNORECASE),
        re.compile(r"\bcounseling\b", re.IGNORECASE),
        re.compile(r"\bpatient.?interaction\b", re.IGNORECASE),
        re.compile(r"\bshared decision\b", re.IGNORECASE),
    ],
    "Teamwork": [
        re.compile(r"\bteamwork\b", re.IGNORECASE),
        re.compile(r"\bteam\s+training\b", re.IGNORECASE),
        re.compile(r"\binterprofessional\b", re.IGNORECASE),
        re.compile(r"\bcollaborat\w+\b", re.IGNORECASE),
        re.compile(r"\bcrew resource\b", re.IGNORECASE),
    ],
    "Leadership": [
        re.compile(r"\bleadership\b", re.IGNORECASE),
        re.compile(r"\bleading\b", re.IGNORECASE),
        re.compile(r"\bsupervis\w+\b", re.IGNORECASE),
        re.compile(r"\bmentor\w+\b", re.IGNORECASE),
    ],
    "Decision-making": [
        re.compile(r"\bdecision.?making\b", re.IGNORECASE),
        re.compile(r"\bclinical reasoning\b", re.IGNORECASE),
        re.compile(r"\bclinical judgment\b", re.IGNORECASE),
        re.compile(r"\bdiagnostic reasoning\b", re.IGNORECASE),
    ],
    "Situational awareness": [
        re.compile(r"\bsituation\w*\s*awareness\b", re.IGNORECASE),
        re.compile(r"\bvigilance\b", re.IGNORECASE),
    ],
    "Stress management": [
        re.compile(r"\bstress\s+manage\w+\b", re.IGNORECASE),
        re.compile(r"\bcognitive load\b", re.IGNORECASE),
        re.compile(r"\bresilience\b", re.IGNORECASE),
    ],
    "CRM": [
        re.compile(r"\bcrisis resource management\b", re.IGNORECASE),
        re.compile(r"\bcrew resource management\b", re.IGNORECASE),
        re.compile(r"\bCRM\b"),
    ],
}


def _get_text(paper: Dict) -> str:
    """Concatenate title and abstract into a single searchable string."""
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    return f"{title} {abstract}"


def classify_sim_types(papers: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, int]]:
    """
    Classify papers by simulation type.
    Returns:
        type_papers: {sim_type: [paper, ...]}
        type_counts: {sim_type: int}
    """
    type_papers: Dict[str, List[Dict]] = defaultdict(list)
    type_counts: Counter = Counter()

    for paper in papers:
        text = _get_text(paper)
        for sim_type, patterns in SIM_TYPES.items():
            if any(pat.search(text) for pat in patterns):
                type_papers[sim_type].append(paper)
                type_counts[sim_type] += 1

    return dict(type_papers), dict(type_counts)


def classify_nts(papers: List[Dict]) -> Dict[str, set]:
    """Classify papers into NTS domains, returning sets of paper IDs."""
    domain_ids: Dict[str, set] = defaultdict(set)
    for paper in papers:
        text = _get_text(paper)
        pid = paper.get("id") or paper.get("doi") or paper.get("title")
        for domain, patterns in NTS_DOMAINS.items():
            if any(pat.search(text) for pat in patterns):
                domain_ids[domain].add(pid)
    return dict(domain_ids)


def plot_sim_type_frequencies(type_counts: Dict[str, int], fig_dir: Path) -> None:
    """Horizontal bar chart of simulation type frequencies."""
    sim_types = sorted(type_counts.keys(), key=lambda t: type_counts[t])
    counts = [type_counts[t] for t in sim_types]

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = plt.cm.Set2(np.linspace(0, 1, len(sim_types)))
    bars = ax.barh(sim_types, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title("Simulation Type Frequencies (Title + Abstract)",
                 fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "simulation_type_frequencies.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_sim_nts_crosstab(type_papers: Dict[str, List[Dict]],
                           nts_domain_ids: Dict[str, set],
                           fig_dir: Path) -> None:
    """Heatmap cross-tabulation of simulation types vs NTS domains."""
    sim_types = sorted(type_papers.keys())
    nts_domains = sorted(nts_domain_ids.keys())

    if not sim_types or not nts_domains:
        logger.warning("Insufficient data for cross-tab heatmap")
        return

    # Build paper-ID sets per simulation type
    sim_type_ids: Dict[str, set] = {}
    for st, papers in type_papers.items():
        sim_type_ids[st] = {p.get("id") or p.get("doi") or p.get("title")
                            for p in papers}

    matrix = np.zeros((len(sim_types), len(nts_domains)), dtype=int)
    for si, st in enumerate(sim_types):
        for ni, nd in enumerate(nts_domains):
            matrix[si, ni] = len(sim_type_ids[st] & nts_domain_ids[nd])

    fig, ax = plt.subplots(figsize=(max(10, len(nts_domains) * 1.3),
                                     max(7, len(sim_types) * 0.8)))
    im = ax.imshow(matrix, aspect="auto", cmap="YlGnBu", interpolation="nearest")

    ax.set_xticks(range(len(nts_domains)))
    ax.set_xticklabels(nts_domains, rotation=45, ha="right", fontsize=10)
    ax.set_yticks(range(len(sim_types)))
    ax.set_yticklabels(sim_types, fontsize=10)

    # Annotate cells
    for i in range(len(sim_types)):
        for j in range(len(nts_domains)):
            val = matrix[i, j]
            if val > 0:
                text_color = "white" if val > matrix.max() * 0.6 else "black"
                ax.text(j, i, str(val), ha="center", va="center",
                        fontsize=9, color=text_color, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Paper Count", fontsize=10)
    ax.set_title("Simulation Types x NTS Domains Cross-Tabulation",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    out = fig_dir / "simulation_nts_crosstab.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_summary_table(type_counts: Dict[str, int], type_papers: Dict[str, List[Dict]],
                        nts_domain_ids: Dict[str, set],
                        total_papers: int, table_dir: Path) -> None:
    """Save markdown summary tables for simulation type analysis."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"simulation_type_summary_{ts}.md"

    lines = [
        "# Simulation Type Classification Summary",
        "",
        f"Total papers analysed: **{total_papers}**",
        "",
        "## Simulation Type Frequencies",
        "",
        "| Simulation Type | Count | % of Corpus |",
        "|-----------------|------:|------------:|",
    ]

    for st in sorted(type_counts, key=lambda t: type_counts[t], reverse=True):
        count = type_counts[st]
        pct = count / total_papers * 100 if total_papers else 0
        lines.append(f"| {st} | {count} | {pct:.1f}% |")

    # Multi-type papers
    paper_type_count: Counter = Counter()
    for st, papers in type_papers.items():
        for p in papers:
            pid = p.get("id") or p.get("doi") or p.get("title")
            paper_type_count[pid] += 1
    multi = sum(1 for c in paper_type_count.values() if c > 1)
    classified = len(paper_type_count)
    unclassified = total_papers - classified

    lines += [
        "",
        f"Papers classified into at least one type: **{classified}** "
        f"({classified / total_papers * 100:.1f}%)",
        f"Papers in multiple types: **{multi}** "
        f"({multi / total_papers * 100:.1f}%)",
        f"Unclassified papers: **{unclassified}** "
        f"({unclassified / total_papers * 100:.1f}%)",
        "",
    ]

    # Cross-tab table
    sim_types = sorted(type_papers.keys())
    nts_domains = sorted(nts_domain_ids.keys())

    lines += [
        "## Simulation Type x NTS Domain Cross-Tabulation",
        "",
        "| Simulation Type | " + " | ".join(nts_domains) + " |",
        "|-----------------|" + "|".join(["-----:" for _ in nts_domains]) + "|",
    ]

    sim_type_ids: Dict[str, set] = {}
    for st, papers in type_papers.items():
        sim_type_ids[st] = {p.get("id") or p.get("doi") or p.get("title")
                            for p in papers}

    for st in sim_types:
        row = f"| {st} |"
        for nd in nts_domains:
            overlap = len(sim_type_ids[st] & nts_domain_ids[nd])
            row += f" {overlap} |"
        lines.append(row)

    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved %s", out)


def main(input_path: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    data_path = Path(input_path)
    if not data_path.exists():
        logger.error("Input file not found: %s", data_path)
        sys.exit(1)

    papers = json.loads(data_path.read_text(encoding="utf-8"))
    logger.info("Loaded %d papers", len(papers))

    output_dir = Path(__file__).parent
    fig_dir = output_dir / "figures"
    table_dir = output_dir / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # Classify simulation types
    type_papers, type_counts = classify_sim_types(papers)

    logger.info("Simulation type counts:")
    for st in sorted(type_counts, key=lambda t: type_counts[t], reverse=True):
        logger.info("  %-30s %d", st, type_counts[st])

    # Classify NTS domains for cross-tab
    nts_domain_ids = classify_nts(papers)
    logger.info("NTS domain coverage (for cross-tab):")
    for nd in sorted(nts_domain_ids, key=lambda d: len(nts_domain_ids[d]), reverse=True):
        logger.info("  %-25s %d", nd, len(nts_domain_ids[nd]))

    # Generate outputs
    plot_sim_type_frequencies(type_counts, fig_dir)
    plot_sim_nts_crosstab(type_papers, nts_domain_ids, fig_dir)
    save_summary_table(type_counts, type_papers, nts_domain_ids, len(papers), table_dir)

    logger.info("Simulation type analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
