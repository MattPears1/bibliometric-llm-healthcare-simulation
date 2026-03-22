#!/usr/bin/env python3
"""
Descriptive Statistics Analysis
- Total papers, year range, mean citations
- Source database distribution (bar chart)
- Open access percentage
- Tier distribution (bar chart)
- Document type distribution
- Data completeness metrics
- Comprehensive stats table (markdown)
"""

import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


def compute_stats(papers: List[Dict]) -> Dict:
    """Compute comprehensive descriptive statistics."""
    total = len(papers)

    # Year statistics
    years = [int(p["year"]) for p in papers
             if p.get("year") and isinstance(p["year"], (int, float))]
    year_min = min(years) if years else None
    year_max = max(years) if years else None
    year_mean = np.mean(years) if years else None
    year_median = int(np.median(years)) if years else None

    # Citation statistics
    citations = [p["citation_count"] for p in papers
                 if p.get("citation_count") is not None
                 and isinstance(p["citation_count"], (int, float))]
    cite_mean = np.mean(citations) if citations else 0
    cite_median = np.median(citations) if citations else 0
    cite_max = max(citations) if citations else 0
    cite_total = sum(citations) if citations else 0

    # Source database
    source_counts = Counter(p.get("source_db", "unknown") for p in papers)

    # Open access
    oa_count = sum(1 for p in papers if p.get("open_access") is True)
    oa_pct = oa_count / total * 100 if total else 0

    # Screening tier
    tier_counts = Counter(p.get("screening_tier", "unspecified") for p in papers)

    # Screening decision
    decision_counts = Counter(p.get("screening_decision", "unspecified") for p in papers)

    # Document type
    type_counts = Counter()
    for p in papers:
        doc_type = p.get("type") or "unspecified"
        doc_type = doc_type.strip() if doc_type else "unspecified"
        if not doc_type:
            doc_type = "unspecified"
        type_counts[doc_type] += 1

    # Data completeness
    has_abstract = sum(1 for p in papers if p.get("abstract") and len(str(p["abstract"]).strip()) > 0)
    has_doi = sum(1 for p in papers if p.get("doi") and len(str(p["doi"]).strip()) > 0)
    has_keywords = sum(1 for p in papers if p.get("keywords") and len(p["keywords"]) > 0)
    has_authors = sum(1 for p in papers if p.get("authors") and len(p["authors"]) > 0)
    has_journal = sum(1 for p in papers if p.get("journal") and len(str(p["journal"]).strip()) > 0)
    has_year = sum(1 for p in papers if p.get("year") is not None)
    has_citations = len(citations)

    completeness = {
        "abstract": has_abstract / total * 100 if total else 0,
        "doi": has_doi / total * 100 if total else 0,
        "keywords": has_keywords / total * 100 if total else 0,
        "authors": has_authors / total * 100 if total else 0,
        "journal": has_journal / total * 100 if total else 0,
        "year": has_year / total * 100 if total else 0,
        "citations": has_citations / total * 100 if total else 0,
    }

    return {
        "total": total,
        "year_min": year_min,
        "year_max": year_max,
        "year_mean": year_mean,
        "year_median": year_median,
        "cite_mean": cite_mean,
        "cite_median": cite_median,
        "cite_max": cite_max,
        "cite_total": cite_total,
        "n_citations": len(citations),
        "source_counts": source_counts,
        "oa_count": oa_count,
        "oa_pct": oa_pct,
        "tier_counts": tier_counts,
        "decision_counts": decision_counts,
        "type_counts": type_counts,
        "completeness": completeness,
    }


def plot_source_distribution(source_counts: Counter, fig_dir: Path) -> None:
    """Bar chart of source database distribution."""
    sources = sorted(source_counts.keys(), key=lambda s: source_counts[s], reverse=True)
    counts = [source_counts[s] for s in sources]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Paired(np.linspace(0.1, 0.9, len(sources)))
    bars = ax.bar(sources, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.01,
                str(count), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xlabel("Source Database", fontsize=12)
    ax.set_ylabel("Number of Papers", fontsize=12)
    ax.set_title("Papers by Source Database", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    out = fig_dir / "source_database_distribution.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_tier_distribution(tier_counts: Counter, fig_dir: Path) -> None:
    """Bar chart of screening tier distribution."""
    tiers = sorted(tier_counts.keys())
    counts = [tier_counts[t] for t in tiers]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2ecc71", "#3498db", "#e67e22", "#95a5a6"]
    bar_colors = colors[:len(tiers)]
    bars = ax.bar(tiers, counts, color=bar_colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.01,
                str(count), ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_xlabel("Screening Tier", fontsize=12)
    ax.set_ylabel("Number of Papers", fontsize=12)
    ax.set_title("Distribution by Screening Tier", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "tier_distribution.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_type_distribution(type_counts: Counter, fig_dir: Path) -> None:
    """Horizontal bar chart of document type distribution (top 15)."""
    top = type_counts.most_common(15)
    labels = [t[0] for t in reversed(top)]
    counts = [t[1] for t in reversed(top)]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    bars = ax.barh(labels, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title("Document Type Distribution", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "document_type_distribution.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_completeness(completeness: Dict[str, float], fig_dir: Path) -> None:
    """Bar chart of data completeness metrics."""
    fields = sorted(completeness.keys(), key=lambda f: completeness[f], reverse=True)
    values = [completeness[f] for f in fields]

    fig, ax = plt.subplots(figsize=(9, 5))
    bar_colors = ["#27ae60" if v >= 90 else "#f39c12" if v >= 70 else "#e74c3c" for v in values]
    bars = ax.bar(fields, values, color=bar_colors, edgecolor="grey", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylim(0, 110)
    ax.set_xlabel("Field", fontsize=12)
    ax.set_ylabel("Completeness (%)", fontsize=12)
    ax.set_title("Data Completeness by Field", fontsize=14, fontweight="bold")
    ax.axhline(y=90, color="green", linestyle="--", alpha=0.4, label="90% threshold")
    ax.axhline(y=70, color="orange", linestyle="--", alpha=0.4, label="70% threshold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    out = fig_dir / "data_completeness.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_stats_table(stats: Dict, table_dir: Path) -> None:
    """Save comprehensive statistics as a markdown table."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"descriptive_stats_{ts}.md"

    lines = [
        "# Descriptive Statistics Summary",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Total papers | {stats['total']} |",
        f"| Year range | {stats['year_min']}--{stats['year_max']} |",
        f"| Median publication year | {stats['year_median']} |",
        f"| Mean citation count | {stats['cite_mean']:.2f} |",
        f"| Median citation count | {stats['cite_median']:.1f} |",
        f"| Max citation count | {stats['cite_max']} |",
        f"| Total citations | {stats['cite_total']} |",
        f"| Papers with citation data | {stats['n_citations']} |",
        f"| Open access papers | {stats['oa_count']} ({stats['oa_pct']:.1f}%) |",
        "",
        "## Source Database Distribution",
        "",
        "| Database | Count | % |",
        "|----------|------:|--:|",
    ]
    for src, cnt in stats["source_counts"].most_common():
        pct = cnt / stats["total"] * 100
        lines.append(f"| {src} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Screening Tier Distribution",
        "",
        "| Tier | Count | % |",
        "|------|------:|--:|",
    ]
    for tier in sorted(stats["tier_counts"].keys()):
        cnt = stats["tier_counts"][tier]
        pct = cnt / stats["total"] * 100
        lines.append(f"| {tier} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Screening Decision Distribution",
        "",
        "| Decision | Count | % |",
        "|----------|------:|--:|",
    ]
    for dec, cnt in stats["decision_counts"].most_common():
        pct = cnt / stats["total"] * 100
        lines.append(f"| {dec} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Document Type Distribution",
        "",
        "| Type | Count | % |",
        "|------|------:|--:|",
    ]
    for dtype, cnt in stats["type_counts"].most_common(20):
        pct = cnt / stats["total"] * 100
        lines.append(f"| {dtype} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Data Completeness",
        "",
        "| Field | Completeness |",
        "|-------|-------------:|",
    ]
    for field in sorted(stats["completeness"].keys(), key=lambda f: stats["completeness"][f], reverse=True):
        lines.append(f"| {field} | {stats['completeness'][field]:.1f}% |")

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

    stats = compute_stats(papers)

    logger.info("Total papers: %d", stats["total"])
    logger.info("Year range: %s - %s", stats["year_min"], stats["year_max"])
    logger.info("Mean citations: %.2f", stats["cite_mean"])
    logger.info("Open access: %d (%.1f%%)", stats["oa_count"], stats["oa_pct"])

    plot_source_distribution(stats["source_counts"], fig_dir)
    plot_tier_distribution(stats["tier_counts"], fig_dir)
    plot_type_distribution(stats["type_counts"], fig_dir)
    plot_completeness(stats["completeness"], fig_dir)
    save_stats_table(stats, table_dir)

    logger.info("Descriptive statistics analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
