"""Pin independently authored search reconciliation; no source execution or prose generation."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from PIL import Image
from contextbase.ai import capsule, schemas, workflow

ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent
PRIOR = REPORT.parent
JOB = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-03'
SNAPSHOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
RENDER = JOB / 'render-metadata-01/student-search'
MARKDOWN = ROOT / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-03/spec/detail/student-search.md'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(name, value):
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    materials = capsule.verify(SNAPSHOT)
    previous_pins = load(PRIOR / 'inputs-after-final-record.json') + load(PRIOR / 'metadata-01-inputs-after.json') + load(REPORT / 'inputs-after.json')
    assert len(previous_pins) == 118
    for item in previous_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    review_file = REPORT / 'student-search-addendum-review.json'
    review = load(review_file)
    Draft202012Validator(schemas.REVIEW).validate(review)
    workflow.references_valid(review, materials)
    assert review['documentId'] == 'SM-DET-STUDENT-SEARCH' and review['approved'] is False
    cli_file = JOB / '488af9821732c8f6/independent-review/review-verified.json'
    cli = load(cli_file)
    assert cli['documentId'] == review['documentId'] and len(cli['findings']) == 1
    manifest_file = RENDER / 'manifest.json'
    manifest = load(manifest_file)
    draft_file = JOB / '488af9821732c8f6/draft-result.json'
    assert sha(MARKDOWN) == manifest['sourceSha256'] == load(draft_file)['contentSha256'] == '370fcc8b85803fe167d0b7148e5e612e657ee6a8c9fcefca77d63a89af6c6777'
    paths = ['sources/Infrastructure/SearchContextStore.cs', 'sources/Infrastructure/WebStudentCoordinator.cs',
             'sources/Web/Controllers/StudentsController.cs', 'sources/Infrastructure/WebHostSetup.cs']
    inputs = [SNAPSHOT / path for path in paths] + [SNAPSHOT / 'manifest.json', MARKDOWN, cli_file,
              manifest_file, draft_file, review_file, REPORT / 'README-search.md', Path(__file__).resolve()]
    record = next(item for item in manifest['diagrams'] if item['id'] == 'diagram-006')
    artifacts = {item['path']: item for item in manifest['artifacts']}
    png = RENDER / 'diagram-006.png'
    mmd = RENDER / 'diagram-006.mmd'
    assert sha(png) == record['png']['sha256'] == artifacts[png.name]['sha256']
    assert sha(mmd) == record['sourceSha256'] == artifacts[mmd.name]['sha256']
    with Image.open(png) as picture:
        assert picture.size == (record['png']['width'], record['png']['height'])
    inputs += [png, mmd]
    before = [pin(path) for path in inputs]
    write('search-inputs-before.json', before)
    after = [pin(path) for path in inputs]
    assert before == after
    for item in previous_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    write('search-inputs-after.json', after)
    evidence = {'schema': 'reverse-ai-source-review-reconciliation/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'documentId': review['documentId'],
        'markdown': pin(MARKDOWN), 'cliReviewConsidered': pin(cli_file), 'newIndependentAddendum': pin(review_file),
        'snapshot': capsule.verification_state(SNAPSHOT),
        'sources': [{**pin(SNAPSHOT / path), 'snapshotRelativePath': path} for path in paths],
        'renderManifest': pin(manifest_file),
        'actuallyViewedImage': {**pin(png), 'sourceLines': record['sourceLines'], 'mermaidSource': pin(mmd),
            'dimensions': [record['png']['width'], record['png']['height']],
            'actuallyViewedAgainForThisAddendum': True, 'viewTool': 'tools.view_image, original detail'},
        'claim': {'verdict': 'CONFIRMED_WITH_SCOPE_QUALIFICATION', 'severity': 'minor',
            'sourceReferences': review['findings'][0]['references'],
            'confirmed': 'E02 diagram U has no independent pre-SQL Gate waiting cancellation edge',
            'refutedOverstatement': 'Current MD949 already disclaims delivery completion after response start/disconnection',
            'alreadyCorrectMarkdownBoundaries': [214, 479, 949],
            'sourceConditionalTrace': ['Valid request reaches Use with cancellation token',
                'Get succeeds; WaitAsync(ct) cancels before gate acquisition and before try/operation',
                'No SearchAsync/SQL/state update/release for this failed acquisition path',
                'OperationCanceledException bypasses Controller catch(WebFault)',
                'If response not started, common middleware sets503 and attempts HTML; successful delivery is not guaranteed']},
        'validation': {'status': 'SCHEMA_AND_PIN_CHECKS_PASS', 'exitCode': 0,
                       'sourceReferencesValidated': 4, 'currentInputsUnchanged': len(before),
                       'prior118ReviewMetadataAndEditorAddendumInputPinsUnchanged': True},
        'currentSearchNeedsFreshAIRevision': True, 'previousReviewsPreservedAsHistoricalRecords': True,
        'staticPublicationDisplayGateStillPasses': True, 'runtimeCancellationReproductionExecuted': False,
        'formalOriginalRubricGradingPerformed': False, 'evaluatorExpectationsRead': False,
        'referenceDesignContentsRead': False, 'productionEdited': False,
        'originalMarkdownEdited': False, 'newAIOrRenderJobsStarted': 0}
    write('search-evidence-manifest.json', evidence)
    print(json.dumps(evidence['validation']))


if __name__ == '__main__':
    main()
