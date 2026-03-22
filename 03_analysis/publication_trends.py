#!/usr/bin/env python3
"""
Publication Trends Analysis
- Publication count by year (bar chart)
- Cumulative growth curve
- CAGR calculation
- Pre/post ChatGPT comparison (Nov 2022 cutoff)
- Separate charts for Tier 1/2/3
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


def analyze_publication_trends(papers: List[Dict], output_dir: str = None) -> Dict:
    """Analyze and visualize publication trends."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # Count by year
    year_counts = Counter()
    tier_year_counts = {"tier1": Counter(), "tier2": Counter(), "tier3": Counter()}

    for paper in papers:
        year = paper.get("year")
        if year and isinstance(year, (int, float)):
            year = int(year)
            if 2019 <= year <= 2027:
                year_counts[year] += 1
                tier = paper.get("screening_tier", "tier1")
                if tier in tier_year_counts:
                    tier_year_counts[tier][year] += 1

    if not year_counts:
        logger.warning("No valid year data found")
        return {"error": "No year data"}

    years = sorted(year_counts.keys())
    counts = [year_counts[y] for y in years]

    # CAGR calculation
    if len(years) >= 2 and counts[0] > 0:
        n_years = years[-1] - years[0]
        if n_years > 0:
            cagr = ((counts[-1] / counts[0]) ** (1 / n_years) - 1) * 100
        else:
            cagr = 0
    else:
        cagr = 0

    # Pre/post ChatGPT (Nov 2022)
    pre_chatgpt = sum(c for y, c in year_counts.items() if y <= 2022)
    post_chatgpt = sum(c for y, c in year_counts.items() if y >= 2023)

    # Cumulative
    cumulative = np.cumsum(counts)

    # --- Figure 1: Publication trends bar chart ---
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(years, counts, color="#2196F3", edgecolor="white", width=0.7)

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(count), ha="center", va="bottom", fontsize=10, fontweight="bold")

    # ChatGPT launch line
    ax.axvline(x=2022.9, color="red", linestyle="--", linewidth=1.5, alpha=0.7)
    ax.text(2022.95, max(counts) * 0.9, "ChatGPT\nLaunch",
            color="red", fontsize=9, ha="left", style="italic")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Publications", fontsize=12)
    ax.set_title("Publication Trends: LLMs in Healthcare Simulation (2020-2026)", fontsize=13, fontweight="bold")
    ax.set_xticks(years)
    plt.tight_layout()
    plt.savefig(fig_dir / "publication_trends.png", dpi=300, bbox_inches="tight")
    plt.close()

    # --- Figure 2: Cumulative growth ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, cumulative, "o-", color="#4CAF50", linewidth=2, markersize=8)
    ax.fill_between(years, cumulative, alpha=0.2, color="#4CAF50")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Cumulative Publications", fontsize=12)
    ax.set_title("Cumulative Growth of LLM-Healthcare Simulation Literature", fontsize=13, fontweight="bold")
    ax.set_xticks(years)
    plt.tight_layout()
    plt.savefig(fig_dir / "cumulative_growth.png", dpi=300, bbox_inches="tight")
    plt.close()

    # --- Table ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_path = table_dir / f"publication_trends_{timestamp}.md"
    with open(table_path, "w") as f:
        f.write("# Publication Trends\n\n")
        f.write(f"**Total papers:** {sum(counts)}\n")
        f.write(f"**CAGR:** {cagr:.1f}%\n")
        f.write(f"**Pre-ChatGPT (2020-2022):** {pre_chatgpt}\n")
        f.write(f"**Post-ChatGPT (2023-2026):** {post_chatgpt}\n\n")
        f.write("| Year | Count | Cumulative | % of Total |\n")
        f.write("|------|-------|------------|------------|\n")
        total = sum(counts)
        for y, c, cum in zip(years, counts, cumulative):
            f.write(f"| {y} | {c} | {cum} | {c/total*100:.1f}% |\n")

    results = {
        "total_papers": sum(counts),
        "year_distribution": dict(year_counts),
        "cagr_percent": round(cagr, 1),
        "pre_chatgpt_count": pre_chatgpt,
        "post_chatgpt_count": post_chatgpt,
        "earliest_year": min(years),
        "latest_year": max(years),
        "peak_year": max(year_counts, key=year_counts.get),
        "peak_count": max(counts),
    }

    logger.info(f"Publication trends: {sum(counts)} papers, CAGR={cagr:.1f}%, peak={max(year_counts, key=year_counts.get)}")
    return results


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python publication_trends.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = analyze_publication_trends(papers)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
