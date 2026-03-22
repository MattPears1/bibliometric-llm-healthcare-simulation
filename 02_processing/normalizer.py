#!/usr/bin/env python3
"""
Record Normalizer - standardizes records from all sources into a unified schema.
Reads raw JSONL files from 01_collection/raw/ and outputs merged normalized records.
"""

import json
import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RecordNormalizer:
    """Normalize and merge records from all collection sources."""

    def __init__(self, raw_dir: str = None, output_dir: str = None):
        base = Path(__file__).parent
        self.raw_dir = Path(raw_dir) if raw_dir else base.parent / "01_collection" / "raw"
        self.output_dir = Path(output_dir) if output_dir else base / "merged"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI: lowercase, strip prefixes and whitespace."""
        if not doi:
            return ""
        doi = doi.strip().lower()
        # Remove common prefixes
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "doi.org/"]:
            if doi.startswith(prefix):
                doi = doi[len(prefix):]
        return doi.strip()

    def _normalize_title(self, title: str) -> str:
        """Normalize title for matching: lowercase, strip special chars, collapse spaces."""
        if not title:
            return ""
        title = title.strip().lower()
        # Remove HTML/XML tags
        title = re.sub(r"<[^>]+>", "", title)
        # Remove special characters but keep spaces
        title = re.sub(r"[^\w\s]", " ", title)
        # Collapse whitespace
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _normalize_author_name(self, name: str) -> str:
        """Normalize author name."""
        if not name:
            return ""
        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name.strip())
        return name

    def _generate_record_id(self, record: Dict) -> str:
        """Generate a deterministic unique ID for a record."""
        doi = self._normalize_doi(record.get("doi", ""))
        if doi:
            return hashlib.sha256(f"doi:{doi}".encode()).hexdigest()[:16]
        title = self._normalize_title(record.get("title", ""))
        year = record.get("year", "")
        key = f"title:{title}:year:{year}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def normalize_record(self, record: Dict) -> Dict:
        """Apply normalization to a single record."""
        normalized = {
            "id": self._generate_record_id(record),
            "doi": self._normalize_doi(record.get("doi", "")),
            "title": (record.get("title", "") or "").strip(),
            "title_normalized": self._normalize_title(record.get("title", "")),
            "abstract": (record.get("abstract", "") or "").strip(),
            "authors": [],
            "year": record.get("year"),
            "journal": (record.get("journal", "") or "").strip(),
            "source_db": record.get("source_db", ""),
            "query_strategy": record.get("query_strategy", ""),
            "citation_count": record.get("citation_count", 0) or 0,
            "keywords": record.get("keywords", []) or [],
            "type": record.get("type", ""),
            "open_access": record.get("open_access", False),
            "url": record.get("url", ""),
            "raw_id": record.get("raw_id", ""),
        }

        # Normalize authors
        for author in record.get("authors", []):
            if isinstance(author, dict):
                normalized["authors"].append({
                    "name": self._normalize_author_name(author.get("name", "")),
                    "affiliation": (author.get("affiliation", "") or "").strip(),
                })
            elif isinstance(author, str):
                normalized["authors"].append({
                    "name": self._normalize_author_name(author),
                    "affiliation": "",
                })

        # Validate year
        if normalized["year"] is not None:
            try:
                normalized["year"] = int(normalized["year"])
                if normalized["year"] < 1900 or normalized["year"] > 2030:
                    normalized["year"] = None
            except (ValueError, TypeError):
                normalized["year"] = None

        return normalized

    def load_all_raw_records(self) -> List[Dict]:
        """Load all records from raw JSONL files."""
        records = []
        for jsonl_path in sorted(self.raw_dir.glob("*.jsonl")):
            source_count = 0
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                        source_count += 1
                    except json.JSONDecodeError:
                        continue
            logger.info(f"Loaded {source_count} records from {jsonl_path.name}")

        logger.info(f"Total raw records loaded: {len(records)}")
        return records

    def normalize_all(self) -> List[Dict]:
        """Load and normalize all raw records."""
        raw_records = self.load_all_raw_records()
        normalized = [self.normalize_record(r) for r in raw_records]
        logger.info(f"Normalized {len(normalized)} records")
        return normalized

    def save(self, records: List[Dict], prefix: str = "normalized") -> Path:
        """Save normalized records to JSON and CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON output
        json_path = self.output_dir / f"{prefix}_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(records)} records to {json_path}")

        # CSV output (flattened)
        csv_path = self.output_dir / f"{prefix}_{timestamp}.csv"
        import csv
        if records:
            fieldnames = ["id", "doi", "title", "year", "journal", "source_db",
                         "query_strategy", "citation_count", "type", "open_access",
                         "url", "abstract"]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
            logger.info(f"Saved CSV to {csv_path}")

        # Summary report
        report_path = self.output_dir / f"{prefix}_report_{timestamp}.md"
        self._write_report(records, report_path)

        return json_path

    def _write_report(self, records: List[Dict], path: Path):
        """Write a normalization summary report."""
        from collections import Counter

        source_counts = Counter(r["source_db"] for r in records)
        year_counts = Counter(r["year"] for r in records if r["year"])
        has_doi = sum(1 for r in records if r["doi"])
        has_abstract = sum(1 for r in records if r["abstract"] and len(r["abstract"]) > 50)

        with open(path, "w") as f:
            f.write("# Normalization Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Total records: {len(records)}\n")
            f.write(f"- Records with DOI: {has_doi} ({has_doi/len(records)*100:.1f}%)\n")
            f.write(f"- Records with abstract (>50 chars): {has_abstract} ({has_abstract/len(records)*100:.1f}%)\n\n")
            f.write(f"## Records by Source\n\n")
            f.write("| Source | Count | % |\n|--------|-------|---|\n")
            for source, count in source_counts.most_common():
                f.write(f"| {source} | {count} | {count/len(records)*100:.1f}% |\n")
            f.write(f"\n## Records by Year\n\n")
            f.write("| Year | Count | % |\n|------|-------|---|\n")
            for year in sorted(year_counts.keys()):
                count = year_counts[year]
                f.write(f"| {year} | {count} | {count/len(records)*100:.1f}% |\n")

        logger.info(f"Report saved to {path}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    normalizer = RecordNormalizer()
    records = normalizer.normalize_all()
    if records:
        normalizer.save(records)
    else:
        print("No records found to normalize.")


if __name__ == "__main__":
    main()
