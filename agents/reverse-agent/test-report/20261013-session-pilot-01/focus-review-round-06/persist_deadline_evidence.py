"""Persist already observed Round6 evidence after deadline; no semantic reads or jobs."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(r'D:\開発\contextbase-evaluation').resolve()
REPORT = Path(__file__).resolve().parent
CAP = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
DEADLINE = datetime.fromisoformat('2026-10-13T03:20:58+00:00')

def read_metadata(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stamp(s):
    if s.endswith(' UTC'):
        s = s[:-4].replace(' ', 'T', 1) + '+00:00'
    return datetime.fromisoformat(s).astimezone(timezone.utc)

def save_exclusive(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}

def checked_hash(p, expected):
    absolute = p.resolve()
    assert absolute.is_relative_to(ROOT), 'Hash target outside workspace'
    current = sha(absolute) if absolute.is_file() else None
    return {'path': absolute.relative_to(ROOT).as_posix(), 'expectedSha256': expected,
            'currentSha256': current, 'match': current == expected}

partial_path = REPORT / 'partial-manifest-03-before-deadline.json'
assert sha(partial_path) == '14c2ad12b1469273012ce9ff3e22526595798c4e64821c251d59e4eda567e895'
partial = read_metadata(partial_path)
bound = stamp(partial['savedAt'])
assert bound < DEADLINE
viewed = partial['viewedImages']
assert len(viewed) == 69 and len({x['path'] for x in viewed}) == 69
before, after, unknown = [], [], []
for item in viewed:
    try:
        when = stamp(item['viewedAt'])
        (before if when <= bound < DEADLINE else after if when >= DEADLINE else unknown).append(item)
    except (KeyError, ValueError):
        unknown.append(item)
assert len(before) == 69 and not after and not unknown

record_paths = [partial_path, REPORT / 'student-search-review.json',
                REPORT / 'preparation-validation.json', REPORT / 'source-pins-before.json',
                REPORT / 'capsule-material-pins.json', REPORT / 'preparation-execution-note.json']
for pattern in ('viewed-batch-*.json', 'source-read-*.json', 'reference-read-*.json',
                'md-read-*.json', '*-frozen-inputs.json'):
    record_paths.extend(sorted(REPORT.glob(pattern)))
record_paths = sorted(set(record_paths))
record_before = {p: sha(p) for p in record_paths}

launch = read_metadata(REPORT / 'preparation-validation.json')['pins']
source = read_metadata(REPORT / 'source-pins-before.json')['files']
capsule = read_metadata(REPORT / 'capsule-material-pins.json')['files']
launch_checks = [checked_hash(ROOT / x['path'], x['sha256']) for x in launch]
source_checks = [checked_hash(CAP / x['path'], x['sha256']) for x in source]
capsule_checks = [checked_hash(CAP / x['path'], x['sha256']) for x in capsule]
artifact_checks = []
for entry in partial['frozenCompletedInputs']:
    record = read_metadata(REPORT / entry['record'])
    for x in record['pins']:
        artifact_checks.append(checked_hash(ROOT / x['sourcePath'], x['sha256']))
        artifact_checks.append(checked_hash(ROOT / x['frozenPath'], x['sha256']))
image_checks = [checked_hash(ROOT / x['path'], x['sha256']) for x in viewed]

# Original files are opened only as byte streams for SHA256, never decoded.
protected_path = REPORT.parent / 'protected-before.json'
protected_baseline_sha = sha(protected_path)
protected = read_metadata(protected_path)
assert len(protected) == 179 and len({x['path'] for x in protected}) == 179
protected_checks = [checked_hash(Path(x['path']), x['sha256']) for x in protected]
assert sha(protected_path) == protected_baseline_sha
protected_record = {
    'schema': 'reverse-independent-protected-sha-check/1', 'round': 6,
    'phase': 'AFTER_DEADLINE_EVIDENCE_PERSISTENCE_SHA_ONLY',
    'checkedAt': datetime.now(timezone.utc).isoformat(),
    'baselinePath': str(protected_path), 'baselineSha256': protected_baseline_sha,
    'checkScope': 'SHA256 only against179 original pins; no protected-file semantic reading',
    'total': 179, 'unchanged': sum(x['match'] for x in protected_checks),
    'changed': sum(not x['match'] and x['currentSha256'] is not None for x in protected_checks),
    'missing': sum(x['currentSha256'] is None for x in protected_checks),
    'evaluatorContentsSemanticallyRead': False, 'originalSpecContentsSemanticallyRead': False,
    'applicationExecuted': False, 'results': protected_checks,
}
protected_output = save_exclusive(REPORT.parent / 'focus-protected-check-06-native-final-01.json', protected_record)

editor_partial = {
    'schema': 'reverse-independent-existing-observations-partial/1', 'round': 6,
    'documentId': 'SM-DET-STUDENT-EDITOR',
    'savedAt': datetime.now(timezone.utc).isoformat(),
    'purpose': 'Post-deadline persistence of observations made before deadline; no new review',
    'publishedMdSha256': '0c10e37c99ede863745128b4a36977eff3436b3f323d635fcca0f4c36f9fc594',
    'approval': None, 'fullSourceProcedureDiagramResultReconciliationCompleted': False,
    'imagesActuallyViewedBeforeDeadline': 39,
    'majorIssuesNewlyConfirmedInObservedSubset': [], 'absenceOfDefectsCertified': False,
    'observationsAlreadyMadeBeforeDeadline': [
        {'images': ['diagram-002.png', 'diagram-004.png', 'diagram-017.png'],
         'note': 'Observed late nonempty-context re-Get after database reads, original401/403/409 before Snapshot, and empty-context NULL branch. Full editor reconciliation remains incomplete.'},
        {'images': ['diagram-015.png'],
         'note': 'Observed Reset FormGuard400 before identity/ID/Snapshot, NULL library exception separate from absent409 and owner403; old ReturnRevision retained.'},
        {'images': ['diagram-008.png', 'diagram-009.png', 'diagram-011.png', 'diagram-021.png'],
         'note': 'Observed local catch boundary/typed catch precedence, NONNULL key lookup miss, separate new-confirmation versus Saved return values, and general unknown formula. This retained checkpoint is not a completed editor acceptance.'},
        {'images': ['layout-001.png', 'layout-002.png', 'layout-003.png', 'diagram-022.png'],
         'note': 'Observed shared header/date/two-column projection, warning direct table, independent delete form, and nullable physical relation. Whole conditional mode combinations were not rendered or verified.'},
        {'images': ['document-001.png', 'document-002.png', 'document-003.png', 'document-004.png',
                    'document-005.png', 'document-006.png', 'document-007.png', 'document-008.png',
                    'document-009.png', 'document-010.png', 'document-011.png', 'document-012.png',
                    'document-013.png', 'document-014.png'],
         'note': 'All whole-document text tiles actually viewed at original resolution. Source-to-procedure-to-graph-to-result reconciliation of all editor text was not completed before the deadline.'},
    ],
    'remaining': ['Complete editor source/field/SQL/ER/procedure/local-graph/result semantic reconciliation',
                  'Authorized-reference design-intent contract evaluation',
                  'Undrawn complete mode combinations', 'Narrow-width rendering',
                  'Live HTTP/binder/application/DB/concurrency/cancellation/response delivery', 'Formal grading'],
    'priorReviewReused': False, 'newPostDeadlineImageOrSourceReading': False,
}
editor_output = save_exclusive(REPORT / 'student-editor-partial-observations-final.json', editor_partial)

records = []
for p in record_paths:
    current = sha(p)
    records.append({'path': p.relative_to(ROOT).as_posix(), 'beforeSha256': record_before[p],
                    'afterSha256': current, 'match': current == record_before[p]})
search_review = read_metadata(REPORT / 'student-search-review.json')
assert search_review['approved'] is True
assert search_review['findings'] == []

final = {
    'schema': 'reverse-independent-deadline-evidence-persistence/1', 'round': 6,
    'savedAt': datetime.now(timezone.utc).isoformat(),
    'deadline': DEADLINE.isoformat(), 'rootObservedInterruptAt': '2026-10-13T03:21:08+00:00',
    'operation': 'Existing evidence persistence and SHA-only rechecks after deadline',
    'approval': None, 'sourceReviewCompleted': None, 'visualReviewCompleted': None,
    'formalGradingCompleted': None,
    'boundary': {
        'preDeadlineManifest': partial_path.name, 'preDeadlineManifestSha256': record_before[partial_path],
        'manifestSavedAtUTC': bound.isoformat(),
        'latestRecordedViewAtUTC': max(stamp(x['viewedAt']) for x in before).isoformat(),
        'basis': 'Every retained actual-view entry has a timestamp at or before the69-entry manifest saved03:20:40.502192Z, before03:20:58Z. Post-deadline work only hashes and persists those existing records.',
        'beforeDeadline': len(before), 'afterDeadline': len(after), 'boundaryUnknown': len(unknown),
        'postDeadlineNewImageViewing': False, 'postDeadlineNewSourceOrMdReading': False,
        'postDeadlineNewReviewOrEvaluation': False,
    },
    'documents': {
        'student-search': {
            'publishedMdSha256': '4a0fe4056d701e3a51ab58e693212de094f1d781d38a6258bbc332d4e99d07cc',
            'images': {'diagrams': 16, 'layouts': 3, 'wholeTextTiles': 11, 'total': 30},
            'boundedSourceOnlyApproval': True,
            'review': {'path': 'student-search-review.json', 'sha256': sha(REPORT / 'student-search-review.json')},
            'approvalScope': 'Fresh raw-source/current-prose/procedure/local-diagram/result and viewed static projections only',
            'unresolvedMeaning': 'Standalone bounded review scope/preserve/unknown annotations; not unresolved text questions under strict CLI REVIEW',
            'cliSchemaGuardReusedOrWeakened': False,
        },
        'student-editor': {
            'publishedMdSha256': editor_partial['publishedMdSha256'],
            'images': {'diagrams': 22, 'layouts': 3, 'wholeTextTiles': 14, 'total': 39},
            'boundedSourceOnlyApproval': None,
            'fullSourceProcedureDiagramResultReconciliationCompleted': False,
            'existingObservedSubset': editor_output,
        },
    },
    'allCurrentGeneratedPngsActuallyViewed': True,
    'unviewedCurrentGeneratedPngs': [],
    'viewedImagesBeforeDeadline': before,
    'afterDeadlineViewedImages': after, 'boundaryUnknownImages': unknown,
    'sourceReadEvidence': partial['sourceReadEvidence'],
    'authorizedDesignReadEvidence': partial['authorizedDesignReadEvidence'],
    'currentMdTextReadEvidence': partial['currentMdTextReadEvidence'],
    'readScopeLimits': [
        'Read-range records preserve actual pre-deadline declared ranges. An initially truncated service output was recovered by the saved recovery record.',
        'Raw search Markdown reads were ranges1-200 and448-805; first output had truncation. Whole1114-line rendered text was actually viewed in11tiles, not claimed as an independent complete raw line scan.',
        'Editor1286-line text was viewed in14tiles; no separate full raw Markdown line-scan or complete semantic reconciliation is claimed.',
        'Only4 of11 authorized reference files in13 saved ranges were semantically read. Full reference-design intention conformity remains unassessed.',
    ],
    'capsuleTrustScope': 'legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest; not sealed-v2',
    'shaOnlyChecksAfterDeadline': {
        'launch26': launch_checks, 'freshSource32': source_checks,
        'capsule43Source11AuthorizedReferences': capsule_checks,
        'rawAnswerDraftMdManifestArtifactsOriginalAndFrozen': artifact_checks,
        'actualViewedPng69': image_checks, 'protected179': protected_output,
        'driftCount': sum(not x['match'] for checks in
                         (launch_checks, source_checks, capsule_checks, artifact_checks, image_checks)
                         for x in checks),
    },
    'immutableExistingEvidenceRecords': records,
    'unassessedScopes': partial['retainedUnassessedScopes'] + ['Complete editor semantic reconciliation'],
    'priorApprovalOrImageReused': False, 'duplicateAiOrRenderStarted': False,
    'stopOrApplicationOrDatabaseExecuted': False,
    'sourceOrMdOrProductionEdited': False, 'evaluationExpectationsRead': False,
    'protectedSemanticContentsRead': False,
    'overallPassInferredFromRenderingOrAllImages': False,
    'operationalNotes': [
        'Preparation helper first invocation wrote four preparation records then failed on exclusive protected-output name collision; new independent protected record succeeded without overwriting history.',
        'Private partial capture first new partial02 attempt failed KeyError because text-freeze metadata matched native-freeze glob; target was not created. Native-only filter then succeeded; first failed attempt is not counted as a pass.',
        'Post-deadline metadata display invoked GetType on null fields and emitted PowerShell diagnostic messages; it did not alter records or perform source/image review.',
    ],
}
final_output = save_exclusive(REPORT / 'final-deadline-persistence-manifest.json', final)
print(json.dumps({'final': final_output, 'editorPartial': editor_output,
                  'protected': protected_output, 'actualBeforeDeadlinePng': len(before),
                  'postDeadlinePng': len(after), 'boundaryUnknown': len(unknown),
                  'overallApproval': None, 'editorApproval': None,
                  'searchBoundedSourceOnlyApproval': True,
                  'driftCount': final['shaOnlyChecksAfterDeadline']['driftCount'],
                  'protectedUnchanged': protected_record['unchanged'],
                  'existingEvidenceDrift': sum(not x['match'] for x in records)}, ensure_ascii=False))
