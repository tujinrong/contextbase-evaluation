"""Independent code-only comparison against immutable frozen r17."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[2]/'src'
RECEIPT=HERE.parent/'training-assisted/runtime-code-assisted-09.json'
RECEIPT_SHA='15ea871e41804dc257bb6aa8e7a5d712ff9147461fb4187c28f4a522426a8309'
CSS_PATH=HERE.parent/'source-pilot/table-css-prototype-r03/candidate.css'
CSS_SHA='e3373dc2efc2ee2a60693a34e7a24010c6092a737a7703722f9d053056be3d54'
FILES={'contextbase/ai/rendering.py':'b413e971287a477577527cab7ab10dccfa652d125c3854ba7ec825b62b154807',
       'contextbase/tests/test_ai_rendering.py':'56b2417487f99412d55f0aa047a282007fbadc8327507dd9e1d01fd5338fca18'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def dump(node):return ast.dump(node,include_attributes=False)

class RemoveStyleAddition(ast.NodeTransformer):
    def visit_BinOp(self,node):
        node=self.generic_visit(node)
        if isinstance(node.op,ast.Add) and isinstance(node.right,ast.Name) and node.right.id=='MARKDOWN_TABLE_READABILITY_STYLE':
            return node.left
        return node

def main():
    assert sha(RECEIPT)==RECEIPT_SHA and sha(CSS_PATH)==CSS_SHA
    receipt=json.loads(RECEIPT.read_text(encoding='utf8'));frozen=Path(receipt['destination'])
    assert inventory(frozen)==receipt['files'] and receipt['fileCount']==126
    current=inventory(MAIN);changes={p:{'old':receipt['files'][p],'new':current[p]} for p in current if current[p]!=receipt['files'][p]}
    assert set(changes)==set(FILES) and all(current[p]==value for p,value in FILES.items())
    old=ast.parse((frozen/'contextbase/ai/rendering.py').read_text(encoding='utf8'))
    new=ast.parse((MAIN/'contextbase/ai/rendering.py').read_text(encoding='utf8'))
    assignments=[node for node in new.body if isinstance(node,ast.Assign) and
                 any(isinstance(target,ast.Name) and target.id=='MARKDOWN_TABLE_READABILITY_STYLE' for target in node.targets)]
    assert len(assignments)==1 and ast.literal_eval(assignments[0].value)==CSS_PATH.read_text(encoding='utf8')
    new.body.remove(assignments[0]);restored=RemoveStyleAddition().visit(new)
    assert dump(old)==dump(restored), 'renderer change outside one CSS constant and its _html style append'
    old_functions={node.name:dump(node) for node in old.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert '_markdown_table_open' in old_functions and '_sanitize' in old_functions
    old_tests=ast.parse((frozen/'contextbase/tests/test_ai_rendering.py').read_text(encoding='utf8'))
    new_tests=ast.parse((MAIN/'contextbase/tests/test_ai_rendering.py').read_text(encoding='utf8'))
    prepared=ast.parse('class RealRenderingTests:\n'+(HERE/'table_css_core_test_methods.py.txt').read_text(encoding='utf8'))
    methods={node.name:dump(node) for node in prepared.body[0].body}
    target=next(node for node in new_tests.body if isinstance(node,ast.ClassDef) and node.name=='RealRenderingTests')
    actual={node.name:dump(node) for node in target.body if isinstance(node,ast.FunctionDef) and node.name in methods}
    assert actual==methods and len(methods)==5
    target.body=[node for node in target.body if not(isinstance(node,ast.FunctionDef) and node.name in methods)]
    assert dump(old_tests)==dump(new_tests), 'old test definitions changed'
    css=CSS_PATH.read_text(encoding='utf8')
    selector='table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"])'
    import tinycss2
    rules=tinycss2.parse_stylesheet(css,skip_comments=True,skip_whitespace=True)
    for rule in rules:
        assert rule.type=='qualified-rule'
        selectors=tinycss2.serialize(rule.prelude).split(',')
        assert all(text.strip().startswith(selector) for text in selectors)
        assert all(declaration.type=='declaration' for declaration in tinycss2.parse_declaration_list(rule.content,skip_comments=True,skip_whitespace=True))
    assert inventory(MAIN)==current and inventory(frozen)==receipt['files']
    out=HERE/'core-r18-independent-integration-qa.json';assert not out.exists()
    result={'schema':'core-r18-independent-code-integration-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS_CODE_DELTA_ONLY','runtimeReceipt':str(RECEIPT),'runtimeReceiptSha256':RECEIPT_SHA,
        'frozenR17Full126FilesUnchanged':True,'main126FilesBeforeAfterUnchangedDuringAudit':True,
        'modifiedFiles':changes,'cssPath':str(CSS_PATH),'cssSha256':CSS_SHA,
        'rendererRestoresExactR17AstAfterRemovingStyleAppend':True,
        'parserDomAndCellOrderCodeUnchanged':True,'sanitizerUnchanged':True,'edgeRendererUnchanged':True,
        'cssOnlyParserMarked3PlusTables':True,'unmarkedEmbeddedAndOneTwoColumnTablesExcluded':True,
        'oldTestsAstUnchanged':True,'addedTestDefinitionsExactPreparedAst':True,
        'addedTests':sorted(name for name in methods if name.startswith('test_')),
        'scope':{'mainEdited':False,'providerCalls':0,'businessMaterialsRead':False,
                 'applicationExecuted':False,'wholeQualityApproved':False,'published':False},
        'limits':['Actual DOM, geometry and pixel results are separate browser gates.',
                  'This audit does not declare the still-running full suite passed.']}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'status':result['status']},ensure_ascii=False))

if __name__=='__main__':main()
