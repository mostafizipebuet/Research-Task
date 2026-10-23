#!/usr/bin/env python3
"""Run the complete analysis. See README.md and docs/START_HERE.md."""
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import traceback
import pandas as pd
from stselab.data import parse_workbook,sha256,write_csv
from stselab.coding import annotate,final_gate,review_queue,REVIEW_FIELDS
from stselab.metrics import build_metrics,reviewer_agreement
from stselab.plots import figures
from stselab.reporting import make_tables,write_report
from stselab.review import review_page

ROOT=Path(__file__).resolve().parent

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'inputs/raw_data.xlsx')
    p.add_argument('--out',type=Path,default=ROOT/'outputs/draft')
    p.add_argument('--codebook',type=Path,default=ROOT/'config/reason_codebook.json')
    p.add_argument('--reviewed',type=Path,help='Exported review CSV; unmatched IDs or changed text are rejected')
    p.add_argument('--second-review',type=Path,help='Optional independent reviewer CSV for agreement only')
    p.add_argument('--mode',choices=['draft','final'],default='draft')
    p.add_argument('--bootstrap',type=int,default=None)
    p.add_argument('--seed',type=int,default=None)
    p.add_argument('--allow-changed-workbook',action='store_true',help='Accept a changed file hash, while retaining strict schema/run checks')
    p.add_argument('--skip-figures',action='store_true',help='For calculation checks; full delivery should include figures')
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    out=args.out.resolve()
    if out in {ROOT,ROOT/'inputs',ROOT/'config',ROOT/'working'} or (ROOT/'inputs') in out.parents or (ROOT/'config') in out.parents:
        raise ValueError('Choose a generated-output folder, not the project root or an input/config folder')
    study=load(ROOT/'config/study.json');criteria=load(ROOT/'config/criteria.json');reference=load(ROOT/'config/requirements_reference.json');codebook=load(args.codebook)
    if args.bootstrap is not None:study['bootstrap_draws']=args.bootstrap
    if args.seed is not None:study['seed']=args.seed
    if study['bootstrap_draws']<100:raise ValueError('Use at least 100 bootstrap draws; default 2000 is recommended')
    if sha256(args.input)!=study['input_sha256'] and not args.allow_changed_workbook:
        raise ValueError('Workbook hash differs from the supplied input. Verify the change; use --allow-changed-workbook deliberately for a corrected file.')
    print('[1/6] Parsing all worksheets and checking schema...')
    flags,opportunities,audit=parse_workbook(args.input,criteria,reference,study['expected_runs'])
    print(f'      {audit["n_runs"]} runs, {audit["n_flags"]:,} flags, {audit["n_opportunities"]:,} checks')
    print('[2/6] Proposing multiple reasons; applying explicit reviewed overrides...')
    annotations=annotate(flags,codebook,args.reviewed)
    if args.mode=='final':final_gate(annotations,codebook)
    print(f'      {int(annotations.label_review_status.eq("reviewed").sum()):,} reviewed labels; {int(annotations.effective_reason_ids.eq("").sum())} unmatched explanations')
    out.mkdir(parents=True,exist_ok=True)
    for folder in ['data','tables','figures','audit']: (out/folder).mkdir(exist_ok=True)
    write_csv(flags,out/'data/flag_explanations.csv');write_csv(opportunities,out/'data/all_opportunities.csv')
    write_csv(annotations,out/'data/annotations.csv');write_csv(annotations[REVIEW_FIELDS],out/'data/review_template.csv')
    queue=review_queue(annotations,study['seed']);write_csv(queue,out/'data/review_queue.csv')
    write_csv(annotations[annotations.effective_reason_ids.eq('')],out/'data/unmatched_explanations.csv')
    write_csv(annotations[['explanation_sha256','explanation']].drop_duplicates(),out/'data/unique_explanation_texts.csv')
    print('[3/6] Computing frequencies, clustered uncertainty, stability and overlap...')
    metrics=build_metrics(opportunities,annotations,codebook,audit,study['bootstrap_draws'],study['seed'],study['confidence_level'])
    write_csv(metrics['reason_assignments'],out/'data/reason_assignments.csv')
    if args.second_review:
        second=annotate(flags,codebook,args.second_review)
        agreement=reviewer_agreement(annotations,second,codebook)
        write_csv(agreement,out/'tables/T13_reviewer_agreement.csv')
    # Remove a stale optional agreement output from an earlier generated run.
    elif (out/'tables/T13_reviewer_agreement.csv').exists():
        (out/'tables/T13_reviewer_agreement.csv').unlink()
    print('[4/6] Generating vector figures and formatted scientific tables...')
    captions={} if args.skip_figures else figures(metrics,annotations,audit,codebook,criteria,reference,out/'figures',args.mode)
    tables,cases=make_tables(out/'tables',metrics,annotations,codebook,audit,reference)
    print('[5/6] Building the offline review page and draft report...')
    review_page(out/'review.html',queue,codebook,criteria,reference,audit)
    write_report(out,metrics,annotations,codebook,audit,captions,cases,args.mode,study)
    (out/'audit/data_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'audit/reason_codebook_used.json').write_text(json.dumps(codebook,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'audit/study_settings_used.json').write_text(json.dumps(study,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Source extraction is a convenience only; PDF figure/layout remains authoritative.
    from pypdf import PdfReader
    for file in ['STSELab_Research_Task.pdf','Requirements_Documentation_Point_Mass.pdf']:
        source=ROOT/'inputs'/file
        if source.exists():
            text='\n\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(PdfReader(source).pages))
            (out/'audit'/(source.stem+'.txt')).write_text(text,encoding='utf-8')
    print('[6/6] Writing the reproducibility manifest...')
    versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','matplotlib','openpyxl','pypdf']}
    input_paths=[args.input,args.codebook,ROOT/'config/criteria.json',ROOT/'config/requirements_reference.json',ROOT/'config/study.json',ROOT/'inputs/STSELab_Research_Task.pdf',ROOT/'inputs/Requirements_Documentation_Point_Mass.pdf']+[p for p in [args.reviewed,args.second_review] if p]
    manifest={'package_version':'1.0.0','generated_utc':datetime.now(timezone.utc).isoformat(),'mode':args.mode,
              'command_arguments':vars(args),'python':sys.version,'platform':platform.platform(),'versions':versions,
              'input_sha256':{str(p):sha256(p) for p in input_paths},
              'code_sha256':{str(p.relative_to(ROOT)):sha256(p) for p in sorted(ROOT.glob('stselab/*.py'))+[ROOT/'run_analysis.py']},
              'output_sha256':{str(p.relative_to(out)):sha256(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'},
              'review_disclosure':'Initial codebook and rules are proposals. Reviewer identities are user-supplied assertions; the program cannot certify expertise or independence.'}
    (out/'audit/manifest.json').write_text(json.dumps(manifest,indent=2,default=str,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Done. Open {out / "Report_Draft.html"}')
    print(f'Review labels and interpretations at {out / "review.html"}')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,FileNotFoundError) as exc:
        print('Analysis stopped: '+str(exc),file=sys.stderr);raise SystemExit(2)
