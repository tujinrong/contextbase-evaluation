"""Record completed fixed-rubric scores and current verification progress."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json

report=Path(__file__).resolve().parents[1]
evaluation=report/'evaluator-only'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(path,value):
    if path.exists(): raise FileExistsError(str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
previous=load(report/'checkpoints/status-scores-r04.json')
results=previous['formalDocumentResults']
for value in results:
    batch=report/value['batch']
    if sha(batch/'score.json')!=value['scoreSha256'] or sha(Path(value['canonicalPath']))!=value['canonicalSha256']:
        raise ValueError('Previously accepted score binding changed')
batch=evaluation/'batches/source-m-class-r04-r6-retry02'
score,pin=load(batch/'score.json'),load(batch/'canonical-pin.json')
completed=[d for d in score['documents'] if d['complete']]
if len(completed)!=1 or completed[0]['documentId']!=pin['documentId'] or score['total']['percentage'] is not None:
    raise ValueError('A single complete document with unknown whole-set score is required')
if sha(Path(pin['canonicalPath']))!=pin['canonicalSha256']: raise ValueError('Canonical binding changed')
results.append({'batch':batch.relative_to(report).as_posix(),'scoreSha256':sha(batch/'score.json'),
    'pinSha256':sha(batch/'canonical-pin.json'),'referenceMode':pin['referenceMode'],
    'canonicalPath':pin['canonicalPath'],'canonicalSha256':pin['canonicalSha256'],'document':completed[0],
    'criticalRows':score['criticalRows'],'mandatoryMissingRows':score['mandatoryMissingRows'],
    'wholeSetPercentage':None,'finalQualified':False})
created=datetime.now(timezone.utc).isoformat()
run=load(report/'run-manifest.json')
rubric=load(evaluation/'fixed-rubric/seal.json')
for mode,suffix,snapshot in (
    ('training-assisted','assisted','e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'),
    ('source-only','source','2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b')):
    entries=[]
    for value in results:
        if value['referenceMode']!=mode: continue
        batch=report/value['batch']
        entries.append({'documentId':value['document']['documentId'],'batchPath':str(batch.resolve()),
            'normalizationPath':str((batch/'defect-normalization.json').resolve()),
            'canonicalPath':value['canonicalPath'],'canonicalSha256':value['canonicalSha256'],'roundId':batch.name})
    fresh(evaluation/f'selection-{suffix}-partial-r05.json',{'schema':'independent-evaluation-batch-selection/1',
        'projectId':'test-project1','profile':'CSharp_ASPNET','referenceMode':mode,'createdAt':created,
        'rubricSha256':rubric['effectiveItemsSha256'],'sourceSnapshotSha256':snapshot,'documents':entries})
fresh(report/'checkpoints/status-scores-r05.json',{'schema':'reverse-agent-status-checkpoint/1','createdAt':created,
    'formalDocumentResults':results,'wholeSetScore':None,'stopPolicy':'checkpoints/user-stop-at-95-r01.json',
    'rootActualImagesViewed':run['nativeVisualReview']['imagesActuallyReviewed'],
    'fourStateScreenDocumentsReviewed':run['screenStateReviewProgress']['completedScreenDocuments'],
    'requiredScreenDocuments':4,'engineeringValidation':run['engineeringValidation'],
    'inputSpecificationsStarted':False,'holdoutGeneralizationStarted':False,'finalQualified':False})
fresh(report/'checkpoints/run-manifest-before-status-r05.json',run)
run.update(updatedAt=created,formalScore=None,formalDocumentResults=results,
    currentFormalGrading={'status':'ELEVEN_DOCUMENT_SCORES_ACCEPTED_ACROSS_SEPARATE_MODES','formalScore':None,
        'wholeSetComplete':False,'qualified':False,'sourceOnlyCompletedDocuments':5,
        'trainingAssistedCompletedDocuments':6,'trainingAssistedDocumentsAtOrAbove95':4})
(report/'run-manifest.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=report/'README.md'
readme.write_text(readme.read_text(encoding='utf-8')+'\n登録基本の4状態は別AI意味レビュー指摘0件とrootの原寸実見を完了し、状態のみの表示確認を通過した（[記録](visual-review/assisted-registration-basic-r05-states-root-native-r01.json)）。文書全体の図は別gateで未完了。root実見は計103画像、4画面文書中2文書の状態確認を完了している。共通描画器r17は点線・太線・双方向のplain接続ラベルを補強し全404テストを通過した（[検査](engine/all-ai-r17-result.json)）。新しいコード・一覧・操作履歴稿は別レビューと採点を進行中。ソースのみクラス170/186点（91.3978％）を追加した[時点記録](checkpoints/status-scores-r05.json)でも全体得点は空欄、95％停止条件・05:15:58 JSTの上限を維持する。\n',encoding='utf-8')
print(json.dumps({'acceptedDocumentsAcrossSeparateModes':len(results),'assisted95':4,'globalPercentage':None}))
