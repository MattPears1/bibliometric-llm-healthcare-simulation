from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "analysis_output" / "NTS_TOP18_COOCCURRENCE_MATRIX_LONG.csv"
OUTPUT = ROOT / "standalone_output"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUTPUT}")
    OUTPUT.mkdir(parents=True)

    rows = pd.read_csv(SOURCE)
    concepts = list(dict.fromkeys(rows["row_concept_id"].tolist()))
    labels_by_id = dict(zip(rows["row_concept_id"], rows["row_concept_label"]))
    labels = [labels_by_id[concept] for concept in concepts]
    n = len(concepts)
    if n != 18:
        raise ValueError(f"Expected 18 concepts, found {n}")

    rows["cooccurring_studies"] = rows["cooccurring_studies"].astype(int)
    diagonal = rows[rows["diagonal_frequency"].astype(str).str.lower().eq("true")]
    frequencies = dict(zip(diagonal["row_concept_id"], diagonal["cooccurring_studies"]))
    if set(frequencies) != set(concepts):
        raise ValueError("Diagonal frequencies do not cover every concept")

    pairs = rows[~rows["diagonal_frequency"].astype(str).str.lower().eq("true")]
    max_pair = max(1, int(pairs["cooccurring_studies"].max()))
    max_strength = max(0.01, float(pairs["cosine_normalised_strength"].max()))
    max_frequency = max(frequencies.values())

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 16,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )
    fig, ax = plt.subplots(figsize=(12.0, 9.4), facecolor="white")
    norm = Normalize(vmin=0, vmax=max_strength)
    cmap = plt.get_cmap("viridis")

    for row in rows.itertuples(index=False):
        i = concepts.index(row.row_concept_id)
        j = concepts.index(row.column_concept_id)
        raw = int(row.cooccurring_studies)
        is_diagonal = str(row.diagonal_frequency).lower() == "true"
        if is_diagonal:
            size = 120 + 920 * math.sqrt(raw / max_frequency)
            colour = "#59636E"
        else:
            size = 20 + 780 * math.sqrt(raw / max_pair) if raw else 9
            colour = cmap(norm(float(row.cosine_normalised_strength))) if raw else "#F2F3F5"
        ax.scatter(j, i, s=size, color=colour, edgecolor="white", linewidth=0.8, zorder=3)
        if is_diagonal or raw >= 5:
            ax.text(
                j,
                i,
                str(raw),
                ha="center",
                va="center",
                fontsize=8.2,
                color="white" if raw else "#666666",
                zorder=4,
            )

    ax.set_xlim(-0.65, n - 0.35)
    ax.set_ylim(n - 0.35, -0.65)
    ax.set_xticks(range(n), labels, rotation=48, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(n), labels)
    ax.tick_params(axis="both", length=0, labelsize=9.2)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#E4E7EB", linewidth=0.6)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_color("#B8BEC5")
        spine.set_linewidth(0.9)

    fig.suptitle(
        "Fine-grained non-technical skills concept co-occurrence",
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )
    ax.set_title(
        "Controlled title-and-abstract phrase analysis across 483 unique studies",
        loc="left",
        fontsize=11.5,
        color="#4A4A4A",
        pad=12,
    )

    cax = ax.inset_axes([0.63, 0.60, 0.30, 0.025])
    colour_bar = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=cax,
        orientation="horizontal",
    )
    colour_bar.set_label("Cosine-normalised co-occurrence", fontsize=8.4, labelpad=3)
    colour_bar.ax.tick_params(labelsize=7.7)

    size_values = sorted(set([5, min(15, max_pair), max_pair]))
    size_handles = [
        ax.scatter(
            [],
            [],
            s=20 + 780 * math.sqrt(value / max_pair),
            color="#8FA3B5",
            edgecolor="white",
            label=f"{value} studies",
        )
        for value in size_values
        if value > 0
    ]
    ax.legend(
        handles=size_handles,
        title="Off-diagonal bubble area",
        loc="upper right",
        bbox_to_anchor=(0.96, 0.965),
        frameon=False,
        fontsize=8.2,
        title_fontsize=8.5,
    )

    fig.subplots_adjust(left=0.205, right=0.975, top=0.90, bottom=0.245)
    fig.text(
        0.5,
        0.02,
        "Diagonal bubbles show individual concept frequency; off-diagonal bubbles show same-study co-occurrence. "
        "Absence of a title/abstract phrase does not establish absence from the full text.",
        ha="center",
        fontsize=9.0,
        color="#4A4A4A",
    )

    png = OUTPUT / "FIGURE_5_FINE_GRAINED_NTS_COOCCURRENCE_600DPI.png"
    svg = OUTPUT / "FIGURE_5_FINE_GRAINED_NTS_COOCCURRENCE.svg"
    eps = OUTPUT / "FIGURE_5_FINE_GRAINED_NTS_COOCCURRENCE.eps"
    fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    fig.savefig(eps, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    qa_dir = OUTPUT / "qa"
    qa_dir.mkdir()
    with Image.open(png) as image:
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        image.save(qa_dir / "FIGURE_5_FINE_GRAINED_NTS_COOCCURRENCE_1600PX_QA.png")

    caption = (
        "Fig. 5 Fine-grained non-technical-skills concept co-occurrence in the 483-study corpus. "
        "A controlled thesaurus was applied with binary whole counting to all 483 titles and the "
        "447 available abstracts. Diagonal bubbles show individual concept frequencies. Off-diagonal "
        "bubble area is proportional to the number of studies containing both concepts, and colour "
        "represents cosine-normalised co-occurrence. The matrix displays the 18 most frequent eligible "
        "concepts. These counts describe explicit title-and-abstract reporting; absence of a phrase "
        "does not establish absence of the skill from the full article.\n"
    )
    methods = (
        "A controlled non-technical-skills thesaurus comprising 78 concept groups and 303 exact lexical "
        "variants was applied to all 483 study titles and the 447 available abstracts. Text was "
        "Unicode-normalised and lowercased, with punctuation and hyphenation standardised. Exact phrase "
        "matching and binary whole counting were used; no stemming or fuzzy matching was applied. "
        "Same-study co-occurrence was calculated for the 18 most frequent eligible concepts.\n\n"
        + caption
    )
    (OUTPUT / "METHODS_AND_CAPTION.md").write_text(methods, encoding="utf-8")

    manifest_rows = []
    for path in sorted(p for p in OUTPUT.rglob("*") if p.is_file() and p.name != "OUTPUT_HASH_MANIFEST.csv"):
        manifest_rows.append(
            {
                "relative_path": path.relative_to(OUTPUT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    with (OUTPUT / "OUTPUT_HASH_MANIFEST.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)


if __name__ == "__main__":
    build()
