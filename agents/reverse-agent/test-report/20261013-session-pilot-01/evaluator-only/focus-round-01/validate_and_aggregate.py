"""Independent pin/row/evidence validation and arithmetic for the two NEW reviews.

Semantic decisions are inputs. This script never assigns semantic matches.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json

OUT=Path(__file__).resolve().parent
F=OUT/'frozen'
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=read(OUT/'frozen-manifest.json')
pins={p['snapshotPath']:p for p in manifest['pins']}
expected=read(OUT/'selected-rows.json')
by_id={r['evaluationId']:r for r in expected}
assert len(expected)==281 and len(by_id)==281 and sum(r['originalPoints'] for r in expected)==316
assert manifest['selectedMaximum']==316 and manifest['oldMatchScoresReused'] is False
for pin in pins.values():
    assert sha(F/pin['snapshotPath'])==pin['sha256'],pin['snapshotPath']
search=read(OUT/'search-evaluation.json')
editor=read(OUT/'editor-evaluation.json')
assert search['oldMatchScoresReused'] is False and editor['oldMatchScoresReused'] is False
assert search['frozenManifestSha256']==editor['manifestSha256']==sha(OUT/'frozen-manifest.json')
assert search['selectedRowsFileSha256']==editor['selectedRowsSha256']==sha(OUT/'selected-rows.json')
assert sha(OUT/'editor-evaluation.json')=='a6afda6e475e7b3bed41ce1978a9ee9989188cdee93e44fa1598482ea966dc84'

items=[]
for row in search['rows']:
    normalized=dict(row)
    normalized['generatedEvidence']=[e for e in row['evidence'] if e['role']=='generated']
    normalized['sourceEvidence']=[e for e in row['evidence'] if e['role']=='source']
    normalized['referenceEvidence']=[e for e in row['evidence'] if e['role'] not in ('source','generated')]
    normalized['criticalFinding']=row['criticalGeneratedContradiction']
    normalized['evaluator']=search['evaluator']
    items.append(normalized)
for row in editor['rows']:
    normalized=dict(row)
    normalized['originalExpectationSha256']=row['expectationSha256']
    normalized['evaluator']=editor['evaluator']
    items.append(normalized)
assert len(items)==281 and len({r['evaluationId'] for r in items})==281
assert {r['evaluationId'] for r in items}==set(by_id)
ref_count=0
for row in items:
    target=by_id[row['evaluationId']]
    assert row['documentId']==target['documentId'] and row['index']==target['index']
    assert row['originalPoints']==target['originalPoints']
    assert row['originalExpectationSha256']==hashlib.sha256(target['originalCells'][4].encode('utf-8')).hexdigest()
    assert row['awardedPoints']==(target['originalPoints'] if row['judgement']=='match' else None if row['judgement']=='hold' else 0)
    if row['judgement']=='match':
        assert row['generatedEvidence'] and row['sourceEvidence'] and row['referenceEvidence'],row['index']
    for group in ('generatedEvidence','sourceEvidence','referenceEvidence'):
        for ref in row[group]:
            assert ref['path'].startswith('frozen/')
            key=ref['path'][7:]
            assert key in pins,key
            assert sha(F/key)==ref['sha256']==pins[key]['sha256']
            count=len((F/key).read_text(encoding='utf-8-sig').splitlines())
            assert 1<=ref['startLine']<=ref['endLine']<=count
            ref_count+=1
counts=Counter(r['judgement'] for r in items)
earned=sum(r['awardedPoints'] or 0 for r in items)
missing=sum(r['originalPoints'] for r in items if r['judgement']=='missing')
pending=sum(r['originalPoints'] for r in items if r['judgement']=='hold')
assert earned+missing+pending==316
assert (earned,missing,pending)==(274,35,7)
assert counts==dict(match=238,missing=38,hold=5)
assert not any(r['criticalFinding'] for r in items)

# Fresh live-input checks: no historical verification result is reused.
capsule=read(F/'provenance/source-capsule-manifest.json')
source_root=ROOT/'test-project1/srcs/CSharp_ASPNET'
live_checks=[]
for entry in capsule['files']:
    p=source_root/entry['path']
    actual=sha(p)
    assert actual==entry['sha256'],p
    live_checks.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=actual,kind='source'))
for entry in capsule['referenceFiles']:
    p=Path(entry['originalPath'])
    actual=sha(p)
    assert actual==entry['sha256'],p
    live_checks.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=actual,kind='authorized-reference'))
bridge=read(F/'evaluation/bridge-CSharp_ASPNET.json')
ids={r['documentId'] for r in items}
for document in bridge['documents']:
    if document['documentId'] in ids:
        for path_key,hash_key,kind in [('currentPath','currentSha256','target-original'),('evaluationChecklist','evaluationSha256','target-checklist')]:
            p=ROOT/document[path_key]
            actual=sha(p)
            assert actual==document[hash_key],p
            live_checks.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=actual,kind=kind))
assert len(live_checks)==58
documents=[]
for document_id in sorted(ids):
    rs=[r for r in items if r['documentId']==document_id]
    generated=search['generatedPath'] if document_id.endswith('001') else editor['generatedDocument']['path']
    documents.append(dict(documentId=document_id,originalRows=len(rs),originalMaximum=sum(r['originalPoints'] for r in rs),
      positiveRows=sum(r['originalPoints']>0 for r in rs),zeroDiagnosticRows=sum(r['originalPoints']==0 for r in rs),
      judgementCounts=dict(Counter(r['judgement'] for r in rs)),confirmedAwardedPoints=sum(r['awardedPoints'] or 0 for r in rs),
      missingPoints=sum(r['originalPoints'] for r in rs if r['judgement']=='missing'),pendingPoints=sum(r['originalPoints'] for r in rs if r['judgement']=='hold'),
      completeScore=None,completePercent=None,generatedPath=generated,generatedSha256=sha(OUT/generated),
      originalSpecificationVersion='8.0',evaluationVersion='7.4',generatedVersion='1.0',criticalGeneratedContradictions=0))
summary=dict(judgementCounts=dict(counts),positiveRows=150,zeroDiagnosticRows=131,
 confirmedAwardedPoints=earned,missingPoints=missing,pendingPoints=pending,
 completeScore=None,completePercent=None,formal95Result=None,criticalGeneratedContradictions=0,
 status='WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION')
report=dict(schema='independent-focused-semantic-evaluation/1',classification='EVALUATOR_ONLY',generatorMayRead=False,
 evaluator='/root/evaluation_inventory',evaluatedAt=datetime.now(timezone.utc).isoformat(),
 projectId='test-project1',profile='CSharp_ASPNET',mode='training-assisted',iteration='20261013-focus-round-01',
 singleIterationScore=True,unionComponent=False,oldMatchScoresReused=False,originalRows=281,originalMaximum=316,
 originalPointsChanged=False,denominatorReduced=False,diagnosticRowsRetained=True,
 formal95MinimumForSelectedTarget=301,frozenManifestSha256=sha(OUT/'frozen-manifest.json'),
 selectedRowsFileSha256=sha(OUT/'selected-rows.json'),sourceCapsuleManifestSha256=manifest['sourceCapsuleManifestSha256'],
 generationBindingScope=manifest['generationBindingScope'],generationReviewAtFreeze='AI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWED',
 sourceCount=43,authorizedReferenceCount=11,selectedDocumentIds=sorted(ids),
 componentReports=[dict(path=name,sha256=sha(OUT/name)) for name in ['search-evaluation.json','editor-evaluation.json']],
 summary=summary,documents=documents,items=items,
 originalSpecificationQualityCompleteScore=None,
 limitations=['原仕様品質の全体採点は未実施。未裁定の原基準/実装差はこの再現軸の保留と別に記録。',
  'source 43/reference 11の訓練補助付き試行でありsource-onlyへ読み替えない。',
  '生成のlegacy-v1 before/after manifest検査を封印v2へ読み替えない。',
  '描画/構造/CLIレビュー/AIレビューの結果はこの意味点へコピーしていない。',
  '実DB/アプリ/同時保存/実データ検査なし。他方式/他文書/全1408点の採点なし。'])
(OUT/'detail-evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
validation=dict(schema='independent-focused-evidence-validation/1',classification='EVALUATOR_ONLY',generatorMayRead=False,
 validatedAt=datetime.now(timezone.utc).isoformat(),status='IDENTITIES_POINTS_EVIDENCE_AND_HASHES_VERIFIED',
 semanticAcceptanceInferredFromMechanicalValidation=False,detailEvaluationSha256=sha(OUT/'detail-evaluation.json'),
 frozenManifestSha256=sha(OUT/'frozen-manifest.json'),selectedRowsSha256=sha(OUT/'selected-rows.json'),
 validatedRows=281,originalMaximum=316,evidenceReferencesValidated=ref_count,fullSnapshotPinsVerified=len(pins),
 liveOriginalInputFilesVerified=len(live_checks),liveOriginalInputHashDrift=[],liveOriginalInputChecks=live_checks,
 confirmedAwardedPoints=earned,missingPoints=missing,pendingPoints=pending,
 completeScore=None,completePercent=None,formal95Result=None,originalSpecificationQualityCompleteScore=None,
 sourceExecutionTestsPerformed=False)
(OUT/'detail-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# 学生検索・登録 focus round 01 独立意味評価','','EVALUATOR ONLY — 原期待値・採点証拠は生成入力に渡さない。','',
 '対象はCSharp_ASPNET詳細画面2冊だけ。生成1.0、原仕様8.0、採点表7.4。source43/利用者承認reference11のtraining-assisted同一snapshot。',
 '**全281行／316点を保持し、観測一致274点、不足35点、未裁定7点。正式完了得点・率・95%判定はnull。**',
 '95%の必要整数点は301。元分母や保留を減らして達成判定を作らない。重要な生成矛盾は今回確定0件。','',
 '| 対象 | 原行数 | 原満点 | 確認済 | 不足 | 未裁定 |','| --- | ---: | ---: | ---: | ---: | ---: |']
for d in documents:
    label='学生検索' if d['documentId'].endswith('001') else '学生登録・編集'
    md.append(f"| {label} | {d['originalRows']} | {d['originalMaximum']} | {d['confirmedAwardedPoints']} | {d['missingPoints']} | {d['pendingPoints']} |")
md+=['','全行新規再読。238一致・38不足・5保留、正配点150行と0点診断131行を維持。旧matchやrender passをコピーしていない。',
 '意味判定担当は検索と編集で独立。図/参照先/複数章/明示された設計意図を組み合わせ、見出し・図・語句だけで加点していない。',
 '検索の静的HTMLはソースUIとして成立するが参考設計の全操作配置を再現していない。設計意図の話題名だけでは操作/表示の属性束を補えない。',
 '型/NULL/SQLバインドは改善。名称の業務長、表示日付意図、表示範囲、参照責務/実装試験計画等には不足が残る。',
 '検索配列正規化・候補ER/人数集計・削除失敗入力保証は正解未裁定。原品質軸全面採点は未実施。',
 '新編集本文は郵便番号の設計表示と現行7桁保存を区別して再現したため、その旧保留を新再現点へ自動転用しなかった。',
 '',f"機械検査：281原ID/配点・{ref_count}証拠参照のSHA/行境界・95snapshot pin・58現行元入力が一致。",
 '生成時のlegacy-v1 manifest前後一致を封印v2へ読み替えない。関連文書plan index未供給の生成記録があるため後続プロンプト改修を遡及評価しない。',
 '', '[合算JSON](detail-evaluation.json)、[証拠/ハッシュ検査](detail-validation.json)、[検索行別判定](search-evaluation.md)、[登録行別判定](editor-evaluation.md)。',
 '実DB/実アプリ/ビルド/競合試験、原品質軸の全面採点、他文書/全1408点の採点は未実施。','']
(OUT/'detail-evaluation.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({**summary,'validatedRows':281,'pins':len(pins),'liveOriginalInputFiles':len(live_checks),'evidenceReferences':ref_count,'reportSha256':sha(OUT/'detail-evaluation.json')},ensure_ascii=False))
