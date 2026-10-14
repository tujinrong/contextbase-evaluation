"""Preserve sealed r01, capture synthetic RCDATA failure, make narrow r02."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01'
AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
old=WORK/'delivery/html_routing_projection_r01.py'
new=WORK/'delivery/html_routing_projection_r02.py'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
old_sha='542a396124d25f2d279a32430405f336055a4327a46207ef95ce856eff3c5829'
assert sha(old)==old_sha and not new.exists()
spec=importlib.util.spec_from_file_location('owned_projection_r01_rcdata_probe_only',old)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
allow={'schema':'spec-agent-html-publication-routing/1','runId':m.RUN_ID,'projectId':m.PROJECT_ID,
    'capsuleManifestSha256':m.CAPSULE_SHA,'executionContextSha256':m.CONTEXT_SHA,'planSha256':'a'*64,
    'sourceOnly':True,'originalApplicationExecuted':False,'formalPercentage':None,'published':False,
    'documents':[{'documentId':'INDEX','kind':'index','canonicalMarkdownPath':'index.md',
        'locations':{'md':'md/index.md','html':'html/index/index.html','pdf':'PDF/index.pdf','xlsx':'Excel/index.xlsx'}}]}
fixture=b'<textarea><!--</textarea><a href="unknown.md">real anchor</a>-->'
final,proof=m.project_html(fixture,allow,'INDEX')
assert final==fixture and proof['anchorHrefCount']==0
old_data=old.read_bytes()
needle=b'class AnchorSpans(HTMLParser):\n    def __init__'
replacement=(b'class AnchorSpans(HTMLParser):\n'
    b'    # Extend the standard parser raw-text mode to RCDATA/legacy raw-text\n'
    b'    # containers so literal comments cannot hide real closing tags/anchors.\n'
    b'    CDATA_CONTENT_ELEMENTS = (\'script\', \'style\', \'textarea\', \'title\', \'xmp\',\n'
    b'                              \'iframe\', \'noembed\', \'noframes\', \'plaintext\')\n'
    b'    def __init__')
assert old_data.count(needle)==1
new_data=old_data.replace(needle,replacement)
with new.open('xb') as stream:stream.write(new_data)
assert sha(old)==old_sha and new.read_bytes()==new_data
report={'schema':'spec-agent-html-routing-rcdata-revision-preparation/1',
    'previous':{'path':str(old),'sha256':old_sha,'status':'HOLD_SYNTHETIC_RCDATA_EDGE'},
    'failureFixture':{'syntheticHtml':fixture.decode(),'expected':'HOLD_UNKNOWN_REAL_LINK_AFTER_TEXTAREA_CLOSE',
        'observed':'SUCCESS_WITH_ZERO_ANCHOR_CALLBACKS','actualNativeBrowserTested':False},
    'candidate':{'path':str(new),'sha256':sha(new)},
    'delta':'AnchorSpans.CDATA_CONTENT_ELEMENTS extension only; all old functions/statements unchanged otherwise.',
    'sealedPreviousBytesUnchanged':True,'actualHtmlOrBusinessInputRead':False,
    'frozenPipelineOrProviderOrBrowserImportedOrRun':False,'actualProjectionCliOrPublishRun':False,
    'newCandidateCompatibilityApproval':'PENDING_SYNTHETIC_AND_INDEPENDENT_REVIEW'}
out=AUDIT/'html-routing-projection-r02-preparation-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'candidateSha256':sha(new),'preparation':str(out),'preparationSha256':sha(out)}))
