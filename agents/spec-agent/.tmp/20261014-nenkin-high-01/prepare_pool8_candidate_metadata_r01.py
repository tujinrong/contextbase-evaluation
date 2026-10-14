"""Scheduling candidate and scenario math only; no preparation/run/provider."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).parent
REPORT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
def safe(path):
    path=Path(path).absolute()
    for node in (path,*path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Linked metadata path refused before read/write')
    return path.resolve()
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def load(path):return json.loads(safe(path).read_text(encoding='utf-8-sig'))
def require(value,message):
    if not value:raise ValueError(message)
def write(path,value):
    path=safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
recipe_path=REPORT/'author-run-recipes-r03.json'
ledger_path=REPORT/'author-wave-allocation-ledger-r02.json'
event_path=REPORT/'author-allocation-events/author-wave-01-consumed-r01.json'
grant_path=REPORT/'author-activation-r01.json'
driver=BASE/'nenkin_writer_driver_r04.py'
pins={str(recipe_path):'9054ece76cad4bae6f9d9fd4e9ec80a49d1a92a98cd14eea3296372ef448005d',
      str(ledger_path):'ac9b9ffc605e3146313b7819d5a242f85f1c60575fcd65b748cfa19b1f0cb9ff',
      str(event_path):'1f7474e6b95ab9093d5dbf3922e02730b12f036bbeeaeac222f9a6613e661552',
      str(grant_path):'0c41034171feabc8847ac2f3ba3836ea30a345c0f5f685980f9c9741f4849c27',
      str(driver):'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'}
require(all(sha(path)==expected for path,expected in pins.items()),'Existing immutable scheduling/grant/driver input drift')
recipe,ledger,event=load(recipe_path),load(ledger_path),load(event_path)
require(event['wave']=='author-wave-01' and event['event']=='CONSUMED_FOR_FIRST_PREPARATION' and
        event['ledgerSha256']==pins[str(ledger_path)] and event['activationSha256']==pins[str(grant_path)],'Consumed pilot evidence differs')
candidate_ledger=deepcopy(ledger)
candidate_ledger.update({'schema':'spec-agent-author-wave-allocation-ledger/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'status':'CANDIDATE_PENDING_ROOT_EXTERNAL_POOL_DECISION','previousLedger':str(ledger_path),
    'previousLedgerSha256':pins[str(ledger_path)],'planReviewApproved':True,'activationIssued':True,
    'consumedWaves':1,'consumptionEvents':[{'path':str(event_path),'sha256':pins[str(event_path)]}],
    'candidateExternalPoolMaximum':8,'currentAuthorizedExternalPoolMaximum':4,
    'candidatePoolIncreaseAuthorized':False,'newWavesConsumedByThisCandidate':0})
pilot=candidate_ledger['allocations'][0]
require(pilot['wave']=='author-wave-01' and pilot['documents']==event['allocation']['documents'],'Pilot identity differs')
pilot.update({'status':'CONSUMED_RUNNING_ROOT_OWNED','allocationConsumed':True,'providerStarted':True,
    'consumptionEvent':str(event_path),'consumptionEventSha256':pins[str(event_path)],
    'soleSessionPollingOwner':'root','rootUnifiedSession':27707})
require(all(x.get('workers')==1 for x in candidate_ledger['allocations'][1:]),'Per-document workers changed')
new_ledger_path=REPORT/'author-wave-allocation-ledger-r03-pool8-candidate.json';write(new_ledger_path,candidate_ledger)
candidate_recipe=deepcopy(recipe)
candidate_recipe.update({'createdAt':datetime.now(timezone.utc).isoformat(),
    'status':'CANDIDATE_PENDING_ROOT_EXTERNAL_POOL_DECISION','supersedes':str(recipe_path),
    'supersedesSha256':pins[str(recipe_path)],'planReviewApproved':True,'activationIssued':True,
    'ledger':str(new_ledger_path),'ledgerSha256':sha(new_ledger_path),
    'currentAuthorizedExternalPoolMaximum':4,'candidatePoolIncreaseAuthorized':False,
    'authorPreparationOrRunExecutedByThisCandidate':False})
candidate_recipe['pool'].update({'externalMaximumAuthorDocuments':8,'neverStartBeyondTotalFour':False,
    'neverStartBeyondApprovedExternalMaximum':True,'perMainWaveDocumentCount':1,'perMainWaveWorkers':1,
    'rootSchedulingDecisionRequiredBeforeEight':True,'noMainBeforeClosedApprovedPilot':True})
candidate_recipe['driverConstraints']={'perWaveWorkersMinimum':1,'perWaveWorkersMaximum':4,
    'actualMainWaveWorkers':1,'externalProcessPoolLimitBoundInGrant':False,
    'allocationLedgerOrRecipeInDriverBindingPinnedFiles':False,
    'fixedSourceContextContainsExternalConcurrencyLimit':False,
    'ledgerAndConsumptionAreIndependentSchedulingMetadata':True,
    'stillBound':['exact driver/schema/runtime/cap/context','exact full-plan activation and approved review',
        'selected document IDs','fresh two-digit wave/job/output roots','exact preparation SHA','2400-second provider ceiling','hard user deadline'],
    'evidenceLocations':[{'file':str(driver),'line':278,'meaning':'binding pinnedFiles excludes recipe/ledger/consumption'},
        {'file':str(driver),'line':438,'meaning':'prepare workers 1..4 and wave NN'},
        {'file':str(driver),'line':554,'meaning':'run verifies exact per-wave preparation/workers'},
        {'file':str(driver),'line':661,'meaning':'ThreadPoolExecutor belongs to one run, not shared external processes'}]}
new_recipe_path=REPORT/'author-run-recipes-r04-pool8-candidate.json';write(new_recipe_path,candidate_recipe)
now=datetime.now(timezone.utc);deadline=datetime.fromisoformat('2026-10-14T13:06:43.011844+00:00')
start=datetime.fromisoformat('2026-10-14T04:30:32.446425+00:00')
phase=[]
for folder in ['04edd548dd1bcaaf','f34c471f197e53bf']:
    root=BASE/'jobs/author-wave-01'/folder
    phase.append({'folder':folder,'analysisVerified':safe(root/'analysis-verified.json').exists(),
        'draftResultSaved':safe(root/'draft-result.json').exists(),'independentReviewVerified':safe(root/'independent-review/review-verified.json').exists(),
        'authorResultSaved':safe(root/'author-document-result.json').exists(),'failureSaved':safe(root/'author-failure.json').exists()})
scenarios=[]
remaining=(deadline-now).total_seconds()/60
for pool,rounds in [(4,15),(8,8)]:
    for minutes in (35,60):
        total=rounds*minutes
        scenarios.append({'externalPool':pool,'equalDurationRounds':rounds,'assumedThreePhaseDocumentMinutes':minutes,
            'main58TextMinutes':total,'marginAgainstCurrentRemainingMinutes':round(remaining-total,3),
            'finishIfMainCouldStartImmediately':datetime.fromtimestamp(now.timestamp()+total*60,timezone.utc).isoformat(),
            'scenarioOnlyNotObservedCompletionForecast':True,
            'excludes':['unfinished pilot tail','reserved index and 2 analysis reports','revisions/retries','native conversion/QA','startup/queue overhead']})
risk={'schema':'spec-agent-author-timing-risk/1','observedAt':now.isoformat(),'deadline':deadline.isoformat(),
    'analysisStartedAt':start.isoformat(),'observedElapsedAnalysisMinutes':round((now-start).total_seconds()/60,3),
    'remainingRunMinutes':round(remaining,3),'phases':phase,'pilotTotalDocumentDurationMeasured':False,
    'draftAndReviewDurationUnknown':True,'mainDocumentKindsHaveDifferentExpectedWorkSizes':True,
    'scenarioInputsProvidedByRootNotMeasurements':[35,60],'scenarios':scenarios,
    'interpretation':'At pool4 both assumed scenarios exceed remaining time even before pilot tail and delivery. Pool8 reduces text queue length but the 60-minute scenario has little or no headroom after excluded work; completion is not guaranteed.',
    'candidateRecipe':str(new_recipe_path),'candidateRecipeSha256':sha(new_recipe_path),
    'candidateLedger':str(new_ledger_path),'candidateLedgerSha256':sha(new_ledger_path),
    'actualCurrentAuthorizedExternalPool':4,'actualActivePilotDocuments':2,'actualActiveMainDocuments':0,
    'poolIncreaseAuthorizedOrExecuted':False,'duplicatePilotStarted':False,
    'sourceOrScopeOrCoreOrPromptOrGrantChanged':False,'published':False}
risk_path=REPORT/'author-timing-risk-r01.json';write(risk_path,risk)
require(all(sha(path)==expected for path,expected in pins.items()),'Immutable inputs changed during metadata candidate preparation')
print(json.dumps({'recipe':str(new_recipe_path),'recipeSha256':sha(new_recipe_path),'ledger':str(new_ledger_path),
    'ledgerSha256':sha(new_ledger_path),'risk':str(risk_path),'riskSha256':sha(risk_path),
    'observedAt':risk['observedAt'],'analysisMinutes':risk['observedElapsedAnalysisMinutes'],
    'remainingMinutes':risk['remainingRunMinutes'],'phases':phase,'providerCallsStarted':0},ensure_ascii=False))
