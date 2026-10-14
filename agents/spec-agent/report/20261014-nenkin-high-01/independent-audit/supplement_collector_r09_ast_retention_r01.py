"""Ordered recursive AST retention proof. Technical Python source only."""
from pathlib import Path
import ast, copy, hashlib, json
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01'
AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
OLD=WORK/'collect_reviewed_r08.py'; NEW=WORK/'collect_reviewed_r09.py'
OLD_SHA='2848e50ff84671608dfada5dece254ec15e80afe0ae55df5de41cf22abf345e3'
NEW_SHA='3788d437323b5db059a3afd908d7ba0dbd3b1dcd3ec7395502fe77e95c3392bc'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(OLD)==OLD_SHA and sha(NEW)==NEW_SHA
old,new=ast.parse(OLD.read_bytes()),ast.parse(NEW.read_bytes())
def equal_with_statement_insertions(left,right):
    if type(left) is not type(right): return False
    if isinstance(left,ast.AST):
        for field in left._fields:
            a,b=getattr(left,field,None),getattr(right,field,None)
            if field in {'body','orelse','finalbody'} and isinstance(a,list) and isinstance(b,list) and all(isinstance(x,ast.stmt) for x in a+b):
                if not ordered_statement_subsequence(a,b): return False
            elif not equal_with_statement_insertions(a,b): return False
        return True
    if isinstance(left,list):
        return len(left)==len(right) and all(equal_with_statement_insertions(a,b) for a,b in zip(left,right))
    return left==right
def ordered_statement_subsequence(original,candidate):
    cursor=0
    for statement in original:
        while cursor<len(candidate) and not equal_with_statement_insertions(statement,candidate[cursor]): cursor+=1
        if cursor==len(candidate): return False
        cursor+=1
    return True
tests=[]
def check(name,condition):
    tests.append({'name':name,'passed':bool(condition)})
oldmain=next(node for node in old.body if isinstance(node,ast.FunctionDef) and node.name=='main')
newmain=next(node for node in new.body if isinstance(node,ast.FunctionDef) and node.name=='main')
check('complete module original statements retained recursively in order',equal_with_statement_insertions(old,new))
check('all main statements retained recursively in order',equal_with_statement_insertions(oldmain,newmain))
oldconstants=[node for node in old.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id.isupper()]
check('all original constants remain exact AST',all(any(ast.dump(node,include_attributes=False)==ast.dump(other,include_attributes=False) for other in new.body) for node in oldconstants))
oldfunctions=[node for node in old.body if isinstance(node,ast.FunctionDef) and node.name!='main']
check('all other original functions remain exact AST',all(any(ast.dump(node,include_attributes=False)==ast.dump(other,include_attributes=False) for other in new.body) for node in oldfunctions))
critical=[]
for node in ast.walk(oldmain):
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
        call=node.value
        if isinstance(call.func,ast.Name) and call.func.id=='require': critical.append(node)
    if isinstance(node,(ast.Import,ast.ImportFrom)): critical.append(node)
check('all original main require statements and imports exact AST',all(any(ast.dump(node,include_attributes=False)==ast.dump(other,include_attributes=False) for other in ast.walk(newmain)) for node in critical))
synthetic=copy.deepcopy(oldmain)
synthetic.body.insert(0,ast.Expr(value=ast.Constant(value='new purely synthetic statement')))
check('retention proof accepts inserted statement',equal_with_statement_insertions(oldmain,synthetic))
synthetic=copy.deepcopy(oldmain); synthetic.body.pop(0)
check('retention proof rejects omitted original statement',not equal_with_statement_insertions(oldmain,synthetic))
synthetic=copy.deepcopy(oldmain); synthetic.body[0],synthetic.body[1]=synthetic.body[1],synthetic.body[0]
check('retention proof rejects reordered original statements',not equal_with_statement_insertions(oldmain,synthetic))
synthetic=copy.deepcopy(oldmain)
target=next(node for node in ast.walk(synthetic) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='require')
target.args[0]=ast.Constant(value=True)
check('retention proof rejects weakened original require condition',not equal_with_statement_insertions(oldmain,synthetic))
synthetic=copy.deepcopy(oldmain)
inner=next(node for node in ast.walk(synthetic) if isinstance(node,ast.FunctionDef) and node.name=='provider_answer')
inner.body.pop(0)
check('retention proof rejects nested provider statement deletion',not equal_with_statement_insertions(oldmain,synthetic))
synthetic=copy.deepcopy(oldmain)
loop=next(node for node in ast.walk(synthetic) if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='item')
loop.body[0],loop.body[1]=loop.body[1],loop.body[0]
check('retention proof rejects document-loop statement reorder',not equal_with_statement_insertions(oldmain,synthetic))
assert sha(OLD)==OLD_SHA and sha(NEW)==NEW_SHA
report={'schema':'spec-agent-collector-ordered-ast-retention/1','reviewer':'/root/delivery_root_review/supplement_collector_review',
    'baseline':{'path':str(OLD),'sha256':OLD_SHA},'candidate':{'path':str(NEW),'sha256':NEW_SHA},
    'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},
    'status':'PASS_ORDERED_AST_RETENTION_ONLY' if all(item['passed'] for item in tests) else 'HOLD_AST_RETENTION',
    'testCount':len(tests),'passedCount':sum(item['passed'] for item in tests),'tests':tests,
    'originalMainStatementCountIncludingNested':sum(isinstance(node,ast.stmt) for node in ast.walk(oldmain)),
    'originalMainRequireAndImportStatementCount':len(critical),'originalConstantCount':len(oldconstants),
    'limitations':{'codeReadOnly':True,'actualCollectorImportedOrRun':False,'providerOrFrozenPipelineImportedOrRun':False,
        'realInputRead':False,'authorRecordsRead':False,'realCompatibilityApproval':False,'nativeApproval':False,
        'atomicOrRaceFreeProof':False}}
out=AUDIT/'supplement-collector-r09-ordered-ast-retention-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream: json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'testCount':len(tests),'passedCount':report['passedCount'],'report':str(out),'sha256':sha(out),'failures':[item for item in tests if not item['passed']]}))
if not all(item['passed'] for item in tests): raise SystemExit(1)
