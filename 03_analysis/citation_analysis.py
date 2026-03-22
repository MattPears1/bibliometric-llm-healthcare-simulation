#!/usr/bin/env python3
"""
Citation Analysis
=================
Computes bibliometric citation indicators and generates visualizations:
- Summary statistics: total citations, mean, median, max, % uncited
- h-index, g-index, i10-index
- Citation distribution histogram (log-scaled y-axis)
- Top 20 most-cited papers table
- Citations aggregated by publication year
"""

import json
import logging
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Index calculations
# ---------------------------------------------------------------------------

def compute_h_index(citations: List[int]) -> int:
    """Largest h such that h papers have >= h citations each."""
    sorted_desc = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(sorted_desc):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


def compute_g_index(citations: List[int]) -> int:
    """Largest g such that the top g papers together have >= g^2 citations."""
    sorted_desc = sorted(citations, reverse=True)
    cumsum = 0
    g = 0
    for i, c in enumerate(sorted_desc):
        cumsum += c
        if cumsum >= (i + 1) ** 2:
            g = i + 1
        else:
            break
    return g


def compute_i10_index(citations: List[int]) -> int:
    """Number of papers with >= 10 citations."""
    return sum(1 for c in citations if c >= 10)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_citations(papers: List[Dict], output_dir: str = None) -> Dict:
    """Run citation analysis and save figures + tables."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # --- Extract citation counts ---
    citation_data = []
    for p in papers:
        cc = p.get("citation_count")
        if cc is not None and isinstance(cc, (int, float)):
            citation_data.append({"paper": p, "citations": int(cc)})
        else:
            citation_data.append({"paper": p, "citations": 0})

    citations = [d["citations"] for d in citation_data]

    if not citations:
        logger.warning("No citation data found")
        return {"error": "No citation data"}

    # --- Summary statistics ---
    total_citations = sum(citations)
    mean_citations = np.mean(citations)
    median_citations = float(np.median(citations))
    max_citations = max(citations)
    n_papers = len(citations)
    n_uncited = sum(1 for c in citations if c == 0)
    pct_uncited = (n_uncited / n_papers) * 100

    h_index = compute_h_index(citations)
    g_index = compute_g_index(citations)
    i10_index = compute_i10_index(citations)

    logger.info(
        f"Citation summary: N={n_papers}, total={total_citations}, "
        f"mean={mean_citations:.1f}, median={median_citations}, "
        f"h={h_index}, g={g_index}, i10={i10_index}, uncited={pct_uncited:.1f}%"
    )

    # --- Figure 1: Citation distribution histogram (log-scaled y-axis) ---
    fig, ax = plt.subplots(figsize=(10, 6))

    # Use log-spaced bins for better visualization of skewed distribution
    nonzero = [c for c in citations if c > 0]
    if nonzero:
        max_log = math.log10(max(nonzero)) + 0.5
        bins = [0] + list(np.logspace(0, max_log, 30))
    else:
        bins = 30

    ax.hist(citations, bins=bins, color="#2196F3", edgecolor="white", alpha=0.85)
    ax.set_yscale("log")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("Citation Count", fontsize=12)
    ax.set_ylabel("Number of Papers (log scale)", fontsize=12)
    ax.set_title("Citation Distribution", fontsize=13, fontweight="bold")

    # Annotate key metrics
    textstr = (
        f"N = {n_papers}\n"
        f"Mean = {mean_citations:.1f}\n"
        f"Median = {median_citations:.0f}\n"
        f"h-index = {h_index}\n"
        f"Uncited = {pct_uncited:.1f}%"
    )
    props = dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.8)
    ax.text(
        0.97, 0.97, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment="top", horizontalalignment="right", bbox=props
    )

    plt.tight_layout()
    plt.savefig(fig_dir / "citation_distribution.png", dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved citation_distribution.png")

    # --- Figure 2: Citations by year ---
    year_citations = Counter()
    year_counts = Counter()
    for d in citation_data:
        year = d["paper"].get("year")
        if year and isinstance(year, (int, float)):
            year = int(year)
            if 2015 <= year <= 2027:
                year_citations[year] += d["citations"]
                year_counts[year] += 1

    if year_citations:
        years_sorted = sorted(year_citations.keys())
        total_by_year = [year_citations[y] for y in years_sorted]
        mean_by_year = [
            year_citations[y] / year_counts[y] if year_counts[y] else 0
            for y in years_sorted
        ]

        fig, ax1 = plt.subplots(figsize=(10, 6))
        bar_width = 0.6
        bars = ax1.bar(
            years_sorted, total_by_year,
            width=bar_width, color="#2196F3", edgecolor="white", alpha=0.8,
            label="Total citations"
        )
        ax1.set_xlabel("Publication Year", fontsize=12)
        ax1.set_ylabel("Total Citations", fontsize=12, color="#2196F3")
        ax1.tick_params(axis="y", labelcolor="#2196F3")
        ax1.set_xticks(years_sorted)

        # Overlay mean citations per paper as line
        ax2 = ax1.twinx()
        ax2.plot(
            years_sorted, mean_by_year, "o-",
            color="#FF5722", linewidth=2, markersize=7, label="Mean per paper"
        )
        ax2.set_ylabel("Mean Citations per Paper", fontsize=12, color="#FF5722")
        ax2.tick_params(axis="y", labelcolor="#FF5722")

        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)

        ax1.set_title("Citations by Publication Year", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(fig_dir / "citations_by_year.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved citations_by_year.png")

    # --- Table 1: Top 20 most-cited papers ---
    sorted_data = sorted(citation_data, key=lambda d: d["citations"], reverse=True)
    top20 = sorted_data[:20]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_path = table_dir / f"citation_top20_{timestamp}.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# Top 20 Most-Cited Papers\n\n")
        f.write(
            "| Rank | Citations | Year | Title | DOI | Journal |\n"
            "|------|-----------|------|-------|-----|---------|\n"
        )
        for rank, d in enumerate(top20, 1):
            p = d["paper"]
            title = p.get("title", "N/A")
            # Truncate long titles for table readability
            if len(title) > 80:
                title = title[:77] + "..."
            doi = p.get("doi", "")
            year = p.get("year", "")
            journal = p.get("journal", "") or ""
            if len(journal) > 40:
                journal = journal[:37] + "..."
            f.write(
                f"| {rank} | {d['citations']} | {year} | {title} | {doi} | {journal} |\n"
            )

    logger.info(f"Saved top-20 table to {table_path}")

    # --- Table 2: Citation summary statistics ---
    summary_path = table_dir / f"citation_summary_{timestamp}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Citation Summary Statistics\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total papers | {n_papers} |\n")
        f.write(f"| Total citations | {total_citations} |\n")
        f.write(f"| Mean citations | {mean_citations:.2f} |\n")
        f.write(f"| Median citations | {median_citations:.0f} |\n")
        f.write(f"| Max citations | {max_citations} |\n")
        f.write(f"| h-index | {h_index} |\n")
        f.write(f"| g-index | {g_index} |\n")
        f.write(f"| i10-index | {i10_index} |\n")
        f.write(f"| Uncited papers | {n_uncited} ({pct_uncited:.1f}%) |\n")

        if year_citations:
            f.write(f"\n## Citations by Year\n\n")
            f.write("| Year | Papers | Total Cites | Mean Cites |\n")
            f.write("|------|--------|-------------|------------|\n")
            for y in years_sorted:
                mean_y = year_citations[y] / year_counts[y] if year_counts[y] else 0
                f.write(
                    f"| {y} | {year_counts[y]} | {year_citations[y]} | {mean_y:.1f} |\n"
                )

    logger.info(f"Saved citation summary to {summary_path}")

    # --- Results dict ---
    results = {
        "total_papers": n_papers,
        "total_citations": total_citations,
        "mean_citations": round(mean_citations, 2),
        "median_citations": median_citations,
        "max_citations": max_citations,
        "h_index": h_index,
        "g_index": g_index,
        "i10_index": i10_index,
        "uncited_papers": n_uncited,
        "pct_uncited": round(pct_uncited, 1),
    }
    return results


def main():
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python citation_analysis.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = analyze_citations(papers)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
