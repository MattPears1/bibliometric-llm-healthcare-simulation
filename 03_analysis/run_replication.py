#!/usr/bin/env python3
"""
Master Replication Script -- 2026-03-25
========================================
Runs ALL bibliometric analyses on core_corpus_dataset.json (3,107 papers)
and saves outputs (figures + tables) to replication_20260325/.

Each analysis module is imported and called with the correct entry-point
function signature as determined by reading the source code.
"""

import io
import json
import logging
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path

# --- Fix stdout encoding for Windows -------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# --- Paths ------------------------------------------------------------------
BASE_DIR = Path(r"C:\Users\MattP\Desktop\Papers\03_Bibliometric_Analysis\Bibliometric_v2\03_analysis")
DATASET_PATH = BASE_DIR / "core_corpus_dataset.json"
OUTPUT_DIR = BASE_DIR / "replication_20260325"
FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

# Ensure output dirs exist
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# Add base dir to sys.path so we can import analysis modules
sys.path.insert(0, str(BASE_DIR))

# --- Logging -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / "replication_log.txt", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("replication")

# --- Load dataset ------------------------------------------------------------
logger.info("Loading dataset from %s", DATASET_PATH)
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    papers = json.load(f)
logger.info("Loaded %d papers", len(papers))

# --- Collect all results -----------------------------------------------------
all_results = {}
errors = []


def run_step(name, func):
    """Run an analysis step with error handling."""
    logger.info("=" * 70)
    logger.info("RUNNING: %s", name)
    logger.info("=" * 70)
    try:
        result = func()
        all_results[name] = result
        logger.info("COMPLETED: %s", name)
        return result
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("FAILED: %s -- %s\n%s", name, e, tb)
        errors.append((name, str(e)))
        all_results[name] = {"error": str(e)}
        return None


# =============================================================================
# 1. Publication Trends
# =============================================================================
def step_publication_trends():
    from publication_trends import analyze_publication_trends
    return analyze_publication_trends(papers, output_dir=str(OUTPUT_DIR))

run_step("publication_trends", step_publication_trends)

# =============================================================================
# 2. Citation Analysis
# =============================================================================
def step_citation_analysis():
    from citation_analysis import analyze_citations
    return analyze_citations(papers, output_dir=str(OUTPUT_DIR))

run_step("citation_analysis", step_citation_analysis)

# =============================================================================
# 3. Author Analysis
# =============================================================================
def step_author_analysis():
    from author_analysis import analyze_authors
    return analyze_authors(papers, output_dir=str(OUTPUT_DIR))

run_step("author_analysis", step_author_analysis)

# =============================================================================
# 4. Journal Analysis
# =============================================================================
def step_journal_analysis():
    from journal_analysis import analyze_journals
    return analyze_journals(papers, output_dir=str(OUTPUT_DIR))

run_step("journal_analysis", step_journal_analysis)

# =============================================================================
# 5. Geographic Analysis
# =============================================================================
def step_geographic_analysis():
    from geographic_analysis import (
        analyze_geography,
        plot_top_countries,
        plot_continent_distribution,
        save_geography_table,
    )
    geo = analyze_geography(papers)
    # Plot and save using the replication output dirs
    plot_top_countries(geo["country_counts"], FIG_DIR)
    plot_continent_distribution(geo["continent_counts"], FIG_DIR)
    save_geography_table(geo, TABLE_DIR)
    # Convert Counter to dict for JSON serialization
    return {
        "papers_with_country": geo["papers_with_country"],
        "international_collab": geo["international_collab"],
        "collab_pct": geo["collab_pct"],
        "total": geo["total"],
        "unique_countries": len(geo["country_counts"]),
        "top10_countries": geo["country_counts"].most_common(10),
        "continent_counts": dict(geo["continent_counts"]),
    }

run_step("geographic_analysis", step_geographic_analysis)

# =============================================================================
# 6. NTS Analysis
# =============================================================================
def step_nts_analysis():
    from nts_analysis import (
        classify_papers as nts_classify_papers,
        plot_domain_frequencies,
        plot_domain_year_heatmap,
        save_summary_table as nts_save_summary_table,
    )
    domain_papers, domain_counts = nts_classify_papers(papers)
    plot_domain_frequencies(domain_counts, FIG_DIR)
    plot_domain_year_heatmap(domain_papers, FIG_DIR)
    nts_save_summary_table(domain_counts, domain_papers, len(papers), TABLE_DIR)
    return {"domain_counts": domain_counts}

run_step("nts_analysis", step_nts_analysis)

# =============================================================================
# 7. LLM Model Analysis
# =============================================================================
def step_llm_model_analysis():
    from llm_model_analysis import (
        classify_papers as llm_classify_papers,
        plot_model_frequencies,
        plot_proprietary_vs_open,
        plot_trend_over_time,
        save_summary_table as llm_save_summary_table,
    )
    model_papers, model_counts = llm_classify_papers(papers)
    plot_model_frequencies(model_counts, FIG_DIR)
    plot_proprietary_vs_open(model_papers, len(papers), FIG_DIR)
    plot_trend_over_time(model_papers, FIG_DIR)
    llm_save_summary_table(model_counts, model_papers, len(papers), TABLE_DIR)
    return {"model_counts": model_counts}

run_step("llm_model_analysis", step_llm_model_analysis)

# =============================================================================
# 8. Simulation Type Analysis
# =============================================================================
def step_simulation_type_analysis():
    from simulation_type_analysis import (
        classify_sim_types,
        classify_nts,
        plot_sim_type_frequencies,
        plot_sim_nts_crosstab,
        save_summary_table as sim_save_summary_table,
    )
    type_papers, type_counts = classify_sim_types(papers)
    nts_domain_ids = classify_nts(papers)
    plot_sim_type_frequencies(type_counts, FIG_DIR)
    plot_sim_nts_crosstab(type_papers, nts_domain_ids, FIG_DIR)
    sim_save_summary_table(type_counts, type_papers, nts_domain_ids, len(papers), TABLE_DIR)
    return {"type_counts": type_counts}

run_step("simulation_type_analysis", step_simulation_type_analysis)

# =============================================================================
# 9. Keyword Co-occurrence
# =============================================================================
def step_keyword_cooccurrence():
    from keyword_cooccurrence import (
        build_cooccurrence,
        plot_top_keywords,
        plot_network,
        plot_wordcloud,
        save_keyword_table,
    )
    keyword_freq, cooccurrence = build_cooccurrence(papers)
    plot_top_keywords(keyword_freq, FIG_DIR)
    plot_network(keyword_freq, cooccurrence, FIG_DIR)
    plot_wordcloud(keyword_freq, FIG_DIR)
    save_keyword_table(keyword_freq, cooccurrence, len(papers), TABLE_DIR)
    return {
        "unique_keywords": len(keyword_freq),
        "top10_keywords": keyword_freq.most_common(10),
    }

run_step("keyword_cooccurrence", step_keyword_cooccurrence)

# =============================================================================
# 10. Thematic Mapping
# =============================================================================
def step_thematic_mapping():
    from thematic_mapping import ThematicMapper
    mapper = ThematicMapper()
    # Override output dirs to point to replication folder
    mapper.output_dir = FIG_DIR
    mapper.tables_dir = TABLE_DIR
    result = mapper.run(papers)
    return {
        "n_clusters": len(result.get("clusters", [])),
        "figure_path": result.get("figure_path", ""),
    }

run_step("thematic_mapping", step_thematic_mapping)

# =============================================================================
# 11. Urology Sub-analysis
# =============================================================================
def step_urology_subanalysis():
    from urology_subanalysis import analyze_urology
    return analyze_urology(papers, output_dir=str(OUTPUT_DIR))

run_step("urology_subanalysis", step_urology_subanalysis)

# =============================================================================
# 12. Research Methods Analysis
# =============================================================================
def step_research_methods():
    from research_methods_analysis import analyze_research_methods
    return analyze_research_methods(papers, output_dir=str(OUTPUT_DIR))

run_step("research_methods", step_research_methods)

# =============================================================================
# Save aggregate results JSON
# =============================================================================
results_path = OUTPUT_DIR / "all_results.json"
with open(results_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, default=str)
logger.info("All results saved to %s", results_path)

# =============================================================================
# Summary
# =============================================================================
logger.info("")
logger.info("=" * 70)
logger.info("REPLICATION COMPLETE")
logger.info("=" * 70)
logger.info("Papers: %d", len(papers))
logger.info("Steps run: %d", len(all_results))
logger.info("Errors: %d", len(errors))
for name, err in errors:
    logger.info("  FAILED: %s -- %s", name, err)
logger.info("Output directory: %s", OUTPUT_DIR)
logger.info("Figures: %s", FIG_DIR)
logger.info("Tables: %s", TABLE_DIR)
