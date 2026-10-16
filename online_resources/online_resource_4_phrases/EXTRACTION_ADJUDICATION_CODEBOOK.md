# Locked structured-extraction adjudication codebook

Version 1.1 — locked 14 August 2026 before final extraction began. Version 1.1 only expands controlled model-family labels and requires preservation of at least one evidence URL; eligibility rules are unchanged.

This codebook governs reconciliation of structured fields for records that have a final `INCLUDE` screening decision. It does not change eligibility. Adjudicators must use the study-specific title, complete retained abstract, source keywords, reviewer evidence, and (when needed) a primary publisher/full-text source.

## General rules

- Record only a feature that is actually used, evaluated, classified, or substantively reviewed in the work. Background examples do not count.
- Multiple labels are allowed and are separated by semicolons.
- An empty value is valid when a feature is not reported or not applicable.
- Do not infer an exact model version, specialty, or NTS domain from the journal, author affiliation, or a generic “AI” label.
- Preserve the exact model description in `model_description_raw`; use normalized families only where supported.

## Simulation modalities

Allowed values: `virtual_patient`, `standardized_patient`, `scenario`, `osce`, `roleplay`, `mannequin`, `task_trainer`, `vr_ar_xr`, `serious_game`, `debriefing`, `other`.

Use `virtual_patient` for an interactive digital patient agent and `standardized_patient` for a human or explicitly standardized-patient construct. `scenario` denotes a clinical scenario that is enacted or interactively traversed; static scenario text alone was excluded at screening. `osce` may co-occur with a patient modality. `roleplay` requires enacted role interaction. `debriefing` requires an explicit post-event reflective or feedback process rather than ordinary answer explanation.

## Non-technical-skill domains

Allowed values: `communication`, `teamwork`, `leadership`, `decision_making`, `situational_awareness`, `task_management`, `stress_management`, `professionalism`, `other`.

Code a domain only when it is an educational objective, intervention component, assessment construct, or reported outcome. Do not automatically map diagnostic or clinical reasoning to NTS `decision_making`. Do not code ordinary system-user dialogue as `communication` unless communication skill is taught or assessed.

## Study design

Exactly one value: `randomized_trial`, `nonrandomized_comparative`, `pre_post`, `observational`, `survey`, `qualitative`, `mixed_methods`, `development_evaluation`, `evidence_review`, `methods_framework`, `other`, or `unclear`.

Use the design actually reported. Prefer `mixed_methods` only when quantitative and qualitative data are both collected and integrated. `development_evaluation` covers system/tool development with empirical technical, usability, fidelity, or educational evaluation. `methods_framework` covers a substantive method or framework without an empirical learner evaluation.

## Model families

Record semicolon-separated normalized families actually used or evaluated. Preserve an adjacent raw description. Allowed normalized labels are: `ChatGPT_unspecified`, `GPT-3.5`, `GPT-4`, `GPT-4o`, `GPT-4.1`, `GPT-5`, `OpenAI_o_series`, `Claude`, `Gemini`, `Bard`, `Llama`, `Mistral`, `DeepSeek`, `Qwen`, `Copilot`, `Med-PaLM`, `BioGPT`, `Grok`, `Gemma`, `Phi`, `Doubao`, `T5_FLAN`, `other_named`, and `unspecified_generative_model`.

Do not convert “ChatGPT” to GPT-3.5 or GPT-4 unless the record states the version. Normalize GPT-4 Turbo to `GPT-4`; normalize o1/o3 and related OpenAI reasoning models to `OpenAI_o_series`. `Copilot` is retained separately unless its underlying model is also explicitly identified. Use `other_named` for an explicitly named family that is not in the allowed list, and retain the name in `model_description_raw`. Where a work compares several named models, record each. Background mentions do not count.

## Specialty

Record the explicit learner/practice specialty or profession as a short normalized label. Examples include `general_medical_education`, `nursing`, `pharmacy`, `dentistry`, `emergency_medicine`, `surgery`, `urology`, `anaesthesia`, `paediatrics`, `obstetrics_gynaecology`, `psychiatry`, `paramedicine_ems`, and `interprofessional`. Multiple values are allowed only when the work substantively includes multiple groups. Do not infer a specialty solely from the publishing journal.

## Resolution and evidence

Every included record receives final values for all five fields plus a concise rationale and up to two evidence URLs; at least one primary or retained-record URL must be preserved. No `UNCERTAIN` value is permitted in the locked extraction. If exact detail remains unavailable, use the permitted empty/`unclear`/`unspecified_generative_model` value and explain why.
