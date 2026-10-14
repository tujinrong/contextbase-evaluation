"""Independent code-only integration comparison; executes no production code."""
from pathlib import Path
import ast,hashlib,json,difflib
P=Path(__file__).resolve().parent
A=P.parents[2]
F=A/'.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-10/src'
M=A/'src'
OUT=P/'r19-integration-independent-code-audit-r01.json'
assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
 return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
before=inventory(F);current=inventory(M)
receipt=P.parent/'training-assisted/runtime-code-assisted-10.json'
assert sha(receipt)=='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
changed=sorted(k for k in before if current.get(k)!=before[k]);added=sorted(set(current)-set(before));deleted=sorted(set(before)-set(current))
assert changed==['contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py'],changed
assert added==['contextbase/ai/node_label_row_gate.py','contextbase/tests/test_ai_node_label_rows.py'],added
assert deleted==[]
gate=M/'contextbase/ai/node_label_row_gate.py'
assert gate.read_bytes()==(P/'node_label_row_gate_r05.py').read_bytes()
candidate_test=(P/'test_node_label_row_gate_r06.py').read_text(encoding='utf8')
main_test=(M/'contextbase/tests/test_ai_node_label_rows.py').read_text(encoding='utf8')
assert candidate_test.replace('from node_label_row_gate_r05 import','from contextbase.ai.node_label_row_gate import')==main_test
old_render=ast.parse((F/'contextbase/ai/rendering.py').read_text(encoding='utf8'))
new_render=ast.parse((M/'contextbase/ai/rendering.py').read_text(encoding='utf8'))
oldfn={n.name:ast.dump(n,include_attributes=False) for n in old_render.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
newfn={n.name:ast.dump(n,include_attributes=False) for n in new_render.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
changed_functions=sorted(k for k in oldfn if newfn.get(k)!=oldfn[k]);added_functions=sorted(set(newfn)-set(oldfn))
measurement=next(n for n in new_render.body if isinstance(n,ast.FunctionDef) and n.name=='_node_label_rows')
measure_literal=next(n.value for n in ast.walk(measurement) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('svg =>'))
assert measure_literal==(P/'measure_node_rows_r05.js').read_text(encoding='utf8')
new_test_ast=ast.parse((M/'contextbase/tests/test_ai_rendering.py').read_text(encoding='utf8'))
old_test_ast=ast.parse((F/'contextbase/tests/test_ai_rendering.py').read_text(encoding='utf8'))
old_tests={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(old_test_ast) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
new_tests={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(new_test_ast) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
assert all(new_tests.get(k)==v for k,v in old_tests.items())
extra_tests=sorted(set(new_tests)-set(old_tests));assert len(extra_tests)==3
diffs={r:''.join(difflib.unified_diff((F/r).read_text(encoding='utf8').splitlines(True),(M/r).read_text(encoding='utf8').splitlines(True),fromfile='frozen-assisted10-r18',tofile='main-r19')) for r in changed}
assert inventory(F)==before and inventory(M)==current
record={'schema':'independent-generic-code-integration-audit/1','scope':'CODE_ONLY_NO_PRODUCTION_IMPORT_OR_RENDER',
 'beforeRuntimeReceipt':str(receipt),'beforeRuntimeReceiptSha256':sha(receipt),'frozenFileCount':len(before),'currentFileCount':len(current),
 'beforeInventory':before,'afterInventory':current,'modifiedFiles':changed,'addedFiles':added,'deletedFiles':deleted,
 'candidateModuleByteExact':True,'candidateTestsImportOnlyChange':True,'measurementR05ByteExact':True,
 'changedFunctions':changed_functions,'addedFunctions':added_functions,'existingTestsAstUnchanged':True,'addedIntegrationTests':extra_tests,
 'manualReview':['Public original vertices parsed only after original mermaid.render; original SVG saved and semantic comparison retained.',
 'Canonical MMD writes/edge lexer/CSS/sanitizer/HTML body functions unchanged; width changes320to400 only trusted generic config.',
 'Node measurement runs after cluster projection in JS-disabled/network-aborted static browser; proof must complete before final PNG.',
 'Proof exceptions retained as ERROR/authorRevisionRequired; nonflow bypass remains original display.'],
 'findings':[{'severity':'BLOCKING_FOR_EFFECTIVE_VISIBILITY_PROOF','condition':'Computed transparent/rgba alpha0 fill is incorrectly accepted by integrated r05 measurement.',
 'negativeEvidence':str(P/'node-effective-fill-probe-r05-gap.json'),'negativeSha256':sha(P/'node-effective-fill-probe-r05-gap.json'),
 'freshCandidate':str(P/'measure_node_rows_r06.js'),'candidateSha256':sha(P/'measure_node_rows_r06.js'),
 'candidateProof':str(P/'node-effective-fill-probe-r06.json'),'candidateProofSha256':sha(P/'node-effective-fill-probe-r06.json')}],
 'inputCodeBeforeAfterUnchanged':True,'mainEditedByReviewer':False,'providerCalls':0,'productionInputsRead':False,'fullSuiteExecutedByReviewer':False,
 'status':'INTEGRATION_SCOPE_CONFIRMED_WITH_VISIBILITY_GAP','wholeApproval':False,'diffs':diffs}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':record['status'],'path':str(OUT),'sha256':sha(OUT),'modified':changed,'added':added,'functionDelta':changed_functions,'testDelta':extra_tests}))
