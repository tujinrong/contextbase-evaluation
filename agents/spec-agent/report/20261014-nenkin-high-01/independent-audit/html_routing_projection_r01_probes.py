"""Synthetic-only projection tests; no actual project/source/HTML/job/output reads."""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
FILE=ROOT/'.tmp/20261014-nenkin-high-01/delivery/html_routing_projection_r01.py'
AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
EXPECTED='542a396124d25f2d279a32430405f336055a4327a46207ef95ce856eff3c5829'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(FILE)==EXPECTED
spec=importlib.util.spec_from_file_location('owned_html_projection_synthetic_only',FILE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def entry(identity,path,kind='common'):
    p=Path(path.replace('/','\\')) if False else m.PurePosixPath(path)
    stem=p.with_suffix('')
    return {'documentId':identity,'kind':kind,'canonicalMarkdownPath':path,
        'locations':{'md':'md/'+path,'html':'html/'+stem.as_posix()+'/'+stem.name+'.html',
        'pdf':'PDF/'+stem.as_posix()+'.pdf','xlsx':'Excel/'+stem.as_posix()+'.xlsx'}}
allowlist={'schema':'spec-agent-html-publication-routing/1','runId':m.RUN_ID,'projectId':m.PROJECT_ID,
    'capsuleManifestSha256':m.CAPSULE_SHA,'executionContextSha256':m.CONTEXT_SHA,'planSha256':'a'*64,
    'sourceOnly':True,'originalApplicationExecuted':False,'formalPercentage':None,'published':False,
    'documents':[entry('INDEX','index.md','index'),entry('A','folder/a.md'),entry('B','folder/b.md'),
        entry('UNICODE','資料/項目.md'),entry('HASH','folder/a#b.md'),entry('SPACE','folder/a b.md')]}
results=[]
def check(name,fn,hold=False):
    try:fn()
    except m.RoutingHold as exc:results.append({'name':name,'passed':hold,'outcome':'HOLD','reason':str(exc)})
    except Exception as exc:results.append({'name':name,'passed':False,'outcome':'UNEXPECTED_ERROR','reason':type(exc).__name__+': '+str(exc)})
    else:results.append({'name':name,'passed':not hold,'outcome':'SUCCESS'})
def project(source,expected,document='INDEX',data=None):
    original=source if isinstance(source,bytes) else source.encode('utf-8')
    final,proof=m.project_html(original,copy.deepcopy(data or allowlist),document)
    target=expected if isinstance(expected,bytes) else expected.encode('utf-8')
    assert final==target,(final,target)
    assert m.inverse_bytes(final,proof['replacements'])==original and proof['inverseByteProofPassed'] is True
    assert proof['originalSha256']==hashlib.sha256(original).hexdigest() and proof['finalSha256']==hashlib.sha256(final).hexdigest()
    assert proof['nonHrefBytesChanged'] is False and proof['domSerialized'] is False
    for record in proof['replacements']:
        assert original[record['originalByteStart']:record['originalByteEnd']]==record['before'].encode('utf-8')
        assert final[record['finalByteStart']:record['finalByteEnd']]==record['after'].encode('utf-8')
        assert record['route']['queryRaw'] in record['before'] and record['route']['fragmentRaw']==''
    return final,proof
check('root-index Markdown target retains .md identity',lambda:project('<a href="folder/a.md">label</a>','<a href="../../md/folder/a.md">label</a>'))
check('nested origin sibling target',lambda:project('<a href="b.md">label</a>','<a href="../../../md/folder/b.md">label</a>','A'))
check('nested origin parent target',lambda:project('<a href="../index.md">label</a>','<a href="../../../md/index.md">label</a>','A'))
check('HTML target retains .html identity',lambda:project('<a href="../html/folder/a/a.html">label</a>','<a href="../folder/a/a.html">label</a>'))
check('PDF target retains .pdf and uppercase folder',lambda:project('<a href="../PDF/folder/a.pdf">label</a>','<a href="../../PDF/folder/a.pdf">label</a>'))
check('Excel target retains .xlsx and uppercase folder',lambda:project('<a href="../Excel/folder/a.xlsx">label</a>','<a href="../../Excel/folder/a.xlsx">label</a>'))
check('Unicode href and label bytes preserved',lambda:project('<a href="資料/項目.md" title="属性">本文</a>','<a href="../../md/資料/項目.md" title="属性">本文</a>'))
check('percent-encoded target lexical spelling preserved',lambda:project('<a href="%66older/%61.md">label</a>','<a href="../../md/%66older/%61.md">label</a>'))
check('percent-encoded Unicode target spelling preserved',lambda:project('<a href="%E8%B3%87%E6%96%99/%E9%A0%85%E7%9B%AE.md">label</a>','<a href="../../md/%E8%B3%87%E6%96%99/%E9%A0%85%E7%9B%AE.md">label</a>'))
check('encoded literal hash is filename identity',lambda:project('<a href="folder/a%23b.md">label</a>','<a href="../../md/folder/a%23b.md">label</a>'))
check('encoded filename space retained',lambda:project('<a href="folder/a%20b.md">label</a>','<a href="../../md/folder/a%20b.md">label</a>'))
check('raw query ampersand entity spelling preserved',lambda:project('<a href="folder/a.md?x=1&amp;y=2">label</a>','<a href="../../md/folder/a.md?x=1&amp;y=2">label</a>'))
check('entity query delimiter spelling preserved',lambda:project('<a href="folder/a.md&#63;x=1&amp;y=2">label</a>','<a href="../../md/folder/a.md&#63;x=1&amp;y=2">label</a>'))
check('HTML entity path separator resolves exact identity',lambda:project('<a href="folder&#47;a.md?x=1">label</a>','<a href="../../md/folder/a.md?x=1">label</a>'))
check('query-only link retains self HTML identity',lambda:project('<a href="?x=1&amp;y=2">label</a>','<a href="?x=1&amp;y=2">label</a>'))
check('empty href retains self HTML identity',lambda:project('<a href="">label</a>','<a href="">label</a>'))
check('explicit current html target yields basename',lambda:project('<a href="../html/index/index.html">label</a>','<a href="index.html">label</a>'))
check('single-quoted attribute quote spacing preserved',lambda:project("<A data-x='a' HREF = 'folder/a.md' class='z'>label</A>","<A data-x='a' HREF = '../../md/folder/a.md' class='z'>label</A>"))
check('unquoted href value only changed',lambda:project('<a href=folder/a.md class=z>label</a>','<a href=../../md/folder/a.md class=z>label</a>'))
check('selfclosing anchor raw bytes retained',lambda:project('<a href="folder/a.md" />','<a href="../../md/folder/a.md" />'))
check('boolean non-href attributes retained',lambda:project('<a disabled href="folder/a.md" hidden>label</a>','<a disabled href="../../md/folder/a.md" hidden>label</a>'))
check('multiple variable length replacements inverse proof',lambda:project('<a href="folder/a.md">a</a><a href="../html/folder/b/b.html">b</a><a href="folder/b.md?q=2">c</a>', '<a href="../../md/folder/a.md">a</a><a href="../folder/b/b.html">b</a><a href="../../md/folder/b.md?q=2">c</a>'))
check('UTF8 BOM and CRLF byte offsets preserved',lambda:project(b'\xef\xbb\xbf<p>\xe6\x96\x87</p>\r\n<a\r\n href="folder/a.md">A</a>\r\n',b'\xef\xbb\xbf<p>\xe6\x96\x87</p>\r\n<a\r\n href="../../md/folder/a.md">A</a>\r\n'))
check('CR-only text offsets preserved',lambda:project('<p>文</p>\r<a href="folder/a.md">A</a>\r','<p>文</p>\r<a href="../../md/folder/a.md">A</a>\r'))
for scheme in ('http','https','HTTP','data'):
    source='<a href="'+scheme+':example?x=1&amp;y=2#anchor">label</a>'
    check(scheme+' external reference unchanged including fragment',lambda source=source:project(source,source))
source='<img src="folder/a.md"><div href="unknown.md" style="background:url(unknown.md)">label</div><!-- <a href="unknown.md">comment</a> --><a href="folder/a.md" data-html="&lt;a href=&quot;unknown.md&quot;&gt;">label</a>'
expected=source.replace('href="folder/a.md" data-html','href="../../md/folder/a.md" data-html')
check('labels images CSS other attrs comment bytes remain exact',lambda:project(source,expected))
for tag in ('script','style','textarea','title','xmp','iframe','noembed','noframes','plaintext'):
    source='<'+tag+'><a href="unknown.md">literal</a></'+tag+'>'
    check(tag+' literal anchor text not rewritten',lambda source=source:project(source,source))
for tag in ('script','style','textarea','title'):
    source='<'+tag+'><a href="unknown.md">literal</a></'+tag+'><a href="folder/a.md">real</a>'
    expected=source.replace('<a href="folder/a.md">','<a href="../../md/folder/a.md">')
    check(tag+' closing tag resumes real anchors only',lambda source=source,expected=expected:project(source,expected))
source='<plaintext><a href="unknown.md">literal</a></plaintext><a href="unknown.md">also literal</a>'
check('plaintext remains raw until EOF',lambda:project(source,source))
check('anchor without href ignored',lambda:project('<a name="x">label</a>','<a name="x">label</a>'))
for href in ('unknown.md','../unknown.md','../PDF/folder/unknown.pdf','/md/folder/a.md','//host/folder/a.md',
             '../../outside.md','folder//a.md','folder/','folder/%2Fa.md','folder/%5Ca.md','%2e%2e/index.md',
             'folder/%ZZ.md','folder/%FF.md','folder/CON.md','folder/a.md.','folder/a.md '):
    check('local target HOLD '+href,lambda href=href:m.project_html(('<a href="'+href+'">label</a>').encode(),allowlist,'INDEX'),True)
for href in ('folder/a.md#one','folder/a.md?x=1&amp;y=2#one','#one','#','folder/a.md&#35;one'):
    def fragment_hold(href=href):
        try:m.project_html(('<a href="'+href+'">label</a>').encode(),allowlist,'INDEX')
        except m.RoutingHold as exc:
            assert exc.details['hrefRaw']==href and exc.details['fragmentRaw']
            if '&amp;' in href:assert exc.details['queryRaw']=='?x=1&amp;y=2'
            raise
    check('all local fragments HOLD with raw spelling '+href,fragment_hold,True)
for href in ('javascript:alert(1)','vbscript:x','file:///x','mailto:x','custom:x'):
    check('unsupported scheme HOLD '+href,lambda href=href:m.project_html(('<a href="'+href+'">label</a>').encode(),allowlist,'INDEX'),True)
check('duplicate href refused',lambda:m.project_html(b'<a href="folder/a.md" HREF="folder/b.md">x</a>',allowlist,'INDEX'),True)
check('value-less href refused',lambda:m.project_html(b'<a href>x</a>',allowlist,'INDEX'),True)
check('selfclosing raw-text ambiguity HOLD',lambda:m.project_html(b'<textarea/><a href="folder/a.md">x</a>',allowlist,'INDEX'),True)
check('invalid UTF8 HTML HOLD',lambda:m.project_html(b'\xff<a href="folder/a.md">x</a>',allowlist,'INDEX'),True)
check('unknown origin ID HOLD',lambda:m.project_html(b'<p>x</p>',allowlist,'UNKNOWN'),True)
mutations={
    'extra schema field':lambda d:d.update(extra=True),
    'wrong run':lambda d:d.update(runId='other'),
    'wrong project':lambda d:d.update(projectId='other'),
    'wrong capsule':lambda d:d.update(capsuleManifestSha256='0'*64),
    'wrong full context':lambda d:d.update(executionContextSha256='0'*64),
    'nonlowercase plan SHA':lambda d:d.update(planSha256='A'*64),
    'business source mode':lambda d:d.update(sourceOnly=False),
    'runtime execution claim':lambda d:d.update(originalApplicationExecuted=True),
    'formal percentage claim':lambda d:d.update(formalPercentage=95),
    'published claim':lambda d:d.update(published=True),
    'missing one format':lambda d:d['documents'][0]['locations'].pop('pdf'),
    'extra format':lambda d:d['documents'][0]['locations'].update(csv='csv/index.csv'),
    'wrong HTML canonical layout':lambda d:d['documents'][0]['locations'].update(html='html/index.html'),
    'wrong PDF root case':lambda d:d['documents'][0]['locations'].update(pdf='pdf/index.pdf'),
    'wrong Excel root case':lambda d:d['documents'][0]['locations'].update(xlsx='excel/index.xlsx'),
    'duplicate ID':lambda d:d['documents'].append(copy.deepcopy(d['documents'][0])),
    'casecolliding paths':lambda d:d['documents'].append(entry('CASE','INDEX.md')),
    'analysis report in final bundle':lambda d:d['documents'].append(entry('REPORT','analysis/report.md','analysis-report')),
    'unknown document field':lambda d:d['documents'][0].update(extra=True),
    'unsafe canonical Windows path':lambda d:d['documents'].append(entry('CON','folder/CON.md')),
    'absolute canonical path':lambda d:d['documents'][0].update(canonicalMarkdownPath='/index.md'),
    'canonical traversal':lambda d:d['documents'][0].update(canonicalMarkdownPath='../index.md'),
    'canonical repeated slash':lambda d:d['documents'][0].update(canonicalMarkdownPath='folder//a.md'),
}
for name,mutator in mutations.items():
    def mutation_case(mutator=mutator):
        changed=copy.deepcopy(allowlist);mutator(changed);m.project_html(b'<p>x</p>',changed,'INDEX')
    check('allowlist HOLD '+name,mutation_case,True)
check('duplicate JSON member refused',lambda:m.parse_json(b'{"x":1,"x":2}'),True)
check('nested duplicate JSON member refused',lambda:m.parse_json(b'{"x":{"a":1,"a":2}}'),True)
for constant in ('NaN','Infinity','-Infinity'):
    check('nonfinite JSON '+constant+' refused',lambda constant=constant:m.parse_json(('{"x":'+constant+'}').encode()),True)
def inverse_tamper():
    final,proof=m.project_html(b'<a href="folder/a.md">x</a>',allowlist,'INDEX')
    m.inverse_bytes(final.replace(b'../../md/',b'../../xx/'),proof['replacements'])
check('inverse proof rejects altered replacement bytes',inverse_tamper,True)
def inverse_offset_tamper():
    final,proof=m.project_html(b'<a href="folder/a.md">x</a>',allowlist,'INDEX')
    proof['replacements'][0]['finalByteStart']+=1
    m.inverse_bytes(final,proof['replacements'])
check('inverse proof rejects altered offset metadata',inverse_offset_tamper,True)
tree=ast.parse(FILE.read_bytes())
imports=[]
for node in ast.walk(tree):
    if isinstance(node,ast.Import):imports.extend(alias.name for alias in node.names)
    if isinstance(node,ast.ImportFrom):imports.append(node.module)
check('candidate imports only standard library',lambda:None if all(name.split('.')[0] in sys.stdlib_module_names for name in imports) else (_ for _ in ()).throw(AssertionError()))
check('candidate contains no browser/provider/core API names',lambda:None if not any(name.startswith(('contextbase','playwright','artifact')) for name in imports) else (_ for _ in ()).throw(AssertionError()))
assert sha(FILE)==EXPECTED
report={'schema':'spec-agent-html-routing-projection-synthetic-review/1','candidate':{'path':str(FILE),'sha256':EXPECTED},
    'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},
    'status':'PASS_SYNTHETIC_PROJECTION_ONLY' if all(item['passed'] for item in results) else 'HOLD_SYNTHETIC_PROJECTION_FAILURE',
    'testCount':len(results),'passedCount':sum(item['passed'] for item in results),'tests':results,
    'syntheticContract':{'fourFolders':['md','html','PDF','Excel'],'originalTargetExtensionRetained':True,
        'allLocalFragmentsHold':True,'queryRawSpellingPreserved':True,'rawHrefSpanOnly':True,'inverseByteProof':True},
    'limitations':{'candidateOnlyStdlibImport':True,'realInputRead':False,'actualAuthorOrRendererRecordsRead':False,
        'actualHtmlRead':False,'actualCliProjectionRun':False,'actualStageOrPublishRun':False,'actualCollectionRun':False,
        'actualWindowsReparseOrFreshOutputIoTested':False,'providerOrBrowserOrMarkersExecuted':False,
        'frozenPipelineImported':False,'originalOutputReadOrModified':False,'nativeQualification':False,
        'fullApprovedPlanCoverageVerified':False,'atomicOrRaceFreeProof':False}}
out=AUDIT/'html-routing-projection-r01-synthetic-review-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'testCount':len(results),'passedCount':report['passedCount'],
    'failures':[item for item in results if not item['passed']],'report':str(out),'sha256':sha(out)}))
if not all(item['passed'] for item in results):raise SystemExit(1)
