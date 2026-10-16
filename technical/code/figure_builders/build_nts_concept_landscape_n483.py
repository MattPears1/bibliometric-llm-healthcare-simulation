from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import textwrap
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import networkx as nx
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = HERE.parents[1]
# The extraction input contains title-and-abstract text and is not redistributed.
# Set NTS_SOURCE_CSV to an authorised local copy when rebuilding extraction outputs.
SOURCE = Path(os.environ.get("NTS_SOURCE_CSV", PACKAGE_ROOT / "RESTRICTED_INPUT_NOT_INCLUDED.csv"))
LEXICON = HERE / "NTS_CONCEPT_LEXICON.csv"

EXPECTED_STUDIES = 483
EXPECTED_EXPLICIT_NTS = 360
CORE_CLASSES = {"umbrella", "core_skill", "training_process"}

DOMAIN_ORDER = [
    "Umbrella and human factors",
    "Communication",
    "Teamwork",
    "Leadership",
    "Decision-making and cognition",
    "Situational awareness",
    "Task and resource management",
    "Stress and self-management",
    "Professionalism and patient-centred care",
    "Learning and debriefing",
]

DOMAIN_COLORS = {
    "Umbrella and human factors": "#6D6E71",
    "Communication": "#2463A7",
    "Teamwork": "#2A9D8F",
    "Leadership": "#E76F51",
    "Decision-making and cognition": "#7A5195",
    "Situational awareness": "#D9A441",
    "Task and resource management": "#4D908E",
    "Stress and self-management": "#F9844A",
    "Professionalism and patient-centred care": "#B56576",
    "Learning and debriefing": "#577590",
    "Context or outcome": "#9B9B9B",
}

CHECKED_DOMAIN_LABELS = [
    ("Communication", "communication"),
    ("Decision-making", "decision_making"),
    ("Teamwork", "teamwork"),
    ("Professionalism", "professionalism"),
    ("Other explicit NTS", "other"),
    ("Leadership", "leadership"),
    ("Stress management", "stress_management"),
    ("Situational awareness", "situational_awareness"),
    ("Task management", "task_management"),
]

PRIORITY_IDS = [
    "closed_loop_communication",
    "open_loop_communication",
    "handover",
    "assertiveness",
    "psychological_safety",
    "leadership",
    "situational_awareness",
    "distraction_management",
    "task_management",
    "workload_management",
    "stress_management",
    "fatigue_management",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalise_text(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[-_/]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def phrase_pattern(phrase: str) -> re.Pattern[str]:
    phrase = normalise_text(phrase)
    return re.compile(r"(?<![a-z0-9])" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?![a-z0-9])")


def parse_semicolon_list(value: object) -> list[str]:
    if value is None or pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def wilson_percent(count: int, total: int) -> float:
    return round(100.0 * count / total, 1) if total else 0.0


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.08, 1.04, label, transform=ax.transAxes, fontsize=15, fontweight="bold", va="bottom")


def build(output: Path) -> None:
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)

    corpus = pd.read_csv(SOURCE, dtype=str, keep_default_na=False)
    if len(corpus) != EXPECTED_STUDIES:
        raise AssertionError(f"Expected {EXPECTED_STUDIES} studies, found {len(corpus)}")
    if corpus["paper_id"].duplicated().any():
        raise AssertionError("paper_id is not unique")

    lex = pd.read_csv(LEXICON, dtype=str, keep_default_na=False)
    if lex["concept_id"].duplicated().any():
        raise AssertionError("concept_id is not unique")
    if not set(lex["domain"]).issubset(set(DOMAIN_COLORS)):
        raise AssertionError("Unmapped lexicon domain")

    compiled: dict[str, list[tuple[str, re.Pattern[str]]]] = {}
    for row in lex.itertuples(index=False):
        variants = [v.strip() for v in row.variants.split("|") if v.strip()]
        compiled[row.concept_id] = [(v, phrase_pattern(v)) for v in variants]

    matches: list[dict[str, object]] = []
    study_concepts: dict[str, set[str]] = defaultdict(set)
    for row in corpus.itertuples(index=False):
        title = normalise_text(row.title)
        abstract = normalise_text(row.abstract)
        for concept in lex.itertuples(index=False):
            title_hits = [raw for raw, pattern in compiled[concept.concept_id] if pattern.search(title)]
            abstract_hits = [raw for raw, pattern in compiled[concept.concept_id] if pattern.search(abstract)]
            if not title_hits and not abstract_hits:
                continue
            study_concepts[row.paper_id].add(concept.concept_id)
            matches.append(
                {
                    "paper_id": row.paper_id,
                    "year": row.year,
                    "title": row.title,
                    "concept_id": concept.concept_id,
                    "concept_label": concept.concept_label,
                    "domain": concept.domain,
                    "classification": concept.classification,
                    "title_match": bool(title_hits),
                    "abstract_match": bool(abstract_hits),
                    "matched_variants": " | ".join(sorted(set(title_hits + abstract_hits))),
                }
            )

    assignments = pd.DataFrame(matches)
    concept_counts = Counter(assignments["concept_id"]) if not assignments.empty else Counter()

    summary_rows = []
    for row in lex.itertuples(index=False):
        n = int(concept_counts.get(row.concept_id, 0))
        subset = assignments[assignments["concept_id"] == row.concept_id] if n else assignments.iloc[0:0]
        summary_rows.append(
            {
                "concept_id": row.concept_id,
                "domain": row.domain,
                "concept_label": row.concept_label,
                "classification": row.classification,
                "study_count": n,
                "percent_of_483": wilson_percent(n, EXPECTED_STUDIES),
                "title_match_studies": int(subset["title_match"].sum()) if n else 0,
                "abstract_match_studies": int(subset["abstract_match"].sum()) if n else 0,
                "study_ids": ";".join(sorted(subset["paper_id"].unique())) if n else "",
            }
        )
    concept_summary = pd.DataFrame(summary_rows).sort_values(
        ["study_count", "domain", "concept_label"], ascending=[False, True, True]
    )

    domain_counts = Counter()
    no_explicit = 0
    for value in corpus["final_nts_domains"]:
        domains = parse_semicolon_list(value)
        if not domains:
            no_explicit += 1
        domain_counts.update(set(domains))
    if EXPECTED_STUDIES - no_explicit != EXPECTED_EXPLICIT_NTS:
        raise AssertionError(
            f"Checked NTS coverage no longer equals {EXPECTED_EXPLICIT_NTS}/{EXPECTED_STUDIES}"
        )

    domain_rows = []
    for label, code in CHECKED_DOMAIN_LABELS:
        n = int(domain_counts.get(code, 0))
        domain_rows.append(
            {"domain": label, "study_count": n, "denominator": EXPECTED_STUDIES, "percent": wilson_percent(n, EXPECTED_STUDIES)}
        )
    checked_domains = pd.DataFrame(domain_rows)

    assignments.to_csv(output / "NTS_TITLE_ABSTRACT_CONCEPT_ASSIGNMENTS.csv", index=False, encoding="utf-8-sig")
    concept_summary.to_csv(output / "NTS_CONCEPT_SUMMARY_ALL.csv", index=False, encoding="utf-8-sig")
    checked_domains.to_csv(output / "NTS_CHECKED_DOMAIN_COUNTS.csv", index=False, encoding="utf-8-sig")

    # Network nodes: the most frequent connected NTS concepts. Rare and absent
    # safety-critical micro-skills are shown separately in Panel B, preventing
    # isolated nodes from distorting the co-occurrence layout.
    eligible = concept_summary[
        concept_summary["classification"].isin(CORE_CLASSES) & (concept_summary["study_count"] >= 2)
    ].copy()
    candidate_ids = list(eligible.head(36)["concept_id"])
    node_meta = lex.set_index("concept_id").loc[candidate_ids]

    graph = nx.Graph()
    for cid in candidate_ids:
        meta = node_meta.loc[cid]
        graph.add_node(
            cid,
            label=meta["concept_label"],
            domain=meta["domain"],
            count=int(concept_counts[cid]),
            classification=meta["classification"],
        )

    pair_counts: Counter[tuple[str, str]] = Counter()
    for concepts in study_concepts.values():
        present = sorted(set(candidate_ids).intersection(concepts))
        for i, left in enumerate(present):
            for right in present[i + 1 :]:
                pair_counts[(left, right)] += 1
    for (left, right), c in pair_counts.items():
        if c < 2:
            continue
        cosine = c / math.sqrt(concept_counts[left] * concept_counts[right])
        graph.add_edge(left, right, cooccurrence=c, layout_weight=cosine)

    nontrivial = [component for component in nx.connected_components(graph) if len(component) >= 2]
    if not nontrivial:
        raise AssertionError("No connected NTS concept network was produced")
    largest = max(nontrivial, key=len)
    display_ids = [cid for cid in candidate_ids if cid in largest][:28]
    display_graph = graph.subgraph(display_ids).copy()

    # Retain the strongest links around every node plus all very frequent links.
    display_edges: set[tuple[str, str]] = set()
    for node in display_graph.nodes:
        ranked = sorted(
            display_graph.edges(node, data=True),
            key=lambda item: (item[2]["layout_weight"], item[2]["cooccurrence"]),
            reverse=True,
        )
        for left, right, _ in ranked[:6]:
            display_edges.add(tuple(sorted((left, right))))
    for left, right, data in display_graph.edges(data=True):
        if data["cooccurrence"] >= 8:
            display_edges.add(tuple(sorted((left, right))))

    rng = np.random.default_rng(190826)
    centers = {}
    angles = np.linspace(0, 2 * np.pi, len(DOMAIN_ORDER), endpoint=False)
    for domain, angle in zip(DOMAIN_ORDER, angles):
        centers[domain] = np.array([1.25 * np.cos(angle), 0.9 * np.sin(angle)])
    initial = {
        node: centers[display_graph.nodes[node]["domain"]] + rng.normal(0, 0.11, size=2)
        for node in display_graph.nodes
    }
    pos = nx.spring_layout(
        display_graph,
        pos=initial,
        seed=190826,
        k=0.62,
        iterations=900,
        weight="layout_weight",
    )

    # Export the exact displayed network.
    network_nodes = []
    for node, data in display_graph.nodes(data=True):
        network_nodes.append(
            {
                "concept_id": node,
                "concept_label": data["label"],
                "domain": data["domain"],
                "classification": data["classification"],
                "study_count": data["count"],
                "x": float(pos[node][0]),
                "y": float(pos[node][1]),
            }
        )
    pd.DataFrame(network_nodes).to_csv(output / "NTS_NETWORK_NODES.csv", index=False, encoding="utf-8-sig")
    network_edges = []
    for left, right, data in display_graph.edges(data=True):
        network_edges.append(
            {
                "source": left,
                "target": right,
                "cooccurrence": data["cooccurrence"],
                "cosine_layout_weight": round(data["layout_weight"], 8),
                "displayed_in_figure": tuple(sorted((left, right))) in display_edges,
            }
        )
    pd.DataFrame(network_edges).to_csv(output / "NTS_NETWORK_EDGES.csv", index=False, encoding="utf-8-sig")

    # Publication figure.
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titlesize": 13,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })
    fig = plt.figure(figsize=(16, 10.0), facecolor="white")
    grid = fig.add_gridspec(2, 2, width_ratios=[0.78, 1.72], height_ratios=[1.10, 0.90], wspace=0.18, hspace=0.36)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[:, 1])

    # A: checked domain prevalence.
    plot_domains = checked_domains.iloc[::-1]
    y = np.arange(len(plot_domains))
    colors = ["#2B6CB0" if n >= 20 else "#8AA6C1" for n in plot_domains["study_count"]]
    ax_a.barh(y, plot_domains["study_count"], color=colors, height=0.68)
    ax_a.set_yticks(y, plot_domains["domain"])
    ax_a.set_xlim(0, 330)
    ax_a.set_xlabel(f"Studies (n={EXPECTED_STUDIES}; domains may overlap)")
    ax_a.set_title("Checked NTS domains", loc="left", fontweight="bold")
    ax_a.grid(axis="x", color="#D9D9D9", linewidth=0.7)
    ax_a.set_axisbelow(True)
    for yi, row in enumerate(plot_domains.itertuples(index=False)):
        ax_a.text(row.study_count + 5, yi, f"{row.study_count} ({row.percent:.1f}%)", va="center", fontsize=8.5)
    ax_a.text(
        0.0,
        -0.22,
        f"At least one explicit NTS domain: {EXPECTED_EXPLICIT_NTS}/{EXPECTED_STUDIES} "
        f"({wilson_percent(EXPECTED_EXPLICIT_NTS, EXPECTED_STUDIES):.1f}%); no explicit domain: "
        f"{EXPECTED_STUDIES - EXPECTED_EXPLICIT_NTS}/{EXPECTED_STUDIES} "
        f"({wilson_percent(EXPECTED_STUDIES - EXPECTED_EXPLICIT_NTS, EXPECTED_STUDIES):.1f}%).",
        transform=ax_a.transAxes,
        fontsize=8.5,
        color="#4A4A4A",
    )
    for spine in ["top", "right", "left"]:
        ax_a.spines[spine].set_visible(False)
    add_panel_label(ax_a, "A")

    # B: selected micro-skills, including absent phrases.
    priority = concept_summary.set_index("concept_id").loc[PRIORITY_IDS].copy()
    priority = priority.iloc[::-1]
    py = np.arange(len(priority))
    pcolors = [DOMAIN_COLORS[d] for d in priority["domain"]]
    ax_b.hlines(py, 0, priority["study_count"], color="#D3D8DD", linewidth=1.3, zorder=1)
    ax_b.scatter(priority["study_count"], py, s=62, color=pcolors, edgecolor="white", linewidth=0.8, zorder=2)
    ax_b.set_yticks(py, priority["concept_label"])
    max_priority = max(5, int(priority["study_count"].max()))
    ax_b.set_xlim(-0.5, max_priority * 1.22 + 1)
    ax_b.set_xlabel("Title/abstract mentions (studies)")
    ax_b.set_title("Selected safety-critical micro-skills", loc="left", fontweight="bold")
    ax_b.grid(axis="x", color="#E3E3E3", linewidth=0.7)
    ax_b.set_axisbelow(True)
    for yi, value in enumerate(priority["study_count"]):
        ax_b.text(value + max(0.15, max_priority * 0.025), yi, str(int(value)), va="center", fontsize=8.5)
    for spine in ["top", "right", "left"]:
        ax_b.spines[spine].set_visible(False)
    add_panel_label(ax_b, "B")

    # C: a triangular bubble heat map avoids the label collisions of a dense
    # node-link display while preserving study-level co-occurrence information.
    matrix_ids = list(eligible.head(18)["concept_id"])
    matrix_labels = [lex.set_index("concept_id").loc[cid, "concept_label"] for cid in matrix_ids]
    matrix_rows = []
    pair_values = []
    strengths = []
    for i, left in enumerate(matrix_ids):
        for j, right in enumerate(matrix_ids):
            if j > i:
                continue
            if left == right:
                raw = int(concept_counts[left])
                strength = 1.0
            else:
                raw = int(pair_counts.get(tuple(sorted((left, right))), 0))
                strength = raw / math.sqrt(concept_counts[left] * concept_counts[right]) if raw else 0.0
                pair_values.append(raw)
                strengths.append(strength)
            matrix_rows.append(
                {
                    "row_concept_id": left,
                    "row_concept_label": lex.set_index("concept_id").loc[left, "concept_label"],
                    "column_concept_id": right,
                    "column_concept_label": lex.set_index("concept_id").loc[right, "concept_label"],
                    "cooccurring_studies": raw,
                    "cosine_normalised_strength": round(strength, 8),
                    "diagonal_frequency": left == right,
                }
            )
    pd.DataFrame(matrix_rows).to_csv(output / "NTS_TOP18_COOCCURRENCE_MATRIX_LONG.csv", index=False, encoding="utf-8-sig")

    max_pair = max(pair_values) if pair_values else 1
    max_strength = max(strengths) if strengths else 1.0
    norm = Normalize(vmin=0, vmax=max_strength)
    cmap = plt.get_cmap("viridis")
    for row in matrix_rows:
        i = matrix_ids.index(row["row_concept_id"])
        j = matrix_ids.index(row["column_concept_id"])
        raw = row["cooccurring_studies"]
        if row["diagonal_frequency"]:
            size = 85 + 620 * math.sqrt(raw / max(concept_counts[cid] for cid in matrix_ids))
            color = "#59636E"
        else:
            size = 18 + 520 * math.sqrt(raw / max_pair) if raw else 8
            color = cmap(norm(row["cosine_normalised_strength"])) if raw else "#F2F3F5"
        ax_c.scatter(j, i, s=size, color=color, edgecolor="white", linewidth=0.7, zorder=3)
        if row["diagonal_frequency"] or raw >= 5:
            ax_c.text(j, i, str(raw), ha="center", va="center", fontsize=7.0, color="white" if raw else "#666666", zorder=4)

    n_matrix = len(matrix_ids)
    ax_c.set_xlim(-0.65, n_matrix - 0.35)
    ax_c.set_ylim(n_matrix - 0.35, -0.65)
    ax_c.set_xticks(range(n_matrix), matrix_labels, rotation=52, ha="right", rotation_mode="anchor")
    ax_c.set_yticks(range(n_matrix), matrix_labels)
    ax_c.tick_params(axis="both", length=0, labelsize=7.3)
    ax_c.set_xticks(np.arange(-0.5, n_matrix, 1), minor=True)
    ax_c.set_yticks(np.arange(-0.5, n_matrix, 1), minor=True)
    ax_c.grid(which="minor", color="#E4E7EB", linewidth=0.55)
    ax_c.tick_params(which="minor", bottom=False, left=False)
    ax_c.set_aspect("equal")
    ax_c.set_title("Fine-grained NTS concept co-occurrence (18 most frequent)", loc="left", fontweight="bold")
    for spine in ax_c.spines.values():
        spine.set_color("#B8BEC5")
        spine.set_linewidth(0.8)
    add_panel_label(ax_c, "C")

    cax = ax_c.inset_axes([0.66, 0.60, 0.28, 0.022])
    colorbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    colorbar.set_label("Cosine-normalised co-occurrence", fontsize=8, labelpad=3)
    colorbar.ax.tick_params(labelsize=7)
    size_values = sorted(set([5, min(15, max_pair), max_pair]))
    size_handles = [
        ax_c.scatter([], [], s=18 + 520 * math.sqrt(value / max_pair), color="#8FA3B5", edgecolor="white", label=f"{value} studies")
        for value in size_values if value > 0
    ]
    ax_c.legend(handles=size_handles, title="Bubble area", loc="upper right", bbox_to_anchor=(0.96, 0.97), frameon=False, fontsize=7, title_fontsize=7.5)

    fig.suptitle("Non-technical skills landscape in LLM-enabled healthcare simulation education", fontsize=18, fontweight="bold", y=0.985)
    fig.subplots_adjust(left=0.055, right=0.975, top=0.90, bottom=0.235)
    fig.text(
        0.5,
        0.012,
        f"Panel A uses checked study-level NTS coding. Panels B–C use a controlled phrase thesaurus with binary whole counting across {EXPECTED_STUDIES} titles and {int((corpus['abstract'].str.strip() != '').sum())} available abstracts; absence of a phrase is not evidence that a skill was absent from the full text.",
        ha="center",
        fontsize=8.2,
        color="#4A4A4A",
    )

    png = output / "FIGURE_NTS_CONCEPT_LANDSCAPE_600DPI.png"
    svg = output / "FIGURE_NTS_CONCEPT_LANDSCAPE.svg"
    eps = output / "FIGURE_NTS_CONCEPT_LANDSCAPE.eps"
    fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    fig.savefig(eps, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    variant_count = sum(len(v) for v in compiled.values())
    covered_studies = len(study_concepts)
    top = concept_summary[concept_summary["classification"].isin(CORE_CLASSES)].head(12)
    methods = (
        "# Methods, results and caption\n\n"
        "## Methods\n\n"
        f"A controlled non-technical skills (NTS) thesaurus comprising {len(lex)} concept groups and {variant_count} exact lexical variants was applied to the title and available abstract of each of the {EXPECTED_STUDIES} unique studies. "
        "Variants included spelling, hyphenation and common terminology alternatives, but no stemming or fuzzy matching. Each concept was counted at most once per study. Panel A uses the independently checked study-level NTS coding; Panels B and C use the title/abstract concept search. Co-occurrence was defined as two concepts appearing in the same study. Panel C shows the 18 most frequent eligible concepts; bubble area represents the number of co-occurring studies and colour represents cosine-normalised co-occurrence. Selected safety-critical micro-skills, including zero counts, were reported separately in Panel B.\n\n"
        "## Results\n\n"
        f"At least one thesaurus concept was found in {covered_studies}/{EXPECTED_STUDIES} studies ({wilson_percent(covered_studies, EXPECTED_STUDIES):.1f}%). The most frequent fine-grained concepts were "
        + ", ".join(f"{r.concept_label} ({int(r.study_count)})" for r in top.itertuples(index=False))
        + ". The micro-skill panel makes low-frequency and absent explicit phrases visible rather than merging them into broader communication or teamwork categories.\n\n"
        "## Figure caption\n\n"
        f"**Figure X. Non-technical skills landscape in LLM-enabled healthcare simulation education.** (A) Prevalence of checked NTS domains among {EXPECTED_STUDIES} unique studies; domains were multiple-response, and {EXPECTED_EXPLICIT_NTS} studies had at least one explicit NTS domain. (B) Study-level title/abstract mentions of selected safety-critical micro-skills, including zero counts. (C) Lower-triangular co-occurrence matrix for the 18 most frequent fine-grained NTS concepts identified with a controlled thesaurus. Diagonal bubbles show individual concept frequencies; off-diagonal bubble area is proportional to the number of studies containing both concepts, and colour represents cosine-normalised co-occurrence. The title/abstract search used binary whole counting across all {EXPECTED_STUDIES} titles and {int((corpus['abstract'].str.strip() != '').sum())} available abstracts. These phrase counts describe explicit reporting and should not be interpreted as proof that an unmentioned skill was absent from the full article.\n"
    )
    (output / "METHODS_RESULTS_CAPTION.md").write_text(methods, encoding="utf-8")

    parameters = {
        "schema_version": "nts_concept_landscape_v1",
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "lexicon": str(LEXICON),
        "lexicon_sha256": sha256(LEXICON),
        "studies": len(corpus),
        "title_coverage": int((corpus["title"].str.strip() != "").sum()),
        "abstract_coverage": int((corpus["abstract"].str.strip() != "").sum()),
        "concept_groups": len(lex),
        "lexical_variants": variant_count,
        "matching": "case-insensitive exact normalized phrase; no stemming or fuzzy matching; binary whole counting",
        "network_nodes": len(display_graph.nodes),
        "network_edges": len(display_graph.edges),
        "figure_matrix_concepts": 18,
        "figure_matrix_encoding": "diagonal=concept frequency; off-diagonal bubble area=raw co-occurring studies; colour=cosine-normalised co-occurrence",
        "network_node_rule": "28 most frequent eligible concepts in the largest connected component among the top 36 concepts with n>=2; rare priority micro-skills are reported in Panel B",
        "network_edge_rule": "layout uses every co-occurrence>=2; display uses strongest 6 cosine-normalized links per node plus every raw co-occurrence>=8",
        "layout": "networkx spring_layout, seed 190826, k 0.62, 900 iterations, cosine-normalized co-occurrence weight",
    }
    (output / "ANALYSIS_PARAMETERS.json").write_text(json.dumps(parameters, indent=2), encoding="utf-8")

    artifacts = []
    for path in sorted(output.iterdir()):
        if path.is_file():
            artifacts.append({"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size})
    with (output / "OUTPUT_HASH_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "sha256", "bytes"])
        writer.writeheader()
        writer.writerows(artifacts)

    print(json.dumps(parameters, indent=2))
    print("\nTop concept counts:")
    print(concept_summary[["concept_label", "domain", "classification", "study_count"]].head(30).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.output.resolve())
