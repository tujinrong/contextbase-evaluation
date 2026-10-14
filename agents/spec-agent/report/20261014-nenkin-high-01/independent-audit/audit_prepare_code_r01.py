"""Code-only AST and toy namespace audit. Never execute production prepare_run."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json,hashlib,tempfile,types
REPO=Path(r'D:/開発/contextbase-evaluation')
SOURCE=REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01/prepare_run.py'
HERE=Path(__file__).resolve().parent
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()=='53746831305a94d79c58cf48260485559044e3ae97f0e54402b6a6352f9c9167'
tree=ast.parse(raw);cases=[]
def check(name,ok):
 assert ok,name
 cases.append({'name':name,'passed':True})
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
check('only helper functions sha and fresh',set(functions)=={'sha','fresh'})
check('only import pathlib datetime hashlib json and capsule',all((isinstance(n,ast.Import) and all(a.name in {'hashlib','json'} for a in n.names)) or (isinstance(n,ast.ImportFrom) and n.module in {'pathlib','datetime','contextbase.ai'}) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))))
check('no subprocess application database shell provider invocation',not any(isinstance(n.func,ast.Name) and n.func.id in {'exec','eval','system'} for n in calls))
output_uses=[n for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id=='OUTPUT' and isinstance(n.ctx,ast.Load)]
check('output used only for root comparison and metadata',len(output_uses)==2)
fresh_calls=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='fresh']
check('three fresh metadata writes',len(fresh_calls)==3)
check('fresh writes only selected REPORT or WORK',all(isinstance(n.args[0],ast.BinOp) and isinstance(n.args[0].left,ast.Name) and n.args[0].left.id in {'REPORT','WORK'} for n in fresh_calls))
create_calls=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='create']
check('single capsule creation from INPUT to snapshot',len(create_calls)==1 and [ast.unparse(x) for x in create_calls[0].args]==['INPUT','snapshot'])
check('AG-SPEC role explicit',raw.count(b"'agentRole': 'AG-SPEC'")==2)
check('source-only and original/evaluation refusal explicit',b"'originalSpecificationsAuthorized': False" in raw and b"'evaluationExpectationsAuthorized': False" in raw and b"'sourceOnly': True" in raw)
check('application execution explicitly unauthorized',b"'originalProgramsAndDatabaseExecutionAuthorized': False" in raw)
check('128 file inventory equality explicit',b"actual_runtime == runtime['files'] and len(actual_runtime) == 128" in raw)
check('exact loaded capsule source path and bytes checked',b"capsule.__file__" in raw and b"runtime['files']['contextbase/ai/capsule.py']" in raw)
check('capsule source-only mode verify explicit',b"capsule.reference_mode(capsule.verify(snapshot)) == 'source-only'" in raw)
check('engineering tests not project qualification explicit',b"infrastructure evidence, not this project quality or formal95" in raw)
checks=[]
def fake_safe(p):
 p=Path(p)
 checks.append(str(p))
 if p.name=='rejected.json':raise ValueError('Synthetic rejected path')
 return p
ns={'capsule':types.SimpleNamespace(safe_path=fake_safe),'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=list(functions.values()),type_ignores=[]),str(SOURCE),'exec'),ns)
with tempfile.TemporaryDirectory(prefix='spec-agent-code-audit-',dir=HERE) as t:
 root=Path(t);p=root/'safe.json'
 ns['fresh'](p,{'toy':True});check('fresh positive writes toy JSON only',json.loads(p.read_text())=={'toy':True})
 data=p.read_bytes()
 try:ns['fresh'](p,{'overwrite':True})
 except FileExistsError:check('fresh existing-file refuses overwrite',p.read_bytes()==data)
 else:raise AssertionError('existing file overwritten')
 blocked=root/'rejected.json'
 try:ns['fresh'](blocked,{'toy':True})
 except ValueError:check('fresh rejected safe_path occurs before file creation',not blocked.exists())
 else:raise AssertionError('unsafe file accepted')
 check('sha positive goes through safe_path',ns['sha'](p)==hashlib.sha256(data).hexdigest() and checks[-1]==str(p))
 try:ns['sha'](blocked)
 except ValueError:check('sha rejected path before read',True)
 else:raise AssertionError('unsafe read accepted')
check('production prepare bytes unchanged',SOURCE.read_bytes()==raw)
findings=[
 {'severity':'MEASUREMENT_GAP','location':'final print and run outputRoot','detail':'oldOutputChanged=False is inferred from absence of output write calls; no old-output inventory before/after is collected. Do not present it as a measured full-output equality.'},
 {'severity':'MEASUREMENT_GAP','location':'protected input collection then capsule.create','detail':'The helper does not compare snapshot source hashes to protected-inputs-before nor recheck complete original input membership and bytes after sealing. Independent metadata verification is needed.'},
 {'severity':'DEFENSE_GAP','location':'registry.read_text before sha(registry)','detail':'The identities registry direct read is not preceded by capsule.safe_path. Hashing it later does not reject a linked path before read. Actual path/link status was not inspected by this code-only audit.'},
 {'severity':'MEASUREMENT_GAP','location':'runtime receipt and source inventory','detail':'Runtime full inventory and loaded capsule are checked before create, but receipt/full membership are not rechecked afterward and other loaded AI modules are not checked here. A separate plan launcher provenance check must cover the modules it uses.'}
]
result={'schema':'spec-agent-independent-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'new nenkin spec-agent preparation metadata only','helper':str(SOURCE),'helperSha256':hashlib.sha256(raw).hexdigest(),'status':'PASS_WITH_MEASUREMENT_AND_DEFENSE_NOTES','cases':cases,'passed':len(cases),'failed':0,'findings':findings,'scopeBoundary':'AG-SPEC authoring role and contextbase.ai infrastructure are explicitly separate; no old ASP.NET prose, expected values or qualification is transferred. The fixed script writes fresh metadata/snapshot only. Reachable n2framework subset selection is deferred to independent plan review.','actualProductionPrepareExecuted':False,'providerExecuted':False,'applicationOrDatabaseOrSourceScriptExecuted':False,'productionSourceBodyRead':False,'originalSpecificationOrExpectedOrOldOutputBodyRead':False,'oldPilotHandoff':{'sourceOnlyBaseline':'CLOSED','r19CompositeR02CodeAudit':'67/67 synthetic PASS; actual helper execution not performed by this reviewer','oplogColumnE12NativeQa':'6/6 ranges personally viewed before old deadline; PASS geometry only; old HOLD retained; formal/adoption approval false'},'limitations':['Only AST and extracted sha/fresh functions were executed against toy files. The production top level and capsule.create were not executed.','No actual junction is exercised here; safety delegation is verified with a rejecting stub.','Actual source snapshot/full inventory and module imports await pinned metadata audit.','Assertions require normal non-optimized Python; this audit did not execute under -O.']}
out=HERE/'prepare-code-review-r01.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'passed':len(cases),'findings':len(findings),'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
