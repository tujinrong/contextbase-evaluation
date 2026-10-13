"""Bind existing reviews to a separate metadata render and newly viewed representative PNGs."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent
JOB = ROOT / 'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-03'
RENDER_REPORT = ROOT / 'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-round-03'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(name, value):
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    original_pins = load(REPORT / 'inputs-after-final-record.json')
    assert len(original_pins) == 67
    for item in original_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    viewed = [Path(item) for item in load(REPORT / 'viewed-images-metadata-01.paths.json')]
    assert len(viewed) == len(set(viewed)) == 8
    new_inputs = [Path(__file__).resolve(), REPORT / 'README-metadata-01.md',
                  REPORT / 'viewed-images-metadata-01.paths.json', REPORT / 'review-manifest.json']
    documents = []
    runtime_files = {}
    for stem, job, expected_hash, graph in [
        ('student-search', '488af9821732c8f6',
         '370fcc8b85803fe167d0b7148e5e612e657ee6a8c9fcefca77d63a89af6c6777', 'diagram-008'),
        ('student-editor', 'eebb51fa1eb2da8f',
         'ae0961d287d2cea643605a2a83b9ad7d5f65683f214b55f001197d02149ca979', 'diagram-007'),
    ]:
        render_root = JOB / 'render-metadata-01' / stem
        manifest_file = render_root / 'manifest.json'
        manifest = load(manifest_file)
        draft_file = JOB / job / 'draft-result.json'
        markdown = Path(manifest['source'])
        report_file = RENDER_REPORT / (stem + '-render-metadata-01.json')
        parent_report = load(report_file)
        assert all(parent_report[key] == value for key, value in manifest.items())
        assert parent_report['documentId'] == load(draft_file)['documentId']
        assert parent_report['generationRuntimeModified'] is False
        assert parent_report['originalApplicationExecuted'] is False
        assert parent_report['correctionLabel'] == 'metadata-01'
        for item in parent_report['renderRuntimeFiles']:
            path = JOB / item['path']
            assert sha(path) == item['sha256']
            runtime_files[path] = pin(path)
        assert sha(markdown) == expected_hash == manifest['sourceSha256'] == load(draft_file)['contentSha256']
        assert manifest['originalModified'] is False
        assert manifest['structure']['status'] == manifest['display']['status'] == 'PASS'
        assert not manifest['safety']['removed'] and not manifest['display']['blockedRequests']
        assert manifest['safety']['inputJavaScriptEnabled'] is False
        assert all(item['status'] == 'PASS' for item in manifest['layouts'] + manifest['diagrams'])
        images = []
        records = {item['id']: item for item in manifest['layouts'] + manifest['diagrams']}
        artifacts = {item['path']: item for item in manifest['artifacts']}
        for path in viewed:
            if path.parent != render_root:
                continue
            record = records[path.stem]
            assert sha(path) == record['png']['sha256'] == artifacts[path.name]['sha256']
            with Image.open(path) as picture:
                assert picture.size == (record['png']['width'], record['png']['height'])
            images.append({**pin(path), 'actuallyViewedByNativeAI': True,
                           'dimensions': [record['png']['width'], record['png']['height']],
                           'sourceLines': record['sourceLines'], 'viewTool': 'tools.view_image, original detail'})
        assert {Path(item['path']).stem for item in images} == {'layout-001', 'layout-002', 'layout-003', graph}
        new_inputs += [manifest_file, report_file, draft_file, markdown] + [ROOT / item['path'] for item in images]
        documents.append({'documentId': load(draft_file)['documentId'], 'markdown': pin(markdown),
            'separateMetadataRenderManifest': pin(manifest_file), 'parentRenderReport': pin(report_file),
            'structureStatus': manifest['structure']['status'], 'displayStatus': manifest['display']['status'],
            'safetyRemoved': manifest['safety']['removed'], 'blockedRequests': manifest['display']['blockedRequests'],
            'allDiagramRenderCount': len(manifest['diagrams']), 'allLayoutRenderCount': len(manifest['layouts']),
            'actuallyViewedImages': images,
            'otherNewPngsVisuallyUnassessed': [item['id'] + '.png' for item in manifest['diagrams']
                                            if item['id'] != graph],
            'allNewDocumentTilesVisuallyUnassessed': [item['path'] for item in manifest['display']['documentCapture']['pages']]})
    assert len(runtime_files) == 13
    new_inputs += list(runtime_files)
    before = [pin(path) for path in new_inputs]
    write('metadata-01-inputs-before.json', before)
    after = [pin(path) for path in new_inputs]
    assert before == after
    for item in original_pins:
        assert sha(ROOT / item['path']) == item['sha256']
    write('metadata-01-inputs-after.json', after)
    result = {'schema': 'reverse-ai-focus-metadata-render-review/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'METADATA_RENDER_PIN_CHECKS_PASS',
        'exitCode': 0, 'original67ReviewInputPinsStillUnchanged': True,
        'originalReviewManifest': pin(REPORT / 'review-manifest.json'),
        'newPinnedInputsUnchanged': len(before), 'documents': documents,
        'separateFrozenRenderRuntimePins': list(runtime_files.values()),
        'exactAdditionalNativeViewedCounts': {'layout': 6, 'diagram': 2},
        'nativeViewedListFile': 'viewed-images-metadata-01.paths.json',
        'boundedSourceReviewRemainsApproved': True, 'boundedRepresentativeNewVisualReviewApproved': True,
        'displayPublicationGatePassedForTheseTwoMarkdowns': True,
        'wholeApplicationOrFullModesApproved': False, 'unviewedNewPixelIdentityAsserted': False,
        'formallyEvaluatedByOriginalRubric': False, 'evaluatorMaterialRead': False,
        'originalMarkdownEdited': False, 'newAIJobsStartedByReviewer': 0,
        'newRenderJobsStartedByReviewer': 0}
    write('metadata-01-manifest.json', result)
    print(json.dumps({'status': result['status'], 'exitCode': 0,
                      'additionalActuallyViewed': 8, 'newPinnedInputsUnchanged': len(before)}))


if __name__ == '__main__':
    main()
