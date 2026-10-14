"""Narrow renderer source/mirror delta review: AST only, no wrapper/core import."""
from pathlib import Path
import ast, hashlib, json
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01'; AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
OLD=WORK/'render_reviewed_r05.py'; NEW=WORK/'render_reviewed_r06.py'
OSHA='b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe'
NSHA='eada05d737ed3bbf9bf0173681eb117024c9a1fa49d778040de51bdd43b40b02'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(OLD)==OSHA and sha(NEW)==NSHA
old,new=ast.parse(OLD.read_bytes()),ast.parse(NEW.read_bytes())
ofd={node.name:node for node in old.body if isinstance(node,ast.FunctionDef)}
nfd={node.name:node for node in new.body if isinstance(node,ast.FunctionDef)}
tests=[]
def check(name,value):tests.append({'name':name,'passed':bool(value)})
def dump(node):return ast.dump(node,include_attributes=False)
check('all old non-main functions unchanged',all(dump(node)==dump(nfd[name]) for name,node in ofd.items() if name!='main'))
def calls(tree,name):return [node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id==name]
def terms(node):return {dump(item) for item in node.values} if isinstance(node,ast.BoolOp) and isinstance(node.op,ast.And) else {dump(node)}
oldguards=calls(ofd['main'],'require'); newguards=calls(nfd['main'],'require')
check('every old require preserved exactly or strengthened with added conjunction',all(any(
    len(a.args)>1 and len(b.args)>1 and dump(a.args[1])==dump(b.args[1]) and terms(a.args[0])<=terms(b.args[0])
    for b in newguards) for a in oldguards))
oldimports=[dump(node) for node in ast.walk(ofd['main']) if isinstance(node,(ast.Import,ast.ImportFrom))]
newimports=[dump(node) for node in ast.walk(nfd['main']) if isinstance(node,(ast.Import,ast.ImportFrom))]
check('original frozen imports retained and no added main imports',oldimports==newimports)
rendercall=next(node for node in ast.walk(nfd['main']) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='render_document')
check('actual render source is mirror',dump(rendercall.args[0])==dump(ast.Name(id='mirror_source',ctx=ast.Load())))
check('actual asset root is isolated mirror root',any(keyword.arg=='asset_root' and dump(keyword.value)==dump(ast.Name(id='mirror_root',ctx=ast.Load())) for keyword in rendercall.keywords))
check('render output remains original explicit output',dump(rendercall.args[1])==dump(ast.Name(id='output',ctx=ast.Load())))
pin_assign=next(node for node in ast.walk(nfd['main']) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='pins' for target in node.targets))
pins={key.value:value for key,value in zip(pin_assign.value.keys,pin_assign.value.values) if isinstance(key,ast.Constant)}
old_pin_assign=next(node for node in ast.walk(ofd['main']) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='pins' for target in node.targets))
oldpins={key.value:value for key,value in zip(old_pin_assign.value.keys,old_pin_assign.value.values) if isinstance(key,ast.Constant)}
check('all old pin values remain unchanged including original approved source',all(key in pins and dump(value)==dump(pins[key]) for key,value in oldpins.items()))
check('mirror renderer source pin is distinct explicit provenance',dump(pins['rendererSource'])==dump(ast.parse('str(mirror_source)',mode='eval').body) and 'citationMirror' in pins)
main_calls=calls(nfd['main'],'verify_citation_mirror')
check('mirror verified before after renderer and before final pin',len(main_calls)>=3)
check('original renderer manifest still preserved raw',any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='fresh' and len(node.args)==2 and dump(node.args[1])==dump(ast.Name(id='raw_manifest',ctx=ast.Load())) for node in ast.walk(nfd['main'])))
check('explicit collector hash and frozen runtime checks added',all(token in ast.get_source_segment(NEW.read_text(encoding='utf-8'),nfd['main']) for token in ["collected['runtimeProvenance'] == runtime","sha(COLLECTOR) == COLLECTOR_SHA"]))
mirror_source=ast.get_source_segment(NEW.read_text(encoding='utf-8'),nfd['mirror_inventory'])
check('mirror inventory rejects unexpected directories files and missing approved file',all(token in mirror_source for token in ['name in expected_dirs','name == final_markdown_location','set(files) == {final_markdown_location}']))
prepare_source=ast.get_source_segment(NEW.read_text(encoding='utf-8'),nfd['prepare_citation_mirror'])
check('mirror scope does not authorize extra source or asset reads',"'additionalSourceOrAssetReadsAuthorized': False" in prepare_source and "'businessTextRewritten': False" in prepare_source)
assert sha(OLD)==OSHA and sha(NEW)==NSHA
report={'schema':'spec-agent-renderer-citation-mirror-narrow-independent-review/1',
    'reviewer':'/root/delivery_root_review/supplement_collector_review',
    'baseline':{'path':str(OLD),'sha256':OSHA},'candidate':{'path':str(NEW),'sha256':NSHA},
    'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},
    'status':'APPROVED_NARROW_CODE_DELTA_ONLY' if all(item['passed'] for item in tests) else 'HOLD_CODE_DELTA',
    'findings':[],'testCount':len(tests),'passedCount':sum(item['passed'] for item in tests),'tests':tests,
    'bindingRequirement':'Actual renderer and untouched original manifest source identify the mirror. Original approved collection source remains separately pinned. Binding must validate both and exclusive byte-identical mirror mapping; never assume old originalSource equals rendererManifest.source.',
    'limitations':{'actualWrapperImportedOrRun':False,'frozenRuntimeImportedOrRun':False,'providerRun':False,
        'actualSourceOrAuthorOrRendererRecordsRead':False,'realInputRead':False,'mirrorPhysicallyCreatedByThisReview':False,
        'actualRendererOrBrowserOrNativeRun':False,'actualConversionOrPublicationRun':False,
        'actualAll128RuntimeHashRecheckPerformed':False,'atomicOrRaceFreeProof':False}}
out=AUDIT/'renderer-r06-narrow-delta-independent-review-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'testCount':len(tests),'passedCount':report['passedCount'],'report':str(out),'sha256':sha(out),'failures':[item for item in tests if not item['passed']]}))
if not all(item['passed'] for item in tests):raise SystemExit(1)
