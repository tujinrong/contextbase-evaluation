"""Record the user's stopping condition and completed immutable score receipts."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

report = Path(__file__).resolve().parents[1]
created = datetime.now(timezone.utc).isoformat()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(path, value):
    if path.exists():
        raise ValueError('Fresh evidence path required: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

evaluation = report/'evaluator-only'
if sha(evaluation/'grader.py') != '83390d439db12119fa7f82cfb48672105488ccb748ca960c68ff918112190bb7':
    raise ValueError('Frozen grader changed')
names = ('source-m-code-category-r03-r6-n2', 'source-table-index-r04-r6',
         'source-m-code-r04-r6', 'source-m-student-r04-r6',
         'assisted-m-code-category-r01-r6', 'assisted-m-class-r02-r6',
         'assisted-m-student-r01-r6', 'assisted-m-code-r02-r6',
         'assisted-table-index-r03-r6', 'assisted-operation-log-r02-r6')
results=[]
for name in names:
    batch = evaluation/'batches'/name
    score, pin = load(batch/'score.json'), load(batch/'canonical-pin.json')
    complete = [d for d in score['documents'] if d['complete']]
    if len(complete) != 1 or complete[0]['documentId'] != pin['documentId']:
        raise ValueError('One completed document is required')
    if score['total']['percentage'] is not None or sha(Path(pin['canonicalPath'])) != pin['canonicalSha256']:
        raise ValueError('Whole-set score must remain unknown; canonical must be unchanged')
    results.append({'batch':batch.relative_to(report).as_posix(), 'scoreSha256':sha(batch/'score.json'),
        'pinSha256':sha(batch/'canonical-pin.json'), 'referenceMode':pin['referenceMode'],
        'canonicalPath':pin['canonicalPath'],'canonicalSha256':pin['canonicalSha256'],
        'document':complete[0], 'criticalRows':score['criticalRows'],
        'mandatoryMissingRows':score['mandatoryMissingRows'], 'wholeSetPercentage':None,
        'finalQualified':False})
rubric = load(evaluation/'fixed-rubric/seal.json')
for mode, suffix, snapshot in (
    ('training-assisted','assisted','e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'),
    ('source-only','source','2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b')):
    entries=[]
    for value in results:
        if value['referenceMode'] != mode:
            continue
        batch = report/value['batch']
        entries.append({'documentId':value['document']['documentId'],'batchPath':str(batch.resolve()),
            'normalizationPath':str((batch/'defect-normalization.json').resolve()),
            'canonicalPath':value['canonicalPath'],'canonicalSha256':value['canonicalSha256'],
            'roundId':batch.name})
    fresh(evaluation/f'selection-{suffix}-partial-r04.json', {
        'schema':'independent-evaluation-batch-selection/1','projectId':'test-project1',
        'profile':'CSharp_ASPNET','referenceMode':mode,'createdAt':created,
        'rubricSha256':rubric['effectiveItemsSha256'],'sourceSnapshotSha256':snapshot,'documents':entries})

scope = {'schema':'reverse-agent-user-scope-change/1','recordedAt':created,
    'userInstruction':'９５％合格時点でSTEOP。',
    'interpretation':'Stop when the eleven contracted ASP.NET documents pass the locked 95-percent evaluation and mandatory verification gates.',
    'deadlineUnchanged':'2026-10-13T20:15:58Z','maximumHoursUnchanged':12,
    'requiredDocuments':11,'overallPercent':95,'eachDocumentPercent':95,'majorCategoryPercent':95,
    'criticalViolations':0,'mandatoryOmissions':0,'unreviewedApplicableRows':0,
    'visualReviewRequiredForScreens':True,
    'stopImmediatelyAfterQualifiedResult':True,'additionalImprovementAfterQualification':False,
    'holdoutGeneralizationAfterPilot':False,'inputSpecificationCreationAfterPilot':False,
    'alreadyPassedDocumentsToBeRewritten':False,'currentQualificationReached':False}
fresh(report/'checkpoints/user-stop-at-95-r01.json',scope)
fresh(report/'checkpoints/status-scores-r04.json', {
    'schema':'reverse-agent-status-checkpoint/1','createdAt':created,'formalDocumentResults':results,
    'wholeSetScore':None,'stopPolicy':'checkpoints/user-stop-at-95-r01.json',
    'rootActualImagesViewed':97,'fourStateScreenDocumentsReviewed':1,'requiredScreenDocuments':4,
    'inputSpecificationsStarted':False,'holdoutGeneralizationStarted':False,'finalQualified':False})
path = report/'run-manifest.json'
manifest = load(path)
fresh(report/'checkpoints/run-manifest-before-stop95-r04.json',manifest)
manifest.update(updatedAt=created,formalScore=None,formalDocumentResults=results,stopPolicy=scope,
    currentFormalGrading={'status':'TEN_DOCUMENT_SCORES_ACCEPTED','formalScore':None,'wholeSetComplete':False,
        'qualified':False,'sourceOnlyCompletedDocuments':4,'trainingAssistedCompletedDocuments':6,
        'trainingAssistedDocumentsAtOrAbove95':4},
    latestProtectedInputVerification='checkpoints/protected-inputs-05.json')
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'acceptedDocuments':len(results),'assistedAtOrAbove95':4,'wholeSetPercentage':None,
    'stopPolicy':scope['interpretation'],'scores':[(r['referenceMode'],r['document']['documentId'],r['document']['percentage']) for r in results]}))
