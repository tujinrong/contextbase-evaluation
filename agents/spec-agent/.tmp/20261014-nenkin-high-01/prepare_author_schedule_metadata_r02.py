"""Metadata-only scheduling; reads verified plan metadata, launches no provider."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
BASE=Path(__file__).parent
REPORT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
DRIVER=BASE/'nenkin_writer_driver_r04.py'
PLAN=BASE/'jobs/plan-03/plan-verified.json'
PLAN_SHA='f302f6d345e87add5a9ac4ef6b0d19f9708dfcb9bdd3c92e3d411795e9d8146d'
functions={'require','safe','raw','digest','sha','pairs','load'}
tree=ast.parse(DRIVER.read_text(encoding='utf-8'))
env={'Path':Path,'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions],type_ignores=[]),str(DRIVER),'exec'),env)
require=env['require'];load=env['load'];sha=env['sha'];safe=env['safe']
require(sha(DRIVER)=='ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664','Audited driver drift')
require(sha(PLAN)==PLAN_SHA,'Verified scheduling plan drift')
docs=[{k:d[k] for k in ('id','kind','path')} for d in load(PLAN)['documents']]
require(len(docs)==63 and len({d['id'] for d in docs})==63,'Expected unique verified plan IDs')
definitions={d['id']:d for d in docs}
pilot_ids=['SCR-013','SCR-017']
require([(definitions[x]['kind'],definitions[x]['path']) for x in pilot_ids]==
        [('basic-design','basic/login.md'),('basic-design','basic/menu.md')],'Pilot exact plan identity drift')
reports=[d['id'] for d in docs if d['kind']=='analysis-report']
require(reports==['ANL-COVERAGE','ANL-TRACEABILITY'] and definitions['IDX-NENKIN']['kind']=='index','Deferred role identities drift')
deferred=['IDX-NENKIN',*reports]
main=[d for d in docs if d['id'] not in set(pilot_ids+deferred)]
require(len(main)==58 and sum(d['kind']!='analysis-report' for d in docs)==61,'Scheduling count differs')
allocations=[]
def allocate(number,ids,phase,workers,depends):
    wave='author-wave-'+f'{number:02d}'
    allocations.append({'wave':wave,'documents':[definitions[x] for x in ids],'phase':phase,'workers':workers,
        'documentConcurrencyUnits':min(workers,len(ids)),'dependsOn':depends,
        'status':'RESERVED_PENDING_ACTIVATION','allocationConsumed':False,
        'jobsRoot':str(safe(BASE/'jobs'/wave)),'draftsRoot':str(safe(BASE/'drafts'/wave)),
        'preparation':str(safe(REPORT/'author-preparation'/wave/'preparation.json')),
        'reportTextPinsRoot':str(safe(REPORT/'text-pins'/wave)),
        'providerStarted':False})
allocate(1,pilot_ids,'pilot',2,['exact-root-activation-and-new-scoped-plan-review-approved'])
for number,doc in enumerate(main,2):
    allocate(number,[doc['id']],'main-specification',1,['pilot-wave-closed-input-unchanged-duration-recorded'])
for number,identity in enumerate(deferred,60):
    allocate(number,[identity],'deferred-index' if identity=='IDX-NENKIN' else 'deferred-analysis-report',1,
        ['main-specification-text-evidence-available','root-derived-delivery-metadata-available'])
for number in range(63,100):
    allocations.append({'wave':'author-wave-'+f'{number:02d}','phase':'revision-or-unstarted-retry-reserve',
        'documents':[],'workers':1,'documentConcurrencyUnits':1,'status':'UNASSIGNED_RESERVE',
        'allocationConsumed':False,'providerStarted':False})
ledger={'schema':'spec-agent-author-wave-allocation-ledger/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'plan':str(safe(PLAN)),'planSha256':PLAN_SHA,'planReviewApproved':False,'activationIssued':False,
    'status':'METADATA_RESERVATIONS_ONLY','maximumWaveNumber':99,'reservedInitialWaves':62,
    'revisionOrRetryWaveCapacity':37,'consumedWaves':0,'allocations':allocations,
    'allocationRule':'Before the first prepare attempt, commit a fresh allocation event. Never reuse attempted wave roots; retries and revisions consume the next unused reserved number. Record every event in a fresh immutable ledger receipt.',
    'rootOwnsCollectionRenderPublication':True,'providerCalls':0,'actualAuthorPreparationExecuted':False,
    'businessSourceOrDraftBodyRead':False,'businessProseAssembledByPython':False}
ledger_path=safe(REPORT/'author-wave-allocation-ledger-r01.json')
def write_metadata(path,value):
    path=safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
write_metadata(ledger_path,ledger)
recipe={'schema':'spec-agent-author-run-recipes/2','createdAt':datetime.now(timezone.utc).isoformat(),
    'status':'READY_NOT_ACTIVATED','role':'AG-SPEC','projectId':'nenkin','mode':'source-only',
    'supersedes':str(safe(REPORT/'author-run-recipes-r01.json')),'supersedesSha256':sha(REPORT/'author-run-recipes-r01.json'),
    'driver':str(safe(DRIVER)),'driverSha256':sha(DRIVER),'driverOrFrozenRuntimeModified':False,
    'plan':str(safe(PLAN)),'planSha256':PLAN_SHA,'planReviewApproved':False,'activationIssued':False,
    'deadline':'2026-10-14T13:06:43.011844+00:00','modelSelection':'user-configured-default-no-override',
    'specificationCount':61,'analysisReportCount':2,'pilotIds':pilot_ids,'mainIds':[d['id'] for d in main],
    'deferredIds':deferred,'mainOrdering':'exact verified plan order with pilot and deferred IDs removed',
    'ledger':str(ledger_path),'ledgerSha256':sha(ledger_path),
    'activationRequirements':['exact root-issued all-plan grant SHA','actual independently approved new scoped review',
        'actual approved plan tuple set equals this scheduling plan','successful audited driver binding and prepare'],
    'pool':{'pilotWorkers':2,'pilotMustCloseBeforeMainPool':True,'perMainWaveDocumentCount':1,
        'perMainWaveWorkers':1,'externalMaximumAuthorDocuments':4,'countUnit':'active document, not wave or shell process',
        'neverStartBeyondTotalFour':True,'deadlineCheckedBeforeEveryFreshStage':True},
    'prepareArgvTemplate':['prepare','--activation','${ROOT_GRANT_PATH}','--activation-sha256','${ROOT_GRANT_SHA256}',
        '--wave','${FRESH_RESERVED_WAVE}','${REPEATED_DOCUMENT_ID_ARGUMENTS_FOR_EXACT_WAVE}',
        '--workers','${TWO_FOR_PILOT_ELSE_ONE}','--timeout','2400'],
    'runArgvTemplate':['run','--preparation','${RETURNED_PREPARATION_PATH}','--preparation-sha256','${RETURNED_PREPARATION_SHA256}'],
    'revisionArgvExtra':['--revision-from','${SAME_RUN_AUTHOR_DOCUMENT_RESULT}','${EXACT_RESULT_SHA256}'],
    'revisionAnalysisFresh':True,
    'closedWaveChecks':['author-inputs-after status UNCHANGED and exact preparation/input binding',
        'author-wave-result input/preparation match, waveIntegrityVerified true and exact inputsAfter SHA',
        'selected document result TEXT_REVIEW_APPROVED and exact returned report pin path/SHA',
        'pin canonical/draft-result/raw independent review/structure/runtime/capsule SHA unchanged'],
    'rootNotificationFields':['documentId','path','kind','canonicalMarkdown','sha256','draftResult','draftResultSha256',
        'independentReview','independentReviewSha256','textPin','textPinSha256','waveResult','waveResultSha256',
        'waveInputsAfter','waveInputsAfterSha256','preparationSha256','capsule','runtime','structureStatus','elapsedSeconds'],
    'afterEachClosedWave':'Report its exact pin and wave SHAs immediately, release its one pool slot, and start the next permitted fresh wave while root overlaps collection/render/native QA.',
    'failedOrRejectedWave':'Keep all original AI artifacts and failure evidence; no text completion claim. Use another unused wave for source-backed revision or retry.',
    'deferredGate':{'indexAndReportsWaitForMainSpecificationsAndRootDeliveryMetadata':True,
        'deliveryMetadataActuallyProvidedToAuthor':False,
        'existingR04InitialRevisionContextOnlyFixedExecutionContext':True,
        'ifActualDeliveryMetadataMustEnterAIText':'Root must specify a separately audited typed metadata presentation route; no inventing actual results and no Python business-body assembly.'},
    'analysisReportsFinalOutputSpecificationBundleIncluded':False,'analysisReportsFinalExcelCountIncluded':False,
    'rootOwnsCollectionRenderPublication':True,'partialClosedSuccessCanBeStaged':True,
    'overallFinalBundleRequiresAllApprovedSpecificationIdsAndRequiredIndependentQA':True,
    'sourceReadmeStatementsObservedDeclarationsNotRuntimeProof':True,'formalPercentageInherited':False,
    'providerCalls':0,'originalApplicationOrDatabaseExecuted':False,'oldBusinessProseOrExpectedReused':False,
    'businessProseAssembledByPython':False,'published':False}
require(sha(PLAN)==PLAN_SHA and sha(DRIVER)==recipe['driverSha256'],'Fixed metadata drift during scheduling')
recipe_path=safe(REPORT/'author-run-recipes-r02.json');write_metadata(recipe_path,recipe)
print(json.dumps({'recipe':str(recipe_path),'recipeSha256':sha(recipe_path),'ledger':str(ledger_path),
    'ledgerSha256':sha(ledger_path),'pilot':pilot_ids,'mainCount':len(main),'deferred':deferred,
    'initialReservedWaves':62,'revisionReserve':37,'providerCalls':0},ensure_ascii=False))
