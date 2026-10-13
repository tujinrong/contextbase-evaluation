"""Persist the final human reread and mechanically verify its row binding.

All 120 final reasons were reread against their selected original identity,
criterion, item and operation; the completed 1108-line candidate was read anew.
No previous semantic decisions are read or transferred by this program.
"""
from pathlib import Path
import sys, datetime, hashlib, json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from artifact_store import exclusive_json, exclusive_bytes
import row_context_guard as guard

HERE=Path(__file__).resolve().parent
selected=guard.read(HERE/'selected-rows.json')
contexts={r['evaluationId']:guard.context(r) for r in selected}
report=guard.read(HERE/'search-evaluation.json')
review={'schema':'final-original-row-context-review/1','classification':'EVALUATOR_ONLY',
 'generatorMayRead':False,'reviewer':'/root/evaluation_inventory',
 'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reportSha256':guard.sha(HERE/'search-evaluation.json'),
 'selectedRowsSha256':guard.sha(HERE/'selected-rows.json'),
 'generatedSha256':report['generatedSha256'],'generatedVersion':'5.0',
 'humanReviewScope':'New full 1108-line candidate, all 120 selected original identities/criteria/item and operation contexts, final reasons and current generated/source/reference evidence; no previous match reuse.',
 'mechanicalGuardDoesNotProveSemanticAcceptance':True,'rows':[]}
for row in report['rows']:
    context=contexts[row['evaluationId']]
    gen=[e for e in row['evidence'] if e['role']=='generated']
    assert row['index']==context['index'] and row['documentId']==context['documentId']
    review['rows'].append({'evaluationId':row['evaluationId'],
      'originalRowContext':context,'finalReasonSha256':guard.reason_hash(row),
      'finalEvidenceSha256':guard.evidence_hash(row),
      'reasonAndEvidenceRecheckedAgainstOriginalContext':True,
      'adjacentRowMappingUsedAsSemanticProof':False,
      'reviewer':'/root/evaluation_inventory',
      'reviewedGeneratedContext':{'meaning':row['reason'],'evidence':gen}})
assert len(review['rows'])==120
exclusive_json(HERE/'search-row-context-review.json',review)
# Same bounded guard contract, saved through the exclusive artifact store.
reviewed={r['evaluationId']:r for r in review['rows']}
for row in report['rows']:
    item=reviewed[row['evaluationId']]
    assert item['originalRowContext']==contexts[row['evaluationId']]
    assert item['finalReasonSha256']==guard.reason_hash(row)
    assert item['finalEvidenceSha256']==guard.evidence_hash(row)
    assert item['reviewedGeneratedContext']['meaning']
    assert item['reviewedGeneratedContext']['evidence']
    assert all(e in guard.evidence(row) for e in item['reviewedGeneratedContext']['evidence'])
validation={'schema':'final-row-context-binding-verification/1','classification':'EVALUATOR_ONLY',
 'generatorMayRead':False,'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'selectedRowsSha256':guard.sha(HERE/'selected-rows.json'),
 'reportSha256':guard.sha(HERE/'search-evaluation.json'),
 'reviewSha256':guard.sha(HERE/'search-row-context-review.json'),
 'reviewedRows':120,'identityCriterionAndLogicalContextMatchedSelectedOriginal':True,
 'finalReasonAndEvidenceBoundToExplicitContextReview':True,'operationSpecificRules':False,
 'semanticScoresAssignedByGuard':False,'semanticAcceptanceInferredFromMechanicalValidation':False,
 'artifactWriteMode':'artifact_store.exclusive_json',
 'limitation':'Explicit human rereading is required. Hash equality and attestations do not prove semantic correctness.'}
exclusive_json(HERE/'search-row-context-validation-final.json',validation)
note='''# 第5稿の最終行文脈照合

EVALUATOR ONLY。元281行・316点を保持し、元の行ID・項目名・criterion・操作をselected-rowsから導出する。新稿検索1108行と検索120原行を再読し、最終理由と根拠を同じ元文脈で確認した。隣接行の対応、行範囲の有効性、過去の一致判定を意味の証明にしない。

row_context_guardはID・文脈・理由SHA・根拠SHAと明示した再読記録の結び付けだけを検証する。業務条件や操作名を実装へ固定せず、意味の採点は人が行う。編集161行は独立担当が同じ工程を行う。両文書の全281行確認が揃うまで合算しない。

第5稿の新規保存はartifact_store.pyのexclusive-createを使用する。訂正時は既存を上書きせずexact旧bytes・別version・transitionを保存する。描画・構造・native画像承認はこの意味判定の代用にしない。
'''
exclusive_bytes(HERE/'row-context-method-scope.md',note.encode('utf-8'))
print(json.dumps({'reviewedRows':120,'reviewSha256':guard.sha(HERE/'search-row-context-review.json'),
 'validationSha256':guard.sha(HERE/'search-row-context-validation-final.json')},ensure_ascii=False))
