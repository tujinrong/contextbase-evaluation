"""Pin independently authored reconciliation without generating semantic prose."""
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
RENDER = JOB / 'render-metadata-01/student-editor'
MARKDOWN = ROOT / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-03/spec/detail/student-editor.md'


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
    preserved_pins = load(PRIOR / 'inputs-after-final-record.json') + load(PRIOR / 'metadata-01-inputs-after.json')
    assert len(preserved_pins) == 100
    for item in preserved_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    review_file = REPORT / 'student-editor-addendum-review.json'
    review = load(review_file)
    Draft202012Validator(schemas.REVIEW).validate(review)
    workflow.references_valid(review, materials)
    assert review['documentId'] == 'SM-DET-STUDENT-EDITOR' and review['approved'] is False
    cli_file = JOB / 'eebb51fa1eb2da8f/independent-review/review-verified.json'
    cli = load(cli_file)
    assert cli['documentId'] == review['documentId'] and len(cli['findings']) == 2
    manifest_file = RENDER / 'manifest.json'
    manifest = load(manifest_file)
    draft_file = JOB / 'eebb51fa1eb2da8f/draft-result.json'
    assert sha(MARKDOWN) == manifest['sourceSha256'] == load(draft_file)['contentSha256'] == 'ae0961d287d2cea643605a2a83b9ad7d5f65683f214b55f001197d02149ca979'
    source_paths = ['sources/Web/Controllers/StudentsController.cs',
                    'sources/Infrastructure/WebStudentCoordinator.cs',
                    'sources/Infrastructure/SearchContextStore.cs',
                    'sources/Infrastructure/WebHostSetup.cs',
                    'sources/Infrastructure/RequestIdentity.cs']
    inputs = [SNAPSHOT / path for path in source_paths] + [MARKDOWN, cli_file, manifest_file,
              draft_file, review_file, REPORT / 'README.md', Path(__file__).resolve()]
    artifacts = {item['path']: item for item in manifest['artifacts']}
    records = {item['id']: item for item in manifest['diagrams']}
    images = []
    for diagram in ['diagram-001', 'diagram-003', 'diagram-013']:
        png = RENDER / (diagram + '.png')
        mmd = RENDER / (diagram + '.mmd')
        record = records[diagram]
        assert sha(png) == record['png']['sha256'] == artifacts[png.name]['sha256']
        assert sha(mmd) == record['sourceSha256'] == artifacts[mmd.name]['sha256']
        with Image.open(png) as picture:
            assert picture.size == (record['png']['width'], record['png']['height'])
        images.append({**pin(png), 'sourceLines': record['sourceLines'], 'mermaidSource': pin(mmd),
                       'dimensions': [record['png']['width'], record['png']['height']],
                       'actuallyViewedAgainForThisAddendum': True,
                       'viewTool': 'tools.view_image, original detail'})
        inputs += [png, mmd]
    before = [pin(path) for path in inputs]
    write('inputs-before.json', before)
    after = [pin(path) for path in inputs]
    assert before == after
    for item in preserved_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    write('inputs-after.json', after)
    evidence = {'schema': 'reverse-ai-source-review-reconciliation/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'documentId': review['documentId'],
        'markdown': pin(MARKDOWN), 'cliReviewConsidered': pin(cli_file), 'newIndependentAddendum': pin(review_file),
        'snapshot': capsule.verification_state(SNAPSHOT),
        'sources': [{**pin(SNAPSHOT / path), 'snapshotRelativePath': path} for path in source_paths],
        'renderManifest': pin(manifest_file), 'actuallyViewedImages': images,
        'claims': [
            {'claim': 'EV01/EV02 late context expiry409 omitted or fixed503', 'verdict': 'CONFIRMED',
             'severity': 'major', 'sourceReferences': review['findings'][0]['references'],
             'preservedCorrectGlobalExplanation': {'markdownLines': [1011, 1011]},
             'sourceConditionalTrace': ['Nonempty context passes initial CheckReturn',
                 'Coordinator awaits applicable GetAsync and LookupAsync',
                 'Entry is expired at later Controller.Load contexts.Get',
                 'WebFault409 prevents Snapshot/View and common middleware retains409 if response not started']},
            {'claim': 'EV07 FormGuard400 missing in local flow/response', 'verdict': 'CONFIRMED_WITH_SCOPE_QUALIFICATION',
             'severity': 'minor', 'sourceReferences': review['findings'][1]['references'],
             'overbroadClaimRefuted': 'The document as a whole already describes FormGuard at723 and400/status policy at1007/1011',
             'methodOrderingQualification': 'Action body FormGuard precedes identity.Read/IdParser/Snapshot; Authorize/CSRF entry filters remain a separate prior boundary',
             'sourceConditionalTrace': ['Authenticated/filtered request reaches Reset action body',
                 'FormGuard finds forbidden key, disallowed duplicate value or invalid exact-name __Invariant',
                 'WebFault400 stops before identity.Read/IdParser/Snapshot/ModelState.Clear/lookup',
                 'Common middleware preserves400 for response not started']}
        ],
        'validation': {'status': 'SCHEMA_AND_PIN_CHECKS_PASS', 'exitCode': 0,
                       'sourceReferencesValidated': 10, 'currentInputsUnchanged': len(before),
                       'prior67ReviewInputsAnd33MetadataInputsUnchanged': True},
        'currentEditorNeedsFreshAIRevision': True, 'previousReviewsPreservedAsHistoricalRecords': True,
        'staticPublicationDisplayGateStillPasses': True,
        'runtimeReproductionExecuted': False, 'formalOriginalRubricGradingPerformed': False,
        'evaluatorExpectationsRead': False, 'referenceDesignContentsRead': False,
        'productionEdited': False, 'originalMarkdownEdited': False, 'newAIOrRenderJobsStarted': 0}
    write('evidence-manifest.json', evidence)
    print(json.dumps(evidence['validation']))


if __name__ == '__main__':
    main()
