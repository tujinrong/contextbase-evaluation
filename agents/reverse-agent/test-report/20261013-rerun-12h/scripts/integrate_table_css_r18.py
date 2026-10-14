"""Apply the reviewed generic CSS and independent synthetic browser regressions."""
from pathlib import Path
import ast, hashlib, json

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
receipt=load(report/'training-assisted/runtime-code-assisted-09.json')
renderer=agent/'src/contextbase/ai/rendering.py'
tests=agent/'src/contextbase/tests/test_ai_rendering.py'
for path in (renderer,tests):
    if sha(path)!=receipt['files'][path.relative_to(agent/'src').as_posix()]:
        raise ValueError('r17 code has changed before r18 integration')
css_path=report/'source-pilot/table-css-prototype-r03/candidate.css'
if sha(css_path)!='e3373dc2efc2ee2a60693a34e7a24010c6092a737a7703722f9d053056be3d54':
    raise ValueError('Reviewed CSS candidate changed')
methods_path=report/'delivery/table_css_core_test_methods.py.txt'
methods=methods_path.read_text(encoding='utf-8-sig')
methods_ast=ast.parse('class Synthetic:\n'+methods)
names=[n.name for n in methods_ast.body[0].body if isinstance(n,ast.FunctionDef)]
if len(names)!=5 or len([n for n in names if n.startswith('test_')])!=4:
    raise ValueError('The exact four browser regressions and measurement helper are required')
old_renderer=renderer.read_text(encoding='utf-8')
old_tests=tests.read_text(encoding='utf-8')
css=css_path.read_text(encoding='utf-8').strip()
if 'MARKDOWN_TABLE_READABILITY_STYLE' in old_renderer or 'def _measure_markdown_table_css' in old_tests:
    raise ValueError('Fresh CSS integration required')
anchor='MERMAID_LABEL_STYLE = '
if old_renderer.count(anchor)!=1: raise ValueError('Renderer anchor ambiguous')
new_renderer=old_renderer.replace(anchor,'MARKDOWN_TABLE_READABILITY_STYLE = '+repr(css)+'\n'+anchor)
html_anchor='html.escape(csp, quote=True) + '\
    "'\"><style>' + BASE_STYLE + \"</style>\""
if new_renderer.count(html_anchor)!=1: raise ValueError('Trusted HTML style anchor ambiguous')
new_renderer=new_renderer.replace(html_anchor,'html.escape(csp, quote=True) + '\
    "'\"><style>' + BASE_STYLE + MARKDOWN_TABLE_READABILITY_STYLE + \"</style>\"")
test_anchor='\n\nif __name__ == "__main__":'
if old_tests.count(test_anchor)!=1: raise ValueError('Test class anchor ambiguous')
new_tests=old_tests.replace(test_anchor,'\n'+methods+test_anchor)
ast.parse(new_renderer)
ast.parse(new_tests)
target=report/'engine/r18-integration-receipt.json'
if target.exists(): raise FileExistsError(str(target))
history=report/'engine/code-history/r18-before'
if history.exists(): raise FileExistsError(str(history))
history.mkdir(parents=True)
(history/'rendering.py').write_bytes(renderer.read_bytes())
(history/'test_ai_rendering.py').write_bytes(tests.read_bytes())
renderer.write_text(new_renderer,encoding='utf-8')
tests.write_text(new_tests,encoding='utf-8')
result={'schema':'generic-table-css-integration/1','previousRuntimeReceiptSha256':sha(report/'training-assisted/runtime-code-assisted-09.json'),
    'cssPath':str(css_path),'cssSha256':sha(css_path),'independentTestMethodsSha256':sha(methods_path),
    'modified':{str(renderer):sha(renderer),str(tests):sha(tests)},
    'canonicalMarkdownChanged':False,'embeddedHtmlMarkupChanged':False,'sourceApplicationExecuted':False,
    'testsPassed':None,'specificationQualityApproved':False}
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
