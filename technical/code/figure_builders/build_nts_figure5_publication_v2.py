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
ASSIGNMENTS_SOURCE = ROOT / "analysis_output" / "NTS_TITLE_ABSTRACT_CONCEPT_ASSIGNMENTS.csv"
SUMMARY_SOURCE = ROOT / "analysis_output" / "NTS_CONCEPT_SUMMARY_ALL.csv"
OUTPUT = ROOT / "publication_v4_tie_aware"
ELIGIBLE_CLASSES = {"umbrella", "core_skill", "training_process"}
MINIMUM_STUDIES = 7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bubble_area(raw: int, maximum: int) -> float:
    """Marker area scaled to retain visible separation at final print size."""
    return 8 + 300 * math.sqrt(raw / maximum)


def build() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUTPUT}")
    OUTPUT.mkdir(parents=True)

    assignments = pd.read_csv(ASSIGNMENTS_SOURCE)
    summary = pd.read_csv(SUMMARY_SOURCE)
    eligible = summary[
        summary["classification"].isin(ELIGIBLE_CLASSES)
        & (summary["study_count"].astype(int) >= MINIMUM_STUDIES)
    ].copy()
    eligible = eligible.sort_values(
        ["study_count", "concept_label"], ascending=[False, True]
    )
    concepts = eligible["concept_id"].tolist()
    labels_by_id = dict(zip(eligible["concept_id"], eligible["concept_label"]))
    labels = [labels_by_id[concept] for concept in concepts]
    n = len(concepts)
    if n != 19:
        raise ValueError(f"Expected 19 tie-aware concepts, found {n}")

    study_sets = {
        concept: set(
            assignments.loc[assignments["concept_id"].eq(concept), "paper_id"].astype(str)
        )
        for concept in concepts
    }
    matrix_rows = []
    for i, row_concept in enumerate(concepts):
        for j, column_concept in enumerate(concepts):
            if j > i:
                continue
            if i == j:
                raw = len(study_sets[row_concept])
                cosine = 1.0
                diagonal = True
            else:
                raw = len(study_sets[row_concept].intersection(study_sets[column_concept]))
                denominator = math.sqrt(
                    len(study_sets[row_concept]) * len(study_sets[column_concept])
                )
                cosine = raw / denominator if denominator else 0.0
                diagonal = False
            matrix_rows.append(
                {
                    "row_concept_id": row_concept,
                    "row_concept_label": labels_by_id[row_concept],
                    "column_concept_id": column_concept,
                    "column_concept_label": labels_by_id[column_concept],
                    "cooccurring_studies": raw,
                    "cosine_normalised_strength": round(cosine, 8),
                    "diagonal_frequency": diagonal,
                }
            )
    rows = pd.DataFrame(matrix_rows)
    rows.to_csv(
        OUTPUT / "NTS_TIE_AWARE_COOCCURRENCE_MATRIX_LONG.csv",
        index=False,
        encoding="utf-8-sig",
    )

    rows["cooccurring_studies"] = rows["cooccurring_studies"].astype(int)
    diagonal_mask = rows["diagonal_frequency"].astype(str).str.lower().eq("true")
    diagonal = rows[diagonal_mask]
    pairs = rows[~diagonal_mask]
    frequencies = dict(zip(diagonal["row_concept_id"], diagonal["cooccurring_studies"]))
    if set(frequencies) != set(concepts):
        raise ValueError("Diagonal frequencies do not cover every concept")

    max_pair = max(1, int(pairs["cooccurring_studies"].max()))
    max_strength = max(0.01, float(pairs["cosine_normalised_strength"].max()))
    max_frequency = max(frequencies.values())

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.0,
            "axes.titlesize": 9.0,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.7,
            "svg.fonttype": "none",
        }
    )

    # 180 mm wide: appropriate for a conventional two-column journal figure.
    fig, ax = plt.subplots(figsize=(7.0866, 7.25), facecolor="white")
    fig.subplots_adjust(left=0.305, right=0.975, top=0.835, bottom=0.275)

    norm = Normalize(vmin=0, vmax=max_strength)
    cmap = plt.get_cmap("viridis")

    # Give the unused upper triangle a quiet background so the data-bearing
    # lower triangle reads as an intentional matrix rather than an incomplete one.
    for i in range(n):
        for j in range(i + 1, n):
            ax.add_patch(
                plt.Rectangle(
                    (j - 0.5, i - 0.5),
                    1,
                    1,
                    facecolor="#F7F8FA",
                    edgecolor="none",
                    zorder=0,
                )
            )

    for row in rows.itertuples(index=False):
        i = concepts.index(row.row_concept_id)
        j = concepts.index(row.column_concept_id)
        raw = int(row.cooccurring_studies)
        is_diagonal = str(row.diagonal_frequency).lower() == "true"

        if is_diagonal:
            size = 52 + 340 * math.sqrt(raw / max_frequency)
            colour = "#455563"
        elif raw > 0:
            size = bubble_area(raw, max_pair)
            colour = cmap(norm(float(row.cosine_normalised_strength)))
        else:
            continue

        ax.scatter(
            j,
            i,
            s=size,
            color=colour,
            edgecolor="white",
            linewidth=0.65,
            zorder=3,
        )

        if is_diagonal or raw >= 5:
            ax.text(
                j,
                i,
                str(raw),
                ha="center",
                va="center",
                fontsize=6.7 if not is_diagonal else 7.0,
                fontweight="semibold" if is_diagonal else "normal",
                color="white",
                zorder=4,
            )

    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(n - 0.4, -0.6)
    ax.set_xticks(range(n), labels, rotation=50, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(n), labels)
    ax.tick_params(axis="both", length=0, pad=3)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#DDE3E9", linewidth=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_aspect("equal")

    for spine in ax.spines.values():
        spine.set_color("#AAB4BE")
        spine.set_linewidth(0.8)

    fig.text(
        0.055,
        0.955,
        "Fine-grained non-technical-skills co-occurrence",
        ha="left",
        va="top",
        fontsize=13.6,
        fontweight="bold",
        color="#17212B",
    )
    fig.text(
        0.055,
        0.915,
        "Controlled lexical analysis of 483 titles and 447 available abstracts",
        ha="left",
        va="top",
        fontsize=9.0,
        color="#52606D",
    )

    # Legends occupy the deliberately unused upper triangle.
    ax.text(
        0.665,
        0.925,
        "Bubble area",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.6,
        fontweight="semibold",
        color="#25313D",
    )
    legend_values = [5, 15, max_pair]
    legend_y = [0.865, 0.785, 0.690]
    for value, ypos in zip(legend_values, legend_y):
        ax.scatter(
            0.72,
            ypos,
            transform=ax.transAxes,
            s=bubble_area(value, max_pair),
            color="#91A4B5",
            edgecolor="white",
            linewidth=0.6,
            clip_on=False,
            zorder=5,
        )
        ax.text(
            0.785,
            ypos,
            f"{value} studies",
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=7.1,
            color="#3C4854",
        )

    ax.text(
        0.665,
        0.555,
        "Cosine-normalised strength",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.1,
        color="#3C4854",
    )
    cax = ax.inset_axes([0.665, 0.495, 0.275, 0.027])
    colour_bar = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=cax,
        orientation="horizontal",
    )
    colour_bar.set_ticks([0.0, 0.1, 0.2, 0.3])
    colour_bar.ax.tick_params(labelsize=6.5, length=2, pad=1)
    colour_bar.outline.set_linewidth(0.55)
    fig.text(
        0.055,
        0.055,
        "Diagonal: concept frequency. Off-diagonal: same-study co-occurrence.\n"
        "Counts describe title-and-abstract reporting, not the full text.",
        ha="left",
        va="bottom",
        fontsize=7.2,
        color="#52606D",
    )

    stem = "FIGURE_5_FINE_GRAINED_NTS_COOCCURRENCE_PUBLICATION_V4_TIE_AWARE"
    png = OUTPUT / f"{stem}_600DPI.png"
    svg = OUTPUT / f"{stem}.svg"
    eps = OUTPUT / f"{stem}.eps"
    fig.savefig(png, dpi=600, facecolor="white")
    fig.savefig(svg, facecolor="white")
    fig.savefig(eps, facecolor="white")
    plt.close(fig)

    with Image.open(png) as image:
        expected_width = round(7.0866 * 600)
        if abs(image.width - expected_width) > 2:
            raise ValueError(f"Unexpected PNG width: {image.width}; expected about {expected_width}")
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        image.save(OUTPUT / f"{stem}_QA_1800PX.png")

    caption = (
        "Fig. 5 Fine-grained non-technical-skills concept co-occurrence in the 483-study corpus. "
        "A controlled thesaurus comprising 78 concept groups and 303 exact lexical variants was "
        "applied with binary whole counting to all 483 titles and the 447 available abstracts. "
        "Diagonal bubbles show concept frequencies. Off-diagonal bubble area is proportional to "
        "the number of studies containing both concepts, and colour represents cosine-normalised "
        "co-occurrence. The matrix displays all 19 NTS umbrella, core-skill, or training-process "
        "concepts occurring in at least seven studies. These are "
        "lexical reporting patterns; absence of a title or abstract phrase does not establish "
        "absence of the skill from the full text.\n"
    )
    (OUTPUT / "PROPOSED_FIGURE_5_CAPTION.md").write_text(caption, encoding="utf-8")

    manifest_rows = []
    for path in sorted(
        p for p in OUTPUT.rglob("*") if p.is_file() and p.name != "OUTPUT_HASH_MANIFEST.csv"
    ):
        manifest_rows.append(
            {
                "relative_path": path.relative_to(OUTPUT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    with (OUTPUT / "OUTPUT_HASH_MANIFEST.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)


if __name__ == "__main__":
    build()
