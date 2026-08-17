# Corrected final integration V2

This corrected-only integration accepts base V4, the authoritative 30-record
Scopus eligibility correction, completed run03 version review, corrected 30-row
checked extraction, and the existing 31-row metadata/OpenAlex package solely as a
source to filter to those exact corrected 30 IDs.

It rejects the historical 31-row extraction and 548-publication/486-family review,
preserves the exact 458 base V4 family member sets, removes only
`sci_42a355e3f11b03dc7d88` / `SIVF-3edd5760b254e839a39f5b03`, verifies protected
fields and ID order, and transactionally creates new outputs. No analysis or
manuscript modification is implemented.

Production commands:

```powershell
python ACTIVE_GSE_REVISION_2026-08-13/03_PIPELINE/scopus_final_integration_corrected_20260816/scopus_final_integration_corrected.py integrate `
  --bindings ACTIVE_GSE_REVISION_2026-08-13/03_PIPELINE/scopus_final_integration_corrected_20260816/PRODUCTION_INPUT_BINDINGS_RUN02.json `
  --output GSE_FULL_RERUN_2026-08-13/16_SCOPUS_VERSION_AND_EXTRACTION/scopus_base_v4_final_integration_run02

python ACTIVE_GSE_REVISION_2026-08-13/03_PIPELINE/scopus_final_integration_corrected_20260816/scopus_final_integration_corrected.py validate `
  --package GSE_FULL_RERUN_2026-08-13/16_SCOPUS_VERSION_AND_EXTRACTION/scopus_base_v4_final_integration_run02
```

The package includes a JSON QA report, manifest, comprehensive hash ledger, and
FROZEN marker. All expected corrected counts are strict assertions.
