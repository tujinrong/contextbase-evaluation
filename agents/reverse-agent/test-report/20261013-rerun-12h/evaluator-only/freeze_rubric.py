"""Freeze the existing rubric and human-approved interpretations, without grading."""
from pathlib import Path
import hashlib
import json
import shutil
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
ORIGINAL = REPO / 'test-project1/srcs/CSharp_ASPNET/spec-eval'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write('\n')

def main():
    decisions = json.loads((HERE / 'reference-issue-decisions.json').read_text(encoding='utf-8-sig'))
    assert {x['id'] for x in decisions['decisions'] if x['status'] == 'USER_CONFIRMED'} == {'REF-001', 'REF-002'}
    fixed = HERE / 'fixed-rubric'
    fixed.mkdir(exist_ok=False)
    originals = []
    for path in sorted(ORIGINAL.rglob('*')):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError('Linked rubric input')
        rel = path.relative_to(ORIGINAL)
        target = fixed / 'original' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        originals.append({'path': rel.as_posix(), 'sha256': digest(path)})
    items = json.loads((fixed / 'original/evaluation-items.json').read_text(encoding='utf-8-sig'))
    changed = []
    for document in items['documents']:
        for row in document['rows']:
            row['effectiveExpected'] = row['expected']
            row['effectiveExpectedNotes'] = []
            row['judgement'] = '未評価'
            for field in ('actualDeduction', 'defectId', 'evaluatedArtifactEvidence', 'evaluator', 'evaluatedAt'):
                row[field] = None
            issue = row.get('referenceIssueId')
            if issue == 'REF-001':
                row['effectiveExpected'] = '\n'.join(line for line in row['expected'].splitlines() if '参考人数' not in line and 'occupancy' not in line)
                row['effectiveExpectedNotes'] = ['REF-001 USER_CONFIRMED: 検索のクラス候補取得では学生・参考人数を集計しない。ERは当該イベントの処理範囲で評価する。']
                row['deductionCondition'] = '承認REF-001を適用した当該イベントの関係の誤り／必要図の欠落：−3。原図の学生・人数関係を必須にしない。'
            elif issue == 'REF-002':
                row['effectiveExpected'] = row['expected'].replace('生年月日は和暦4入力、変換後のみbirth_dateとして保存する。', '検索の生年月日は和暦表示のみで編集・保存しない。和暦4入力・birth_date保存の説明は登録画面へ適用する。')
                row['effectiveExpectedNotes'] = ['REF-002 USER_CONFIRMED: 検索生年月日は和暦表示のみ。和暦4入力・保存は登録画面の説明。']
                row['deductionCondition'] = '承認REF-002による適用範囲を含め、意味の矛盾／全欠落：−3。意味は正しいが条件・対象等不足：−2。'
            if issue in ('REF-001', 'REF-002'):
                changed.append({'evaluationId': row['evaluationId'], 'issueId': issue, 'fromJudgement': '保留', 'toJudgement': '未評価'})
    rows = [r for d in items['documents'] for r in d['rows']]
    assert len(rows) == 7079
    assert sum(r['maximumPenalty'] for r in rows) == 8682
    assert len(changed) == 3
    items['schema'] = 'independent-semantic-rubric/1'
    items['interpretationDecisions'] = decisions
    items['versionComparisonPolicy'] = '原版8.0の文字再現を要求しない。今回の版・原本対応・識別を確認する。'
    save(fixed / 'effective-items.json', items)
    seal = {'schema': 'independent-rubric-freeze/1', 'frozenAt': datetime.now(timezone.utc).isoformat(),
        'originalFiles': originals, 'effectiveItemsSha256': digest(fixed / 'effective-items.json'),
        'decisionSha256': digest(HERE / 'reference-issue-decisions.json'), 'resolvedRows': changed,
        'evaluationRows': len(rows), 'maximumPoints': 8682, 'originalSpecificationsModified': False,
        'score': None, 'status': 'UNASSESSED'}
    save(fixed / 'seal.json', seal)
    print(json.dumps({'rows': len(rows), 'maximumPoints': 8682, 'resetHolds': len(changed), 'status': 'UNASSESSED'}))

if __name__ == '__main__':
    main()
