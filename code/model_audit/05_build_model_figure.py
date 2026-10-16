#!/usr/bin/env python3
"""Build publication-ready Figure 6 for the corrected model inventory."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path('controlled_source/LLM_Study_FIXED_WINDOWS_TESTED')
DATA = ROOT / (
    r"ACTIVE_GSE_REVISION_2026-08-13\99_QA\model_inventory_fulltext_20260825"
    r"\corrected_inventory"
)
OUT = DATA / "figure_6"

COLOUR_NONREVIEW = "#315B7D"
COLOUR_REVIEW = "#74A8A2"
COLOUR_UNRESOLVED = "#A7ADB4"
TEXT = "#26323D"
GRID = "#DDE2E7"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wrap_label(value: str) -> str:
    replacements = {
        "ChatGPT (version unspecified)": "ChatGPT\n(version unspecified)",
        "Other named model/system": "Other named\nmodel/system",
        "OpenAI o-series": "OpenAI o-series",
    }
    return replacements.get(value, value)


def save_figure(fig: plt.Figure, stem: str) -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {
        "png": OUT / f"{stem}_600DPI.png",
        "svg": OUT / f"{stem}.svg",
        "eps": OUT / f"{stem}.eps",
    }
    fig.savefig(paths["png"], dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(paths["svg"], facecolor="white", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(paths["eps"], facecolor="white", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    with Image.open(paths["png"]) as image:
        preview_width = 1600
        preview_height = round(image.height * preview_width / image.width)
        preview = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
        paths["preview"] = OUT / f"{stem}_1600PX_QA.png"
        preview.save(paths["preview"])
    return paths


def build(analysis_n: int) -> dict[str, Path]:
    counts = read_csv(DATA / f"CORRECTED_MODEL_FAMILY_COUNTS_N{analysis_n}.csv")
    coverage = read_csv(DATA / f"MODEL_IDENTITY_COVERAGE_N{analysis_n}.csv")
    named = next(row for row in coverage if row["identity_status"].startswith("Named family"))
    unresolved = next(row for row in coverage if row["identity_status"].startswith("No named"))

    plotted = [row for row in counts if row["model_family"] != "unspecified_generative_model"]
    plotted.sort(key=lambda row: (-int(row["publications"]), row["display_label"]))

    # Intended display width is the 6.2-inch manuscript text block.
    fig = plt.figure(figsize=(6.2, 8.35))
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=[1.05, 7.3],
        hspace=0.16,
        left=0.40,
        right=0.965,
        top=0.975,
        bottom=0.075,
    )
    coverage_ax = fig.add_subplot(grid[0])
    families_ax = fig.add_subplot(grid[1])

    # Panel A: record-level coverage, mutually exclusive.
    named_n = int(named["publications"])
    unresolved_n = int(unresolved["publications"])
    coverage_ax.barh([0], [named_n], color=COLOUR_NONREVIEW, height=0.46)
    coverage_ax.barh([0], [unresolved_n], left=[named_n], color=COLOUR_UNRESOLVED, height=0.46)
    coverage_ax.set_xlim(0, analysis_n)
    coverage_ax.set_ylim(-0.65, 0.65)
    coverage_ax.set_yticks([])
    coverage_ax.set_xticks([])
    coverage_ax.spines[:].set_visible(False)
    coverage_ax.set_title(
        "A   Model-family identity established from available evidence",
        loc="left",
        fontsize=10.1,
        fontweight="bold",
        color=TEXT,
        pad=4,
    )
    coverage_ax.text(
        named_n / 2,
        0,
        f"Named family\n{named_n} ({100 * named_n / analysis_n:.1f}%)",
        ha="center",
        va="center",
        fontsize=8.2,
        color="white",
        fontweight="bold",
        linespacing=1.1,
    )
    coverage_ax.text(
        named_n + unresolved_n / 2,
        0,
        f"Not established\n{unresolved_n} ({100 * unresolved_n / analysis_n:.1f}%)",
        ha="center",
        va="center",
        fontsize=8.0,
        color="#2F3740",
        fontweight="bold",
        linespacing=1.1,
    )

    # Panel B: every controlled named family with a non-zero count.
    y = np.arange(len(plotted))
    non_review = np.array([int(row["non_review_publications"]) for row in plotted])
    reviews = np.array([int(row["evidence_review_publications"]) for row in plotted])
    totals = non_review + reviews
    families_ax.barh(y, non_review, color=COLOUR_NONREVIEW, height=0.66, label="Empirical, methods or other publications")
    families_ax.barh(y, reviews, left=non_review, color=COLOUR_REVIEW, height=0.66, label="Evidence reviews")
    families_ax.set_yticks(y, [wrap_label(row["display_label"]) for row in plotted], fontsize=8.15)
    families_ax.invert_yaxis()
    xmax = int(np.ceil((max(totals) + 9) / 10) * 10)
    families_ax.set_xlim(0, xmax)
    families_ax.set_xticks(np.arange(0, xmax + 1, 20))
    families_ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.8)
    families_ax.set_axisbelow(True)
    families_ax.spines[["top", "right", "left"]].set_visible(False)
    families_ax.spines["bottom"].set_color("#8E979F")
    families_ax.tick_params(axis="y", length=0, pad=5)
    families_ax.tick_params(axis="x", labelsize=8.0)
    families_ax.set_xlabel(
        f"Publications (analysis set n={analysis_n}; model families are non-exclusive)",
        fontsize=9.0,
        labelpad=7,
    )
    families_ax.set_title(
        "B   Named model families represented in the corpus",
        loc="left",
        fontsize=10.1,
        fontweight="bold",
        color=TEXT,
        pad=6,
    )
    for bar_y, total in zip(y, totals):
        families_ax.text(
            float(total) + 1.4,
            float(bar_y),
            str(int(total)),
            va="center",
            ha="left",
            fontsize=8.1,
            color=TEXT,
        )
    families_ax.legend(
        loc="lower right",
        bbox_to_anchor=(1.0, 0.012),
        frameon=False,
        ncol=2,
        fontsize=7.45,
        handlelength=1.4,
        columnspacing=1.25,
        handletextpad=0.45,
    )

    stem = f"FIGURE_6_CORRECTED_MODEL_FAMILIES_N{analysis_n}"
    paths = save_figure(fig, stem)

    plotted_path = OUT / f"{stem}_PLOTTED_DATA.csv"
    with plotted_path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = [
            "model_family",
            "display_label",
            "publications",
            "percent_of_analysis_set",
            "non_review_publications",
            "evidence_review_publications",
            "analysis_set_n",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(plotted)

    caption = (
        f"Fig. 6 Model-family reporting and named families represented across {analysis_n} studies after the model re-audit. "
        f"Panel A shows whether at least one named family was established from the evidence available to the review; ‘not established’ does not mean that an article’s full text failed to name a model. "
        "Panel B shows publication-level family counts, separated into evidence reviews and other publication types. Families are non-exclusive, and a count from an evidence review indicates substantive synthesis rather than model deployment by the review authors. "
        "‘Other named model/system’ groups named systems outside the predefined categories."
    )
    caption_path = OUT / f"{stem}_CAPTION.txt"
    caption_path.write_text(caption + "\n", encoding="utf-8")

    manifest_path = OUT / f"{stem}_MANIFEST.txt"
    manifest_lines = [
        f"analysis_n={analysis_n}",
        f"named_family_established={named_n}",
        f"not_established={unresolved_n}",
        f"family_rows={len(plotted)}",
        f"source_counts_sha256={sha256(DATA / f'CORRECTED_MODEL_FAMILY_COUNTS_N{analysis_n}.csv')}",
        f"source_coverage_sha256={sha256(DATA / f'MODEL_IDENTITY_COVERAGE_N{analysis_n}.csv')}",
        f"plotted_data_sha256={sha256(plotted_path)}",
        f"png_sha256={sha256(paths['png'])}",
        f"svg_sha256={sha256(paths['svg'])}",
        f"eps_sha256={sha256(paths['eps'])}",
        f"preview_sha256={sha256(paths['preview'])}",
        f"caption_sha256={sha256(caption_path)}",
    ]
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    paths["plotted_data"] = plotted_path
    paths["caption"] = caption_path
    paths["manifest"] = manifest_path
    return paths


def main() -> None:
    outputs = {analysis_n: build(analysis_n) for analysis_n in (485, 483)}
    for analysis_n, paths in outputs.items():
        print(f"n={analysis_n}")
        for key, path in paths.items():
            print(f"  {key}: {path}")


if __name__ == "__main__":
    main()
