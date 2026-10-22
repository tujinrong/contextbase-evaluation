"""Narrow parser AST probe only; no whole projection/PIL/core/browser import."""
from pathlib import Path
import ast,base64,hashlib,json,re
from html.parser import HTMLParser
p=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery/pdf_projection_r05.py')
expected='2dc8d9eb7426d1187001ea2458c6f93bee761243ea21ac03aa4178e3940ba1e2'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
tree=ast.parse(p.read_bytes())
nodes=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in {'sha','require','OuterHtml','inspect_html'}]
ns={'base64':base64,'hashlib':hashlib,'re':re,'HTMLParser':HTMLParser}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'parser-AST-only','exec'),ns)
cases=['<!doctype html><html lang="ja">&amp;<head></head><body>ok</body></html>',
    '<!doctype html><html lang="ja"><head></head><body>ok</body></html>&amp;',
    '<!doctype html><html lang="ja">&#65;<head></head><body>ok</body></html>',
    '<!doctype html><html lang="ja"><head></head><body>ok</body></html>&#65;']
results=[]
for text in cases:
    try:ns['inspect_html'](text)
    except ValueError as exc:results.append({'syntheticHtml':text,'outcome':'HOLD','error':str(exc)})
    else:results.append({'syntheticHtml':text,'outcome':'ACCEPTED_BOUNDARY_ENTITY'})
out=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/independent-audit/pdf-r05-boundary-entity-probe-r01.json')
report={'schema':'spec-agent-pdf-parser-boundary-entity-probe/1','candidate':{'path':str(p),'sha256':expected},
    'status':'HOLD_ENTITY_CALLBACKS_SKIP_STRUCTURAL_TEXT_GUARD' if any(r['outcome']=='ACCEPTED_BOUNDARY_ENTITY' for r in results) else 'BOUNDARY_ENTITIES_REJECTED',
    'cases':results,'scope':'Own synthetic structural parser fixtures only; actual HTML and native/browser/PDF not executed.',
    'actualProviderCoreOrPILOrBrowserImported':False,'actualPdfOrMarkerExecuted':False}
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'results':results,'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
