#!/usr/bin/env python3
"""
Thematic/Strategic Diagram (Callon et al., 1991)
=================================================
Builds a strategic diagram from keyword co-occurrence network:
- X-axis: Centrality (how connected a theme cluster is to other clusters)
- Y-axis: Density (how developed/mature a theme cluster is internally)

Four quadrants:
  Q1 (high centrality, high density): Motor themes - well-developed and central
  Q2 (low centrality, high density): Niche themes - well-developed but peripheral
  Q3 (low centrality, low density): Emerging or declining themes
  Q4 (high centrality, low density): Basic/transversal themes - important but underdeveloped

Based on: Callon, M., Courtial, J.P., & Laville, F. (1991). Co-word analysis as a tool for
describing the network of interactions between basic and technological research.
Scientometrics, 22(1), 155-205.

Implementation follows formulas from bibliometrix R package (thematicMap.R).
"""

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


class ThematicMapper:
    """Build Callon's strategic diagram from bibliometric data."""

    # Stopwords to exclude from keyword extraction
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "this", "that",
        "these", "those", "it", "its", "we", "our", "their", "they", "them",
        "he", "she", "his", "her", "not", "no", "nor", "so", "if", "as",
        "than", "then", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "over", "about", "up", "down",
        "out", "off", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "only", "own", "same", "very", "just", "also",
        "study", "paper", "article", "research", "results", "method", "methods",
        "conclusion", "conclusions", "objective", "objectives", "background",
        "introduction", "discussion", "findings", "however", "using", "used",
        "based", "among", "well", "new", "two", "one", "three", "first",
    }

    def __init__(self, min_keyword_freq: int = 3, min_cooccurrence: int = 2,
                 clustering_resolution: float = 1.0):
        self.min_keyword_freq = min_keyword_freq
        self.min_cooccurrence = min_cooccurrence
        self.clustering_resolution = clustering_resolution
        self.output_dir = Path(__file__).parent / "figures"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir = Path(__file__).parent / "tables"
        self.tables_dir.mkdir(parents=True, exist_ok=True)

    def extract_keywords(self, papers: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract keywords from each paper.
        Uses author keywords if available, otherwise extracts from title+abstract.
        Returns: {paper_id: [keyword1, keyword2, ...]}
        """
        paper_keywords = {}

        for paper in papers:
            pid = paper.get("id", paper.get("doi", str(hash(paper.get("title", "")))))
            keywords = []

            # Use author keywords first
            if paper.get("keywords"):
                for kw in paper["keywords"]:
                    if isinstance(kw, str) and len(kw) > 2:
                        keywords.append(kw.lower().strip())

            # If no keywords, extract from title + abstract
            if not keywords:
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                keywords = self._extract_ngrams(text)

            paper_keywords[pid] = keywords

        return paper_keywords

    def _extract_ngrams(self, text: str, max_ngram: int = 3) -> List[str]:
        """Extract meaningful n-grams from text."""
        text = text.lower()
        text = re.sub(r"[^\w\s-]", " ", text)
        words = [w for w in text.split() if w not in self.STOPWORDS and len(w) > 2]

        ngrams = []
        # Unigrams
        ngrams.extend(words)
        # Bigrams
        for i in range(len(words) - 1):
            ngrams.append(f"{words[i]} {words[i+1]}")
        # Trigrams
        if max_ngram >= 3:
            for i in range(len(words) - 2):
                ngrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")

        return ngrams

    def build_cooccurrence_network(self, paper_keywords: Dict[str, List[str]]) -> nx.Graph:
        """
        Build keyword co-occurrence network.
        Nodes = keywords, edges = co-occurrence in same paper.
        Edge weight = number of papers where both keywords appear.
        """
        # Count keyword frequencies
        keyword_freq = Counter()
        for keywords in paper_keywords.values():
            keyword_freq.update(set(keywords))  # Count each keyword once per paper

        # Filter by minimum frequency
        valid_keywords = {k for k, v in keyword_freq.items()
                         if v >= self.min_keyword_freq}
        logger.info(f"Keywords above min frequency ({self.min_keyword_freq}): {len(valid_keywords)}")

        # Build co-occurrence matrix
        cooccurrence = defaultdict(int)
        for keywords in paper_keywords.values():
            valid = sorted(set(kw for kw in keywords if kw in valid_keywords))
            for i in range(len(valid)):
                for j in range(i + 1, len(valid)):
                    pair = (valid[i], valid[j])
                    cooccurrence[pair] += 1

        # Build network
        G = nx.Graph()
        for kw in valid_keywords:
            G.add_node(kw, frequency=keyword_freq[kw])

        for (kw1, kw2), weight in cooccurrence.items():
            if weight >= self.min_cooccurrence:
                # Normalize by Association Strength (Van Eck & Waltman, 2009)
                freq1 = keyword_freq[kw1]
                freq2 = keyword_freq[kw2]
                n_papers = len(paper_keywords)
                assoc_strength = (weight * n_papers) / (freq1 * freq2) if freq1 * freq2 > 0 else 0
                G.add_edge(kw1, kw2, weight=weight, assoc_strength=assoc_strength)

        # Remove isolated nodes
        isolates = list(nx.isolates(G))
        G.remove_nodes_from(isolates)
        logger.info(f"Co-occurrence network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        return G

    def detect_clusters(self, G: nx.Graph) -> Dict[str, int]:
        """Detect thematic clusters using Louvain community detection."""
        if G.number_of_nodes() == 0:
            return {}

        communities = nx.community.louvain_communities(
            G, weight="weight", resolution=self.clustering_resolution, seed=42
        )

        # Assign cluster IDs
        node_clusters = {}
        for cluster_id, community in enumerate(communities):
            for node in community:
                node_clusters[node] = cluster_id

        logger.info(f"Detected {len(communities)} thematic clusters")
        return node_clusters

    def compute_callon_metrics(self, G: nx.Graph, clusters: Dict[str, int]) -> List[Dict]:
        """
        Compute Callon's centrality and density for each cluster.

        Centrality = sum of edge weights between the cluster and other clusters
                     (measures external cohesion / importance)

        Density = sum of internal edge weights / number of nodes in cluster
                  (measures internal development / maturity)
        """
        if not clusters:
            return []

        # Group nodes by cluster
        cluster_nodes = defaultdict(set)
        for node, cid in clusters.items():
            cluster_nodes[cid].add(node)

        results = []

        for cid, nodes in cluster_nodes.items():
            if len(nodes) < 2:
                continue

            # Internal edges (within cluster)
            internal_weight = 0
            for n1 in nodes:
                for n2 in nodes:
                    if n1 < n2 and G.has_edge(n1, n2):
                        internal_weight += G[n1][n2]["weight"]

            # External edges (between cluster and other clusters)
            external_weight = 0
            for n1 in nodes:
                for neighbor in G.neighbors(n1):
                    if neighbor not in nodes:
                        external_weight += G[n1][neighbor]["weight"]

            # Callon metrics
            density = internal_weight / len(nodes) if len(nodes) > 0 else 0
            centrality = external_weight  # Can also normalize by cluster size

            # Top keywords in cluster (by frequency)
            kw_freqs = [(n, G.nodes[n].get("frequency", 0)) for n in nodes]
            kw_freqs.sort(key=lambda x: -x[1])
            top_keywords = [kw for kw, _ in kw_freqs[:5]]
            label = " / ".join(top_keywords[:3])

            results.append({
                "cluster_id": cid,
                "label": label,
                "top_keywords": top_keywords,
                "n_keywords": len(nodes),
                "centrality": centrality,
                "density": density,
                "internal_weight": internal_weight,
                "external_weight": external_weight,
            })

        return results

    def plot_strategic_diagram(self, cluster_data: List[Dict],
                               title: str = "Strategic Diagram: LLMs in Healthcare Simulation",
                               save_path: Optional[str] = None) -> str:
        """
        Plot the 4-quadrant strategic diagram.
        """
        if not cluster_data:
            logger.warning("No cluster data to plot")
            return ""

        fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        centralities = [c["centrality"] for c in cluster_data]
        densities = [c["density"] for c in cluster_data]
        sizes = [c["n_keywords"] for c in cluster_data]

        # Median lines for quadrant boundaries
        med_centrality = np.median(centralities)
        med_density = np.median(densities)

        # Plot clusters as bubbles
        max_size = max(sizes) if sizes else 1
        bubble_sizes = [300 + (s / max_size) * 2000 for s in sizes]

        # Color by quadrant
        colors = []
        for c in cluster_data:
            if c["centrality"] >= med_centrality and c["density"] >= med_density:
                colors.append("#2196F3")  # Q1: Motor (blue)
            elif c["centrality"] < med_centrality and c["density"] >= med_density:
                colors.append("#4CAF50")  # Q2: Niche (green)
            elif c["centrality"] < med_centrality and c["density"] < med_density:
                colors.append("#FF9800")  # Q3: Emerging/Declining (orange)
            else:
                colors.append("#F44336")  # Q4: Basic (red)

        scatter = ax.scatter(centralities, densities, s=bubble_sizes,
                           c=colors, alpha=0.6, edgecolors="black", linewidths=1)

        # Add labels
        for i, c in enumerate(cluster_data):
            ax.annotate(c["label"], (c["centrality"], c["density"]),
                       fontsize=8, ha="center", va="bottom",
                       fontweight="bold",
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                edgecolor="gray", alpha=0.8))

        # Quadrant lines and labels
        ax.axhline(y=med_density, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.axvline(x=med_centrality, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

        # Quadrant labels
        x_range = max(centralities) - min(centralities) if len(centralities) > 1 else 1
        y_range = max(densities) - min(densities) if len(densities) > 1 else 1
        x_pad = x_range * 0.02
        y_pad = y_range * 0.02

        ax.text(max(centralities) + x_pad, max(densities) + y_pad,
               "MOTOR THEMES\n(well-developed, central)",
               ha="right", va="top", fontsize=9, color="#2196F3", style="italic")
        ax.text(min(centralities) - x_pad, max(densities) + y_pad,
               "NICHE THEMES\n(well-developed, peripheral)",
               ha="left", va="top", fontsize=9, color="#4CAF50", style="italic")
        ax.text(min(centralities) - x_pad, min(densities) - y_pad,
               "EMERGING / DECLINING\n(underdeveloped, peripheral)",
               ha="left", va="bottom", fontsize=9, color="#FF9800", style="italic")
        ax.text(max(centralities) + x_pad, min(densities) - y_pad,
               "BASIC THEMES\n(underdeveloped, central)",
               ha="right", va="bottom", fontsize=9, color="#F44336", style="italic")

        ax.set_xlabel("Centrality (external cohesion)", fontsize=12)
        ax.set_ylabel("Density (internal development)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        # Legend
        legend_elements = [
            mpatches.Patch(facecolor="#2196F3", alpha=0.6, label="Motor themes"),
            mpatches.Patch(facecolor="#4CAF50", alpha=0.6, label="Niche themes"),
            mpatches.Patch(facecolor="#FF9800", alpha=0.6, label="Emerging/declining"),
            mpatches.Patch(facecolor="#F44336", alpha=0.6, label="Basic themes"),
        ]
        ax.legend(handles=legend_elements, loc="upper left", fontsize=9)

        plt.tight_layout()

        if save_path is None:
            save_path = str(self.output_dir / "strategic_diagram.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"Strategic diagram saved to {save_path}")
        return save_path

    def run(self, papers: List[Dict]) -> Dict:
        """Run the full thematic mapping pipeline."""
        logger.info(f"Starting thematic mapping with {len(papers)} papers")

        # Step 1: Extract keywords
        paper_keywords = self.extract_keywords(papers)

        # Step 2: Build co-occurrence network
        G = self.build_cooccurrence_network(paper_keywords)

        if G.number_of_nodes() < 5:
            logger.warning("Too few keywords for meaningful thematic mapping")
            return {"error": "Insufficient keywords", "nodes": G.number_of_nodes()}

        # Step 3: Detect clusters
        clusters = self.detect_clusters(G)

        # Step 4: Compute Callon metrics
        cluster_data = self.compute_callon_metrics(G, clusters)

        # Step 5: Plot strategic diagram
        fig_path = self.plot_strategic_diagram(cluster_data)

        # Step 6: Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_path = self.tables_dir / f"thematic_map_data_{timestamp}.json"
        with open(data_path, "w") as f:
            json.dump({
                "clusters": cluster_data,
                "network_stats": {
                    "nodes": G.number_of_nodes(),
                    "edges": G.number_of_edges(),
                    "density": nx.density(G),
                    "n_clusters": len(set(clusters.values())) if clusters else 0,
                },
                "parameters": {
                    "min_keyword_freq": self.min_keyword_freq,
                    "min_cooccurrence": self.min_cooccurrence,
                    "clustering_resolution": self.clustering_resolution,
                },
            }, f, indent=2)

        # Write summary table
        table_path = self.tables_dir / f"thematic_clusters_{timestamp}.md"
        with open(table_path, "w") as f:
            f.write("# Thematic Cluster Summary\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("| Cluster | Label | Keywords | Centrality | Density | Quadrant |\n")
            f.write("|---------|-------|----------|------------|---------|----------|\n")

            med_c = np.median([c["centrality"] for c in cluster_data]) if cluster_data else 0
            med_d = np.median([c["density"] for c in cluster_data]) if cluster_data else 0

            for c in sorted(cluster_data, key=lambda x: -x["centrality"]):
                if c["centrality"] >= med_c and c["density"] >= med_d:
                    quadrant = "Motor"
                elif c["centrality"] < med_c and c["density"] >= med_d:
                    quadrant = "Niche"
                elif c["centrality"] < med_c and c["density"] < med_d:
                    quadrant = "Emerging/Declining"
                else:
                    quadrant = "Basic"
                f.write(f"| {c['cluster_id']} | {c['label']} | {c['n_keywords']} | "
                       f"{c['centrality']:.1f} | {c['density']:.1f} | {quadrant} |\n")

        logger.info(f"Thematic mapping complete. {len(cluster_data)} clusters identified.")
        return {
            "clusters": cluster_data,
            "figure_path": fig_path,
            "data_path": str(data_path),
            "table_path": str(table_path),
        }


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python thematic_mapping.py <analysis_dataset.json>")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        papers = json.load(f)

    mapper = ThematicMapper()
    results = mapper.run(papers)
    print(f"\nThematic mapping complete: {len(results.get('clusters', []))} clusters")


if __name__ == "__main__":
    main()
