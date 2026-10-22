"""Three exact offset probes in the AST-only structural parser."""
from pathlib import Path
import ast,base64,hashlib,json,re
from html.parser import HTMLParser
p=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery/pdf_projection_r05.py')
expected='2dc8d9eb7426d1187001ea2458c6f93bee761243ea21ac03aa4178e3940ba1e2'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
nodes=[node for node in ast.parse(p.read_bytes()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in {'sha','require','OuterHtml','inspect_html'}]
ns={'base64':base64,'hashlib':hashlib,'re':re,'HTMLParser':HTMLParser}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'parser-offset-AST-only','exec'),ns)
results=[]
Base=ns['OuterHtml']
class Probe(Base):
    def __init__(self,text):super().__init__(text);self.closing_offsets=[]
    def handle_endtag(self,tag):
        if tag in {'head','body','html'}:
            self.closing_offsets.append({'tag':tag,'observed':self.source_offset(),'expected':self.text.index('</'+tag+'>')})
        super().handle_endtag(tag)
for label,separator in [('CR before LF','\r'),('Unicode LS before LF','\u2028'),('formfeed before LF','\f')]:
    text='<!doctype html><html lang="ja"><head><style>x'+separator+'Y\nZ</style></head><body>content</body></html>'
    q=Probe(text)
    try:q.feed(text);q.close()
    except ValueError as exc:outcome='HOLD_VALID_BALANCED_STRUCTURE';error=str(exc)
    else:outcome='ACCEPTED';error=None
    results.append({'name':label,'closingOffsets':q.closing_offsets,'outcome':outcome,'error':error,
        'offsetsExact':all(item['observed']==item['expected'] for item in q.closing_offsets)})
report={'schema':'spec-agent-pdf-parser-source-offset-probe/1','candidate':{'path':str(p),'sha256':expected},
    'status':'HOLD_SOURCE_OFFSETS_DO_NOT_MATCH_HTMLPARSER_LF_LINES' if any(not r['offsetsExact'] for r in results) else 'SOURCE_OFFSETS_EXACT',
    'cases':results,'scope':'Three own synthetic structural parser fixtures. No actual HTML, projection generation, PDF, browser, marker or whole module import.'}
out=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/independent-audit/pdf-r05-source-offset-probe-r01.json')
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'results':results,'report':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
