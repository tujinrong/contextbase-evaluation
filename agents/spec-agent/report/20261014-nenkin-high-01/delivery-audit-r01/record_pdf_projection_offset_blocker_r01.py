"""Record independent functions-only blocker and already permitted dependency metadata."""
import ast,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
probe=A/'probe_pdf_metadata_and_projection_r01.py'
tree=ast.parse(probe.read_text(encoding='utf-8'))
nodes=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='spec' for t in node.targets):break
    nodes.append(node)
ns={'__name__':'permitted_metadata_only'}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(probe),'exec'),ns)
after={p:ns['hash_file'](p) for p in ns['pins']}
assert after==ns['pins']
metadata=ns['metadata']
metadata.update(beforeAfterPinsUnchanged=True,pinnedFileCount=len(after))
metadata_receipt=ns['save']('pdf-runtime-deps-metadata-r01.json',metadata)
failures=[]
for filename,expected in (
    ('pdf_projection_r02.py','660e8f5731d14c5415d43b4ebf3a750e81bcbc6df5082778403d7af56375fbe1'),
    ('pdf_projection_r03.py','1f97920494cade5b41f6047607c495662b3dc965368529b4040ef69ba60b66d5'),
):
    p=D/filename;assert ns['hash_file'](p)==expected
    spec=importlib.util.spec_from_file_location('synthetic_projection_offset_'+filename.replace('.','_'),p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    raw=b'<!doctype html><html lang="ja"><head></head><body>synthetic</body></html>'
    try:m.project_html(raw,[])
    except TypeError as exc:
        assert str(exc)=="'int' object is not callable"
        failures.append({'path':str(p),'sha256':expected,'fixtureSha256':hashlib.sha256(raw).hexdigest(),
                         'fixtureIsSyntheticOnly':True,'exceptionType':type(exc).__name__,'exception':str(exc),
                         'stack':traceback.format_exc(),'actualPdfCreated':False,'driverImported':False})
    else:raise AssertionError('Missing expected offset collision')
    assert ns['hash_file'](p)==expected
record={'schema':'spec-agent-pdf-offset-independent-blocker/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'CODE_AND_SYNTHETIC_FUNCTIONS_ONLY','status':'HOLD','findingId':'HTMLPARSER_OFFSET_ATTRIBUTE_COLLISION',
        'finding':'OuterHtml.offset() collides with integer HTMLParser.offset; valid outer head close invokes the integer.',
        'sourceLines':[38,39,61,62],'fixtures':failures,'originalFirstProbeFailed':True,
        'originalProbePath':str(probe),'originalProbeSha256':ns['hash_file'](probe),'dependencyReceipt':metadata_receipt,
        'allPinnedBytesUnchanged':True,'beforeHashes':ns['pins'],'afterHashes':after,
        'browserStarted':False,'playwrightImported':False,'pdfCreated':False,'markerExecuted':False,
        'providerExecuted':False,'businessInputRead':False,'semanticApproval':False,'formalQualityAssessed':False,
        'wholeApproval':False,'adoption':False,'published':False}
receipt=ns['save']('pdf-projection-offset-independent-blocker-r01.json',record)
print(json.dumps({'dependencyReceipt':metadata_receipt,'blockerReceipt':receipt,'playwrightNoncacheFileCount':ns['runtime'][0]['fileCount']},ensure_ascii=False))
