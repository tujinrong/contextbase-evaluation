"""Evaluator-only final row-context guard; never assign semantic scores.

Original identity/context is derived from the selected original row. Reviewers
must reread final reason and evidence in that context and supply attestations.
This verifies their binding and evidence identity, not semantic acceptance.
No operation-specific rule or generation instruction exists here.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def context(row):
    cells=row['originalCells']
    fields={}
    for label,value in re.findall(r'(?:^|；)([^；=]+)=([^；]*)',cells[4]):
        fields[label]=value
    logical=next((fields[name] for name in ('論理項目名','論理名','候補ID','移送ID','内部項目ID') if name in fields),cells[2])
    return {'evaluationId':row['evaluationId'],'documentId':row['documentId'],
        'index':row['index'],'section':cells[1],'specificationId':cells[2],
        'criterion':cells[3],'logicalContext':logical,'kind':fields.get('種類'),
        'eventContext':fields.get('関連イベント',fields.get('関連イベントID')),
        'expectationSha256':hashlib.sha256(cells[4].encode('utf-8')).hexdigest()}

def evidence(row):
    if 'evidence' in row:return row['evidence']
    return [e for name in ('generatedEvidence','sourceEvidence','referenceEvidence') for e in row.get(name,[])]

def reason_hash(row):
    return hashlib.sha256(row['reason'].encode('utf-8')).hexdigest()

def evidence_hash(row):
    canonical=json.dumps(evidence(row),ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--selected',required=True,type=Path)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--review',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    original=read(args.selected)
    contexts={r['evaluationId']:context(r) for r in original}
    assert len(contexts)==len(original)
    if args.report is None:
        result={'schema':'original-row-context-worklist/1','classification':'EVALUATOR_ONLY',
            'generatorMayRead':False,'selectedRowsSha256':sha(args.selected),
            'semanticAcceptanceInferred':False,'rows':[dict(v,reviewStatus='UNREVIEWED') for v in contexts.values()]}
    else:
        assert args.review is not None,'Explicit reviewer attestations required.'
        report=read(args.report);review=read(args.review)
        rows=report.get('rows',report.get('items'))
        assert rows is not None
        assert review['reportSha256']==sha(args.report)
        assert review['selectedRowsSha256']==sha(args.selected)
        reviewed={r['evaluationId']:r for r in review['rows']}
        assert len(reviewed)==len(rows) and set(reviewed)=={r['evaluationId'] for r in rows}
        for row in rows:
            item=reviewed[row['evaluationId']]
            assert item['originalRowContext']==contexts[row['evaluationId']]
            assert item['finalReasonSha256']==reason_hash(row)
            assert item['finalEvidenceSha256']==evidence_hash(row)
            assert item['reasonAndEvidenceRecheckedAgainstOriginalContext'] is True
            assert item['adjacentRowMappingUsedAsSemanticProof'] is False
            assert item['reviewer'] and item['reviewedGeneratedContext']
            assert item['reviewedGeneratedContext']['meaning']
            refs=item['reviewedGeneratedContext']['evidence']
            assert refs and all(ref in evidence(row) for ref in refs)
            assert row['index']==contexts[row['evaluationId']]['index']
            assert row['documentId']==contexts[row['evaluationId']]['documentId']
        result={'schema':'final-row-context-binding-verification/1','classification':'EVALUATOR_ONLY',
            'generatorMayRead':False,'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'selectedRowsSha256':sha(args.selected),'reportSha256':sha(args.report),'reviewSha256':sha(args.review),
            'reviewedRows':len(rows),'identityCriterionAndLogicalContextMatchedSelectedOriginal':True,
            'finalReasonAndEvidenceBoundToExplicitContextReview':True,
            'operationSpecificRules':False,'semanticScoresAssignedByGuard':False,
            'semanticAcceptanceInferredFromMechanicalValidation':False,
            'limitation':'Reviewer rereading is required. Hash equality and attestation identity do not prove semantic correctness.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    assert not args.output.exists(),'Preserve earlier worklist/verification; select a new output name.'
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
