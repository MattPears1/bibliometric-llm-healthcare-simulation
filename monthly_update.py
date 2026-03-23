#!/usr/bin/env python3
"""
Monthly Bibliometric Update Script
====================================
Runs the full pipeline, regenerates all analyses and figures,
auto-populates the manuscript template with fresh numbers,
builds the figure compendium, and commits to git.

Usage:
    python monthly_update.py                # Full update
    python monthly_update.py --dry-run      # Show what would change without modifying
    python monthly_update.py --push         # Update and push to GitHub
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "01_collection"))
sys.path.insert(0, str(BASE_DIR / "02_processing"))
sys.path.insert(0, str(BASE_DIR / "03_analysis"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / f"monthly_update_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def step(name):
    logger.info(f"\n{'='*60}\n  {name}\n{'='*60}")


def run_collection():
    step("PHASE 1: DATA COLLECTION")
    from collection_manager import run_collection_cycle
    return run_collection_cycle()


def run_processing():
    step("PHASE 2: PROCESSING (normalize + dedup + screen)")
    from normalizer import RecordNormalizer
    normalizer = RecordNormalizer()
    records = normalizer.normalize_all()
    normalizer.save(records, prefix="normalized_monthly")

    from deduplicator import Deduplicator
    dedup = Deduplicator()
    unique = dedup.deduplicate(records)
    dedup.save(unique, prefix="deduplicated_monthly")

    from screener import PaperScreener
    screener = PaperScreener()
    screener.ai_enabled = False
    results = screener.screen_all(unique)
    screener.save(results, prefix="screened_monthly")

    # Build core dataset: high/medium confidence, Tier 2/3, with medical+LLM+sim terms
    included = results["included"]
    medical = ['healthcare','health care','medical','clinical','surgical','surgery',
        'nursing','hospital','patient','physician','doctor','medicine','nurse',
        'emergency','anesthesia','anaesthesia','residency','trainee']
    llm = ['large language model','llm','chatgpt','gpt','claude','gemini',
        'generative ai','artificial intelligence','natural language processing']
    sim = ['simulation','simulator','simulated','virtual patient','standardized patient',
        'standardised patient','scenario','debriefing','mannequin','virtual reality',
        'roleplay','role-play','osce','sim-based','simulation-based','immersive']
    edu = ['education','training','teaching','learning','curriculum','student',
        'resident','trainee','faculty','competency','assessment']

    core = []
    for p in included:
        if p.get("screening_confidence") not in ["high", "medium"]:
            continue
        if p.get("screening_tier", "") not in ["tier2", "tier3"]:
            continue
        text = f"{p.get('title','')} {p.get('abstract','')}".lower()
        if not any(t in text for t in medical):
            continue
        if not any(t in text for t in llm):
            continue
        title = (p.get("title", "") or "").strip()
        if len(title) < 15 or not p.get("year"):
            continue
        core.append(p)

    core_path = BASE_DIR / "03_analysis" / "core_dataset.json"
    with open(core_path, "w", encoding="utf-8") as f:
        json.dump(core, f, indent=2, ensure_ascii=False)

    logger.info(f"Core dataset: {len(core)} papers")
    return {"raw": len(records), "unique": len(unique), "included": len(included), "core": len(core)}


def run_analyses():
    step("PHASE 3: ALL ANALYSES")
    with open(BASE_DIR / "03_analysis" / "core_dataset.json", encoding="utf-8") as f:
        papers = json.load(f)

    results = {}

    from publication_trends import analyze_publication_trends
    results["trends"] = analyze_publication_trends(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Publication trends: done")

    from citation_analysis import analyze_citations
    results["citations"] = analyze_citations(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Citations: done")

    from author_analysis import analyze_authors
    results["authors"] = analyze_authors(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Authors: done")

    from journal_analysis import analyze_journals
    results["journals"] = analyze_journals(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Journals: done")

    try:
        from geographic_analysis import analyze_geography
        results["geography"] = analyze_geography(papers)
        logger.info("  Geography: done")
    except Exception as e:
        logger.error(f"  Geography: {e}")

    try:
        from nts_analysis import analyze_nts
        results["nts"] = analyze_nts(papers)
        logger.info("  NTS: done")
    except Exception as e:
        logger.error(f"  NTS: {e}")

    try:
        from keyword_cooccurrence import analyze_keywords
        results["keywords"] = analyze_keywords(papers)
        logger.info("  Keywords: done")
    except Exception as e:
        logger.error(f"  Keywords: {e}")

    from thematic_mapping import ThematicMapper
    mapper = ThematicMapper(min_keyword_freq=5, min_cooccurrence=3)
    results["thematic"] = mapper.run(papers)
    logger.info("  Thematic: done")

    from urology_subanalysis import analyze_urology
    results["urology"] = analyze_urology(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Urology: done")

    from research_methods_analysis import analyze_research_methods
    results["methods"] = analyze_research_methods(papers, str(BASE_DIR / "03_analysis"))
    logger.info("  Research methods: done")

    # Run remaining scripts via CLI (different function signatures)
    for script in ["descriptive_stats.py", "llm_model_analysis.py", "simulation_type_analysis.py"]:
        try:
            subprocess.run(
                [sys.executable, str(BASE_DIR / "03_analysis" / script), str(BASE_DIR / "03_analysis" / "core_dataset.json")],
                capture_output=True, timeout=120
            )
            logger.info(f"  {script}: done")
        except Exception as e:
            logger.error(f"  {script}: {e}")

    # Save combined results
    with open(BASE_DIR / "03_analysis" / "MONTHLY_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def populate_manuscript(results):
    step("PHASE 4: POPULATE MANUSCRIPT")
    date_str = datetime.now().strftime("%Y%m%d")
    t = results.get("trends", {})
    c = results.get("citations", {})
    a = results.get("authors", {})
    j = results.get("journals", {})
    u = results.get("urology", {})

    with open(BASE_DIR / "03_analysis" / "core_dataset.json", encoding="utf-8") as f:
        n_papers = len(json.load(f))

    # Read template and populate
    template_path = BASE_DIR / "04_manuscript" / "template.md"
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Key replacements
    replacements = {
        "{{n_papers}}": str(f"{n_papers:,}"),
        "{{cagr}}": str(t.get("cagr_percent", "N/A")),
        "{{h_index}}": str(c.get("h_index", "N/A")),
        "{{peak_year}}": str(t.get("peak_year", "N/A")),
        "{{peak_count}}": str(f"{t.get('peak_count', 0):,}"),
        "{{total_citations}}": str(f"{c.get('total_citations', 0):,}"),
        "{{mean_citations}}": str(c.get("mean_citations", "N/A")),
        "{{n_authors}}": str(f"{a.get('unique_authors', 0):,}"),
        "{{n_journals}}": str(f"{j.get('unique_journals', 0):,}"),
        "{{urology_papers}}": str(u.get("urology_papers", "N/A")),
        "{{date}}": datetime.now().strftime("%Y-%m-%d"),
        "{{github_url}}": "https://github.com/MattPears1/bibliometric-llm-healthcare-simulation",
    }

    populated = template
    for key, val in replacements.items():
        populated = populated.replace(key, val)

    out_path = BASE_DIR / "04_manuscript" / "output" / f"MANUSCRIPT_{date_str}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(populated)
    logger.info(f"Manuscript saved: {out_path}")

    # Also run the assembler for the full version
    subprocess.run(
        [sys.executable, str(BASE_DIR / "04_manuscript" / "assemble_manuscript.py")],
        capture_output=True, timeout=60
    )

    # Build figure compendium
    subprocess.run(
        [sys.executable, str(BASE_DIR / "build_figure_compendium.py")],
        capture_output=True, timeout=120
    )
    logger.info("Figure compendium generated")


def git_commit_and_push(push=False):
    step("PHASE 5: GIT COMMIT")
    date_str = datetime.now().strftime("%Y-%m-%d")
    subprocess.run(["git", "add", "-A"], cwd=str(BASE_DIR))
    subprocess.run(
        ["git", "commit", "-m", f"Monthly update: {date_str}\n\nAutomated re-run of full bibliometric pipeline.\nAll data, analyses, figures, and manuscript refreshed."],
        cwd=str(BASE_DIR)
    )
    if push:
        subprocess.run(["git", "push"], cwd=str(BASE_DIR))
        logger.info("Pushed to GitHub")
    logger.info("Git commit complete")


def main():
    parser = argparse.ArgumentParser(description="Monthly Bibliometric Update")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--push", action="store_true", help="Push to GitHub after update")
    parser.add_argument("--skip-collection", action="store_true", help="Skip data collection (use existing data)")
    args = parser.parse_args()

    start = time.time()
    logger.info(f"Monthly update started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if args.dry_run:
        logger.info("DRY RUN - no changes will be made")
        return

    if not args.skip_collection:
        run_collection()

    proc = run_processing()
    results = run_analyses()
    populate_manuscript(results)
    git_commit_and_push(push=args.push)

    elapsed = (time.time() - start) / 60
    logger.info(f"\nMonthly update complete in {elapsed:.1f} minutes")
    logger.info(f"Core dataset: {proc.get('core', 'N/A')} papers")


if __name__ == "__main__":
    main()
