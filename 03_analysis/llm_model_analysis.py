#!/usr/bin/env python3
"""
LLM Model Analysis
- Classify which LLM models are mentioned in each paper (title + abstract)
- Bar chart of model frequencies
- Proprietary vs open-source split
- Trend over time: which models are rising/falling by year
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
# LLM model definitions: model_name -> list of compiled regex patterns
# ---------------------------------------------------------------------------
LLM_MODELS: Dict[str, List[re.Pattern]] = {
    "GPT-4o": [
        re.compile(r"\bGPT-?4o\b", re.IGNORECASE),
    ],
    "GPT-4": [
        re.compile(r"\bGPT-?4\b(?!o)", re.IGNORECASE),
    ],
    "GPT-3.5": [
        re.compile(r"\bGPT-?3\.?5\b", re.IGNORECASE),
    ],
    "GPT-5": [
        re.compile(r"\bGPT-?5\b", re.IGNORECASE),
    ],
    "ChatGPT (generic)": [
        re.compile(r"\bChatGPT\b", re.IGNORECASE),
    ],
    "Claude": [
        re.compile(r"\bClaude\b"),
    ],
    "Gemini": [
        re.compile(r"\bGemini\b", re.IGNORECASE),
    ],
    "Llama": [
        re.compile(r"\bLlama\b", re.IGNORECASE),
        re.compile(r"\bLLaMA\b"),
    ],
    "Med-PaLM": [
        re.compile(r"\bMed-?PaLM\b", re.IGNORECASE),
    ],
    "Mistral": [
        re.compile(r"\bMistral\b", re.IGNORECASE),
    ],
}

# "Generic LLM" is a fallback when no specific model matched
GENERIC_LLM_PATTERNS: List[re.Pattern] = [
    re.compile(r"\blarge language model\b", re.IGNORECASE),
    re.compile(r"\bLLM\b"),
]

# Proprietary vs open-source classification
PROPRIETARY_MODELS = {"ChatGPT (generic)", "GPT-4", "GPT-4o", "GPT-3.5", "GPT-5",
                       "Claude", "Gemini", "Med-PaLM"}
OPEN_SOURCE_MODELS = {"Llama", "Mistral"}


def _get_text(paper: Dict) -> str:
    """Concatenate title and abstract into a single searchable string."""
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    return f"{title} {abstract}"


def classify_papers(papers: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, int]]:
    """
    Classify papers by LLM model mentions.
    Returns:
        model_papers: {model: [paper, ...]}
        model_counts: {model: int}
    """
    model_papers: Dict[str, List[Dict]] = defaultdict(list)
    model_counts: Counter = Counter()

    for paper in papers:
        text = _get_text(paper)
        matched_any_specific = False

        # Check specific models first (order matters for GPT-4o vs GPT-4)
        for model, patterns in LLM_MODELS.items():
            if any(pat.search(text) for pat in patterns):
                # For ChatGPT (generic), only count if the match isn't part of a
                # version-specific mention like "ChatGPT-4" that would also
                # match GPT-4. We still count it as a generic mention.
                model_papers[model].append(paper)
                model_counts[model] += 1
                matched_any_specific = True

        # Generic LLM fallback
        if not matched_any_specific:
            if any(pat.search(text) for pat in GENERIC_LLM_PATTERNS):
                model_papers["Generic LLM"].append(paper)
                model_counts["Generic LLM"] += 1

    return dict(model_papers), dict(model_counts)


def plot_model_frequencies(model_counts: Dict[str, int], fig_dir: Path) -> None:
    """Vertical bar chart of LLM model mention frequencies."""
    models = sorted(model_counts.keys(), key=lambda m: model_counts[m], reverse=True)
    counts = [model_counts[m] for m in models]

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = []
    for m in models:
        if m in PROPRIETARY_MODELS:
            colors.append("#4C72B0")  # blue for proprietary
        elif m in OPEN_SOURCE_MODELS:
            colors.append("#55A868")  # green for open-source
        else:
            colors.append("#C4C4C4")  # grey for generic

    bars = ax.bar(range(len(models)), counts, color=colors, edgecolor="grey",
                  linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.01,
                str(count), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=40, ha="right", fontsize=10)
    ax.set_ylabel("Number of Papers", fontsize=12)
    ax.set_title("LLM Model Mentions in Corpus (Title + Abstract)", fontsize=14,
                 fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend for proprietary vs open-source
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4C72B0", edgecolor="grey", label="Proprietary"),
        Patch(facecolor="#55A868", edgecolor="grey", label="Open-source"),
        Patch(facecolor="#C4C4C4", edgecolor="grey", label="Generic / Unspecified"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()
    out = fig_dir / "llm_model_frequencies.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_proprietary_vs_open(model_papers: Dict[str, List[Dict]],
                              total_papers: int, fig_dir: Path) -> None:
    """Pie chart showing proprietary vs open-source vs generic vs no-mention split."""
    prop_ids = set()
    open_ids = set()
    generic_ids = set()

    for model, papers in model_papers.items():
        ids = {p.get("id") or p.get("doi") or p.get("title") for p in papers}
        if model in PROPRIETARY_MODELS:
            prop_ids |= ids
        elif model in OPEN_SOURCE_MODELS:
            open_ids |= ids
        elif model == "Generic LLM":
            generic_ids |= ids

    # Papers mentioning both proprietary and open-source
    both_ids = prop_ids & open_ids
    prop_only = len(prop_ids - open_ids - generic_ids)
    open_only = len(open_ids - prop_ids - generic_ids)
    both_count = len(both_ids)
    generic_only = len(generic_ids - prop_ids - open_ids)
    no_mention = total_papers - len(prop_ids | open_ids | generic_ids)

    labels = ["Proprietary only", "Open-source only", "Both", "Generic LLM only",
              "No LLM mention"]
    sizes = [prop_only, open_only, both_count, generic_only, no_mention]
    colors_pie = ["#4C72B0", "#55A868", "#DD8452", "#C4C4C4", "#F0F0F0"]

    # Filter out zero slices
    filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors_pie) if s > 0]
    if not filtered:
        logger.warning("No data for proprietary vs open-source chart")
        return
    labels_f, sizes_f, colors_f = zip(*filtered)

    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        sizes_f, labels=labels_f, colors=colors_f, autopct="%1.1f%%",
        startangle=140, pctdistance=0.85, textprops={"fontsize": 10})
    for autotext in autotexts:
        autotext.set_fontweight("bold")
    ax.set_title("Proprietary vs Open-Source LLM Mentions", fontsize=14,
                 fontweight="bold")

    plt.tight_layout()
    out = fig_dir / "llm_proprietary_vs_opensource.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_trend_over_time(model_papers: Dict[str, List[Dict]], fig_dir: Path) -> None:
    """Line chart showing model mention trends by year."""
    # Collect year data per model
    model_year_counts: Dict[str, Counter] = {}
    all_years: set = set()

    for model, papers in model_papers.items():
        if model == "Generic LLM":
            continue  # skip generic for trend plot to avoid clutter
        year_counts = Counter()
        for p in papers:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                year_counts[int(y)] += 1
                all_years.add(int(y))
        if year_counts:
            model_year_counts[model] = year_counts

    if not all_years or not model_year_counts:
        logger.warning("No year data for trend analysis")
        return

    years = sorted(all_years)

    # Sort models by total count descending
    model_totals = {m: sum(yc.values()) for m, yc in model_year_counts.items()}
    top_models = sorted(model_totals, key=lambda m: model_totals[m], reverse=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    markers = ["o", "s", "D", "^", "v", "<", ">", "p", "*", "h"]
    color_cycle = plt.cm.tab10(np.linspace(0, 1, len(top_models)))

    for idx, model in enumerate(top_models):
        yc = model_year_counts[model]
        values = [yc.get(y, 0) for y in years]
        ax.plot(years, values, marker=markers[idx % len(markers)],
                color=color_cycle[idx], linewidth=2, markersize=7, label=model)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Papers", fontsize=12)
    ax.set_title("LLM Model Mention Trends Over Time", fontsize=14, fontweight="bold")
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=10)
    ax.legend(loc="upper left", fontsize=9, ncol=2, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out = fig_dir / "llm_model_trends.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_summary_table(model_counts: Dict[str, int], model_papers: Dict[str, List[Dict]],
                        total_papers: int, table_dir: Path) -> None:
    """Save a markdown summary table of LLM model classification."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"llm_model_summary_{ts}.md"

    lines = [
        "# LLM Model Classification Summary",
        "",
        f"Total papers analysed: **{total_papers}**",
        "",
        "## Model Frequencies",
        "",
        "| Model | Count | % of Corpus | Category |",
        "|-------|------:|------------:|----------|",
    ]

    for model in sorted(model_counts, key=lambda m: model_counts[m], reverse=True):
        count = model_counts[model]
        pct = count / total_papers * 100 if total_papers else 0
        if model in PROPRIETARY_MODELS:
            cat = "Proprietary"
        elif model in OPEN_SOURCE_MODELS:
            cat = "Open-source"
        else:
            cat = "Generic"
        lines.append(f"| {model} | {count} | {pct:.1f}% | {cat} |")

    # Proprietary vs open-source summary
    prop_ids = set()
    open_ids = set()
    for model, papers in model_papers.items():
        ids = {p.get("id") for p in papers}
        if model in PROPRIETARY_MODELS:
            prop_ids |= ids
        elif model in OPEN_SOURCE_MODELS:
            open_ids |= ids

    lines += [
        "",
        "## Proprietary vs Open-Source Summary",
        "",
        f"- Papers mentioning **any proprietary** model: {len(prop_ids)} "
        f"({len(prop_ids)/total_papers*100:.1f}%)",
        f"- Papers mentioning **any open-source** model: {len(open_ids)} "
        f"({len(open_ids)/total_papers*100:.1f}%)",
        f"- Papers mentioning **both**: {len(prop_ids & open_ids)}",
        "",
    ]

    # Year breakdown
    lines += ["## Trends by Year", "", "| Year |"]
    all_models = sorted(model_counts.keys())
    lines[-1] += " | ".join(all_models) + " |"
    lines.append("|------|" + "|".join(["-----:" for _ in all_models]) + "|")

    all_years = set()
    for papers in model_papers.values():
        for p in papers:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                all_years.add(int(y))

    for year in sorted(all_years):
        row = f"| {year} |"
        for model in all_models:
            c = sum(1 for p in model_papers.get(model, [])
                    if p.get("year") == year)
            row += f" {c} |"
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

    model_papers, model_counts = classify_papers(papers)

    logger.info("LLM model mention counts:")
    for model in sorted(model_counts, key=lambda m: model_counts[m], reverse=True):
        logger.info("  %-25s %d", model, model_counts[model])

    plot_model_frequencies(model_counts, fig_dir)
    plot_proprietary_vs_open(model_papers, len(papers), fig_dir)
    plot_trend_over_time(model_papers, fig_dir)
    save_summary_table(model_counts, model_papers, len(papers), table_dir)

    logger.info("LLM model analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
