"""Persist NEW independent semantic decisions for the frozen round-05 search.

Every decision was made after reading the current text and selected original
rows. This builder performs identity, evidence, pin, and arithmetic checks only.
It never reads an earlier semantic-score report or derives credit from keywords.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from artifact_store import exclusive_json,exclusive_bytes
import collections
import datetime as dt
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'frozen'
ROOT = HERE.parents[5]
DOC = 'DET-CSharp_ASPNET-SCR-STU-001'
GEN = 'generated/spec/detail/student-search.md'
ORIG = 'current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
CHECK = 'evaluation/test-project1/spec-eval/checklists/DET-CSharp_ASPNET-SCR-STU-001.md'

# index | NEW judgement | actual new generated ranges | independently read meaning; supplied only after v5.0 completion
DECISIONS = (HERE/'search-decisions.tsv').read_text(encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

cache = {}
def read(path):
    return path.read_text(encoding='utf-8-sig').splitlines()

def ev(path, first, last=None, role='generated'):
    last = first if last is None else last
    if path not in cache:
        cache[path] = read(FROZEN / path)
    assert 1 <= first <= last <= len(cache[path]), (path, first, last)
    return {'path': 'frozen/' + path, 'startLine': first, 'endLine': last,
            'sha256': sha(FROZEN / path), 'role': role}

def spans(value):
    for fragment in value.split(','):
        pair = fragment.split('-')
        yield int(pair[0]), int(pair[-1])

selected_raw = json.loads((HERE/'selected-rows.json').read_text(encoding='utf-8-sig'))
selected = [r for r in selected_raw if r['documentId'] == DOC]
assert len(selected) == 120 and sum(r['originalPoints'] for r in selected) == 147
by_index = {r['index']: r for r in selected}
orig_lines, check_lines = read(FROZEN/ORIG), read(FROZEN/CHECK)
gen_lines = read(FROZEN/GEN)
metadata = json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',gen_lines[0]).group(1))
assert metadata['documentId']=='SM-DET-STUDENT-SEARCH' and metadata['version']=='5.0'
chapters = {'EV-SRC-001':(151,196), 'EV-SRC-002':(197,247),
            'EV-SRC-003':(248,294), 'EV-SRC-004':(295,342),
            'EV-SRC-005':(343,381), 'EV-SRC-006':(382,430)}

def original_evidence(row):
    key = row['originalCells'][2]
    hits = [i+1 for i,line in enumerate(check_lines) if row['evaluationId'] in line]
    assert len(hits)==1
    result = [ev(CHECK,hits[0],role='original-evaluation-row')]
    if key in chapters:
        result.append(ev(ORIG,*chapters[key],role='current-original'))
    elif row['index']==0:
        result.append(ev(ORIG,14,78,role='current-original'))
    elif row['index']==1:
        result.append(ev(ORIG,27,45,role='current-original'))
    elif row['index']==119:
        result.append(ev(ORIG,540,len(orig_lines),role='current-original'))
    else:
        hits = [i+1 for i,line in enumerate(orig_lines) if '| '+key+' |' in line]
        result.append(ev(ORIG,hits[0],role='current-original') if hits else
                      ev(ORIG,118,148,role='current-original'))
    return result

rows=[]
for decision in DECISIONS.strip().splitlines():
    index_text, judgement, span_text, reason = decision.split('|',3)
    index=int(index_text); original=by_index[index]
    generated = [ev(GEN,a,b) for a,b in spans(span_text)]
    cited = {}
    for a,b in spans(span_text):
        for line in gen_lines[a-1:b]:
            for path, range_text in re.findall(r'`((?:sources|reference-designs)/[^`:\n]+):([\d,\-]+)`', line):
                for first,last in spans(range_text):
                    role = 'source' if path.startswith('sources/') else 'authorized-reference-design'
                    cited[(path,first,last)] = ev(path,first,last,role=role)
    if index in (9,99):
        cited[('status-source',111,112)] = ev('sources/Core/SqlServerStudentService.cs',111,112,role='source')
    if index==71:
        cited[('original-operation',446,456)] = ev(ORIG,446,456,role='conflicting-original-operation')
    if index==76:
        for path,a,b in [('sources/Web/Controllers/StudentsController.cs',18,19),
                         ('sources/Core/SqlServerStudentService.cs',107,108),
                         ('sources/Core/SqlServerStudentService.cs',169,170),
                         ('sources/Infrastructure/WebStudentCoordinator.cs',20,20),
                         ('sources/Infrastructure/WebPresentation.cs',23,23)]:
            cited[(path,a,b)] = ev(path,a,b,role='independent-source-contradiction-evidence')
    references=original_evidence(original)
    all_refs=generated+list(cited.values())+references
    points=original['originalPoints']
    rows.append({'index':index,'documentId':DOC,'evaluationId':original['evaluationId'],
        'targetChapter':original['originalCells'][1], 'specificationId':original['originalCells'][2],
        'viewpoint':original['originalCells'][3], 'originalPoints':points,
        'originalExpectationSha256':hashlib.sha256(original['originalCells'][4].encode('utf-8')).hexdigest(),
        'judgement':judgement,'awardedPoints':None if judgement=='hold' else points if judgement=='match' else 0,
        'diagnosticOnly':points==0,'reason':reason,
        'originalCriticalClassification':original['criticalClassification'],
        'criticalGeneratedContradiction':False,
        'criticalReason':'新本文の元行文脈に対する独立再読で重大な事実矛盾は確認しない。',
        'originalQualityJudgement':'hold_reference_adjudication' if judgement=='hold' else 'not_scored_in_this_reproduction_review',
        'originalQualityAwardedPoints':None,
        'referenceReproductionJudgement':judgement,
        'sourceFidelity':'SOURCE_AND_DESIGN_INTENT_SEPARATED_OR_EXPLICITLY_RECORDED_CONFLICT',
        'semanticReview':'INDEPENDENT_NEW_VERSION_5_0_FULL_TEXT_AND_TARGET_ROW_REVIEW',
        'oldMatchReused':False,'evidence':all_refs})

assert len(rows)==120 and [r['index'] for r in rows]==list(range(120))
assert len({r['evaluationId'] for r in rows})==120
counts=collections.Counter(r['judgement'] for r in rows)
earned=sum(r['awardedPoints'] or 0 for r in rows)
missing=sum(r['originalPoints'] for r in rows if r['judgement']=='missing')
conflict=sum(r['originalPoints'] for r in rows if r['judgement']=='conflict')
held=sum(r['originalPoints'] for r in rows if r['judgement']=='hold')
assert earned+missing+conflict+held==147
manifest=json.loads((HERE/'frozen-manifest.json').read_text(encoding='utf-8-sig'))
input_manifest=json.loads((HERE/'frozen-input-manifest.json').read_text(encoding='utf-8-sig'))
snapshot=json.loads((HERE/'student-search-snapshot.json').read_text(encoding='utf-8-sig'))
assert len(manifest['pins'])==128 and len(input_manifest['pins'])==88 and len(snapshot['pins'])==20
for pin in manifest['pins']:
    assert sha(FROZEN/pin['snapshotPath'])==pin['sha256'], pin['snapshotPath']
job=FROZEN/'provenance/jobs/488af9821732c8f6'
draft=json.loads((job/'draft-result.json').read_text(encoding='utf-8-sig'))
assert draft['contentSha256']==sha(FROZEN/GEN)==snapshot['generatedSha256']
published=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail/student-search.md'
assert sha(published)==sha(FROZEN/GEN)
summary={'judgementCounts':dict(counts),'originalRows':120,'positiveRows':71,'zeroDiagnosticRows':49,
         'originalMaximum':147,'confirmedAwardedPoints':earned,'missingPoints':missing,
         'conflictPoints':conflict,'unearnedPoints':missing+conflict,'pendingPoints':held,
         'completeScore':None,'completePercent':None,'passed95':None,
         'criticalGeneratedContradictions':0,'generatedConflictRows':counts.get('conflict',0),
         'status':'WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION'}
result={'schema':'semantic-detail-evaluation/2.0','classification':'EVALUATOR_ONLY','generatorMayRead':False,
        'evaluator':'/root/evaluation_inventory','evaluatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),
        'projectId':'test-project1','profile':'CSharp_ASPNET','mode':'training-assisted',
        'iteration':'20261013-focus-round-05','attempt':'focus-round-05','documentId':DOC,
        'generatedVersion':'5.0','originalSpecificationVersion':'8.0','evaluationVersion':'7.4',
        'generatedPath':'frozen/'+GEN,'generatedSha256':sha(FROZEN/GEN),
        'originalSpecificationSha256':sha(FROZEN/ORIG),'evaluationChecklistSha256':sha(FROZEN/CHECK),
        'frozenManifestSha256':sha(HERE/'frozen-manifest.json'),
        'inputManifestSha256':sha(HERE/'frozen-input-manifest.json'),
        'candidateSnapshotSha256':sha(HERE/'student-search-snapshot.json'),
        'selectedRowsFileSha256':sha(HERE/'selected-rows.json'),
        'sourceCapsuleManifestSha256':manifest['sourceCapsuleManifestSha256'],
        'sourceFiles':43,'authorizedReferenceFiles':11,'runtimeAtLaunchFiles':13,
        'oldMatchScoresReused':False,'originalPointsChanged':False,'denominatorReduced':False,
        'diagnosticRowsRetained':True,'generationBindingScope':manifest['generationBindingScope'],
        'pinVerification':{'unionPinsVerified':128,'inputPins':88,'candidatePins':20,'mismatches':0},
        'provenance':{'job':'488af9821732c8f6','draftResultSha256':sha(job/'draft-result.json'),
                      'analysisVerifiedSha256':sha(job/'analysis-verified.json'),
                      'draftPromptSha256':sha(job/'draft/prompt.txt'),
                      'analysisPromptSha256':sha(job/'analysis/prompt.txt'),
                      'draftContentMatchesPublishedMd':True,
                      'relatedDocumentPlanIndexSupplied':True,
                      'wholePlanAndSafeFeedbackObservedInActualPrompt':True,
                      'runtimeFrozenAtLaunch':True,'laterProductionScopeChangesAttributed':False},
        'scoringPolicy':['全120原行と新本文を再読した新規意味判定。機械は算術/ID/ハッシュ/証拠範囲のみを処理。',
                        '図、参照先、複数章、明示した設計意図の意味を組み合わせる。語句/図存在だけの一致は不可。',
                        '未実装設計意図を正しく分離した記述は再現に含めるが実装/DB成功の証明にはしない。',
                        '1点は属性一式。基表とJOIN NULL、業務長と容量、rawとDTOと正規化を区別。',
                        '各原行のstable ID/項目/criterion/操作文脈と最終理由・根拠を公開前に再読照合。隣接位置を意味の証明にしない。',
                        '原仕様/実装または原仕様内の正解未裁定はhold/null、元147点と全診断行を保持。'],
        'summary':summary,'rows':rows,
        'notPerformed':['実装ビルド/実機/実DB試験','原仕様品質軸の全体採点',
                        'この採点による独立HTML/PDF/Excelレンダリング検査','他の文書/1408点全体の採点']}
exclusive_json(HERE/'search-evaluation.json',result)
md=['# Focus round 05 学生検索 独立意味評価','','EVALUATOR ONLY — generation入力不可。','',
    f"生成5.0 SHA256 `{result['generatedSha256']}`。原仕様8.0／採点表7.4。",
    'source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。',
    f'全120行（有配点71＋診断49）、観測一致{earned}/147点、不足{missing}点、矛盾{conflict}点、保留{held}点。',
    '重大矛盾0件。完了得点・完了率・95%判定はnull。','',
    '全判定と現版根拠は下の行別表を参照。生成・ソース・設計意図を分け、旧判定の転用を行わない。',
    '在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。','',
    '| index | 評価ID | 配点 | 判定 | 加点 | 所見 |','| --- | --- | ---: | --- | ---: | --- |']
for r in rows:
    value='null' if r['awardedPoints'] is None else str(r['awardedPoints'])
    md.append(f"| {r['index']} | {r['evaluationId']} | {r['originalPoints']} | {r['judgement']} | {value} | {r['reason']} |")
md+=['','各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。',
     'このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。','']
exclusive_bytes(HERE/'search-evaluation.md','\n'.join(md).encode('utf-8'))
print(json.dumps(summary,ensure_ascii=False))
