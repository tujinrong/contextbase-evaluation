"""Record the completed index score, without changing any evaluation evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
evaluation = report / 'evaluator-only'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

results = load(report / 'checkpoints/status-scores-r05.json')['formalDocumentResults']
for value in results:
    batch = report / value['batch']
    assert sha(batch / 'score.json') == value['scoreSha256']
    assert sha(Path(value['canonicalPath'])) == value['canonicalSha256']
batch = evaluation / 'batches/assisted-table-index-r04-r6'
score, pin = load(batch / 'score.json'), load(batch / 'canonical-pin.json')
complete = [d for d in score['documents'] if d['complete']]
assert len(complete) == 1 and complete[0]['documentId'] == pin['documentId']
assert score['total']['percentage'] is None
assert sha(Path(pin['canonicalPath'])) == pin['canonicalSha256']
results = [v for v in results if not (v['referenceMode'] == pin['referenceMode'] and v['document']['documentId'] == pin['documentId'])]
results.append({'batch':batch.relative_to(report).as_posix(), 'scoreSha256':sha(batch/'score.json'),
    'pinSha256':sha(batch/'canonical-pin.json'), 'referenceMode':pin['referenceMode'],
    'canonicalPath':pin['canonicalPath'], 'canonicalSha256':pin['canonicalSha256'],
    'document':complete[0], 'criticalRows':score['criticalRows'], 'mandatoryMissingRows':score['mandatoryMissingRows'],
    'wholeSetPercentage':None, 'finalQualified':False})
created = datetime.now(timezone.utc).isoformat()
run = load(report / 'run-manifest.json')
seal = load(evaluation / 'fixed-rubric/seal.json')
for mode, suffix, snapshot in (
    ('training-assisted','assisted','e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'),
    ('source-only','source','2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b')):
    entries = []
    for value in results:
        if value['referenceMode'] != mode:
            continue
        b = report / value['batch']
        entries.append({'documentId':value['document']['documentId'], 'batchPath':str(b.resolve()),
            'normalizationPath':str((b/'defect-normalization.json').resolve()),
            'canonicalPath':value['canonicalPath'], 'canonicalSha256':value['canonicalSha256'], 'roundId':b.name})
    fresh(evaluation/f'selection-{suffix}-partial-r06.json', {'schema':'independent-evaluation-batch-selection/1',
        'projectId':'test-project1', 'profile':'CSharp_ASPNET', 'referenceMode':mode, 'createdAt':created,
        'rubricSha256':seal['effectiveItemsSha256'], 'sourceSnapshotSha256':snapshot, 'documents':entries})
fresh(report/'checkpoints/status-scores-r06.json', {'schema':'reverse-agent-status-checkpoint/1',
    'createdAt':created, 'formalDocumentResults':results, 'wholeSetScore':None,
    'stopPolicy':'checkpoints/user-stop-at-95-r01.json', 'rootActualImagesViewed':107,
    'fourStateScreenDocumentsReviewed':3, 'requiredScreenDocuments':4,
    'engineeringValidation':'engine/all-ai-r18-result.json',
    'protectedInputs':'checkpoints/protected-inputs-06.json',
    'inputSpecificationsStarted':False, 'holdoutGeneralizationStarted':False, 'finalQualified':False})
fresh(report/'checkpoints/run-manifest-before-status-r06.json', run)
assisted = [v for v in results if v['referenceMode'] == 'training-assisted']
run.update(updatedAt=created, formalScore=None, formalDocumentResults=results,
    latestProtectedInputVerification='checkpoints/protected-inputs-06.json',
    currentFormalGrading={'status':'SCORES_ACCEPTED_FOR_EXPLICIT_DOCUMENTS_ONLY', 'formalScore':None,
        'wholeSetComplete':False, 'qualified':False, 'sourceOnlyCompletedDocuments':5,
        'trainingAssistedCompletedDocuments':len(assisted),
        'trainingAssistedDocumentsAtOrAbove95':sum(v['document']['pass95'] for v in assisted)})
(report/'run-manifest.json').write_text(json.dumps(run, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
readme = report / 'README.md'
with readme.open('a', encoding='utf-8') as stream:
    stream.write('\nテーブル仕様書r04は83/85点（97.6471％）で、訓練素材を許可した方式の95％以上は5文書となった。採点済み6文書のうち操作履歴は旧稿の採点であり、新稿の独立採点は進行中。検索詳細と登録基本は図・レイアウト・4状態を合わせた静的表示レビューを通過し、状態確認は4画面文書中3文書、root実見は計107画像。共通描画器r18は408テストを通過し、保護入力218ファイルは15:17:08Z時点で変更なし。全11文書の合格と全体得点は未確定のまま、95％合格時停止・12時間上限を維持する。[時点記録](checkpoints/status-scores-r06.json)。\n')
print(json.dumps({'assistedCompleted':len(assisted), 'assisted95':sum(v['document']['pass95'] for v in assisted),
                  'wholeSetPercentage':None, 'rootActualImagesViewed':107, 'fourStateScreens':3}))
