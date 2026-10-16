#!/usr/bin/env python3
"""Build a transparent correction layer for the 485-study model inventory.

The frozen production input is never modified.  This script combines:

* the adjudicated re-audit of the 225 sole-unspecified records;
* a conservative full-text correction pass over already named records; and
* two explicitly flagged preprint/published-version pairs.

It emits both the production-denominator (n=485) model analysis and a
version-collapsed sensitivity analysis (n=483).  The latter is not silently
promoted to the manuscript authority; it exists so the denominator decision is
visible and reproducible before live-document edits.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path('controlled_source/LLM_Study_FIXED_WINDOWS_TESTED')
SOURCE = ROOT / (
    r"GSE_FULL_RERUN_2026-08-13\16_SCOPUS_VERSION_AND_EXTRACTION"
    r"\scopus_base_v4_final_integration_run02"
    r"\COMBINED_CANONICAL_CHECKED_EXTRACTION_CORRECTED_V2.csv"
)
READJUDICATION = ROOT / (
    r"99_QA\model_name_reaudit_20260825"
    r"\MODEL_NAME_REAUDIT_225_ADJUDICATED.csv"
)
RETRIEVAL_MANIFEST = ROOT / (
    r"ACTIVE_GSE_REVISION_2026-08-13\99_QA"
    r"\model_inventory_fulltext_20260825\FULLTEXT_RETRIEVAL_MANIFEST.csv"
)
OUT = ROOT / (
    r"ACTIVE_GSE_REVISION_2026-08-13\99_QA"
    r"\model_inventory_fulltext_20260825\corrected_inventory"
)


MODEL_ORDER = [
    "ChatGPT_unspecified",
    "GPT-3.5",
    "GPT-4",
    "GPT-4o",
    "GPT-4.1",
    "GPT-5",
    "OpenAI_o_series",
    "Claude",
    "Gemini",
    "Bard",
    "Llama",
    "Mistral",
    "DeepSeek",
    "Qwen",
    "Copilot",
    "Med-PaLM",
    "BioGPT",
    "Grok",
    "Gemma",
    "Phi",
    "Doubao",
    "T5_FLAN",
    "other_named",
    "unspecified_generative_model",
]

DISPLAY = {
    "ChatGPT_unspecified": "ChatGPT (version unspecified)",
    "OpenAI_o_series": "OpenAI o-series",
    "other_named": "Other named model/system",
    "unspecified_generative_model": "Family not established from available evidence",
}


def edit(
    *,
    add: str = "",
    remove: str = "",
    names: str,
    role: str,
    locator: str,
    note: str,
) -> dict[str, str]:
    return {
        "add": add,
        "remove": remove,
        "names": names,
        "role": role,
        "locator": locator,
        "note": note,
    }


# These are deliberately conservative.  A model is added only when the checked
# article shows it was used, evaluated/compared, used for an ancillary study
# task, or substantively synthesised.  Passing background and reference-list
# mentions are excluded.
MANUAL_CORRECTIONS: dict[str, dict[str, str]] = {
    "e5b4ed028b3c0ea2eeec": edit(
        add="ChatGPT_unspecified",
        names="ChatGPT (version not reported)",
        role="ancillary source translation",
        locator="full text, source-corpus translation description",
        note="ChatGPT translated the historical source corpus used to build the role-play.",
    ),
    "9aeba4bdaf161dff8c40": edit(
        add="GPT-4;Bard;Claude;Copilot",
        names="ChatGPT-4; Google Bard; Claude; Microsoft Bing (GPT-4 API)",
        role="model screening/comparison before platform selection",
        locator="full text, implementation discussion, lines 353-359 of retained text",
        note="Initial platform tests compared these systems before ChatGPT-3.5 was selected.",
    ),
    "67e2860b474712736027": edit(
        add="Mistral",
        names="Mistral 7B Instruct v0.2",
        role="evaluated question-answering backbone",
        locator="full text, Table 1 and methods/model appendix",
        note="Mistral 7B was evaluated as the paired LLM backbone for an LLaVA pipeline.",
    ),
    "f1b256cdccd6208d0cc8": edit(
        add="GPT-5",
        names="GPT-5",
        role="evaluated feedback model",
        locator="full text, model table and results tables",
        note="GPT-5 was evaluated alongside GPT-4o and Claude Sonnet 4.",
    ),
    "64a85483f87115653128": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="GPT-3.5 Turbo",
        role="learner-facing virtual-patient response generator",
        locator="full text, system overview",
        note="The central response generator is explicitly GPT-3.5 Turbo.",
    ),
    "3b0e82db448631888b4c": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="GPT-3.5 Turbo 16k",
        role="GutGPT response model",
        locator="full text, Appendix C: Details of GutGPT",
        note="GutGPT explicitly used the GPT-3.5 Turbo 16k API.",
    ),
    "df6dd96b9ea594a121ce": edit(
        add="Qwen;DeepSeek;other_named",
        names="Qwen3-8B; Qwen3-32B; DeepSeek-R1; ChatGLM4.5",
        role="evaluated baseline and component models",
        locator="full text, baseline and intent-recognition tables",
        note="The reported model comparisons include Qwen, DeepSeek and ChatGLM families.",
    ),
    "32b43fcb025a9d77581f": edit(
        add="Gemini;Qwen",
        remove="unspecified_generative_model",
        names="Google Gemini text-to-image; Qwen3-Omni-30B-A3B-Thinking",
        role="appearance generation and automated physics-aware evaluation",
        locator="full text, Methods, appearance variation and automated evaluation",
        note="The previously unnamed multimodal evaluator is identified as Qwen3-Omni.",
    ),
    "296fc2ba93325a6b3ed0": edit(
        add="Grok",
        names="Grok 3",
        role="ancillary error-analysis image generation",
        locator="full text, error-analysis figure methods",
        note="Grok 3 generated privacy-preserving illustrations used in the error analysis.",
    ),
    "412046e11296d150c70a": edit(
        add="GPT-4o;Claude;Gemini;OpenAI_o_series",
        names="ChatGPT-4o; Claude 3.5/3.7 Sonnet; Gemini variants; OpenAI o1",
        role="substantively reviewed models",
        locator="full text, model-specific review sections",
        note="Dedicated synthesis sections discuss these model families, beyond search terms or references.",
    ),
    "d644a8da3cdeae0603e0": edit(
        add="GPT-5",
        remove="ChatGPT_unspecified",
        names="GPT-5; HeyGen",
        role="text chatbot and voice-avatar simulation tools",
        locator="full text, Materials, lines 214-216 of retained text",
        note="The text chatbot is explicitly described as the GPT-5 model.",
    ),
    "25591cbc3c2b21cbfbdf": edit(
        add="GPT-3.5;GPT-4",
        remove="ChatGPT_unspecified",
        names="GPT-3.5 Turbo; GPT-4; Adobe Firefly",
        role="ancillary simulation-design and content-generation tools",
        locator="full text, AI-assisted simulation design methods",
        note="Both exact OpenAI model families were used in designing the educational simulation.",
    ),
    "81337a44aeb46520e3ec": edit(
        add="GPT-4o;Gemini;Claude;Qwen;Mistral",
        remove="unspecified_generative_model",
        names="GPT-4o; Gemini 2.0 Flash/Pro; Claude 3.7 Sonnet; Qwen QWQ 32B; Mistral Small 3",
        role="production workflow and tested local alternatives",
        locator="full text, implementation/model-selection section",
        note="The production workflow and the locally tested alternative are fully named.",
    ),
    "fd0c4ec164cda596074b": edit(
        add="ChatGPT_unspecified",
        names="ChatGPT custom GPT; ChatGPT o1 Pro; ChatGPT-5 Pro",
        role="virtual patient and assessment models",
        locator="full text, patient implementation and assessment methods",
        note="A custom ChatGPT product powered the patient; o1 Pro and GPT-5 Pro scored transcripts.",
    ),
    "3a2d4841832fea8715fe": edit(
        add="GPT-4;DeepSeek;Gemini;other_named",
        names="GPT-4; DeepSeek-V3; Gemini 2.5 Flash; ChatGLM4.5",
        role="judge, patient-agent and intent-recognition comparisons",
        locator="full text, model comparison and evaluation tables",
        note="The framework evaluates these families in addition to GPT-4o and Qwen.",
    ),
    "44090e715310ee158f37": edit(
        add="GPT-4o;GPT-3.5;Claude;Llama;Mistral;other_named",
        remove="unspecified_generative_model",
        names="GPT-4; GPT-4o; GPT-3.5; Claude Opus; Claude Sonnet 3.5; Llama 3 8B/70B; Mixtral 8x7B; Starling-7B-beta",
        role="OSCE transcript-grading models",
        locator="full text, Table 1 and model-performance results",
        note="The supposedly unnamed comparison set is fully enumerated in the article.",
    ),
    "582bc7c400fa7acf214f": edit(
        add="GPT-4",
        remove="ChatGPT_unspecified",
        names="ChatGPT-4 / GPT-4",
        role="simulated patient and scoring model",
        locator="full text, Study Design",
        note="The experiment explicitly selected ChatGPT-4 for both phases.",
    ),
    "b4fa4675ffa2674da6e1": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="GPT-3.5 Turbo",
        role="simulated consultation model",
        locator="full text, Methods",
        note="All experiments used GPT-3.5 Turbo.",
    ),
    "78b358c1b1f53fdbc100": edit(
        add="GPT-3.5;GPT-4;GPT-4o;Claude;Gemini;Llama;Mistral;Qwen;Med-PaLM;OpenAI_o_series;other_named",
        names="GPT-3.5; GPT-4; GPT-4o; Claude 3/4; Gemini; Llama 3; Mistral/Mixtral; Qwen 3; Med-PaLM 2; OpenAI o4-mini; other domain-specific models",
        role="substantively reviewed model families",
        locator="full text, model-specific synthesis sections and figures",
        note="These families receive substantive discussion or model-specific synthesis, not only reference-list mention.",
    ),
    "038dc9e15385ce662149": edit(
        add="GPT-4o;Claude;Gemini",
        names="GPT-4o/4.5; Claude 3.7; Gemini 2.5",
        role="substantively reviewed virtual-patient model comparisons",
        locator="full text, systematic-review synthesis",
        note="The review reports multimodel comparisons while retaining an unspecified category for other systems.",
    ),
    "2972cffe675ec25e930c": edit(
        add="GPT-4",
        remove="ChatGPT_unspecified",
        names="ChatGPT 4.0",
        role="learner-facing patient simulation",
        locator="full text, Methods",
        note="Prompts and interactions were conducted with the free ChatGPT 4.0 version.",
    ),
    "7a9ca4d4d16f4705139f": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="ChatGPT 3.5",
        role="virtual standardized patient",
        locator="full text, intervention description",
        note="The patient role-play was conducted on ChatGPT 3.5 in February 2023.",
    ),
    "03dcc8a1b078476d19e0": edit(
        add="GPT-4",
        remove="ChatGPT_unspecified",
        names="GPT-4 architecture",
        role="VR-OSCE feedback model",
        locator="full text, intervention methods",
        note="The embedded ChatGPT model is explicitly identified as GPT-4 architecture.",
    ),
    "668b98624eeda1089d99": edit(
        add="GPT-4",
        remove="ChatGPT_unspecified",
        names="GPT-4 family / GPT-4 API",
        role="learner-facing simulated patient",
        locator="full text, model development and study procedure",
        note="The article identifies a GPT-4-family custom GPT and states that encounters used the GPT-4 API.",
    ),
    "da8839d00c24db7f6ad6": edit(
        add="GPT-5",
        names="ChatGPT o1 Pro; ChatGPT-5 Pro",
        role="transcript assessment models",
        locator="preprint full text, abstract and assessment methods",
        note="The preprint evaluates both o1 Pro and GPT-5 Pro; it is also flagged as a published-version duplicate.",
    ),
    "1b913a0ed3ab13c6f644": edit(
        add="GPT-3.5;GPT-4;GPT-4o",
        names="ChatGPT; GPT-3.5; GPT-4; GPT-4 Turbo; ChatGPT-4o",
        role="substantively synthesised simulation models",
        locator="full text, types-of-simulation section and included-study table",
        note="The systematic review table explicitly enumerates these GPT families; unspecified is retained for other systems.",
    ),
    "37bb0c4c182653ebb8f9": edit(
        add="Claude;Mistral",
        names="Claude Sonnet 4.0; Mistral Large 2.1",
        role="pre-study model comparison",
        locator="full text, Procedure",
        note="Both models were directly compared with GPT-4o during model selection.",
    ),
    "20e73ed62a3078e6a9b4": edit(
        add="GPT-5;Claude;Grok",
        names="GPT-5.1; GPT-5.2; Claude Sonnet 4.5; Grok 4",
        role="profile generation and evaluated feedback models",
        locator="full text, patient-profile methods and feedback-model comparison table",
        note="These models were used or quantitatively evaluated alongside GPT-4o variants.",
    ),
    "24c93ac0955292251f20": edit(
        add="GPT-3.5;Gemini;GPT-4o;Copilot",
        names="GPT-3.5; Gemini; GPT-4o; Microsoft Copilot",
        role="model comparison, qualitative analysis and preliminary testing",
        locator="full text, formative phase, model evaluation and limitations",
        note="The study compared GPT-3.5 and Gemini, used Copilot for thematic analysis, and tested GPT-4o latency.",
    ),
    "d2f64f874b70a189b145": edit(
        add="Mistral",
        names="Mistral 7B",
        role="tested language encoder",
        locator="full text, model deployment",
        note="Mistral 7B was deployed and evaluated before Vicuna was selected because of device overheating.",
    ),
    "14a6c8b99daf76e8179d": edit(
        add="GPT-4o",
        remove="ChatGPT_unspecified",
        names="ChatGPT-4o",
        role="virtual-patient collection generation",
        locator="full text, Methods, final paragraph of generation workflow",
        note="All prompts were run with ChatGPT-4o between January and March 2025.",
    ),
    "54972cda535948a803e8": edit(
        add="GPT-4o",
        remove="ChatGPT_unspecified",
        names="ChatGPT-4o; SimConverse",
        role="learner-facing patient simulations",
        locator="full text, Methods, study design and procedures",
        note="The ChatGPT condition explicitly used ChatGPT-4o; SimConverse remains other_named.",
    ),
    "f4d7fdee2c3cc083329d": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="ChatGPT-3.5",
        role="standardised-patient simulation",
        locator="full text, Methods",
        note="The mixed-methods intervention explicitly used ChatGPT-3.5.",
    ),
    "60f8f44c77f909f61dc3": edit(
        add="GPT-3.5",
        remove="ChatGPT_unspecified",
        names="ChatGPT 3.5",
        role="smoking-cessation simulated patient",
        locator="full text, Introduction and Intervention",
        note="The intervention used ChatGPT 3.5; students could use its free interface or an existing Plus account.",
    ),
    "38da855b4155bb083590": edit(
        add="GPT-4",
        names="GPT-4",
        role="substantively reviewed model family",
        locator="full text, framing and applications synthesis",
        note="GPT-4 is repeatedly treated as a central model in the review, not merely cited in references.",
    ),
    "5c99d6be17d81210020f": edit(
        add="GPT-3.5;GPT-4;Gemini",
        names="GPT-3.5; GPT-4/ChatGPT-4; Gemini (formerly Bard)",
        role="substantively reviewed model families",
        locator="full text, model overview and performance sections",
        note="The narrative review directly synthesises these model families in orthopaedic education.",
    ),
    "eb8b75c75edacbfa547b": edit(
        add="GPT-3.5;GPT-4;Copilot",
        names="GPT-3.5; GPT-4; Microsoft Copilot",
        role="substantively discussed prompt-design platforms",
        locator="full text, LLM overview and OSCE use-case section",
        note="These platforms/versions are part of the paper's substantive prompt-design discussion.",
    ),
}


# The preferred published reports are retained in the n=483 sensitivity set.
DUPLICATE_VERSION_PAIRS = {
    "15b1e2fee67db58575b7": {
        "preferred": "ed072d60d05f5e236143",
        "basis": "Research Square preprint and BMC Medical Education publication; identical author list and same trial.",
    },
    "da8839d00c24db7f6ad6": {
        "preferred": "fd0c4ec164cda596074b",
        "basis": "JMIR preprint 81673 and published DOI 10.2196/81673; same manuscript number, authors and study.",
    },
}


def split_models(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def ordered(models: set[str]) -> list[str]:
    rank = {name: index for index, name in enumerate(MODEL_ORDER)}
    unknown = sorted((m for m in models if m not in rank), key=str.casefold)
    return sorted((m for m in models if m in rank), key=rank.__getitem__) + unknown


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    fields = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def family_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(rows)
    all_counts: Counter[str] = Counter()
    review_counts: Counter[str] = Counter()
    nonreview_counts: Counter[str] = Counter()
    for row in rows:
        families = split_models(row["corrected_model_families"])
        for family in families:
            all_counts[family] += 1
            if row["final_study_design"] == "evidence_review":
                review_counts[family] += 1
            else:
                nonreview_counts[family] += 1
    result: list[dict[str, object]] = []
    for family, count in sorted(all_counts.items(), key=lambda item: (-item[1], item[0])):
        result.append(
            {
                "model_family": family,
                "display_label": DISPLAY.get(family, family),
                "publications": count,
                "percent_of_analysis_set": f"{100 * count / total:.2f}",
                "non_review_publications": nonreview_counts[family],
                "evidence_review_publications": review_counts[family],
                "analysis_set_n": total,
                "multiple_response_note": "families are non-exclusive; one publication may contribute to several rows",
            }
        )
    return result


def coverage(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(rows)
    named = sum(
        any(family != "unspecified_generative_model" for family in split_models(row["corrected_model_families"]))
        for row in rows
    )
    not_established = total - named
    unspecified_presence = sum(
        "unspecified_generative_model" in split_models(row["corrected_model_families"])
        for row in rows
    )
    return [
        {
            "identity_status": "Named family established from available evidence",
            "publications": named,
            "percent": f"{100 * named / total:.2f}",
            "analysis_set_n": total,
        },
        {
            "identity_status": "No named family established from available evidence",
            "publications": not_established,
            "percent": f"{100 * not_established / total:.2f}",
            "analysis_set_n": total,
        },
        {
            "identity_status": "Unspecified-family label present (non-exclusive diagnostic)",
            "publications": unspecified_presence,
            "percent": f"{100 * unspecified_presence / total:.2f}",
            "analysis_set_n": total,
        },
    ]


def main() -> None:
    with SOURCE.open("r", newline="", encoding="utf-8-sig") as handle:
        base_rows = list(csv.DictReader(handle))
    if len(base_rows) != 485:
        raise RuntimeError(f"expected 485 production rows, found {len(base_rows)}")

    with READJUDICATION.open("r", newline="", encoding="utf-8-sig") as handle:
        readjudicated = {row["paper_id"]: row for row in csv.DictReader(handle)}
    if len(readjudicated) != 225:
        raise RuntimeError(f"expected 225 re-adjudicated rows, found {len(readjudicated)}")

    with RETRIEVAL_MANIFEST.open("r", newline="", encoding="utf-8-sig") as handle:
        retrieval = {row["paper_id"]: row for row in csv.DictReader(handle)}
    if len(retrieval) != 485:
        raise RuntimeError(f"expected 485 retrieval rows, found {len(retrieval)}")

    output_rows: list[dict[str, str]] = []
    correction_rows: list[dict[str, object]] = []
    for source_row in base_rows:
        row = dict(source_row)
        paper_id = row["paper_id"]
        before = set(split_models(row["final_model_families"]))
        after = set(before)
        sources: list[str] = []
        names: list[str] = []
        roles: list[str] = []
        locators: list[str] = []
        notes: list[str] = []
        audit_category = ""

        reaudit = readjudicated.get(paper_id)
        if reaudit and reaudit.get("proposed_model_families", "").strip():
            proposed = {
                "other_named" if value == "PROPOSED_OpenAI_GPT_unspecified" else value
                for value in split_models(reaudit["proposed_model_families"])
            }
            after.discard("unspecified_generative_model")
            after.update(proposed)
            sources.append("225-record adjudicated re-audit")
            names.append(reaudit.get("normalised_models", ""))
            roles.append(reaudit.get("model_role", ""))
            locators.append(reaudit.get("evidence_locator", ""))
            notes.append(reaudit.get("adjudication_note", ""))
            audit_category = reaudit.get("adjudication_category", "")

        manual = MANUAL_CORRECTIONS.get(paper_id)
        if manual:
            after.difference_update(split_models(manual["remove"]))
            after.update(split_models(manual["add"]))
            sources.append("full-text correction pass over already named records")
            names.append(manual["names"])
            roles.append(manual["role"])
            locators.append(manual["locator"])
            notes.append(manual["note"])

        if not after:
            raise RuntimeError(f"correction left {paper_id} without a model-family value")
        unknown = after - set(MODEL_ORDER)
        if unknown:
            raise RuntimeError(f"unknown corrected model labels for {paper_id}: {sorted(unknown)}")

        corrected = ";".join(ordered(after))
        duplicate = DUPLICATE_VERSION_PAIRS.get(paper_id)
        include_483 = "no" if duplicate else "yes"
        family_established = any(value != "unspecified_generative_model" for value in after)
        retrieval_row = retrieval[paper_id]

        row.update(
            {
                "production_model_families": row["final_model_families"],
                "corrected_model_families": corrected,
                "model_identity_status": (
                    "named family established from available evidence"
                    if family_established
                    else "not established from available evidence"
                ),
                "model_audit_names_or_description": (
                    "; ".join(value for value in names if value)
                    or row.get("final_model_description_raw", "")
                ),
                "model_roles_for_correction": "; ".join(value for value in roles if value),
                "model_correction_evidence_locator": "; ".join(value for value in locators if value),
                "model_correction_source": "; ".join(sources),
                "model_correction_note": " ".join(value for value in notes if value),
                "model_correction_applied": "yes" if corrected != row["final_model_families"] else "no",
                "model_reaudit_category": audit_category,
                "retrieval_status": retrieval_row.get("retrieval_status", ""),
                "retrieval_source_type": retrieval_row.get("source_type", ""),
                "retrieval_source_url": retrieval_row.get("source_url", ""),
                "analysis_set_n483_include": include_483,
                "duplicate_version_preferred_paper_id": duplicate["preferred"] if duplicate else "",
                "duplicate_version_basis": duplicate["basis"] if duplicate else "",
            }
        )
        output_rows.append(row)

        if corrected != source_row["final_model_families"]:
            correction_rows.append(
                {
                    "paper_id": paper_id,
                    "doi": row.get("doi", ""),
                    "title": row.get("title", ""),
                    "final_study_design": row.get("final_study_design", ""),
                    "before_model_families": source_row["final_model_families"],
                    "after_model_families": corrected,
                    "audit_names": row["model_audit_names_or_description"],
                    "model_role": row["model_roles_for_correction"],
                    "evidence_locator": row["model_correction_evidence_locator"],
                    "correction_source": row["model_correction_source"],
                    "adjudication_category": audit_category,
                    "note": row["model_correction_note"],
                }
            )

    if len(output_rows) != 485:
        raise RuntimeError("corrected inventory row count drift")
    if len({row["paper_id"] for row in output_rows}) != 485:
        raise RuntimeError("corrected inventory paper IDs are not unique")

    n483_rows = [row for row in output_rows if row["analysis_set_n483_include"] == "yes"]
    if len(n483_rows) != 483:
        raise RuntimeError(f"expected 483 rows after two version collapses, found {len(n483_rows)}")

    OUT.mkdir(parents=True, exist_ok=True)
    inventory_path = OUT / "CORRECTED_485_STUDY_MODEL_INVENTORY.csv"
    correction_path = OUT / "MODEL_CORRECTION_LEDGER.csv"
    n485_counts_path = OUT / "CORRECTED_MODEL_FAMILY_COUNTS_N485.csv"
    n483_counts_path = OUT / "CORRECTED_MODEL_FAMILY_COUNTS_N483.csv"
    n485_coverage_path = OUT / "MODEL_IDENTITY_COVERAGE_N485.csv"
    n483_coverage_path = OUT / "MODEL_IDENTITY_COVERAGE_N483.csv"
    duplicate_path = OUT / "POSSIBLE_MISSED_VERSION_LINKS.csv"

    write_csv(inventory_path, output_rows)
    write_csv(correction_path, correction_rows)
    write_csv(n485_counts_path, family_counts(output_rows))
    write_csv(n483_counts_path, family_counts(n483_rows))
    write_csv(n485_coverage_path, coverage(output_rows))
    write_csv(n483_coverage_path, coverage(n483_rows))
    write_csv(
        duplicate_path,
        [
            {
                "alternate_paper_id": alternate,
                "preferred_paper_id": details["preferred"],
                "basis": details["basis"],
            }
            for alternate, details in DUPLICATE_VERSION_PAIRS.items()
        ],
    )

    summary = {
        "production_source_rows": 485,
        "sole_unspecified_records_reaudited": 225,
        "records_with_corrected_model_families": len(correction_rows),
        "corrections_from_225_record_reaudit": sum(
            bool(readjudicated.get(row["paper_id"], {}).get("proposed_model_families", "").strip())
            for row in output_rows
        ),
        "additional_full_text_corrections_to_already_named_records": len(MANUAL_CORRECTIONS),
        "n485_coverage": coverage(output_rows),
        "n483_coverage": coverage(n483_rows),
        "version_pairs_flagged": len(DUPLICATE_VERSION_PAIRS),
        "version_collapsed_analysis_rows": len(n483_rows),
        "generic_gpt_version_unresolved_coding": (
            "Mapped to locked other_named while the exact audit text preserves "
            "OpenAI GPT family (version unspecified)."
        ),
        "scope_note": (
            "Counts are paper-level and multiple-response. Evidence-review records indicate "
            "models substantively synthesised, not necessarily models run by review authors."
        ),
        "input_hashes": {
            str(SOURCE): sha256(SOURCE),
            str(READJUDICATION): sha256(READJUDICATION),
            str(RETRIEVAL_MANIFEST): sha256(RETRIEVAL_MANIFEST),
        },
    }
    summary_path = OUT / "CORRECTED_MODEL_INVENTORY_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    hashes = []
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "OUTPUT_SHA256.txt":
            hashes.append(f"{sha256(path)}  {path.name}")
    (OUT / "OUTPUT_SHA256.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"outputs: {OUT}")


if __name__ == "__main__":
    main()
