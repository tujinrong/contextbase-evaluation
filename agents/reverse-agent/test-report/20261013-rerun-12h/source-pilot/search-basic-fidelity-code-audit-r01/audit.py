"""Code-only AST audit. All evidence files in this script are synthetic."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from jsonschema import Draft202012Validator

REPO=Path(r'D:\開発\contextbase-evaluation')
BASE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
HERE=Path(__file__).resolve().parent
TARGET=BASE/'review_search_basic_fidelity_v1.py'
EXPECTED='a9a705106a5b262bc81be0f9b11765c3746aee143590676a963c2a5d95d5d995'
GENERIC=BASE/'review_table_index_fidelity_v2.py'
STATE=BASE/'run_state_projection_v6.py'
RUNTIME=BASE/'runtime-code/assisted-06/src/contextbase/ai'
CODE=[TARGET,GENERIC,STATE,RUNTIME/'schemas.py',RUNTIME/'workflow.py',RUNTIME/'capsule.py']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p) for p in CODE}
assert before[str(TARGET)]==EXPECTED
assert before[str(STATE)]=='dea405e860904d3cff89a1de675a5c8b0270d24bad76f9005c90518f140ca78f'
trees={str(p):ast.parse(p.read_text(encoding='utf-8-sig')) for p in CODE}
def extract(tree,names,ns):
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected}==set(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),'<code-only selected definitions>','exec'),ns)

# schemas.py is pure shape construction (no imports or file reads).
schema_ns={}
exec(compile(trees[str(RUNTIME/'schemas.py')],'<frozen pure schemas>','exec'),schema_ns)
workflow_ns={}
extract(trees[str(RUNTIME/'workflow.py')],['_materials','references_valid'],workflow_ns)
capsule_ns={'os':os,'Path':Path}
extract(trees[str(RUNTIME/'capsule.py')],['safe_path'],capsule_ns)
FIXTURE=HERE/'synthetic-capsule'
FIXTURE.mkdir(exist_ok=False)
reference='reference-designs/primary.md'
contents={'sources/a.txt':'alpha one\nalpha two\nalpha three\n',
          'sources/b.txt':'beta one\nbeta two\n',
          reference:'design one\ndesign two\ndesign three\n'}
for name,value in contents.items():
    p=FIXTURE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value,encoding='utf-8')
manifest={'files':[{'path':n.removeprefix('sources/'),'indexed':'indexed/'+n.removeprefix('sources/'),'lines':len(v.splitlines())}
                   for n,v in contents.items() if n.startswith('sources/')],
          'referenceFiles':[{'path':reference,'lines':3}]}
closure=sorted(contents)
safe_reads=[]
def traced_safe(path):
    p=capsule_ns['safe_path'](path)
    if FIXTURE not in p.parents:raise ValueError('Synthetic fixture only')
    safe_reads.append(str(p))
    return p
state=SimpleNamespace(workflow=SimpleNamespace(**workflow_ns,schemas=SimpleNamespace(**schema_ns)),
                      capsule=SimpleNamespace(safe_path=traced_safe),SNAPSHOT=FIXTURE)
ns={'state':state,'deepcopy':deepcopy,'REFERENCE':reference}
for node in trees[str(TARGET)].body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'QUOTED_REFERENCE','UNIT','SCHEMA'} for t in node.targets):
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<target schema only>','exec'),ns)
    elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=="SCHEMA['required'].append":
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<target required schema only>','exec'),ns)
extract(trees[str(TARGET)],['raw_path','validate_coverage'],ns)
SCHEMA=ns['SCHEMA']
Draft202012Validator.check_schema(SCHEMA)
validator=Draft202012Validator(SCHEMA)
def unit(path,i=1):
    return {'id':'u'+str(i),'basis':'reference-design' if path.startswith('reference-designs/') else 'observed-source',
            'statementUnit':'synthetic unit '+str(i),'references':[{'path':path,'startLine':1,'endLine':1,'quote':contents[path].splitlines()[0]}],
            'canonicalLocation':'# Synthetic / line 2','assessment':'covered','reason':'Synthetic exact correspondence'}
positive={'documentId':'TOY-DOC','approved':True,'findings':[],'unresolved':[],
          'coverageAudit':{'materialPathsRead':closure,'sourceToCanonical':[unit(p,i) for i,p in enumerate(closure,1)],
                           'canonicalToSource':[unit(p,i+10) for i,p in enumerate(closure,1)],'omittedOrUnreadMaterials':[]}}
results=[]
def check(name,mutator=lambda a:None,expected='ACCEPT',extra=None):
    a=deepcopy(positive);mutator(a);safe_reads.clear()
    try:
        validator.validate(a)
        workflow_ns['references_valid'](a,manifest)
        ns['validate_coverage'](a,manifest,{'materialClosure':closure})
        if a['approved'] and (a['unresolved'] or any(f['severity'] in {'critical','major'} for f in a['findings'])):
            raise ValueError('Mirrored main approval contradiction gate')
        actual='ACCEPT';error=None
    except Exception as exc:actual='REJECT';error=type(exc).__name__+': '+str(exc).splitlines()[0]
    row={'name':name,'expected':expected,'actual':actual,'passed':actual==expected,'error':error,'rawSafePathCalls':len(safe_reads)}
    if extra:row.update(extra)
    results.append(row)
def change_unit(direction,field,value,index=0):return lambda a:a['coverageAudit'][direction][index].__setitem__(field,value)
def change_ref(field,value,index=0):return lambda a:a['coverageAudit']['sourceToCanonical'][index]['references'][0].__setitem__(field,value)
check('positive exact 3 material bidirectional quoted ledger')
check('material read omission',lambda a:a['coverageAudit']['materialPathsRead'].pop(), 'REJECT')
check('material read extra',lambda a:a['coverageAudit']['materialPathsRead'].append('outside.txt'),'REJECT')
check('material read duplicate',lambda a:a['coverageAudit']['materialPathsRead'].append(closure[0]),'REJECT')
check('omitted material plus approved',lambda a:a['coverageAudit']['omittedOrUnreadMaterials'].append(closure[0]),'REJECT')
for direction in ['sourceToCanonical','canonicalToSource']:
    check(direction+' empty',lambda a,d=direction:a['coverageAudit'].__setitem__(d,[]),'REJECT')
    check(direction+' duplicate IDs',lambda a,d=direction:a['coverageAudit'][d].append(deepcopy(a['coverageAudit'][d][0])),'REJECT')
    for assessment in ['partial','missing','contradicted','unsubstantiated']:
        check(direction+' approved '+assessment,change_unit(direction,'assessment',assessment),'REJECT')
check('source unit no raw reference',change_unit('sourceToCanonical','references',[]),'REJECT')
check('covered canonical unit no raw reference',change_unit('canonicalToSource','references',[]),'REJECT')
check('indexed alias evidence',change_ref('path','indexed/a.txt'),'REJECT')
check('source alias without sources prefix',change_ref('path','a.txt'),'REJECT')
check('manifest evidence',change_ref('path','manifest.json'),'REJECT')
check('outside raw closure',change_ref('path','sources/missing.txt'),'REJECT')
check('path traversal',change_ref('path','sources/../../outside.txt'),'REJECT')
check('wrong basis',change_unit('sourceToCanonical','basis','observed-source'),'REJECT')
check('start line zero',change_ref('startLine',0),'REJECT')
check('end beyond range',change_ref('endLine',400),'REJECT')
check('reverse line range',change_ref('startLine',2),'REJECT')
check('boolean start line',change_ref('startLine',True),'REJECT')
check('forged quote',change_ref('quote','never present'),'REJECT')
check('concatenated noncontiguous quote',change_ref('quote','design one\ndesign three'),'REJECT')
check('empty quote',change_ref('quote',''),'REJECT')
check('quote from wrong exact row',change_ref('quote','design two'),'REJECT')
check('valid substring quote is accepted intentionally',change_ref('quote','design'))
check('valid contiguous multiline quote',lambda a:(change_ref('endLine',2)(a),change_ref('quote','design one\ndesign two')(a)))
check('primary design unit absent',lambda a:a['coverageAudit'].__setitem__('sourceToCanonical',[unit('sources/a.txt',1)]),'REJECT')
check('unknown assessment',change_unit('sourceToCanonical','assessment','accepted'),'REJECT')
check('unknown basis',change_unit('sourceToCanonical','basis','guessed'),'REJECT')
check('extra unit schema field',change_unit('sourceToCanonical','extra',True),'REJECT')
check('missing canonical field',lambda a:a['coverageAudit']['canonicalToSource'][0].pop('canonicalLocation'),'REJECT')
check('approved unresolved contradiction',lambda a:a['unresolved'].append('unresolved'),'REJECT')
for severity in ['critical','major']:
    check('approved '+severity+' finding contradiction',lambda a,s=severity:a['findings'].append({'severity':s,'documentLocation':'Synthetic','defect':'Synthetic','repairDirection':'Synthetic','references':[]}),'REJECT')
check('finding outside closure',lambda a:a['findings'].append({'severity':'minor','documentLocation':'Synthetic','defect':'Synthetic','repairDirection':'Synthetic','references':[{'path':'outside.txt','startLine':1,'endLine':1}]}),'REJECT')
# These accepted negatives are gaps, not approval positives.
check('GAP primary 1 row only despite 3 materials read',lambda a:a['coverageAudit'].__setitem__('sourceToCanonical',[unit(reference,1)]),extra={'gap':'MATERIAL_LEDGER_NOT_EXHAUSTIVE'})
check('GAP canonical ledger one unit only',lambda a:a['coverageAudit'].__setitem__('canonicalToSource',[unit(reference,1)]),extra={'gap':'CANONICAL_UNIT_COMPLETENESS_AI_ONLY'})
check('GAP empty covered canonical location',change_unit('sourceToCanonical','canonicalLocation',''),extra={'gap':'CANONICAL_LOCATION_NOT_VALIDATED'})
check('GAP nonexistent covered canonical location',change_unit('canonicalToSource','canonicalLocation','line 99999 / # DOES NOT EXIST'),extra={'gap':'CANONICAL_LOCATION_NOT_VALIDATED'})
for field in ['id','statementUnit','reason']:
    check('GAP empty '+field,change_unit('sourceToCanonical',field,''),extra={'gap':'UNIT_TEXT_CAN_BE_EMPTY'})
check('GAP all canonical units excluded without refs/reason',lambda a:a['coverageAudit'].__setitem__('canonicalToSource',[{'id':'excluded','basis':'observed-source','statementUnit':'','references':[],'canonicalLocation':'','assessment':'scope-excluded','reason':''}]),extra={'gap':'UNJUSTIFIED_CANONICAL_EXCLUSION'})
check('nonapproved missing canonical no refs is accepted',lambda a:(a.__setitem__('approved',False),change_unit('canonicalToSource','assessment','missing')(a),change_unit('canonicalToSource','references',[])(a)))

# Confirm schema transport nodes carry type on enums/const and roundtrip.
untyped=[]
def walk(value,path='$'):
    if isinstance(value,dict):
        if ('enum' in value or 'const' in value) and 'type' not in value:untyped.append(path)
        for k,v in value.items():walk(v,path+'/'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):walk(v,path+'/'+str(i))
walk(SCHEMA)
results.append({'name':'transport all enums typed, JSON roundtrip','expected':'PASS','actual':'PASS' if not untyped and json.loads(json.dumps(SCHEMA))==SCHEMA else 'FAIL','passed':not untyped,'untyped':untyped})
# Pure code AST retention. No prepare/main executes and no production imports occur.
target_funcs={n.name:n for n in trees[str(TARGET)].body if isinstance(n,ast.FunctionDef)}
generic_funcs={n.name:n for n in trees[str(GENERIC)].body if isinstance(n,ast.FunctionDef)}
ast_retention={name:ast.dump(target_funcs[name],include_attributes=False)==ast.dump(generic_funcs[name],include_attributes=False) for name in ['sha','load']}
main_text=ast.unparse(target_funcs['main']);prep_text=ast.unparse(target_funcs['prepare'])
guards={'same capsule/plan/contract/runtime/helper fixed':all(s in prep_text for s in ['state.MANIFEST_SHA','state.PLAN_SHA','state.CONTRACT_SHA','state.RUNTIME_RECORD_SHA','HELPER_SHA']),
        'plan handoff bytes and meaning':all(s in prep_text for s in ['plan-handoff.json',"plan_handoff['snapshot'] != capsule_state","plan_handoff['planSha256'] != state.PLAN_SHA"]),
        'raw completed analysis revalidation':'state.workflow._resume_analysis' in prep_text,
        'fresh job gate':"if job.exists():" in main_text,
        'same 2400 bounded deadline':"2400, capsule_state, args.deadline" in main_text,
        'pre AI and after/finally unchanged':prep_text.count('state.assert_unchanged(metadata)')==1 and main_text.count('state.assert_unchanged(metadata)')==2,
        'all writes to fresh job':all('job /' in ast.unparse(n.args[0]) for n in ast.walk(target_funcs['main']) if isinstance(n,ast.Call) and ast.unparse(n.func)=='state.capsule.write_json'),
        'no subprocess/app execution':not any(isinstance(n,ast.Call) and ast.unparse(n.func).split('.')[0] in {'subprocess','exec','eval','os','shutil'} for n in ast.walk(target_funcs['main']))}
after={str(p):digest(p) for p in CODE};assert before==after
report={'schema':'code-only-fidelity-helper-audit/1','time':datetime.now(timezone.utc).isoformat(),
        'scope':'CODE_AND_SYNTHETIC_AST_FUNCTIONS_ONLY','status':'REVIEW_REQUIRED','target':str(TARGET),'targetSha256':EXPECTED,
        'codeBefore':before,'codeAfter':after,'productionCodeUnchanged':True,'syntheticCaseCount':len(results),'syntheticPassed':sum(r['passed'] for r in results),
        'cases':results,'pureFunctionAstUnchanged':ast_retention,'retainedPrepareMainGuards':guards,
        'findings':[{'id':'F1','severity':'major','codeLocation':'validate_coverage materialPathsRead and ledger loops',
                     'observation':'An approved ledger can cite only one primary-reference row while declaring all three synthetic materials read. Other material representation/disposition and full reference line accounting are not mechanically required.',
                     'limit':'Complete semantic unit enumeration cannot be proven by line coverage. Do not infer a production omission from this synthetic acceptance.',
                     'repair':'Add exact per-material raw range disposition/read ledger, justify exclusions, and require semantic unit references to accounted ranges; retain AI semantic judgment and report it separately.'},
                    {'id':'F2','severity':'major','codeLocation':'UNIT and validate_coverage',
                     'observation':'Covered unit with empty/nonexistent canonicalLocation passes; all canonical units may be scope-excluded with blank statement/reason and no references.',
                     'repair':'Use fixed canonical SHA plus exact existing heading/line ranges for represented units; require nonblank unit text/ID/reason and reasoned exclusion. This establishes location existence, not semantic completeness.'}],
        'notPerformed':['Production snapshot/reference/canonical/analysis/PIN reads','prepare/main/provider','Actual review/application/SQL/browser','Original rubric/expected/score reads','Semantic fidelity and whole-original unit completeness'],
        'counters':{'actualProvider':0,'productionMaterialRead':0,'actualPrepare':0,'actualCanonicalWrites':0}}
(HERE/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'report':str(HERE/'review.json'),'sha256':digest(HERE/'review.json'),'cases':len(results),'passed':sum(r['passed'] for r in results),'status':report['status'],'guards':guards},ensure_ascii=False))
assert all(r['passed'] for r in results)
assert all(guards.values())
