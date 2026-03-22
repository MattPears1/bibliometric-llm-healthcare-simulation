#!/usr/bin/env python3
"""
PRISMA 2020 Flow Diagram Generator
Generates a publication-quality PRISMA flow diagram using matplotlib.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def create_prisma_diagram(
    n_databases=7,
    db_counts=None,
    n_raw=92941,
    n_duplicates=11940,
    n_unique=81001,
    n_screened=81001,
    n_excluded_screen=69472,
    n_included=11529,
    n_tier1=5810,
    n_tier2=489,
    n_tier3=2827,
    n_uncertain=8213,
    output_path=None,
):
    """Create PRISMA 2020 flow diagram."""
    if output_path is None:
        output_path = Path(__file__).parent / "figures" / "prisma_flow.png"

    if db_counts is None:
        db_counts = {
            "OpenAlex": 49068,
            "Europe PMC": 18721,
            "Crossref": 19219,
            "CORE": 2134,
            "PubMed": 1066,
            "Semantic Scholar": "~2000",
            "DOAJ": 41,
        }

    fig, ax = plt.subplots(figsize=(14, 16))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Colors
    id_color = "#E3F2FD"  # Light blue - identification
    sc_color = "#FFF3E0"  # Light orange - screening
    inc_color = "#E8F5E9"  # Light green - included
    exc_color = "#FFEBEE"  # Light red - excluded
    border = "#333333"

    def add_box(x, y, w, h, text, color, fontsize=9, bold=False):
        rect = mpatches.FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.3",
            facecolor=color, edgecolor=border, linewidth=1.5
        )
        ax.add_patch(rect)
        weight = "bold" if bold else "normal"
        ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
                fontweight=weight, wrap=True,
                bbox=dict(facecolor="none", edgecolor="none"))

    def add_arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=border, lw=1.5))

    # Title
    ax.text(50, 98, "PRISMA 2020 Flow Diagram", ha="center", va="center",
            fontsize=16, fontweight="bold")

    # === IDENTIFICATION ===
    ax.text(8, 93, "IDENTIFICATION", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#1565C0", rotation=90)

    # Database box
    db_text = f"Records identified from\n7 databases (n = {n_raw:,})\n\n"
    for db, count in db_counts.items():
        if isinstance(count, int):
            db_text += f"  {db}: {count:,}\n"
        else:
            db_text += f"  {db}: {count}\n"
    add_box(40, 88, 35, 14, db_text, id_color, fontsize=8)

    # Duplicates removed
    add_arrow(40, 81, 40, 76)
    add_box(72, 78, 22, 5, f"Duplicates removed\n(n = {n_duplicates:,}, {n_duplicates/n_raw*100:.1f}%)", exc_color, fontsize=8)
    add_arrow(57, 82, 61, 78)

    # === SCREENING ===
    ax.text(8, 65, "SCREENING", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#E65100", rotation=90)

    # Records screened
    add_box(40, 70, 30, 6, f"Records screened\n(n = {n_unique:,})", sc_color, fontsize=9, bold=True)
    add_arrow(40, 76, 40, 73)

    # Stage 1 excluded
    add_box(72, 64, 22, 6, f"Excluded by keyword\nscreening (n = {n_excluded_screen:,})", exc_color, fontsize=8)
    add_arrow(55, 68, 61, 64)

    # Stage 1 result
    add_arrow(40, 67, 40, 58)
    add_box(40, 55, 30, 6, f"Papers after Stage 1 screening\n(n = {n_included:,})", sc_color, fontsize=9)

    # Uncertain papers note
    add_box(72, 52, 22, 5, f"Including {n_uncertain:,} uncertain\npapers for AI review", "#FFF9C4", fontsize=8)
    add_arrow(55, 53, 61, 52)

    # === INCLUDED ===
    ax.text(8, 35, "INCLUDED", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#2E7D32", rotation=90)

    add_arrow(40, 52, 40, 44)

    # Tier boxes
    add_box(20, 38, 22, 8,
            f"Tier 1: LLM + Medical\n(broadest scope)\nn = {n_tier1:,}",
            inc_color, fontsize=9, bold=True)

    add_box(50, 38, 22, 8,
            f"Tier 2: + Simulation\n(core scope)\nn = {n_tier2:,}",
            "#C8E6C9", fontsize=9, bold=True)

    add_box(80, 38, 22, 8,
            f"Tier 3: + NTS\n(focused scope)\nn = {n_tier3:,}",
            "#A5D6A7", fontsize=9, bold=True)

    add_arrow(30, 44, 20, 42)
    add_arrow(40, 44, 50, 42)
    add_arrow(50, 44, 80, 42)

    # Final included
    add_box(50, 26, 40, 6,
            f"Total included in bibliometric analysis: n = {n_included:,}",
            "#66BB6A", fontsize=11, bold=True)
    add_arrow(50, 34, 50, 29)

    # Analysis note
    add_box(50, 16, 45, 8,
            "Analyses performed:\n"
            "Publication trends | Citation analysis | Lotka's & Bradford's laws\n"
            "Geographic distribution | Keyword co-occurrence | Callon's strategic diagram\n"
            "NTS domain classification | LLM model analysis | Urology sub-analysis",
            "#E8EAF6", fontsize=8)
    add_arrow(50, 23, 50, 20)

    plt.savefig(str(output_path), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"PRISMA diagram saved to {output_path}")
    return str(output_path)


if __name__ == "__main__":
    create_prisma_diagram()
