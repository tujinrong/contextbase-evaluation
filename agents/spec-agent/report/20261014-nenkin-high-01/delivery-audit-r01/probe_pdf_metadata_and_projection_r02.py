"""Independent PDF code/dependency metadata and synthetic-only projection audit.

No business document, PDF writer, browser, Playwright import, or marker is used.
"""
import ast
import base64
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(r'D:\開発\contextbase-evaluation')
DEL = ROOT/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery'
AUDIT = ROOT/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'
DEPS = ROOT/'agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps'
BUNDLE = Path(r'C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies')
EXPECTED = {
    DEL/'pdf_projection_r04.py': '7bcd51255ceddc0e07e03ff4e26102a9b8689246aab8408f119c89cdf6f13394',
    DEL/'export_pdf_bound_r05.py': '03a6fb7f445b52211c07d50cbd1a07bff413e5a1f91b1b5bfd38fb7d924d84e3',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def checked_path(path):
    path = Path(path)
    for p in (path, *path.parents):
        if p.exists():
            s = p.lstat()
            assert not p.is_symlink() and not(getattr(s, 'st_file_attributes', 0)&0x400), str(p)
    assert path.resolve() == path.absolute(), str(path)
    return path

def hash_file(path):
    return sha(checked_path(path).read_bytes())

def save(name, data):
    target = checked_path(AUDIT/name)
    assert target.parent == AUDIT and not target.exists()
    with target.open('x', encoding='utf-8') as h:
        json.dump(data, h, ensure_ascii=False, indent=2)
        h.write('\n')
    return {'path': str(target), 'sha256': hash_file(target)}

def package_inventory(package, distribution):
    folder = checked_path(DEPS/package)
    metadata = checked_path(DEPS/distribution/'METADATA')
    text = metadata.read_text(encoding='utf-8')
    fields = {}
    for field in ('Name', 'Version', 'Requires-Python'):
        matches = re.findall(r'^'+re.escape(field)+r': (.+)$', text, re.M)
        fields[field] = matches[0] if len(matches)==1 else None
    fields['Requires-Dist'] = re.findall(r'^Requires-Dist: (.+)$', text, re.M)
    files = {}
    for path in sorted(folder.rglob('*')):
        checked_path(path)
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc', '.pyo'}:
            files[str(path)] = hash_file(path)
    assert files and fields['Name'] and fields['Version']
    return {'packageRoot': str(folder), 'distributionMetadata': str(metadata),
            'distributionMetadataSha256': hash_file(metadata), 'distribution': fields,
            'nonCacheFiles': files, 'fileCount': len(files), 'moduleImported': False}

pins = {str(path): hash_file(path) for path in EXPECTED}
assert all(pins[str(path)]==value for path,value in EXPECTED.items())
ast.parse((DEL/'export_pdf_bound_r05.py').read_text(encoding='utf-8'))
runtime = [
    package_inventory('playwright', 'playwright-1.57.0.dist-info'),
    package_inventory('greenlet', 'greenlet-3.5.6.dist-info'),
    package_inventory('pyee', 'pyee-13.0.1.dist-info'),
]
for package in runtime:
    pins.update(package['nonCacheFiles'])
    pins[package['distributionMetadata']] = package['distributionMetadataSha256']
tools = {}
for label, path in (
    ('bundledPython', BUNDLE/'python/python.exe'),
    ('pdftoppm', BUNDLE/'native/poppler/Library/bin/pdftoppm.exe'),
    ('pdfinfo', BUNDLE/'native/poppler/Library/bin/pdfinfo.exe'),
    ('bundledNodePlaywrightMetadata', BUNDLE/'node/node_modules/playwright/package.json'),
    ('bundledNodePlaywrightCoreMetadata', BUNDLE/'node/node_modules/playwright-core/package.json'),
):
    path = checked_path(path)
    tools[label] = {'path': str(path), 'sha256': hash_file(path), 'size': path.stat().st_size}
    pins[str(path)] = tools[label]['sha256']
for label in ('bundledNodePlaywrightMetadata', 'bundledNodePlaywrightCoreMetadata'):
    data = json.loads(Path(tools[label]['path']).read_text(encoding='utf-8'))
    tools[label].update(version=data['version'], exports=data.get('exports'), moduleImported=False)
parser_receipt = checked_path(AUDIT/'analysis-dependencies-r01.json')
pins[str(parser_receipt)] = hash_file(parser_receipt)
metadata = {
    'schema': 'spec-agent-pdf-runtime-metadata/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'DEPENDENCY_CODE_METADATA_AND_BYTE_HASH_ONLY', 'approvedAnalysisDependencyRoot': str(DEPS),
    'existingParserReceipt': str(parser_receipt), 'existingParserReceiptSha256': pins[str(parser_receipt)],
    'existingParserReceiptDoesNotClaimPlaywright': True, 'pythonPackages': runtime, 'tools': tools,
    'popplerVersionObservedByVersionOnly': '26.07.0',
    'pythonPlaywrightVersion': '1.57.0', 'nodePlaywrightVersion': '1.62.1',
    'playwrightImportExecuted': False, 'playwrightDriverExecuted': False, 'browserStarted': False,
    'pdfCreated': False, 'markerExecuted': False, 'providerExecuted': False, 'businessInputRead': False,
    'dependencyDirectoryModified': False,
    'limits': ['Non-cache inventory does not assert all cache bytes unchanged.',
               'Package version metadata and hashes do not prove browser compatibility or actual process ownership.',
               'A future invocation must explicitly bootstrap and pin approved dependency paths; default isolated bundled Python did not resolve Playwright.',
               'Node Playwright is a separate distribution; its version is not substituted for Python Playwright.'],
}

spec = importlib.util.spec_from_file_location('independent_pdf_projection_r04', DEL/'pdf_projection_r04.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tests = []
findings = []

def case(name, function):
    function()
    tests.append({'name': name, 'pass': True})

def rejects(function):
    try:
        function()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return str(exc)
    raise AssertionError('Expected rejection')

def html(body='', head=''):
    return ('<!doctype html><html lang="ja"><head>'+head+'</head><body>'+body+'</body></html>').encode('utf-8')

def png(width, height, colored=False):
    from PIL import Image
    image = Image.new('RGBA', (width,height), (255,255,255,255))
    if colored:
        pixels=image.load()
        for y in range(height):
            for x in range(width):
                if x<width//2 and y<height//2:
                    pixels[x,y]=(255,255,255,255)
                elif x>=width//2 and y<height//2:
                    pixels[x,y]=(13,37,59,0)
                else:
                    pixels[x,y]=(x%256,y%256,(x+y)%256,(x*3+y)%256)
    stream=io.BytesIO();image.save(stream,format='PNG');raw=stream.getvalue()
    return image, {'id': 'SYNTHETIC-PNG', 'sha256': sha(raw), 'width': width, 'height': height, 'bytes': raw}

small_image, small = png(20,10)
src='data:image/png;base64,'+base64.b64encode(small['bytes']).decode('ascii')
valid = html('<h1>合成検査 001</h1><p>SRC-001 / 令和06年01月01日 &amp; A→B</p><img src="'+src+'">', '<!-- </head> -->')

def projection_exact():
    projected, receipt, tiles=m.project_html(valid,[small])
    assert receipt['inverseRestoresCanonicalHtmlBytes'] and receipt['onlyInsertions']
    assert not tiles and projected.encode().replace(('<style data-spec-agent-pdf="1">'+m.PRINT_CSS+'</style>').encode(),b'',1)==valid
    assert projected.index('<style data-spec-agent-pdf')>projected.index('<!-- </head> -->')
    assert sha(small['bytes']) in m.inspect_html(projected).imageHashes
case('nonASCII-source-and-head-comment-insert-only-raw-byte-inverse',projection_exact)

for name, raw in [
    ('iframe', html('<iframe></iframe>')),
    ('script', html('<script>void 0</script>')),
    ('object', html('<object></object>')),
    ('event', html('<p onclick="void 0">x</p>')),
    ('meta-refresh-spaces', html('', '<meta http-equiv=" Refresh " content="0">')),
    ('external-image-http', html('<img src="https://invalid.example/image.png">')),
    ('nonPNG-inline-svg', html('<img src="data:image/svg+xml;base64,eA==">')),
    ('external-stylesheet-link', html('', '<link rel="stylesheet" href="https://invalid.example/style.css">')),
    ('image-missing-src', html('<img>')),
    ('bad-base64', html('<img src="data:image/png;base64,@@@">')),
    ('duplicate-attributes-casefold', html('<p id="x" ID="y">x</p>')),
    ('active-srcset', html('<img src="'+src+'" srcset="https://invalid.example/image.png">')),
    ('form-action', html('<form action="https://invalid.example/"></form>')),
    ('processing-instruction', html('<?proc x?>')),
    ('DTD-not-HTML', html().replace(b'<!doctype html>', b'<!DOCTYPE html SYSTEM "https://invalid.example/dtd">')),
    ('duplicate-head', html('<head></head>')),
    ('duplicate-body', html('<body></body>')),
    ('structural-closing-mismatch', html().replace(b'</body></html>',b'</html></body>')),
    ('unbound-inline-PNG', valid),
]:
    case('reject-'+name,lambda raw=raw: rejects(lambda:m.project_html(raw,[])))

case('reject-native-SHA-drift',lambda:rejects(lambda:m.project_html(html(),[{**small,'sha256':'0'*64}])))
case('reject-native-dimensions-drift',lambda:rejects(lambda:m.project_html(html(),[{**small,'width':21}])))
case('reject-duplicate-native-ID',lambda:rejects(lambda:m.project_html(valid,[small,small])))
case('reject-bound-nonPNG-bytes',lambda:rejects(lambda:m.project_html(html(),[{**small,'bytes':b'not png','sha256':sha(b'not png')}])))
case('reject-invalid-source-length',lambda:rejects(lambda:m.origins(True,900,60)))
case('reject-invalid-overlap',lambda:rejects(lambda:m.origins(10,900,900)))

def pixel_budget():
    class Fake:
        format='PNG';width=40_000_001;height=1
    with patch.object(m.Image,'open',return_value=Fake()):
        rejects(lambda:m.native_tiles([small]))
case('reject-pixel-budget-before-load',pixel_budget)

large_image,large=png(1601,1201,True)
large['id']='LARGE-ALL-PIXELS'

def native_exact():
    from PIL import Image
    projected,receipt,tiles=m.project_html(html(),[large])
    assert len(tiles)==6 and len(receipt['nativeTiles'])==6
    for tile in tiles:
        decoded=Image.open(io.BytesIO(tile['bytes']));decoded.load();decoded=decoded.convert('RGBA')
        expected=large_image.crop(tile['cropBox'])
        assert decoded.tobytes()==expected.tobytes()
        assert sha(tile['bytes'])==tile['tileSha256'] and sha(decoded.tobytes())==tile['rgbaSha256']
        assert tile['sourceSha256']==large['sha256']
    for y in range(large['height']):
        spans=sorted((t['cropBox'][0],t['cropBox'][2]) for t in tiles if t['cropBox'][1]<=y<t['cropBox'][3])
        reached=0
        for a,b in spans:
            assert a<=reached
            reached=max(reached,b)
        assert reached==large['width']
    assert 'LARGE-ALL-PIXELS 1/6' in projected and all(t['bytes'] for t in tiles)
    assert large_image.getpixel((100,100))==(255,255,255,255)
    assert large_image.getpixel((1500,100))==(13,37,59,0)
case('large-PNG-every-saved-tile-exactRGBA-all-row-pixel-coverage-white-transparent',native_exact)

def small_missing():
    from PIL import Image
    projected,receipt,tiles=m.project_html(html('<p>synthetic</p>'),[{**small,'kind':'layout'}])
    assert len(tiles)==1 and len(receipt['nativeTiles'])==1 and 'data:image/png' in projected
    assert tiles[0]['cropBox']==[0,0,20,10] and tiles[0]['sourceTileCount']==1
    decoded=Image.open(io.BytesIO(tiles[0]['bytes']));decoded.load()
    assert decoded.convert('RGBA').tobytes()==small_image.tobytes()
    assert receipt['allNativeAssetsEitherInlineOrAnnexed']
    assert receipt['nativeAssetIdsRetained']==['SYNTHETIC-PNG']
case('small-noninline-layout-bound-image-annex-1of1-all-pixels',small_missing)

def diagram_missing():
    rejects(lambda:m.project_html(html(),[{**small,'kind':'diagram'}]))
case('reject-missing-canonical-inline-diagram',diagram_missing)

def diagram_duplicate():
    pictures=[{**small,'id':'DIAGRAM-1','kind':'diagram'},{**small,'id':'DIAGRAM-2','kind':'diagram'}]
    rejects(lambda:m.project_html(html('<img src="'+src+'">'),pictures))
    projected,receipt,tiles=m.project_html(html('<img src="'+src+'"><img src="'+src+'">'),pictures)
    assert not tiles and receipt['canonicalInlineNativeImageCount']==2
    assert receipt['nativeAssetIdsRetained']==['DIAGRAM-1','DIAGRAM-2']
case('duplicate-SHA-diagrams-minimum-two-inline-occurrences',diagram_duplicate)

def both_comment_boundaries():
    raw=html('<p>合成 001</p><!-- </body> -->','<!-- </head> -->')
    projected,receipt,tiles=m.project_html(raw,[])
    assert receipt['inverseRestoresCanonicalHtmlBytes'] and not tiles
    assert projected.encode().replace(('<style data-spec-agent-pdf="1">'+m.PRINT_CSS+'</style>').encode(),b'',1)==raw
case('head-and-body-comment-close-literals-do-not-anchor-insertions',both_comment_boundaries)

def offset_delta_exact():
    old=(DEL/'pdf_projection_r03.py').read_bytes()
    current=(DEL/'pdf_projection_r04.py').read_bytes()
    assert sha(old)=='1f97920494cade5b41f6047607c495662b3dc965368529b4040ef69ba60b66d5'
    assert old.replace(b'def offset(',b'def source_offset(').replace(b'self.offset()',b'self.source_offset()')==current
    old_driver=(DEL/'export_pdf_bound_r04.py').read_bytes()
    current_driver=(DEL/'export_pdf_bound_r05.py').read_bytes()
    assert sha(old_driver)=='91d10a2ffaf523febaa2e3acb5be125a2d0682339aa173dfebbf1d20a0fa7642'
    assert old_driver.replace(b'from pdf_projection_r03 import',b'from pdf_projection_r04 import')==current_driver
    for p in (DEL/'pdf_projection_r03.py',DEL/'export_pdf_bound_r04.py'):
        pins[str(p)]=hash_file(p)
case('fresh-offset-rename-three-points-and-driver-import-only-byte-exact-deltas',offset_delta_exact)

def css_network_accepted():
    projected,_,_=m.project_html(html('<p>synthetic</p>','<style>@import url("https://invalid.example/x.css");p{background-image:url("https://invalid.example/x.png")}</style>'),[])
    assert 'https://invalid.example/x.css' in projected
    findings.append({'id':'INLINE-CSS-RESOURCE-URL-ACCEPTED','severity':'LIMITATION_REQUIRES_RUNTIME_BLOCKED_REQUEST_HOLD',
                     'observedBy':'functions-only synthetic counterexample','sourceLines':[44,47,67],
                     'actual':'Pure HTML inspection accepts CSS @import/url; driver route abort and blocked-request rejection are required.',
                     'runtimeRouteExecuted':False})
case('observe-inline-CSS-network-URL-pure-gate-limitation',css_network_accepted)

model={'title':'合成検査','sourceMetadata':{'sections':[{'heading':'概要'}]},'visibleCoverage':['SRC-001','令和06年01月01日','01','値→結果','duplicate','duplicate']}
good='合成検査 概要 SRC-001 令和06年01月01日 01 値→結果 duplicate duplicate'
def good_coverage():
    result=m.text_coverage(good,model)
    assert not result['missing'] and not result['multiplicityFailures'] and result['visualQualified'] is False
case('full-literals-leadingzero-era-punctuation-duplicate-good',good_coverage)

def fail_coverage(text,missing=None,multiple=False):
    result=m.text_coverage(text,model)
    if missing:assert missing in result['missing']
    if multiple:assert result['multiplicityFailures']
case('missing-full-ID-not-prefix',lambda:fail_coverage(good.replace('SRC-001','SRC-00'),missing='SRC-001'))
def isolated_leadingzero():
    isolated={'title':'HEADER','sourceMetadata':{'sections':[]},'visibleCoverage':['01']}
    assert '01' in m.text_coverage('HEADER 1',isolated)['missing']
case('missing-isolated-leading-zero',isolated_leadingzero)
case('missing-source-punctuation',lambda:fail_coverage(good.replace('値→結果','値-結果'),missing='値→結果'))
case('missing-era-token',lambda:fail_coverage(good.replace('令和06','平成06'),missing='令和06年01月01日'))
case('missing-minimum-duplicate-occurrence',lambda:fail_coverage(good.replace('duplicate duplicate','duplicate'),multiple=True))

def whitespace_only():
    result=m.text_coverage(good.replace('SRC-001','SRC-\n001').replace('令和06','令 和 06'),model)
    assert not result['missing'] and not result['multiplicityFailures']
case('whitespace-only-layout-equivalence',whitespace_only)

def ordered_good():
    r=m.canonical_text_order(' A\n001 B 002 A001 ',['A001','B002','A001'])
    assert not r['orderFailures'] and r['visualQualified'] is False
case('canonical-order-repeated-literal-good',ordered_good)
def ordered_bad():
    assert m.canonical_text_order('B002 A001',['A001','B002'])['orderFailures']
    assert m.canonical_text_order('A001 B002',['A001','B002','A001'])['orderFailures']
case('canonical-order-reorder-or-missing-repeat-detected',ordered_bad)

driver=(DEL/'export_pdf_bound_r05.py').read_text(encoding='utf-8')
tree=ast.parse(driver)
names={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
worker=ast.get_source_segment(driver,names['worker'])
supervisor=ast.get_source_segment(driver,names['supervise'])
job=ast.get_source_segment(driver,names['OwnedWindowsJob'])
main=ast.get_source_segment(driver,names['main'])
source_checks={
    'ready-before-GO-read':worker.index('worker_ready()')<worker.index("readline(4)")<worker.index('load_bound('),
    'GO-after-creationTime-job-assignment':supervisor.index("ready.get('creationTime')")<supervisor.index('job=OwnedWindowsJob(')<supervisor.index("process.stdin.write(b'GO\\n')"),
    'job-public-time-before-assignment':job.index('creation_time(self.k,process)')<job.index('AssignProcessToJobObject(self.handle,process)'),
    'job-kill-on-close-flag': 'LimitFlags=0x2000' in job,
    'marker-and-bounded-timeouts-required':'args.pdf_marker_completed' in main and '30<=args.stage_timeout<=300' in main and 'args.total_timeout<=3600' in main,
    'source-md-exact-readbytes-and-copy':"source_md=safe_path(entry['markdown']).read_bytes()" in worker and "fresh_write(destination/'Markdown'/relative,source_md)" in worker,
    'input-JS-false-SW-block-download-false':"java_script_enabled=False,service_workers='block'" in worker and 'accept_downloads=False' in worker,
    'abort-all-route-and-HOLD-any-blocked':"context.route('**/*'" in worker and "route.abort()" in worker and "require(not blocked" in worker,
    'PDF-all-pages-strict-extraction':"strict=True" in worker and "for p in reader.pages" in worker,
    'canonical-DOM-full-sequence-and-multiplicity-required':"canonical_text_order(extracted,canonical_strings)" in worker and "not coverage['multiplicityFailures']" in worker and "not coverage['canonicalTextOrder']['orderFailures']" in worker,
    'Poppler-all-pages-count-bound':"'-f','1','-l',str(len(reader.pages))" in worker and "len(images)==len(reader.pages)" in worker,
    'after-input-and-tool-repin':'load_bound(args.binding,args.binding_sha256);tool(args.chromium,args.chromium_sha256);tool(args.poppler,args.poppler_sha256)' in worker,
    'actualvisual-never-code-PASS':"'allActualPagesViewed':False" in worker and "'visualReview':'PENDING'" in worker,
    'no-add-style-tag':'.add_style_tag(' not in driver,
    'geometry-whole-ASCII-range-measure':r'/[A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*/g' in m.GEOMETRY_JS and 'range.setStart(node,i)' in m.GEOMETRY_JS and "token-internal-wrap" in m.GEOMETRY_JS,
}
assert all(source_checks.values()),source_checks

after={p:hash_file(p) for p in pins}
assert after==pins
metadata['beforeAfterPinsUnchanged']=True
metadata['pinnedFileCount']=len(pins)
metadata_receipt=save('pdf-runtime-deps-metadata-r02.json',metadata)
result={
    'schema':'spec-agent-pdf-independent-functions-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'CODE_AND_SYNTHETIC_FUNCTIONS_ONLY','projection':{'path':str(DEL/'pdf_projection_r04.py'),'sha256':pins[str(DEL/'pdf_projection_r04.py')]},
    'driver':{'path':str(DEL/'export_pdf_bound_r05.py'),'sha256':pins[str(DEL/'export_pdf_bound_r05.py')]},
    'dependencyReceipt':metadata_receipt,'tests':tests,'passedSyntheticCases':len(tests),
    'staticSourceChecks':source_checks,'staticSourceCheckCount':len(source_checks),'findings':findings,
    'status':'CODE_AND_SYNTHETIC_PASS_ACTUAL_PDF_REVIEW_PENDING','beforeHashes':pins,'afterHashes':after,
    'allPinnedBytesUnchanged':True,'pureProjectionImported':True,'driverImported':False,
    'functionsOnlyPILSyntheticPNGsCreatedInMemory':True,
    'actualPdfCreated':False,'actualBrowserStarted':False,'actualPlaywrightImported':False,
    'actualWindowsJobAPICalled':False,'actualProcessOwnershipVerified':False,
    'markerExecuted':False,'providerExecuted':False,'businessInputRead':False,
    'formalQualityAssessed':False,'semanticApproval':False,'stateApproval':False,'wholeApproval':False,
    'adoption':False,'published':False,
    'limits':['Canonical/source population completeness and source quality were not assessed.',
              'Multiplicity substring counts are conservative and do not prove cell occurrence alignment.',
              'Whole ASCII token geometry source is present; no DOM geometry was actually executed, and non-ASCII geometry is not measured by this regex.',
              'No actual owned Windows Job, timeout kill, browser, PDF writer, Poppler render, or PDF text extraction was exercised.',
              'Every actual PDF page needs fresh original-size visual review.',
              'Inline CSS resource URLs rely on runtime route abort plus blocked-request HOLD.',
              'Default driver dependency imports still require a trusted, pinned bootstrap recipe.'],
}
receipt=save('pdf-projection-r04-driver-r05-independent-probes-r01.json',result)
print(json.dumps({'metadataReceipt':metadata_receipt,'auditReceipt':receipt,'syntheticCases':len(tests),'staticSourceChecks':len(source_checks),'findings':[f['id'] for f in findings]},ensure_ascii=False))
