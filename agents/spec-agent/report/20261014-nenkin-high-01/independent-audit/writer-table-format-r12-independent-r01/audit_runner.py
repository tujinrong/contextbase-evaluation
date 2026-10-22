"""Independent code-only audit. Never import the audited driver or run its I/O/provider paths."""
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
from jsonschema import Draft202012Validator

OUT = Path(__file__).parent
INPUT = Path('D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
names = ['nenkin_writer_driver_r11.py', 'nenkin_writer_driver_r12_candidate.py', 'nenkin_table_format_supplement_schema_r01.json']
expected = ['be2a1a686eae3058226c6f630af17a9d5c1cfc2c0e6c1d7f259dd9db52f2dcfb', '530cd857d4e6246251570ecc5f76da75a53f8152edbccf8a9382a1695701e5a1', 'f52cfc32df8d28074d2fdcf2cf5bf289e60745fd9f754ee6bf3adf88837fb9a9']
data = [(INPUT / n).read_bytes() for n in names]
hashes = [hashlib.sha256(v).hexdigest() for v in data]
assert hashes == expected
old, new = [ast.parse(v.decode('utf-8-sig')) for v in data[:2]]
schema = json.loads(data[2])
cases = []

def case(name, fn, rejected=False):
    try:
        fn()
    except Exception as exc:
        if not rejected:
            cases.append({'name': name, 'passed': False, 'error': type(exc).__name__ + ': ' + str(exc)})
            return
        if not isinstance(exc, (ValueError, __import__('jsonschema').exceptions.ValidationError)):
            cases.append({'name': name, 'passed': False, 'unexpectedError': type(exc).__name__ + ': ' + str(exc)})
            return
        cases.append({'name': name, 'passed': True, 'expectedRejection': type(exc).__name__, 'message': str(exc).splitlines()[0]})
    else:
        cases.append({'name': name, 'passed': not rejected, 'expectedRejectionMissing': rejected})

def verify(value, message='assertion failed'):
    if not value:
        raise AssertionError(message)

dump = lambda n: ast.dump(n, include_attributes=False)
old_f = {n.name: n for n in old.body if isinstance(n, ast.FunctionDef)}
new_f = {n.name: n for n in new.body if isinstance(n, ast.FunctionDef)}
changed = [k for k in old_f if dump(old_f[k]) != dump(new_f[k])]
same = [k for k in old_f if dump(old_f[k]) == dump(new_f[k])]
added = sorted(set(new_f) - set(old_f))
allowed_changes = ['recheck', 'prepare', 'scoped_review', 'text_pin', 'run', 'main']
allowed_added = ['table_format_revision_context', 'table_format_selection', 'with_table_format_metadata']
added_constants = ['TABLE_FORMAT_KINDS', 'TABLE_FORMAT_SCHEMA', 'TABLE_FORMAT_POLICY']
case('AST exact six changed functions and three new functions', lambda: verify(changed == allowed_changes and added == allowed_added and len(same) == 23 and not (set(old_f) - set(new_f))))
old_other = [n for n in old.body if not isinstance(n, ast.FunctionDef)]
new_other = [n for n in new.body if not isinstance(n, ast.FunctionDef) and not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in added_constants for t in n.targets))]
case('AST all original non-function nodes imports constants schemas and entry guard preserved', lambda: verify([dump(n) for n in old_other] == [dump(n) for n in new_other]))
actual_added = [n.targets[0].id for n in new.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in added_constants]
case('AST exactly three added constants', lambda: verify(actual_added == added_constants and len(new.body) - len(old.body) == 6))
def retained_nodes(predicate):
    for name in allowed_changes:
        before=Counter(dump(n) for n in ast.walk(old_f[name]) if predicate(n))
        after=Counter(dump(n) for n in ast.walk(new_f[name]) if predicate(n))
        verify(not (before-after), 'original protected AST node changed or removed: '+name)
case('AST modified functions retain all original require guard calls', lambda: retained_nodes(lambda n:isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require'))
case('AST modified functions retain original local imports', lambda: retained_nodes(lambda n:isinstance(n,(ast.Import,ast.ImportFrom))))
case('AST modified functions retain original workflow and capsule calls', lambda: retained_nodes(lambda n:isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id in {'workflow','capsule'}))
policy = ast.literal_eval(next(n.value for n in new.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'TABLE_FORMAT_POLICY'))
kinds = frozenset({'logical-table-definition', 'physical-table-definition'})
case('schema valid Draft202012 and exact driver policy const', lambda: (Draft202012Validator.check_schema(schema), verify(schema['properties']['tableFormatPolicy']['const'] == policy)))
case('policy only two kinds and all fact authority omission core verdict flags false', lambda: verify(set(policy['documentKinds']) == kinds and all(policy[k] is False for k in ['addsBusinessFactsOrAnswers', 'addsSourceReadPermissions', 'omitsExistingValidFacts', 'frozenCoreOrLoadedPromptChanged', 'reviewVerdictMayBeOverridden'])))
case('policy preserves cells forbids external blocks and distinguishes planned GRID state', lambda: verify(all(s in ' '.join(policy['rules']) for s in ['inside the appropriate table cells', 'h3 headings, paragraphs', 'code fences, SQL fences, Mermaid diagrams', 'existing planned GRID document', 'not proof that the other document has been generated', 'planned or unverified'])))

# Extract only these six function AST nodes. No module body, imports, bootstrap,
# actual binding, provider, prepare, run, main, source/data readers are executed.
extract = ['require', 'hash_arg', 'with_table_format_metadata', 'table_format_selection', 'table_format_revision_context', 'recheck']
ns = {'__builtins__': __builtins__, 're': re, 'TABLE_FORMAT_KINDS': kinds, 'TABLE_FORMAT_POLICY': policy}
exec(compile(ast.Module(body=[new_f[n] for n in extract], type_ignores=[]), '<independent-extracted-pure-functions>', 'exec'), ns)
WORK = PureWindowsPath('Q:/virtual-audit/work')
REPORT = PureWindowsPath('Q:/virtual-audit/report')
S = WORK / 'nenkin_table_format_supplement_schema_r01.json'
P = WORK / 'execution-metadata' / 'format.json'
ns.update(WORK=WORK, REPORT=REPORT, TABLE_FORMAT_SCHEMA=(S, hashes[2]))
base = {'grant': 'virtual-grant', 'grantSha256': '8'*64, 'snapshot': {'manifestSha256': '1'*64, 'mode': 'source-only'}, 'executionContextSha256': '2'*64, 'planSha256': '3'*64, 'pinnedFiles': {'Q:\\virtual-audit\\base.json': '4'*64}}
plan = {'documents': [{'id': 'LT', 'kind': 'logical-table-definition', 'path': 'tables/logical.md'}, {'id': 'PT', 'kind': 'physical-table-definition', 'path': 'tables/physical.md'}, {'id': 'GRID', 'kind': 'detailed-specification', 'path': 'grid/detail.md'}]}
value = {'schema': 'spec-agent-table-format-supplement/1', 'runId': '20261014-nenkin-high-01', 'projectId': 'nenkin', 'mode': 'source-only', 'capsuleManifestSha256': '1'*64, 'executionContextSha256': '2'*64, 'planSha256': '3'*64, 'documentKinds': sorted(kinds), 'documents': [{'documentId': d['id'], 'kind': d['kind'], 'path': d['path']} for d in plan['documents'][:2]], 'tableFormatPolicy': deepcopy(policy)}
for field in ['businessEvidenceAuthority', 'newSourceReadPermissions', 'originalAppExecuted', 'originalSpecificationsAuthorized', 'evaluationExpectationsAuthorized', 'businessProseAssembledByPython', 'semanticOrNativeOrFormalApproval']:
    value[field] = False
original_context = {'schema': 'synthetic-original-context/1', 'scope': {'allOriginalMetadata': True}, 'authorizedEvidence': ['synthetic-only']}
vfs = {}
calls = {'virtualSha': 0, 'virtualLoad': 0, 'virtualBinding': 0}
def safe(path):
    return PureWindowsPath(path)
def sha(path):
    calls['virtualSha'] += 1
    return hashlib.sha256(vfs[str(safe(path))]).hexdigest()
def load(path):
    calls['virtualLoad'] += 1
    return json.loads(vfs[str(safe(path))])
def binding_stub(grant, grant_sha, *, check_deadline=True):
    calls['virtualBinding'] += 1
    verify(grant == base['grant'] and grant_sha == base['grantSha256'])
    return deepcopy(base), deepcopy(plan), original_context
ns.update(safe=safe, sha=sha, load=load, binding=binding_stub)
def reset(v=None):
    ns['sha'] = sha
    vfs.clear()
    vfs[str(S)] = data[2]
    vfs[str(P)] = json.dumps(value if v is None else v, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return sha(P)
def bind(v=None, pin=None, path=P, expected_sha=None, plan_value=None):
    checksum = reset(v)
    if path != P:
        vfs[str(safe(path))] = vfs[str(P)]
    return ns['with_table_format_metadata'](deepcopy(base) if pin is None else pin, deepcopy(plan) if plan_value is None else plan_value, path, checksum if expected_sha is None else expected_sha)
def valid_bind():
    before = deepcopy(base)
    result = bind()
    verify(base == before and 'tableFormatMetadata' not in base)
    verify(result['pinnedFiles'] is not base['pinnedFiles'] and len(result['pinnedFiles']) == 3)
    verify(result['tableFormatMetadata']['documentIds'] == ['LT','PT'])
    verify(result['tableFormatMetadata']['internalAnalysisDraftCallbackChecksPerformed'] is False and result['tableFormatMetadata']['atomicOrRaceFreeProof'] is False)
case('valid two-kind binding adds metadata pins and leaves original pin unchanged', valid_bind)
case('report execution-metadata path also allowed', lambda: verify('tableFormatMetadata' in bind(path=REPORT / 'execution-metadata' / 'format.json')))
case('existing identical file pins accepted', lambda: bind(pin={**deepcopy(base), 'pinnedFiles': {**base['pinnedFiles'], str(P): reset(), str(S): hashes[2]}}))
for label, field, bad in [('run identity', 'runId', 'other-run'), ('project identity', 'projectId', 'other-project'), ('mode identity', 'mode', 'reference-design'), ('schema identity', 'schema', 'spec-agent-table-format-supplement/2'), ('capsule identity', 'capsuleManifestSha256', '5'*64), ('context identity', 'executionContextSha256', '5'*64), ('plan identity', 'planSha256', '5'*64), ('document kinds scope', 'documentKinds', ['detailed-specification'])]:
    case('reject ' + label, lambda field=field,bad=bad: bind({**deepcopy(value), field: bad}), True)
for field in ['businessEvidenceAuthority', 'newSourceReadPermissions', 'originalAppExecuted', 'originalSpecificationsAuthorized', 'evaluationExpectationsAuthorized', 'businessProseAssembledByPython']:
    case('reject authority/provenance flag ' + field, lambda field=field: bind({**deepcopy(value), field: True}), True)
case('reject additional business fact body', lambda: bind({**deepcopy(value), 'businessBody': 'synthetic unauthorized body'}), True)
case('reject omitted required field', lambda: bind({k:v for k,v in value.items() if k != 'planSha256'}), True)
for label, docs in [('empty documents', []), ('duplicate document', [value['documents'][0], value['documents'][0]]), ('same ID differing item', [value['documents'][0], {**value['documents'][1], 'documentId':'LT'}]), ('unknown ID', [{**value['documents'][0], 'documentId':'UNKNOWN'}]), ('non-table kind', [{'documentId':'GRID','kind':'detailed-specification','path':'grid/detail.md'}]), ('wrong exact kind', [{**value['documents'][0], 'kind':'physical-table-definition'}]), ('wrong exact path', [{**value['documents'][0], 'path':'tables/other.md'}]), ('doc extra authority', [{**value['documents'][0], 'newSourceReadPermissions':True}])]:
    case('reject ' + label, lambda docs=docs: bind({**deepcopy(value), 'documents':docs}), True)
case('reject policy rule drift', lambda: bind({**deepcopy(value), 'tableFormatPolicy': {**deepcopy(policy), 'rules':['synthetic replacement']}}), True)
case('reject base mode outside source-only', lambda: bind(pin={**deepcopy(base),'snapshot': {**base['snapshot'],'mode':'reference-design'}}), True)
case('reject supplement outside execution-metadata', lambda: bind(path=WORK / 'other' / 'format.json'), True)
case('reject supplement in another run', lambda: bind(path=PureWindowsPath('Q:/other-run/execution-metadata/format.json')), True)
case('reject non-json supplement', lambda: bind(path=P.with_suffix('.txt')), True)
case('reject uppercase expected SHA', lambda: bind(expected_sha='A'*64), True)
case('reject wrong supplement SHA', lambda: bind(expected_sha='f'*64), True)
case('reject supplement repinning enriched original', lambda: bind(pin={**deepcopy(base), 'tableFormatMetadata':{}}), True)
case('reject existing supplement pin conflict', lambda: bind(pin={**deepcopy(base),'pinnedFiles':{str(P):'f'*64}}), True)
case('reject existing schema pin conflict', lambda: bind(pin={**deepcopy(base),'pinnedFiles':{str(S):'f'*64}}), True)
def corrupt_schema():
    checksum=reset(); vfs[str(S)] += b' '
    ns['with_table_format_metadata'](deepcopy(base),deepcopy(plan),P,checksum)
case('reject schema byte drift', corrupt_schema, True)
def binding_drift():
    checksum=reset(); counts={}
    def drift(path):
        key=str(safe(path)); counts[key]=counts.get(key,0)+1
        return 'f'*64 if key==str(P) and counts[key]>1 else sha(path)
    ns['sha']=drift
    ns['with_table_format_metadata'](deepcopy(base),deepcopy(plan),P,checksum)
case('reject supplement drift during binding second hash', binding_drift, True)
reset(); good=bind()
case('selection allows exact LT and PT subset', lambda: (ns['table_format_selection'](good,plan,['LT']), ns['table_format_selection'](good,plan,['PT','LT'])))
for label, selected in [('empty', []), ('duplicate',['LT','LT']), ('non-table',['GRID']), ('unknown',['UNKNOWN'])]:
    case('reject selection '+label, lambda selected=selected: ns['table_format_selection'](good,plan,selected), True)
case('base selection no supplement remains inert', lambda: verify(ns['table_format_selection'](base,plan,[]) is None))
def initial_context():
    saved=deepcopy(original_context)
    result=ns['table_format_revision_context'](original_context,original_context,good,plan['documents'][0])
    verify(result is not original_context and result['executionContext'] is original_context and original_context==saved and result['tableFormatPolicy']==policy and result['tableFormatMetadata']==good['tableFormatMetadata']['context'])
case('initial context full original object preserved without mutation', initial_context)
previous = {'executionContext':original_context, 'previousMarkdown':'synthetic full Markdown sentinel', 'previousReview':{'approved':False,'findings':['synthetic sentinel']}, 'completedAnalysisReuse': {'analysisJob':'synthetic-only'}, 'businessProseAssembledByPython':False}
def revision_context():
    saved=deepcopy(previous)
    result=ns['table_format_revision_context'](previous,original_context,good,plan['documents'][1])
    verify(previous==saved and result is not previous and all(result[k] == v for k,v in saved.items()))
case('revision context preserves full prior Markdown review reuse metadata and original context', revision_context)
case('base context identity remains inert', lambda: verify(ns['table_format_revision_context'](previous,original_context,base,plan['documents'][2]) is previous))
case('reject policy into GRID definition', lambda: ns['table_format_revision_context'](previous,original_context,good,plan['documents'][2]), True)
case('reject policy into unknown table ID', lambda: ns['table_format_revision_context'](previous,original_context,good,{**plan['documents'][0],'id':'UNKNOWN'}), True)
case('reject prior context missing full original', lambda: ns['table_format_revision_context']({'executionContext':{}},original_context,good,plan['documents'][0]), True)
case('reject prior conflicting table policy', lambda: ns['table_format_revision_context']({**previous,'tableFormatPolicy':{}},original_context,good,plan['documents'][0]), True)
def rebind_good():
    reset(); verify(ns['recheck'](good)==(plan,original_context)); verify(ns['recheck'](good,check_deadline=False)==(plan,original_context))
case('recheck stub rebinds metadata with exact final pin equality', rebind_good)
case('recheck base no metadata unchanged', lambda: verify(ns['recheck'](base)==(plan,original_context)))
def rebind_drift():
    reset(); vfs[str(P)] += b' '
    ns['recheck'](good)
case('recheck rejects supplement byte drift', rebind_drift, True)
def final_pin_drift():
    reset(); altered=deepcopy(good); altered['tableFormatMetadata']['atomicOrRaceFreeProof']=True
    ns['recheck'](altered)
case('recheck rejects bound metadata field drift', final_pin_drift, True)
def changed_base():
    reset()
    def changed(grant,grant_sha,*,check_deadline=True):
        now=deepcopy(base); now['planSha256']='6'*64
        return now,deepcopy(plan),original_context
    ns['binding']=changed
    try: ns['recheck'](good)
    finally: ns['binding']=binding_stub
case('recheck rejects underlying synthetic base identity drift', changed_base, True)

failed = [c for c in cases if not c['passed']]
report = {'schema':'independent-table-format-code-audit/1', 'createdAt':datetime.now(timezone.utc).isoformat(), 'status':'PASS_TECHNICAL_CODE_ONLY' if not failed else 'FAIL_TECHNICAL_CODE_ONLY', 'inputs':[{'path':str(INPUT/n),'sha256':h} for n,h in zip(names,hashes)], 'scope':{'inputArtifactReadAllowlist':names,'actualDriverModuleImported':False,'actualSourcePlanContextCapsuleRawMarkdownSupplementRead':False,'actualProductionJobProviderBootstrapBindingMainRunPrepareReviewTextPinExecuted':False,'actualProviderExecutions':0,'extractExecuted':extract,'syntheticRebindingOnly':True,'virtualOperations':calls,'genericJsonschemaDependencyImported':True}, 'ast':{'oldFunctionCount':len(old_f),'newFunctionCount':len(new_f),'unchangedFunctions':same,'changedFunctions':changed,'addedFunctions':added,'addedConstants':actual_added,'originalImportsNonFunctionNodesAndSchemaConstantsUnchanged':cases[1]['passed']}, 'passedCaseCount':len(cases)-len(failed),'caseCount':len(cases),'cases':cases,'findings':failed,'limitations':['No business/source semantic accuracy, native fidelity, 95-point score, formal evaluation, actual Markdown compliance, generation success or AI review approval was tested or granted.','Policy text is checked as inert canonical-format instructions only; retention of all actual source facts and tables remains an AI generation/review obligation.','No actual recheck binding, provider, production job, existing text-pin schema file or frozen runtime module was read/imported/executed. Existing schema constants and all original core AST were compared only.','safe/raw/load/sha and binding were replaced solely in extracted functions by a PureWindowsPath virtual filesystem and synthetic fixtures; native filesystem symlink handling and races were not tested.','Before/after pin checks do not prove atomicity, race freedom or internal analysis/draft callback checks.','The policy and preserved revision context use shallow copies; intended metadata references remain shared, and this audit grants no deep immutability proof.']}
report['dependencySetupNotes'] = {'genericDependencyPathsUsed': ['D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps', 'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/session-python-deps'], 'optionalLocalVendorInstallInterrupted': True, 'localVendorImportedByAudit': False, 'optionalVendorCleanupRejectedByExecutionPolicy': True, 'vendorDirectoryRetained': True, 'cleanupRejectionReason': 'blocked by policy; no more specific reason returned'}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'audit-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary='''# Independent writer table-format r12 audit\n\nStatus: %s. %d/%d code-only cases passed.\n\nInput SHA256:\n%s\n\nAST: 23 original functions unchanged; 6 changed (recheck, prepare, scoped_review, text_pin, run, main); 3 added (with_table_format_metadata, table_format_selection, table_format_revision_context); 3 constants added. Original imports, non-function nodes, existing SCHEMAS constants and entry guard unchanged.\n\nThe extracted pure functions were tested with synthetic virtual pin, plan and file metadata. Scope includes two canonical table kinds, exact IDs/paths, schema/policy identity, false authority flags, conflicting pins, binding and recheck drift, restricted selection, and retention of full original/prior revision context.\n\nThe policy contains the cell fact retention, table-only HEADER/detail LIST, external h3/paragraph/fence/diagram exclusions, and planned GRID reference state distinctions. This is a review of generic policy text, not proof of actual Markdown or source fact compliance.\n\nActual provider executions: 0. Actual source/plan/context/capsule/raw/Markdown/supplement/evaluation/production job/frozen runtime reads or executions: 0. Actual driver module, binding/bootstrap/main/prepare/run/review/text_pin executions: 0. Generic jsonschema dependency was imported.\n\nLimitations:\n%s\n\nSee audit-results.json for each test, and audit_runner.py for the isolated harness.\n''' % (report['status'],report['passedCaseCount'],report['caseCount'],'\n'.join('- '+n+': '+h for n,h in zip(names,hashes)),'\n'.join('- '+x for x in report['limitations']))
summary += '\nDependency setup note: an optional local vendor installation was interrupted after parent supplied generic dependency paths. That vendor was not imported by this audit. Optional recursive cleanup was automatically rejected as "blocked by policy" with no more specific reason; vendor is retained under this audit output directory.\n'
(OUT/'audit-report.md').write_text(summary,encoding='utf-8')
print(json.dumps({'status':report['status'],'passed':report['passedCaseCount'],'total':report['caseCount'],'failed':failed,'changed':changed,'unchangedCount':len(same),'output':str(OUT)},ensure_ascii=False))
sys.exit(bool(failed))
