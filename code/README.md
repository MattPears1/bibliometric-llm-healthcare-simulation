# Code and tests

`verify_public_release.py` is the public, offline verification entry point and requires only the Python standard library:

```bash
python code/verify_public_release.py .
```

The remaining scripts are provenance copies of the collection, corrected integration, and V5 analysis code used in the authoritative workspace. The V5 and corrected-integration regression suites passed against the complete hash-bound source package before release (20/20 and 5/5 tests respectively).

Those production regression tests intentionally refer to provider-derived inputs that are not redistributed and to the original fail-closed directory contract. They are supplied for methodological inspection, but a public clone alone cannot execute the complete production suite. This is expected and should not be worked around by replacing missing inputs with live or approximate records.

The production engine depends on `fresh_analysis_engine_v2.py` and its local modules, all supplied in this directory. NumPy and Matplotlib requirements are listed at the repository root.
