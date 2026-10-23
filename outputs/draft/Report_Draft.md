# Understanding LLM Explanations for Requirement Quality Violations

**EXPLORATORY DRAFT — INTERPRETATIONS REQUIRE REVIEW**

## 1. Aim and research questions
Identify the reasons expressed in the LLM's explanations; quantify their consistency across the fixed requirements and repeated runs; examine fit to the assigned criteria; and investigate reasons shared across criteria. Explanations are observable written justifications, not evidence of the model's internal reasoning process.

## 2. Data and source audit
The workbook contains 100 runs of 13 requirements against 7 criteria, yielding 9,100 possible checks and 3,229 flag explanations. There are 2,566 unique explanation strings. Repetition is retained as a frequency observation. All worksheet JSON objects are parsed, schema-checked and reconciled to the complete opportunity grid. An absent criterion is coded as not flagged, not as verified compliance.

Worksheet labels have these numerical gaps: [1000]. The actual sheet count is authoritative; a gap is not proof of a missing run, and worksheet order is not a time series. Model identity, complete prompt, sampling settings and random seeds were not supplied. Independence is stated in the task, not verified from execution metadata.

The user-supplied Point Mass PDF provides the reference requirements, context and ConOps. Its exact correspondence to what the original LLM saw is not established. In particular, claims about note placement or quoted wording must be conditional on this source comparison.

## 3. Research design
Each flag is assigned a stable ID: worksheet | requirement | criterion. The pipeline retains its exact text, JSON pointer and text hash. It proposes multiple reason labels using explicit regular expressions in an editable codebook. Codebook development is exploratory and used this dataset; rule coverage is not held-out validation or classification accuracy. Requirement scopes disambiguate domain-specific rules; criterion IDs do not determine the proposed reason labels.

Interpretation review separates (a) the reasons expressed, (b) factual support relative to the supplied source, and (c) fit to the assigned criterion. Reviewed overrides preserve suggestions and record reviewer identity, date, source location and rationale. Current state: 0/3,229 explanations have reviewed labels; 8 have no effective reason. An unresolved flag is excluded from reason-set similarity comparisons and never treated as an empty unflagged set. Even a matched explanation can contain a secondary reason that the rules missed.

Flag rates use 100 runs as denominator for each requirement–criterion pair. Reason rates are reported both per all runs and conditional on the criterion being flagged. Within one explanation a reason is counted once. Multi-label totals can exceed the number of explanations. Conditional rates can be unstable with small denominators, which are displayed.

Wilson score intervals describe uncertainty in repeated-run flag/reason probabilities for a fixed requirement under the stated independence assumption. They do not measure uncertainty about whether a defect is real. Aggregate criterion intervals resample complete runs (2,000 draws; seed 20261021), retaining dependence among the 13 fixed requirements. These are pointwise descriptive intervals, not multiplicity-adjusted discovery tests. A degenerate bootstrap interval at a constant count cannot rule out unobserved variation.

Flag agreement counts matching present/absent decisions between run pairs. Reason Jaccard equals the number of shared labels divided by labels in either set. The main reason-similarity plot conditions on both runs flagging; supplemental tables also report at-least-one-positive comparisons and exact agreement including joint absences. These dependent run pairs are descriptive comparisons, not independent statistical replicates. Frequencies are reported alongside consistency to expose prevalence effects.

## 4. Exact descriptive observations
Of the 91 requirement–criterion pairs, 21 are flagged in every run, 37 are never flagged, and 33 vary across runs. Stable flagging does not establish correctness. The table below is calculated directly from the raw flags.

| criterion_id | flags | opportunities | Rate |
| --- | --- | --- | --- |
| A2 | 248 | 1300 | 19.1% |
| A3 | 111 | 1300 | 8.5% |
| A4 | 570 | 1300 | 43.8% |
| A5 | 254 | 1300 | 19.5% |
| A6 | 172 | 1300 | 13.2% |
| A9 | 972 | 1300 | 74.8% |
| A10 | 902 | 1300 | 69.4% |

## 5. Reason patterns and evidence
Figures 3–5 and tables T06–T09 describe the effective labels. In draft mode these combine proposed and reviewed labels, with review status preserved at record level. They must not be presented as validated expert categories. Figure 6 shows review coverage, retaining pending judgments. Overlap can be legitimate: one issue may have implications for more than one criterion. Test rival interpretations against exact quotations and source definitions before describing overlap as misuse.

Table T12 and the worked-example guide identify cases deserving close reading: source absence versus incorrectness, explicit notes versus singularity, intentional design freedom versus ambiguity, and style claims without the approved guide. They are candidate discussion points, not adjudicated conclusions.

## 6. Limitations and open questions
- One fixed requirement set, one unspecified LLM/settings combination, and no independent expert defect labels. No accuracy, precision, recall, or F1 of requirement defect detection is estimated.
- The exact prompt, model/version and approved style guide are unavailable. Differences between the supplied reference PDF and original input remain possible.
- The codebook and lexical rules were developed with access to the dataset; misses, overmatching, multi-reason omissions, and granularity effects need review. High pattern coverage is not evidence of correct labels.
- No human review or independent coder agreement is implied by automatic analysis. Inter-rater statistics are emitted only when two distinct reviewer files are supplied; independence remains the researchers' responsibility.
- No universal engineering truth follows from a repeated flag. Missing provenance is not proof that a number is wrong; a wording difference is not automatically a failure to conform.
- Pairwise run similarities and observations within a run are dependent. Inference is conditional on these fixed requirements and the stated run-generation process.
- Written explanations can be post-hoc justifications. This study cannot recover an LLM's hidden reasoning or causal decision rule.

## 7. Relationship to the earlier paper
Topcu et al., Trust at Your Own Peril (2025), DOI 10.1002/sys.21810, combine text comparison and qualitative analysis of generated engineering artifacts. Their sections 5.2–5.3 discuss variability across repeated LLM runs as an open issue. The present task studies the reasons given while evaluating existing requirements. The earlier paper informs careful coding and counterexample checking; its failure modes are not imposed as this study's categories.

## 8. Next steps before submission
Review the reason codebook, inspect the entire set of proposed labels for omissions and errors, enter evidence/criterion-fit judgments, and rerun with the reviewed file. Use the review queue to begin, not as proof that unreviewed records are accurate. Check the difficult and rare cases, including counterexamples. Mark accepted codebook entries explicitly. Final mode checks completion of these records, but it cannot certify the scientific correctness of a person's judgments. Explain your decisions in the final report and presentation.

## Sources
- STSELab_Research_Task.pdf, pp. 1–3: criteria, study design, objectives and deliverables.
- Requirements_Documentation_Point_Mass.pdf, pp. 1–2: supplied source context and requirements.
- inputs/raw_data.xlsx, worksheet A2 cells: exact observations, linked by record ID.
- Topcu et al. (2025), https://doi.org/10.1002/sys.21810, sections 3.3.2, 5.2 and 5.3.
- NIST/SEMATECH e-Handbook, Wilson score intervals: https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
- Matplotlib savefig documentation: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
