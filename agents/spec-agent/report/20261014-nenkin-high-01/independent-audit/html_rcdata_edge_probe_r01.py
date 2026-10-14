"""Synthetic raw-container edge probe, candidate-only import."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
p=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery/html_routing_projection_r01.py')
s=importlib.util.spec_from_file_location('owned_projection_edge_only',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
fixtures=['<textarea><!--</textarea><a href="unknown.md">real anchor</a>-->',
    '<textarea><!-- comment </textarea><a href="unknown.md">real anchor</a> --></textarea>',
    '<textarea><!--a</textarea><a href="unknown.md">real anchor</a>--></textarea>',
    '<title><!-- comment </title><a href="unknown.md">real anchor</a> -->',
    '<xmp><!-- comment </xmp><a href="unknown.md">real anchor</a> -->']
class Probe(m.AnchorSpans):
    def __init__(self,text):super().__init__(text);self.events=[]
    def handle_starttag(self,tag,attrs):self.events.append(('start',tag,self.inert_tag));super().handle_starttag(tag,attrs)
    def handle_endtag(self,tag):self.events.append(('end',tag,self.inert_tag));super().handle_endtag(tag)
    def handle_comment(self,data):self.events.append(('comment',data,self.inert_tag))
allow={'schema':'spec-agent-html-publication-routing/1','runId':m.RUN_ID,'projectId':m.PROJECT_ID,
    'capsuleManifestSha256':m.CAPSULE_SHA,'executionContextSha256':m.CONTEXT_SHA,'planSha256':'a'*64,
    'sourceOnly':True,'originalApplicationExecuted':False,'formalPercentage':None,'published':False,
    'documents':[{'documentId':'INDEX','kind':'index','canonicalMarkdownPath':'index.md',
        'locations':{'md':'md/index.md','html':'html/index/index.html','pdf':'PDF/index.pdf','xlsx':'Excel/index.xlsx'}}]}
results=[]
for text in fixtures:
    q=Probe(text);q.feed(text);q.close()
    try:m.project_html(text.encode(),allow,'INDEX')
    except m.RoutingHold as exc:
        results.append({'syntheticFixture':text,'events':q.events,'spans':q.spans,
            'actualCandidateOutcome':'HOLD_UNKNOWN_LOCAL_TARGET','passed':len(q.spans)==1,
            'reason':str(exc)})
    else:results.append({'syntheticFixture':text,'actualCandidateOutcome':'UNEXPECTED_SUCCESS','passed':False})
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
report={'schema':'spec-agent-html-routing-rcdata-concern-resolution/1','candidate':{'path':str(p),'sha256':sha(p)},
    'status':'CONCERN_NOT_REPRODUCED_CURRENT_BUNDLED_RUNTIME' if all(item['passed'] for item in results) else 'HOLD_REPRODUCED_EDGE',
    'runtime':'Bundled Python 3.12.14','testCount':len(results),'passedCount':sum(item['passed'] for item in results),
    'tests':results,'initialConcern':'Older HTMLParser behavior was inferred before testing; current runtime correctly recognizes raw/RCDATA closing tags and subsequent real anchors.',
    'revisionCreated':False,'sealedCandidateChanged':False,
    'limitations':{'syntheticOnly':True,'actualBrowserOrNativeTested':False,'actualHtmlOrProjectInputRead':False,
        'providerOrFrozenPipelineImportedOrRun':False,'actualProjectionCliRun':False}}
out=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/independent-audit/html-routing-r01-rcdata-concern-resolution-r01.json')
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'testCount':len(results),'passedCount':report['passedCount'],'report':str(out),'sha256':sha(out)}))
if not all(item['passed'] for item in results):raise SystemExit(1)
