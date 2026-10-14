"""Bounded pure metadata probes. No production activation, frozen imports or providers."""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps')
from jsonschema import Draft202012Validator
import jsonschema
assert Path(jsonschema.__file__).resolve().is_relative_to(Path(sys.path[0]).resolve())
ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
DRIVER = ROOT / 'nenkin_writer_driver_r05.py'
EXPECTED = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
TOY = REPORT / 'independent-audit/writer-metadata-r05-toy-r02'
OUT = REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r02.json'
assert hashlib.sha256(DRIVER.read_bytes()).hexdigest() == EXPECTED
assert not TOY.exists() and not OUT.exists()
spec = importlib.util.spec_from_file_location('new_metadata_driver_only', DRIVER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
actual_schemas = dict(m.METADATA_SCHEMAS)
results = []

def emit(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def fixture(index):
    m.WORK = TOY / str(index) / 'work'
    m.REPORT = TOY / str(index) / 'report'
    identity = {'runId': '20261014-nenkin-high-01', 'projectId': 'nenkin',
        'capsuleManifestSha256': 'a'*64, 'executionContextSha256': 'b'*64, 'planSha256': 'c'*64,
        'sourceOnly': True, 'businessEvidenceAuthority': False, 'originalAppExecuted': False,
        'originalSpecificationsAuthorized': False, 'evaluationExpectationsAuthorized': False,
        'newSourceReadPermissions': False}
    plan = {'documents': [{'id': 'INDEX', 'kind': 'index', 'path': 'index.md'},
        {'id': 'REPORT', 'kind': 'analysis-report', 'path': 'analysis/report.md'},
        {'id': 'BASIC', 'kind': 'basic-design', 'path': 'basic/a.md'}]}
    docs = [{'documentId': 'INDEX', 'kind': 'index', 'path': 'index.md'},
        {'documentId': 'REPORT', 'kind': 'analysis-report', 'path': 'analysis/report.md'}]
    route = {'schema': 'spec-agent-same-run-routing-record/1', **identity,
        'formalPercentage': None, 'published': False, 'documents': [
            {**docs[0], 'disposition': 'specification', 'locations': [
                {'scope': 'specification-bundle', 'format': 'md', 'relativePath': 'md/index.md'}]},
            {**docs[1], 'disposition': 'report-only', 'locations': [
                {'scope': 'execution-report', 'format': 'md', 'relativePath': 'analysis/report.md'}]}]}
    evidence_path = m.REPORT / 'audit-record.json'
    emit(evidence_path, {'schema': 'toy-evidence-only/1', 'declaredStatus': 'RECORDED', 'actualQualification': False})
    completion = {'schema': 'spec-agent-same-run-completion-record/1', **identity,
        'formalPercentage': None, 'published': False, 'documents': [
            {**docs[0], 'recordStatus': 'RECORDED', 'evidence': [
                {'path': str(evidence_path), 'sha256': m.sha(evidence_path)}]},
            {**docs[1], 'recordStatus': 'NOT_RUN', 'evidence': []}]}
    path = m.WORK / 'execution-metadata/supplement.json'
    route_path = m.REPORT / 'execution-metadata/routing.json'
    completion_path = m.REPORT / 'execution-metadata/completion.json'
    supplement = {'schema': 'spec-agent-same-run-execution-metadata/1', **identity, 'documents': docs,
        'records': [{'kind': 'routing', 'path': str(route_path), 'sha256': '0'*64},
            {'kind': 'completion', 'path': str(completion_path), 'sha256': '0'*64}]}
    pin = {'snapshot': {'manifestSha256': 'a'*64, 'mode': 'source-only'},
        'executionContextSha256': 'b'*64, 'planSha256': 'c'*64, 'pinnedFiles': {}}
    return {'pin': pin, 'plan': plan, 'supplement': supplement, 'route': route,
        'completion': completion, 'path': path, 'routePath': route_path,
        'completionPath': completion_path, 'evidencePath': evidence_path}

def build(f, *, invalid_supplement_hash=False, invalid_route_hash=False):
    emit(f['routePath'], f['route'])
    emit(f['completionPath'], f['completion'])
    f['supplement']['records'][0]['sha256'] = 'd'*64 if invalid_route_hash else m.sha(f['routePath'])
    f['supplement']['records'][1]['sha256'] = m.sha(f['completionPath'])
    emit(f['path'], f['supplement'])
    return m.with_execution_metadata(f['pin'], f['plan'], f['path'],
        'e'*64 if invalid_supplement_hash else m.sha(f['path']))

def run(name, expected, alter=None, operation=None, **build_options):
    f = fixture(len(results)+1)
    try:
        if alter:
            alter(f)
        bound = build(f, **build_options)
        if operation:
            operation(f, bound)
        result = 'ACCEPTED'
        detail = None
    except (ModuleNotFoundError, ImportError):
        raise
    except Exception as exc:
        result = 'REJECTED'
        detail = {'type': type(exc).__name__, 'message': str(exc).splitlines()[0]}
    results.append({'name': name, 'expected': expected, 'actual': result, 'passed': result == expected, 'detail': detail})

run('typed index and report metadata accepted; business authority false', 'ACCEPTED')
for field, value in [('projectId','other'), ('runId','other'), ('capsuleManifestSha256','d'*64),
        ('executionContextSha256','d'*64), ('planSha256','d'*64), ('sourceOnly',False),
        ('businessEvidenceAuthority',True), ('originalAppExecuted',True),
        ('originalSpecificationsAuthorized',True), ('evaluationExpectationsAuthorized',True),
        ('newSourceReadPermissions',True)]:
    run('supplement ' + field + ' drift refused', 'REJECTED', lambda f, k=field,v=value: f['supplement'].__setitem__(k,v))
run('supplement raw SHA drift refused', 'REJECTED', invalid_supplement_hash=True)
run('referenced record SHA drift refused', 'REJECTED', invalid_route_hash=True)
run('routing cap identity drift refused', 'REJECTED', lambda f: f['route'].__setitem__('capsuleManifestSha256', 'd'*64))
run('completion context identity drift refused', 'REJECTED', lambda f: f['completion'].__setitem__('executionContextSha256','d'*64))
run('business specification supplemental target refused', 'REJECTED', lambda f: f['supplement']['documents'].__setitem__(0,
    {'documentId':'BASIC','kind':'basic-design','path':'basic/a.md'}))
run('unknown target ID refused', 'REJECTED', lambda f: f['supplement']['documents'][0].__setitem__('documentId','MISSING'))
run('target plan path drift refused', 'REJECTED', lambda f: f['supplement']['documents'][0].__setitem__('path','index-other.md'))
run('target kind drift refused', 'REJECTED', lambda f: f['supplement']['documents'][0].__setitem__('kind','analysis-report'))
run('duplicate target IDs refused', 'REJECTED', lambda f: f['supplement']['documents'].__setitem__(1,dict(f['supplement']['documents'][0])))
run('extra prose member refused by strict schema', 'REJECTED', lambda f: f['supplement'].__setitem__('businessProse','untrusted toy content'))
run('supplement outside execution metadata region refused', 'REJECTED', lambda f: f.__setitem__('path',m.WORK / 'misc/supplement.json'))
run('routing record outside owned region refused', 'REJECTED', lambda f: f.__setitem__('routePath',TOY / 'external/routing.json'))
run('analysis report in specification bundle refused', 'REJECTED', lambda f: f['route']['documents'][1]['locations'][0].__setitem__('scope','specification-bundle'))
run('report disposition mismatch refused', 'REJECTED', lambda f: f['route']['documents'][1].__setitem__('disposition','specification'))
run('parent traversal route refused', 'REJECTED', lambda f: f['route']['documents'][0]['locations'][0].__setitem__('relativePath','../index.md'))
run('routing path extension mismatch refused', 'REJECTED', lambda f: f['route']['documents'][0]['locations'][0].__setitem__('relativePath','md/index.pdf'))
run('recorded completion without evidence refused', 'REJECTED', lambda f: f['completion']['documents'][0].__setitem__('evidence',[]))
run('completion evidence SHA drift refused', 'REJECTED', lambda f: f['completion']['documents'][0]['evidence'][0].__setitem__('sha256','d'*64))
run('completion evidence outside owned roots refused', 'REJECTED', lambda f: f['completion']['documents'][0]['evidence'][0].__setitem__('path',str(TOY / 'external/evidence.json')))
run('completion evidence inside capsule refused', 'REJECTED', lambda f: f['completion']['documents'][0]['evidence'][0].__setitem__('path',str(m.WORK / 'snapshot-input-02/manifest.json')))
run('formal percentage declaration refused', 'REJECTED', lambda f: f['completion'].__setitem__('formalPercentage',95))
run('published declaration refused', 'REJECTED', lambda f: f['route'].__setitem__('published',True))
run('metadata wave exact IDs accepted', 'ACCEPTED', operation=lambda f,b: m.metadata_selection(b,f['plan'],['INDEX','REPORT']))
run('metadata wave subset IDs refused', 'REJECTED', operation=lambda f,b: m.metadata_selection(b,f['plan'],['INDEX']))
run('metadata wave includes business ID refused', 'REJECTED', operation=lambda f,b: m.metadata_selection(b,f['plan'],['INDEX','REPORT','BASIC']))

def exact_context(f,b):
    original = {'schema':'toy-original-context/1','sourceOnly':True,'nested':{'scope':['a','b']}}
    before = json.dumps(original,sort_keys=True)
    combined = m.metadata_revision_context(original,original,b)
    assert combined['executionContext'] is original and json.dumps(original,sort_keys=True) == before
    assert combined['sameRunExecutionMetadata'] == b['executionMetadata']['context']
    assert m.metadata_provenance(b)['atomicOrRaceFreeProof'] is False
    assert m.metadata_provenance(b)['internalAnalysisDraftCallbackChecksPerformed'] is False
    revised = {'executionContext':original,'previousCanonicalMarkdown':'full\r\nMarkdown\r\n',
        'preservedIndependentReviewRawResponse':'{\r\n  "approved": false\r\n}\r\n'}
    combined_revision = m.metadata_revision_context(revised,original,b)
    assert combined_revision['previousCanonicalMarkdown'] == revised['previousCanonicalMarkdown']
    assert combined_revision['preservedIndependentReviewRawResponse'] == revised['preservedIndependentReviewRawResponse']
    assert 'sameRunExecutionMetadata' not in revised

run('original full context and exact current draft/raw-review bytes preserved', 'ACCEPTED', operation=exact_context)
run('revision context replacement refused', 'REJECTED', operation=lambda f,b: m.metadata_revision_context({'executionContext':{}},{'a':1},b))
run('existing supplement member overwrite refused', 'REJECTED', operation=lambda f,b: m.metadata_revision_context(
    {'executionContext':{'a':1},'sameRunExecutionMetadata':{}},{'a':1},b))

def absent_function_ast():
    base = ast.parse((ROOT / 'nenkin_writer_driver_r04.py').read_text(encoding='utf-8'))
    new = ast.parse(DRIVER.read_text(encoding='utf-8'))
    previous = {n.name:ast.dump(n,include_attributes=False) for n in base.body if isinstance(n,ast.FunctionDef)}
    current = {n.name:ast.dump(n,include_attributes=False) for n in new.body if isinstance(n,ast.FunctionDef)}
    changed = sorted(k for k in previous if previous[k] != current[k])
    assert changed == ['main','prepare','previous_revision','recheck','run','scoped_review','text_pin']
    critical = ['binding','bootstrap','fixed_grant','provider_evidence','module_pin','safe','inside','inventory']
    assert all(previous[k] == current[k] for k in critical)
    calls = [n for n in ast.walk(new) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
        and isinstance(n.func.value,ast.Name) and n.func.value.id == 'workflow' and n.func.attr == 'document']
    assert len(calls) == 1
    return {'changedExistingFunctions':changed,'criticalFrozenBindingFunctionsASTUnchanged':critical,
        'frozenWorkflowDocumentCallCount':1,'internalOrchestrationReimplemented':False}

ast_evidence = absent_function_ast()
assert hashlib.sha256(DRIVER.read_bytes()).hexdigest() == EXPECTED
report = {'schema':'spec-agent-writer-metadata-bounded-probes/1','status':'PASS' if all(r['passed'] for r in results) else 'FAILED',
    'driver':str(DRIVER),'driverSha256':EXPECTED,'probeCount':len(results),'passed':sum(r['passed'] for r in results),
    'probes':results,'astEvidence':ast_evidence,'fixtureScope':'synthetic owned metadata only',
    'actualActivationBindingVerified':False,'actualPreviousProviderArtifactsVerified':False,
    'actualGenerationExecuted':False,'actualIndependentReviewExecuted':False,'actualNativeOrFormalQualification':False,
    'frozenCoreOrLoadedPromptModified':False,'providerStarts':0,
    'jsonschemaImportedFrom':str(Path(jsonschema.__file__).resolve()),
    'jsonschemaImportSha256':hashlib.sha256(Path(jsonschema.__file__).read_bytes()).hexdigest(),
    'priorProbeInvalidated':'r01 was an invalid -I dependency environment; all negative results there were import failures, not behavioral validation',
    'verificationBoundaryClaim':'Composite generation and separate review before/after, final pin and wave completion only; no internal analysis/draft callback or atomic/race-free proof'}
emit(OUT,report)
print(json.dumps({'status':report['status'],'probeCount':report['probeCount'],'passed':report['passed'],'report':str(OUT),
    'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'providerStarts':0},ensure_ascii=False))
if report['status'] != 'PASS':
    sys.exit(1)
