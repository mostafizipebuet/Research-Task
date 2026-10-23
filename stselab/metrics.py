"""Descriptive estimates with explicit units and denominators.

Run-level bootstrapping preserves dependence among the fixed 13 requirements.
Pairwise reason similarities are descriptive; run pairs are not independent samples.
"""
from itertools import combinations
from statistics import NormalDist
import math
import numpy as np
import pandas as pd
from .coding import split_codes

def wilson(k, n, level=0.95):
    if n <= 0: return (float('nan'),float('nan'))
    if not 0 <= k <= n: raise ValueError('Wilson counts must satisfy 0 <= k <= n')
    z = NormalDist().inv_cdf((1+level)/2)
    p = k/n
    d = 1+z*z/n
    center=(p+z*z/(2*n))/d
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,center-half),min(1,center+half)

def cluster_interval(values, draws=2000, seed=20261021, level=0.95):
    values=np.asarray(values,dtype=float)
    if values.size==0: return (float('nan'),float('nan'))
    rng=np.random.default_rng(seed)
    indices=rng.integers(0,len(values),size=(draws,len(values)))
    boots=values[indices].mean(axis=1)
    alpha=(1-level)/2
    return tuple(np.quantile(boots,[alpha,1-alpha]))

def jaccard(a,b):
    union=a|b
    return len(a&b)/len(union) if union else float('nan')

def reason_long(annotations):
    cols=['record_id','run_id','requirement_id','criterion_id','reason_id','label_review_status']
    rows=[]
    for r in annotations.to_dict('records'):
        for reason in split_codes(r['effective_reason_ids']):
            rows.append({**{k:r[k] for k in cols if k!='reason_id'},'reason_id':reason})
    return pd.DataFrame(rows,columns=cols)

def build_metrics(opportunities, annotations, codebook, audit, draws=2000,seed=20261021,level=0.95):
    n=audit['n_runs']; q=audit['n_requirements']; runs=audit['run_ids']
    reasons=reason_long(annotations)
    names={r['reason_id']:r['label'] for r in codebook}
    freq=opportunities.groupby(['requirement_id','criterion_id'],sort=False).agg(flags=('flagged','sum'),runs=('flagged','size')).reset_index()
    freq['rate']=freq['flags']/freq.runs
    bounds=[wilson(k,m,level) for k,m in zip(freq['flags'],freq.runs)]
    freq['wilson_low']=[b[0] for b in bounds];freq['wilson_high']=[b[1] for b in bounds]
    crit_rows=[]
    for crit,g in opportunities.groupby('criterion_id',sort=False):
        run_rates=g.groupby('run_id').flagged.mean().reindex(runs).to_numpy()
        lo,hi=cluster_interval(run_rates,draws,seed,level)
        crit_rows.append(dict(criterion_id=crit,flags=int(g.flagged.sum()),opportunities=len(g),rate=float(g.flagged.mean()),
                             cluster_boot_low=lo,cluster_boot_high=hi,independent_resampling_units=n,fixed_requirements=q))
    crit_df=pd.DataFrame(crit_rows)
    pair_flag_count=freq.set_index(['requirement_id','criterion_id'])['flags'].to_dict()
    reason_rows=[]
    for (req,crit,reason),g in reasons.groupby(['requirement_id','criterion_id','reason_id'],sort=False):
        count=g.run_id.nunique();flagged=int(pair_flag_count[(req,crit)])
        lo,hi=wilson(count,n,level)
        clo,chi=wilson(count,flagged,level)
        reason_rows.append(dict(requirement_id=req,criterion_id=crit,reason_id=reason,reason_label=names[reason],
                                runs_with_reason=count,total_runs=n,flagged_runs=flagged,unconditional_rate=count/n,
                                conditional_rate=count/flagged,wilson_low=lo,wilson_high=hi,
                                conditional_wilson_low=clo,conditional_wilson_high=chi))
    reason_freq=pd.DataFrame(reason_rows,columns=['requirement_id','criterion_id','reason_id','reason_label','runs_with_reason','total_runs','flagged_runs','unconditional_rate','conditional_rate','wilson_low','wilson_high','conditional_wilson_low','conditional_wilson_high'])
    by_crit=[]
    for crit in crit_df.criterion_id:
        denom=int(annotations.criterion_id.eq(crit).sum())
        for reason in names:
            count=int(((reasons.criterion_id==crit)&(reasons.reason_id==reason)).sum())
            by_crit.append(dict(criterion_id=crit,reason_id=reason,reason_label=names[reason],flag_explanations_with_reason=count,
                                total_flag_explanations=denom,share_of_flags=count/denom if denom else np.nan,
                                opportunity_prevalence=count/(n*q),opportunities=n*q))
    by_crit=pd.DataFrame(by_crit)
    stability=[]
    for row in freq.to_dict('records'):
        req,crit=row['requirement_id'],row['criterion_id']
        subset=annotations[(annotations.requirement_id==req)&(annotations.criterion_id==crit)]
        present={r['run_id']:set(split_codes(r['effective_reason_ids'])) or None for r in subset.to_dict('records')}
        exact=[];positive_j=[];both_j=[];known_pairs=0
        for a,b in combinations(runs,2):
            x,y=present.get(a,set()),present.get(b,set())
            if x is None or y is None: continue  # unresolved is not an empty/unflagged set
            known_pairs+=1;exact.append(x==y)
            if x or y: positive_j.append(jaccard(x,y))
            if x and y: both_j.append(jaccard(x,y))
        m=row['flags'];total_pairs=n*(n-1)//2
        stability.append(dict(requirement_id=req,criterion_id=crit,flagged_runs=m,unresolved_flag_explanations=sum(x is None for x in present.values()),
                              flag_agreement=(m*(m-1)+(n-m)*(n-m-1))/(n*(n-1)) if n>1 else np.nan,
                              exact_reason_agreement_all=float(np.mean(exact)) if exact else np.nan,
                              mean_jaccard_at_least_one_positive=float(np.mean(positive_j)) if positive_j else np.nan,
                              mean_jaccard_both_positive=float(np.mean(both_j)) if both_j else np.nan,
                              total_run_pairs=total_pairs,comparable_pairs=known_pairs,
                              pairs_at_least_one_positive=len(positive_j),pairs_both_positive=len(both_j)))
    stability=pd.DataFrame(stability)
    overlaps=[]
    for (req,reason),g in reasons.groupby(['requirement_id','reason_id']):
        by={c:set(x.run_id) for c,x in g.groupby('criterion_id')}
        for a,b in combinations(sorted(by),2):
            x,y=by[a],by[b]
            overlaps.append(dict(requirement_id=req,reason_id=reason,reason_label=names[reason],criterion_a=a,criterion_b=b,
                                 runs_both=len(x&y),runs_only_a=len(x-y),runs_only_b=len(y-x),runs_neither=n-len(x|y),
                                 n_runs=n,run_jaccard=len(x&y)/len(x|y)))
    overlap=pd.DataFrame(overlaps,columns=['requirement_id','reason_id','reason_label','criterion_a','criterion_b','runs_both','runs_only_a','runs_only_b','runs_neither','n_runs','run_jaccard'])
    quality=[]
    for crit,g in annotations.groupby('criterion_id',sort=False):
        quality.append(dict(criterion_id=crit,n_flags=len(g),labels_reviewed=int(g.label_review_status.eq('reviewed').sum()),
                            source_assessed=int(g.source_status.ne('pending').sum()),alignment_assessed=int(g.alignment_status.ne('pending').sum()),
                            unresolved_labels=int(g.effective_reason_ids.eq('').sum()),
                            multiple_proposed_reasons=int(g.effective_reason_ids.map(lambda s:len(split_codes(s))>1).sum())))
    examples=[]
    # Evidence-backed examples for each category, including differing criteria where available.
    for reason in names:
        ids=reasons.loc[reasons.reason_id.eq(reason),'record_id']
        subset=annotations[annotations.record_id.isin(ids)]
        if subset.empty: continue
        chosen=subset.drop_duplicates('criterion_id').head(3)
        for r in chosen.to_dict('records'):
            examples.append(dict(reason_id=reason,reason_label=names[reason],**{k:r[k] for k in ['record_id','explanation','effective_reason_ids','label_review_status','source_status','alignment_status','review_notes','assessment_note']}))
    stability['interpretation']='Descriptive pairwise similarities; run pairs are dependent; joint absences excluded from positive Jaccard.'
    return dict(flag_frequency=freq,criterion_summary=crit_df,reason_frequency=reason_freq,
                reason_by_criterion=by_crit,run_stability=stability,reason_overlap=overlap,
                review_coverage=pd.DataFrame(quality),reason_examples=pd.DataFrame(examples),reason_assignments=reasons)

def kappa(a,b):
    if not len(a):return np.nan
    a=np.asarray(a);b=np.asarray(b);categories=set(a)|set(b)
    po=float(np.mean(a==b));pe=sum(float(np.mean(a==c))*float(np.mean(b==c)) for c in categories)
    return (po-pe)/(1-pe) if pe<1 else np.nan

def reviewer_agreement(first,second,codebook):
    merged=first.merge(second,on='record_id',suffixes=('_a','_b'))
    g=merged[(merged.label_review_status_a=='reviewed')&(merged.label_review_status_b=='reviewed')]
    if g.empty:raise ValueError('Two reviewer files contain no jointly reviewed labels')
    if (g.reviewer_a==g.reviewer_b).any():raise ValueError('Agreement needs distinct reviewer identities; repeated review by one person is not inter-rater agreement')
    a=[set(split_codes(v)) for v in g.effective_reason_ids_a]
    b=[set(split_codes(v)) for v in g.effective_reason_ids_b]
    rows=[dict(metric='exact_multilabel_agreement',reason_id='',n=len(g),value=float(np.mean([x==y for x,y in zip(a,b)]))),
          dict(metric='mean_multilabel_jaccard',reason_id='',n=len(g),value=float(np.mean([jaccard(x,y) for x,y in zip(a,b)])))]
    for r in codebook:
        x=[r['reason_id'] in s for s in a];y=[r['reason_id'] in s for s in b]
        rows.append(dict(metric='binary_cohen_kappa',reason_id=r['reason_id'],n=len(g),value=kappa(x,y)))
    for field in ['source_status','alignment_status']:
        h=merged[(merged[field+'_a']!='pending')&(merged[field+'_b']!='pending')&(merged.reviewer_a!=merged.reviewer_b)]
        if len(h):rows.append(dict(metric=field+'_cohen_kappa',reason_id='',n=len(h),value=kappa(h[field+'_a'],h[field+'_b'])))
    return pd.DataFrame(rows)
