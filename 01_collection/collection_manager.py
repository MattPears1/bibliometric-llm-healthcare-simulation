#!/usr/bin/env python3
"""
Collection Manager - orchestrates all data source collectors.
Runs them sequentially, handles failures gracefully, supports loop mode.
"""

import json
import logging
import time
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from openalex_collector import OpenAlexCollector
from pubmed_collector import PubMedCollector
from europepmc_collector import EuropePMCCollector
from crossref_collector import CrossrefCollector
from semantic_scholar_collector import SemanticScholarCollector
from core_collector import CORECollector
from doaj_collector import DOAJCollector

logger = logging.getLogger(__name__)

# Ordered list of collectors (run sequentially)
COLLECTORS = [
    ("OpenAlex", OpenAlexCollector),
    ("PubMed", PubMedCollector),
    ("Europe PMC", EuropePMCCollector),
    ("Crossref", CrossrefCollector),
    ("Semantic Scholar", SemanticScholarCollector),
    ("CORE", CORECollector),
    ("DOAJ", DOAJCollector),
]


def run_collection_cycle(config_path: str = None) -> dict:
    """Run one complete collection cycle across all sources."""
    cycle_start = datetime.now()
    results = {}

    for name, collector_class in COLLECTORS:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting: {name}")
        logger.info(f"{'='*60}")

        try:
            kwargs = {}
            if config_path:
                kwargs["config_path"] = config_path

            collector = collector_class(**kwargs)
            stats = collector.collect()
            results[name] = stats
            logger.info(f"{name}: {stats.get('total_new_records', 0)} new records")

        except KeyboardInterrupt:
            logger.warning(f"Interrupted during {name}. Checkpoints saved.")
            raise

        except Exception as e:
            logger.error(f"{name} failed: {e}")
            results[name] = {"error": str(e)}
            continue

    cycle_end = datetime.now()
    duration = (cycle_end - cycle_start).total_seconds()

    # Summary
    total_new = sum(
        r.get("total_new_records", 0)
        for r in results.values()
        if isinstance(r, dict) and "error" not in r
    )
    total_errors = sum(
        r.get("errors", 0)
        for r in results.values()
        if isinstance(r, dict) and "error" not in r
    )
    failed_sources = [k for k, v in results.items() if isinstance(v, dict) and "error" in v]

    summary = {
        "cycle_start": cycle_start.isoformat(),
        "cycle_end": cycle_end.isoformat(),
        "duration_seconds": duration,
        "total_new_records": total_new,
        "total_errors": total_errors,
        "failed_sources": failed_sources,
        "per_source": results,
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"COLLECTION CYCLE COMPLETE")
    logger.info(f"Duration: {duration:.0f}s ({duration/60:.1f} min)")
    logger.info(f"New records: {total_new}")
    logger.info(f"Errors: {total_errors}")
    if failed_sources:
        logger.warning(f"Failed sources: {', '.join(failed_sources)}")
    logger.info(f"{'='*60}")

    # Save cycle summary
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    summary_path = log_dir / f"cycle_summary_{cycle_start.strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    return summary


def run_loop(config_path: str = None, interval_hours: float = 24, max_days: int = 7):
    """Run collection in loop mode - repeats every interval_hours for max_days."""
    start_time = time.time()
    max_seconds = max_days * 24 * 3600
    cycle_count = 0

    logger.info(f"Starting loop mode: interval={interval_hours}h, max_days={max_days}")

    while (time.time() - start_time) < max_seconds:
        cycle_count += 1
        logger.info(f"\n{'#'*60}")
        logger.info(f"LOOP CYCLE {cycle_count}")
        logger.info(f"{'#'*60}")

        try:
            summary = run_collection_cycle(config_path)
        except KeyboardInterrupt:
            logger.info("Loop interrupted by user.")
            break

        elapsed = time.time() - start_time
        remaining = max_seconds - elapsed

        if remaining <= 0:
            logger.info("Max duration reached. Stopping loop.")
            break

        sleep_seconds = min(interval_hours * 3600, remaining)
        logger.info(
            f"Cycle {cycle_count} done. "
            f"Sleeping {sleep_seconds/3600:.1f}h before next cycle. "
            f"Total elapsed: {elapsed/3600:.1f}h / {max_days*24}h"
        )
        time.sleep(sleep_seconds)

    logger.info(f"Loop complete after {cycle_count} cycles.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bibliometric Data Collection Manager")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--loop", action="store_true", help="Run in loop mode")
    parser.add_argument("--interval", type=float, default=24, help="Hours between cycles (loop mode)")
    parser.add_argument("--max-days", type=int, default=7, help="Max days to run (loop mode)")
    parser.add_argument("--source", type=str, help="Run only a specific source (e.g., 'openalex')")
    args = parser.parse_args()

    # Setup logging
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "collection.log"),
            logging.StreamHandler(),
        ],
    )

    if args.source:
        # Run single source
        source_map = {name.lower().replace(" ", "_"): cls for name, cls in COLLECTORS}
        alt_map = {
            "openalex": "openalex",
            "pubmed": "pubmed",
            "europepmc": "europe_pmc",
            "europe_pmc": "europe_pmc",
            "crossref": "crossref",
            "semantic_scholar": "semantic_scholar",
            "core": "core",
            "doaj": "doaj",
        }
        key = alt_map.get(args.source.lower(), args.source.lower())
        if key not in source_map:
            print(f"Unknown source: {args.source}. Available: {list(source_map.keys())}")
            return
        collector = source_map[key]()
        collector.collect()
    elif args.loop:
        run_loop(args.config, args.interval, args.max_days)
    else:
        run_collection_cycle(args.config)


if __name__ == "__main__":
    main()
