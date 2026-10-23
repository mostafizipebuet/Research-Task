"""Meaningful checks for parsing, denominators, review provenance and metric edges."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from stselab.data import parse_workbook,DataError,unique_object,canonical_requirement
from stselab.coding import annotate,propose,final_gate,REVIEW_FIELDS
from stselab.metrics import wilson,jaccard,cluster_interval,build_metrics,reviewer_agreement

ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'config'/name).read_text(encoding='utf-8'))

class FakeCell:
    def __init__(self,value):self.value=value;self.data_type='s'
class FakeSheet:
    title='Execution1';max_row=2;max_column=1
    def __init__(self,obj):self.obj=obj
    def __getitem__(self,key):return FakeCell('Raw Data' if key=='A1' else json.dumps(self.obj))
class FakeWorkbook:
    sheetnames=['Execution1']
    def __init__(self,obj):self.sheet=FakeSheet(obj)
    def __iter__(self):return iter([self.sheet])
    def close(self):pass

class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.criteria=load('criteria.json');cls.reference=load('requirements_reference.json');cls.book=load('reason_codebook.json')
        cls.flags,cls.opp,cls.audit=parse_workbook(ROOT/'inputs/raw_data.xlsx',cls.criteria,cls.reference)
        cls.ann=annotate(cls.flags,cls.book)
    def test_raw_accounting_and_sentinels(self):
        self.assertEqual(len(self.flags),3229);self.assertEqual(len(self.opp),9100)
        self.assertEqual(int(self.opp.flagged.sum()),len(self.flags))
        self.assertEqual(self.audit['naming_gaps'],[1000])
        counts=self.flags.groupby(['requirement_id','criterion_id']).size()
        self.assertEqual(counts['PR.1','A4'],81);self.assertEqual(counts['PR.1','A9'],100)
        self.assertEqual(counts['FR.1','A6'],58);self.assertEqual(counts['FR.1','A5'],48)
    def test_zero_flags_retained(self):
        zero=self.opp[(self.opp.requirement_id=='FR.2')&(self.opp.criterion_id=='A2')]
        self.assertEqual(len(zero),100);self.assertEqual(zero.flagged.sum(),0)
    def test_no_repeated_observations_dropped(self):
        self.assertGreater(len(self.flags),self.flags.explanation.nunique())
        self.assertFalse(self.flags.record_id.duplicated().any())
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(DataError):json.loads('{"FR.1":[],"FR.1":[]}',object_pairs_hook=unique_object)
    def test_missing_requirement_rejected(self):
        obj={r['requirement_id']:[] for r in self.reference['requirements']};obj.pop('RR.1')
        with patch('stselab.data.openpyxl.load_workbook',return_value=FakeWorkbook(obj)):
            with self.assertRaises(DataError):parse_workbook('unused',self.criteria,self.reference,expected_runs=1)
    def test_duplicate_criterion_rejected(self):
        obj={r['requirement_id']:[] for r in self.reference['requirements']}
        flag={'criterion':'A4','name':'Unambiguous','explanation':'a'};obj['PR.1']=[flag,flag]
        with patch('stselab.data.openpyxl.load_workbook',return_value=FakeWorkbook(obj)):
            with self.assertRaises(DataError):parse_workbook('unused',self.criteria,self.reference,expected_runs=1)
    def test_multilabel_and_nonmatching_text(self):
        labels,_=propose('It uses shall be able to and no more than, which are discouraged.','PR.3',self.book)
        self.assertEqual(set(labels),{'R06','R08'})
        labels,_=propose('The measurement conditions and datum are not stated.','PR.1',self.book)
        self.assertNotIn('R01',labels)
        labels,_=propose('A novel argument with no recognizable signal.','FR.1',self.book)
        self.assertEqual(labels,[])
    def test_unit_discrepancy_and_accuracy_scope_separate(self):
        labels,_=propose('It is unclear whether accuracy applies to the final position or the entire path; 0.1 inches equals 2.54 mm.','PR.1',self.book)
        self.assertIn('R10',labels);self.assertIn('R11',labels)
    def test_wilson_boundary_and_known_value(self):
        lo,hi=wilson(0,100);self.assertAlmostEqual(lo,0);self.assertAlmostEqual(hi,.0369934982,places=8)
        lo,hi=wilson(100,100);self.assertAlmostEqual(lo,.9630065018,places=8);self.assertAlmostEqual(hi,1)
        self.assertTrue(math.isnan(wilson(0,0)[0]))
    def test_jaccard_joint_absence_not_one(self):
        self.assertEqual(jaccard({'R01'},{'R01','R02'}),.5)
        self.assertTrue(math.isnan(jaccard(set(),set())))
    def test_cluster_bootstrap_reproducible(self):
        a=cluster_interval([0,.5,1],500,31);b=cluster_interval([0,.5,1],500,31)
        self.assertEqual(a,b)
    def test_unresolved_not_treated_as_unflagged(self):
        opp=pd.DataFrame([dict(run_id=f'r{i}',requirement_id='X',criterion_id='A4',flagged=int(i<2)) for i in range(4)])
        ann=pd.DataFrame([dict(record_id='a',run_id='r0',requirement_id='X',criterion_id='A4',effective_reason_ids='R01',proposed_reason_ids='R01',label_review_status='proposed',source_status='pending',alignment_status='pending',explanation='x',review_notes='',assessment_note=''),
                          dict(record_id='b',run_id='r1',requirement_id='X',criterion_id='A4',effective_reason_ids='',proposed_reason_ids='',label_review_status='proposed',source_status='pending',alignment_status='pending',explanation='y',review_notes='',assessment_note='')])
        metrics=build_metrics(opp,ann,self.book,dict(n_runs=4,n_requirements=1,run_ids=['r0','r1','r2','r3']),draws=100)
        row=metrics['run_stability'].iloc[0]
        self.assertEqual(row.total_run_pairs,6);self.assertEqual(row.comparable_pairs,3)
        self.assertEqual(row.unresolved_flag_explanations,1);self.assertEqual(row.pairs_both_positive,0)
        self.assertEqual(metrics['reason_frequency'].iloc[0].unconditional_rate,.25)
        self.assertEqual(metrics['reason_frequency'].iloc[0].conditional_rate,.5)
    def test_review_hash_and_provenance(self):
        row=self.ann.iloc[0]
        review={k:row[k] for k in REVIEW_FIELDS};review['explanation_sha256']='changed'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'review.csv';pd.DataFrame([review]).to_csv(p,index=False)
            with self.assertRaises(ValueError):annotate(self.flags,self.book,p)
            review['explanation_sha256']=row.explanation_sha256;review['label_review_status']='reviewed';review['reviewed_reason_ids']='R04'
            pd.DataFrame([review]).to_csv(p,index=False)
            with self.assertRaises(ValueError):annotate(self.flags,self.book,p)
    def test_review_override_changes_labels_preserves_suggestions(self):
        row=self.ann.iloc[0];review={k:row[k] for k in REVIEW_FIELDS}
        review.update(label_review_status='reviewed',reviewed_reason_ids='R02',reviewer='Synthetic test reviewer',reviewed_at='2026-10-21T00:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'review.csv';pd.DataFrame([review]).to_csv(p,index=False)
            changed=annotate(self.flags,self.book,p).iloc[0]
            self.assertEqual(changed.effective_reason_ids,'R02');self.assertEqual(changed.proposed_reason_ids,row.proposed_reason_ids)
            self.assertEqual(changed.explanation,row.explanation)
    def test_final_mode_rejects_unreviewed(self):
        with self.assertRaises(ValueError):final_gate(self.ann,self.book)
    def test_independent_review_not_invented(self):
        with self.assertRaises(ValueError):reviewer_agreement(self.ann,self.ann,self.book)

if __name__=='__main__':unittest.main()
