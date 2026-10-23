# STSELab Research Package

**Start with `outputs/draft/Report_Draft.html`.** Precomputed results are included, so you can inspect the figures and tables before installing anything.

The archive was rebuilt and the analysis rechecked on 23 October 2026. See `docs/COMPLETENESS_CHECK.md` for the verified contents and the research work still needed before submission.

This package supports Mostafizur Rahman Khan's task from Professor Taylan Topcu: analyze the reasons an LLM gives when evaluating the same 13 engineering requirements in 100 runs. It preserves all 3,229 flag explanations and all 9,100 possible requirement–criterion checks.

## What is complete, and what needs your research judgment?

- **Working and reproducible:** strict parsing, exact flag counts, editable reason proposals, consistency/overlap metrics, figures, tables, draft report sections, presentation outline, and an offline review interface.
- **Provisional:** the proposed reason codebook and regex labels. The bundled version contains no claimed human-reviewed labels, expert defect truth, or independent coder agreement.
- **Your next research step:** review the proposed labels and the evidence/criterion-fit judgments, then rerun. A high rule-match rate is not coding accuracy. Matched explanations may still contain missed secondary reasons.

## Three ways to use it

### A. Inspect the ready-made outputs

1. Unzip the entire folder; do not run files from inside the ZIP viewer.
2. Open `outputs/draft/Report_Draft.html` in your browser.
3. Open `outputs/draft/tables/Scientific_Tables.pdf` for a formatted table book.
4. Open `outputs/draft/review.html` to review the explanations offline.

### B. Run locally (Python 3.11+)

Open a terminal in this folder:

```bash
python -m venv .venv
```

Activate it on Windows:

```bat
.venv\Scripts\activate
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

For the versions used to build the included outputs, install `requirements-tested.txt` instead. Numerical outputs should reproduce with the same inputs, versions and seed. PDF metadata and system font/rendering differences can affect file bytes across systems.

After installation, `run_windows.bat` is a convenient Windows launcher. No GPU, paid API, new LLM run, or model download is required.

### C. Use Google Colab

Upload `START_HERE.ipynb` to Colab. The notebook asks you to upload this ZIP, installs the listed packages, runs the same pipeline, and displays selected outputs. Download the entire results folder as a ZIP when finished. The review page can be opened locally after downloading it; it does not send data anywhere.

## Review and regenerate

1. Open `outputs/draft/review.html`.
2. Read the original explanation and source reference. Select the reasons actually expressed.
3. Choose **Reviewed by me** only after checking the labels.
4. Enter source evidence and criterion-fit judgments separately. Provide a reviewer name, source location and reasoning for those judgments.
5. Click **Save this review**, then **Export review CSV**. Browser storage alone is not a durable export.
6. Save the exported file as `working/annotations_reviewed.csv`.
7. Rerun:

```bash
python run_analysis.py --reviewed working/annotations_reviewed.csv --out outputs/reviewed_draft
```

The program uses reviewed labels where present and proposals elsewhere. All outputs preserve review status. Open the new report to see the effects of your changes.

`config/reason_codebook.json` is authoritative. Edit definitions, scopes or regex patterns there when the data requires it; add new reason IDs rather than forcing unmatched text into an existing category. `config/reason_codebook.csv` is a convenient initial reading copy; editing that CSV alone does not change the pipeline. Rerunning exports the authoritative codebook to table T02. Record changes in `docs/CODEBOOK_CHANGELOG.md`.

For completed analysis:

```bash
python run_analysis.py --reviewed working/annotations_reviewed.csv --mode final --out outputs/final
```

Final mode requires reviewed labels, evidence/criterion judgments, and `status: "accepted"` for every used codebook entry. `not_verifiable` and `not_judgable` are valid honest judgments when explained. Final mode checks recorded completion, not the scientific correctness of those judgments.

## Main files

| Path | Purpose |
|---|---|
| `run_analysis.py` | One command for the complete pipeline |
| `START_HERE.ipynb` | Guided notebook for local Jupyter or Colab |
| `inputs/` | Original workbook and the two supplied task/reference PDFs |
| `config/` | Study settings, source transcriptions, criteria and editable codebook |
| `stselab/` | Parsing, coding, statistics, plotting, reporting and review-page modules |
| `outputs/draft/figures/` | Six figures, each in PNG/PDF/SVG |
| `outputs/draft/tables/` | CSV, Markdown, LaTeX where appropriate, HTML and a PDF table book |
| `outputs/draft/data/` | Exact explanations, full opportunity grid, annotations and review queue |
| `outputs/draft/audit/` | Input/code/output hashes, environment, schema audit and reference text |
| `docs/` | Plain-English instructions, methods, worked example, and codebook history |
| `working/` | Your exported reviews; never overwritten by the pipeline |
| `tests/` | Standard-library tests; no extra test framework needed |

## Useful commands

```bash
python -m unittest discover -s tests -v
python run_analysis.py --help
python run_analysis.py --bootstrap 5000 --out outputs/more_bootstrap
```

For two genuinely independent reviewers:

```bash
python run_analysis.py --reviewed working/reviewer_1.csv --second-review working/reviewer_2.csv --out outputs/two_reviewers
```

T13 is produced only when there are jointly reviewed records and distinct reviewer identities. Different names do not prove that reviews were independent; record the actual procedure.

## Scope and provenance

The task deadline supplied by the professor is November 2, 2026, 8:00 AM EST (7:00 PM Bangladesh). No messages or submissions are sent by this code. The supplied documents and data remain their owners' material.

Read `docs/START_HERE.md` next. The package supports the research; its initial draft report and presentation outline are not a substitute for your interpreted, evidence-checked final report and presentation.
