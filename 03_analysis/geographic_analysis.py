#!/usr/bin/env python3
"""
Geographic Analysis
- Extract countries from author affiliations
- Top 20 countries bar chart
- International collaboration percentage
- Continental distribution
"""

import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country mapping: aliases / abbreviations -> canonical name
# ---------------------------------------------------------------------------
COUNTRY_ALIASES: Dict[str, str] = {
    "usa": "United States",
    "u.s.a.": "United States",
    "u.s.a": "United States",
    "u.s.": "United States",
    "united states of america": "United States",
    "united states": "United States",
    "us": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "p.r. china": "China",
    "p.r.china": "China",
    "peoples republic of china": "China",
    "people's republic of china": "China",
    "republic of korea": "South Korea",
    "korea": "South Korea",
    "south korea": "South Korea",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "saudi arabia": "Saudi Arabia",
    "czech republic": "Czech Republic",
    "czechia": "Czech Republic",
    "russian federation": "Russia",
    "republic of ireland": "Ireland",
    "new zealand": "New Zealand",
    "south africa": "South Africa",
    "hong kong": "Hong Kong",
    "taiwan": "Taiwan",
    "sri lanka": "Sri Lanka",
    "costa rica": "Costa Rica",
    "puerto rico": "Puerto Rico",
    "trinidad and tobago": "Trinidad and Tobago",
    "the netherlands": "Netherlands",
}

# Full country list for direct matching
COUNTRIES: List[str] = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Belarus", "Belgium",
    "Benin", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil",
    "Brunei", "Bulgaria", "Burkina Faso", "Cambodia", "Cameroon", "Canada",
    "Chile", "China", "Colombia", "Congo", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Estonia", "Ethiopia", "Finland", "France",
    "Gabon", "Georgia", "Germany", "Ghana", "Greece", "Guatemala",
    "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia",
    "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Latvia", "Lebanon",
    "Libya", "Lithuania", "Luxembourg", "Macao", "Macau", "Madagascar",
    "Malawi", "Malaysia", "Mali", "Malta", "Mexico", "Moldova", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nepal",
    "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway",
    "Oman", "Pakistan", "Palestine", "Panama", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Puerto Rico", "Qatar", "Romania",
    "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Sierra Leone",
    "Singapore", "Slovakia", "Slovenia", "South Africa", "South Korea",
    "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tanzania", "Thailand", "Trinidad and Tobago", "Tunisia",
    "Turkey", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom",
    "United States", "Uruguay", "Uzbekistan", "Venezuela", "Vietnam",
    "Yemen", "Zambia", "Zimbabwe",
]

# Build regex patterns for each country (word-boundary matching)
_COUNTRY_PATTERNS: List[tuple] = []
for _c in COUNTRIES:
    _COUNTRY_PATTERNS.append((_c, re.compile(r"\b" + re.escape(_c) + r"\b", re.IGNORECASE)))

# Also build alias patterns
_ALIAS_PATTERNS: List[tuple] = []
for _alias, _canonical in COUNTRY_ALIASES.items():
    _ALIAS_PATTERNS.append((_canonical, re.compile(r"\b" + re.escape(_alias) + r"\b", re.IGNORECASE)))

# Continent mapping
CONTINENT_MAP: Dict[str, str] = {
    "United States": "North America", "Canada": "North America", "Mexico": "North America",
    "Costa Rica": "North America", "Cuba": "North America", "Dominican Republic": "North America",
    "El Salvador": "North America", "Guatemala": "North America", "Honduras": "North America",
    "Jamaica": "North America", "Nicaragua": "North America", "Panama": "North America",
    "Puerto Rico": "North America", "Trinidad and Tobago": "North America",
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Paraguay": "South America", "Peru": "South America", "Uruguay": "South America",
    "Venezuela": "South America",
    "United Kingdom": "Europe", "Germany": "Europe", "France": "Europe", "Italy": "Europe",
    "Spain": "Europe", "Netherlands": "Europe", "Belgium": "Europe", "Switzerland": "Europe",
    "Austria": "Europe", "Sweden": "Europe", "Norway": "Europe", "Denmark": "Europe",
    "Finland": "Europe", "Ireland": "Europe", "Portugal": "Europe", "Greece": "Europe",
    "Poland": "Europe", "Czech Republic": "Europe", "Hungary": "Europe", "Romania": "Europe",
    "Bulgaria": "Europe", "Croatia": "Europe", "Serbia": "Europe", "Slovenia": "Europe",
    "Slovakia": "Europe", "Estonia": "Europe", "Latvia": "Europe", "Lithuania": "Europe",
    "Luxembourg": "Europe", "Malta": "Europe", "Cyprus": "Europe", "Iceland": "Europe",
    "Albania": "Europe", "Bosnia and Herzegovina": "Europe", "Montenegro": "Europe",
    "Moldova": "Europe", "Belarus": "Europe", "Ukraine": "Europe", "Russia": "Europe",
    "Georgia": "Europe",
    "China": "Asia", "Japan": "Asia", "South Korea": "Asia", "India": "Asia",
    "Pakistan": "Asia", "Bangladesh": "Asia", "Sri Lanka": "Asia", "Nepal": "Asia",
    "Thailand": "Asia", "Vietnam": "Asia", "Malaysia": "Asia", "Singapore": "Asia",
    "Indonesia": "Asia", "Philippines": "Asia", "Taiwan": "Asia", "Hong Kong": "Asia",
    "Macao": "Asia", "Macau": "Asia", "Mongolia": "Asia", "Cambodia": "Asia",
    "Myanmar": "Asia", "Brunei": "Asia", "Kazakhstan": "Asia", "Uzbekistan": "Asia",
    "Azerbaijan": "Asia", "Armenia": "Asia",
    "Iran": "Middle East", "Iraq": "Middle East", "Israel": "Middle East",
    "Jordan": "Middle East", "Lebanon": "Middle East", "Syria": "Middle East",
    "Turkey": "Middle East", "Saudi Arabia": "Middle East", "Kuwait": "Middle East",
    "Bahrain": "Middle East", "Qatar": "Middle East", "Oman": "Middle East",
    "Yemen": "Middle East", "United Arab Emirates": "Middle East", "Palestine": "Middle East",
    "Australia": "Oceania", "New Zealand": "Oceania",
    "Egypt": "Africa", "South Africa": "Africa", "Nigeria": "Africa", "Kenya": "Africa",
    "Ghana": "Africa", "Ethiopia": "Africa", "Tanzania": "Africa", "Uganda": "Africa",
    "Cameroon": "Africa", "Senegal": "Africa", "Mali": "Africa", "Niger": "Africa",
    "Congo": "Africa", "Rwanda": "Africa", "Mozambique": "Africa", "Madagascar": "Africa",
    "Zambia": "Africa", "Zimbabwe": "Africa", "Botswana": "Africa", "Namibia": "Africa",
    "Malawi": "Africa", "Benin": "Africa", "Burkina Faso": "Africa", "Gabon": "Africa",
    "Sierra Leone": "Africa", "Morocco": "Africa", "Tunisia": "Africa", "Algeria": "Africa",
    "Libya": "Africa", "Sudan": "Africa",
}


def extract_countries_from_paper(paper: Dict) -> Set[str]:
    """Extract unique country names from author affiliation strings."""
    countries: Set[str] = set()
    authors = paper.get("authors")
    if not authors or not isinstance(authors, list):
        return countries

    for author in authors:
        aff = None
        if isinstance(author, dict):
            aff = author.get("affiliation") or author.get("affiliations") or ""
        elif isinstance(author, str):
            aff = author
        if not aff or not isinstance(aff, str):
            continue

        # Check aliases first (more specific patterns like "USA", "UK")
        for canonical, pat in _ALIAS_PATTERNS:
            if pat.search(aff):
                countries.add(canonical)

        # Check full country names
        for country, pat in _COUNTRY_PATTERNS:
            if pat.search(aff):
                countries.add(country)

    return countries


def analyze_geography(papers: List[Dict]) -> Dict:
    """Run full geographic analysis."""
    country_counter: Counter = Counter()
    continent_counter: Counter = Counter()
    papers_with_country = 0
    international_collab = 0
    paper_countries_list: List[Set[str]] = []

    for paper in papers:
        countries = extract_countries_from_paper(paper)
        paper_countries_list.append(countries)

        if countries:
            papers_with_country += 1
            for c in countries:
                country_counter[c] += 1
                continent = CONTINENT_MAP.get(c, "Other")
                continent_counter[continent] += 1

            if len(countries) > 1:
                international_collab += 1

    collab_pct = international_collab / papers_with_country * 100 if papers_with_country else 0

    return {
        "country_counts": country_counter,
        "continent_counts": continent_counter,
        "papers_with_country": papers_with_country,
        "international_collab": international_collab,
        "collab_pct": collab_pct,
        "total": len(papers),
    }


def plot_top_countries(country_counts: Counter, fig_dir: Path, top_n: int = 20) -> None:
    """Horizontal bar chart of top N countries."""
    top = country_counts.most_common(top_n)
    labels = [t[0] for t in reversed(top)]
    counts = [t[1] for t in reversed(top)]

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.viridis(np.linspace(0.2, 0.85, len(labels)))
    bars = ax.barh(labels, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title(f"Top {top_n} Countries by Publication Count", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "top_countries.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_continent_distribution(continent_counts: Counter, fig_dir: Path) -> None:
    """Pie chart of continental distribution."""
    labels = []
    sizes = []
    for cont, cnt in continent_counts.most_common():
        labels.append(cont)
        sizes.append(cnt)

    fig, ax = plt.subplots(figsize=(9, 7))
    colors = plt.cm.Set2(np.linspace(0, 1, len(labels)))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.1f%%", colors=colors,
        startangle=140, pctdistance=0.82, textprops={"fontsize": 10},
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax.set_title("Continental Distribution of Authorships", fontsize=14, fontweight="bold")
    plt.tight_layout()

    out = fig_dir / "continent_distribution.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_geography_table(geo: Dict, table_dir: Path) -> None:
    """Save geographic analysis results as markdown."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"geographic_analysis_{ts}.md"

    lines = [
        "# Geographic Analysis Summary",
        "",
        "## Overview",
        "",
        f"- Total papers: **{geo['total']}**",
        f"- Papers with identifiable country: **{geo['papers_with_country']}** "
        f"({geo['papers_with_country'] / geo['total'] * 100:.1f}%)",
        f"- International collaborations (>1 country): **{geo['international_collab']}** "
        f"({geo['collab_pct']:.1f}% of papers with country data)",
        f"- Unique countries identified: **{len(geo['country_counts'])}**",
        "",
        "## Top 20 Countries",
        "",
        "| Rank | Country | Papers | % of identified |",
        "|-----:|---------|-------:|----------------:|",
    ]
    with_c = geo["papers_with_country"] or 1
    for rank, (country, cnt) in enumerate(geo["country_counts"].most_common(20), 1):
        pct = cnt / with_c * 100
        lines.append(f"| {rank} | {country} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Continental Distribution",
        "",
        "| Continent | Authorships | % |",
        "|-----------|------------:|--:|",
    ]
    total_cont = sum(geo["continent_counts"].values()) or 1
    for cont, cnt in geo["continent_counts"].most_common():
        pct = cnt / total_cont * 100
        lines.append(f"| {cont} | {cnt} | {pct:.1f}% |")

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

    geo = analyze_geography(papers)

    logger.info("Papers with country data: %d / %d", geo["papers_with_country"], geo["total"])
    logger.info("International collaborations: %d (%.1f%%)",
                geo["international_collab"], geo["collab_pct"])
    logger.info("Unique countries: %d", len(geo["country_counts"]))
    logger.info("Top 5 countries: %s", geo["country_counts"].most_common(5))

    plot_top_countries(geo["country_counts"], fig_dir)
    plot_continent_distribution(geo["continent_counts"], fig_dir)
    save_geography_table(geo, table_dir)

    logger.info("Geographic analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
