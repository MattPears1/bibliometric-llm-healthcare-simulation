#!/usr/bin/env python3
"""
Keyword Co-occurrence Analysis
- Extract keywords from paper metadata or title
- Build co-occurrence matrix
- Network visualization with spring layout
- Top 30 keywords bar chart
- Word cloud from all keywords
"""

import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# Common stopwords to filter from title-extracted keywords
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "it", "its", "this", "that", "these", "those", "he", "she", "they",
    "we", "i", "you", "my", "your", "his", "her", "our", "their",
    "what", "which", "who", "whom", "where", "when", "why", "how",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "above", "after", "again", "all", "also", "am",
    "any", "because", "before", "between", "both", "each", "few",
    "more", "most", "other", "over", "own", "same", "some", "such",
    "into", "up", "out", "off", "down", "only", "still", "here", "there",
    "through", "during", "under", "further", "once", "using", "based",
    "study", "analysis", "review", "approach", "among", "across",
    "results", "use", "used", "new", "however", "including", "method",
    "methods", "within", "effect", "effects", "role",
}


def normalize_keyword(kw: str) -> str:
    """Lowercase and strip a keyword."""
    return kw.strip().lower()


def extract_keywords_from_title(title: str) -> List[str]:
    """Extract meaningful multi-word or single-word terms from title."""
    if not title:
        return []
    # Remove punctuation except hyphens within words
    clean = re.sub(r"[^\w\s-]", " ", title.lower())
    words = clean.split()
    keywords = []
    # Keep words that are not stopwords and have length > 2
    for w in words:
        w = w.strip("-")
        if w and w not in STOPWORDS and len(w) > 2:
            keywords.append(w)
    return keywords


def get_paper_keywords(paper: Dict) -> List[str]:
    """Get keywords from paper metadata; fall back to title extraction."""
    kws = paper.get("keywords")
    if kws and isinstance(kws, list) and len(kws) > 0:
        return [normalize_keyword(k) for k in kws if isinstance(k, str) and k.strip()]

    # Fallback: extract from title
    title = paper.get("title") or ""
    return extract_keywords_from_title(title)


def build_cooccurrence(papers: List[Dict], top_n: int = 50) -> Tuple[Counter, Dict]:
    """
    Build keyword frequency and co-occurrence data.
    Returns:
        keyword_freq: Counter of keyword frequencies
        cooccurrence: {(kw1, kw2): count}
    """
    keyword_freq: Counter = Counter()
    cooccurrence: Counter = Counter()

    for paper in papers:
        kws = get_paper_keywords(paper)
        unique_kws = list(dict.fromkeys(kws))  # deduplicate, preserve order

        for kw in unique_kws:
            keyword_freq[kw] += 1

        # Co-occurrence: pairs of keywords within the same paper
        for kw1, kw2 in combinations(sorted(set(unique_kws)), 2):
            cooccurrence[(kw1, kw2)] += 1

    return keyword_freq, cooccurrence


def plot_top_keywords(keyword_freq: Counter, fig_dir: Path, top_n: int = 30) -> None:
    """Horizontal bar chart of top N keywords by frequency."""
    top = keyword_freq.most_common(top_n)
    labels = [t[0] for t in reversed(top)]
    counts = [t[1] for t in reversed(top)]

    fig, ax = plt.subplots(figsize=(10, 9))
    colors = plt.cm.plasma(np.linspace(0.15, 0.85, len(labels)))
    bars = ax.barh(labels, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=8, fontweight="bold")

    ax.set_xlabel("Frequency", fontsize=12)
    ax.set_title(f"Top {top_n} Keywords by Frequency", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "top_keywords.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_network(keyword_freq: Counter, cooccurrence: Counter, fig_dir: Path,
                 top_n_nodes: int = 40, min_edge_weight: int = 3) -> None:
    """Network visualization of keyword co-occurrence using networkx."""
    try:
        import networkx as nx
    except ImportError:
        logger.warning("networkx not installed; skipping network plot")
        return

    # Select top N keywords as nodes
    top_keywords = {kw for kw, _ in keyword_freq.most_common(top_n_nodes)}

    G = nx.Graph()
    for kw in top_keywords:
        G.add_node(kw, freq=keyword_freq[kw])

    # Add edges with weight >= threshold
    for (kw1, kw2), weight in cooccurrence.items():
        if kw1 in top_keywords and kw2 in top_keywords and weight >= min_edge_weight:
            G.add_edge(kw1, kw2, weight=weight)

    # Remove isolated nodes
    isolates = list(nx.isolates(G))
    G.remove_nodes_from(isolates)

    if len(G.nodes()) == 0:
        logger.warning("No connected nodes in co-occurrence network; skipping plot")
        return

    # Layout
    pos = nx.spring_layout(G, k=1.8, iterations=60, seed=42)

    # Node sizes proportional to frequency
    freqs = [G.nodes[n].get("freq", 1) for n in G.nodes()]
    max_freq = max(freqs) if freqs else 1
    node_sizes = [300 + 2500 * (f / max_freq) for f in freqs]

    # Edge widths proportional to co-occurrence
    edge_weights = [G.edges[e]["weight"] for e in G.edges()]
    max_ew = max(edge_weights) if edge_weights else 1
    edge_widths = [0.5 + 4.0 * (w / max_ew) for w in edge_weights]
    edge_alphas = [0.2 + 0.6 * (w / max_ew) for w in edge_weights]

    fig, ax = plt.subplots(figsize=(14, 11))

    # Draw edges with varying alpha
    for (u, v), width, alpha in zip(G.edges(), edge_widths, edge_alphas):
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        ax.plot(x, y, color="#888888", linewidth=width, alpha=alpha, zorder=1)

    # Draw nodes
    node_colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(G.nodes())))
    xs = [pos[n][0] for n in G.nodes()]
    ys = [pos[n][1] for n in G.nodes()]
    ax.scatter(xs, ys, s=node_sizes, c=node_colors, edgecolors="black",
               linewidths=0.5, zorder=2, alpha=0.85)

    # Labels
    for n in G.nodes():
        ax.annotate(n, pos[n], fontsize=7, ha="center", va="center",
                    fontweight="bold", zorder=3)

    ax.set_title("Keyword Co-occurrence Network", fontsize=15, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()

    out = fig_dir / "keyword_cooccurrence_network.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_wordcloud(keyword_freq: Counter, fig_dir: Path) -> None:
    """Generate a word cloud from keyword frequencies."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        logger.warning("wordcloud not installed; skipping word cloud")
        return

    if not keyword_freq:
        logger.warning("No keywords for word cloud")
        return

    wc = WordCloud(
        width=1600, height=900,
        background_color="white",
        max_words=200,
        colormap="viridis",
        prefer_horizontal=0.7,
        min_font_size=8,
        max_font_size=120,
        random_state=42,
    )
    wc.generate_from_frequencies(keyword_freq)

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Keyword Word Cloud", fontsize=16, fontweight="bold", pad=15)
    plt.tight_layout()

    out = fig_dir / "keyword_wordcloud.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_keyword_table(keyword_freq: Counter, cooccurrence: Counter,
                       total_papers: int, table_dir: Path) -> None:
    """Save keyword analysis summary as markdown."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"keyword_analysis_{ts}.md"

    lines = [
        "# Keyword Co-occurrence Analysis Summary",
        "",
        f"- Total papers: **{total_papers}**",
        f"- Unique keywords: **{len(keyword_freq)}**",
        f"- Unique co-occurrence pairs: **{len(cooccurrence)}**",
        "",
        "## Top 50 Keywords by Frequency",
        "",
        "| Rank | Keyword | Frequency | % of papers |",
        "|-----:|---------|----------:|------------:|",
    ]
    for rank, (kw, cnt) in enumerate(keyword_freq.most_common(50), 1):
        pct = cnt / total_papers * 100 if total_papers else 0
        lines.append(f"| {rank} | {kw} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Top 30 Co-occurrence Pairs",
        "",
        "| Rank | Keyword 1 | Keyword 2 | Co-occurrences |",
        "|-----:|-----------|-----------|---------------:|",
    ]
    for rank, ((kw1, kw2), cnt) in enumerate(cooccurrence.most_common(30), 1):
        lines.append(f"| {rank} | {kw1} | {kw2} | {cnt} |")

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

    keyword_freq, cooccurrence = build_cooccurrence(papers)
    logger.info("Unique keywords: %d", len(keyword_freq))
    logger.info("Top 10 keywords: %s", keyword_freq.most_common(10))

    plot_top_keywords(keyword_freq, fig_dir)
    plot_network(keyword_freq, cooccurrence, fig_dir)
    plot_wordcloud(keyword_freq, fig_dir)
    save_keyword_table(keyword_freq, cooccurrence, len(papers), table_dir)

    logger.info("Keyword co-occurrence analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
