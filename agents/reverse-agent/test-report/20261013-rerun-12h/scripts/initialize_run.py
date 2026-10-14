"""Freeze run metadata and filename contracts; never assemble specification prose."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REPORT = REPO / 'agents/reverse-agent/test-report/20261013-rerun-12h'
SUBJECT = REPO / 'test-project1/srcs/CSharp_ASPNET'
STARTED = '2026-10-13T08:15:58Z'
DEADLINE = '2026-10-13T20:15:58Z'

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    now = datetime.now(timezone.utc).isoformat()
    source_entries = {
        '01_学生検索画面.md': ['Views/Students/Search.cshtml', 'Web/Controllers/StudentsController.cs', 'Web/Inputs/StudentSearchInput.cs'],
        '02_学生登録画面.md': ['Views/Students/Edit.cshtml', 'Web/Controllers/StudentsController.cs', 'Web/Inputs/StudentSaveInput.cs', 'Web/Inputs/StudentDeleteInput.cs'],
        '03_テーブル仕様書.md': ['database/001_schema.sql', 'Core/Contracts.cs'],
        '04_コード設計書.md': ['database/002_seed.sql', 'Core/MasterMaintenanceService.cs'],
    }
    rubric = json.loads((SUBJECT / 'spec-eval/evaluation-items.json').read_text(encoding='utf-8'))
    definitions = []
    for doc in rubric['documents']:
        relative = Path(doc['sourcePath']).relative_to('spec').as_posix()
        filename = Path(relative).name
        if '/テーブル/' in relative:
            kind, entries = 'table-definition', ['database/001_schema.sql']
        elif relative.startswith('詳細仕様書/'):
            kind, entries = 'detailed-specification', source_entries[filename]
        elif filename == '03_テーブル仕様書.md':
            kind, entries = 'table-index', source_entries[filename]
        elif filename == '04_コード設計書.md':
            kind, entries = 'code-design', source_entries[filename]
        else:
            kind, entries = 'basic-design', source_entries[filename]
        assert all((SUBJECT / entry).is_file() for entry in entries)
        definitions.append({'id': doc['documentId'], 'kind': kind, 'path': relative, 'sourcePaths': entries})
    contract = {'schema': 'reverse-ai-document-contract/1', 'projectId': 'test-project1', 'documents': definitions}
    save(REPORT / 'document-contract.json', contract)
    save(REPORT / 'search-document-contract.json', {**contract, 'documents': [doc for doc in definitions if Path(doc['path']).name == '01_学生検索画面.md']})
    save(REPORT / 'register-document-contract.json', {**contract, 'documents': [doc for doc in definitions if Path(doc['path']).name == '02_学生登録画面.md']})
    save(REPORT / 'data-document-contract.json', {**contract, 'documents': [doc for doc in definitions if Path(doc['path']).name not in {'01_学生検索画面.md', '02_学生登録画面.md'}]})
    protected = []
    for path in sorted(SUBJECT.rglob('*')):
        if path.is_file() and not any(part.casefold() in {'bin', 'obj', '.git', '.vs'} for part in path.relative_to(SUBJECT).parts):
            protected.append({'path': path.relative_to(REPO).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)})
    save(REPORT / 'protected-inputs-before.json', {'schema': 'protected-input-files/1', 'observedAt': now, 'files': protected})
    save(REPORT / 'evaluator-only/reference-issue-decisions.json', {
        'schema': 'reference-issue-decisions/1', 'observedAt': now,
        'authorization': 'Human reply to request_user_input_async: この解釈で確定する',
        'originalSpecificationsModified': False,
        'decisions': [
            {'id': 'REF-001', 'decision': '検索のクラス候補取得では学生・参考人数を集計しない。イベントERはこの処理範囲で評価する。', 'status': 'USER_CONFIRMED'},
            {'id': 'REF-002', 'decision': '検索の生年月日は和暦表示のみ。和暦4入力・birth_date保存は登録画面の説明。', 'status': 'USER_CONFIRMED'}
        ]})
    save(REPORT / 'run-manifest.json', {
        'schema': 'reverse-agent-rerun/1', 'runId': '20261013-rerun-12h', 'projectId': contract['projectId'], 'profile': 'CSharp_ASPNET',
        'startedAt': STARTED, 'deadline': DEADLINE, 'maximumHours': 12,
        'source': str(SUBJECT), 'baselineMode': 'source-only',
        'targetDocuments': len(definitions), 'filenamePolicy': 'same relative paths and filenames as original specification documents',
        'generationOutput': 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/spec',
        'evaluationDirectory': 'agents/reverse-agent/test-report/20261013-rerun-12h/evaluator-only',
        'gates': {'overallPercent': 95, 'eachDocumentPercent': 95, 'majorCategoryPercent': 95,
                  'criticalViolations': 0, 'mandatoryOmissions': 0, 'unreviewedApplicableRows': 0,
                  'visualReviewRequiredForScreens': True},
        'inputProgramExecutionAuthorized': False, 'modelWeightTrainingPerformed': False,
        'status': 'STARTED', 'formalScore': None})
    print(json.dumps({'status': 'INITIALIZED', 'documents': len(definitions), 'protectedFiles': len(protected), 'deadline': DEADLINE}, ensure_ascii=False))

if __name__ == '__main__':
    main()
