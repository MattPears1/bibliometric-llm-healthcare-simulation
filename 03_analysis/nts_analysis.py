#!/usr/bin/env python3
"""
Non-Technical Skills (NTS) Domain Analysis
- Classify papers by NTS domains via regex on title + abstract
- Bar chart of NTS domain frequencies
- Cross-tab heatmap: NTS domain by year

v2 IMPROVEMENTS (Methodology Review 2026-03-22):
  - "Communication" domain: tightened from broad \\bcommunicat\\w+\\b to
    context-aware matching. Bare "communication" now requires proximity to
    training/simulation/education context words. This prevents cancer
    communication, science communication, etc. from being classified as NTS.
  - "Teamwork": similarly, "collaborat\\w+" now requires educational context
    proximity to avoid matching generic research collaboration mentions.
  - "Leadership": removed overly broad "leading" pattern (matched "leading
    cause", "leading to", etc.). Added "team leader" and "followership".
  - "Decision-making": added "therapeutic reasoning", "clinical decision",
    "prioriti[sz]ation".
  - "Situational awareness": added "anticipat" with context, "cue
    recognition", "fixation error".
  - "Stress management": added "burnout", "wellbeing", "well-being",
    "emotional regulation", "psychological safety".
  - "CRM": added TEAMSTEPPS, SPLINTS, and other validated team assessment
    frameworks.
  - Added new domain "Task management" covering workload distribution,
    resource allocation, and planning in clinical context.
  - Added new domain "Professionalism" covering professional identity,
    ethical reasoning, reflective practice.
"""

import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: context-aware pattern matching
# ---------------------------------------------------------------------------
# Education/training context words that should be near broad NTS terms
# All use word boundaries to prevent substring false positives
# (e.g., "nts" matching inside "patients", "skill" matching "deskilling")
_CONTEXT_WORDS = (
    r"\btraining\b|\bsimulation\b|\beducation\b|\bskills?\b|\bcompetenc\w+\b|"
    r"\bdebrief\w*\b|\bassessment\b|\bcurriculum\b|\bteach\w*\b|\blearn\w*\b|"
    r"\bworkshop\b|\bcourse\b|\bfaculty\b|\bresidents?\b|\bstudents?\b|"
    r"\btrainees?\b|\bperformance\b|\bfeedback\b|\bscenarios?\b|\bosce\b|"
    r"\bnts\b|\bnon.?technical\b|\bnontechnical\b|\bsim.?based\b|"
    r"\bmedical education\b|\bnursing education\b|"
    r"\bsurgical education\b|\bclinical training\b"
)


def _context_pattern(core_pattern: str, context_window: int = 250) -> re.Pattern:
    """
    Build a compiled regex that matches `core_pattern` ONLY if one of the
    education/training context words appears within `context_window` characters
    before or after it.

    This uses a lookahead/lookbehind approximation: we match the core pattern
    and then verify context in code rather than trying a single giant regex.
    Returns a special sentinel pattern; actual matching is done in
    _context_search().
    """
    # We return the core pattern compiled; the caller handles context checking
    return re.compile(core_pattern, re.IGNORECASE)


# Store context-dependent patterns separately
_CONTEXT_RE = re.compile(_CONTEXT_WORDS, re.IGNORECASE)


def _has_context(text: str, match_start: int, match_end: int,
                 window: int = 250) -> bool:
    """Check if education/training context words appear near the match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    snippet = text[start:end]
    return bool(_CONTEXT_RE.search(snippet))


class _ContextPattern:
    """A pattern that only matches if education context is nearby."""

    def __init__(self, pattern_str: str, window: int = 250):
        self.pattern = re.compile(pattern_str, re.IGNORECASE)
        self.window = window

    def search(self, text: str) -> Optional[re.Match]:
        for m in self.pattern.finditer(text):
            if _has_context(text, m.start(), m.end(), self.window):
                return m
        return None

    @property
    def flags(self):
        return self.pattern.flags


# ---------------------------------------------------------------------------
# NTS domain definitions: domain -> list of pattern objects
# Each can be a re.Pattern (standard) or _ContextPattern (context-aware)
# ---------------------------------------------------------------------------
NTS_DOMAINS: Dict[str, list] = {
    "Communication": [
        # Context-aware: "communication/communicating/etc." only counts
        # when near education/training terms
        _ContextPattern(r"\bcommunicat\w+\b"),
        re.compile(r"\bempathy\b", re.IGNORECASE),
        re.compile(r"\bempathic\b", re.IGNORECASE),
        re.compile(r"\bhistory.?taking\b", re.IGNORECASE),
        re.compile(r"\bcounsell?ing\b", re.IGNORECASE),
        re.compile(r"\bpatient.?interaction\b", re.IGNORECASE),
        re.compile(r"\bshared decision\b", re.IGNORECASE),
        re.compile(r"\bclosed.?loop\s+communicat\w+\b", re.IGNORECASE),
        re.compile(r"\bbreaking bad news\b", re.IGNORECASE),
        re.compile(r"\bdifficult conversation\b", re.IGNORECASE),
        re.compile(r"\bmotivational interview\w*\b", re.IGNORECASE),
        re.compile(r"\bpatient.?centred\s+communicat\w+\b", re.IGNORECASE),
        re.compile(r"\bpatient.?centered\s+communicat\w+\b", re.IGNORECASE),
        re.compile(r"\bhandover\b", re.IGNORECASE),
        re.compile(r"\bhandoff\b", re.IGNORECASE),
        re.compile(r"\bSBAR\b"),  # Situation-Background-Assessment-Recommendation
    ],
    "Teamwork": [
        re.compile(r"\bteamwork\b", re.IGNORECASE),
        re.compile(r"\bteam\s+training\b", re.IGNORECASE),
        re.compile(r"\bteam\s+performance\b", re.IGNORECASE),
        re.compile(r"\binterprofessional\b", re.IGNORECASE),
        re.compile(r"\bmultidisciplinary\s+team\b", re.IGNORECASE),
        # Context-aware: "collaboration" only counts near education context
        _ContextPattern(r"\bcollaborat\w+\b"),
        re.compile(r"\bcrew resource\b", re.IGNORECASE),
        re.compile(r"\bteam.?based\s+learning\b", re.IGNORECASE),
        re.compile(r"\bshared mental model\b", re.IGNORECASE),
        re.compile(r"\brole\s+allocat\w+\b", re.IGNORECASE),
    ],
    "Leadership": [
        re.compile(r"\bleadership\b", re.IGNORECASE),
        # Removed: \bleading\b -- too many false positives
        # ("leading cause", "leading to")
        re.compile(r"\bsupervis\w+\b", re.IGNORECASE),
        re.compile(r"\bmentor\w+\b", re.IGNORECASE),
        re.compile(r"\bteam\s+leader\b", re.IGNORECASE),
        re.compile(r"\bfollowership\b", re.IGNORECASE),
        re.compile(r"\bdelegat\w+\b", re.IGNORECASE),
    ],
    "Decision-making": [
        re.compile(r"\bdecision.?making\b", re.IGNORECASE),
        re.compile(r"\bclinical reasoning\b", re.IGNORECASE),
        re.compile(r"\bclinical judg[e]?ment\b", re.IGNORECASE),
        re.compile(r"\bdiagnostic reasoning\b", re.IGNORECASE),
        re.compile(r"\btherapeutic reasoning\b", re.IGNORECASE),
        re.compile(r"\bclinical decision\b", re.IGNORECASE),
        re.compile(r"\bprioritiz\w+\b", re.IGNORECASE),
        re.compile(r"\bprioritisation\b", re.IGNORECASE),
        re.compile(r"\bheurist\w+\b", re.IGNORECASE),
    ],
    "Situational awareness": [
        re.compile(r"\bsituation\w*\s*awareness\b", re.IGNORECASE),
        re.compile(r"\bvigilance\b", re.IGNORECASE),
        _ContextPattern(r"\banticipath?\w+\b"),  # anticipation/anticipating near training
        re.compile(r"\bcue\s+recognition\b", re.IGNORECASE),
        re.compile(r"\bfixation\s+error\b", re.IGNORECASE),
        re.compile(r"\benvironmental\s+scanning\b", re.IGNORECASE),
    ],
    "Stress management": [
        re.compile(r"\bstress\s+manage\w+\b", re.IGNORECASE),
        re.compile(r"\bcognitive load\b", re.IGNORECASE),
        re.compile(r"\bresilience\b", re.IGNORECASE),
        re.compile(r"\bburnout\b", re.IGNORECASE),
        re.compile(r"\bwell.?being\b", re.IGNORECASE),
        re.compile(r"\bemotional\s+regulat\w+\b", re.IGNORECASE),
        re.compile(r"\bpsychological\s+safety\b", re.IGNORECASE),
        re.compile(r"\bfatigue\s+manage\w+\b", re.IGNORECASE),
        re.compile(r"\bcoping\s+strateg\w+\b", re.IGNORECASE),
    ],
    "CRM": [
        re.compile(r"\bcrisis resource management\b", re.IGNORECASE),
        re.compile(r"\bcrew resource management\b", re.IGNORECASE),
        re.compile(r"\bCRM\b"),
        re.compile(r"\bTEAMSTEPPS\b", re.IGNORECASE),
        re.compile(r"\bSPLINTS\b"),  # scrub practitioners' list of NTS
    ],
    "Task management": [
        re.compile(r"\btask\s+manage\w+\b", re.IGNORECASE),
        re.compile(r"\bworkload\s+manage\w+\b", re.IGNORECASE),
        re.compile(r"\bworkload\s+distribut\w+\b", re.IGNORECASE),
        re.compile(r"\bresource\s+allocat\w+\b", re.IGNORECASE),
        re.compile(r"\bplanning\s+and\s+prepar\w+\b", re.IGNORECASE),
        re.compile(r"\btask\s+prioriti[sz]\w+\b", re.IGNORECASE),
    ],
    "Professionalism": [
        re.compile(r"\bprofessional\s+identity\b", re.IGNORECASE),
        re.compile(r"\bethical\s+reasoning\b", re.IGNORECASE),
        re.compile(r"\breflective\s+practice\b", re.IGNORECASE),
        re.compile(r"\bprofessionalism\b", re.IGNORECASE),
        re.compile(r"\bself.?assessment\b", re.IGNORECASE),
    ],
}


def _get_text(paper: Dict) -> str:
    """Concatenate title and abstract into a single searchable string."""
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    return f"{title} {abstract}"


def classify_papers(papers: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, int]]:
    """
    Classify papers into NTS domains.
    Returns:
        domain_papers: {domain: [paper, ...]}
        domain_counts: {domain: int}
    """
    domain_papers: Dict[str, List[Dict]] = defaultdict(list)
    domain_counts: Counter = Counter()

    for paper in papers:
        text = _get_text(paper)
        for domain, patterns in NTS_DOMAINS.items():
            if any(pat.search(text) for pat in patterns):
                domain_papers[domain].append(paper)
                domain_counts[domain] += 1

    return dict(domain_papers), dict(domain_counts)


def plot_domain_frequencies(domain_counts: Dict[str, int], fig_dir: Path) -> None:
    """Horizontal bar chart of NTS domain frequencies."""
    domains = sorted(domain_counts.keys(), key=lambda d: domain_counts[d])
    counts = [domain_counts[d] for d in domains]

    fig, ax = plt.subplots(figsize=(10, max(6, len(domains) * 0.55)))
    colors = plt.cm.Set2(np.linspace(0, 1, len(domains)))
    bars = ax.barh(domains, counts, color=colors, edgecolor="grey", linewidth=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Number of Papers", fontsize=12)
    ax.set_title("Non-Technical Skills (NTS) Domain Frequencies", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = fig_dir / "nts_domain_frequencies.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_domain_year_heatmap(domain_papers: Dict[str, List[Dict]], fig_dir: Path) -> None:
    """Heatmap of NTS domain counts by publication year."""
    # Collect all years
    all_years: set = set()
    for papers in domain_papers.values():
        for p in papers:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                all_years.add(int(y))

    if not all_years:
        logger.warning("No valid year data for heatmap")
        return

    years = sorted(all_years)
    domains = sorted(domain_papers.keys())

    matrix = np.zeros((len(domains), len(years)), dtype=int)
    year_idx = {y: i for i, y in enumerate(years)}

    for di, domain in enumerate(domains):
        for p in domain_papers[domain]:
            y = p.get("year")
            if y and isinstance(y, (int, float)):
                yi = year_idx.get(int(y))
                if yi is not None:
                    matrix[di, yi] += 1

    fig, ax = plt.subplots(figsize=(max(10, len(years) * 0.9), max(6, len(domains) * 0.7)))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(domains)))
    ax.set_yticklabels(domains, fontsize=10)

    # Annotate cells
    for i in range(len(domains)):
        for j in range(len(years)):
            val = matrix[i, j]
            if val > 0:
                text_color = "white" if val > matrix.max() * 0.6 else "black"
                ax.text(j, i, str(val), ha="center", va="center",
                        fontsize=8, color=text_color, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Paper Count", fontsize=10)
    ax.set_title("NTS Domains by Publication Year", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year", fontsize=12)
    plt.tight_layout()

    out = fig_dir / "nts_domain_year_heatmap.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def save_summary_table(domain_counts: Dict[str, int], domain_papers: Dict[str, List[Dict]],
                       total_papers: int, table_dir: Path) -> None:
    """Save a markdown summary table of NTS domain classification."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = table_dir / f"nts_domains_{ts}.md"

    lines = [
        "# NTS Domain Classification Summary",
        "",
        f"Total papers analysed: **{total_papers}**",
        "",
        "| Domain | Count | % of Corpus | Example Patterns |",
        "|--------|------:|------------:|------------------|",
    ]
    for domain in sorted(domain_counts, key=lambda d: domain_counts[d], reverse=True):
        count = domain_counts[domain]
        pct = count / total_papers * 100 if total_papers else 0
        pattern_strs = []
        for p in NTS_DOMAINS[domain][:3]:
            if hasattr(p, 'pattern') and hasattr(p.pattern, 'pattern'):
                # _ContextPattern
                pattern_strs.append(f"{p.pattern.pattern} (context)")
            else:
                pattern_strs.append(p.pattern)
        lines.append(f"| {domain} | {count} | {pct:.1f}% | {', '.join(pattern_strs)} |")

    # Count papers appearing in >1 domain
    paper_domain_count: Counter = Counter()
    for domain, papers in domain_papers.items():
        for p in papers:
            pid = p.get("id") or p.get("doi") or p.get("title")
            paper_domain_count[pid] += 1
    multi = sum(1 for c in paper_domain_count.values() if c > 1)
    unclassified = total_papers - len(paper_domain_count)

    lines += [
        "",
        f"Papers classified into at least one domain: **{len(paper_domain_count)}** "
        f"({len(paper_domain_count) / total_papers * 100:.1f}%)",
        f"Papers in multiple domains: **{multi}** "
        f"({multi / total_papers * 100:.1f}%)",
        f"Unclassified papers: **{unclassified}** "
        f"({unclassified / total_papers * 100:.1f}%)",
        "",
    ]

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

    domain_papers, domain_counts = classify_papers(papers)

    logger.info("NTS domain counts:")
    for domain in sorted(domain_counts, key=lambda d: domain_counts[d], reverse=True):
        logger.info("  %-25s %d", domain, domain_counts[domain])

    plot_domain_frequencies(domain_counts, fig_dir)
    plot_domain_year_heatmap(domain_papers, fig_dir)
    save_summary_table(domain_counts, domain_papers, len(papers), table_dir)

    logger.info("NTS analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <analysis_dataset.json>")
        sys.exit(1)
    main(sys.argv[1])
