"""Independent repaired integration audit; AST/code only, no production imports."""
from pathlib import Path
import ast,hashlib,json,difflib
P=Path(__file__).resolve().parent
A=P.parents[2];F=A/'.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-10/src';M=A/'src'
OUT=P/'r19-integration-independent-code-audit-r02.json'
assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
 return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def functions(tree,tests=False):
 nodes=ast.walk(tree) if tests else tree.body
 return {n.name:ast.dump(n,include_attributes=False) for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and (not tests or n.name.startswith('test_'))}
receipt=P.parent/'training-assisted/runtime-code-assisted-10.json'
assert sha(receipt)=='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
before=inventory(F);current=inventory(M);frozen_receipt=json.loads(receipt.read_text(encoding='utf8'))
assert len(before)==126 and before==frozen_receipt['files'] and len(current)==128
changed=sorted(k for k in before if current.get(k)!=before[k]);added=sorted(set(current)-set(before));deleted=sorted(set(before)-set(current))
assert changed==['contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py']
assert added==['contextbase/ai/node_label_row_gate.py','contextbase/tests/test_ai_node_label_rows.py'] and not deleted
assert current['contextbase/ai/rendering.py']=='b7b5e79dc4184a9774bc8203a60142a9cec83e1ebc43be25db7d969ea6263edc'
assert current['contextbase/tests/test_ai_rendering.py']=='7ce6ac9c7c1c14975b6d270538ec5aa9a78e56fbf6bc6e5f46177c901f047c1b'
assert (M/added[0]).read_bytes()==(P/'node_label_row_gate_r05.py').read_bytes()
assert (P/'test_node_label_row_gate_r06.py').read_text(encoding='utf8').replace('from node_label_row_gate_r05 import','from contextbase.ai.node_label_row_gate import')==(M/added[1]).read_text(encoding='utf8')
old_ast=ast.parse((F/changed[0]).read_text(encoding='utf8'));new_ast=ast.parse((M/changed[0]).read_text(encoding='utf8'))
oldfn=functions(old_ast);newfn=functions(new_ast)
changed_functions=sorted(k for k in oldfn if newfn.get(k)!=oldfn[k]);added_functions=sorted(set(newfn)-set(oldfn))
assert changed_functions==['render_document'] and added_functions==['_node_label_rows']
measurement=next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name=='_node_label_rows')
literal=next(n.value for n in ast.walk(measurement) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('svg =>'))
assert literal==(P/'measure_node_rows_r06.js').read_text(encoding='utf8')
old_tests=functions(ast.parse((F/changed[1]).read_text(encoding='utf8')),True)
new_tests=functions(ast.parse((M/changed[1]).read_text(encoding='utf8')),True)
changed_tests=sorted(k for k in old_tests if new_tests.get(k)!=old_tests[k]);extra_tests=sorted(set(new_tests)-set(old_tests))
assert changed_tests==['test_mermaid_directive_cannot_lower_strict_security']
assert extra_tests==['test_actual_svg_transparent_fill_is_rejected_but_partial_alpha_is_visible','test_indivisible_oversized_node_token_is_rejected_before_final_png','test_node_literals_are_bound_to_visible_whole_tokens_and_original_source','test_unproven_node_effective_visibility_is_rejected_before_final_png']
diffs={r:''.join(difflib.unified_diff((F/r).read_text(encoding='utf8').splitlines(True),(M/r).read_text(encoding='utf8').splitlines(True),fromfile='frozen-assisted10-r18',tofile='main-r19-repaired-r02')) for r in changed}
evidence_names=['r19-integration-independent-code-audit-r01.json','node-effective-fill-probe-r05-gap.json','node-effective-fill-probe-r06.json']
evidence={str(P/n):sha(P/n) for n in evidence_names}
first=P.parent/'engine/all-ai-r19-root-r01.log';final=P.parent/'engine/all-ai-r19-root-r02.log'
assert first.exists() and final.exists()
logs={str(p):sha(p) for p in [first,final]}
assert inventory(F)==before and inventory(M)==current
record={'schema':'independent-generic-code-integration-audit/2','scope':'CODE_ONLY_NO_PRODUCTION_IMPORT_OR_RENDER','beforeRuntimeReceipt':str(receipt),'beforeRuntimeReceiptSha256':sha(receipt),'frozenFileCount':126,'currentFileCount':128,'beforeInventory':before,'afterInventory':current,'modifiedFiles':changed,'addedFiles':added,'deletedFiles':deleted,'candidateModuleByteExact':True,'candidateTestsImportOnlyChange':True,'measurementR06ByteExact':True,'measurementR06Sha256':sha(P/'measure_node_rows_r06.js'),'changedFunctions':changed_functions,'addedFunctions':added_functions,'changedExistingTests':changed_tests,'otherExistingTestsAstUnchanged':True,'addedIntegrationTests':extra_tests,
 'manualReview':['Trusted generic flowchart width is400; public original vertices parsed only after mermaid.render. Original MMD and insert-only view projection remain separate with original/view receipts.',
 'Only render_document and new node-measurement function differ from r18. Sanitizer, HTML body functions, CSS table projection, edge lexer and semantic SVG comparison remain unchanged.',
 'Strict security metadata is recorded before literal/row proof; safe original SVG is retained before a later proof ERROR. Unknown img markup now explicitly fails instead of receiving a display PASS.',
 'Changed legacy hostile test requires strict security, no blocked request, unknown-markup ERROR, authorRevisionRequired, original MD unchanged, no final PNG, and no source-SVG event attributes. This strengthens expected failure handling rather than weakening safety.',
 'Effective visibility rejects transparent/rgba alpha0/none/fillOpacity0 and ancestor display/visibility/opacity. Finite positive rectangles and node/canvas containment plus exact literal/whole ASCII-numeric row proof are mandatory.',
 'Final PNG occurs only after visible node proof. Exceptions retain ERROR and authorRevisionRequired. Nonflow display, semantic signatures and prior frozen r18 outputs are preserved.'],
 'historicalFailureEvidence':evidence,'preservedSuiteLogs':logs,'visibilityGapClosedByExactR06Candidate':True,'findings':[],
 'inputCodeBeforeAfterUnchanged':True,'mainEditedByReviewer':False,'providerCalls':0,'productionInputsRead':False,'fullSuiteExecutedByReviewer':False,'completeInertGuarantee':False,'status':'PASS_INDEPENDENT_CODE_ONLY_INTEGRATION_SCOPE','wholeApproval':False,'published':False,'diffs':diffs}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':record['status'],'path':str(OUT),'sha256':sha(OUT),'modified':{k:current[k] for k in changed},'added':{k:current[k] for k in added},'count':len(current),'findings':record['findings']}))
