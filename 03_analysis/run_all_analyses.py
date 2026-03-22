#!/usr/bin/env python3
"""
Master analysis runner - executes all analysis scripts and generates combined report.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


def run_all(dataset_path: str = None):
    """Run all analyses and generate combined report."""
    if dataset_path is None:
        dataset_path = str(BASE_DIR / "analysis_dataset.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    logger.info(f"Running all analyses on {len(papers)} papers")
    results = {}

    # 1. Descriptive stats
    try:
        from descriptive_stats import analyze_descriptive_stats
        results["descriptive"] = analyze_descriptive_stats(papers, str(BASE_DIR))
        logger.info("Descriptive stats: DONE")
    except Exception as e:
        logger.error(f"Descriptive stats failed: {e}")

    # 2. Publication trends
    try:
        from publication_trends import analyze_publication_trends
        results["trends"] = analyze_publication_trends(papers, str(BASE_DIR))
        logger.info("Publication trends: DONE")
    except Exception as e:
        logger.error(f"Publication trends failed: {e}")

    # 3. Citation analysis
    try:
        from citation_analysis import analyze_citations
        results["citations"] = analyze_citations(papers, str(BASE_DIR))
        logger.info("Citation analysis: DONE")
    except Exception as e:
        logger.error(f"Citation analysis failed: {e}")

    # 4. Author analysis
    try:
        from author_analysis import analyze_authors
        results["authors"] = analyze_authors(papers, str(BASE_DIR))
        logger.info("Author analysis: DONE")
    except Exception as e:
        logger.error(f"Author analysis failed: {e}")

    # 5. Journal analysis
    try:
        from journal_analysis import analyze_journals
        results["journals"] = analyze_journals(papers, str(BASE_DIR))
        logger.info("Journal analysis: DONE")
    except Exception as e:
        logger.error(f"Journal analysis failed: {e}")

    # 6. Geographic analysis
    try:
        from geographic_analysis import analyze_geography
        results["geography"] = analyze_geography(papers, str(BASE_DIR))
        logger.info("Geographic analysis: DONE")
    except Exception as e:
        logger.error(f"Geographic analysis failed: {e}")

    # 7. NTS analysis
    try:
        from nts_analysis import analyze_nts
        results["nts"] = analyze_nts(papers, str(BASE_DIR))
        logger.info("NTS analysis: DONE")
    except Exception as e:
        logger.error(f"NTS analysis failed: {e}")

    # 8. Keyword co-occurrence
    try:
        from keyword_cooccurrence import analyze_keywords
        results["keywords"] = analyze_keywords(papers, str(BASE_DIR))
        logger.info("Keyword co-occurrence: DONE")
    except Exception as e:
        logger.error(f"Keyword co-occurrence failed: {e}")

    # 9. Thematic mapping
    try:
        from thematic_mapping import ThematicMapper
        mapper = ThematicMapper(min_keyword_freq=8, min_cooccurrence=4)
        results["thematic"] = mapper.run(papers)
        logger.info("Thematic mapping: DONE")
    except Exception as e:
        logger.error(f"Thematic mapping failed: {e}")

    # 10. Urology sub-analysis
    try:
        from urology_subanalysis import analyze_urology
        results["urology"] = analyze_urology(papers, str(BASE_DIR))
        logger.info("Urology sub-analysis: DONE")
    except Exception as e:
        logger.error(f"Urology sub-analysis failed: {e}")

    # 11. LLM model analysis (if exists)
    try:
        from llm_model_analysis import analyze_llm_models
        results["llm_models"] = analyze_llm_models(papers, str(BASE_DIR))
        logger.info("LLM model analysis: DONE")
    except Exception as e:
        logger.error(f"LLM model analysis failed: {e}")

    # 12. Simulation type analysis (if exists)
    try:
        from simulation_type_analysis import analyze_simulation_types
        results["simulation_types"] = analyze_simulation_types(papers, str(BASE_DIR))
        logger.info("Simulation type analysis: DONE")
    except Exception as e:
        logger.error(f"Simulation type analysis failed: {e}")

    # Generate combined report
    _generate_report(results, papers)

    # Save all results
    results_path = BASE_DIR / f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"All analyses complete. Results saved to {results_path}")
    return results


def _generate_report(results: dict, papers: list):
    """Generate FULL_ANALYSIS_REPORT.md."""
    report_path = BASE_DIR / "FULL_ANALYSIS_REPORT.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(report_path, "w") as f:
        f.write(f"# Full Bibliometric Analysis Report\n\n")
        f.write(f"**Generated:** {timestamp}\n")
        f.write(f"**Dataset:** {len(papers)} papers\n\n")
        f.write("---\n\n")

        # Descriptive
        if "descriptive" in results:
            d = results["descriptive"]
            f.write("## 1. Descriptive Statistics\n\n")
            f.write(f"- Total papers: {d.get('total_papers', 'N/A')}\n")
            f.write(f"- Year range: {d.get('year_range', 'N/A')}\n")
            f.write(f"- Open access: {d.get('open_access_pct', 'N/A')}%\n\n")

        # Trends
        if "trends" in results:
            t = results["trends"]
            f.write("## 2. Publication Trends\n\n")
            f.write(f"- CAGR: {t.get('cagr_percent', 'N/A')}%\n")
            f.write(f"- Peak year: {t.get('peak_year', 'N/A')} ({t.get('peak_count', 'N/A')} papers)\n")
            f.write(f"- Pre-ChatGPT: {t.get('pre_chatgpt_count', 'N/A')}\n")
            f.write(f"- Post-ChatGPT: {t.get('post_chatgpt_count', 'N/A')}\n\n")

        # Citations
        if "citations" in results:
            c = results["citations"]
            f.write("## 3. Citation Analysis\n\n")
            f.write(f"- h-index: {c.get('h_index', 'N/A')}\n")
            f.write(f"- Mean citations: {c.get('mean_citations', 'N/A')}\n")
            f.write(f"- Uncited: {c.get('uncited_pct', 'N/A')}%\n\n")

        # NTS
        if "nts" in results:
            f.write("## 4. Non-Technical Skills\n\n")
            n = results["nts"]
            if isinstance(n, dict) and "domains" in n:
                for domain, count in sorted(n["domains"].items(), key=lambda x: -x[1]):
                    f.write(f"- {domain}: {count}\n")
            f.write("\n")

        # Urology
        if "urology" in results:
            u = results["urology"]
            f.write("## 5. Urology Sub-Analysis\n\n")
            f.write(f"- Urology papers: {u.get('urology_papers', 'N/A')} ({u.get('urology_percentage', 'N/A')}%)\n")
            f.write(f"- Boot camp papers: {u.get('bootcamp_papers', 'N/A')}\n")
            f.write(f"- Urology + boot camp: {u.get('urology_bootcamp_papers', 'N/A')}\n\n")

        # Figures list
        f.write("## Figures Generated\n\n")
        fig_dir = BASE_DIR / "figures"
        if fig_dir.exists():
            for fig in sorted(fig_dir.glob("*.png")):
                f.write(f"- `{fig.name}`\n")

    logger.info(f"Report saved to {report_path}")


if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else None
    run_all(dataset)
