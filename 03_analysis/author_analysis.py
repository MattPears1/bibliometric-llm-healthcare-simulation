#!/usr/bin/env python3
"""
Author Analysis
===============
Bibliometric analysis of authorship patterns:
- Total unique authors, most prolific (top 20)
- Author name normalisation: handles "First Last" and "Last, First" formats
- Lotka's law test: log-log OLS regression of author productivity
  (expected exponent ~ 2.0 for classical inverse-square law)
- Collaboration index (average authors per paper)
- Single-paper vs multi-paper author ratio
- Visualisations: author productivity distribution, top authors bar chart
"""

import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Author name parsing
# ---------------------------------------------------------------------------

def normalise_author_name(raw_name: str) -> Optional[str]:
    """Normalise an author name to 'Lastname, Initials' form.

    Handles:
      - "Last, First Middle"  -> "Last, F M"
      - "First Middle Last"   -> "Last, F M"
      - "F. M. Last"          -> "Last, F M"
      - Single-word names are returned as-is (lowercased title-case).

    Returns None for empty / clearly invalid names.
    """
    if not raw_name or not raw_name.strip():
        return None

    name = raw_name.strip()
    # Remove digits, stray punctuation artefacts
    name = re.sub(r"[0-9]", "", name)
    name = name.strip(" .,;")

    if not name:
        return None

    # Detect "Last, First..." format
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        last = parts[0].strip()
        firsts = parts[1].strip() if len(parts) > 1 else ""
    else:
        # "First [Middle ...] Last" — last token is surname
        tokens = name.split()
        if len(tokens) == 1:
            return tokens[0].title()

        def _looks_like_initials(token: str) -> bool:
            """Return True if a token is likely initials rather than a name.

            Matches: single letter ("R"), single letter with dot ("R."),
            or all-uppercase 2-3 letter clusters that are likely packed
            initials ("TF", "ABC").
            """
            stripped = token.strip(".")
            if not stripped or not stripped.isalpha():
                return False
            if len(stripped) == 1:
                return True
            # All-uppercase short token like "TF" => packed initials
            if len(stripped) <= 3 and stripped.isupper():
                return True
            return False

        # Heuristic: if trailing tokens look like initials
        # (e.g. "Scherr R", "Heston TF"), they are not the surname.
        # Walk backwards to find where the initials start.
        surname_end = len(tokens)
        for i in range(len(tokens) - 1, 0, -1):
            if _looks_like_initials(tokens[i]):
                surname_end = i
            else:
                break

        if surname_end < len(tokens):
            # Trailing tokens are initials: "Surname [Surname2] I1 I2"
            last = " ".join(tokens[:surname_end]).strip()
            firsts = " ".join(tokens[surname_end:])
        else:
            # Normal case: last token is surname
            last = tokens[-1].strip()
            firsts = " ".join(tokens[:-1])

    # Build initials from first-name part
    first_tokens = firsts.split()
    initials = []
    for t in first_tokens:
        t = t.strip(".")
        if not t:
            continue
        # Packed uppercase initials like "TF" -> "T", "F"
        if len(t) <= 3 and t.isupper():
            for ch in t:
                initials.append(ch.upper())
        else:
            initials.append(t[0].upper())
    initial_str = " ".join(initials)

    last = last.strip().title()
    if not last:
        return None

    if initial_str:
        return f"{last}, {initial_str}"
    return last


def extract_authors(paper: Dict) -> List[str]:
    """Return list of normalised author names from a paper dict."""
    authors_raw = paper.get("authors", [])
    if not authors_raw:
        return []
    names = []
    for entry in authors_raw:
        if isinstance(entry, dict):
            raw = entry.get("name", "")
        elif isinstance(entry, str):
            raw = entry
        else:
            continue
        norm = normalise_author_name(raw)
        if norm:
            names.append(norm)
    return names


# ---------------------------------------------------------------------------
# Lotka's law
# ---------------------------------------------------------------------------

def lotkas_law_test(
    author_paper_counts: Counter,
) -> Dict:
    """Fit Lotka's inverse-square law via log-log OLS.

    Lotka's law states: y_n = C / n^beta  where beta ~ 2.0.
    We regress log(proportion of authors with n papers) on log(n).

    Returns dict with slope (beta), intercept, R-squared, and data points.
    """
    # Frequency of frequencies: how many authors wrote exactly n papers
    freq_of_freq = Counter(author_paper_counts.values())
    total_authors = sum(freq_of_freq.values())

    ns = sorted(freq_of_freq.keys())
    proportions = [freq_of_freq[n] / total_authors for n in ns]

    if len(ns) < 2:
        return {"beta": None, "r_squared": None, "message": "Insufficient data points"}

    log_n = np.log10(ns)
    log_p = np.log10(proportions)

    # OLS: log_p = intercept + slope * log_n
    coeffs = np.polyfit(log_n, log_p, 1)
    slope, intercept = coeffs
    # R-squared
    predicted = np.polyval(coeffs, log_n)
    ss_res = np.sum((log_p - predicted) ** 2)
    ss_tot = np.sum((log_p - np.mean(log_p)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return {
        "beta": round(-slope, 3),  # Lotka exponent (negate because slope is negative)
        "intercept": round(intercept, 3),
        "r_squared": round(r_squared, 3),
        "n_values": ns,
        "proportions": proportions,
        "log_n": log_n.tolist(),
        "log_p": log_p.tolist(),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_authors(papers: List[Dict], output_dir: str = None) -> Dict:
    """Run author analysis and save figures + tables."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # --- Build author-level counts ---
    author_counter = Counter()  # author -> number of papers
    authors_per_paper = []

    for paper in papers:
        author_list = extract_authors(paper)
        authors_per_paper.append(len(author_list))
        for a in set(author_list):  # deduplicate within a single paper
            author_counter[a] += 1

    total_unique_authors = len(author_counter)
    papers_with_authors = sum(1 for a in authors_per_paper if a > 0)

    # Collaboration index: mean authors per paper (papers with >= 1 author)
    collab_index = (
        np.mean([a for a in authors_per_paper if a > 0])
        if papers_with_authors
        else 0
    )

    single_paper_authors = sum(1 for c in author_counter.values() if c == 1)
    multi_paper_authors = total_unique_authors - single_paper_authors
    single_multi_ratio = (
        single_paper_authors / multi_paper_authors
        if multi_paper_authors > 0
        else float("inf")
    )

    logger.info(
        f"Authors: {total_unique_authors} unique, collaboration index={collab_index:.2f}, "
        f"single-paper={single_paper_authors}, multi-paper={multi_paper_authors}"
    )

    # --- Lotka's law ---
    lotka = lotkas_law_test(author_counter)
    logger.info(
        f"Lotka's law: beta={lotka.get('beta')}, R^2={lotka.get('r_squared')}"
    )

    # --- Figure 1: Author productivity distribution (log-log) ---
    freq_of_freq = Counter(author_counter.values())
    ns_sorted = sorted(freq_of_freq.keys())
    counts_ff = [freq_of_freq[n] for n in ns_sorted]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(ns_sorted, counts_ff, color="#4CAF50", edgecolor="white", alpha=0.85)
    ax.set_yscale("log")
    if max(ns_sorted) > 20:
        ax.set_xscale("log")
    ax.set_xlabel("Number of Papers per Author", fontsize=12)
    ax.set_ylabel("Number of Authors (log scale)", fontsize=12)
    ax.set_title("Author Productivity Distribution", fontsize=13, fontweight="bold")

    # Annotate Lotka's law fit
    if lotka.get("beta") is not None:
        textstr = (
            f"Lotka exponent (beta) = {lotka['beta']:.2f}\n"
            f"R² = {lotka['r_squared']:.3f}\n"
            f"Expected beta ≈ 2.0"
        )
        props = dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8)
        ax.text(
            0.97, 0.97, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", horizontalalignment="right", bbox=props,
        )

    plt.tight_layout()
    plt.savefig(fig_dir / "author_productivity.png", dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved author_productivity.png")

    # --- Figure 2: Lotka's law log-log regression plot ---
    if lotka.get("beta") is not None:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            lotka["log_n"], lotka["log_p"],
            color="#FF5722", s=60, zorder=5, label="Observed"
        )
        # Regression line
        x_fit = np.linspace(min(lotka["log_n"]), max(lotka["log_n"]), 50)
        y_fit = lotka["intercept"] + (-lotka["beta"]) * x_fit
        ax.plot(x_fit, y_fit, "--", color="#333333", linewidth=1.5, label="OLS fit")
        ax.set_xlabel("log₁₀(Papers per Author)", fontsize=12)
        ax.set_ylabel("log₁₀(Proportion of Authors)", fontsize=12)
        ax.set_title(
            f"Lotka's Law Test (β = {lotka['beta']:.2f}, R² = {lotka['r_squared']:.3f})",
            fontsize=13, fontweight="bold",
        )
        ax.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(fig_dir / "lotkas_law.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved lotkas_law.png")

    # --- Figure 3: Top 20 most prolific authors ---
    top20 = author_counter.most_common(20)
    top_names = [t[0] for t in top20][::-1]  # reverse for horizontal bar
    top_counts = [t[1] for t in top20][::-1]

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(range(len(top_names)), top_counts, color="#2196F3", edgecolor="white")
    ax.set_yticks(range(len(top_names)))
    ax.set_yticklabels(top_names, fontsize=10)
    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title("Top 20 Most Prolific Authors", fontsize=13, fontweight="bold")

    # Value labels
    for bar, count in zip(bars, top_counts):
        ax.text(
            bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
            str(count), va="center", fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(fig_dir / "top_authors.png", dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved top_authors.png")

    # --- Figure 4: Collaboration index over time ---
    year_author_counts = {}
    for paper in papers:
        year = paper.get("year")
        if year and isinstance(year, (int, float)):
            year = int(year)
            if 2015 <= year <= 2027:
                n_auth = len(extract_authors(paper))
                if n_auth > 0:
                    year_author_counts.setdefault(year, []).append(n_auth)

    if year_author_counts:
        years_sorted = sorted(year_author_counts.keys())
        mean_collab = [np.mean(year_author_counts[y]) for y in years_sorted]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(years_sorted, mean_collab, "o-", color="#9C27B0", linewidth=2, markersize=8)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Mean Authors per Paper", fontsize=12)
        ax.set_title("Collaboration Index by Year", fontsize=13, fontweight="bold")
        ax.set_xticks(years_sorted)
        ax.axhline(y=collab_index, color="gray", linestyle="--", alpha=0.5, label=f"Overall mean = {collab_index:.2f}")
        ax.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(fig_dir / "collaboration_index.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved collaboration_index.png")

    # --- Tables ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Table: top 20 authors
    table_path = table_dir / f"author_top20_{timestamp}.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# Top 20 Most Prolific Authors\n\n")
        f.write("| Rank | Author | Papers |\n")
        f.write("|------|--------|--------|\n")
        for rank, (author, count) in enumerate(author_counter.most_common(20), 1):
            f.write(f"| {rank} | {author} | {count} |\n")
    logger.info(f"Saved top-20 authors table to {table_path}")

    # Table: summary statistics
    summary_path = table_dir / f"author_summary_{timestamp}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Author Analysis Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total unique authors | {total_unique_authors} |\n")
        f.write(f"| Papers with author data | {papers_with_authors} |\n")
        f.write(f"| Collaboration index (mean authors/paper) | {collab_index:.2f} |\n")
        f.write(f"| Single-paper authors | {single_paper_authors} ({single_paper_authors/total_unique_authors*100:.1f}%) |\n")
        f.write(f"| Multi-paper authors | {multi_paper_authors} ({multi_paper_authors/total_unique_authors*100:.1f}%) |\n")
        f.write(f"| Single/multi ratio | {single_multi_ratio:.2f} |\n")
        if lotka.get("beta") is not None:
            f.write(f"| Lotka exponent (beta) | {lotka['beta']:.3f} |\n")
            f.write(f"| Lotka R-squared | {lotka['r_squared']:.3f} |\n")

        f.write(f"\n## Author Productivity Distribution\n\n")
        f.write("| Papers | Authors | Cumulative % |\n")
        f.write("|--------|---------|-------------|\n")
        cumsum = 0
        for n in ns_sorted[:15]:  # First 15 rows
            cumsum += freq_of_freq[n]
            f.write(
                f"| {n} | {freq_of_freq[n]} | {cumsum/total_unique_authors*100:.1f}% |\n"
            )
        if len(ns_sorted) > 15:
            remaining = total_unique_authors - cumsum
            f.write(f"| >{ns_sorted[14]} | {remaining} | 100.0% |\n")

    logger.info(f"Saved author summary to {summary_path}")

    # --- Results dict ---
    results = {
        "total_unique_authors": total_unique_authors,
        "papers_with_authors": papers_with_authors,
        "collaboration_index": round(collab_index, 2),
        "single_paper_authors": single_paper_authors,
        "multi_paper_authors": multi_paper_authors,
        "single_multi_ratio": round(single_multi_ratio, 2),
        "top5_authors": author_counter.most_common(5),
        "lotka_beta": lotka.get("beta"),
        "lotka_r_squared": lotka.get("r_squared"),
    }
    return results


def main():
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python author_analysis.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = analyze_authors(papers)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
