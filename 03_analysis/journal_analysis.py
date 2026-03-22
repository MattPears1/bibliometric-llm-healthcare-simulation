#!/usr/bin/env python3
"""
Journal / Source Analysis
=========================
Bibliometric analysis of journal/source distribution:
- Papers per journal, top 20 journals bar chart
- Bradford's law of scattering: zones of journal productivity
  * Zone 1 (core): fewest journals producing the first 1/3 of papers
  * Zone 2 (middle): next 1/3 of papers
  * Zone 3 (peripheral): remaining 1/3
  * Bradford multiplier: ratio of journal counts between adjacent zones
- Publication type distribution (pie/bar chart)
"""

import json
import logging
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bradford's law
# ---------------------------------------------------------------------------

def compute_bradford_zones(
    journal_paper_counts: Counter,
) -> Dict:
    """Partition journals into three Bradford zones.

    Journals are sorted in descending order of productivity (paper count).
    Zone 1 (core) contains the fewest journals that together produce roughly
    the first third of total papers. Zone 2 covers the next third, Zone 3 the rest.

    Returns a dict with zone assignments, multipliers, and summary data.
    """
    if not journal_paper_counts:
        return {"error": "No journal data"}

    total_papers = sum(journal_paper_counts.values())
    one_third = total_papers / 3

    # Sort journals by descending paper count
    sorted_journals = journal_paper_counts.most_common()

    zones: Dict[str, List[Tuple[str, int]]] = {"zone1": [], "zone2": [], "zone3": []}
    cumulative = 0
    current_zone = "zone1"

    for journal, count in sorted_journals:
        cumulative += count
        zones[current_zone].append((journal, count))
        if current_zone == "zone1" and cumulative >= one_third:
            current_zone = "zone2"
        elif current_zone == "zone2" and cumulative >= 2 * one_third:
            current_zone = "zone3"

    n1 = len(zones["zone1"])
    n2 = len(zones["zone2"])
    n3 = len(zones["zone3"])

    p1 = sum(c for _, c in zones["zone1"])
    p2 = sum(c for _, c in zones["zone2"])
    p3 = sum(c for _, c in zones["zone3"])

    # Bradford multipliers
    mult_1_2 = n2 / n1 if n1 > 0 else None
    mult_2_3 = n3 / n2 if n2 > 0 else None

    return {
        "zones": zones,
        "zone_journal_counts": {"zone1": n1, "zone2": n2, "zone3": n3},
        "zone_paper_counts": {"zone1": p1, "zone2": p2, "zone3": p3},
        "total_journals": n1 + n2 + n3,
        "total_papers": total_papers,
        "multiplier_1_2": round(mult_1_2, 2) if mult_1_2 is not None else None,
        "multiplier_2_3": round(mult_2_3, 2) if mult_2_3 is not None else None,
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_journals(papers: List[Dict], output_dir: str = None) -> Dict:
    """Run journal/source analysis and save figures + tables."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    fig_dir = Path(output_dir) / "figures"
    table_dir = Path(output_dir) / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    # --- Count papers per journal ---
    journal_counter = Counter()
    type_counter = Counter()
    no_journal_count = 0

    for paper in papers:
        journal = paper.get("journal", "").strip()
        if journal:
            journal_counter[journal] += 1
        else:
            no_journal_count += 1

        ptype = paper.get("type", "").strip()
        if ptype:
            type_counter[ptype] += 1
        else:
            type_counter["(not specified)"] += 1

    total_journals = len(journal_counter)
    papers_with_journal = sum(journal_counter.values())

    logger.info(
        f"Journals: {total_journals} unique sources, "
        f"{papers_with_journal} papers with journal data, "
        f"{no_journal_count} without"
    )

    # --- Bradford's law ---
    bradford = compute_bradford_zones(journal_counter)
    if "error" not in bradford:
        logger.info(
            f"Bradford zones: Z1={bradford['zone_journal_counts']['zone1']} journals "
            f"({bradford['zone_paper_counts']['zone1']} papers), "
            f"Z2={bradford['zone_journal_counts']['zone2']} journals "
            f"({bradford['zone_paper_counts']['zone2']} papers), "
            f"Z3={bradford['zone_journal_counts']['zone3']} journals "
            f"({bradford['zone_paper_counts']['zone3']} papers), "
            f"multipliers: {bradford['multiplier_1_2']}, {bradford['multiplier_2_3']}"
        )

    # --- Figure 1: Top 20 journals bar chart ---
    top20 = journal_counter.most_common(20)
    if top20:
        top_names = [t[0] for t in top20][::-1]
        top_counts = [t[1] for t in top20][::-1]

        # Truncate long journal names for display
        display_names = []
        for name in top_names:
            if len(name) > 50:
                display_names.append(name[:47] + "...")
            else:
                display_names.append(name)

        fig, ax = plt.subplots(figsize=(12, 9))
        bars = ax.barh(
            range(len(display_names)), top_counts,
            color="#2196F3", edgecolor="white", alpha=0.85,
        )
        ax.set_yticks(range(len(display_names)))
        ax.set_yticklabels(display_names, fontsize=9)
        ax.set_xlabel("Number of Papers", fontsize=12)
        ax.set_title("Top 20 Journals / Sources", fontsize=13, fontweight="bold")

        for bar, count in zip(bars, top_counts):
            ax.text(
                bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9,
            )

        plt.tight_layout()
        plt.savefig(fig_dir / "top_journals.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved top_journals.png")

    # --- Figure 2: Bradford's law cumulative plot ---
    if "error" not in bradford:
        sorted_journals = journal_counter.most_common()
        cum_papers = np.cumsum([c for _, c in sorted_journals])
        journal_rank = np.arange(1, len(sorted_journals) + 1)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(
            np.log10(journal_rank), cum_papers,
            "-", color="#4CAF50", linewidth=2,
        )
        ax.set_xlabel("log₁₀(Journal Rank)", fontsize=12)
        ax.set_ylabel("Cumulative Papers", fontsize=12)
        ax.set_title("Bradford's Law: Cumulative Paper Distribution", fontsize=13, fontweight="bold")

        # Mark zone boundaries
        z1_n = bradford["zone_journal_counts"]["zone1"]
        z2_n = bradford["zone_journal_counts"]["zone2"]
        z1_boundary = z1_n
        z2_boundary = z1_n + z2_n

        for boundary, label, color in [
            (z1_boundary, "Zone 1 | Zone 2", "#FF9800"),
            (z2_boundary, "Zone 2 | Zone 3", "#F44336"),
        ]:
            if boundary < len(journal_rank):
                ax.axvline(
                    x=np.log10(boundary), color=color,
                    linestyle="--", linewidth=1.5, alpha=0.7,
                )
                ax.text(
                    np.log10(boundary) + 0.02, cum_papers[-1] * 0.5,
                    label, color=color, fontsize=9, rotation=90, va="center",
                )

        # Annotate zone stats
        textstr = (
            f"Zone 1 (core): {z1_n} journals, {bradford['zone_paper_counts']['zone1']} papers\n"
            f"Zone 2 (middle): {z2_n} journals, {bradford['zone_paper_counts']['zone2']} papers\n"
            f"Zone 3 (peripheral): {bradford['zone_journal_counts']['zone3']} journals, "
            f"{bradford['zone_paper_counts']['zone3']} papers\n"
            f"Multiplier Z1→Z2: {bradford['multiplier_1_2']}\n"
            f"Multiplier Z2→Z3: {bradford['multiplier_2_3']}"
        )
        props = dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8)
        ax.text(
            0.03, 0.97, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment="top", horizontalalignment="left", bbox=props,
        )

        plt.tight_layout()
        plt.savefig(fig_dir / "bradford_law.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved bradford_law.png")

    # --- Figure 3: Publication type distribution ---
    if type_counter:
        # Use bar chart if many types, pie chart if few
        sorted_types = type_counter.most_common()
        type_labels = [t[0] for t in sorted_types]
        type_counts = [t[1] for t in sorted_types]

        if len(sorted_types) <= 8:
            # Pie chart
            fig, ax = plt.subplots(figsize=(9, 7))
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_types)))
            wedges, texts, autotexts = ax.pie(
                type_counts, labels=None, autopct="%1.1f%%",
                colors=colors, startangle=140, pctdistance=0.85,
            )
            ax.legend(
                wedges, [f"{l} (n={c})" for l, c in zip(type_labels, type_counts)],
                loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9,
            )
            ax.set_title("Publication Type Distribution", fontsize=13, fontweight="bold")
        else:
            # Horizontal bar chart for many types
            display_labels = type_labels[::-1]
            display_counts = type_counts[::-1]
            fig, ax = plt.subplots(figsize=(10, max(6, len(sorted_types) * 0.4)))
            ax.barh(
                range(len(display_labels)), display_counts,
                color="#FF9800", edgecolor="white", alpha=0.85,
            )
            ax.set_yticks(range(len(display_labels)))
            ax.set_yticklabels(display_labels, fontsize=9)
            ax.set_xlabel("Number of Papers", fontsize=12)
            ax.set_title("Publication Type Distribution", fontsize=13, fontweight="bold")
            for i, count in enumerate(display_counts):
                ax.text(count + 0.3, i, str(count), va="center", fontsize=9)

        plt.tight_layout()
        plt.savefig(fig_dir / "publication_types.png", dpi=300, bbox_inches="tight")
        plt.close()
        logger.info("Saved publication_types.png")

    # --- Tables ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Table: top 20 journals
    table_path = table_dir / f"journal_top20_{timestamp}.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# Top 20 Journals / Sources\n\n")
        f.write("| Rank | Journal | Papers | % of Total |\n")
        f.write("|------|---------|--------|------------|\n")
        for rank, (journal, count) in enumerate(journal_counter.most_common(20), 1):
            pct = count / papers_with_journal * 100 if papers_with_journal else 0
            f.write(f"| {rank} | {journal} | {count} | {pct:.1f}% |\n")
    logger.info(f"Saved top-20 journals table to {table_path}")

    # Table: Bradford zones
    if "error" not in bradford:
        bradford_path = table_dir / f"bradford_zones_{timestamp}.md"
        with open(bradford_path, "w", encoding="utf-8") as f:
            f.write("# Bradford's Law Zones\n\n")
            f.write("| Zone | Description | Journals | Papers | % Papers |\n")
            f.write("|------|-------------|----------|--------|----------|\n")
            for zone, desc in [
                ("zone1", "Core"),
                ("zone2", "Middle"),
                ("zone3", "Peripheral"),
            ]:
                nj = bradford["zone_journal_counts"][zone]
                np_ = bradford["zone_paper_counts"][zone]
                pct = np_ / bradford["total_papers"] * 100 if bradford["total_papers"] else 0
                f.write(f"| {zone.replace('zone', 'Zone ')} | {desc} | {nj} | {np_} | {pct:.1f}% |\n")

            f.write(f"\n**Total journals:** {bradford['total_journals']}\n")
            f.write(f"**Total papers (with journal):** {bradford['total_papers']}\n")
            f.write(f"**Bradford multiplier Z1 → Z2:** {bradford['multiplier_1_2']}\n")
            f.write(f"**Bradford multiplier Z2 → Z3:** {bradford['multiplier_2_3']}\n")

            # List core journals (Zone 1)
            f.write(f"\n## Zone 1 (Core) Journals\n\n")
            f.write("| Journal | Papers |\n")
            f.write("|---------|--------|\n")
            for journal, count in bradford["zones"]["zone1"]:
                f.write(f"| {journal} | {count} |\n")

        logger.info(f"Saved Bradford zones table to {bradford_path}")

    # Table: journal summary
    summary_path = table_dir / f"journal_summary_{timestamp}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Journal / Source Analysis Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total unique journals/sources | {total_journals} |\n")
        f.write(f"| Papers with journal data | {papers_with_journal} |\n")
        f.write(f"| Papers without journal data | {no_journal_count} |\n")
        if journal_counter:
            top_journal, top_count = journal_counter.most_common(1)[0]
            f.write(f"| Most prolific journal | {top_journal} ({top_count} papers) |\n")
        # Papers per journal stats
        ppj = list(journal_counter.values())
        if ppj:
            f.write(f"| Mean papers per journal | {np.mean(ppj):.2f} |\n")
            f.write(f"| Median papers per journal | {np.median(ppj):.0f} |\n")
            single_paper_journals = sum(1 for c in ppj if c == 1)
            f.write(
                f"| Single-paper journals | {single_paper_journals} "
                f"({single_paper_journals/total_journals*100:.1f}%) |\n"
            )

        f.write(f"\n## Publication Types\n\n")
        f.write("| Type | Count | % |\n")
        f.write("|------|-------|----|\n")
        total_typed = sum(type_counter.values())
        for ptype, count in type_counter.most_common():
            pct = count / total_typed * 100 if total_typed else 0
            f.write(f"| {ptype} | {count} | {pct:.1f}% |\n")

    logger.info(f"Saved journal summary to {summary_path}")

    # --- Results dict ---
    results = {
        "total_unique_journals": total_journals,
        "papers_with_journal": papers_with_journal,
        "papers_without_journal": no_journal_count,
        "top5_journals": journal_counter.most_common(5),
        "publication_types": type_counter.most_common(),
    }
    if "error" not in bradford:
        results["bradford_zone_journals"] = bradford["zone_journal_counts"]
        results["bradford_zone_papers"] = bradford["zone_paper_counts"]
        results["bradford_multiplier_1_2"] = bradford["multiplier_1_2"]
        results["bradford_multiplier_2_3"] = bradford["multiplier_2_3"]

    return results


def main():
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python journal_analysis.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = analyze_journals(papers)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
