"""A config-selected fresh AI cycle; no application-specific prose or rules."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import shutil
import sys

agent = Path(__file__).resolve().parents[2]
repo = agent.parents[1]
config_path = Path(sys.argv[1]).resolve()
config_data = config_path.read_bytes()
config = json.loads(config_data.decode('utf-8'))
def digest(data):
    return hashlib.sha256(data).hexdigest()
def local(key):
    value = (repo / config[key]).resolve()
    if repo not in value.parents:
        raise ValueError('Run paths must stay within the selected repository')
    return value
snapshot, plan = local('snapshot'), local('plan')
jobs, output, report = local('jobs'), local('output'), local('report')
previous, feedback, visual, text_jobs = (local(key) for key in ('previousOutput','feedback','visual','previousJobs'))
if jobs.exists() or output.exists() or report.exists():
    raise FileExistsError('Fresh job/output/report roots required')
plan_data = plan.read_bytes()
plan_value = json.loads(plan_data.decode('utf-8'))
selected = config['documents']
if not selected or len(set(selected)) != len(selected):
    raise ValueError('Explicit unique document selection required')
workers = config.get('workers',2)
if type(workers) is not int or not 1 <= workers <= 4:
    raise ValueError('One to four explicitly configured workers required')
deadline = datetime.fromisoformat(config['deadline'].replace('Z','+00:00'))
if deadline.tzinfo is None or (deadline - datetime.now(timezone.utc)).total_seconds() <= 60:
    raise RuntimeError('No new AI job at or after the deadline')
inputs = []
prepared = {}
def read_pin(path):
    data = path.read_bytes()
    inputs.append({'path':path.relative_to(repo).as_posix(),'sha256':digest(data)})
    return json.loads(data.decode('utf-8'))
for identity in selected:
    definitions = [d for d in plan_value['documents'] if d['id'] == identity]
    if len(definitions) != 1 or definitions[0]['kind'] == 'analysis-report':
        raise ValueError('One planned publication document required')
    definition = definitions[0]
    source = (previous / definition['path']).resolve()
    if previous not in source.parents:
        raise ValueError('Previous document path escapes its output root')
    data = source.read_bytes()
    inputs.append({'path':source.relative_to(repo).as_posix(),'sha256':digest(data)})
    stem = Path(definition['path']).stem
    safe_feedback = read_pin(feedback / (stem + '-feedback.json'))
    visual_review = read_pin(visual / (stem + '-review.json'))
    text_review = read_pin(text_jobs / digest(identity.encode())[:16] / 'independent-review/review-verified.json')
    addenda = []
    for relative in config.get('sourceReviewAddenda',{}).get(identity,[]):
        addendum_path = (repo/relative).resolve()
        if (repo not in addendum_path.parents or
                any(part.casefold() in {'spec-eval','evaluator-only'} for part in addendum_path.parts)):
            raise ValueError('Protected or out-of-scope review addendum refused')
        addendum = read_pin(addendum_path)
        if addendum.get('documentId') != identity:
            raise ValueError('Review addendum identity mismatch')
        addenda.append(addendum)
    if safe_feedback.get('classification') not in {'GENERATOR_SAFE_SOURCE_FEEDBACK','WRITER_SAFE_SOURCE_ONLY'}:
        raise ValueError('Only explicitly classified source-backed feedback is permitted')
    if (safe_feedback.get('reviewDocumentId') != identity or
            visual_review.get('documentId') != identity or text_review.get('documentId') != identity):
        raise ValueError('Feedback/review identity mismatch')
    prepared[identity] = {'previousDraft':data.decode('utf-8'),'previousDraftSha256':digest(data),
        'previousSourceBackedFeedback':safe_feedback,'previousNativeVisualSourceReview':visual_review,
        'previousTextSourceReview':text_review,'requestedRevision':config['revision'],
        'sourceBackedReviewAddenda':addenda,
        'freshAnalysisInstruction':'前稿と批評を正解期待値にせず、固定した原ソースと許可された参考設計を新しく解析します。修正済みの根拠付き情報を維持し、図と本文の条件・結果も相互照合します。本文はAIが再執筆し、Pythonによる本文差替えは行いません。'}

# All source-backed inputs exist before creating a run or starting any AI call.
if plan.read_bytes() != plan_data:
    raise ValueError('Plan changed during source-backed input preparation')
runtime = jobs / 'runtime-code'
runtime_pins = []
for source in [agent/'src/contextbase/__init__.py',*sorted((agent/'src/contextbase/ai').glob('*.py'))]:
    target = runtime / source.relative_to(agent/'src')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    runtime_pins.append({'sourcePath':source.relative_to(repo).as_posix(),
                         'runtimePath':target.relative_to(jobs).as_posix(),'sha256':digest(target.read_bytes())})
shutil.copyfile(Path(__file__),jobs/'runner-source.py')
sys.path.insert(0,str(runtime))
from contextbase.ai import capsule, workflow
from contextbase.ai.validation import validate_document
state = capsule.verification_state(snapshot)
definitions = {identity:workflow.select_document(plan,identity) for identity in selected}
for definition in definitions.values():
    workflow._definition_state(snapshot,definition)
capsule.write_json(report/'scope.json',{'projectId':config['projectId'],'profile':config['profile'],
    'startedAt':datetime.now(timezone.utc).isoformat(),'deadline':config['deadline'],
    'snapshot':state,'inputMode':state['mode'],'documents':selected,'planSha256':digest(plan_data),
    'configPath':config_path.relative_to(repo).as_posix(),'configSha256':digest(config_data),
    'runnerSha256':digest(Path(__file__).read_bytes()),'runtimeFrozenAtLaunch':True,
    'preservedRunnerPath':(jobs/'runner-source.py').relative_to(repo).as_posix(),
    'runtimeFiles':runtime_pins,'inputPins':inputs,'freshAnalysisRequired':True,
    'expectedAnswersProvided':False,'semanticProseAssembledByPython':False})

def task(identity):
    definition = definitions[identity]
    folder = digest(identity.encode())[:16]
    context = prepared[identity]
    context['structuralFindings'] = validate_document(context['previousDraft'],definition['path'],expected_document_id=identity)
    capsule.write_json(jobs/(folder+'-revision-context.json'),context)
    try:
        draft = workflow.document(snapshot,definition,jobs/folder,output,
            timeout=config.get('timeout',1800),deadline=config['deadline'],revision_context=context)
        capsule.write_json(report/'progress'/(folder+'-draft.json'),draft)
        try:
            review = workflow.review(snapshot,output/definition['path'],definition,
                jobs/folder/'independent-review',timeout=config.get('timeout',1800),deadline=config['deadline'])
            accepted = review['approved'] and not draft['structureFindings']
        except workflow.ReviewStructureConflict as exc:
            review,accepted = exc.answer,False
        result = {'documentId':identity,'draft':draft,'review':review,
            'status':'TEXT_SOURCE_REVIEW_APPROVED_AWAITING_VISUAL_AND_GRADING' if accepted else 'REQUIRES_AI_REVISION',
            'reviewScope':'text-source-and-structure','visualFidelityVerified':False,'formalSemanticScore':None}
    except Exception as exc:
        result = {'documentId':identity,'status':'FAILED','errorType':type(exc).__name__,'error':str(exc),
                  'visualFidelityVerified':False,'formalSemanticScore':None}
    capsule.write_json(report/'progress'/(folder+'.json'),result)
    print(json.dumps({'documentId':identity,'status':result['status']},ensure_ascii=False),flush=True)
    return result
with ThreadPoolExecutor(max_workers=workers) as pool:
    results = [future.result() for future in as_completed([pool.submit(task,identity) for identity in selected])]
input_drift = [pin['path'] for pin in inputs if digest((repo/pin['path']).read_bytes()) != pin['sha256']]
runtime_drift = [pin['runtimePath'] for pin in runtime_pins if digest((jobs/pin['runtimePath']).read_bytes()) != pin['sha256']]
capsule.write_json(report/'results.json',{'documents':results,'inputDrift':input_drift,'runtimeDrift':runtime_drift,
    'runtimeFrozenAtLaunch':True,'freshAnalysisInEachDocument':True,'semanticProseAssembledByPython':False,
    'formallyEvaluated':False,'visualFidelityVerified':False})
