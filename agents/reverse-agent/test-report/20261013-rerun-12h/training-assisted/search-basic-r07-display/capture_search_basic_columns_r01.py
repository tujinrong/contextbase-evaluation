"""Prepared only: insert-only CSS viewing projection; no source content authoring."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
import argparse, hashlib, json, os, subprocess, time

ALLOWED = Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\training-assisted\search-basic-r07-display')
SOURCE = ALLOWED / 'render-r18/document.html'
NATIVE_REVIEW = ALLOWED / 'native-review-r01.json'
RECEIPT = ALLOWED.parent / 'runtime-code-assisted-10.json'
DEADLINE = datetime.fromisoformat('2026-10-13T20:15:58+00:00')
CHROMIUM = Path(r'C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe')
TARGET = 'table[data-renderer-markdown][data-renderer-columns]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"])'
CELLS = ','.join(TARGET + part for part in ('>thead>tr>th','>thead>tr>td','>tbody>tr>th','>tbody>tr>td','>tfoot>tr>th','>tfoot>tr>td','>tr>th','>tr>td'))
FIRST = ','.join(part + ':first-child' for part in CELLS.split(','))
CSS = CELLS + '{min-width:8em}' + FIRST + '{min-width:12em;white-space:nowrap;overflow-wrap:normal;word-break:normal;hyphens:none}'
STYLE = ('<style data-delivery-search-basic-columns="r01">' + CSS + '</style>').encode('utf-8')

FIXED_PINS = {
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\render_pinned_r18.py": "aa8e7fcfca1e8a376a000de62da077f59c0d2fd2a9d901df588d177672a8a677",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\delivery\\render_assisted_screen_r18.py": "2921f97c6c4cc396dc459c26c96ba8d692d6a3046be77f44724183d3376b1b6f",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\runtime-code-assisted-10.json": "54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be",
  "D:\\開発\\contextbase-evaluation\\test-project1\\spec-analysis\\CSharp_ASPNET\\20261013-rerun-12h\\training-assisted\\drafts\\revision-search-basic-r07\\基本設計書\\01_学生検索画面.md": "c954ae728a0a51040c2ab99dc0d20fc4416955483a158269e5014df7bd9e122b",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\.tmp\\20261013-rerun-12h\\training-assisted\\jobs\\revision-search-basic-r07\\draft-result.json": "2516ab6967ae2bb9498c410be725983c1a24eeb401c147882866501eb4ceb52e",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\.tmp\\20261013-rerun-12h\\training-assisted\\snapshot\\manifest.json": "e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\render-r18\\document.html": "0b91d1f2c87dc6a8a45206774e3fe4489270dffb024920e6e6aa0c27741c9acd",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\render-r18\\manifest.json": "b9aa89acc1ff3cb020aa710905f8532b4791579d0a3c09639c6e3f6f2d9464b9",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\render-r18\\render-pins.json": "113b1489c567d861ad2ae6562018cb09c51b678b01c0034225d7c21eee6e915e",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\delivery\\probe_registration_detail_columns_r03.py": "169a27a7e5d75d2ed91475a0673a5eb0d61b246668109b3b608c61eaab415a10",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\native-review-r01.json": "528e0138a0c76f685908eaabb62f88e3fcaa01b311769df72659cead0f260446",
  "D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\training-assisted\\search-basic-r07-display\\audit-helper-r01.json": "abb34eeb6a8a0c30e4892d66bdfa4df2f84824baf1d6c4ef53c44df7555bf42d"
}

def require(ok, message):
    if not ok: raise ValueError(message)

def safe(path):
    path = Path(os.path.abspath(path))
    for p in (path, *path.parents):
        require(not p.is_symlink() and not (p.exists() and getattr(p.lstat(), 'st_file_attributes', 0) & 0x400), 'Linked path rejected')
    return path

def sha(path): return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def digest(data): return hashlib.sha256(data).hexdigest()

def exclusive(path, data):
    with safe(path).open('xb') as stream: stream.write(data)

def output_path(value):
    path = safe(value)
    require(path.parent == safe(ALLOWED) and path.name.startswith('html-columns-'), 'Output outside fresh allowed candidate directory')
    return path

def stage(out, name, **extra):
    p = safe(out / 'stages.jsonl')
    with p.open('a', encoding='utf-8') as stream:
        event = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(), 'stage': name, **extra}
        stream.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(json.dumps(event, ensure_ascii=False), flush=True)

def runtime_inventory(root):
    root = safe(root); files = {}
    def visit(directory):
        for p in sorted(safe(directory).iterdir()):
            p = safe(p)
            if p.name == '__pycache__' or p.suffix in {'.pyc', '.pyo'}: continue
            if p.is_dir(): visit(p)
            elif p.is_file(): files[p.relative_to(root).as_posix()] = sha(p)
            else: raise ValueError('Unexpected runtime entry')
    visit(root); return files

def input_pins():
    pins = dict(FIXED_PINS)
    for p, expected in pins.items(): require(sha(p) == expected, 'Fixed input SHA mismatch: ' + p)
    native = json.loads(safe(NATIVE_REVIEW).read_text(encoding='utf-8'))
    require(len(native['beforeAfterPins']) == 404, 'Native review pin count mismatch')
    # Reuse metadata bindings only; its visual coverage/status is not borrowed.
    for p, expected in native['beforeAfterPins'].items():
        require(isinstance(expected, str), 'Invalid metadata hash entry')
        require(p not in pins or pins[p] == expected, 'Conflicting metadata pin')
        pins[p] = expected
    receipt = json.loads(safe(RECEIPT).read_text(encoding='utf-8'))
    root = safe(receipt['destination'])
    require(receipt['fileCount'] == len(receipt['files']) == 126, 'Frozen receipt count mismatch')
    require(runtime_inventory(root) == receipt['files'], 'Frozen non-cache source inventory mismatch')
    for relative, expected in receipt['files'].items():
        path = safe(root / relative)
        require(path.is_relative_to(root), 'Frozen entry escaped root')
        pins[str(path)] = expected
    pins[str(safe(__file__))] = sha(__file__)
    pins[str(safe(CHROMIUM))] = sha(CHROMIUM)
    for p, expected in pins.items(): require(sha(p) == expected, 'Pinned input SHA mismatch: ' + p)
    return pins, root, receipt['files']

@contextmanager
def temporary_runtime(runtime):
    temporary = safe(runtime / 'tmp'); temporary.mkdir(parents=True)
    previous = {key: os.environ.get(key) for key in ('TEMP', 'TMP', 'TMPDIR')}
    try:
        os.environ.update({key: str(temporary) for key in previous})
        yield
    finally:
        for key, value in previous.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value

def worker(out):
    from bs4 import BeautifulSoup
    from playwright.sync_api import sync_playwright
    require(datetime.now(timezone.utc) < DEADLINE, 'Deadline reached')
    out = output_path(out)
    require(out.is_dir() and (out / 'owned-launch.json').is_file(), 'Owned fresh launch required')
    pins, frozen, frozen_files = input_pins()
    original_bytes = safe(SOURCE).read_bytes()
    require(original_bytes.count(b'</head>') == 1 and original_bytes.count(b'<body') == 1, 'Unexpected safe HTML boundaries')
    offset = original_bytes.index(b'</head>')
    require(original_bytes.index(b'<head') < offset < original_bytes.index(b'<body'), 'CSS insertion outside head')
    projected_bytes = original_bytes[:offset] + STYLE + original_bytes[offset:]
    require(projected_bytes[:offset] + projected_bytes[offset + len(STYLE):] == original_bytes, 'Insert-only inverse bytes mismatch')
    original = original_bytes.decode('utf-8'); projected = projected_bytes.decode('utf-8')
    before = BeautifulSoup(original, 'html.parser'); after = BeautifulSoup(projected, 'html.parser')
    require(before.body is not None and after.body is not None, 'Missing body')
    body_before = str(before.body).encode('utf-8'); body_after = str(after.body).encode('utf-8')
    require(body_before == body_after and before.body.get_text() == after.body.get_text(), 'Body DOM/text changed')
    require(original_bytes[original_bytes.index(b'<body'):] == projected_bytes[projected_bytes.index(b'<body'):], 'Body raw bytes changed')
    require([str(x) for x in before.find_all('table')] == [str(x) for x in after.find_all('table')], 'Table attributes/order changed')
    require([str(x) for x in before.find_all('img')] == [str(x) for x in after.find_all('img')], 'Image elements/attributes/order changed')
    require([(x.name,dict(x.attrs)) for x in before.body.descendants if getattr(x, 'name', None)] == [(x.name,dict(x.attrs)) for x in after.body.descendants if getattr(x, 'name', None)], 'Body element attributes/order changed')
    marked = before.select('table[data-renderer-markdown]')
    require(all(str(t.get('data-renderer-columns','')).isdigit() and int(t['data-renderer-columns']) >= 1 for t in marked), 'Invalid marked table column metadata')
    target_count = sum(int(t['data-renderer-columns']) >= 3 for t in marked)
    require(target_count > 0, 'No marked 3+ column table')
    html_path = safe(out / '01_学生検索画面.html')
    exclusive(html_path, projected_bytes); exclusive(out / 'candidate.css', CSS.encode('utf-8'))
    stage(out, 'insert-only-and-body-equality-verified', sourceHtmlSha256=digest(original_bytes), projectionHtmlSha256=digest(projected_bytes), insertionOffset=offset, targetTableCount=target_count)
    runtime = safe(out / '.runtime'); require(not runtime.exists(), 'Runtime profile already exists')
    runtime.mkdir()
    requests = []; pages = []
    style_check = """selector => Array.from(document.querySelectorAll('table')).filter(t=>!t.matches(selector)).map(t=>Array.from(t.querySelectorAll('th,td')).map(c=>{const s=getComputedStyle(c);return {whiteSpace:s.whiteSpace,minWidth:s.minWidth,wordBreak:s.wordBreak,overflowWrap:s.overflowWrap,hyphens:s.hyphens}}))"""
    with temporary_runtime(runtime), sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(str(safe(runtime / 'profile')),
            executable_path=str(safe(CHROMIUM)), headless=True, timeout=45000,
            java_script_enabled=False, service_workers='block', locale='ja-JP', accept_downloads=False,
            viewport={'width':2400,'height':4000}, device_scale_factor=1,
            downloads_path=str(safe(runtime / 'downloads')), traces_dir=str(safe(runtime / 'traces')))
        try:
            def abort(route): requests.append(route.request.url); route.abort()
            context.route('**/*', abort)
            page = context.new_page(); page.set_default_timeout(45000)
            page.set_content(original, wait_until='domcontentloaded', timeout=45000)
            page.evaluate('() => document.fonts.ready.then(() => true)')
            unaffected_before = page.evaluate(style_check, TARGET)
            page.set_content(projected, wait_until='domcontentloaded', timeout=45000)
            page.evaluate('() => document.fonts.ready.then(() => true)')
            unaffected_after = page.evaluate(style_check, TARGET)
            require(unaffected_before == unaffected_after, 'Unmarked/1-2-column/embedded table computed properties changed')
            dims = page.evaluate('() => ({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,bodyWidth:document.body.scrollWidth})')
            require(dims['width'] <= 2400, 'Projection exceeds 2400px viewport')
            diagnostics = page.evaluate("""selector => {
                const found=[];
                for(const c of document.querySelectorAll(selector)) {
                    const walker=document.createTreeWalker(c,NodeFilter.SHOW_TEXT);
                    for(let node;node=walker.nextNode();) for(const m of node.textContent.matchAll(/[A-Za-z_][A-Za-z0-9_]*(?:[-.][A-Za-z0-9_]+)*/g)) {
                        const r=document.createRange();r.setStart(node,m.index);r.setEnd(node,m.index+m[0].length);
                        const rects=Array.from(r.getClientRects()).filter(x=>x.width>0&&x.height>0);
                        const tops=Array.from(new Set(rects.map(x=>Math.round(x.top*10)/10)));
                        if(tops.length>1) found.push({token:m[0],visibleRowTops:tops,firstColumn:c.cellIndex===0});
                    }
                } return found;
            }""", CELLS)
            for y in range(0, dims['height'], 4000):
                require(datetime.now(timezone.utc) < DEADLINE, 'Deadline reached while capturing')
                height = min(4000, dims['height'] - y)
                target = safe(out / ('document-page-%03d.png' % (len(pages)+1)))
                require(not target.exists(), 'Capture already exists')
                page.screenshot(full_page=True, animations='disabled', path=str(target),
                    clip={'x':0,'y':y,'width':2400,'height':height}, timeout=45000)
                pages.append({'path':str(target),'sha256':sha(target),'x':0,'y':y,'width':2400,'height':height,'scale':1})
                stage(out, 'native-page-captured', page=len(pages), y=y, height=height)
        finally:
            context.close()
    require(not requests, 'Unexpected blocked network requests')
    require(runtime_inventory(frozen) == frozen_files, 'Frozen non-cache inventory changed')
    require(all(sha(p) == expected for p, expected in pins.items()), 'Source pins changed')
    result = {
        'schema':'search-basic-insert-only-css-native-capture/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'DERIVED_NATIVE_GEOMETRY_ONLY','status':'NATIVE_CAPTURED_VISUAL_REVIEW_PENDING',
        'documentId':'CSHARP_ASPNET-BAS-STU-01','markdownSha256':'c954ae728a0a51040c2ab99dc0d20fc4416955483a158269e5014df7bd9e122b',
        'sourceHtml':str(SOURCE),'sourceHtmlSha256':digest(original_bytes),'projectionHtml':str(html_path),'projectionHtmlSha256':digest(projected_bytes),
        'css':CSS,'cssSha256':digest(CSS.encode('utf-8')),'insertionOffset':offset,'insertedByteLength':len(STYLE),'insertedBytesSha256':digest(STYLE),
        'removeInsertedElementRecoversOriginalBytes':True,'bodyRawBytesEqual':True,'bodyDomBytesEqual':True,'bodyDomSha256':digest(body_before),'bodyTextEqual':True,
        'allTablesDeepExact':True,'allImageElementsDeepExact':True,'bodyElementOrderExact':True,'allTablesEqual':True,'allImageElementsEqual':True,
        'unmarkedAndOneTwoColumnTableComputedPropertiesExact':True,'targetMarkedTableCount':target_count,
        'dimensions':dims,'documentCapture':{'width':2400,'height':dims['height'],'pages':pages},
        'asciiWholeTokenWrapDiagnostics':diagnostics,'sourceBindings':pins,'sourceBindingsBefore':pins,'sourceBindingsAfter':pins,'allPinnedBytesUnchanged':True,
        'rendererNonCacheFiles':126,'cacheFilesIncludedInImmutabilityClaim':False,
        'javascriptEnabled':False,'networkRequests':requests,'profile':str(runtime / 'profile'),'temporaryRoot':str(runtime / 'tmp'),
        'borrowedVisualCoverage':0,'actualVisualReviewPerformed':False,'applicationExecuted':False,'providerExecuted':False,
        'canonicalOrOriginalHtmlModified':False,'businessContentAuthored':False,'mainModified':False,'sourceModified':False,
        'formalApproval':False,'semanticApproval':False,'stateApproval':False,'wholeDocumentApproval':False,'adoptionApproval':False,'published':False}
    exclusive(out / 'result.json', (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    stage(out, 'capture-complete-visual-review-pending', pages=len(pages), diagnostics=len(diagnostics), resultSha256=sha(out / 'result.json'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-root',type=Path,default=ALLOWED/'html-columns-r01')
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args(); out=output_path(args.output_root)
    require(safe(Path(__file__).parent) == safe(ALLOWED), 'Helper outside designated directory')
    if args.worker: return worker(out)
    remaining=(DEADLINE-datetime.now(timezone.utc)).total_seconds()
    require(remaining > 30, 'Insufficient deadline reserve')
    require(not out.exists(), 'Fresh output directory required')
    out.mkdir()
    exclusive(out/'owned-launch.json',json.dumps({'parentPid':os.getpid(),'helper':str(safe(__file__)),'helperSha256':sha(__file__),'output':str(out),'scope':'DERIVED_NATIVE_GEOMETRY_ONLY'}).encode('utf-8'))
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    timeout=min(240,remaining-30);started=time.monotonic()
    with safe(out/'stdout.log').open('xb') as stdout, safe(out/'stderr.log').open('xb') as stderr:
        proc=subprocess.Popen([sys.executable,'-B','-X','utf8','-u',str(safe(__file__)),'--output-root',str(out),'--worker'],
            stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        status='UNKNOWN';code=None
        try:
            code=proc.wait(timeout=timeout);status='COMPLETE' if code==0 else 'FAILED'
        except subprocess.TimeoutExpired:
            status='TIMED_OUT'
            if proc.poll() is None:subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=10)
            code=proc.wait(timeout=10)
    metadata={'status':status,'ownedWorkerPid':proc.pid,'exitCode':code,'elapsedSeconds':round(time.monotonic()-started,3),'timeoutSeconds':timeout,'deadline':DEADLINE.isoformat(),'cleanupReserveSeconds':30,
        'scope':'DERIVED_NATIVE_GEOMETRY_ONLY','applicationExecuted':False,'providerExecuted':False,'actualVisualReviewPerformed':False,'semanticApproval':False,'formalApproval':False,'wholeDocumentApproval':False,'published':False}
    exclusive(out/'worker.json',(json.dumps(metadata,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(metadata),flush=True)
    return 0 if status=='COMPLETE' else 1

if __name__ == '__main__': sys.exit(main() or 0)
