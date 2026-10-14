"""Append one explicitly sealed document result to a fresh status checkpoint."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys

report = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(report / 'evaluator-only'))
import grader

def read(path):
    return json.loads(grader.safe(path, grader.REPO).read_text(encoding='utf-8-sig'))
def sha(path):
    return grader.digest(grader.safe(path, grader.REPO))
def fresh(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--batch', required=True)
    parser.add_argument('--score-file', default='score.json')
    parser.add_argument('--normalization-file', default='defect-normalization.json')
    parser.add_argument('--visual-review')
    args = parser.parse_args()
    if not args.revision.isalnum():
        raise ValueError('Plain checkpoint revision required')
    previous = grader.safe(report / args.previous, report / 'checkpoints')
    batch = grader.safe(report / 'evaluator-only/batches' / args.batch, report / 'evaluator-only/batches')
    score_path = grader.safe(batch / args.score_file, batch)
    norm_path = grader.safe(batch / args.normalization_file, batch)
    score, pin, normalization = read(score_path), read(batch/'canonical-pin.json'), read(norm_path)
    completed = [d for d in score['documents'] if d['complete']]
    if (len(completed) != 1 or completed[0]['documentId'] != pin['documentId'] or
        score['total']['percentage'] is not None or score['defectNormalizationReviewed'] is not True or
        normalization['status'] != 'INDEPENDENTLY_REVIEWED' or
        normalization['batchManifestSha256'] != sha(batch/'batch.json') or
        sha(Path(pin['canonicalPath'])) != pin['canonicalSha256']):
        raise ValueError('A complete unchanged independently normalized document is required')
    results = read(previous)['formalDocumentResults']
    for value in results:
        old_batch = report / value['batch']
        if (sha(old_batch/value.get('scoreFilename','score.json')) != value['scoreSha256'] or
            sha(Path(value['canonicalPath'])) != value['canonicalSha256']):
            raise ValueError('Previously accepted score/canonical binding changed')
    results = [v for v in results if not (v['referenceMode'] == pin['referenceMode'] and v['document']['documentId'] == pin['documentId'])]
    value = {'batch':batch.relative_to(report).as_posix(), 'scoreSha256':sha(score_path),
        'scoreFilename':args.score_file, 'normalizationFilename':args.normalization_file,
        'pinSha256':sha(batch/'canonical-pin.json'), 'referenceMode':pin['referenceMode'],
        'canonicalPath':pin['canonicalPath'], 'canonicalSha256':pin['canonicalSha256'],
        'document':completed[0], 'criticalRows':score['criticalRows'],
        'mandatoryMissingRows':score['mandatoryMissingRows'], 'wholeSetPercentage':None, 'finalQualified':False}
    if args.visual_review:
        visual_path = grader.safe(report/args.visual_review, report)
        visual = read(visual_path)
        if (visual['documentId'] != pin['documentId'] or visual['documentSha256'] != pin['canonicalSha256'] or
            visual['reviewScope'] != 'STATIC_PROJECTION_VS_SOURCE_RESOURCES'):
            raise ValueError('Visual proof belongs to another canonical')
        value['visualReviewPath'] = visual_path.relative_to(report).as_posix()
    results.append(value)
    created = datetime.now(timezone.utc).isoformat()
    run_path = report/'run-manifest.json'
    run_sha, run = sha(run_path), read(run_path)
    seal = read(report/'evaluator-only/fixed-rubric/seal.json')
    for mode,suffix,snapshot in (
        ('training-assisted','assisted','e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'),
        ('source-only','source','2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b')):
        entries = []
        for v in results:
            if v['referenceMode'] != mode:
                continue
            b = report/v['batch']
            e = {'documentId':v['document']['documentId'], 'batchPath':str(b),
                'normalizationPath':str(b/v.get('normalizationFilename','defect-normalization.json')),
                'canonicalPath':v['canonicalPath'], 'canonicalSha256':v['canonicalSha256'], 'roundId':b.name}
            if v.get('visualReviewPath'):
                e.update(visualReviewPath=v['visualReviewPath'], requiredVisualModes=['initial','normal','error','view-edit'])
            entries.append(e)
        fresh(report/f'evaluator-only/selection-{suffix}-partial-{args.revision}.json',
            {'schema':'independent-evaluation-batch-selection/1', 'projectId':'test-project1',
             'profile':'CSharp_ASPNET', 'referenceMode':mode, 'createdAt':created,
             'rubricSha256':seal['effectiveItemsSha256'], 'sourceSnapshotSha256':snapshot, 'documents':entries})
    fresh(report/f'checkpoints/status-scores-{args.revision}.json',
        {'schema':'reverse-agent-status-checkpoint/1', 'createdAt':created,
         'formalDocumentResults':results, 'wholeSetScore':None,
         'stopPolicy':'checkpoints/user-stop-at-95-r01.json',
         'rootActualImagesViewed':run['nativeVisualReview']['imagesActuallyReviewed'],
         'fourStateScreenDocumentsReviewed':run['screenStateReviewProgress']['completedScreenDocuments'],
         'requiredScreenDocuments':4, 'engineeringValidation':run['engineeringValidation'],
         'inputSpecificationsStarted':False, 'holdoutGeneralizationStarted':False, 'finalQualified':False})
    fresh(report/f'checkpoints/run-manifest-before-status-{args.revision}.json',run)
    assisted = [v for v in results if v['referenceMode']=='training-assisted']
    source = [v for v in results if v['referenceMode']=='source-only']
    run.update(updatedAt=created, formalScore=None, formalDocumentResults=results,
        currentFormalGrading={'status':'EXPLICIT_DOCUMENT_SCORES_ONLY', 'formalScore':None,
            'wholeSetComplete':False, 'qualified':False,
            'sourceOnlyCompletedDocuments':len(source), 'trainingAssistedCompletedDocuments':len(assisted),
            'trainingAssistedDocumentsAtOrAbove95':sum(v['document']['pass95'] for v in assisted)})
    if sha(run_path)!=run_sha:
        raise ValueError('Run metadata changed concurrently; checkpoint remains immutable')
    run_path.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'document':completed[0], 'assistedDocumentsAtOrAbove95':sum(v['document']['pass95'] for v in assisted),
                      'wholeSetPercentage':None},ensure_ascii=False))

if __name__=='__main__':
    main()
