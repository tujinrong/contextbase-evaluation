"""Code-only AST delta and owned synthetic probes; never execute helper main."""
import ast,copy,hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[3]/'.tmp/20261013-rerun-12h/training-assisted'
V2=BASE/'prepare_fidelity_reuse_v2.py'
V3=BASE/'prepare_fidelity_reuse_v3.py'
EXPECTED='4c021b0b332ec05bcc879c8547d44881327ca7b48b457df511a5d21495e231e7'
SEARCH='CSHARP_ASPNET-BAS-STU-01'
SEARCH_FILE='review_search_basic_fidelity_v2.py'
SEARCH_SHA='ac28f04d4026fec974619f8394fe4997dcea91c6f9c3b0efa3c8926183abda15'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
initial={str(p):digest(p) for p in (V2,V3,BASE/SEARCH_FILE)}
assert initial[str(V3)]==EXPECTED and initial[str(BASE/SEARCH_FILE)]==SEARCH_SHA
t2,t3=[ast.parse(p.read_text(encoding='utf-8-sig')) for p in (V2,V3)]
def literal(tree,name):
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
h2,h3=literal(t2,'HELPERS'),literal(t3,'HELPERS')
def dump(n):return ast.dump(n,include_attributes=False)
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
main3=function(t3,'main')
coverage_if=next(n for n in main3.body if isinstance(n,ast.If) and 'validate_coverage' in ast.unparse(n))
tests=[]
def check(name,condition):
    assert condition,name
    tests.append({'name':name,'passed':True})
def rejects(name,fn):
    try:fn()
    except (ValueError,KeyError,TypeError):check(name,True)
    else:raise AssertionError(name+' accepted')

check('fixed v3 code SHA',digest(V3)==EXPECTED)
check('registered search filename and fixed inspected v2 SHA',h3[SEARCH]==(SEARCH_FILE,SEARCH_SHA))
check('new registry adds only search role',set(h3)==set(h2)|{SEARCH})
check('existing two role mappings unchanged',all(h3[k]==h2[k] for k in h2))
check('registered coverage helper code SHA unchanged',digest(BASE/SEARCH_FILE)==SEARCH_SHA)
for name in ['sha','load','canonical_material']:
    check(name+' AST unchanged',dump(function(t2,name))==dump(function(t3,name)))
check('new conditional is exact search role only',dump(coverage_if.test)==dump(ast.parse("args.document_id=='CSHARP_ASPNET-BAS-STU-01'",mode='eval').body))
check('coverage call receives review manifest old exactly',dump(coverage_if.body[0])==dump(ast.parse('module.validate_coverage(review,manifest,old)').body[0]) and len(coverage_if.body)==1 and not coverage_if.orelse)

normalized=copy.deepcopy(t3)
for n in normalized.body:
    if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HELPERS' for x in n.targets):
        n.value=copy.deepcopy(next(a.value for a in t2.body if isinstance(a,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HELPERS' for x in a.targets)))
    if isinstance(n,ast.FunctionDef) and n.name=='main':
        n.body=[x for x in n.body if not (isinstance(x,ast.If) and 'validate_coverage' in ast.unparse(x))]
        old_instruction=next(x.value for x in ast.walk(t2) if isinstance(x,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='instructions' for k in x.keys) for k,x in zip(x.keys,x.values) if isinstance(k,ast.Constant) and k.value=='instructions')
        for d in ast.walk(n):
            if isinstance(d,ast.Dict):
                for i,k in enumerate(d.keys):
                    if isinstance(k,ast.Constant) and k.value=='instructions':d.values[i]=ast.Constant(old_instruction)
check('all inherited imports constants guard flow and writes AST exact after three declared deltas',dump(normalized)==dump(t2))

positions={ast.unparse(n):i for i,n in enumerate(main3.body)}
ci=main3.body.index(coverage_if)
refi=next(i for i,n in enumerate(main3.body) if ast.unparse(n).startswith('workflow.references_valid('))
bindingi=next(i for i,n in enumerate(main3.body) if isinstance(n,ast.If) and 'Fresh fidelity input/review/handoff/completion binding differs' in ast.unparse(n))
resumei=next(i for i,n in enumerate(main3.body) if 'workflow._resume_analysis(' in ast.unparse(n))
writei=next(i for i,n in enumerate(main3.body) if ast.unparse(n).startswith('capsule.write_json('))
check('reference validator before new coverage validator',refi<ci)
check('coverage before handoff binding and raw pin collection',ci<bindingi)
check('coverage before resumed analysis and original reference read',ci<resumei)
check('coverage before all output writes',ci<writei)

# Execute only the isolated new conditional with toy spies and no helper imports.
code=compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(coverage_if)],type_ignores=[])),'<isolated-coverage-dispatch>','exec')
toy_review={'coverageAudit':'owned toy'};toy_manifest={'files':[]};toy_old={'rawMaterialPaths':['sources/toy.cs']}
def dispatch(role,reject=False):
    calls=[]
    def validator(*values):
        calls.append(values)
        if reject:raise ValueError('Synthetic invalid unit ledger')
    ns={'args':types.SimpleNamespace(document_id=role),'module':types.SimpleNamespace(validate_coverage=validator),'review':toy_review,'manifest':toy_manifest,'old':toy_old}
    exec(code,ns)
    return calls
calls=dispatch(SEARCH)
check('search dispatch executes validator once',len(calls)==1)
check('validator preserves exact object identities',calls[0][0] is toy_review and calls[0][1] is toy_manifest and calls[0][2] is toy_old)
for role in h2:check('existing role skips search coverage: '+role,dispatch(role,reject=True)==[])
rejects('invalid coverage immediately rejects search preparation',lambda:dispatch(SEARCH,True))

# Execute only the existing fixed-helper SHA gate with safe toy metadata.
helper_gate=next(n for n in main3.body if isinstance(n,ast.If) and 'The independently inspected fidelity helper changed' in ast.unparse(n))
gate_code=compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(helper_gate)],type_ignores=[])),'<isolated-fixed-helper-sha>','exec')
def fixed_gate(actual,expected):exec(gate_code,{'sha':lambda _:actual,'helper':'owned-code-fixture','expected':expected})
fixed_gate(SEARCH_SHA,SEARCH_SHA);check('fixed helper hash positive control',True)
rejects('helper byte drift rejected before helper import/prepare',lambda:fixed_gate('0'*64,SEARCH_SHA))
check('helper SHA gate precedes dynamic loader and prepare',main3.body.index(helper_gate)<next(i for i,n in enumerate(main3.body) if 'spec_from_file_location' in ast.unparse(n))<next(i for i,n in enumerate(main3.body) if 'module.prepare()' in ast.unparse(n)))

# Alias closure behavior runs the unchanged pure function on a toy source manifest.
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(function(t3,'canonical_material'))],type_ignores=[])),'<toy-alias>','exec'),ns)
cm=ns['canonical_material'];paths={'Core/Toy.cs'}
check('bare source alias canonicalized',cm('Core/Toy.cs',paths)=='sources/Core/Toy.cs')
check('indexed source alias canonicalized',cm('indexed/Core/Toy.cs.txt',paths)=='sources/Core/Toy.cs')
check('reference path preserved',cm('reference-designs/toy.md',paths)=='reference-designs/toy.md')
check('unknown bare path not invented as source',cm('Absent.cs',paths)=='Absent.cs')
required={cm(p,paths) for p in ['indexed/Core/Toy.cs.txt','reference-designs/toy.md']}
read={cm(p,paths) for p in ['Core/Toy.cs','reference-designs/toy.md']}
check('same closure positive reuse set control',not required-read)
check('new dependency requires unparsed disposition',bool((required|{'sources/New.cs'})-read))

instruction=next(x.value for x in ast.walk(t3) if isinstance(x,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='instructions' for k in x.keys) for k,x in zip(x.keys,x.values) if isinstance(k,ast.Constant) and k.value=='instructions')
for text in ['完全MD','双方向unit ledger','全イベント全分岐','source実装とreference-design','完了factsは不変','元画像未閲覧・実アプリ未実行','採点/rubric/expected','source-only成果物は参照しない']:
    check('generic writer boundary/granularity instruction: '+text,text in instruction)
check('instructions contain no numeric business acceptance data',not any(s in instruction for s in ['E-STU','10000','PageSize=','Cookie.Name']))
check('helper code pins unchanged after audit',initial=={p:digest(Path(p)) for p in initial})

report={'schema':'code-only-independent-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'subject':str(V3),'subjectSha256':EXPECTED,'comparison':str(V2),'comparisonSha256':initial[str(V2)],
 'scope':'HELPER_CODE_AST_AND_ISOLATED_SYNTHETIC_FIXTURES_ONLY','status':'TECHNICAL_PASS_WITH_SCOPE_LIMITS',
 'tests':tests,'testCount':len(tests),'passedCount':len(tests),'findings':[],
 'declaredChanges':['Exact search helper filename/SHA registration','Search-only v2 coverage validation before binding/reuse/output','Domain-neutral complete-draft granularity and evidence-boundary instructions'],
 'inheritedGuardsAstIdentical':True,'inputCodePins':initial,'inputCodeUnchanged':True,
 'productionCapsuleSourceReferenceCanonicalExpectedScoreAnswerReads':0,'actualPrepareMainProviderApplicationRuns':0,
 'limitations':['Actual prepare main, production helper dynamic import, production material reads, and output writes were not executed.',
  'Inherited guard flow is established by exact AST equivalence, not a fresh full production integration run.',
  'Coverage semantics and unit/exclusion completeness require independent AI/content review; this audit only establishes revalidation dispatch and retained code boundaries.',
  'The canonical_material indexed-alias behavior is inherited; this audit does not strengthen or claim an additional manifest-membership guard for that pure mapper.']}
out=HERE/'review.json'
if out.exists():raise FileExistsError('Fresh report required')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(out),'sha256':digest(out),'testCount':len(tests),'passedCount':len(tests),'status':report['status']},ensure_ascii=False))
