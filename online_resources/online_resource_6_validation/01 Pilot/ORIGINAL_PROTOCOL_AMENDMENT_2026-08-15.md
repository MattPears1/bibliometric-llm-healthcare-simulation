# Human-audit sample 2 — protocol amendment, 15 August 2026

## What changed

A second blinded 100-record human-audit sample was drawn under seed `20260815-HV2`.
The original sample (seed `20260813-HV1`) remains in
`prospective_human_audit_v2_run01/` and is unmodified.

## Why

On 15 August 2026 the phase-2 finaliser was executed against sample 1 using an
agent-generated review, as an end-to-end test of the audit pipeline before the human
review began. That run joined sample 1 to its hidden model labels and produced
`DRYRUN_agent_reviewer_results_run01/`. Sample 1's protected labels are therefore no
longer sealed, so sample 1 was not used for the first-human review.

## What was and was not disclosed

Only aggregate and stratum-level results from the dry run were reported: overall
agreement, Cohen's kappa, confusion matrices, and per-stratum counts. **No per-record
answer was disclosed to the human reviewer**, and the row-level file
(`HUMAN_AUDIT_COMPARISON_RESULTS_PROTECTED.csv`) was not opened by them. The human
reviewer therefore does not know the model decision for any individual record.

## Overlap between the two samples

23 of the 100 sample-2 records also appear in sample 1. Several strata draw from small
pools (particularly the boundary-negative subpools of 8, 6 and 6), so a change of seed
cannot produce a disjoint sample. Because no per-record answers were disclosed, these
23 records remain blinded to the human reviewer in the sense that matters — the
reviewer cannot know what the models decided for any of them.

## How sample 2 was produced

The locked builder `build_prospective_human_audit_v2.py` was **not modified**. A
wrapper imported it unchanged and overrode only the seed guard, so the strata
definitions, `stable_rank` selection, shortfall rules, validation and manifest writing
are byte-identical to the locked code path. The seed actually used is recorded in the
package manifest.

Strata are unchanged: 40 difficult, 20 model-agreed inclusions, 20 model-agreed
exclusions, 20 boundary-negative records from outside the candidate frame.

## Reporting requirement

If any result from this audit reaches the manuscript or the response to reviewers, the
following must be stated plainly:

1. Two samples were drawn; the first was expended on a pipeline test and the second was
   used for the human review.
2. The reason for the second draw, as above.
3. That 23 records are common to both samples.
4. That no per-record model decision was disclosed before the human review.

Selective reporting of a second sample without disclosing the first would be
misrepresentation. The honest framing is that the pipeline was tested before use, which
is ordinary good practice, and that the test consumed the original sample.

## Status

Sample 2 is built and blinded. The first-human review has not started. The deferral
record in `07_SCREENING_FINALIZED/model_consensus_finalization_run01/` still stands and
is superseded only when a completed human-audit package exists.
