"""Read-only transport and approval-scope checks; no AI or source execution."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from contextbase.ai import capsule, prompts, workflow


ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent
JOB = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-01'
SNAPSHOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
CODE = ROOT / 'agents/reverse-agent/src/contextbase/ai'
SOURCE = SNAPSHOT / 'sources'
MDROOT = ROOT / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01/spec/detail'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def write(name, value):
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    paths = [ROOT / item for item in [
        'AGENTS.md', 'docs/仕様書作成ルール.md', 'docs/MD構造・Excel変換規約.md',
        'agents/README.md', 'agents/reverse-agent/AGENTS.md',
        'agents/reverse-agent/src/contextbase/tests/test_ai_plan_context.py',
    ]]
    paths += [CODE / item for item in ['prompts.py', 'workflow.py', 'iteration.py', 'rendering.py', 'schemas.py', '__main__.py']]
    paths += [SOURCE / item for item in ['Views/Shared/_Layout.cshtml', 'Views/Students/Edit.cshtml',
                                        'Views/Students/Search.cshtml', 'wwwroot/css/site.css']]
    jobs = [('488af9821732c8f6', 'student-search'), ('eebb51fa1eb2da8f', 'student-editor')]
    plan = Path(load(JOB / jobs[1][0] / 'analysis-handoff.json')['planFile'])
    paths += [plan, plan.parent / 'plan-handoff.json', SNAPSHOT / 'manifest.json']
    for directory, stem in jobs:
        paths += [MDROOT / (stem + '.md')]
        paths += [JOB / directory / name for name in ['analysis-handoff.json', 'analysis-verified.json', 'draft-result.json']]
        for phase in ['analysis', 'draft', 'independent-review']:
            paths += [JOB / directory / phase / name for name in ['prompt.txt', 'result.json']]
        paths += [JOB / directory / 'independent-review' / name for name in ['review-verified.json', 'review-handoff.json', 'events.jsonl']]
        render = JOB / 'render' / stem.removeprefix('student-')
        paths += [render / 'manifest.json', render / 'layout-001.png']
    before = [pin(path) for path in paths]
    write('inputs-before.json', before)

    actual = []
    checks = []
    for directory, stem in jobs:
        doc_job = JOB / directory
        handoff = load(doc_job / 'analysis-handoff.json')
        definition = workflow.select_document(plan, handoff['document']['id'])
        current_context = workflow._document_context(SNAPSHOT, definition)
        marker = '\n原文からAIが作成した全体文書計画（生成状態・採点期待値ではありません）:\n'
        index, _ = json.JSONDecoder().raw_decode(current_context.split(marker, 1)[1])
        expected = [{'id': doc['id'], 'path': doc['path'], 'title': doc['title'], 'kind': doc['kind'],
                     'responsibilities': doc['responsibilities']} for doc in load(plan)['documents']]
        assert index == expected
        phase_records = []
        for phase in ['analysis', 'draft', 'independent-review']:
            prompt_path = doc_job / phase / 'prompt.txt'
            prompt = prompt_path.read_text(encoding='utf-8')
            result = load(doc_job / phase / 'result.json')
            assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == result['metadata']['prompt_sha256']
            assert marker.strip() not in prompt
            phase_records.append({'phase': phase, 'promptSha256': result['metadata']['prompt_sha256'],
                                  'wholePlanContextPresent': False, 'providerStatus': result['metadata']['status']})
        checks.append({'name': 'current helper carries exact original AI whole-plan map: ' + definition['id'], 'status': 'PASS', 'documents': len(index)})
        checks.append({'name': 'all preserved Round1 prompts bound to recorded hashes lack newer map: ' + definition['id'], 'status': 'PASS'})
        markdown = MDROOT / (stem + '.md')
        markdown_sha = hashlib.sha256(markdown.read_bytes()).hexdigest()
        review = load(doc_job / 'independent-review/review-verified.json')
        review_handoff = load(doc_job / 'independent-review/review-handoff.json')
        render = load(JOB / 'render' / stem.removeprefix('student-') / 'manifest.json')
        assert markdown_sha == review_handoff['documentSha256'] == render['sourceSha256']
        assert render['semanticApproval'] == 'NOT_ASSESSED'
        assert not any('image' in key.lower() or 'render' in key.lower() or 'visual' in key.lower() for key in review_handoff)
        actual.append({'documentId': definition['id'], 'documentSha256': markdown_sha,
                       'phases': phase_records, 'textApproved': review['approved'],
                       'textFindingCount': len(review['findings']), 'renderDisplay': render['display']['status'],
                       'renderSemanticApproval': render['semanticApproval'], 'visualMaterialBoundByTextHandoff': False})

    editor_job = JOB / jobs[1][0]
    editor_review = load(editor_job / 'independent-review/review-verified.json')
    assert editor_review == {'documentId': 'SM-DET-STUDENT-EDITOR', 'approved': True, 'findings': [], 'unresolved': []}
    assert '<header>' in (SOURCE / 'Views/Shared/_Layout.cshtml').read_text(encoding='utf-8')
    source_edit = (SOURCE / 'Views/Students/Edit.cshtml').read_text(encoding='utf-8')
    editor_md = (MDROOT / 'student-editor.md').read_text(encoding='utf-8')
    assert '<h1>' in source_edit and '<h3>学生登録' in editor_md
    assert '<div class="grid">' not in source_edit and '<div class="grid">' in editor_md
    commands = [event['item'].get('command', '') for event in
                (json.loads(line) for line in (editor_job / 'independent-review/events.jsonl').read_text(encoding='utf-8').splitlines())
                if event.get('type') == 'item.completed' and event.get('item', {}).get('type') == 'command_execution']
    result_file = editor_job / 'independent-review/result.json'
    image_file = JOB / 'render/editor/layout-001.png'
    assert image_file.stat().st_mtime > result_file.stat().st_mtime
    checks.append({'name': 'actual text-approved editor contains source-backed heading and wrapper mismatches', 'status': 'PASS'})
    checks.append({'name': 'viewed render artifact was written after text reviewer result', 'status': 'PASS'})
    assert '画像を閲覧していないレビューは視覚的一致を承認しません' in prompts.REVIEW
    checks.append({'name': 'current prompt separates unviewed visual scope', 'status': 'PASS'})
    after = [pin(path) for path in paths]
    write('inputs-after.json', after)
    assert before == after
    checks.append({'name': 'all audited production, source, original response and render bytes unchanged', 'status': 'PASS', 'files': len(paths)})
    write('audit-check-results.json', {
        'schema': 'reverse-ai-method-audit-checks/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'checkType': 'New read-only transport/approval-scope evidence checks; not production regression suite',
        'runtimeWorkflowPath': str(Path(workflow.__file__).resolve()),
        'snapshot': capsule.verification_state(SNAPSHOT), 'checks': checks, 'actualJobs': actual,
        'editorReviewerExplicitSourceCommands': {'count': len(commands),
            'hasEditView': any('Edit.cshtml' in command for command in commands),
            'hasSharedStylesheet': any('site.css' in command for command in commands),
            'hasExplicitSharedLayoutPath': any('_Layout.cshtml' in command for command in commands),
            'scope': 'Command strings only; absence of a literal path is not proof no other indirect read occurred'},
        'artifactWriteOrderUtc': {
            'textResultLastWrite': datetime.fromtimestamp(result_file.stat().st_mtime, timezone.utc).isoformat(),
            'layoutPngLastWrite': datetime.fromtimestamp(image_file.stat().st_mtime, timezone.utc).isoformat()},
        'sourceProgramsExecuted': False, 'newProviderJobsStarted': 0, 'evaluatorMaterialRead': False,
        'formalBusinessRubricEvaluated': False, 'priorTestPassReused': False})
    print(json.dumps({'status': 'PASS', 'newEvidenceChecks': len(checks), 'unchangedPinnedFiles': len(paths)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
