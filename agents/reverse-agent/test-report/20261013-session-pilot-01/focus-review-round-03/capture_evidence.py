"""Verify already authored Round3 review and actually viewed artifacts; no prose generation."""
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
JOB = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-03'
SNAPSHOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'


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
    viewed = [Path(path) for path in load(REPORT / 'viewed-images.paths.json')]
    assert len(viewed) == len(set(viewed)) == 31
    starting = load(REPORT / 'source-pins-before.json')
    assert len(starting) == 24
    for item in starting:
        assert sha(SNAPSHOT / item['path']) == item['sha256']
    source_files = [SNAPSHOT / item['path'] for item in starting]
    input_files = source_files + [SNAPSHOT / 'manifest.json', REPORT / 'viewed-images.paths.json',
                                 REPORT / 'README.md', Path(__file__).resolve()]
    source_pins = [{**item, 'lines': len((SNAPSHOT / item['path']).read_text(encoding='utf-8').splitlines())}
                   for item in starting]
    documents = []
    image_count = {'layout': 0, 'diagram': 0}
    for directory, stem, expected_md, expected_viewed_diagrams in [
        ('488af9821732c8f6', 'student-search',
         '370fcc8b85803fe167d0b7148e5e612e657ee6a8c9fcefca77d63a89af6c6777', 15),
        ('eebb51fa1eb2da8f', 'student-editor',
         'ae0961d287d2cea643605a2a83b9ad7d5f65683f214b55f001197d02149ca979', 10),
    ]:
        draft_file = JOB / directory / 'draft-result.json'
        draft = load(draft_file)
        render_root = JOB / 'render' / stem
        manifest_file = render_root / 'manifest.json'
        manifest = load(manifest_file)
        markdown = Path(manifest['source'])
        review_file = REPORT / (stem + '-review.json')
        review = load(review_file)
        assert draft['documentId'] == review['documentId']
        assert sha(markdown) == draft['contentSha256'] == manifest['sourceSha256'] == expected_md
        assert draft['analysisExecutedInThisJob'] is True
        assert draft['aiAuthored'] is True and draft['semanticProseAssembledByPython'] is False
        Draft202012Validator(schemas.REVIEW).validate(review)
        workflow.references_valid(review, materials)
        assert manifest['originalModified'] is False
        assert manifest['structure']['status'] == 'PASS' and not manifest['structure']['findings']
        assert all(item['status'] == 'PASS' for item in manifest['layouts'] + manifest['diagrams'])
        assert manifest['safety']['inputJavaScriptEnabled'] is False
        assert manifest['safety']['removed'] == [{'kind': 'element', 'name': 'meta'}] * 4
        artifacts = {item['path']: item for item in manifest['artifacts']}
        records = {item['id']: item for item in manifest['layouts'] + manifest['diagrams']}
        native_images = []
        for path in viewed:
            if path.parent != render_root:
                continue
            record = records[path.stem]
            assert sha(path) == record['png']['sha256'] == artifacts[path.name]['sha256']
            with Image.open(path) as picture:
                assert picture.size == (record['png']['width'], record['png']['height'])
            native_images.append({**pin(path), 'sourceLines': record['sourceLines'],
                'dimensions': [record['png']['width'], record['png']['height']],
                'actuallyViewedByNativeAI': True, 'viewTool': 'tools.view_image, original detail'})
            image_count['layout' if path.stem.startswith('layout-') else 'diagram'] += 1
        assert len(native_images) == expected_viewed_diagrams + 3
        assert {item['id'] + '.png' for item in manifest['layouts']} <= {Path(item['path']).name for item in native_images}
        input_files += [draft_file, markdown, manifest_file, review_file] + [ROOT / item['path'] for item in native_images]
        documents.append({'documentId': review['documentId'], 'markdown': pin(markdown),
            'draftResult': pin(draft_file), 'renderManifest': pin(manifest_file),
            'review': pin(review_file), 'boundedScopeApproved': review['approved'],
            'findingCounts': {severity: sum(item['severity'] == severity for item in review['findings'])
                              for severity in ['critical', 'major', 'minor']},
            'renderStructureStatus': manifest['structure']['status'], 'renderDisplayStatus': manifest['display']['status'],
            'allDiagramRenderCount': len(manifest['diagrams']),
            'renderedDiagramStatuses': {item['id']: item['status'] for item in manifest['diagrams']},
            'actuallyViewedImages': native_images,
            'unviewedDiagramPngs': [item['id'] + '.png' for item in manifest['diagrams']
                                  if not any(Path(image['path']).stem == item['id'] for image in native_images)],
            'allDocumentTilesUnviewed': [item['path'] for item in manifest['display']['documentCapture']['pages']],
            'safetyRemoved': manifest['safety']['removed'], 'reviewSchemaAndReferences': 'PASS'})
    assert image_count == {'layout': 6, 'diagram': 25}
    before = [pin(path) for path in input_files]
    write('inputs-before-final-record.json', before)
    write('source-pins-after.json', source_pins)
    after = [pin(path) for path in input_files]
    assert before == after
    for item in starting:
        assert sha(SNAPSHOT / item['path']) == item['sha256']
    write('inputs-after-final-record.json', after)
    review_manifest = {
        'schema': 'reverse-ai-focus-source-visual-review/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'snapshot': capsule.verification_state(SNAPSHOT), 'referenceMode': capsule.reference_mode(materials),
        'reviewScope': 'Raw source plus published Round3 Markdown and explicitly listed actually viewed static PNGs',
        'sourcePins': source_pins, 'documents': documents,
        'exactNativeViewedCounts': image_count, 'nativeViewedListFile': 'viewed-images.paths.json',
        'all24PreparedSourcePinsUnchanged': True, 'finalPinnedInputsUnchanged': len(before),
        'preservedSourceFacts': [
            {'fact': 'Search Page preserves individual403/409/422 and distinguishes catch reconstruction from Razor/common errors',
             'markdownLines': [540, 613], 'references': [
                 {'path': 'sources/Web/Controllers/StudentsController.cs', 'startLine': 18, 'endLine': 19},
                 {'path': 'sources/Infrastructure/WebStudentCoordinator.cs', 'startLine': 11, 'endLine': 12},
                 {'path': 'sources/Infrastructure/SearchContextStore.cs', 'startLine': 13, 'endLine': 14},
                 {'path': 'sources/Infrastructure/WebPresentation.cs', 'startLine': 23, 'endLine': 23}]},
            {'fact': 'Editor date-part null after valid era/prior parsing and AdmissionDate null bypass normal422 capture; common503 requires response not started',
             'markdownLines': [883, 919], 'references': [
                 {'path': 'sources/Core/JapaneseDateService.cs', 'startLine': 19, 'endLine': 24},
                 {'path': 'sources/Core/JapaneseDateService.cs', 'startLine': 52, 'endLine': 59},
                 {'path': 'sources/Core/StudentNormalizer.cs', 'startLine': 123, 'endLine': 143},
                 {'path': 'sources/Core/SqlServerStudentService.cs', 'startLine': 232, 'endLine': 239},
                 {'path': 'sources/Infrastructure/WebHostSetup.cs', 'startLine': 23, 'endLine': 23}]},
            {'fact': 'Name HTTP mapping, raw8scalar versus browser16UTF16, key160scalar, name_key nvarchar320 NOT NULL and typed @name642 remain separate',
             'markdownLines': [124, 125], 'references': [
                 {'path': 'sources/Web/Inputs/StudentSearchInput.cs', 'startLine': 8, 'endLine': 22},
                 {'path': 'sources/Core/StudentNormalizer.cs', 'startLine': 47, 'endLine': 70},
                 {'path': 'sources/Core/SqlServerStudentService.cs', 'startLine': 114, 'endLine': 115},
                 {'path': 'sources/Core/SqlServerStudentService.cs', 'startLine': 141, 'endLine': 141},
                 {'path': 'sources/database/001_schema.sql', 'startLine': 10, 'endLine': 12}]},
            {'fact': 'Shared header/h1/CSS, inert source routes, link appearance, independent modes and no invented editor confirmation grid retained',
             'references': [
                 {'path': 'sources/Views/Shared/_Layout.cshtml', 'startLine': 1, 'endLine': 1},
                 {'path': 'sources/Views/Students/Search.cshtml', 'startLine': 3, 'endLine': 8},
                 {'path': 'sources/Views/Students/Edit.cshtml', 'startLine': 3, 'endLine': 17},
                 {'path': 'sources/wwwroot/css/site.css', 'startLine': 1, 'endLine': 1}]},
            {'fact': 'ConfirmationRequired can have zero candidates when a supplied token is invalid',
             'references': [{'path': 'sources/Core/SqlServerStudentService.cs', 'startLine': 276, 'endLine': 290}]}
        ],
        'unassessedScopes': ['Editor unlisted10 SQL/ER diagram PNGs', 'All document vertical tiles',
            'Narrow viewports', 'Full existing edit/Viewer/admin/confirmation and search conditional screen compositions',
            'Original application, framework binding, actual DB data/deployment, concurrency and browser focus execution'],
        'knownUnknownsPreserved': 'DTO annotations, required/date HTML and source inference do not prove HTTP binder runtime values or deployed DB behavior',
        'publicationMethodObservation': 'Both SANITIZED logs remove only standalone HTML charset/viewport meta, without active application route removal; metadata policy remains a separate renderer check',
        'publicationApproved': False, 'fullScreenModeVisualFidelityVerified': False,
        'originalMarkdownChangedForRender': False, 'sourceProgramsExecuted': False,
        'newProviderJobsStartedByReviewer': 0, 'newRenderJobsStartedByReviewer': 0,
        'evaluatorMaterialRead': False, 'referenceDesignContentsSemanticallyReadForThisReview': False,
        'formallyEvaluatedByOriginalRubric': False, 'priorPassReused': False,
        'productionEdited': False}
    workflow.references_valid({'facts': [
        {'id': str(index), 'basis': 'observed-source', 'references': fact['references']}
        for index, fact in enumerate(review_manifest['preservedSourceFacts'])
    ]}, materials)
    reference_count = sum(len(fact['references']) for fact in review_manifest['preservedSourceFacts'])
    review_manifest['freshSourceReferenceRangeChecks'] = reference_count
    write('review-manifest.json', review_manifest)
    result = {'status': 'SCHEMA_AND_PIN_CHECKS_PASS', 'exitCode': 0, 'viewedLayouts': 6,
              'viewedDiagrams': 25, 'unchangedFinalInputPins': len(before), 'unchangedPreparedSourcePins': 24,
              'sourcePins': len(source_pins), 'rawSourceReferenceRangeChecks': reference_count,
              'boundedReviewApproved': True, 'publicationApproved': False}
    write('validation-result.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
