#!/usr/bin/env python3
"""Verify the n=483 publication without network access or third-party packages."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

RESOURCE_NAMES = {
    1: "online_resource_1_search_strategy",
    2: "online_resource_2_selection_and_versions",
    3: "online_resource_3_complete_results",
    4: "online_resource_4_phrases",
    5: "online_resource_5_reduced_dataset",
    6: "online_resource_6_validation",
}
EXPECTED_COUNTS = dict(completed_discovery_sources=6, retrieval_occurrences=9719,
    candidate_records=3919, eligible_publication_records=547,
    alternate_publication_versions=64, unique_studies=483)

def portable_root(root):
    root = Path(root).resolve()
    if os.name == "nt" and not str(root).startswith(chr(92)*2+"?"+chr(92)):
        return Path(chr(92)*2+"?"+chr(92)+str(root))
    return root

def read_rows(path):
    csv.field_size_limit(20_000_000)
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Missing or duplicate CSV headers: "+str(path.name))
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError("Malformed CSV row: "+str(path.name))
        return rows

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def check_science(root):
    root = portable_root(root)
    resources = {n:root/"online_resources"/name for n,name in RESOURCE_NAMES.items()}
    def read(n, name):return read_rows(resources[n]/name)
    studies = read(5, "CHECKED_STUDY_DATASET_N483.csv")
    ids = {r["paper_id"] for r in studies}
    require(len(studies) == 483 and len(ids) == 483 and "" not in ids, "Expected 483 unique study identifiers")
    require(len({r["study_family_id"] for r in studies}) == 483, "Expected unique study families")
    versions = read(2, "ELIGIBLE_PUBLICATION_VERSION_LEDGER_N547.csv")
    preferred = [r for r in versions if r["preferred_for_analysis"].lower() == "yes"]
    require(len(versions)==547 and len(preferred)==483 and len(versions)-len(preferred)==64, "Publication-version counts differ")
    require(len({r["record_key"] for r in versions}) == 547, "Duplicate publication-version identifier")
    require({r["record_key"] for r in preferred}=={r["preferred_record_key"] for r in studies}, "Preferred-publication join differs")
    require({r["source_record_id"] for r in preferred}==ids, "Preferred study identifiers differ")
    searches = read(1,"SEARCH_STRATEGIES_18.csv")
    totals = read(1,"SOURCE_TOTALS.csv")
    require(len(searches)==18 and len(totals)==6 and sum(int(r["retrieval_occurrences"]) for r in totals)==9719,"Search counts differ")
    decisions = read(2,"COMPLETE_RECORD_LEVEL_SELECTION_LEDGER_N3919.csv")
    require(len(decisions)==3919 and len({r["paper_id"] for r in decisions})==3919,"Screening records differ")
    require(sum(r["final_decision"]=="INCLUDE" for r in decisions)==547,"Eligible decision count differs")
    direct = sum({r["reviewer_A_decision"],r["reviewer_B_decision"]}=={"INCLUDE","EXCLUDE"} for r in decisions)
    three = sum(r["reviewer_A_decision"]!=r["reviewer_B_decision"] for r in decisions)
    binary = sum((r["reviewer_A_decision"]=="INCLUDE")!=(r["reviewer_B_decision"]=="INCLUDE") for r in decisions)
    require((direct,three,binary)==(477,551,501),"Paired model-review disagreements differ")
    years = Counter(r["year"] for r in studies)
    for row in read(3,"SUPPLEMENT_ANNUAL_COUNTS_COMPLETE.csv"):
        require(years[row["category"][:4]]==int(row["count"]),"Annual study count differs")
    family_counts = Counter(x.strip() for r in studies for x in r["model_families_current"].split(";") if x.strip())
    published = {r["model_family"]:int(r["publications"]) for r in read(3,"CORRECTED_MODEL_FAMILY_COUNTS_N483.csv")}
    require(dict(family_counts)==published,"Corrected model family counts differ")
    audit = read(5,"MODEL_AUDIT_RECORDS_N483.csv")
    require(len(audit)==483 and {r["paper_id"] for r in audit}==ids,"Model-audit identifiers differ")
    current = {r["paper_id"]:r["model_families_current"] for r in studies}
    require(all(r["corrected_model_families"]==current[r["paper_id"]] for r in audit),"Current model family audit join differs")
    phrases = read(4,"SUPPLEMENT_PER_STUDY_PHRASE_INDICATORS.csv")
    require(len(phrases)==483 and {r["paper_id"] for r in phrases}==ids,"Phrase study identifiers differ")
    require(all(v in {"0","1"} for r in phrases for k,v in r.items() if k!="paper_id"),"Invalid phrase indicator")
    pilot=read(6,"01 Pilot/PILOT_RECORDS_N100.csv")
    s1=read(6,"02 Eligibility Sample 1/INITIAL_COMPARISONS_100.csv")
    s2=read(6,"03 Eligibility Sample 2/DECISIONS_AND_RATIONALES_100.csv")
    require(len(pilot)==100 and len({r["paper_id"] for r in pilot})==100,"Pilot identifiers differ")
    require(all(r["reviewer_kind"]=="AI agent workflow dry run; not a human reviewer" for r in pilot),"Pilot must be labelled as an agent test")
    require(Counter(r["agent_initial_decision"] for r in pilot)=={"EXCLUDE":67,"INCLUDE":30,"UNCERTAIN":3},"Pilot initial decisions differ")
    require(len(s1)==100 and len({r["paper_id"] for r in s1})==100,"August sample differs")
    require(len(s2)==100 and len({r["paper_id"] for r in s2})==100,"September sample differs")
    overlap = {r["paper_id"] for r in pilot}&{r["paper_id"] for r in s1}
    reported = read(6,"01 Pilot/PILOT_SAMPLE1_OVERLAP_N23.csv")
    require(len(overlap)==23 and len(reported)==23 and {r["paper_id"] for r in reported}==overlap,"Pilot overlap differs")
    require(len({r["paper_id"] for r in s1}&{r["paper_id"] for r in s2})==5,"Human-sample overlap differs")
    require(sum(r["lead_author_initial_decision"]==r["then_current_pipeline_decision"] for r in s1)==85,"August initial human comparison differs")
    original=read(6,"02 Eligibility Sample 1/ORIGINAL_RECORDED_DECISIONS_AND_RATIONALES_100.csv")
    s1map={r["audit_id"]:r for r in s1}
    require(len(original)==100 and all(r["human_initial_decision"]==s1map[r["audit_id"]]["lead_author_initial_decision"] and r["paper_id"]==s1map[r["audit_id"]]["paper_id"] for r in original),"Recovered human answer join differs")
    inside=[r for r in s2 if r["outside_candidate_frame"].lower() not in {"true","yes","1"}]
    require(len(inside)==80,"September candidate-frame split differs")
    firm=[r for r in inside if r["after_blank_clarification"] in {"INCLUDE","EXCLUDE"}]
    require(len(firm)==78 and sum(r["after_blank_clarification"]==r["frozen_production_decision"] for r in firm)==65,"September initial human comparison differs")
    require(sum(r["lead_author_post_comparison_decision"]==r["frozen_production_decision"] for r in inside)==71,"September post-comparison result differs")
    recheck=read(6,"04 Recheck of 15 disagreements/INITIAL_AND_LATEST_AUTHOR_DECISIONS_15.csv")
    require(len(recheck)==15,"August recheck count differs")
    nts=read(6,"05 NTS classification check/COMPARISONS_38_STUDIES_342_JUDGEMENTS.csv")
    require(len(nts)==342 and len({r["paper_id"] for r in nts})==38,"NTS comparison size differs")
    require(Counter(r["comparison"] for r in nts)=={"AGREE":305,"DIFFER":22,"UNCLEAR":15},"NTS judgement totals differ")
    require({r["paper_id"] for r in nts}<=ids,"NTS comparison contains non-corpus study")
    require(len({(r["paper_id"],r["domain"]) for r in nts})==342,"Duplicate NTS judgement")
    require(len(read(6,"05 NTS classification check/AUTHOR_CHECKED_NTS_44.csv"))==44,"NTS reviewed count differs")
    require(len(read(6,"05 NTS classification check/DIFFERENT_OR_UNCLEAR_NTS_JUDGEMENTS.csv"))==37,"NTS difference count differs")
    require(len(list((root/"results/figures").glob("Fig[1-7].png")))==7,"Expected seven current article figures")
    freeze=json.loads((root/"audit/PUBLIC_RELEASE_FREEZE_V3.json").read_text(encoding="utf-8"))
    require(freeze["authoritative_counts"]==EXPECTED_COUNTS,"Frozen authority counts differ")
    return {"unique_studies":483,"eligible_records":547,"alternate_versions":64,
        "direct_model_disagreements":direct,"pilot_records":100,"pilot_august_overlap":23,
        "august_september_overlap":5,"nts_judgements":342}

def release_files(root):
    return {p.relative_to(root).as_posix():p for p in root.rglob("*")
        if p.is_file() and not any(x in p.relative_to(root).parts for x in {".git","__pycache__", ".pytest_cache"})
        and p.relative_to(root).as_posix()!="SHA256SUMS.csv"}

def verify(root):
    root=portable_root(root)
    records=read_rows(root/"SHA256SUMS.csv")
    actual=release_files(root)
    names=[r["relative_path"] for r in records]
    require(len(set(names))==len(names),"Duplicate checksum entry")
    require(set(names)==set(actual),"File checksum coverage differs")
    for r in records:
        path=actual[r["relative_path"]]
        require(not path.is_symlink(),"Symbolic links are not release files")
        require(path.stat().st_size==int(r["bytes"]),"Byte count differs: "+r["relative_path"])
        require(sha256(path)==r["sha256"],"SHA-256 differs: "+r["relative_path"])
    return {"status":"PASS","release_files_verified":len(records),"scientific_checks":check_science(root)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",nargs="?",type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    try:
        print(json.dumps(verify(args.root),indent=2))
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},indent=2),file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
