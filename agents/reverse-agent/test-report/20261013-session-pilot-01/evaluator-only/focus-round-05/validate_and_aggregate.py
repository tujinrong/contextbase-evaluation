"""Validate independent NEW decisions and their frozen identities; aggregate only.

No semantic outcome is assigned here. The two reviewers supply those decisions.
Earlier reports and matches are neither opened nor used as validation results.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from artifact_store import exclusive_json,exclusive_bytes
import row_context_guard as guard
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
F=OUT/'frozen'
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest=read(OUT/'frozen-manifest.json')
input_manifest=read(OUT/'frozen-input-manifest.json')
pins={p['snapshotPath']:p for p in manifest['pins']}
assert len(pins)==128 and len(input_manifest['pins'])==88
assert manifest['allCandidatesComplete'] is True
assert manifest['inputManifestSha256']==sha(OUT/'frozen-input-manifest.json')
assert manifest['oldMatchScoresReused'] is False and manifest['selectedMaximum']==316
assert manifest['generationBindingScope']=='legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest'
for pin in pins.values():
    assert sha(F/pin['snapshotPath'])==pin['sha256'],pin['snapshotPath']
    assert (F/pin['snapshotPath']).stat().st_size==pin['bytes']

expected=read(OUT/'selected-rows.json')
by_id={r['evaluationId']:r for r in expected}
assert len(expected)==len(by_id)==281 and sum(r['originalPoints'] for r in expected)==316
assert sha(OUT/'selected-rows.json')==manifest['selectedRowsSha256']
search=read(OUT/'search-evaluation.json')
editor=read(OUT/'editor-evaluation.json')
assert search['oldMatchScoresReused'] is False and editor['oldMatchScoresReused'] is False
assert search['generatedVersion']==editor['generatedVersion']=='5.0'
assert search['originalSpecificationVersion']==editor['currentReferenceVersion']=='8.0'
assert search['evaluationVersion']==editor['checklistVersion']=='7.4'
assert search['frozenManifestSha256']==sha(OUT/'frozen-manifest.json')
assert search['inputManifestSha256']==editor['inputManifestSha256']==sha(OUT/'frozen-input-manifest.json')
assert search['selectedRowsFileSha256']==editor['selectedRowsSha256']==sha(OUT/'selected-rows.json')

context_checks=[]
for stem in ('search','editor'):
    review=read(OUT/(stem+'-row-context-review.json'))
    component=read(OUT/(stem+'-evaluation.json'))
    review_by_id={r['evaluationId']:r for r in review['rows']}
    assert len(review_by_id)==len(component['rows'])
    for row in component['rows']:
        attestation=review_by_id[row['evaluationId']]
        assert attestation['originalRowContext']==guard.context(by_id[row['evaluationId']])
        assert attestation['finalReasonSha256']==guard.reason_hash(row)
        assert attestation['finalEvidenceSha256']==guard.evidence_hash(row)
        assert attestation['reasonAndEvidenceRecheckedAgainstOriginalContext'] is True
        assert attestation['adjacentRowMappingUsedAsSemanticProof'] is False
        assert attestation['reviewedGeneratedContext']['meaning']
        assert attestation['reviewedGeneratedContext']['evidence']
        assert all(e in guard.evidence(row) for e in attestation['reviewedGeneratedContext']['evidence'])
    validation_name=stem+'-row-context-validation-final.json' if stem=='search' else 'editor-context-verification.json'
    validation=read(OUT/validation_name)
    assert review['reportSha256']==sha(OUT/(stem+'-evaluation.json'))
    assert validation['reportSha256']==review['reportSha256']
    assert validation['reviewSha256']==sha(OUT/(stem+'-row-context-review.json'))
    assert validation['semanticScoresAssignedByGuard'] is False
    context_checks.append({'document':stem,'reviewSha256':sha(OUT/(stem+'-row-context-review.json')),'validationSha256':sha(OUT/validation_name),'reviewedRows':validation['reviewedRows'],'semanticAcceptanceInferred':False})
assert sum(x['reviewedRows'] for x in context_checks)==281

final_component_manifest=read(OUT/'final-component-manifest-01.json')
for pin in final_component_manifest['pins']:
    assert sha(OUT/pin['livePath'])==sha(OUT/pin['snapshotPath'])==pin['sha256']
preservation_limitations={'allCurrentFinalComponentsExactBytesPreserved':True,
    'finalComponentsByteSnapshotManifestSha256':sha(OUT/'final-component-manifest-01.json'),
    'finalComponentsByteSnapshotFilesVerified':len(final_component_manifest['pins']),
    'existingArtifactsOverwritten':False,'correctionRequiresSeparateVersionAndTransition':True}
synthetic=read(OUT.parent/'artifact-store-synthetic-01/validation.json')
assert synthetic['status']=='PASS' and synthetic['checksPassed']==5
assert synthetic['businessRulesOrExpectedAnswersEmbedded'] is False
persistence_method={'helperSha256':sha(OUT.parent/'artifact_store.py'),
    'syntheticValidationSha256':sha(OUT.parent/'artifact-store-synthetic-01/validation.json'),
    'syntheticChecksPassed':5,'aggregateWritesExclusiveCreate':True,
    'generatorOrProductionChanged':False,'currentArtifactWritesExclusiveCreate':True}

raw_proof=read(OUT/'raw-provenance-final.json')
assert raw_proof['allFourInferencePhasesComplete'] is True
assert len(raw_proof['checks'])==4 and not raw_proof['pending']
assert raw_proof['driverFreshFlagsUsedAsProof'] is False
assert raw_proof['semanticAcceptanceInferred'] is False

generation_checks=[]
for stem, job_id, plan_id in [('student-search','488af9821732c8f6','SM-DET-STUDENT-SEARCH'),
                             ('student-editor','eebb51fa1eb2da8f','SM-DET-STUDENT-EDITOR')]:
    snapshot=read(OUT/(stem+'-snapshot.json'))
    assert len(snapshot['pins'])==20
    assert sha(OUT/(stem+'-snapshot.json'))==manifest['documentSnapshotSha256s'][stem]
    assert snapshot['inputManifestSha256']==sha(OUT/'frozen-input-manifest.json')
    draft=read(F/'provenance/jobs'/job_id/'draft-result.json')
    frozen=F/'generated/spec/detail'/(stem+'.md')
    published=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail'/(stem+'.md')
    assert draft['contentSha256']==snapshot['generatedSha256']==sha(frozen)==sha(published)
    meta=json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',frozen.read_text(encoding='utf-8-sig').splitlines()[0]).group(1))
    assert meta['documentId']==plan_id and meta['version']=='5.0'
    generation_checks.append({'document':stem,'jobId':job_id,'contentSha256':sha(frozen),
        'draftResultSha256':sha(F/'provenance/jobs'/job_id/'draft-result.json'),
        'snapshotSha256':sha(OUT/(stem+'-snapshot.json')),
        'publishedEqualsFrozenEqualsCompletedDraft':True,
        'candidatePinsVerified':20,'version':'5.0'})

plan=read(F/'provenance/plan/plan-verified.json')
actual_prompt_scope=[]
for job_id in ('488af9821732c8f6','eebb51fa1eb2da8f'):
    for phase in ('analysis','draft'):
        prompt_path=F/'provenance/jobs'/job_id/phase/'prompt.txt'
        prompt=prompt_path.read_text(encoding='utf-8-sig')
        assert all(doc['id'] in prompt and doc['path'] in prompt for doc in plan['documents'])
        assert 'previousSourceBackedFeedback' in prompt
        actual_prompt_scope.append({'jobId':job_id,'phase':phase,'promptSha256':sha(prompt_path),
            'wholePlanDocumentsVerified':len(plan['documents']),'safeFeedbackPresent':True})
assert len({entry['threadId'] for entry in raw_proof['checks']})==4
scope=read(F/'provenance/scope.json')
assert scope['runtimeFrozenAtLaunch'] is True and len(scope['runtimeFiles'])==13
for item in scope['runtimeFiles']:
    assert sha(F/'provenance'/item['runtimePath'])==item['sha256']
assert scope['planSha256']==sha(F/'provenance/plan/plan-verified.json')
assert scope['expectedAnswersProvided'] is False and scope['inputMode']=='training-assisted'
assert scope.get('sourceOnlyScoreClaimed') is not True

items=[]
for row in search['rows']:
    normalized=dict(row)
    normalized['generatedEvidence']=[e for e in row['evidence'] if e['role']=='generated']
    normalized['sourceEvidence']=[e for e in row['evidence'] if e['role'] in ('source','independent-source-contradiction-evidence')]
    normalized['referenceEvidence']=[e for e in row['evidence'] if e['role'] not in ('source','independent-source-contradiction-evidence','generated')]
    normalized['criticalFinding']=row['criticalGeneratedContradiction']
    normalized['evaluator']=search['evaluator']
    items.append(normalized)
for row in editor['rows']:
    assert row['originalCriticalClassification']==by_id[row['evaluationId']]['criticalClassification']
    normalized=dict(row)
    normalized['originalExpectationSha256']=hashlib.sha256(by_id[row['evaluationId']]['originalCells'][4].encode('utf-8')).hexdigest()
    normalized['referenceEvidence']=row['referenceEvidence']+row.get('checklistEvidence',[])
    normalized['originalCriticalClassification']=by_id[row['evaluationId']]['criticalClassification']
    normalized['evaluator']=editor['evaluator']
    items.append(normalized)
assert len(items)==281 and len({r['evaluationId'] for r in items})==281
assert {r['evaluationId'] for r in items}==set(by_id)
ref_count=0
for row in items:
    target=by_id[row['evaluationId']]
    assert row['documentId']==target['documentId'] and row['index']==target['index']
    assert row['originalPoints']==target['originalPoints']
    assert row['originalCriticalClassification']==target['criticalClassification']
    assert row['originalExpectationSha256']==hashlib.sha256(target['originalCells'][4].encode('utf-8')).hexdigest()
    assert row['judgement'] in ('match','missing','hold','conflict')
    assert row['awardedPoints']==(target['originalPoints'] if row['judgement']=='match' else None if row['judgement']=='hold' else 0)
    assert row['generatedEvidence'] and row['sourceEvidence'] and row['referenceEvidence'],(row['documentId'],row['index'])
    for group in ('generatedEvidence','sourceEvidence','referenceEvidence'):
        for ref in row[group]:
            assert ref['path'].startswith('frozen/')
            key=ref['path'][7:]
            assert key in pins,key
            assert sha(F/key)==ref['sha256']==pins[key]['sha256']
            line_count=len((F/key).read_text(encoding='utf-8-sig').splitlines())
            assert 1<=ref['startLine']<=ref['endLine']<=line_count
            ref_count+=1

counts=Counter(r['judgement'] for r in items)
earned=sum(r['awardedPoints'] or 0 for r in items)
missing=sum(r['originalPoints'] for r in items if r['judgement']=='missing')
conflict=sum(r['originalPoints'] for r in items if r['judgement']=='conflict')
held=sum(r['originalPoints'] for r in items if r['judgement']=='hold')
assert earned+missing+conflict+held==316
assert sum(r['originalPoints']>0 for r in items)==150 and sum(r['originalPoints']==0 for r in items)==131
critical_count=sum(bool(r['criticalFinding']) for r in items)

# Recheck original inputs now, instead of copying a previous verification status.
capsule=read(F/'provenance/source-capsule-manifest.json')
live_checks=[]
for entry in capsule['files']:
    p=ROOT/'test-project1/srcs/CSharp_ASPNET'/entry['path']
    actual=sha(p); assert actual==entry['sha256']
    live_checks.append({'path':p.relative_to(ROOT).as_posix(),'sha256':actual,'kind':'source'})
for entry in capsule['referenceFiles']:
    p=Path(entry['originalPath']);actual=sha(p);assert actual==entry['sha256']
    live_checks.append({'path':p.relative_to(ROOT).as_posix(),'sha256':actual,'kind':'authorized-reference'})
bridge=read(F/'evaluation/bridge-CSharp_ASPNET.json')
ids={r['documentId'] for r in items}
for document in bridge['documents']:
    if document['documentId'] in ids:
        for key,hkey,kind in [('currentPath','currentSha256','target-original'),
                              ('evaluationChecklist','evaluationSha256','target-checklist')]:
            p=ROOT/document[key];actual=sha(p);assert actual==document[hkey]
            live_checks.append({'path':p.relative_to(ROOT).as_posix(),'sha256':actual,'kind':kind})
assert len(live_checks)==58
live_launch_pin_checks=[]
for pin in manifest['pins']:
    p=Path(pin['originalPath'])
    if not p.is_absolute():p=ROOT/p
    actual=sha(p)
    assert actual==pin['sha256'],('Frozen launch origin drift',p)
    live_launch_pin_checks.append({'path':pin['originalPath'],'kind':pin['kind'],'sha256':actual})
runner_pin=next(pin for pin in manifest['pins'] if pin['kind']=='launch-runner')
assert runner_pin['originalPath']==scope['preservedRunnerPath']
assert runner_pin['sha256']==scope['runnerSha256']==sha(F/'provenance/launch-runner.py')
preserved_runner_check={'path':runner_pin['originalPath'],'sha256':runner_pin['sha256'],
    'matchesLaunchScopeAndFrozenCopy':True,
    'workingDriverExcludedFromInputAndDriftComparison':True}

documents=[]
for doc_id in sorted(ids):
    rows=[r for r in items if r['documentId']==doc_id]
    gen=search['generatedPath'] if doc_id.endswith('001') else 'frozen/generated/spec/detail/student-editor.md'
    documents.append({'documentId':doc_id,'originalRows':len(rows),
        'originalMaximum':sum(r['originalPoints'] for r in rows),
        'positiveRows':sum(r['originalPoints']>0 for r in rows),
        'zeroDiagnosticRows':sum(r['originalPoints']==0 for r in rows),
        'judgementCounts':dict(Counter(r['judgement'] for r in rows)),
        'confirmedAwardedPoints':sum(r['awardedPoints'] or 0 for r in rows),
        'missingPoints':sum(r['originalPoints'] for r in rows if r['judgement']=='missing'),
        'conflictPoints':sum(r['originalPoints'] for r in rows if r['judgement']=='conflict'),
        'unearnedPoints':sum(r['originalPoints'] for r in rows if r['judgement'] in ('missing','conflict')),
        'pendingPoints':sum(r['originalPoints'] for r in rows if r['judgement']=='hold'),
        'criticalGeneratedContradictions':sum(bool(r['criticalFinding']) for r in rows),'completeScore':None,'completePercent':None,
        'generatedPath':gen,'generatedSha256':sha(OUT/gen),
        'originalSpecificationVersion':'8.0','evaluationVersion':'7.4','generatedVersion':'5.0'})
summary={'judgementCounts':dict(counts),'positiveRows':150,'zeroDiagnosticRows':131,
    'confirmedAwardedPoints':earned,'missingPoints':missing,'conflictPoints':conflict,
    'unearnedPoints':missing+conflict,'pendingPoints':held,'pendingRows':sum(r['judgement']=='hold' for r in items),
    'completeScore':None,'completePercent':None,'formal95Result':None,
    'criticalGeneratedContradictions':critical_count,'generatedNonCriticalConflictRows':counts.get('conflict',0),
    'status':'WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION'}
report={'schema':'independent-focused-semantic-evaluation/2','classification':'EVALUATOR_ONLY','generatorMayRead':False,
    'evaluator':'/root/evaluation_inventory','evaluatedAt':datetime.now(timezone.utc).isoformat(),
    'projectId':'test-project1','profile':'CSharp_ASPNET','mode':'training-assisted',
    'iteration':'20261013-focus-round-05','attempt':'focus-round-05',
    'singleIterationScore':True,'unionComponent':False,'oldMatchScoresReused':False,
    'originalRows':281,'originalMaximum':316,'formal95MinimumForSelectedTarget':301,
    'originalPointsChanged':False,'denominatorReduced':False,'diagnosticRowsRetained':True,
    'frozenManifestSha256':sha(OUT/'frozen-manifest.json'),
    'inputManifestSha256':sha(OUT/'frozen-input-manifest.json'),
    'selectedRowsFileSha256':sha(OUT/'selected-rows.json'),
    'sourceCapsuleManifestSha256':manifest['sourceCapsuleManifestSha256'],
    'sourceCount':43,'authorizedReferenceCount':11,'runtimeAtLaunchFiles':13,
    'generationBindingScope':manifest['generationBindingScope'],
    'generationChecks':generation_checks,'actualPromptScopeChecks':actual_prompt_scope,'finalOriginalRowContextReviews':context_checks,
    'rawInferenceProvenanceSha256':sha(OUT/'raw-provenance-final.json'),
    'actualRawInferencePhasesVerified':4,'driverFreshFlagsUsedAsExecutionProof':False,
    'preservedLaunchRunnerCheck':preserved_runner_check,'selectedDocumentIds':sorted(ids),
    'componentReports':[{'path':name,'sha256':sha(OUT/name)} for name in ('search-evaluation.json','editor-evaluation.json')],
    'summary':summary,'documents':documents,'items':items,
    'artifactPreservationLimitations':preservation_limitations,'artifactPersistenceMethod':persistence_method,
    'originalSpecificationQualityCompleteScore':None,
    'limitations':['原品質軸全面採点なし。原仕様/実装または原仕様内の未裁定は全行保留として保持。',
        'source43/reference11のtraining-assisted結果をsource-onlyにしない。',
        'Round5起動runtime13は固定済み。後続の封印/fields-scope修正をこの実行へ遡及適用しない。',
        '原版legacy-v1前後検査をsealed v2証明に読み替えない。',
        '構造/描画/CLI/AIレビューPASSを意味点へコピーしていない。',
        '実アプリ/実DB/ビルド/競合試験なし。他方式/他文書/全1408点を評価していない。']}
exclusive_json(OUT/'detail-evaluation.json',report)
validation={'schema':'independent-focused-evidence-validation/2','classification':'EVALUATOR_ONLY','generatorMayRead':False,
    'validatedAt':datetime.now(timezone.utc).isoformat(),'status':'IDENTITIES_POINTS_EVIDENCE_AND_HASHES_VERIFIED',
    'semanticAcceptanceInferredFromMechanicalValidation':False,
    'detailEvaluationSha256':sha(OUT/'detail-evaluation.json'),
    'frozenManifestSha256':sha(OUT/'frozen-manifest.json'),'selectedRowsSha256':sha(OUT/'selected-rows.json'),
    'validatedRows':281,'originalMaximum':316,'evidenceReferencesValidated':ref_count,
    'fullSnapshotPinsVerified':128,'inputPinsVerified':88,'eachCandidatePinsVerified':20,
    'liveOriginalInputFilesVerified':58,'liveOriginalInputHashDrift':[],
    'liveOriginalInputChecks':live_checks,'liveLaunchOrCapsulePinsVerified':len(live_launch_pin_checks),
    'liveLaunchOrCapsulePinChecks':live_launch_pin_checks,
    'preservedLaunchRunnerCheck':preserved_runner_check,
    'runtimeAtLaunchFilesVerified':13,'laterWorkingRuntimeRequiredToMatch':False,
    'completedDraftPublicationChecks':generation_checks,'actualPromptScopeChecks':actual_prompt_scope,'finalRowContextReviews':context_checks,
    'artifactPreservationLimitations':preservation_limitations,'artifactPersistenceMethod':persistence_method,
    'rawInferenceProvenanceSha256':sha(OUT/'raw-provenance-final.json'),
    'actualRawInferencePhasesVerified':4,'driverFreshFlagsUsedAsExecutionProof':False,
    'confirmedAwardedPoints':earned,'missingPoints':missing,'conflictPoints':conflict,
    'unearnedPoints':missing+conflict,'pendingPoints':held,
    'completeScore':None,'completePercent':None,'formal95Result':None,
    'sourceExecutionTestsPerformed':False,'originalSpecificationQualityCompleteScore':None}
exclusive_json(OUT/'detail-validation.json',validation)
md=['# 学生検索・登録 focus round 05 独立意味評価','','EVALUATOR ONLY — 期待値と行別評価を生成入力へ渡さない。','',
    '対象はCSharp_ASPNET詳細画面2冊のみ。生成5.0、原仕様8.0、採点表7.4。同じsource43/reference11のtraining-assisted。',
    f'**元281行／316点。観測一致{earned}点、不足{missing}点、矛盾{conflict}点、未裁定{held}点。**',
    '正式完了点・率・95%判定はnull。必要整数点301、保留を分母から外さない。',
    f'元分類に基づく重大矛盾{critical_count}件。','',
    '| 対象 | 元行数 | 元満点 | 確認済 | 不足 | 矛盾 | 未裁定 |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for d in documents:
    label='学生検索' if d['documentId'].endswith('001') else '学生登録・編集'
    md.append(f"| {label} | {d['originalRows']} | {d['originalMaximum']} | {d['confirmedAwardedPoints']} | {d['missingPoints']} | {d['conflictPoints']} | {d['pendingPoints']} |")
md+=['',f"新規{counts['match']}一致・{counts['missing']}不足・{counts.get('conflict',0)}矛盾・{counts['hold']}保留。",
    '各担当が新稿全文と元行を再読し、最終理由と現版根拠を元の項目・criterion・操作で照合した。親評価者も全281最終理由と元文脈の一覧を再読した。隣接行・旧点・単語・描画合格を意味の証明にしない。',
    '現在の評価/再読記録をexclusive-createで保存し、固定byte snapshotを残した。訂正はexact旧byte・別version・transitionが必要で既存を上書きしない。',
    '',f'機械検査：281元ID/配点と文脈結合、{ref_count}根拠範囲、128固定pin=入力88+両候補各20、58現行原入力、起動runtime13のSHA一致。',
    '保存runner・config・許可入力・plan/capsuleを照合。後続driver/provider改修を起動版へ遡及しない。',
    '両MDは公開/凍結/完了draft-result/AI raw本文が一致。実4推論のresult/answer/events/checkpoint/handoffが完了し、freshAnalysisフラグを実施証明にしていない。',
    '4つの実promptに固定全計画のID/pathと安全批評が存在する。実scopeはlegacy-v1 raw-indexed unsealedでsealed v2とは称さない。',
    '', '[合算JSON](detail-evaluation.json)、[根拠/ハッシュ検査](detail-validation.json)、[検索](search-evaluation.md)、[登録](editor-evaluation.md)。',
    '実アプリ/実DB/ビルド/競合試験、原品質軸全面、他文書/1408点全体は未実施。','']
exclusive_bytes(OUT/'detail-evaluation.md','\n'.join(md).encode('utf-8'))
print(json.dumps({**summary,'validatedRows':281,'pins':128,'liveOriginalInputFiles':58,
                  'evidenceReferences':ref_count,'reportSha256':sha(OUT/'detail-evaluation.json'),
                  'validationSha256':sha(OUT/'detail-validation.json')},ensure_ascii=False))
