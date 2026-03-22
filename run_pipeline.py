#!/usr/bin/env python3
"""
Master Pipeline Orchestrator for Bibliometric Analysis v2
=========================================================
Runs the full pipeline: collect → normalize → deduplicate → screen → analyze

Usage:
    python run_pipeline.py --all              # Run everything
    python run_pipeline.py --collect          # Collection only
    python run_pipeline.py --process          # Processing only (normalize + dedup + screen)
    python run_pipeline.py --analyze          # Analysis only
    python run_pipeline.py --loop             # Continuous loop mode
    python run_pipeline.py --collect --process  # Collection + processing
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "01_collection"))
sys.path.insert(0, str(BASE_DIR / "02_processing"))
sys.path.insert(0, str(BASE_DIR / "03_analysis"))

logger = logging.getLogger(__name__)


def run_collection():
    """Phase 1: Collect data from all sources."""
    logger.info("=" * 60)
    logger.info("PHASE 1: DATA COLLECTION")
    logger.info("=" * 60)

    from collection_manager import run_collection_cycle
    summary = run_collection_cycle()
    return summary


def run_processing():
    """Phase 2: Normalize, deduplicate, and screen."""
    logger.info("=" * 60)
    logger.info("PHASE 2: DATA PROCESSING")
    logger.info("=" * 60)

    # Step 1: Normalize
    logger.info("Step 2.1: Normalizing records...")
    from normalizer import RecordNormalizer
    normalizer = RecordNormalizer()
    records = normalizer.normalize_all()
    if not records:
        logger.error("No records to process!")
        return {"error": "No records found"}
    norm_path = normalizer.save(records)
    logger.info(f"Normalized {len(records)} records")

    # Step 2: Deduplicate
    logger.info("Step 2.2: Deduplicating records...")
    from deduplicator import Deduplicator
    dedup = Deduplicator()
    unique = dedup.deduplicate(records)
    dedup_path = dedup.save(unique)
    logger.info(f"Deduplicated: {len(records)} → {len(unique)}")

    # Step 3: Screen
    logger.info("Step 2.3: Screening papers...")
    from screener import PaperScreener
    screener = PaperScreener()
    results = screener.screen_all(unique)
    screener.save(results)

    included = results["included"]
    logger.info(f"Screening: {len(unique)} → {len(included)} included")

    # Save analysis-ready dataset
    analysis_dir = BASE_DIR / "03_analysis"
    dataset_path = analysis_dir / "analysis_dataset.json"
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(included, f, indent=2, ensure_ascii=False)
    logger.info(f"Analysis dataset saved: {dataset_path} ({len(included)} papers)")

    return {
        "normalized": len(records),
        "deduplicated": len(unique),
        "included": len(included),
        "excluded": len(results["excluded"]),
    }


def run_analysis():
    """Phase 3: Run all analyses."""
    logger.info("=" * 60)
    logger.info("PHASE 3: ANALYSIS")
    logger.info("=" * 60)

    dataset_path = BASE_DIR / "03_analysis" / "analysis_dataset.json"
    if not dataset_path.exists():
        logger.error(f"Analysis dataset not found: {dataset_path}")
        logger.error("Run --process first to create the dataset.")
        return {"error": "No analysis dataset"}

    with open(dataset_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    logger.info(f"Loaded {len(papers)} papers for analysis")

    results = {}

    # Publication trends
    try:
        logger.info("Running publication trends analysis...")
        from publication_trends import analyze_publication_trends
        results["publication_trends"] = analyze_publication_trends(papers)
    except Exception as e:
        logger.error(f"Publication trends failed: {e}")

    # Thematic mapping
    try:
        logger.info("Running thematic mapping...")
        from thematic_mapping import ThematicMapper
        mapper = ThematicMapper()
        results["thematic_mapping"] = mapper.run(papers)
    except Exception as e:
        logger.error(f"Thematic mapping failed: {e}")

    # Save combined results
    results_path = BASE_DIR / "03_analysis" / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Analysis results saved to {results_path}")

    return results


def run_full_pipeline():
    """Run the complete pipeline."""
    start = time.time()
    logger.info("#" * 60)
    logger.info("FULL BIBLIOMETRIC PIPELINE - START")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("#" * 60)

    collection = run_collection()
    processing = run_processing()
    analysis = run_analysis()

    elapsed = time.time() - start
    logger.info("#" * 60)
    logger.info(f"FULL PIPELINE COMPLETE in {elapsed/60:.1f} minutes")
    logger.info("#" * 60)

    return {"collection": collection, "processing": processing, "analysis": analysis}


def run_loop(interval_hours=24, max_days=7):
    """Run pipeline in loop mode."""
    logger.info(f"Starting loop mode: interval={interval_hours}h, max_days={max_days}")
    start = time.time()
    max_seconds = max_days * 24 * 3600
    cycle = 0

    while (time.time() - start) < max_seconds:
        cycle += 1
        logger.info(f"\n{'#' * 60}\nLOOP CYCLE {cycle}\n{'#' * 60}")

        try:
            run_full_pipeline()
        except KeyboardInterrupt:
            logger.info("Loop interrupted.")
            break
        except Exception as e:
            logger.error(f"Cycle {cycle} failed: {e}")

        remaining = max_seconds - (time.time() - start)
        if remaining <= 0:
            break
        sleep_time = min(interval_hours * 3600, remaining)
        logger.info(f"Sleeping {sleep_time/3600:.1f}h before next cycle...")
        time.sleep(sleep_time)

    logger.info(f"Loop complete after {cycle} cycles.")


def main():
    parser = argparse.ArgumentParser(description="Bibliometric Analysis v2 Pipeline")
    parser.add_argument("--collect", action="store_true", help="Run data collection")
    parser.add_argument("--process", action="store_true", help="Run data processing")
    parser.add_argument("--analyze", action="store_true", help="Run analysis")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--loop", action="store_true", help="Run in loop mode")
    parser.add_argument("--interval", type=float, default=24, help="Loop interval (hours)")
    parser.add_argument("--max-days", type=int, default=7, help="Max loop duration (days)")
    args = parser.parse_args()

    # Setup logging
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(),
        ],
    )

    if args.loop:
        run_loop(args.interval, args.max_days)
    elif args.all:
        run_full_pipeline()
    else:
        if args.collect:
            run_collection()
        if args.process:
            run_processing()
        if args.analyze:
            run_analysis()
        if not (args.collect or args.process or args.analyze):
            parser.print_help()


if __name__ == "__main__":
    main()
