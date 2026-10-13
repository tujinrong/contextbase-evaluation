"""Correct two evidence bindings on the SAME already frozen Round2 candidate.

Preserve published reports. No previous-round score is used for a new candidate.
The two corrected semantic decisions were reread at their actual new MD ranges.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

P=Path(__file__).resolve().parent
F=P/'frozen'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,j):
    q=P/name
    assert not q.exists(),name
    q.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ev(name,a,b,role):
    lines=(F/name).read_text(encoding='utf-8-sig').splitlines()
    assert 1<=a<=b<=len(lines)
    return {'path':'frozen/'+name,'startLine':a,'endLine':b,'sha256':sha(F/name),'role':role}

prior_search=read(P/'search-evaluation.json')
prior_detail=read(P/'detail-evaluation.json')
assert sha(P/'detail-evaluation.json')=='582a6bf1a53632c3d8ff3058ff9e42c414934320e799fb70953b62a4f98f5658'
assert prior_search['generatedSha256']=='7750a80014ed98cd2408807798c30cead8f395e6e139a8b1cb4a610768f5634a'
manifest=read(P/'frozen-manifest.json')
pins={x['snapshotPath']:x for x in manifest['pins']}
for k,v in pins.items():assert sha(F/k)==v['sha256']
selected={r['evaluationId']:r for r in read(P/'selected-rows.json')}
search=copy.deepcopy(prior_search)
corrected=[]
definitions={
    15:('クリア',[(140,140),(585,623)],
        [('Web/Controllers/StudentsController.cs',21,22),('Infrastructure/WebStudentCoordinator.cs',15,15),('Web/Inputs/StudentSearchInput.cs',7,18)],
        'クリア操作は同じContext IDのApplied/LastResultを消去し版更新、ModelState消去と初期01/02・20・studentNo ascへ戻して未検索を再描画する。学生DELETE/検索はしない。'),
    16:('新規登録',[(141,141),(724,771)],
        [('Views/Students/Search.cshtml',6,6),('Web/Controllers/StudentsController.cs',23,25),('Infrastructure/WebStudentCoordinator.cs',17,17)],
        '新規登録はViewer非表示/Staff・Administrator対象とし、遷移先で作成権限を確認する。検索条件を新規学生へ転記せず、復帰Contextを渡して登録側が候補と新規入力を構成する。'),
}
for index,(label,gen,source,reason) in definitions.items():
    row=search['rows'][index]
    target=selected[row['evaluationId']]
    assert target['index']==index and label in target['originalCells'][4]
    assert row['judgement']=='match' and row['originalPoints']==row['awardedPoints']==1
    reference=[x for x in row['evidence'] if x['role'] in ('current-original','original-evaluation-row')]
    row['evidence']=[ev('generated/spec/detail/student-search.md',a,b,'generated') for a,b in gen]
    row['evidence']+=[ev('sources/'+name,a,b,'source') for name,a,b in source]+reference
    row['reason']=reason
    row['sameCandidateEvidenceCorrection']=True
    row['correctionSemanticReview']='CORRECT_OPERATION_REREAD_AGAINST_SELECTED_ORIGINAL_AND_FROZEN_SOURCE'
    corrected.append(copy.deepcopy(row))
notice={'schema':'same-candidate-evidence-correction/1','classification':'EVALUATOR_ONLY','generatorMayRead':False,
    'correctedAt':datetime.now(timezone.utc).isoformat(),'iteration':'20261013-focus-round-02',
    'reason':'原行15=クリア、16=新規登録に、別操作の意味/生成証拠を割り当てた記録誤りを訂正。',
    'sameCandidateSha256':prior_search['generatedSha256'],'originalCandidateEvaluationReplaced':False,
    'priorSearchReportSha256':sha(P/'search-evaluation.json'),'priorAggregateReportSha256':sha(P/'detail-evaluation.json'),
    'unchangedJudgements':True,'unchangedPoints':True,'unchangedConfirmedPoints':286,
    'formalScore':None,'newCandidateScoredFromOldMatches':False,'correctedRows':corrected}
search['evidenceCorrection']=dict(notice,correctedRows=[r['evaluationId'] for r in corrected])
write('search-evaluation-corrected-01.json',search)
detail=copy.deepcopy(prior_detail)
by_id={r['evaluationId']:r for r in corrected}
for i,row in enumerate(detail['items']):
    if row['evaluationId'] not in by_id:continue
    replacement=copy.deepcopy(by_id[row['evaluationId']])
    replacement['generatedEvidence']=[e for e in replacement['evidence'] if e['role']=='generated']
    replacement['sourceEvidence']=[e for e in replacement['evidence'] if e['role']=='source']
    replacement['referenceEvidence']=[e for e in replacement['evidence'] if e['role'] not in ('source','generated')]
    replacement['criticalFinding']=False
    replacement['evaluator']=search['evaluator']
    detail['items'][i]=replacement
detail['componentReports'][0]={'path':'search-evaluation-corrected-01.json','sha256':sha(P/'search-evaluation-corrected-01.json')}
detail['evidenceCorrection']={k:v for k,v in notice.items() if k!='correctedRows'}
assert detail['summary']==prior_detail['summary']
ref_count=0
for row in detail['items']:
    target=selected[row['evaluationId']]
    assert row['index']==target['index'] and row['originalPoints']==target['originalPoints']
    assert row['originalExpectationSha256']==hashlib.sha256(target['originalCells'][4].encode('utf-8')).hexdigest()
    assert row['awardedPoints']==(target['originalPoints'] if row['judgement']=='match' else None if row['judgement']=='hold' else 0)
    for typ in ('generatedEvidence','sourceEvidence','referenceEvidence'):
        assert row[typ]
        for e in row[typ]:
            k=e['path'][7:]
            assert sha(F/k)==e['sha256']==pins[k]['sha256']
            lines=(F/k).read_text(encoding='utf-8-sig').splitlines()
            assert 1<=e['startLine']<=e['endLine']<=len(lines)
            ref_count+=1
assert len(detail['items'])==281 and sum(r['originalPoints'] for r in detail['items'])==316
write('detail-evaluation-corrected-01.json',detail)
validation=copy.deepcopy(read(P/'detail-validation.json'))
validation['validatedAt']=datetime.now(timezone.utc).isoformat()
validation['detailEvaluationSha256']=sha(P/'detail-evaluation-corrected-01.json')
validation['evidenceReferencesValidated']=ref_count
validation['evidenceCorrectionApplied']=True
validation['priorPublishedReportFilesOverwritten']=False
ROOT=P
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
for item in validation['liveOriginalInputChecks']:
    assert sha(ROOT/item['path'])==item['sha256']
for item in validation['liveLaunchOrCapsulePinChecks']:
    origin=Path(item['path'])
    if not origin.is_absolute():origin=ROOT/origin
    assert sha(origin)==item['sha256']
validation['liveChecksRepeatedForCorrection']=True
write('detail-validation-corrected-01.json',validation)
notice['correctedSearchReport']={'path':'search-evaluation-corrected-01.json','sha256':sha(P/'search-evaluation-corrected-01.json')}
notice['correctedAggregateReport']={'path':'detail-evaluation-corrected-01.json','sha256':sha(P/'detail-evaluation-corrected-01.json')}
notice['correctedValidation']={'path':'detail-validation-corrected-01.json','sha256':sha(P/'detail-validation-corrected-01.json')}
write('row-evidence-correction-01.json',notice)
(P/'row-evidence-correction-01.md').write_text('\n'.join([
    '# Round2 操作2行の根拠割当訂正','','EVALUATOR ONLY。公開済み報告は保存したまま、新しい訂正報告を追加。','',
    '原行15=クリア、16=新規登録に対する理由と生成証拠の割当誤りを、正しい原行と本文/ソースで再確認し訂正した。',
    '両行はmatch・各1点のまま。検索129/147、全体286/316、不足20・矛盾3・保留7点に変更なし。',
    '正式得点・率・95%判定null。安全feedbackとRound3入力に変更なし。','',
    '[訂正合算JSON](detail-evaluation-corrected-01.json)、[訂正検証](detail-validation-corrected-01.json)、[訂正内容](row-evidence-correction-01.json)。',
    f'全281ID/316配点と{ref_count}根拠範囲を再検証。旧採点を新候補へ転用したものではない。','']),encoding='utf-8')
print(json.dumps({'correctedAggregateSha256':sha(P/'detail-evaluation-corrected-01.json'),'evidenceRanges':ref_count,'confirmed':286,'originalMaximum':316,'formalScore':None},ensure_ascii=False))
