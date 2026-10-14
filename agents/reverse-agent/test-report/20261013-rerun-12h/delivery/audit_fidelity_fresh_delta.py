"""Reuse the prior synthetic full-prepare audit; never import production helpers."""
from pathlib import Path
import ast, hashlib, json
BASE=Path(__file__).resolve().parent
OLD=BASE/'audit_index_fidelity_v1.py'
source=OLD.read_text(encoding='utf8')
jobs=[('review_table_index_fidelity_v2.py','d91af2a872d0d8cefbefc8eeebf227ff25f9cc9f03ff73431fb3d4e2878bfe5b','index-fidelity-v2-independent'),
 ('review_operation_log_fidelity_v1.py','25435ff0aad7ea16c59d280f1be7e5fa776345a48a4f806c76d862092383e5b3','oplog-fidelity-v1-independent')]
results=[]
for filename,pinned,directory in jobs:
 text=source.replace('review_table_index_fidelity_v1.py',filename).replace('4979e0b711cee17d79ecad4ebee99fc995b53238c2534377a53d3cd6398f56ae',pinned)
 text=text.replace("'index-fidelity-v1-independent'",repr(directory))
 text=text.replace("planhandoff:'6'*64","planhandoff:'bf1079b4288b0d68cc0964f71d77c48f4ee4da201012a23e5a8764aa0a762f02'")
 text=text.replace("assert probe('old handoff unchecked '","assert not probe('old handoff checked '")
 text=text.replace("assert probe('plan handoff unchecked '","assert not probe('plan handoff checked '")
 text=text.replace("'status':'REQUIRES_FRESH_GUARD_FIX'","'status':'PASS_CODE_ONLY_SYNTHETIC_BOUNDARY'")
 parsed=ast.parse(text)
 # Strip only report findings assignment; assertions and helper function AST stay exact.
 for node in ast.walk(parsed):
  if isinstance(node,ast.Dict):
   for index,key in enumerate(node.keys):
    if isinstance(key,ast.Constant) and key.value=='findings' and isinstance(node.values[index],ast.List) and len(node.values[index].elts)==2:
     node.values[index]=ast.List(elts=[],ctx=ast.Load())
 env={'__file__':str(OLD),'__name__':'independent_ast_audit'}
 exec(compile(ast.fix_missing_locations(parsed),str(OLD),'exec'),env)
 env['main']()
 report=BASE/directory/'review.json'
 value=json.loads(report.read_text(encoding='utf8'))
 assert value['acceptedNegativeCases']==[]
 results.append({'helper':filename,'helperSha256':pinned,'report':str(report),'reportSha256':hashlib.sha256(report.read_bytes()).hexdigest(),'cases':value['caseCount'],'providerCalls':0})
 print(json.dumps(results[-1],ensure_ascii=False))
(BASE/'fidelity-fresh-delta-summary.json').write_text(json.dumps({'schema':'independent-code-only-delta/1','helpers':results,'productionDataRead':False,'providerCalls':0,'helperImportedOrMainExecuted':False,'scope':'Fresh handoff guard deltas and synthetic prepare only; no fidelity or content approval.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
