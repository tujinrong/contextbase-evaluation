"""Independent technical probes: AST-extracted collector functions, own memory stubs.
No module import of collector, writer, provenance helper, or frozen pipeline.
No real source, author records, provider, business Markdown, or delivery IO.
"""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from collections import Counter
import ast, copy, hashlib, json

ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK = ROOT / '.tmp/20261014-nenkin-high-01'
AUDIT = ROOT / 'report/20261014-nenkin-high-01/independent-audit'
CANDIDATE = WORK / 'collect_reviewed_r09.py'
BASELINE = WORK / 'collect_reviewed_r08.py'
EXPECTED = '3788d437323b5db059a3afd908d7ba0dbd3b1dcd3ec7395502fe77e95c3392bc'
BASE_EXPECTED = '2848e50ff84671608dfada5dece254ec15e80afe0ae55df5de41cf22abf345e3'
def digest(data):
    return hashlib.sha256(data).hexdigest()
candidate_bytes, baseline_bytes = CANDIDATE.read_bytes(), BASELINE.read_bytes()
assert digest(candidate_bytes) == EXPECTED
assert digest(baseline_bytes) == BASE_EXPECTED
candidate = ast.parse(candidate_bytes)
baseline = ast.parse(baseline_bytes)
names = {'require', 'bind_optional_metadata', 'prompt_metadata_object', 'metadata_prompt_binding'}
nodes = [node for node in candidate.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names
constants = {}
for node in candidate.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if isinstance(node.value, ast.Constant) and node.targets[0].id.startswith(('METADATA_', 'DRAFT_', 'REVIEW_')):
            constants[node.targets[0].id] = ast.literal_eval(node.value)
results = []
def test(name, fn, rejects=False):
    try:
        fn()
    except (ValueError, KeyError, TypeError, AssertionError, json.JSONDecodeError) as exc:
        results.append({'name': name, 'passed': rejects, 'rejectionType': type(exc).__name__})
    else:
        results.append({'name': name, 'passed': not rejects})

# All baseline require calls must survive unchanged in the candidate AST.
def require_calls(tree):
    return Counter(ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'require')
old_calls, new_calls = require_calls(baseline), require_calls(candidate)
test('all baseline require expressions retained', lambda: (_ for _ in ()).throw(AssertionError()) if old_calls - new_calls else None)
old_functions = {node.name: node for node in baseline.body if isinstance(node, ast.FunctionDef) and node.name != 'main'}
new_functions = {node.name: node for node in candidate.body if isinstance(node, ast.FunctionDef)}
test('all baseline non-main functions byte-independent AST identical', lambda: all(
    ast.dump(node, include_attributes=False) == ast.dump(new_functions[name], include_attributes=False)
    for name, node in old_functions.items()) or (_ for _ in ()).throw(AssertionError()))

writer_path = PurePosixPath('/owned/nenkin_writer_driver_r05.py')
context = {'schema': 'synthetic-context/1', 'sourceOnly': True, 'scope': ['owned-input']}
metadata_context = {'schema': 'synthetic-metadata-context/1', 'policy': 'no business evidence', 'referencedRecords': [{'recordStatus': 'NOT_RUN'}]}
plan = {'documents': [{'id': 'INDEX', 'kind': 'index', 'path': 'index.md'}, {'id': 'REPORT', 'kind': 'analysis-report', 'path': 'analysis/report.md'}]}
definition = copy.deepcopy(plan['documents'][0])
base = {'grant': '/owned/report/grant.json', 'grantSha256': 'a' * 64, 'pinnedFiles': {'/owned/base.json': 'b' * 64}, 'snapshot': {'mode': 'source-only'}}
metadata = {'supplement': {'path': '/owned/execution-metadata/supplement.json', 'sha256': 'c' * 64},
            'context': metadata_context, 'contextSha256': 'd' * 64, 'documentIds': ['INDEX', 'REPORT'],
            'pinnedFiles': {'/owned/execution-metadata/supplement.json': 'c' * 64, '/owned/evidence.json': 'e' * 64},
            'businessEvidenceAuthority': False, 'newSourceReadPermissions': False,
            'internalAnalysisDraftCallbackChecksPerformed': False, 'atomicOrRaceFreeProof': False}
composite = copy.deepcopy(base)
composite['pinnedFiles'].update(metadata['pinnedFiles'])
composite['executionMetadata'] = copy.deepcopy(metadata)
provenance = {key: value for key, value in metadata.items() if key != 'context'}
prep = {'helper': str(writer_path), 'helperSha256': constants['METADATA_WRITER_SHA'], 'documents': ['INDEX', 'REPORT']}
grant = {'driverSha256': constants['METADATA_WRITER_SHA']}
class MemoryWriter:
    METADATA_REVIEW_MARKER = constants['METADATA_REVIEW_MARKER']
    def __init__(self):
        self.calls = []
        self.base_plan = copy.deepcopy(plan)
        self.base_context = copy.deepcopy(context)
    def binding(self, grant_path, grant_sha, *, check_deadline):
        self.calls.append(('binding', grant_path, grant_sha, check_deadline))
        assert grant_path == base['grant'] and grant_sha == base['grantSha256'] and check_deadline is False
        return copy.deepcopy(base), copy.deepcopy(self.base_plan), copy.deepcopy(self.base_context)
    def with_execution_metadata(self, original_base, exact_plan, path, expected):
        self.calls.append(('with', copy.deepcopy(original_base), path, expected))
        assert original_base == base and exact_plan == plan
        assert path == metadata['supplement']['path'] and expected == metadata['supplement']['sha256']
        return copy.deepcopy(composite)
    def metadata_selection(self, bound, exact_plan, selected):
        self.calls.append(('selection', tuple(selected)))
        assert len(selected) == len(set(selected)) and set(selected) == set(metadata['documentIds'])
    def metadata_provenance(self, bound):
        return {key: value for key, value in bound['executionMetadata'].items() if key != 'context'}

def environment():
    remembers = []
    writer = MemoryWriter()
    ns = dict(constants, json=json, METADATA_WRITER=writer_path,
              safe=lambda value: PurePosixPath(value),
              sha=lambda value: constants['METADATA_WRITER_SHA'],
              load=lambda value: copy.deepcopy(context), guard=SimpleNamespace(CONTEXT='/owned/context.json'))
    def remember(path, expected=None):
        remembers.append((str(path), expected))
        return PurePosixPath(path)
    ns['metadata_writer'] = lambda callback: writer
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(CANDIDATE) + ':AST-only', 'exec'), ns)
    return ns, writer, remembers, remember

def bind_case(mutator=None, *, absent=False, report=False):
    ns, writer, remembers, remember = environment()
    supplied, selected, prepared, granted = copy.deepcopy(composite), copy.deepcopy(definition), copy.deepcopy(prep), copy.deepcopy(grant)
    if absent:
        supplied = copy.deepcopy(base)
    if report:
        selected = copy.deepcopy(plan['documents'][1])
    if mutator:
        mutator(ns, writer, supplied, selected, prepared, granted)
    result = ns['bind_optional_metadata'](supplied, selected, plan, prepared, granted, remember, writer=writer)
    if absent:
        assert result is None and not writer.calls and not remembers
    else:
        assert result == {'context': metadata_context, 'provenance': provenance}
        assert remembers == list(metadata['pinnedFiles'].items())
        assert writer.calls[0][0] == 'binding' and writer.calls[1][0] == 'with' and writer.calls[2][0] == 'selection'

test('ordinary wave skips all writer binding and pins', lambda: bind_case(absent=True))
test('index supplement binds from independent activation base', bind_case)
test('analysis report supplement accepted', lambda: bind_case(report=True))
mutations = {
    'business document refused': lambda n,w,s,d,p,g: d.update(kind='basic-design'),
    'wrong writer path refused': lambda n,w,s,d,p,g: p.update(helper='/owned/other.py'),
    'wrong writer preparation hash refused': lambda n,w,s,d,p,g: p.update(helperSha256='0'*64),
    'wrong activation driver hash refused': lambda n,w,s,d,p,g: g.update(driverSha256='0'*64),
    'writer marker drift refused': lambda n,w,s,d,p,g: setattr(w, 'METADATA_REVIEW_MARKER', 'changed'),
    'actual base plan mismatch refused': lambda n,w,s,d,p,g: w.base_plan.update(extra=True),
    'actual full base context mismatch refused': lambda n,w,s,d,p,g: w.base_context.update(extra=True),
    'arbitrary composite field refused': lambda n,w,s,d,p,g: s.update(arbitrary=True),
    'composite original base field mutation refused': lambda n,w,s,d,p,g: s['snapshot'].update(mode='other'),
    'composite pin omission refused': lambda n,w,s,d,p,g: s['pinnedFiles'].pop('/owned/evidence.json'),
    'composite pin mutation refused': lambda n,w,s,d,p,g: s['pinnedFiles'].update({'/owned/evidence.json':'0'*64}),
    'composite metadata context mutation refused': lambda n,w,s,d,p,g: s['executionMetadata']['context'].update(extra=True),
    'composite metadata context hash mutation refused': lambda n,w,s,d,p,g: s['executionMetadata'].update(contextSha256='0'*64),
    'composite metadata authority mutation refused': lambda n,w,s,d,p,g: s['executionMetadata'].update(businessEvidenceAuthority=True),
    'composite supplemental reference path mutation refused': lambda n,w,s,d,p,g: s['executionMetadata']['supplement'].update(path='/wrong.json'),
    'composite supplemental reference hash mutation refused': lambda n,w,s,d,p,g: s['executionMetadata']['supplement'].update(sha256='0'*64),
    'wave selected subset refused': lambda n,w,s,d,p,g: p.update(documents=['INDEX']),
    'wave selected duplicate refused': lambda n,w,s,d,p,g: p.update(documents=['INDEX','REPORT','INDEX']),
    'wave selected unrelated ID refused': lambda n,w,s,d,p,g: p.update(documents=['INDEX','UNRELATED']),
    'definition missing supplemental target refused': lambda n,w,s,d,p,g: d.update(id='OTHER'),
    'writer code drift after rebind refused': lambda n,w,s,d,p,g: n.update(sha=lambda value:'0'*64),
    'grant path drift refused': lambda n,w,s,d,p,g: s.update(grant='/wrong/grant.json'),
    'grant hash drift refused': lambda n,w,s,d,p,g: s.update(grantSha256='0'*64),
}
for name, mutation in mutations.items():
    test(name, lambda mutation=mutation: bind_case(mutation), rejects=True)

ns, _, _, _ = environment()
dm, rm, mm = constants['DRAFT_SCOPE_MARKER'], constants['REVIEW_SCOPE_MARKER'], constants['METADATA_REVIEW_MARKER']
def prompt_case(mutator=None, *, absent=False, ordinary_body_marker=False, revision=False):
    option = None if absent else {'context': copy.deepcopy(metadata_context), 'provenance': copy.deepcopy(provenance)}
    carriers = [{} for _ in range(3)] if absent else [{'executionMetadata':copy.deepcopy(provenance)} for _ in range(3)]
    scope = copy.deepcopy(context) if absent else {'executionContext':copy.deepcopy(context), 'sameRunExecutionMetadata':copy.deepcopy(metadata_context)}
    if revision:
        scope['previousCanonicalMarkdown'] = 'synthetic earlier draft\r\n'
        scope['revisionProvenance'] = {'sourceResultSha256':'f'*64}
    draft_prompt = dm + json.dumps(scope, ensure_ascii=False) + '\nAIによる解析素材:\n{}'
    review_prompt = rm + json.dumps(context, ensure_ascii=False)
    if not absent:
        review_prompt += mm + json.dumps(metadata_context, ensure_ascii=False)
    review_prompt += '\n原稿本文:\n' + ('synthetic literal ' + mm if ordinary_body_marker else 'synthetic text')
    selected = copy.deepcopy(definition)
    data = [option, selected, carriers, draft_prompt, review_prompt]
    if mutator:
        mutator(data)
    ns['metadata_prompt_binding'](data[0], data[1], *data[2], data[3], data[4], context)
test('supplement prompt full original context and three provenance carriers accepted', prompt_case)
test('supplement preserves additional revision context members', lambda: prompt_case(revision=True))
test('ordinary prompt without metadata accepted', lambda: prompt_case(absent=True))
test('ordinary canonical body literal metadata marker allowed', lambda: prompt_case(absent=True, ordinary_body_marker=True))
for index, role in enumerate(('text pin','author result','review handoff')):
    test(role+' metadata drift refused', lambda index=index: prompt_case(lambda d: d[2][index]['executionMetadata'].update(contextSha256='0'*64)), True)
    test(role+' metadata omission refused', lambda index=index: prompt_case(lambda d: d[2][index].clear()), True)
    test(role+' unbound metadata refused', lambda index=index: prompt_case(lambda d: d[2][index].update(executionMetadata=provenance), absent=True), True)
test('supplement business kind refused in prompt chain', lambda: prompt_case(lambda d: d[1].update(kind='basic-design')), True)
test('supplement missing draft scope marker refused', lambda: prompt_case(lambda d: d.__setitem__(3, 'unscoped')), True)
test('supplement altered original execution context refused', lambda: prompt_case(lambda d: d.__setitem__(3, dm+json.dumps({'executionContext':{},'sameRunExecutionMetadata':metadata_context}))), True)
test('supplement altered draft metadata refused', lambda: prompt_case(lambda d: d.__setitem__(3, dm+json.dumps({'executionContext':context,'sameRunExecutionMetadata':{}}))), True)
test('supplement missing independent review metadata refused', lambda: prompt_case(lambda d: d.__setitem__(4, rm+json.dumps(context)+'\n原稿本文:\ntext')), True)
test('supplement altered independent review original scope refused', lambda: prompt_case(lambda d: d.__setitem__(4, rm+'{}'+mm+json.dumps(metadata_context)+'\n原稿本文:\ntext')), True)
test('supplement altered independent review metadata refused', lambda: prompt_case(lambda d: d.__setitem__(4, rm+json.dumps(context)+mm+'{}'+'\n原稿本文:\ntext')), True)
test('supplement duplicate review metadata marker refused', lambda: prompt_case(lambda d: d.__setitem__(4, d[4].split('\n原稿本文:\n')[0]+mm+'{}\n原稿本文:\ntext')), True)
test('ordinary unbound draft metadata context refused', lambda: prompt_case(lambda d: d.__setitem__(3, dm+json.dumps({'executionContext':context,'sameRunExecutionMetadata':metadata_context})), absent=True), True)
test('ordinary unbound review-prefix metadata refused', lambda: prompt_case(lambda d: d.__setitem__(4, rm+json.dumps(context)+mm+json.dumps(metadata_context)+'\n原稿本文:\ntext'), absent=True), True)
test('strict parser accepts complete JSON followed by later prompt section', lambda: ns['prompt_metadata_object'](dm+'{"safe":true}\nnext section',dm)=={'safe':True} or (_ for _ in ()).throw(AssertionError()))
test('strict parser duplicate JSON member refused', lambda: ns['prompt_metadata_object'](dm+'{"x":1,"x":2}',dm), True)
test('strict parser nested duplicate JSON member refused', lambda: ns['prompt_metadata_object'](dm+'{"x":{"a":1,"a":2}}',dm), True)
for item in ('NaN','Infinity','-Infinity'):
    test('strict parser nonfinite '+item+' refused', lambda item=item: ns['prompt_metadata_object'](dm+'{"x":'+item+'}',dm), True)
test('strict parser missing marker refused', lambda: ns['prompt_metadata_object']('{}',dm), True)
test('strict parser duplicate marker refused', lambda: ns['prompt_metadata_object'](dm+'{}'+dm+'{}',dm), True)

# The actual added raw-review reconstruction block is executed in isolation with
# own source-context, validator and prompt stubs. No frozen imports execute.
main_node = new_functions['main']
review_block = next(node for node in ast.walk(main_node) if isinstance(node, ast.If)
    and any(isinstance(item, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'expected_review' for target in item.targets)
            for item in node.body))
body = [node for node in review_block.body if not isinstance(node, (ast.Import,ast.ImportFrom))]
block = compile(ast.Module(body=body,type_ignores=[]), str(CANDIDATE)+':raw-review-AST-only','exec')
class MemoryDocument:
    def __init__(self, content): self.content=content
    def read_bytes(self): return self.content
def raw_review_case(*, body='synthetic 文書\r\nline2\r\n', mutation=None):
    md = body.encode('utf-8')
    core='common policy\nUser task (within that boundary):\n'+'review rules'+'document context'+rm+json.dumps(context,ensure_ascii=False,indent=2)+mm+json.dumps(metadata_context,ensure_ascii=False,indent=2)+'\n原稿本文:\n'+body+'\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n[]'
    local = dict(ns, document=MemoryDocument(md), definition=copy.deepcopy(definition),
        validate_document=lambda *args,**kwargs:[], workflow=SimpleNamespace(select_document=lambda *args:copy.deepcopy(definition),_document_context=lambda *args:'document context'),
        prompts=SimpleNamespace(REVIEW='review rules'), provider=SimpleNamespace(COMMON_POLICY='common policy'),
        guard=SimpleNamespace(SNAPSHOT='/synthetic/snapshot'), plan='/synthetic/plan.json', context=copy.deepcopy(context),
        execution_metadata={'context':copy.deepcopy(metadata_context)}, review_prompt=core)
    if mutation: mutation(local)
    exec(block,local)
test('raw full review reconstruction preserves CRLF and Japanese text', raw_review_case)
test('raw full review reconstruction accepts LF document', lambda: raw_review_case(body='synthetic 文書\nline2\n'))
test('raw full review rejects newline normalization', lambda: raw_review_case(mutation=lambda d:d.update(review_prompt=d['review_prompt'].replace('\r\n','\n'))),True)
test('raw full review rejects omitted body line', lambda: raw_review_case(mutation=lambda d:d.update(review_prompt=d['review_prompt'].replace('line2\r\n',''))),True)
test('raw full review rejects prefix rule mutation', lambda: raw_review_case(mutation=lambda d:d.update(review_prompt=d['review_prompt'].replace('review rules','other'))),True)
test('raw full review rejects structure record mutation', lambda: raw_review_case(mutation=lambda d:d.update(review_prompt=d['review_prompt'][:-2]+'["wrong"]')),True)
test('raw full review rejects extra trailing text', lambda: raw_review_case(mutation=lambda d:d.update(review_prompt=d['review_prompt']+'\nextra')),True)
test('raw full review rejects supplemental context mutation', lambda: raw_review_case(mutation=lambda d:d['execution_metadata']['context'].update(extra=True)),True)

# Files are reread only for source-code identity, never production metadata.
assert digest(CANDIDATE.read_bytes()) == EXPECTED
assert digest(BASELINE.read_bytes()) == BASE_EXPECTED
report = {'schema':'spec-agent-independent-collector-supplement-probes/1',
    'reviewer':'/root/delivery_root_review/supplement_collector_review',
    'candidate':{'path':str(CANDIDATE),'sha256':EXPECTED},
    'baseline':{'path':str(BASELINE),'sha256':BASE_EXPECTED},
    'script':{'path':str(Path(__file__)),'sha256':digest(Path(__file__).read_bytes())},
    'status':'PASS_CODE_AND_AST_ISOLATED_SYNTHETIC_ONLY' if all(item['passed'] for item in results) else 'HOLD_SYNTHETIC_FAILURE',
    'testCount':len(results),'passedCount':sum(item['passed'] for item in results),'tests':results,
    'preservedBaselineRequireCallCount':sum(old_calls.values()),
    'limitations':{'actualCollectorImportedOrRun':False,'writerImportedOrRun':False,'provenanceHelperImported':False,
        'frozenRuntimeImportedOrRun':False,'realInputRead':False,'businessMarkdownRead':False,'providerRun':False,
        'authorRecordsRead':False,'actualCollectionPerformed':False,'actualWriterBindingTested':False,
        'actualSchemaValidationTested':False,'realFilesystemReparseBehaviorTested':False,
        'originalArtifactsModified':False,'atomicOrRaceFreeProof':False}}
target=AUDIT/'supplement-collector-r09-independent-probes-r01.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2); stream.write('\n')
print(json.dumps({'status':report['status'],'testCount':len(results),'passedCount':report['passedCount'],
    'failures':[item for item in results if not item['passed']], 'report':str(target),'sha256':digest(target.read_bytes())}))
if not all(item['passed'] for item in results):
    raise SystemExit(1)
