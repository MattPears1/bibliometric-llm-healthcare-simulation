# Section 1. Pilot: 100-record agent workflow test

The original Pilot records were recovered from the retained August research archive. Source hashes and the original protocol amendment accompany this export. Both sampling-manifest output hashes verify, and the recovered human-review input matches the hash locked in the August finalization manifest.

This Pilot used seed 20260813-HV1 and was processed by an AI agent as an end-to-end test before human review. Original columns were named human_* because the pipeline used a human-review template; the public export correctly labels these answers agent_*. Blank final-answer fields are preserved and are not substituted with invented decisions.

PILOT_RECORDS_N100.csv contains all 100 identifiers, bibliographic locators, strata, initial decisions, reason codes, rationales and retained final-answer fields. P001–P100 are publication identifiers mapped to the original H001–H100; these are distinct from the August human sample's H identifiers. Join samples using paper_id.

Exactly 23 paper identifiers also occur in Eligibility Sample 1 (the August human sample, historically named SAMPLE2). PILOT_SAMPLE1_OVERLAP_N23.csv gives the exact mapping. That overlap is separate from the five records shared between the August and September human samples.

The contemporaneous protocol records that only aggregate dry-run results were disclosed before the August human review; it reports that individual model answers were not shown to the human reviewer. This is a historical process statement, not something that can be reconstructed from CSV values alone. The Pilot supplies workflow provenance and is not human validation or an independent accuracy estimate. No Pilot statistic is pooled with the human checks.

Abstracts, source keywords and raw provider payloads are withheld. Original sources are retained privately and remain unchanged.
