"""Readable, traceable summaries. Interpretation is never silently fabricated."""
from pathlib import Path
import html
import json
import textwrap
import pandas as pd
from .coding import split_codes
from .data import write_csv
from .plots import scientific_tables_pdf

CSS='''body{font:15px/1.65 system-ui,sans-serif;color:#17324d;margin:36px auto;max-width:1120px;padding:0 24px}h1{font-size:30px;line-height:1.2}h2{margin-top:38px;border-bottom:2px solid #007f85;padding-bottom:8px}h3{margin-top:26px}table{border-collapse:collapse;width:100%;font-size:12px;margin:16px 0}th{background:#17324d;color:white;text-align:left}th,td{padding:9px;border:1px solid #d4dfe7;vertical-align:top}tr:nth-child(even){background:#f0f5f7}img{max-width:100%;height:auto}.banner{padding:16px 20px;background:#fff4e4;border-left:5px solid #c87928}.metrics{display:flex;gap:16px;flex-wrap:wrap}.metric{padding:16px;background:#edf5f7;border-radius:8px;min-width:160px}.metric strong{display:block;font-size:28px}.muted{color:#536a7c;font-size:13px}code{background:#edf3f7;padding:2px 4px}pre{background:#edf3f7;white-space:pre-wrap;padding:16px}a{color:#007f85}section{break-inside:avoid}blockquote{border-left:4px solid #007f85;margin:18px 0;padding:8px 18px;background:#f1f6f8}@media print{body{max-width:none;margin:10mm;font-size:10pt}h2{break-before:auto}img{max-height:210mm;object-fit:contain}.banner{border:1px solid #bbb}a{color:inherit}}'''

def markdown_table(df):
    def clean(x):return str(x).replace('|','/').replace('\n',' ')
    rows=['| '+' | '.join(map(clean,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']
    rows+=['| '+' | '.join(clean(x) for x in row)+' |' for row in df.fillna('').itertuples(index=False,name=None)]
    return '\n'.join(rows)

def latex_table(df):
    trans={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    def esc(x):return ''.join(trans.get(c,c) for c in str(x)).replace('\n',' ')
    lines=[r'% UTF-8; compile with XeLaTeX or LuaLaTeX. For long tables use the CSV/HTML versions.',r'\begin{tabular}{'+'l'*len(df.columns)+'}',r'\hline',' & '.join(esc(c) for c in df.columns)+r' \\',r'\hline']
    lines+=[' & '.join(esc(v) for v in row)+r' \\' for row in df.fillna('').itertuples(index=False,name=None)]
    return '\n'.join(lines+[r'\hline',r'\end{tabular}'])

def make_tables(out, metrics, annotations, codebook, audit, reference):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    audit_table=pd.DataFrame([('Runs',audit['n_runs']),('Requirements',audit['n_requirements']),('Criteria',audit['n_criteria']),('Possible requirement–criterion checks',audit['n_opportunities']),('Flag explanations',audit['n_flags']),('Not-flagged checks',audit['n_unflagged']),('Unique explanation strings',audit['n_unique_explanation_texts']),('Observed requirement–criterion pairs',audit['n_observed_requirement_criterion_pairs']),('Labels human-reviewed',int(annotations.label_review_status.eq('reviewed').sum())),('Explanations with no matched reason',int(annotations.effective_reason_ids.eq('').sum()))],columns=['Measure','Value'])
    book=pd.DataFrame([{k:r[k] for k in ['reason_id','label','definition','inclusion','exclusion','status']} for r in codebook])
    flag_matrix=metrics['flag_frequency'].pivot(index='requirement_id',columns='criterion_id',values='flags').reindex(index=[r['requirement_id'] for r in reference['requirements']],columns=['A2','A3','A4','A5','A6','A9','A10']).reset_index()
    tables={'T01_data_audit':audit_table,'T02_reason_codebook':book,'T03_flag_counts_matrix':flag_matrix,
            'T04_flag_rates_and_intervals':metrics['flag_frequency'],'T05_criterion_summary':metrics['criterion_summary'],
            'T06_reason_rates_by_requirement':metrics['reason_frequency'],'T07_reason_by_criterion':metrics['reason_by_criterion'],
            'T08_run_consistency':metrics['run_stability'],'T09_within_requirement_overlap':metrics['reason_overlap'],
            'T10_review_coverage':metrics['review_coverage'],'T11_reason_examples':metrics['reason_examples']}
    htmlparts=['<!doctype html><html><head><meta charset="utf-8"><title>Scientific tables</title><style>'+CSS+'</style></head><body><h1>Scientific tables</h1><p>Counts of flags are observed outputs. Reason labels are provisional until reviewed. CSV files retain full precision and evidence IDs.</p>']
    for name,df in tables.items():
        write_csv(df,out/(name+'.csv'))
        (out/(name+'.md')).write_text(markdown_table(df),encoding='utf-8')
        # Large evidence text tables are more usable in HTML and CSV than tabular LaTeX.
        if name not in ['T02_reason_codebook','T11_reason_examples']:
            (out/(name+'.tex')).write_text(latex_table(df),encoding='utf-8')
        htmlparts+=['<h2>'+name.replace('_',' ')+'</h2>',df.to_html(index=False,escape=True,float_format=lambda x:f'{x:.4f}',na_rep='NA')]
    htmlparts.append('</body></html>');(out/'index.html').write_text('\n'.join(htmlparts),encoding='utf-8')
    reasons=metrics['reason_assignments'].groupby('reason_id').size().rename('Flag explanations').reset_index()
    reasons=reasons.merge(book[['reason_id','label']],on='reason_id').sort_values('Flag explanations',ascending=False)[['reason_id','label','Flag explanations']]
    reasons['Share of flags']=reasons['Flag explanations'].map(lambda x:f'{x/len(annotations):.1%}')
    overlap=metrics['reason_overlap'].sort_values('runs_both',ascending=False).head(15)[['requirement_id','reason_id','criterion_a','criterion_b','runs_both','runs_only_a','runs_only_b']]
    cases=worked_cases(annotations)
    frames=[('Table 1. Data audit',audit_table,[.7,.3],[75,20],14,'The 13 requirements are fixed cases. The repeated runs are the resampling units.'),
            ('Table 2. Proposed reason definitions',book[['reason_id','label','definition']],[.08,.27,.65],[7,28,72],8,'Proposed categories are editable. Inclusion/exclusion rules and regexes are supplied in config/reason_codebook.json.'),
            ('Table 3. Flag counts out of '+str(audit['n_runs']),flag_matrix,[.2]+[.8/7]*7,[15]+[8]*7,15,'Zeros are not-flagged judgments, not verified passes. Wilson intervals are provided in T04.'),
            ('Table 4. Reason frequency across flag explanations',reasons,[.09,.58,.17,.16],[8,55,15,15],14,'Multi-label coding: one flag can contain several reasons. These counts do not measure requirement defect prevalence.'),
            ('Table 5. Same reason under two criteria in one requirement',overlap,[.17,.12,.14,.14,.15,.14,.14],[15,10,10,10,10,10,10],15,'Both = number of runs assigning this reason under both criteria. This association alone does not establish criterion confusion.'),
            ('Table 6. Worked review cases',cases[['Record','Review focus','Question to resolve']],[.24,.25,.51],[26,26,58],4,'These are review prompts, not adjudicated expert findings. Full explanations remain in the linked raw-data records.')]
    scientific_tables_pdf(out/'Scientific_Tables.pdf',frames)
    write_csv(cases,out/'T12_worked_cases.csv')
    return tables,cases

def worked_cases(ann):
    selections=[('FR.1','A6','Notes versus singularity','The supplied PDF already labels Notes 1–4. Does the criticism concern notes, actual additional obligations, or a different input format?'),
                ('FR.1','A4','Design freedom versus ambiguity','Note 1 intentionally leaves the path to be determined. What additional boundary would be necessary, and is the LLM imposing a design choice?'),
                ('PR.1','A9','Missing source versus incorrectness','The ConOps gives no numerical tolerance. Does this establish incorrectness, or only that correctness cannot be verified from the supplied source?'),
                ('PR.3','A10','Style-guide evidence','The explanation calls wording prohibited. Which approved style guide establishes that rule? The supplied task only gives the general criterion.'),
                ('PR.7','A9','Operating versus testing context','The context names ISS and PR7 names normal gravity. Does the condition describe on-orbit use, ground testing, a loading direction, or an unsupported assumption?'),
                ('RR.1','A4','One minute versus two motion limits','Two motions of up to 30 seconds can total one minute. Inspect whether an alleged timing contradiction is real, and what all operations includes.')]
    rows=[]
    for req,crit,focus,question in selections:
        g=ann[(ann.requirement_id==req)&(ann.criterion_id==crit)]
        if req=='RR.1':
            h=g[g.explanation.str.contains('conflict|inconsisten',case=False,regex=True)];g=h if len(h) else g
        if not len(g):continue
        r=g.iloc[0]
        rows.append({'Record':r.record_id,'Review focus':focus,'Question to resolve':question,'Original explanation':r.explanation,'Proposed reasons':r.proposed_reason_ids,'Status':r.label_review_status})
    return pd.DataFrame(rows)

def write_report(out,metrics,annotations,codebook,audit,captions,cases,mode,study):
    out=Path(out);n=audit['n_runs'];total=audit['n_flags'];reviewed=int(annotations.label_review_status.eq('reviewed').sum())
    unclassified=int(annotations.effective_reason_ids.eq('').sum());f=metrics['flag_frequency']
    at100=int(f['flags'].eq(n).sum());at0=int(f['flags'].eq(0).sum());variable=len(f)-at100-at0
    crit=metrics['criterion_summary'].copy();crit['Rate']=crit.rate.map(lambda v:f'{v:.1%}');crit=crit[['criterion_id','flags','opportunities','Rate']]
    label='REVIEWED ANALYSIS' if mode=='final' else 'EXPLORATORY DRAFT — INTERPRETATIONS REQUIRE REVIEW'
    text=f'''# Understanding LLM Explanations for Requirement Quality Violations

**{label}**

## 1. Aim and research questions
Identify the reasons expressed in the LLM's explanations; quantify their consistency across the fixed requirements and repeated runs; examine fit to the assigned criteria; and investigate reasons shared across criteria. Explanations are observable written justifications, not evidence of the model's internal reasoning process.

## 2. Data and source audit
The workbook contains {n} runs of {audit['n_requirements']} requirements against {audit['n_criteria']} criteria, yielding {audit['n_opportunities']:,} possible checks and {total:,} flag explanations. There are {audit['n_unique_explanation_texts']:,} unique explanation strings. Repetition is retained as a frequency observation. All worksheet JSON objects are parsed, schema-checked and reconciled to the complete opportunity grid. An absent criterion is coded as not flagged, not as verified compliance.

Worksheet labels have these numerical gaps: {audit['naming_gaps']}. The actual sheet count is authoritative; a gap is not proof of a missing run, and worksheet order is not a time series. Model identity, complete prompt, sampling settings and random seeds were not supplied. Independence is stated in the task, not verified from execution metadata.

The user-supplied Point Mass PDF provides the reference requirements, context and ConOps. Its exact correspondence to what the original LLM saw is not established. In particular, claims about note placement or quoted wording must be conditional on this source comparison.

## 3. Research design
Each flag is assigned a stable ID: worksheet | requirement | criterion. The pipeline retains its exact text, JSON pointer and text hash. It proposes multiple reason labels using explicit regular expressions in an editable codebook. Codebook development is exploratory and used this dataset; rule coverage is not held-out validation or classification accuracy. Requirement scopes disambiguate domain-specific rules; criterion IDs do not determine the proposed reason labels.

Interpretation review separates (a) the reasons expressed, (b) factual support relative to the supplied source, and (c) fit to the assigned criterion. Reviewed overrides preserve suggestions and record reviewer identity, date, source location and rationale. Current state: {reviewed:,}/{total:,} explanations have reviewed labels; {unclassified:,} have no effective reason. An unresolved flag is excluded from reason-set similarity comparisons and never treated as an empty unflagged set. Even a matched explanation can contain a secondary reason that the rules missed.

Flag rates use {n} runs as denominator for each requirement–criterion pair. Reason rates are reported both per all runs and conditional on the criterion being flagged. Within one explanation a reason is counted once. Multi-label totals can exceed the number of explanations. Conditional rates can be unstable with small denominators, which are displayed.

Wilson score intervals describe uncertainty in repeated-run flag/reason probabilities for a fixed requirement under the stated independence assumption. They do not measure uncertainty about whether a defect is real. Aggregate criterion intervals resample complete runs ({study['bootstrap_draws']:,} draws; seed {study['seed']}), retaining dependence among the 13 fixed requirements. These are pointwise descriptive intervals, not multiplicity-adjusted discovery tests. A degenerate bootstrap interval at a constant count cannot rule out unobserved variation.

Flag agreement counts matching present/absent decisions between run pairs. Reason Jaccard equals the number of shared labels divided by labels in either set. The main reason-similarity plot conditions on both runs flagging; supplemental tables also report at-least-one-positive comparisons and exact agreement including joint absences. These dependent run pairs are descriptive comparisons, not independent statistical replicates. Frequencies are reported alongside consistency to expose prevalence effects.

## 4. Exact descriptive observations
Of the {len(f)} requirement–criterion pairs, {at100} are flagged in every run, {at0} are never flagged, and {variable} vary across runs. Stable flagging does not establish correctness. The table below is calculated directly from the raw flags.

{markdown_table(crit)}

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
'''
    (out/'Report_Draft.md').write_text(text,encoding='utf-8')
    parts=['<!doctype html><html><head><meta charset="utf-8"><title>STSELab analysis report</title><style>'+CSS+'</style></head><body>',
           '<h1>Understanding LLM explanations for requirement quality violations</h1><div class="banner">'+label+'</div>',
           '<div class="metrics">'+''.join(f'<div class="metric"><strong>{v:,}</strong>{html.escape(k)}</div>' for k,v in [('Runs',n),('Flag explanations',total),('Reviewed labels',reviewed),('Unmatched explanations',unclassified)])+'</div>',
           '<p><a href="review.html">Open the offline review interface</a> · <a href="tables/index.html">Browse all tables</a> · <a href="tables/Scientific_Tables.pdf">Scientific table book</a></p>']
    # Simple, explicit conversion avoids an extra markdown dependency.
    in_list=False
    for para in text.split('\n\n')[1:]:
        if para.startswith('## '):parts.append('<h2>'+html.escape(para[3:])+'</h2>')
        elif para.startswith('| '):parts.append(crit.to_html(index=False,escape=True))
        elif para.startswith('- '):parts.append('<ul>'+''.join('<li>'+html.escape(x[2:])+'</li>' for x in para.splitlines() if x.startswith('- '))+'</ul>')
        else:parts.append('<p>'+html.escape(para).replace('\n','<br>')+'</p>')
    parts.append('<h2>Scientific figures</h2>')
    for stem,caption in captions.items():parts.append(f'<section><img src="figures/{stem}.png" alt="{html.escape(caption)}"><p class="muted">{html.escape(caption)}</p></section>')
    parts.append('<h2>Worked review cases</h2>'+cases.to_html(index=False,escape=True)+'<p class="muted">The complete original text and exact source IDs are retained in data/flag_explanations.csv and data/annotations.csv.</p></body></html>')
    (out/'Report_Draft.html').write_text('\n'.join(parts),encoding='utf-8')
    (out/'Figure_Captions.md').write_text('\n\n'.join('## '+k+'\n\n'+v for k,v in captions.items()),encoding='utf-8')
    slides=f'''# Presentation outline — adapt after interpretation review

1. **Research question.** What reasons does the LLM give, and are those reasons stable and appropriate? Explain the four questions in one sentence each.
2. **Data and design.** {n} repeated runs; 13 fixed requirements; 7 criteria; {total:,} flag explanations. Show Figure 1 and define flag, explanation, and reason.
3. **Observed flag pattern.** Figure 2; show variation and stable cells. Emphasize that frequency is not correctness.
4. **How reasons were coded.** Show two original explanations and the codebook. Describe multi-label coding, validation, reviewer involvement, and uncertainty honestly.
5. **Common and rare reasons.** Figure 3; explain two examples and one rare counterexample. State current review coverage.
6. **Consistency.** Figure 4; distinguish flag stability from conditional reason stability. Explain why joint absences and prevalence matter.
7. **Criterion overlap.** Figure 5 plus one within-requirement example from T09. Explain a legitimate alternative to the confusion hypothesis.
8. **Source and criterion-fit review.** Figure 6 and T12. Use actual completed reviews; pending bars cannot support a validity claim.
9. **Limits and next study.** Unknown prompt/model; fixed requirements; lack of expert ground truth; coding uncertainty. Propose a targeted follow-up.
10. **Takeaways and reproducibility.** Present only evidence-supported conclusions. Show how an example traces to a worksheet and how to reproduce the figures.

Suggested speaking time: 12–15 minutes, adjusted to the professor's requested duration. This is an outline, not a finished slide deck.
'''
    (out/'Presentation_Outline.md').write_text(slides,encoding='utf-8')
