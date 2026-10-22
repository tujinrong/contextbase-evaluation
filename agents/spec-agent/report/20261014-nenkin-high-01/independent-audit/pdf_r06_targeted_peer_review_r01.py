"""Targeted parser/projection AST checks with approved actual HTML only.
Native tiling is an explicit own memory stub; no whole module/PIL/core/browser.
"""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
import ast,base64,copy,hashlib,json,math,re
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01';AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
OLD=WORK/'delivery/pdf_projection_r04.py';PREVIOUS=WORK/'delivery/pdf_projection_r05.py';NEW=WORK/'delivery/pdf_projection_r06.py'
HTML=WORK/'renders/menu-pilot-01/SCR-017/menu.html'
MANIFEST=HTML.parent/'manifest.json';PINS=HTML.parent/'render-pins.json'
PREFLIGHT=ROOT/'report/20261014-nenkin-high-01/menu-pilot-pdf-html-preflight-r01.json'
EXPECTED={str(OLD):'7bcd51255ceddc0e07e03ff4e26102a9b8689246aab8408f119c89cdf6f13394',
    str(PREVIOUS):'2dc8d9eb7426d1187001ea2458c6f93bee761243ea21ac03aa4178e3940ba1e2',
    str(NEW):'4cad3b55f4e0c2d0b2f58349f727bd613e47f2a0a532b809da2d50812e2d785b',
    str(HTML):'96dbe96e0ffb579bf45c93a08e9c203efcb73b0365531648f975604d4eab8c2b',
    str(PREFLIGHT):'291f543764a5111223999dd57d08a27b9cbe1e2a6faaa51e6adcb772c2eb2abf'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert all(sha(path)==value for path,value in EXPECTED.items())
manifest=json.loads(MANIFEST.read_bytes());renderpin=json.loads(PINS.read_bytes())
assert renderpin['canonicalHtmlSha256']==EXPECTED[str(HTML)] and renderpin['canonicalHtmlFilename']=='menu.html'
assert renderpin['renderManifestSha256']==sha(MANIFEST) and renderpin['documentId']=='SCR-017'
EXPECTED[str(MANIFEST)]=sha(MANIFEST);EXPECTED[str(PINS)]=sha(PINS)
old,previous,new=ast.parse(OLD.read_bytes()),ast.parse(PREVIOUS.read_bytes()),ast.parse(NEW.read_bytes())
def dump(node):return ast.dump(node,include_attributes=False)
def functions(tree):return {node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
of,pf,nf=functions(old),functions(previous),functions(new)
def methods(tree):
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='OuterHtml')
    return {node.name:node for node in cls.body if isinstance(node,ast.FunctionDef)}
om,pm,nm=methods(old),methods(previous),methods(new)
tests=[]
def test(name,fn,hold=False):
    try:fn()
    except (ValueError,AssertionError,KeyError,TypeError,UnicodeError) as exc:tests.append({'name':name,'passed':hold,'outcome':'HOLD','type':type(exc).__name__})
    else:tests.append({'name':name,'passed':not hold,'outcome':'SUCCESS'})
def assert_true(condition):assert condition
test('old4 native tiling and text helpers unchanged exact AST',lambda:assert_true(all(dump(node)==dump(nf[name]) for name,node in of.items() if name not in {'inspect_html','project_html'})))
test('all old4 active attribute network and inline PNG guard statements unchanged',lambda:assert_true([dump(node) for node in om['handle_starttag'].body[:8]]==[dump(node) for node in nm['handle_starttag'].body[:8]]))
test('r5 to r6 all pure projection functions unchanged',lambda:assert_true(all(dump(node)==dump(nf[name]) for name,node in pf.items())))
test('r5 to r6 other parser methods unchanged except newline constructor',lambda:assert_true(all(dump(node)==dump(nm[name]) for name,node in pm.items() if name!='__init__')))
assign=lambda tree:{node.targets[0].id:dump(node) for node in tree.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
test('all old4 constants including printCSS and geometry JS unchanged',lambda:assert_true(assign(old)==assign(new)))
constants={}
for node in new.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and isinstance(node.value,ast.Constant):constants[node.targets[0].id]=node.value.value
nodes=[node for node in new.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in {'sha','require','OuterHtml','inspect_html','project_html'}]
ns=dict(constants,base64=base64,hashlib=hashlib,re=re,HTMLParser=HTMLParser,Counter=Counter,
    CONTENT_WIDTH_PX=math.floor((420-24)/25.4*96),CONTENT_HEIGHT_PX=math.floor((297-24)/25.4*96))
ANNEX='<section data-peer-native-stub="1">synthetic annex</section>'
ns['native_tiles']=lambda pictures,inline_hashes=():(ANNEX,[])
exec(compile(ast.Module(body=nodes,type_ignores=[]),'pdf-projection-peer-AST-only','exec'),ns)
def single(content='',head=''):
    return '<!doctype html><html lang="ja"><head>'+head+'</head><body>'+content+'</body></html>'
def child(content='',head=''):
    return '<!DOCTYPE html><html lang="ja"><head>'+head+'</head><body>'+content+'</body></html>'
def projected(text,pictures=None):
    raw=text.encode('utf-8');q=ns['inspect_html'](text)
    result,proof,tiles=ns['project_html'](raw,pictures or [])
    style='<style data-spec-agent-pdf="1">'+ns['PRINT_CSS']+'</style>'
    if q.nested_documents:
        expected=text[:q.body_close]+style+ANNEX+text[q.body_close:]
        assert proof['cssInsertionLocation']=='outer-body-tail-before-native-annex'
    else:
        expected=text[:q.body_close]+ANNEX+text[q.body_close:]
        expected=expected[:q.head_close]+style+expected[q.head_close:]
        assert proof['cssInsertionLocation']=='outer-head-tail'
    assert result==expected and proof['inverseRestoresCanonicalHtmlBytes'] is True
    assert proof['canonicalHtmlSha256']==hashlib.sha256(raw).hexdigest()
    assert proof['onlyInsertions'] is True and proof['canonicalTextOrCellsReauthored'] is False
    return result,proof,q
test('single-root original head insertion retained',lambda:projected(single('source','<style>p{color:red}</style>')))
test('balanced child body CSS override insertion after all sourceCSS',lambda:projected(single(child('画面','<style>@page{size:A4}</style>'),'\n<style>p{color:red}</style>')))
test('two sibling child documents accepted one outertail insertion',lambda:projected(single(child('first')+child('second'))))
actual_bytes=HTML.read_bytes();actual_text=actual_bytes.decode('utf-8')
pictures=[{'id':entry['id'],'kind':kind[:-1],'sha256':entry['png']['sha256'],'width':entry['png']['width'],'height':entry['png']['height']}
    for kind in ('layouts','diagrams') for entry in manifest[kind]]
artifacts={entry['path']:entry['sha256'] for entry in manifest['artifacts']}
assert len(pictures)==8 and all(artifacts[p['id']+'.png']==p['sha256'] for p in pictures)
def actual_case():
    result,proof,q=projected(actual_text,pictures)
    assert len(q.nested_documents)==1 and len(q.imageHashes)==7
    assert q.head_close==actual_text.index('</head>') and q.body_close==actual_text.rindex('</body>')
    assert proof['cssInsertionOffset']>actual_text.rindex('</style>')
    assert result.encode('utf-8').count(b'<tr>')==actual_bytes.count(b'<tr>')
test('actual pinned menu rawHTML balanced source docs CSS order allrows and byteinverse',actual_case)
for label,separator in [('CR','\r'),('UnicodeLS','\u2028'),('formfeed','\f')]:
    def offset_case(separator=separator):
        text=single('source','<style>x'+separator+'Y\nZ</style>')
        result,proof,q=projected(text)
        assert q.head_close==text.index('</head>') and q.body_close==text.rindex('</body>')
    test(label+' beforeLF exact HTMLParser offset and inverse',offset_case)
for code in ('&amp;','&#65;','&#x41;'):
    test('entity beforehead HOLD '+code,lambda code=code:ns['inspect_html']('<!doctype html><html lang="ja">'+code+'<head></head><body>ok</body></html>'),True)
    test('entity afterouterhtml HOLD '+code,lambda code=code:ns['inspect_html'](single('ok')+code),True)
    test('entity pendingchilddoctype HOLD '+code,lambda code=code:ns['inspect_html'](single('<!DOCTYPE html>'+code+'<html><head></head><body>ok</body></html>')),True)
test('literal entity and charref spellings inside body retained',lambda:projected(single('&amp;&#65;&#x41;')))
malformed={
    'missing outer head':'<!doctype html><html lang="ja"><body>x</body></html>',
    'duplicate outer head':'<!doctype html><html lang="ja"><head></head><head></head><body>x</body></html>',
    'duplicate outer body':'<!doctype html><html lang="ja"><head></head><body>x</body><body>y</body></html>',
    'child inside outerhead':single('ok','<html><head></head><body>x</body></html>'),
    'nested child child':single(child(child('deep'))),
    'missing child head':single('<html><body>x</body></html>'),
    'late child head':single('<html><head></head><body>x</body><head></head></html>'),
    'orphan child head':single('<head></head>'),
    'orphan child body':single('<body>x</body>'),
    'wrong child close':single('<html><head></head><body>x</html></body>'),
    'ambiguous outer close':'<!doctype html><html lang="ja"><head></head><body>x</body bad></html>',
    'pending child doctype without html':single('<!DOCTYPE html><p>x</p>'),
    'doctype in head':single('x','<!DOCTYPE html>'),
    'selfclosing structural tag':single('<html/>'),
    'second outerroot':single('x')+'<html><head></head><body>x</body></html>',
    'text afterroot':single('x')+'not whitespace',
    'text between wrappers':'<!doctype html><html lang="ja">not whitespace<head></head><body>x</body></html>'}
for name,text in malformed.items():test('malformed HOLD '+name,lambda text=text:ns['inspect_html'](text),True)
for tag in ('script','iframe','frame','frameset','object','embed','base','link'):
    test('existing activeelement HOLD '+tag,lambda tag=tag:ns['inspect_html'](single('<'+tag+'>x</'+tag+'>')),True)
for key in ('src','srcset','poster','action','formaction','data','background','xlink:href'):
    test('existing networkattribute HOLD '+key,lambda key=key:ns['inspect_html'](single('<div '+key+'="https://example.invalid/x"></div>')),True)
test('existing eventattribute HOLD',lambda:ns['inspect_html'](single('<p onclick="x">x</p>')),True)
test('existing refresh HOLD',lambda:ns['inspect_html'](single('<meta http-equiv="refresh" content="0">')),True)
test('existing duplicateattribute HOLD',lambda:ns['inspect_html'](single('<p id="a" ID="b">x</p>')),True)
test('existing processinginstruction HOLD',lambda:ns['inspect_html'](single('<?x>')),True)
test('existing nonHTMLdoctype HOLD',lambda:ns['inspect_html'](single('<!DOCTYPE svg>')),True)
payload=b'own synthetic inline byte payload';inline_sha=hashlib.sha256(payload).hexdigest()
inline='<img src="data:image/png;base64,'+base64.b64encode(payload).decode()+'">'
test('existing unboundinline image HOLD',lambda:ns['project_html'](single(inline).encode(),[]),True)
test('existing missingdiagram multiplicity HOLD',lambda:ns['project_html'](single('').encode(),[{'id':'D','kind':'diagram','sha256':inline_sha}]),True)
test('existing duplicateimage identity HOLD',lambda:ns['project_html'](single(inline).encode(),[{'id':'D','sha256':inline_sha}]*2),True)
assert all(sha(path)==value for path,value in EXPECTED.items())
report={'schema':'spec-agent-pdf-projection-r06-targeted-peer-audit/1','reviewer':'/root/delivery_root_review/supplement_collector_review',
    'status':'APPROVED_TARGETED_PARSER_AND_INSERTION_CODE_ONLY' if all(t['passed'] for t in tests) else 'HOLD_TARGETED_PEER_FAILURE',
    'pinnedFilesBeforeAfter':EXPECTED,'inputsBeforeAfterUnchanged':True,'testCount':len(tests),'passedCount':sum(t['passed'] for t in tests),'tests':tests,
    'actualHtmlMetadata':{'rawHtmlSha256':EXPECTED[str(HTML)],'balancedNestedSourceDocuments':1,'canonicalInlinePngCount':7,
        'actualManifestNativePictureMetadataCount':8,'layoutSourceLines':[40,89]},
    'scope':'AST-extracted actual parser/inspect/project code. Actual approved canonicalHTML is read and insertion projected only in memory. Original inlinePNG bytes remain in unchanged canonicalHTML. Native tile generation is an explicit own in-memory stub and is not rerun.',
    'limitations':{'wholeProjectionOrFrozenCoreImported':False,'PILOrNativePixelTilingExecuted':False,'actualPngFilesRead':False,
        'savedPrintHtmlOrPdfCreated':False,'browserOrPdfOrMarkersRun':False,'sourceBusinessOriginalSpecEvalOrOldOutputRead':False,
        'nativeGeometryPrintLegibilityOrPdfTextCoverageVerified':False,'semanticSpecificationApproval':False,
        'formalPercentage':None,'publicationApproved':False},'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))}}
out=AUDIT/'pdf-projection-r06-targeted-peer-audit-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'tests':len(tests),'passed':report['passedCount'],'failures':[t for t in tests if not t['passed']],
    'report':str(out),'sha256':sha(out)}))
if not all(t['passed'] for t in tests):raise SystemExit(1)
