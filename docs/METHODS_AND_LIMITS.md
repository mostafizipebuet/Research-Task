# Methods and interpretation limits

## Observation structure

The workbook contains 100 independent runs according to the assignment. Each run evaluates the same 13 requirements against seven criteria. The 9,100 potential checks are not 9,100 independent requirements. Within a run, judgments can be related; the same requirement recurs across all runs. Exact repeated strings remain observations.

## Reason coding

The codebook is an inductive starting proposal informed by this corpus. Regex patterns are transparent retrieval/labeling aids. They detect text consistent with a category; they can overmatch, miss paraphrases, or miss an additional argument within an otherwise matched explanation. Coverage measures only whether at least one label was proposed. No probability/confidence score is invented from regex matches.

Semantic similarity alone would also not establish sound engineering reasoning. This package uses source-linked review for that interpretive question. It does not call an LLM or ask a second model to certify the first model's explanations.

One category may have a clear definition yet co-occur with another. Multi-label coding preserves this. Category granularity influences counts and stability. Examine whether useful distinctions are being collapsed or duplicated, and document changes.

## Frequency estimands

For fixed requirement q and criterion c, let F(r,q,c) be 1 when run r flags the criterion. Flag frequency is the sum of F over runs divided by n=100.

For reason k, let R(r,q,c,k) be 1 when that reason is coded in that flag. All-run reason rate is sum(R)/n. Conditional reason rate is sum(R)/sum(F). A reason counts once within a flag even if several regex patterns match. Cross-criterion counts retain separate flags. The within-requirement overlap table distinguishes same-run co-occurrence from presence in different runs.

All-run reason rates that include unreviewed proposals are conditional on the proposal system. A missing proposed reason does not show that the LLM expressed no meaningful argument. Review unmatched records and check for missed secondary reasons.

## Uncertainty

Wilson intervals are computed for fixed requirement–criterion rates and observed reason rates, using the stated independent-run design. Aggregate criterion summaries use percentile bootstrapping of entire runs, keeping all 13 requirements in each sampled run. There is no resampling of individual flag rows as independent cases.

Intervals are pointwise, descriptive and conditional on the fixed requirement set and supplied generation design. There are no significance stars, multiplicity-adjusted discoveries, claims of universal LLM reliability, or statistical correction for unknown dependence between nominally independent runs. The same seed and run order produce the same resampling indices.

## Consistency

Exact flag agreement is the share of unordered pairs of different runs with identical binary flag decisions. This can be large when a criterion is rarely flagged. The figures therefore show counts/rates alongside agreement.

Reason Jaccard is intersection size divided by union size. The main summary considers pairs where both runs flag and both have a known nonempty reason set. A second summary includes pairs with at least one positive set. Two empty sets are excluded from positive Jaccard. Unresolved flagged sets are unknown, not empty. The output reports all relevant comparison counts. Run pairs are dependent, so no binomial interval is computed using 4,950 pairs as an independent sample size.

## Evidence review

Source status means support for the explanation's claim relative to the provided materials. Criterion fit asks whether the argument fits the assigned definition. These are different assessments and should have different notes where needed. Source absence can prevent a judgment; it is not proof of incorrectness. Similar reasons under A4 and A5 may reflect real conceptual overlap.

The supplied PDF is a reference, not a verified record of exactly what the model received. The model name/version, full prompt, settings and approved writing guide are unavailable. Treat observations about note layout, terms quoted by the model, external ISS environmental values and mandatory writing conventions accordingly.

Do not report precision, recall, F1, or a false-positive rate for actual requirement defects without independent defensible labels. The package's only optional kappa calculations compare documented reviewer assignments; they do not evaluate engineering truth. The program can check that different reviewer names exist, but not that the process was independent.

## Useful source references

- Supplied task PDF, pp.1–3; supplied Point Mass PDF, pp.1–2.
- Topcu et al. (2025), *Trust at Your Own Peril*, DOI https://doi.org/10.1002/sys.21810, especially §§3.3.2, 5.2–5.3. This informs the qualitative approach and discussion of repeated-run stability; its original categories are not imposed on this task.
- NIST Wilson score interval documentation: https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
- Matplotlib figure export documentation: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
