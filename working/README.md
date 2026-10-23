# Your reviewed files

Keep exported `annotations_reviewed.csv` here. This folder is not overwritten by the pipeline.
The initial package has no human-reviewed labels or source/criterion judgments.

Run from the package root:

```bash
python run_analysis.py --reviewed working/annotations_reviewed.csv --out outputs/reviewed_draft
```

For an optional second independent coder, save their separate CSV here and add
`--second-review working/reviewer_2.csv`. Only jointly reviewed rows with distinct
reviewer identities are compared. An independent human coder must perform their own review.
