"""Independent identity/weight/evidence/hash validation, not a semantic scorer."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json

O=Path(__file__).resolve().parent
F=O/'frozen'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((O/'detail-evaluation.json').read_text(encoding='utf-8'))
manifest=json.loads((O/'frozen-manifest.json').read_text(encoding='utf-8'))
bridge=json.loads((F/'evaluation/bridge-CSharp_ASPNET.json').read_text(encoding='utf-8-sig'))
ids={'DET-CSharp_ASPNET-SCR-STU-001','DET-CSharp_ASPNET-SCR-STU-002'}
expected={x['evaluationId']:x for x in bridge['items'] if x['documentId'] in ids}
items=report['items']; pins={x['snapshotPath']:x for x in manifest['pins']}
assert len(items)==281 and len({x['evaluationId'] for x in items})==281
assert set(expected)=={x['evaluationId'] for x in items}
assert report['originalMaximum']==316 and report['denominatorReduced'] is False
assert sha(O/'detail-evaluation.json')=='a7cf7dd7b638a27f5bc91edd58ed986bc4b1fdee7fc4bfe373a759cb32d3019b'
assert sha(O/'frozen-manifest.json')==report['frozenManifestSha256']
assert sha(O/'selected-rows.json')==report['selectedRowsFileSha256']
assert sha(F/'evaluation/bridge-CSharp_ASPNET.json')==report['bridgeSha256']
evidence_count=0
for row in items:
    original=expected[row['evaluationId']]
    assert row['documentId']==original['documentId']
    assert row['index']==original['index']
    assert row['originalPoints']==original['originalPoints']
    assert row['originalExpectationSha256']==hashlib.sha256(original['originalCells'][4].encode('utf-8')).hexdigest()
    assert row['awardedPoints']==(original['originalPoints'] if row['judgement']=='match' else None if row['judgement'] in ['hold','unobservable'] else 0)
    if row['judgement']=='match':
        assert row['generatedEvidence'] and row['sourceEvidence'] and row['referenceEvidence']
    for category in ['generatedEvidence','sourceEvidence','referenceEvidence']:
        for ref in row[category]:
            assert ref['path'].startswith('frozen/')
            key=ref['path'][len('frozen/'):]
            assert key in pins
            assert ref['sha256']==pins[key]['sha256']==sha(F/key)
            lines=(F/key).read_text(encoding='utf-8-sig').splitlines()
            assert 1<=ref['startLine']<=ref['endLine']<=len(lines)
            evidence_count+=1
for pin in manifest['pins']:
    assert sha(F/pin['snapshotPath'])==pin['sha256']
for pin in report['pins']:
    assert pin['verifiedSha256']==pin['sha256']==sha(F/pin['snapshotPath'])
repository=O
while not (repository/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert repository.parent!=repository
    repository=repository.parent
capsule=json.loads((F/'provenance/assisted-capsule-manifest.json').read_text(encoding='utf-8'))
live_source_root=repository/'test-project1/srcs/CSharp_ASPNET'
live_inputs_verified=0
for entry in capsule['files']:
    assert sha(live_source_root/entry['path'])==entry['sha256']
    live_inputs_verified+=1
for entry in capsule['referenceFiles']:
    assert sha(Path(entry['originalPath']))==entry['sha256']
    live_inputs_verified+=1
for doc in bridge['documents']:
    if doc['documentId'] in ids:
        assert sha(repository/doc['currentPath'])==doc['currentSha256']
        assert sha(repository/doc['evaluationChecklist'])==doc['evaluationSha256']
        live_inputs_verified+=2
total_points=sum(x['originalPoints'] for x in items)
confirmed=sum(x['awardedPoints'] or 0 for x in items)
pending_points=sum(x['originalPoints'] for x in items if x['awardedPoints'] is None)
missing_points=sum(x['originalPoints'] for x in items if x['judgement']=='missing')
assert total_points==316 and confirmed==269 and pending_points==8 and missing_points==39
assert confirmed+missing_points+pending_points==total_points
assert Counter(x['judgement'] for x in items)=={'match':226,'missing':47,'hold':8}
assert report['summary']['completeScore'] is None and report['summary']['completePercent'] is None
assert not any(x['criticalFinding'] for x in items)
result=dict(schema='independent-detail-artifact-validation/1',classification='EVALUATOR_ONLY',generatorMayRead=False,evaluator='/root/evaluation_inventory',validatedAt=datetime.now(timezone.utc).isoformat(),status='IDENTITIES_POINTS_EVIDENCE_AND_HASHES_VERIFIED',semanticAcceptanceInferredFromMechanicalValidation=False,detailEvaluation='detail-evaluation.json',detailEvaluationSha256=sha(O/'detail-evaluation.json'),target=dict(documents=2,rows=281,originalMaximum=316,minimumFor95=301,mode='training-assisted',component='20261013-pilot-v2-r2'),judgementCounts=dict(Counter(x['judgement'] for x in items)),confirmedAwardedPoints=confirmed,missingPoints=missing_points,pendingPoints=pending_points,completedScore=None,completedPercentage=None,criticalGeneratedContradictions=0,evidenceReferencesValidated=evidence_count,relevantPinsVerified=len(report['pins']),fullSnapshotPinsVerified=len(manifest['pins']),originalSpecificationQualityScore=None,sourceExecutionTestsPerformed=False)
result['liveOriginalInputFilesVerified']=live_inputs_verified
result['liveOriginalInputHashDrift']=[]
(O/'detail-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# EVALUATOR_ONLY — 学生検索・学生登録の意味採点baseline','','2026-10-13 JST。対象は `CSharp_ASPNET` の詳細画面2冊だけ。入力はソース43ファイルと利用者が許可した参考MD11冊を持つ `training-assisted` snapshot、出力は `20261013-pilot-v2-r2` の生成MD版1.0。原仕様版8.0、該当採点表版7.4、行と配点を固定して新規評価した。','','**281行／316点を全保持。確認済加点269点、欠落39点、保留8点。完了得点・正式率は未確定。95%の最小整数点は301点で、保留を含む本結果は達成判定へ使わない。**','','| 対象詳細書 | 審査行 | 原満点 | 確認済加点 | 欠落点 | 保留点 |','| --- | --- | --- | --- | --- | --- |']
for doc in report['documents']:
    label='学生検索' if doc['documentId'].endswith('001') else '学生登録・編集'
    lines.append(f"| {label} | {doc['originalRows']} | {doc['originalMaximum']} | {doc['confirmedAwardedPoints']} | {doc['missingPoints']} | {doc['pendingPoints']} |")
lines+=['','[行別意味採点](detail-evaluation.json)と[独立のID・配点・証拠検査](detail-validation.json)を分離した。226一致行、47欠落行、8保留行で、0点診断131行も保持する。各行の生成MD・ソース・原参照の番号付き証拠を保存した。今回、本文採点担当と検査担当を分け、過去の合格を新結果として流用していない。','','不足は、項目の実DB型・NULL属性と業務長の一式、設計上の表示契約、試験観点と正本責務の説明である。正しい現行差の説明を生成の矛盾へ置換していない。保留は配列正規化・原仕様内の候補ER/人数集計不整合・表示契約・削除失敗時の原入力扱いに関する未裁定を含む。重要制約の生成矛盾は今回確定0だが、保留が残り合格を意味しない。','','機械検査は281 IDの一意性・原IDの完全一致・元配点・全証拠のSHA/行範囲・対象62 pinと全83 snapshot pinの不変を確認した。構造検証や描画検証の成功は意味加点に転記していない。原仕様品質軸の完了得点は本成果で採点していない。実アプリ・実SQL Server・同時保存試験は未実施。','','物理テーブル7冊の過去baselineは同フォルダーに保存済だが、今回の画面2冊の分母へ加えていない。方式全体1408点の率や95%達成をこの部分集合から宣言しない。次の原稿は新しい出力SHAを凍結して再採点し、現baselineのpassを引き継がない。']
(O/'screen-baseline-summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
