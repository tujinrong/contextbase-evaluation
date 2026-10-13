"""Bind the completed human reread to final reason/evidence identities.

The reviewer reread the new 983-line text and the 120 original context pairs.
This persists that reread only; it never chooses a semantic judgement.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from artifact_store import exclusive_json,exclusive_bytes
import datetime,hashlib,importlib.util,json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard',HERE.parent/'row_context_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
selected=guard.read(HERE/'selected-rows.json')
contexts={r['evaluationId']:guard.context(r) for r in selected}
report=guard.read(HERE/'search-evaluation.json')
review={'schema':'final-original-row-context-review/1','classification':'EVALUATOR_ONLY',
 'generatorMayRead':False,'reviewer':'/root/evaluation_inventory',
 'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reportSha256':guard.sha(HERE/'search-evaluation.json'),
 'selectedRowsSha256':guard.sha(HERE/'selected-rows.json'),
 'generatedSha256':report['generatedSha256'],'generatedVersion':'4.0',
 'humanReviewScope':'New full 983-line candidate, 120 selected original identities/criteria/operation contexts, final reasons and current evidence; no previous match reuse.',
 'mechanicalGuardDoesNotProveSemanticAcceptance':True,'rows':[]}
for row in report['rows']:
    context=contexts[row['evaluationId']]
    gen=[e for e in row['evidence'] if e['role']=='generated']
    review['rows'].append({'evaluationId':row['evaluationId'],
      'originalRowContext':context,'finalReasonSha256':guard.reason_hash(row),
      'finalEvidenceSha256':guard.evidence_hash(row),
      'reasonAndEvidenceRecheckedAgainstOriginalContext':True,
      'adjacentRowMappingUsedAsSemanticProof':False,
      'reviewer':'/root/evaluation_inventory',
      'reviewedGeneratedContext':{'meaning':row['reason'],'evidence':gen}})
assert len(review['rows'])==120
p=HERE/'search-row-context-review.json';assert not p.exists()
exclusive_json(p,review)
print(json.dumps({'reviewedRows':120,'reportSha256':review['reportSha256'],'reviewSha256':guard.sha(p)}))
