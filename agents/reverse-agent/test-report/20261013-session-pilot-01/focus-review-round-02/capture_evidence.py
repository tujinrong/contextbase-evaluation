"""Pin already authored review and actually viewed artifacts, without authoring prose."""
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
JOB = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-02-attempt-02'
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
    viewed = [Path(path) for path in load(REPORT / 'viewed-images-corrected.paths.json')]
    assert len(viewed) == len(set(viewed)) == 26
    starting_sources = load(REPORT / 'source-pins-before.json')
    for item in starting_sources:
        assert sha(SNAPSHOT / item['path']) == item['sha256']
    sources = {item['path'] for item in starting_sources}
    sources.update('sources/' + path for path in [
        'Infrastructure/WebStudentCoordinator.cs', 'Infrastructure/SearchContextStore.cs',
        'Infrastructure/EditorSnapshotStore.cs', 'Infrastructure/RequestIdentity.cs',
        'Infrastructure/WebPresentation.cs', 'database/002_seed.sql'])
    documents = []
    input_files = [SNAPSHOT / path for path in sorted(sources)]
    input_files.append(SNAPSHOT / 'manifest.json')
    image_count = {'layout': 0, 'diagram': 0}
    for directory, stem in [('488af9821732c8f6', 'student-search'), ('eebb51fa1eb2da8f', 'student-editor')]:
        draft_file = JOB / directory / 'draft-result.json'
        draft = load(draft_file)
        render_root = JOB / 'render-corrected' / stem
        manifest_file = render_root / 'manifest.json'
        manifest = load(manifest_file)
        markdown = Path(manifest['source'])
        review_file = REPORT / (stem + '-review.json')
        review = load(review_file)
        assert draft['documentId'] == review['documentId']
        assert sha(markdown) == draft['contentSha256'] == manifest['sourceSha256']
        Draft202012Validator(schemas.REVIEW).validate(review)
        workflow.references_valid(review, materials)
        assert not any(finding['code'] == 'META_PATH' for finding in manifest['structure']['findings'])
        assert all(item['status'] == 'PASS' for item in manifest['layouts'] + manifest['diagrams'])
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
        assert {item['id'] + '.png' for item in manifest['layouts']} <= {Path(item['path']).name for item in native_images}
        input_files += [draft_file, markdown, manifest_file, review_file] + [ROOT / item['path'] for item in native_images]
        documents.append({'documentId': review['documentId'], 'markdown': pin(markdown),
            'draftResult': pin(draft_file), 'correctedRenderManifest': pin(manifest_file),
            'review': pin(review_file), 'approved': review['approved'],
            'findingCounts': {severity: sum(item['severity'] == severity for item in review['findings'])
                              for severity in ['critical', 'major', 'minor']},
            'renderStructureStatus': manifest['structure']['status'], 'renderDisplayStatus': manifest['display']['status'],
            'allDiagramRenderCount': len(manifest['diagrams']),
            'renderedDiagramStatuses': {item['id']: item['status'] for item in manifest['diagrams']},
            'actuallyViewedImages': native_images,
            'unviewedDiagramPngs': [item['id'] + '.png' for item in manifest['diagrams']
                                  if not any(Path(image['path']).stem == item['id'] for image in native_images)],
            'structureFindings': manifest['structure']['findings'],
            'safetyRemoved': manifest['safety']['removed'], 'schemaAndRawSourceReferences': 'PASS'})
    assert image_count == {'layout': 5, 'diagram': 21}
    before = [pin(path) for path in input_files]
    write('inputs-before-final-record.json', before)
    source_pins = [{'path': path, 'sha256': sha(SNAPSHOT / path),
                    'lines': len((SNAPSHOT / path).read_text(encoding='utf-8').splitlines())}
                   for path in sorted(sources)]
    write('source-pins-after.json', source_pins)
    after = [pin(path) for path in input_files]
    assert before == after
    write('inputs-after-final-record.json', after)
    write('review-manifest.json', {
        'schema': 'reverse-ai-focus-source-visual-review/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'snapshot': capsule.verification_state(SNAPSHOT), 'referenceMode': capsule.reference_mode(materials),
        'reviewScope': 'Raw source plus published Round2 Markdown and actually viewed corrected static PNGs',
        'sourcePins': source_pins, 'documents': documents,
        'exactNativeViewedCounts': image_count, 'nativeViewedListFile': 'viewed-images-corrected.paths.json',
        'first15SourcePinsUnchangedFromPreparation': True, 'finalPinnedInputsUnchanged': len(before),
        'canonicalMetaPathCallerIssueResolvedInCorrectedRender': True,
        'initialCallerArtifactsPreserved': True, 'originalMarkdownChangedForRender': False,
        'preservedSourceFacts': [
            'Shared header/h1 and original UI field ordering/CSS restored without invented editor grid wrapper',
            'Normal-new/Viewer-unsearched screens and documented confirmation/admin/found fragments separated',
            'Search Name request mapping, NameKey160, name_key nvarchar320 NOT NULL and @name NVarChar642 retained',
            'HTTP raw/binder/service boundaries and UnassignedOnly JS clear vs server disabled distinction retained',
            'ConfirmationRequired may legitimately have zero candidates when a supplied token is invalid',
            'NoChange vs Saved303, memory reset vs latest DB reload, delete failure Load and possible404 retained'],
        'unassessedScopes': ['Unlisted SQL/ER diagram PNGs', 'All document vertical tiles',
            'Narrow viewports', 'Full existing edit/Viewer/admin/confirmation screen compositions',
            'Original application, framework binding, actual DB data/deployment, concurrency and browser focus execution'],
        'knownUnknownsPreserved': 'Draft unresolved operational/binder/real-execution boundaries remain outside the static source/image verdict; no new runtime certainty asserted',
        'publicationApproved': False, 'fullScreenModeVisualFidelityVerified': False,
        'sourceProgramsExecuted': False, 'newProviderJobsStartedByReviewer': 0,
        'evaluatorMaterialRead': False, 'referenceDesignContentsReadForThisReview': False,
        'formallyEvaluatedByOriginalRubric': False, 'priorPassReused': False,
        'productionEdited': False})
    print(json.dumps({'status': 'SCHEMA_AND_PIN_CHECKS_PASS', 'viewedLayouts': 5,
                      'viewedDiagrams': 21, 'unchangedFinalInputPins': len(before),
                      'sourcePins': len(source_pins), 'publicationApproved': False}))


if __name__ == '__main__':
    main()
