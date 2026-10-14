import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\training-assisted')
paths=[BASE/'review_search_basic_fidelity_v1.py',BASE/'review_search_basic_fidelity_v2.py']
trees=[ast.parse(p.read_text(encoding='utf-8-sig')) for p in paths]
funcs=[{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)} for t in trees]
same={name:ast.dump(funcs[0][name],include_attributes=False)==ast.dump(funcs[1][name],include_attributes=False) for name in ['prepare','raw_path','sha','load']}
constants=[]
for tree in trees:
    constants.append({n.targets[0].id:ast.dump(n.value,include_attributes=False) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'DOCUMENT_ID','PARENT_SHA','PIN','PIN_SHA','REFERENCE','REFERENCE_SHA','HELPER_SHA','SCOPE'}})
report={'scope':'CODE_ONLY_AST_DELTA','v1Sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'v2Sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),
        'unchangedFunctions':same,'exactDocParentReferenceRuntimeScopeConstantsUnchanged':constants[0]==constants[1],
        'changedFunctions':[name for name in funcs[0] if ast.dump(funcs[0][name],include_attributes=False)!=ast.dump(funcs[1][name],include_attributes=False)],
        'changes':'Only UNIT schema/validate_coverage and main prompt+numbered canonical+coverage metric reporting; prepare pins/runtime/inventory/closure/resume unchanged.',
        'productionMaterialReads':0,'providerInvocations':0}
assert all(same.values()) and constants[0]==constants[1]
(HERE/'delta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(HERE/'delta.json'),'sha256':hashlib.sha256((HERE/'delta.json').read_bytes()).hexdigest(),'unchangedFunctions':same}))
