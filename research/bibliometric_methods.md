# Bibliometric Methods Reference Guide
## Comprehensive Methodology for Advanced Bibliometric Analysis

**Research compiled: 2026-03-22**
**Purpose: Reference document for implementing advanced bibliometric analyses in Python**

---

## Table of Contents

1. [Strategic/Thematic Diagram (Callon's Strategic Diagram)](#1-strategic-thematic-diagram)
2. [Bibliometric Laws](#2-bibliometric-laws)
3. [Co-occurrence Analysis](#3-co-occurrence-analysis)
4. [Network Analysis Tools](#4-network-analysis-tools)
5. [Standard Bibliometric Indicators](#5-standard-bibliometric-indicators)
6. [Python Libraries for Bibliometrics](#6-python-libraries-for-bibliometrics)
7. [Key References](#7-key-references)

---

## 1. Strategic/Thematic Diagram (Callon's Strategic Diagram)

### 1.1 Overview

The strategic diagram (Callon, Courtial, & Laville, 1991; Cobo et al., 2011) is a two-dimensional plot where keyword clusters (themes) are positioned according to their **centrality** (x-axis) and **density** (y-axis). The mean values of centrality and density divide the space into four quadrants representing different theme categories.

### 1.2 Mathematical Formulas

#### Step 1: Build the Keyword Co-occurrence Matrix

Given a corpus of N documents, construct a co-occurrence matrix C where:
- C_ij = number of documents in which keyword i and keyword j both appear
- C_i = total occurrences of keyword i (diagonal elements or total document count for keyword i)

#### Step 2: Compute the Equivalence Index (Association Strength)

The equivalence index (also called association strength) between keywords i and j:

```
e_ij = c_ij^2 / (c_i * c_j)
```

Where:
- c_ij = co-occurrence frequency of keywords i and j
- c_i = total occurrence of keyword i
- c_j = total occurrence of keyword j

This is the measure used in the original Callon et al. (1991) co-word analysis. The bibliometrix R package implements this as:

```
Association Strength: S_ij = C_ij / (D_i * D_j)
```

Where D_i and D_j are the diagonal values (node degrees/total occurrences).

#### Step 3: Cluster Detection

Apply a community detection algorithm (typically Louvain or Walktrap) to the weighted co-occurrence network to identify thematic clusters.

#### Step 4: Compute Callon's Centrality and Density

For each cluster k:

**Centrality** (external cohesion -- importance of the theme to the field):
```
centrality_k = sum of e_ij for all pairs where i is in cluster k and j is NOT in cluster k
```

Scaled version (from Cobo et al., 2011 / SciMAT):
```
centrality_k = 10 * SUM(e_uv)  where u in cluster k, v not in cluster k
```

**Density** (internal cohesion -- development degree of the theme):
```
density_k = (sum of e_ij for all pairs where both i and j are in cluster k) / w_k
```

Where w_k is the number of keywords in cluster k.

Scaled version:
```
density_k = 100 * SUM(e_ij) / w_k  where both i,j in cluster k
```

#### Step 5: Construct the Strategic Diagram

Plot each cluster as a bubble where:
- x = centrality (or rank of centrality)
- y = density (or rank of density)
- bubble size = number of documents or keywords in the cluster

Draw dividing lines at the **mean centrality** and **mean density** (or mean of ranked values) to create four quadrants.

### 1.3 The Four Quadrants

| Quadrant | Centrality | Density | Interpretation |
|----------|-----------|---------|----------------|
| **Q1 (upper-right)** | High | High | **Motor themes**: Well-developed and important to the field. Core topics. |
| **Q2 (upper-left)** | Low | High | **Niche themes**: Well-developed internally but peripheral. Specialized topics. |
| **Q3 (lower-left)** | Low | Low | **Emerging or declining themes**: Weakly developed and marginal. Either nascent or fading. |
| **Q4 (lower-right)** | High | Low | **Basic/transversal themes**: Important to the field but not internally developed. General, foundational topics. |

### 1.4 Python Implementation

```python
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from adjustText import adjust_text

def build_cooccurrence_matrix(df, keyword_col='keywords', sep=';'):
    """
    Build keyword co-occurrence matrix from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with one row per document
    keyword_col : str
        Column containing keywords (semicolon-separated string)
    sep : str
        Separator between keywords

    Returns
    -------
    cooc_matrix : pd.DataFrame
        Square co-occurrence matrix
    """
    from itertools import combinations

    # Parse keywords
    docs_keywords = []
    for idx, row in df.iterrows():
        if pd.notna(row[keyword_col]):
            kws = [kw.strip().lower() for kw in str(row[keyword_col]).split(sep) if kw.strip()]
            docs_keywords.append(kws)

    # Count occurrences and co-occurrences
    keyword_counts = defaultdict(int)
    cooc_counts = defaultdict(int)

    for kws in docs_keywords:
        unique_kws = list(set(kws))
        for kw in unique_kws:
            keyword_counts[kw] += 1
        for pair in combinations(sorted(unique_kws), 2):
            cooc_counts[pair] += 1

    # Build matrix
    all_keywords = sorted(keyword_counts.keys())
    n = len(all_keywords)
    kw_to_idx = {kw: i for i, kw in enumerate(all_keywords)}

    matrix = np.zeros((n, n), dtype=int)
    for (kw1, kw2), count in cooc_counts.items():
        i, j = kw_to_idx[kw1], kw_to_idx[kw2]
        matrix[i, j] = count
        matrix[j, i] = count

    # Diagonal = occurrence count
    for kw, count in keyword_counts.items():
        matrix[kw_to_idx[kw], kw_to_idx[kw]] = count

    return pd.DataFrame(matrix, index=all_keywords, columns=all_keywords)


def compute_equivalence_index(cooc_matrix):
    """
    Compute the equivalence index (association strength) matrix.

    e_ij = c_ij^2 / (c_i * c_j)  [Callon's original]
    OR
    e_ij = c_ij / (c_i * c_j)    [Van Eck & Waltman association strength]

    We use the association strength (non-squared) as in bibliometrix.
    """
    matrix = cooc_matrix.values.astype(float)
    diag = np.diag(matrix).copy()

    # Avoid division by zero
    diag[diag == 0] = 1

    # Association strength: S_ij = C_ij / (D_i * D_j)
    outer = np.outer(diag, diag)
    equiv = matrix / outer
    np.fill_diagonal(equiv, 0)  # No self-loops

    return pd.DataFrame(equiv, index=cooc_matrix.index, columns=cooc_matrix.columns)


def build_network_and_detect_communities(equiv_matrix, min_weight=0.0, resolution=1.0):
    """
    Build a weighted network from the equivalence index matrix
    and detect communities using Louvain algorithm.
    """
    G = nx.Graph()
    keywords = equiv_matrix.index.tolist()

    for i in range(len(keywords)):
        for j in range(i + 1, len(keywords)):
            w = equiv_matrix.iloc[i, j]
            if w > min_weight:
                G.add_edge(keywords[i], keywords[j], weight=w)

    # Remove isolated nodes
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)

    # Louvain community detection
    communities = louvain_communities(G, weight='weight', resolution=resolution, seed=42)

    # Create cluster labels
    node_to_cluster = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            node_to_cluster[node] = idx

    return G, node_to_cluster, communities


def compute_callon_metrics(G, node_to_cluster, communities):
    """
    Compute Callon centrality and density for each cluster.

    Centrality = sum of edge weights between this cluster and other clusters
    Density = sum of internal edge weights / number of nodes in cluster
    """
    results = []

    for cluster_id, cluster_nodes in enumerate(communities):
        cluster_set = set(cluster_nodes)
        internal_weight = 0.0
        external_weight = 0.0

        for u, v, data in G.edges(data=True):
            w = data.get('weight', 1.0)
            u_in = u in cluster_set
            v_in = v in cluster_set

            if u_in and v_in:
                internal_weight += w
            elif u_in or v_in:
                external_weight += w

        n_nodes = len(cluster_set)
        density = (internal_weight / n_nodes) * 100 if n_nodes > 0 else 0
        centrality = external_weight * 10

        # Label = most connected keyword in the cluster
        subgraph = G.subgraph(cluster_set)
        if len(subgraph.nodes()) > 0:
            label = max(subgraph.nodes(),
                       key=lambda n: subgraph.degree(n, weight='weight'))
        else:
            label = list(cluster_set)[0]

        results.append({
            'cluster_id': cluster_id,
            'label': label,
            'n_keywords': n_nodes,
            'centrality': centrality,
            'density': density,
            'keywords': sorted(cluster_set)
        })

    return pd.DataFrame(results)


def plot_strategic_diagram(cluster_df, use_ranks=True, figsize=(12, 10)):
    """
    Plot Callon's strategic diagram with four quadrants.
    """
    fig, ax = plt.subplots(figsize=figsize)

    if use_ranks:
        cluster_df = cluster_df.copy()
        cluster_df['x'] = cluster_df['centrality'].rank()
        cluster_df['y'] = cluster_df['density'].rank()
    else:
        cluster_df['x'] = cluster_df['centrality']
        cluster_df['y'] = cluster_df['density']

    mean_x = cluster_df['x'].mean()
    mean_y = cluster_df['y'].mean()

    # Bubble size proportional to number of keywords
    sizes = cluster_df['n_keywords'] * 100

    scatter = ax.scatter(cluster_df['x'], cluster_df['y'], s=sizes,
                        alpha=0.6, edgecolors='black', linewidth=0.5)

    # Add labels
    texts = []
    for _, row in cluster_df.iterrows():
        texts.append(ax.text(row['x'], row['y'], row['label'],
                            fontsize=9, ha='center', va='center'))

    # Quadrant dividers
    ax.axvline(x=mean_x, color='grey', linestyle='--', linewidth=0.8)
    ax.axhline(y=mean_y, color='grey', linestyle='--', linewidth=0.8)

    # Quadrant labels
    x_range = cluster_df['x'].max() - cluster_df['x'].min()
    y_range = cluster_df['y'].max() - cluster_df['y'].min()

    ax.text(mean_x - x_range * 0.3, mean_y + y_range * 0.4,
            'NICHE THEMES\n(Q2)', fontsize=10, ha='center', color='grey', style='italic')
    ax.text(mean_x + x_range * 0.3, mean_y + y_range * 0.4,
            'MOTOR THEMES\n(Q1)', fontsize=10, ha='center', color='grey', style='italic')
    ax.text(mean_x - x_range * 0.3, mean_y - y_range * 0.4,
            'EMERGING/DECLINING\n(Q3)', fontsize=10, ha='center', color='grey', style='italic')
    ax.text(mean_x + x_range * 0.3, mean_y - y_range * 0.4,
            'BASIC THEMES\n(Q4)', fontsize=10, ha='center', color='grey', style='italic')

    ax.set_xlabel('Centrality (Relevance Degree)', fontsize=12)
    ax.set_ylabel('Density (Development Degree)', fontsize=12)
    ax.set_title("Strategic Diagram (Callon's Thematic Map)", fontsize=14)

    plt.tight_layout()
    return fig, ax
```

### 1.5 Key References for Strategic Diagram

- Callon, M., Courtial, J.-P., & Laville, F. (1991). Co-word analysis as a tool for describing the network of interactions between basic and technological research. *Scientometrics*, 22(1), 155-205.
- Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2011). An approach for detecting, quantifying, and visualizing the evolution of a research field. *Journal of Informetrics*, 5(1), 146-166.
- Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2012). SciMAT: A new science mapping analysis software tool. *Journal of the American Society for Information Science and Technology*, 63(8), 1609-1630.

---

## 2. Bibliometric Laws

### 2.1 Lotka's Law (Author Productivity Distribution)

#### Theory

Lotka's law describes the frequency distribution of scientific productivity. It states that the number of authors making n contributions is approximately 1/n^a of those making a single contribution.

#### Mathematical Formulation

**General form:**
```
f(n) = C / n^a
```

Where:
- f(n) = proportion of authors with exactly n publications
- n = number of publications
- a = exponent (Lotka's original: a = 2, the "inverse square law")
- C = constant ensuring the distribution sums to 1

**Probabilistic form:**
```
p(n) = n^(-a) / zeta(a)
```

Where zeta(a) is the Riemann zeta function: zeta(a) = SUM(k=1 to inf) 1/k^a

**Log-linear form (for fitting):**
```
log(f(n)) = log(C) - a * log(n)
```

The slope of the log-log plot yields -a.

#### Estimation Methods

1. **Linear Least Squares (on log-log data):**
   Fit log(y) = log(C) - a * log(x) using OLS regression.

2. **Maximum Likelihood Estimation:**
   Solve: psi(a) - ln(a - 1) = -(1/N) * SUM(ln(x_i))
   where psi is the digamma function.

#### Goodness-of-Fit: Kolmogorov-Smirnov Test

The K-S test compares the empirical CDF with the theoretical CDF:
```
F(x) = 1 - zeta(a, x+1) / zeta(a)
```

Where zeta(a, x+1) is the Hurwitz zeta function.

Test statistic: D = max|F_empirical(x) - F_theoretical(x)|

If p-value > 0.05, the data are consistent with Lotka's law.

#### Python Implementation

```python
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import ks_2samp
from scipy.special import zeta

def test_lotka_law(author_counts):
    """
    Test Lotka's law on author productivity data.

    Parameters
    ----------
    author_counts : pd.Series
        Number of publications per author (value_counts of author column)

    Returns
    -------
    dict with: beta (exponent), C (constant), R2, KS_stat, KS_pvalue,
    observed frequencies, expected frequencies
    """
    # Frequency distribution: how many authors published exactly n papers
    freq = author_counts.value_counts().sort_index()
    n_values = freq.index.values.astype(float)
    observed = freq.values.astype(float)
    observed_prop = observed / observed.sum()

    # Fit using log-log linear regression (Least Squares)
    log_n = np.log10(n_values)
    log_f = np.log10(observed_prop)

    # Linear fit: log(f) = log(C) - beta * log(n)
    coeffs = np.polyfit(log_n, log_f, 1)
    beta = -coeffs[0]
    C = 10 ** coeffs[1]

    # R-squared
    log_f_pred = coeffs[1] + coeffs[0] * log_n
    ss_res = np.sum((log_f - log_f_pred) ** 2)
    ss_tot = np.sum((log_f - np.mean(log_f)) ** 2)
    R2 = 1 - ss_res / ss_tot

    # Expected values under Lotka's law
    expected_prop = C / (n_values ** beta)
    expected_prop = expected_prop / expected_prop.sum()  # Normalize

    # K-S test: compare cumulative distributions
    obs_cumul = np.cumsum(observed_prop)
    exp_cumul = np.cumsum(expected_prop)
    D_max = np.max(np.abs(obs_cumul - exp_cumul))

    # Critical value at alpha=0.05 (Pao's formula)
    N = observed.sum()
    D_critical = 1.36 / np.sqrt(N)

    return {
        'beta': beta,
        'C': C,
        'R2': R2,
        'KS_D': D_max,
        'KS_critical': D_critical,
        'lotka_holds': D_max < D_critical,
        'n_values': n_values,
        'observed_prop': observed_prop,
        'expected_prop': expected_prop
    }


def plot_lotka(results, figsize=(10, 6)):
    """Plot observed vs expected Lotka's law distribution."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Linear scale
    ax1.bar(results['n_values'], results['observed_prop'],
            alpha=0.7, label='Observed', color='steelblue')
    ax1.plot(results['n_values'], results['expected_prop'],
             'r-o', label=f"Lotka (beta={results['beta']:.2f})", markersize=4)
    ax1.set_xlabel('Number of Publications')
    ax1.set_ylabel('Proportion of Authors')
    ax1.set_title("Lotka's Law Fit")
    ax1.legend()

    # Log-log scale
    ax2.scatter(np.log10(results['n_values']), np.log10(results['observed_prop']),
                label='Observed', color='steelblue')
    ax2.plot(np.log10(results['n_values']), np.log10(results['expected_prop']),
             'r-', label=f"Lotka (beta={results['beta']:.2f})")
    ax2.set_xlabel('log10(Number of Publications)')
    ax2.set_ylabel('log10(Proportion of Authors)')
    ax2.set_title("Lotka's Law (Log-Log)")
    ax2.legend()

    plt.tight_layout()
    return fig
```

### 2.2 Bradford's Law (Journal Scatter)

#### Theory

Bradford's law describes how scientific literature on a given subject is distributed across journals. A small core of journals contains approximately one-third of all relevant articles, with successive zones requiring geometrically increasing numbers of journals to contain the same volume of articles.

#### Mathematical Formulation

**Verbal formulation (zone ratios):**
```
Journals in Zone 1 : Zone 2 : Zone 3 = 1 : n : n^2
```

Where n is the Bradford multiplier (typically 2-7, field-specific).

**Zone construction:**
1. Rank journals by number of articles (descending)
2. Compute cumulative article counts
3. Divide into k zones, each with approximately A/k articles (A = total articles)
4. The Bradford multiplier: n = (journals in Zone 2) / (journals in Zone 1)

**Bradford's distribution (graphical formulation):**
```
R(r) = a + b * ln(r)    for r >= r_0 (core zone boundary)
```

Where:
- R(r) = cumulative number of articles from the first r journals
- a, b = constants estimated from data
- r_0 = number of journals in the nucleus/core zone

#### Python Implementation

```python
def test_bradford_law(df, journal_col='source_title', n_zones=3):
    """
    Test Bradford's law on journal distribution data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with one row per document
    journal_col : str
        Column containing journal/source titles
    n_zones : int
        Number of Bradford zones (default 3)

    Returns
    -------
    dict with: zone assignments, Bradford multiplier, journal ranking
    """
    # Count articles per journal
    journal_counts = df[journal_col].value_counts().sort_values(ascending=False)

    total_articles = journal_counts.sum()
    target_per_zone = total_articles / n_zones

    # Assign zones
    cumsum = 0
    zone = 1
    zones = {}
    zone_journals = {z: 0 for z in range(1, n_zones + 1)}
    zone_articles = {z: 0 for z in range(1, n_zones + 1)}

    for journal, count in journal_counts.items():
        cumsum += count
        zones[journal] = zone
        zone_journals[zone] += 1
        zone_articles[zone] += count

        if cumsum >= target_per_zone * zone and zone < n_zones:
            zone += 1

    # Bradford multiplier
    if zone_journals[1] > 0:
        multiplier = zone_journals[2] / zone_journals[1]
    else:
        multiplier = np.nan

    # Theoretical test: ratio should be approximately 1:n:n^2
    ratios = [zone_journals[z] / zone_journals[1] for z in range(1, n_zones + 1)]
    theoretical = [1, multiplier, multiplier ** 2]

    # Build Bradford curve data
    cum_journals = np.arange(1, len(journal_counts) + 1)
    cum_articles = np.cumsum(journal_counts.values)

    return {
        'zone_journals': zone_journals,
        'zone_articles': zone_articles,
        'multiplier': multiplier,
        'observed_ratios': ratios,
        'theoretical_ratios': theoretical,
        'journal_ranking': journal_counts,
        'zones': zones,
        'cum_journals': cum_journals,
        'cum_articles': cum_articles
    }


def plot_bradford(results, figsize=(10, 6)):
    """Plot Bradford's law curve."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Bradford curve (cumulative articles vs log(rank))
    ax1.plot(np.log(results['cum_journals']), results['cum_articles'],
             'b-', linewidth=2)
    ax1.set_xlabel('ln(Cumulative Number of Journals)')
    ax1.set_ylabel('Cumulative Number of Articles')
    ax1.set_title("Bradford's Law Curve")

    # Zone bar chart
    zones = list(results['zone_journals'].keys())
    j_counts = [results['zone_journals'][z] for z in zones]
    a_counts = [results['zone_articles'][z] for z in zones]

    x = np.arange(len(zones))
    width = 0.35
    ax2.bar(x - width/2, j_counts, width, label='Journals', color='steelblue')
    ax2.bar(x + width/2, a_counts, width, label='Articles', color='coral')
    ax2.set_xlabel('Zone')
    ax2.set_ylabel('Count')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'Zone {z}\n(n={j_counts[i]})' for i, z in enumerate(zones)])
    ax2.set_title(f"Bradford Zones (multiplier={results['multiplier']:.2f})")
    ax2.legend()

    plt.tight_layout()
    return fig
```

### 2.3 Zipf's Law (Word Frequency)

#### Theory

Zipf's law states that the frequency of a word is inversely proportional to its rank in the frequency table.

#### Mathematical Formulation

**Basic form:**
```
f(r) = C / r^a
```

Or equivalently:
```
f * r^a = C    (constant)
```

Where:
- f(r) = frequency of the word at rank r
- r = rank (1 = most frequent, 2 = second most frequent, etc.)
- a = exponent (typically close to 1)
- C = constant

**Log-linear form:**
```
log(f) = log(C) - a * log(r)
```

#### Python Implementation

```python
def test_zipf_law(word_frequencies):
    """
    Test Zipf's law on word/keyword frequency data.

    Parameters
    ----------
    word_frequencies : pd.Series
        Word frequency counts (e.g., keyword value_counts), sorted descending

    Returns
    -------
    dict with: alpha (exponent), C (constant), R2, ranks, frequencies
    """
    freq_sorted = word_frequencies.sort_values(ascending=False)
    ranks = np.arange(1, len(freq_sorted) + 1).astype(float)
    freqs = freq_sorted.values.astype(float)

    # Log-log linear regression
    log_r = np.log10(ranks)
    log_f = np.log10(freqs)

    coeffs = np.polyfit(log_r, log_f, 1)
    alpha = -coeffs[0]
    C = 10 ** coeffs[1]

    # R-squared
    log_f_pred = coeffs[1] + coeffs[0] * log_r
    ss_res = np.sum((log_f - log_f_pred) ** 2)
    ss_tot = np.sum((log_f - np.mean(log_f)) ** 2)
    R2 = 1 - ss_res / ss_tot

    # Expected values
    expected = C / (ranks ** alpha)

    return {
        'alpha': alpha,
        'C': C,
        'R2': R2,
        'ranks': ranks,
        'observed': freqs,
        'expected': expected,
        'words': freq_sorted.index.tolist()
    }
```

---

## 3. Co-occurrence Analysis

### 3.1 Keyword Co-occurrence Network

A keyword co-occurrence network is an undirected weighted graph where:
- **Nodes** = keywords
- **Edges** = co-occurrence relationships
- **Edge weight** = number of documents where both keywords appear

#### Construction Steps

1. Parse keywords from each document
2. For each document, create edges between all pairs of keywords
3. Aggregate edge weights across all documents
4. Optionally threshold (remove edges below minimum weight)
5. Normalize edge weights using a similarity measure

### 3.2 Normalization Methods

Given a co-occurrence matrix C with:
- C_ij = co-occurrence frequency between items i and j
- C_i = total occurrence of item i (diagonal value)

#### Association Strength (Van Eck & Waltman, 2009) -- RECOMMENDED

```
AS_ij = C_ij / (C_i * C_j)
```

Probabilistic measure. Estimates how many co-occurrences are expected if items are randomly distributed, then compares observed vs expected. Van Eck & Waltman (2009) demonstrated this is superior to set-theoretic measures for bibliometric co-occurrence data.

#### Jaccard Index

```
J_ij = C_ij / (C_i + C_j - C_ij)
```

Set-theoretic measure. Ratio of intersection to union.

#### Salton's Cosine

```
S_ij = C_ij / sqrt(C_i * C_j)
```

Set-theoretic measure. Normalizes by geometric mean of set sizes.

#### Inclusion Index (Simpson Coefficient)

```
I_ij = C_ij / min(C_i, C_j)
```

Captures containment relationship.

#### Equivalence Index (Callon)

```
E_ij = C_ij^2 / (C_i * C_j)
```

Note: This equals the square of Salton's cosine. Used in original co-word analysis by Callon et al. (1991).

#### Python Implementation

```python
def normalize_cooccurrence(cooc_matrix, method='association'):
    """
    Normalize a co-occurrence matrix using various similarity measures.

    Parameters
    ----------
    cooc_matrix : pd.DataFrame
        Raw co-occurrence matrix (diagonal = occurrence counts)
    method : str
        One of: 'association', 'jaccard', 'cosine', 'inclusion', 'equivalence'

    Returns
    -------
    pd.DataFrame : normalized similarity matrix
    """
    M = cooc_matrix.values.astype(float)
    D = np.diag(M).copy().astype(float)
    D[D == 0] = 1  # avoid division by zero

    n = len(D)
    S = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            cij = M[i, j]
            ci = D[i]
            cj = D[j]

            if method == 'association':
                s = cij / (ci * cj) if (ci * cj) > 0 else 0
            elif method == 'jaccard':
                denom = ci + cj - cij
                s = cij / denom if denom > 0 else 0
            elif method == 'cosine':
                s = cij / np.sqrt(ci * cj) if (ci * cj) > 0 else 0
            elif method == 'inclusion':
                s = cij / min(ci, cj) if min(ci, cj) > 0 else 0
            elif method == 'equivalence':
                s = (cij ** 2) / (ci * cj) if (ci * cj) > 0 else 0
            else:
                raise ValueError(f"Unknown method: {method}")

            S[i, j] = s
            S[j, i] = s

    return pd.DataFrame(S, index=cooc_matrix.index, columns=cooc_matrix.columns)
```

### 3.3 Author Co-citation Analysis (ACA)

Two authors are **co-cited** when they are both cited in the same document's reference list. The co-citation frequency reflects the degree to which the scientific community perceives them as related.

#### Construction

1. Parse reference lists from each document
2. Extract author names from each reference
3. Build author-by-document cited matrix R (rows = cited authors, cols = citing documents)
4. Co-citation matrix: CC = R * R^T
5. CC_ij = number of documents that cite both author i and author j

#### Python Implementation

```python
def build_cocitation_matrix(df, references_col='references'):
    """
    Build author co-citation matrix.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed reference data
    references_col : str
        Column containing list of cited author names per document
    """
    from itertools import combinations

    cocitation_counts = defaultdict(int)
    author_counts = defaultdict(int)

    for idx, row in df.iterrows():
        refs = row[references_col]
        if isinstance(refs, list):
            unique_authors = list(set(refs))
            for author in unique_authors:
                author_counts[author] += 1
            for pair in combinations(sorted(unique_authors), 2):
                cocitation_counts[pair] += 1

    # Build matrix (similar to co-occurrence matrix above)
    all_authors = sorted(author_counts.keys())
    n = len(all_authors)
    auth_to_idx = {a: i for i, a in enumerate(all_authors)}

    matrix = np.zeros((n, n), dtype=int)
    for (a1, a2), count in cocitation_counts.items():
        i, j = auth_to_idx[a1], auth_to_idx[a2]
        matrix[i, j] = count
        matrix[j, i] = count

    for author, count in author_counts.items():
        matrix[auth_to_idx[author], auth_to_idx[author]] = count

    return pd.DataFrame(matrix, index=all_authors, columns=all_authors)
```

### 3.4 Bibliographic Coupling

Two documents are **bibliographically coupled** when they cite at least one common reference. The coupling strength equals the number of shared references.

#### Matrix Construction

Given a citation matrix C (rows = citing documents, columns = cited references):
```
B = C * C^T
```

Where B_ij = number of references shared between documents i and j.

#### Normalized (Salton's Cosine):
```
BC_ij = B_ij / sqrt(B_ii * B_jj)
```

#### Python Implementation

```python
def build_bibliographic_coupling(df, references_col='cited_references'):
    """
    Build bibliographic coupling matrix using matrix multiplication.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with one row per document
    references_col : str
        Column containing list of cited references per document
    """
    from scipy.sparse import lil_matrix

    # Collect all unique references
    all_refs = set()
    doc_refs = []
    for idx, row in df.iterrows():
        refs = row[references_col] if isinstance(row[references_col], list) else []
        doc_refs.append(refs)
        all_refs.update(refs)

    all_refs = sorted(all_refs)
    ref_to_idx = {r: i for i, r in enumerate(all_refs)}

    # Build sparse citation matrix C (documents x references)
    n_docs = len(df)
    n_refs = len(all_refs)
    C = lil_matrix((n_docs, n_refs), dtype=int)

    for doc_idx, refs in enumerate(doc_refs):
        for ref in refs:
            C[doc_idx, ref_to_idx[ref]] = 1

    C = C.tocsr()

    # Bibliographic coupling: B = C * C^T
    B = C.dot(C.T).toarray()

    # Normalize with Salton's cosine
    diag = np.diag(B).astype(float)
    diag[diag == 0] = 1
    outer = np.outer(np.sqrt(diag), np.sqrt(diag))
    B_norm = B / outer
    np.fill_diagonal(B_norm, 0)

    return pd.DataFrame(B_norm, index=df.index, columns=df.index)
```

---

## 4. Network Analysis Tools

### 4.1 NetworkX for Bibliometric Networks

NetworkX is the primary Python library for constructing and analyzing bibliometric networks.

#### Key Network Metrics

```python
def compute_network_statistics(G):
    """Compute comprehensive network statistics for a bibliometric network."""
    stats = {}

    # Basic properties
    stats['n_nodes'] = G.number_of_nodes()
    stats['n_edges'] = G.number_of_edges()
    stats['density'] = nx.density(G)

    # Connectedness
    if nx.is_connected(G):
        stats['is_connected'] = True
        stats['diameter'] = nx.diameter(G)
        stats['avg_path_length'] = nx.average_shortest_path_length(G)
    else:
        stats['is_connected'] = False
        components = list(nx.connected_components(G))
        stats['n_components'] = len(components)
        largest = max(components, key=len)
        stats['largest_component_size'] = len(largest)
        H = G.subgraph(largest)
        stats['diameter'] = nx.diameter(H)
        stats['avg_path_length'] = nx.average_shortest_path_length(H)

    # Centrality measures
    stats['degree_centrality'] = nx.degree_centrality(G)
    stats['betweenness_centrality'] = nx.betweenness_centrality(G, weight='weight')
    stats['closeness_centrality'] = nx.closeness_centrality(G)
    stats['pagerank'] = nx.pagerank(G, weight='weight')

    # Clustering
    stats['avg_clustering'] = nx.average_clustering(G, weight='weight')
    stats['transitivity'] = nx.transitivity(G)

    return stats
```

### 4.2 Community Detection Algorithms

#### Louvain Algorithm (Recommended)

```python
from networkx.algorithms.community import louvain_communities

# Native NetworkX implementation (NetworkX >= 2.7)
communities = louvain_communities(G, weight='weight', resolution=1.0, seed=42)

# python-louvain package (alternative)
# pip install python-louvain
import community as community_louvain
partition = community_louvain.best_partition(G, weight='weight', resolution=1.0)
modularity = community_louvain.modularity(partition, G, weight='weight')
```

Key parameters:
- **resolution**: < 1 favors larger communities, > 1 favors smaller communities
- **seed**: for reproducibility
- Modularity > 0.3 indicates good community structure; > 0.7 is excellent

#### Walktrap Algorithm

```python
# Using igraph (alternative to Louvain)
# pip install python-igraph
import igraph as ig

# Convert NetworkX graph to igraph
edges = [(u, v, d['weight']) for u, v, d in G.edges(data=True)]
ig_graph = ig.Graph.TupleList(edges, weights=True)

# Walktrap (random walks-based)
walktrap = ig_graph.community_walktrap(weights='weight', steps=4)
clusters = walktrap.as_clustering()
```

#### Leiden Algorithm (improved Louvain)

```python
# pip install leidenalg python-igraph
import leidenalg

# Using igraph graph
partition = leidenalg.find_partition(ig_graph,
                                      leidenalg.ModularityVertexPartition,
                                      weights='weight')
```

### 4.3 Visualization Best Practices for Publication-Quality Figures

```python
def plot_bibliometric_network(G, partition, figsize=(14, 14),
                               node_scale=300, font_size=8,
                               top_n_labels=30, min_edge_weight=None,
                               layout='spring', dpi=300):
    """
    Create a publication-quality bibliometric network visualization.

    Parameters
    ----------
    G : nx.Graph
        The bibliometric network
    partition : dict
        Node -> community mapping
    figsize : tuple
        Figure size in inches
    node_scale : int
        Scaling factor for node sizes
    font_size : int
        Font size for node labels
    top_n_labels : int
        Only label the top N nodes by degree
    min_edge_weight : float or None
        Minimum edge weight to display
    layout : str
        Layout algorithm: 'spring', 'kamada_kawai', 'circular'
    dpi : int
        Resolution for saving
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Compute layout
    if layout == 'spring':
        k = 1.5 / np.sqrt(G.number_of_nodes())  # Adjust spacing
        pos = nx.spring_layout(G, k=k, iterations=50, weight='weight', seed=42)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G, weight='weight')
    else:
        pos = nx.circular_layout(G)

    # Node sizes based on weighted degree
    degrees = dict(G.degree(weight='weight'))
    max_deg = max(degrees.values()) if degrees else 1
    node_sizes = [degrees.get(n, 0) / max_deg * node_scale for n in G.nodes()]

    # Node colors based on community
    unique_communities = sorted(set(partition.values()))
    cmap = plt.cm.Set3 if len(unique_communities) <= 12 else plt.cm.tab20
    color_map = {c: cmap(i / max(len(unique_communities) - 1, 1))
                 for i, c in enumerate(unique_communities)}
    node_colors = [color_map[partition[n]] for n in G.nodes()]

    # Filter edges if needed
    if min_edge_weight is not None:
        edges_to_draw = [(u, v) for u, v, d in G.edges(data=True)
                         if d.get('weight', 0) >= min_edge_weight]
    else:
        edges_to_draw = list(G.edges())

    # Edge widths
    edge_weights = [G[u][v].get('weight', 1) for u, v in edges_to_draw]
    max_ew = max(edge_weights) if edge_weights else 1
    edge_widths = [0.1 + 2.0 * (w / max_ew) for w in edge_weights]

    # Draw
    nx.draw_networkx_edges(G, pos, edgelist=edges_to_draw,
                           width=edge_widths, alpha=0.3,
                           edge_color='grey', ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                           node_color=node_colors, alpha=0.8,
                           edgecolors='black', linewidths=0.5, ax=ax)

    # Label only top nodes
    top_nodes = sorted(G.nodes(), key=lambda n: degrees.get(n, 0), reverse=True)[:top_n_labels]
    labels = {n: n for n in top_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=font_size, ax=ax)

    ax.set_axis_off()
    plt.tight_layout()

    return fig, ax
```

#### Layout Recommendations for Bibliometric Networks

| Network Type | Recommended Layout | Reasoning |
|-------------|-------------------|-----------|
| Keyword co-occurrence | Spring (Fruchterman-Reingold) | Clusters naturally emerge |
| Co-citation | Kamada-Kawai or Spring | Shows intellectual structure |
| Collaboration | Spring with high k | Keeps country/institution groups visible |
| Small networks (<50 nodes) | Kamada-Kawai | More deterministic, cleaner |
| Large networks (>500 nodes) | Spring with `k=0.1-0.3` | Handles scale |

#### Matplotlib Settings for Publication Quality

```python
# Global settings for publication-quality figures
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.transparent': False,
})
```

---

## 5. Standard Bibliometric Indicators

### 5.1 Author-Level Metrics

#### h-index (Hirsch, 2005)

The h-index is the largest value h such that the author has h publications with at least h citations each.

```python
def compute_h_index(citations):
    """
    Compute h-index from a list of citation counts.

    Parameters
    ----------
    citations : list or np.array
        Citation count for each publication

    Returns
    -------
    int : h-index
    """
    sorted_citations = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(sorted_citations):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h
```

#### g-index (Egghe, 2006)

The g-index is the largest value g such that the top g publications have together at least g^2 citations.

```python
def compute_g_index(citations):
    """
    Compute g-index from a list of citation counts.
    g-index: largest g such that top g papers have >= g^2 total citations.
    Note: g >= h always.
    """
    sorted_citations = sorted(citations, reverse=True)
    cumsum = 0
    g = 0
    for i, c in enumerate(sorted_citations):
        cumsum += c
        if cumsum >= (i + 1) ** 2:
            g = i + 1
        else:
            break
    return g
```

#### i10-index (Google Scholar)

Number of publications with at least 10 citations.

```python
def compute_i10_index(citations):
    """i10-index: number of publications with >= 10 citations."""
    return sum(1 for c in citations if c >= 10)
```

### 5.2 Collaboration Metrics

#### Collaboration Index (CI)

The Collaboration Index measures the mean number of authors per article:

```
CI = Total number of authors across all articles / Total number of articles
```

Note: This counts author slots, not unique authors. A paper with 3 authors contributes 3 to the numerator.

```python
def compute_collaboration_index(df, authors_col='authors', sep=';'):
    """
    Compute Collaboration Index = mean authors per paper.
    """
    author_counts = df[authors_col].apply(
        lambda x: len(str(x).split(sep)) if pd.notna(x) else 0
    )
    ci = author_counts.mean()
    return ci
```

#### Degree of Collaboration (DC) -- Subramanyam's formula

```
DC = N_m / (N_s + N_m)
```

Where:
- N_m = number of multi-authored publications
- N_s = number of single-authored publications

```python
def compute_degree_of_collaboration(df, authors_col='authors', sep=';'):
    """Subramanyam's Degree of Collaboration."""
    author_counts = df[authors_col].apply(
        lambda x: len(str(x).split(sep)) if pd.notna(x) else 0
    )
    n_multi = (author_counts > 1).sum()
    n_single = (author_counts == 1).sum()
    dc = n_multi / (n_single + n_multi) if (n_single + n_multi) > 0 else 0
    return dc
```

#### Collaborative Coefficient (CC) -- Ajiferuke et al. (1988)

```
CC = 1 - SUM(j=1 to k) [ (1/j) * f_j ] / N
```

Where:
- f_j = number of j-authored papers
- N = total number of papers
- k = maximum number of authors on any paper

```python
def compute_collaborative_coefficient(df, authors_col='authors', sep=';'):
    """Ajiferuke's Collaborative Coefficient."""
    author_counts = df[authors_col].apply(
        lambda x: len(str(x).split(sep)) if pd.notna(x) else 0
    )
    N = len(df)
    weighted_sum = sum((1.0 / j) * (author_counts == j).sum()
                       for j in range(1, author_counts.max() + 1))
    cc = 1 - weighted_sum / N
    return cc
```

#### International Collaboration Percentage

```
ICP = (Number of papers with authors from >= 2 countries) / (Total papers) * 100
```

```python
def compute_international_collaboration(df, country_col='countries', sep=';'):
    """
    Compute international collaboration percentage.
    Requires a column with country affiliations per paper.
    """
    def count_unique_countries(x):
        if pd.isna(x):
            return 0
        countries = [c.strip() for c in str(x).split(sep) if c.strip()]
        return len(set(countries))

    n_countries = df[country_col].apply(count_unique_countries)
    intl_papers = (n_countries >= 2).sum()
    total_papers = len(df)

    icp = (intl_papers / total_papers) * 100 if total_papers > 0 else 0
    return icp
```

### 5.3 Document-Level and Collection-Level Metrics

#### Annual Growth Rate (AGR)

```
AGR = ((Publications in year t) - (Publications in year t-1)) / (Publications in year t-1) * 100
```

#### Compound Annual Growth Rate (CAGR)

```
CAGR = ((Publications in final year / Publications in initial year)^(1/n) - 1) * 100
```

Where n = number of years in the period.

#### Mean Citation Rate

```
MCR = Total citations / Total publications
```

#### Publication Doubling Time

```
DT = ln(2) / ln(1 + AGR/100)
```

```python
def compute_collection_metrics(df, year_col='year', citation_col='cited_by'):
    """Compute collection-level bibliometric metrics."""
    metrics = {}

    # Publications per year
    pub_per_year = df[year_col].value_counts().sort_index()

    # Compound Annual Growth Rate
    years = sorted(pub_per_year.index)
    if len(years) >= 2:
        n_years = years[-1] - years[0]
        if n_years > 0 and pub_per_year[years[0]] > 0:
            metrics['CAGR'] = ((pub_per_year[years[-1]] / pub_per_year[years[0]])
                               ** (1 / n_years) - 1) * 100

    # Mean Citation Rate
    if citation_col in df.columns:
        metrics['mean_citation_rate'] = df[citation_col].mean()
        metrics['median_citation_rate'] = df[citation_col].median()

    # Total metrics
    metrics['total_publications'] = len(df)
    metrics['timespan'] = f"{years[0]}-{years[-1]}" if years else "N/A"

    return metrics
```

---

## 6. Python Libraries for Bibliometrics

### 6.1 Available Libraries (as of 2025-2026)

| Library | Focus | Data Sources | Maintained? | Key Features |
|---------|-------|-------------|-------------|--------------|
| **pybliometrics** | Scopus API wrapper | Scopus only | Yes | Retrieve documents, authors, affiliations from Scopus |
| **metaknowledge** | Bibliometric & network analysis | WoS, Scopus, PubMed, NSF | Yes | Network construction, citation analysis, export to NetworkX |
| **PyBibX** | Full bibliometric analysis + AI | WoS, Scopus, PubMed | Yes | EDA, networks, thematic analysis, AI (BERT, GPT integration) |
| **Biblium** | Advanced bibliometric analysis | Multiple | New (2025) | Comprehensive metrics, concept mapping, LLM integration |
| **litstudy** | Literature analysis in Jupyter | Scopus, Semantic Scholar, DBLP, CrossRef | Yes | Automated analysis in Jupyter notebooks |
| **pyscisci** | Science of science | WoS, MAG, OpenAlex | Yes | Network analysis, impact metrics |
| **tethne** | Bibliometric network analysis | WoS, Scopus | Aging | Co-citation, bibliographic coupling, direct integration with NetworkX |

### 6.2 What Exists vs What We Need to Build

#### Already Available (use existing libraries or straightforward with pandas/networkx):

- Basic descriptive statistics (pandas)
- Publication trend analysis (pandas + matplotlib)
- Author productivity distributions (pandas)
- Citation analysis (pandas)
- Network construction: co-occurrence, co-citation, bibliographic coupling (networkx)
- Community detection: Louvain, Leiden (networkx, python-louvain, leidenalg)
- h-index, g-index, i10-index (simple functions)
- Geographic analysis (with geopandas for mapping)
- Word clouds (wordcloud library)

#### Need to Build Ourselves (custom implementation required):

1. **Strategic/Thematic Diagram**: No ready-made Python equivalent of bibliometrix's thematicMap(). Must implement:
   - Co-occurrence matrix construction
   - Association strength computation
   - Community detection
   - Callon centrality/density computation
   - Four-quadrant plotting

2. **Bibliometric Law Testing**: No single Python library provides Lotka/Bradford/Zipf tests with proper statistical tests. Must implement:
   - Lotka's law fitting + K-S test
   - Bradford zone analysis
   - Zipf's law fitting

3. **Thematic Evolution Analysis**: Tracking how themes evolve across time periods. Must implement:
   - Time-sliced thematic maps
   - Overlap/similarity between clusters across periods
   - Sankey-style evolution diagrams

4. **Collaboration Network Metrics**: Custom functions for:
   - Collaboration Index, Degree of Collaboration
   - International collaboration percentage
   - Collaboration network construction from affiliation data

### 6.3 Recommended Technology Stack

```
Core:
  - pandas >= 2.0          # Data manipulation
  - numpy >= 1.24          # Numerical computation
  - scipy >= 1.10          # Statistical tests, optimization
  - matplotlib >= 3.7      # Visualization
  - seaborn >= 0.12        # Statistical visualization

Network Analysis:
  - networkx >= 3.0        # Graph construction and analysis
  - python-louvain >= 0.16 # Louvain community detection (pip: community)
  - leidenalg >= 0.10      # Leiden algorithm (optional, improved Louvain)

Additional:
  - scikit-learn           # For TF-IDF, clustering if needed
  - wordcloud              # Word cloud visualization
  - adjustText             # Non-overlapping text labels
  - openpyxl               # Excel export
```

---

## 7. Key References

### Foundational Methodology

1. Callon, M., Courtial, J.-P., & Laville, F. (1991). Co-word analysis as a tool for describing the network of interactions between basic and technological research: The case of polymer chemistry. *Scientometrics*, 22(1), 155-205.

2. Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2011). An approach for detecting, quantifying, and visualizing the evolution of a research field: A practical application to the fuzzy sets theory field. *Journal of Informetrics*, 5(1), 146-166.

3. Cobo, M. J., Lopez-Herrera, A. G., Herrera-Viedma, E., & Herrera, F. (2012). SciMAT: A new science mapping analysis software tool. *Journal of the American Society for Information Science and Technology*, 63(8), 1609-1630.

### Bibliometric Laws

4. Lotka, A. J. (1926). The frequency distribution of scientific productivity. *Journal of the Washington Academy of Sciences*, 16(12), 317-323.

5. Bradford, S. C. (1934). Sources of information on specific subjects. *Engineering*, 137, 85-86.

6. Zipf, G. K. (1949). *Human behavior and the principle of least effort*. Addison-Wesley.

7. Pao, M. L. (1985). Lotka's law: A testing procedure. *Information Processing & Management*, 21(4), 305-320.

### Network Analysis & Normalization

8. Van Eck, N. J., & Waltman, L. (2009). How to normalize cooccurrence data? An analysis of some well-known similarity measures. *Journal of the American Society for Information Science and Technology*, 60(8), 1635-1651.

9. Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.

10. Van Eck, N. J., & Waltman, L. (2014). Visualizing bibliometric networks. In *Measuring scholarly impact* (pp. 285-320). Springer.

### Bibliometric Indicators

11. Hirsch, J. E. (2005). An index to quantify an individual's scientific research output. *Proceedings of the National Academy of Sciences*, 102(46), 16569-16572.

12. Egghe, L. (2006). Theory and practise of the g-index. *Scientometrics*, 69(1), 131-152.

13. Subramanyam, K. (1983). Bibliometric studies of research collaboration: A review. *Journal of Information Science*, 6(1), 33-38.

14. Ajiferuke, I., Burell, Q., & Tague, J. (1988). Collaborative coefficient: A single measure of the degree of collaboration in research. *Scientometrics*, 14(5-6), 421-433.

### Software & Tools

15. Aria, M., & Cuccurullo, C. (2017). bibliometrix: An R-tool for comprehensive science mapping analysis. *Journal of Informetrics*, 11(4), 959-975.

16. Pereira, V., & Basilio, M. P. (2023). pyBibX -- A Python Library for Bibliometric and Scientometric Analysis Powered with Artificial Intelligence Tools. arXiv:2304.14516.

### Co-citation and Bibliographic Coupling

17. Small, H. (1973). Co-citation in the scientific literature: A new measure of the relationship between two documents. *Journal of the American Society for Information Science*, 24(4), 265-269.

18. Kessler, M. M. (1963). Bibliographic coupling between scientific papers. *American Documentation*, 14(1), 10-25.

19. White, H. D., & Griffith, B. C. (1981). Author cocitation: A literature measure of intellectual structure. *Journal of the American Society for Information Science*, 32(3), 163-171.

---

## Appendix A: Complete Pipeline Summary

The recommended analysis pipeline for our bibliometric study:

```
1. Data Preparation
   - Clean and standardize keywords, author names, affiliations
   - Parse reference lists for co-citation/coupling analysis

2. Descriptive Statistics
   - Publication trends (annual output, CAGR)
   - Author productivity (Lotka's law test)
   - Journal distribution (Bradford's law test)
   - Keyword frequency (Zipf's law test)

3. Collaboration Analysis
   - Collaboration Index, Degree of Collaboration
   - International collaboration percentage
   - Co-authorship network

4. Co-occurrence Analysis
   - Build keyword co-occurrence matrix
   - Normalize with association strength
   - Construct weighted network
   - Community detection (Louvain)

5. Strategic/Thematic Diagram
   - Compute Callon centrality and density per cluster
   - Plot four-quadrant strategic diagram
   - Interpret motor/niche/emerging/basic themes

6. Citation Analysis
   - h-index, g-index for top authors
   - Most cited documents and authors
   - Citation trends over time

7. Network Visualization
   - Keyword co-occurrence network
   - Author collaboration network
   - Publication-quality figures (300 DPI, serif fonts)
```

---

*This document serves as the methodological reference for implementing advanced bibliometric analyses. All formulas and code snippets have been cross-referenced with the bibliometrix R package source code and the primary literature.*
