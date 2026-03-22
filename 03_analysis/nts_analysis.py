#!/usr/bin/env python3
"""
Non-Technical Skills (NTS) Domain Analysis
- Classify papers by NTS domains via regex on title + abstract
- Bar chart of NTS domain frequencies
- Cross-tab heatmap: NTS domain by year
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
# NTS domain definitions: domain -> list of compiled regex patterns
# ---------------------------------------------------------------------------
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


def classify_papers(papers: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, int]]:
    """
    Classify papers into NTS domains.
    Returns:
        domain_papers: {domain: [paper, ...]}
        domain_counts: {domain: int}
    """
    domain_papers: Dict[str, List[Dict]] = defaultdict(list)
    domain_counts: Counter = Counter()

    for paper in papers:
        text = _get_text(paper)
        for domain, patterns in NTS_DOMAINS.items():
            if any(pat.search(text) for pat in patterns):
                domain_papers[domain].append(paper)
                domain_counts[domain] += 1

    return dict(domain_papers), dict(domain_counts)


def plot_domain_frequencies(domain_counts: Dict[str, int], fig_dir: Path) -> None:
    """Horizontal bar chart of NTS domain frequencies."""
    domains = sorted(domain_counts.keys(), key=lambda d: domain_counts[d])
    counts = [domain_counts[d] for d in domains]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Set2(np.linspace(0, 1, len(domains)))
    bars = ax.barh(domains, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title("Non-Technical Skills (NTS) Domain Frequencies", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "nts_domain_frequencies.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_domain_year_heatmap(domain_papers: Dict[str, List[Dict]], fig_dir: Path) -> None:
    """Heatmap of NTS domain counts by publication year."""
    # Collect all years
    all_years: set = set()
    for papers in domain_papers.values():
        for p in papers:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                all_years.add(int(y))

    if not all_years:
        logger.warning("No valid year data for heatmap")
        return

    years = sorted(all_years)
    domains = sorted(domain_papers.keys())

    matrix = np.zeros((len(domains), len(years)), dtype=int)
    year_idx = {y: i for i, y in enumerate(years)}

    for di, domain in enumerate(domains):
        for p in domain_papers[domain]:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                yi = year_idx.get(int(y))
                if yi is not None:
                    matrix[di, yi] += 1

    fig, ax = plt.subplots(figsize=(max(10, len(years) * 0.9), max(6, len(domains) * 0.7)))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(domains)))
    ax.set_yticklabels(domains, fontsize=10)

    # Annotate cells
    for i in range(len(domains)):
        for j in range(len(years)):
            val = matrix[i, j]
            if val > 0:
                text_color = "white" if val > matrix.max() * 0.6 else "black"
                ax.text(j, i, str(val), ha="center", va="center",
                        fontsize=8, color=text_color, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Paper Count", fontsize=10)
    ax.set_title("NTS Domains by Publication Year", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year", fontsize=12)
    plt.tight_layout()

    out = fig_dir / "nts_domain_year_heatmap.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_summary_table(domain_counts: Dict[str, int], domain_papers: Dict[str, List[Dict]],
                       total_papers: int, table_dir: Path) -> None:
    """Save a markdown summary table of NTS domain classification."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"nts_domains_{ts}.md"

    lines = [
        "# NTS Domain Classification Summary",
        "",
        f"Total papers analysed: **{total_papers}**",
        "",
        "| Domain | Count | % of Corpus | Example Patterns |",
        "|--------|------:|------------:|------------------|",
    ]
    for domain in sorted(domain_counts, key=lambda d: domain_counts[d], reverse=True):
        count = domain_counts[domain]
        pct = count / total_papers * 100 if total_papers else 0
        pattern_strs = [p.pattern for p in NTS_DOMAINS[domain][:3]]
        lines.append(f"| {domain} | {count} | {pct:.1f}% | {', '.join(pattern_strs)} |")

    # Multi-domain papers
    multi = 0
    for paper_list in domain_papers.values():
        paper_ids = {p.get("id") or p.get("doi") for p in paper_list}
    # Count papers appearing in >1 domain
    paper_domain_count: Counter = Counter()
    for domain, papers in domain_papers.items():
        for p in papers:
            pid = p.get("id") or p.get("doi") or p.get("title")
            paper_domain_count[pid] += 1
    multi = sum(1 for c in paper_domain_count.values() if c > 1)
    unclassified = total_papers - len(paper_domain_count)

    lines += [
        "",
        f"Papers classified into at least one domain: **{len(paper_domain_count)}** "
        f"({len(paper_domain_count) / total_papers * 100:.1f}%)",
        f"Papers in multiple domains: **{multi}** "
        f"({multi / total_papers * 100:.1f}%)",
        f"Unclassified papers: **{unclassified}** "
        f"({unclassified / total_papers * 100:.1f}%)",
        "",
    ]

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

    domain_papers, domain_counts = classify_papers(papers)

    logger.info("NTS domain counts:")
    for domain in sorted(domain_counts, key=lambda d: domain_counts[d], reverse=True):
        logger.info("  %-25s %d", domain, domain_counts[domain])

    plot_domain_frequencies(domain_counts, fig_dir)
    plot_domain_year_heatmap(domain_papers, fig_dir)
    save_summary_table(domain_counts, domain_papers, len(papers), table_dir)

    logger.info("NTS analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
