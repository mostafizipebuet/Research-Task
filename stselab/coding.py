"""Transparent multi-label proposals and explicit human overrides; no model calls."""
import hashlib
import json
import re
from pathlib import Path
import pandas as pd

SOURCE_STATUS = ['pending','supported','partly_supported','contradicted','not_verifiable']
ALIGNMENT_STATUS = ['pending','aligned','partly_aligned','misaligned','not_judgable']
REVIEW_FIELDS = ['record_id','explanation_sha256','reviewed_reason_ids','label_review_status','source_status',
                 'alignment_status','reviewer','reviewed_at','evidence_locator','assessment_note']

def split_codes(value):
    return sorted(set(x.strip() for x in str(value or '').split(';') if x.strip()))

def validate_codebook(codebook):
    ids = [x['reason_id'] for x in codebook]
    if len(ids) != len(set(ids)) or 'UNRESOLVED' in ids:
        raise ValueError('Codebook IDs must be unique; UNRESOLVED is reserved')
    for reason in codebook:
        for field in ['label','definition','inclusion','exclusion','patterns','status']:
            if field not in reason:
                raise ValueError(f'{reason["reason_id"]}: missing {field}')
        for pattern in reason['patterns']:
            re.compile(pattern, re.I)

def propose(text, req, codebook):
    labels, evidence = [], []
    for reason in codebook:
        if reason.get('requirement_scope') and req not in reason['requirement_scope']:
            continue
        matches = []
        for pattern in reason['patterns']:
            match = re.search(pattern, text, re.I)
            if match:
                matches.append(dict(pattern=pattern,span=match.group(0),start=match.start(),end=match.end()))
        if matches:
            labels.append(reason['reason_id'])
            evidence.append(dict(reason_id=reason['reason_id'],matches=matches))
    return sorted(labels), evidence

def review_notes(req, crit, labels, text):
    notes = []
    if 'R01' in labels:
        notes.append('Missing provenance does not prove an incorrect numerical value or unnecessary requirement. Distinguish absence of a cited source from an explicit contradiction.')
    if crit == 'A10':
        notes.append('The task defines Conforming but does not supply the approved writing guide. Verify claims that wording is prohibited; exact original model instructions are unknown.')
    if req == 'FR.1' and 'R04' in labels:
        notes.append('Reference PDF p.2 labels Notes 1-4 explicitly. Compare the claim about misplaced assumptions against that layout; do not equate a note with a second obligation. Original prompt formatting is unavailable.')
    if req == 'FR.1' and 'R15' in labels:
        notes.append('Note 1 intentionally leaves the path to be determined. Consider whether this is legitimate design freedom rather than ambiguity.')
    if req in ['FR.1','FR.2'] and any(x in labels for x in ['R16','R18','R09']):
        notes.append('FR1 Notes 3-4 give coordinates and PR7 gives mass. Consider individual-statement sufficiency versus information elsewhere in the requirement set.')
    if 'R11' in labels:
        notes.append('0.1 inch = 2.54 mm. A numerical difference alone does not establish unacceptable engineering rounding; allowed precision is not supplied.')
    if req == 'PR.7':
        notes.append('Reference context says ISS and PR7 mentions normal gravity. Ground testing/loading and on-orbit operation are alternatives to examine; no test intent or original prompt is supplied.')
    if 'R24' in labels:
        notes.append('PR3/PR5 allow up to 30 seconds per movement, so two maxima total 60 seconds. A one-minute cycle is not automatically contradictory; inspect exact wording and included operations.')
    if req == 'ER.1' and re.search(r'approximately|~101|101\.3', text, re.I):
        notes.append('The reference says Assume 21 degrees, not approximately 21; a claimed actual ISS pressure needs an external source. Compare text carefully before declaring a defect.')
    if any(x in labels for x in ['R12','R13','R14','R23']):
        notes.append('Missing measurement detail may concern completeness or verifiability. Examine why it is classified as ambiguity; the assignment does not provide a separate verifiability criterion.')
    if 'R02' in labels or 'R03' in labels:
        notes.append('A design constraint can be legitimate when justified at this level. Compare Necessary, Appropriate and Correct without assuming every prescribed implementation is invalid.')
    if not labels:
        notes.append('No rule matched. Read the whole explanation; add or revise the codebook rather than treating this as an absence of reasons.')
    return ' | '.join(notes)

def annotate(flags, codebook, reviewed_path=None):
    validate_codebook(codebook)
    result = flags.copy()
    rows = []
    for row in result.to_dict('records'):
        labels, evidence = propose(row['explanation'], row['requirement_id'], codebook)
        row.update(proposed_reason_ids=';'.join(labels),effective_reason_ids=';'.join(labels),
                   matched_spans_json=json.dumps(evidence,ensure_ascii=False),label_review_status='proposed',
                   reviewed_reason_ids='',source_status='pending',alignment_status='pending',reviewer='',reviewed_at='',
                   evidence_locator='',assessment_note='',review_notes=review_notes(row['requirement_id'],row['criterion_id'],labels,row['explanation']),
                   coding_origin='deterministic rules from the proposed codebook')
        rows.append(row)
    result = pd.DataFrame(rows)
    if reviewed_path:
        reviewed = pd.read_csv(reviewed_path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        absent = set(REVIEW_FIELDS)-set(reviewed.columns)
        if absent:
            raise ValueError(f'Review file missing columns: {sorted(absent)}')
        if reviewed.record_id.duplicated().any():
            raise ValueError('Duplicate record IDs in review file')
        known = result.set_index('record_id')
        if set(reviewed.record_id)-set(known.index):
            raise ValueError('Review file contains records not present in this workbook')
        code_ids = {c['reason_id'] for c in codebook}
        for review in reviewed.to_dict('records'):
            rid = review['record_id']
            if review['explanation_sha256'] != known.loc[rid,'explanation_sha256']:
                raise ValueError(f'{rid}: original explanation has changed; review cannot be silently reused')
            if 'explanation' in review and review['explanation'] != known.loc[rid,'explanation']:
                raise ValueError(f'{rid}: review file altered the original explanation')
            if review['label_review_status'] not in ['proposed','reviewed','needs_revision']:
                raise ValueError(f'{rid}: invalid label review status')
            if review['source_status'] not in SOURCE_STATUS or review['alignment_status'] not in ALIGNMENT_STATUS:
                raise ValueError(f'{rid}: invalid evidence/alignment status')
            labels = split_codes(review['reviewed_reason_ids'])
            if set(labels)-code_ids:
                raise ValueError(f'{rid}: unknown reason label(s): {set(labels)-code_ids}')
            edited = review['label_review_status']=='reviewed' or review['source_status']!='pending' or review['alignment_status']!='pending'
            if edited and not (review['reviewer'].strip() and review['reviewed_at'].strip()):
                raise ValueError(f'{rid}: reviewed judgments require reviewer and reviewed_at')
            if (review['source_status']!='pending' or review['alignment_status']!='pending') and not (review['evidence_locator'].strip() and review['assessment_note'].strip()):
                raise ValueError(f'{rid}: evidence judgments require a source locator and an explanatory note')
            if review['label_review_status']=='reviewed' and not labels:
                raise ValueError(f'{rid}: a reviewed flag must have at least one defined reason. Add an appropriate code when needed.')
            idx = result.index[result.record_id.eq(rid)][0]
            for field in REVIEW_FIELDS[2:]:
                result.at[idx,field] = review[field]
            if review['label_review_status']=='reviewed':
                result.at[idx,'effective_reason_ids'] = ';'.join(labels)
                result.at[idx,'coding_origin'] = 'human-reviewed labels (reviewer asserted)'
    return result

def final_gate(annotations, codebook):
    issues = []
    for field, mask in [('labels',annotations.label_review_status.ne('reviewed')),
                        ('source status',annotations.source_status.eq('pending')),
                        ('criterion alignment',annotations.alignment_status.eq('pending'))]:
        if mask.any(): issues.append(f'{int(mask.sum())} flags have unfinished {field}')
    used = {c for value in annotations.effective_reason_ids for c in split_codes(value)}
    pending = [c['reason_id'] for c in codebook if c['reason_id'] in used and c['status']!='accepted']
    if pending: issues.append('Used codebook entries must have status accepted: '+', '.join(pending))
    if issues:
        raise ValueError('Final mode requires completed interpretation review. '+ '; '.join(issues))

def review_queue(annotations, seed=20261021):
    """Priorities guide review, not an unbiased validation sample or accuracy estimate."""
    df = annotations.copy()
    frequency = {}
    for value in df.effective_reason_ids:
        for c in split_codes(value): frequency[c] = frequency.get(c,0)+1
    def priority(row):
        labels = split_codes(row.effective_reason_ids)
        return (100 if not labels else 0)+(30 if row.criterion_id in ['A2','A3','A9','A10'] else 0)+(20 if row.requirement_id=='FR.1' else 0)+(15 if len(labels)>1 else 0)+(20 if any(frequency[c]<10 for c in labels) else 0)
    df['review_priority'] = df.apply(priority,axis=1)
    return df.sort_values(['review_priority','record_id'],ascending=[False,True])
