# Delivery validation

Validation performed on 21 October 2026 using Python 3.12.14 and the versions in `requirements-tested.txt`.

| Check | Result |
|---|---|
| Full pipeline on the supplied workbook | Completed successfully: 100 runs, 13 requirements, 7 criteria, 9,100 opportunities, 3,229 flag explanations |
| Standard-library test suite | All 16 tests passed |
| Missing requirements, duplicate JSON keys, duplicate flags | Rejected in tests |
| Denominators and zero-flag pairs | Reconciled against raw workbook counts |
| Wilson bounds, seeded bootstrap, unresolved reason sets | Passed the included numerical and behavior checks |
| Review provenance | Changed text/hash, unknown records, and incomplete reviewed judgments are rejected |
| Initial review state | Zero human-reviewed labels; eight unmatched explanations remain visible |
| Scientific figures | All six PNG/PDF/SVG sets generated; layouts visually inspected |
| Scientific table book | Eleven pages generated and visually inspected; full detailed tables also exported separately |
| Review-page JavaScript | Entire generated script passed Node syntax compilation |
| Review CSV transport | The actual page's CSV functions round-tripped all 3,229 records, including Unicode, quotes, commas and line breaks |
| Python review import | Accepted the exported test CSV and preserved its explicit override and evidence fields |
| Notebook | All code cells compile; the local project-location cell was executed successfully |

The transport check used one synthetic review outside the deliverable folder. It is not included in the delivered annotations or research results.

The Google Colab upload/download flow was provided but not executed in a live Colab session. A real browser UI automation session was unavailable because this environment has no installed Chromium executable. The review page's source, generated payload, JavaScript syntax and CSV transport were checked; browser rendering and click interactions were not independently automated. The editable CSV workflow can also be used directly.

These checks establish software behavior within the tested scope. They do not validate the proposed reason taxonomy, the correctness of every rule match, source-evidence judgments, criterion fit, or actual requirement defects. Those remain research judgments to record and explain.

To repeat the core tests:

```bash
python -m unittest discover -s tests -v
```
