"""Trusted synthetic table-CSS probe. No source application or business prose creation."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from datetime import datetime, timezone

from markdown_it import MarkdownIt
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from contextbase.ai import rendering as baseline, capsule

HERE = Path(__file__).resolve().parent
REPO = Path(r'D:\開発\contextbase-evaluation')
REPORT = REPO / 'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot'
RECEIPT = REPORT / 'runtime-code-source-10.json'
RECEIPT_SHA = 'a38c4efa878dc4c6a47967a39b99494ddc3818d63db953e00058e7eab80b1083'
CHROME = Path(r'C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe')
SELECTOR = 'table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"])'
CSS = (SELECTOR + '{table-layout:auto}' + SELECTOR + ' col{width:auto!important}' +
       SELECTOR + ' th,' + SELECTOR + ' td{overflow-wrap:normal;word-break:normal;white-space:normal}')
NORMAL_ONLY_CSS = SELECTOR + ' th,' + SELECTOR + ' td{overflow-wrap:normal;word-break:normal;white-space:normal}'

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def write(path: Path, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8') if not isinstance(value, bytes) else value
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(raw)

def integrity():
    if sha(capsule.safe_path(RECEIPT).read_bytes()) != RECEIPT_SHA:
        raise ValueError('Frozen source10 receipt drift')
    receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
    root = capsule.safe_path(Path(receipt['destination']))
    found = {p.relative_to(root).as_posix(): sha(capsule.safe_path(p).read_bytes())
             for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if found != receipt['files']:
        raise ValueError('Frozen source10 inventory drift')
    for name, exact in receipt['imports'].items():
        spec = importlib.util.find_spec(name)
        if spec is None or Path(spec.origin).resolve() != Path(exact).resolve():
            raise ValueError('Resolved import drift: ' + name)
    exact_renderer = root / 'contextbase/ai/rendering.py'
    if Path(baseline.__file__).resolve() != exact_renderer.resolve():
        raise ValueError('Loaded baseline renderer wrong')
    return {'receiptSha256': RECEIPT_SHA, 'root': str(root), 'files': len(found),
            'imports': len(receipt['imports']), 'rendererSha256': sha(exact_renderer.read_bytes()),
            'rendererFile': str(exact_renderer)}

def derived():
    raw = Path(baseline.__file__).read_bytes()
    tree = ast.parse(raw)
    match = [n for n in tree.body if isinstance(n, ast.Assign) and
             any(isinstance(t, ast.Name) and t.id == 'BASE_STYLE' for t in n.targets)]
    if len(match) != 1:
        raise ValueError('One BASE_STYLE assignment required')
    lines = raw.decode('utf-8').splitlines(keepends=True)
    node = match[0]
    lines[node.lineno-1:node.end_lineno] = ['BASE_STYLE = ' + repr(baseline.BASE_STYLE + CSS) + '\n']
    copy = ''.join(lines).encode('utf-8')
    out = HERE / 'rendering_table_css_prototype.py'
    write(out, copy)
    # Every AST definition/import remains exactly unchanged; only one trusted style constant differs.
    old = [ast.dump(n, include_attributes=False) for n in tree.body if n is not node]
    new_tree = ast.parse(copy)
    new = [ast.dump(n, include_attributes=False) for n in new_tree.body if not
           (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BASE_STYLE' for t in n.targets))]
    if old != new:
        raise ValueError('Prototype changes outside BASE_STYLE')
    spec = importlib.util.spec_from_file_location('contextbase.ai.table_css_prototype_r01', out)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, {'path': str(out), 'sha256': sha(copy), 'onlyBaseStyleAstChanged': True,
                    'css': CSS, 'cssSha256': sha(CSS.encode())}

def table(headers, rows):
    return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---'] * len(headers)) + '|\n' + '\n'.join(
        '| ' + ' | '.join(row) + ' |' for row in rows) + '\n\n'

ATOMIC = ['SYNTHETIC_CATEGORY_WITH_LONG_NAME', 'sample_atomic_identifier_abcdefghijklmno',
          'unique_synthetic_datatype', '123456789012345678901234567890123456789012345678901234567890',
          'SYNTHETIC-STATUS-0123456789', 'SampleAtomicIdentifierWithManyCharactersWithoutBreaks',
          'sample_parameter_identifier_abcdefghijklmnopqrstuvwxyz']
EMBEDDED = ('<style>#embedded{width:320px;border:2px solid #345;padding:8px;font-size:15px}'
            '#embedded table{width:300px;border-collapse:collapse}#embedded td{border:1px solid #789;padding:4px}'
            '#embedded input{width:120px}#embedded textarea{width:140px;height:40px}</style>'
            '<div id="embedded"><h3>独立合成レイアウト</h3><table><tbody><tr><td>固定欄</td>'
            '<td>ScreenAtomicIdentifier</td></tr><tr><td><input disabled value="fixture"></td>'
            '<td><textarea disabled>合成表示</textarea></td></tr></tbody></table></div>')
FIXTURE = '# Trusted synthetic CSS fixture\n\n'
FIXTURE += table(['単独欄'], [['OneColumnStableIdentifier 日本語説明']])
FIXTURE += table(['識別子', '説明'], [['TwoColumnStableIdentifier', '二列表の説明。' * 8]])
FIXTURE += table(['分類ID', 'パラメータ', '説明'], [[ATOMIC[0], ATOMIC[6], '日本語説明を自然に折り返す。' * 16]])
FIXTURE += table(['分類ID', '列A', '列B', '列C', '列D', '説明'],
                 [[ATOMIC[0], ATOMIC[1], ATOMIC[2], ATOMIC[3], ATOMIC[4], '長い日本語の合成説明。' * 14]])
FIXTURE += table(['No', 'physical_id', 'logical', 'kind', 'size', 'required', 'default', 'source', 'description'],
                 [['1', '`' + ATOMIC[1] + '`', '日本語項目', ATOMIC[2], '1234567890', 'Y', 'NULL', 'FixtureOnly:1', '日本語説明。' * 20],
                  ['2', ATOMIC[5], '空欄例', 'text', '', 'N', '', 'FixtureOnly:2', '説明の後に `SyntheticInlineCode` を保持する。']])
FIXTURE += table(['No', 'group', 'item', 'type', 'io', 'binding', 'choice', 'required', 'format', 'description'],
                 [['1', 'SyntheticGroup', 'SyntheticItem', 'text', 'I', ATOMIC[1], 'SyntheticCandidate', 'Y', '99999', '日本語説明。' * 10]])
FIXTURE += EMBEDDED

JS = r'''({atomic}) => {
  const rect = r => ({x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom});
  const tables = [...document.querySelectorAll('table')].map(t => ({outerHTML:t.outerHTML,
    parser:t.hasAttribute('data-renderer-markdown'), columns:t.getAttribute('data-renderer-columns'),
    box:rect(t.getBoundingClientRect()), layout:getComputedStyle(t).tableLayout,
    cells:[...t.querySelectorAll('th,td')].map(c => ({tag:c.tagName,html:c.innerHTML,text:c.textContent,
      rowSpan:c.rowSpan,colSpan:c.colSpan,box:rect(c.getBoundingClientRect()),
      overflowWrap:getComputedStyle(c).overflowWrap,wordBreak:getComputedStyle(c).wordBreak,
      whiteSpace:getComputedStyle(c).whiteSpace}))}));
  const tokens=[],overflows=[];
  for(const cell of document.querySelectorAll('table[data-renderer-markdown] th, table[data-renderer-markdown] td')) {
    const walker=document.createTreeWalker(cell,NodeFilter.SHOW_TEXT); let n;
    while(n=walker.nextNode()) {
      if(!n.textContent.trim())continue;
      const r=document.createRange();r.selectNodeContents(n);
      const boxes=[...r.getClientRects()].map(rect), cb=cell.getBoundingClientRect();
      for(const b of boxes)if(b.x<cb.x-1||b.right>cb.right+1||b.y<cb.y-1||b.bottom>cb.bottom+1)
        overflows.push({text:n.textContent,box:b,cell:rect(cb)});
      for(const token of atomic) { let from=0,pos;
        while((pos=n.textContent.indexOf(token,from))>=0) {
          const tr=document.createRange();tr.setStart(n,pos);tr.setEnd(n,pos+token.length);
          const br=[...tr.getClientRects()].filter(x=>x.width>0).map(rect);
          const lines=[...new Set(br.map(b=>Math.round(b.y*10)/10))];
          tokens.push({token,rects:br,lineCount:lines.length,singleLine:lines.length===1,
            withinCell:br.every(b=>b.x>=cb.x-1&&b.right<=cb.right+1&&b.y>=cb.y-1&&b.bottom<=cb.bottom+1)});
          from=pos+token.length;
        }
      }
    }
  }
  const embedded=document.querySelector('#embedded');
  return {tables,tokens,overflows,width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,
          embedded:embedded?{html:embedded.outerHTML,box:rect(embedded.getBoundingClientRect()),
            descendants:[...embedded.querySelectorAll('*')].map(e=>({tag:e.tagName,
              x:e.getBoundingClientRect().x-embedded.getBoundingClientRect().x,
              y:e.getBoundingClientRect().y-embedded.getBoundingClientRect().y,
              width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,
              layout:getComputedStyle(e).tableLayout,overflowWrap:getComputedStyle(e).overflowWrap}))}:null};
}'''

def parser_body(module, source):
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    parser.renderer.rules['table_open'] = lambda tokens,index,options,env: module._markdown_table_open(
        tokens,index,options,env,parser.renderer)
    return parser.render(source)

def measure(context, module, source, out, atomic=ATOMIC, extra_css=''):
    out.mkdir(exist_ok=False)
    body = parser_body(module, source)
    document = module._html(body, '<style>'+extra_css+'</style>' if extra_css else '')
    write(out / 'fixture.html', document.encode('utf-8'))
    page = context.new_page()
    try:
        page.set_content(document, wait_until='load')
        page.evaluate('() => document.fonts.ready')
        state = page.evaluate(JS, {'atomic':atomic})
        display = {}
        try:
            module._capture_document(page, out, display)
            state['capture'] = {'status':'PASS',**display}
        except ValueError as e:
            state['capture'] = {'status':'REJECTED','reason':str(e)}
        if page.locator('#embedded').count():
            page.locator('#embedded').screenshot(path=str(out/'embedded.png'), animations='disabled')
        write(out/'measurement.json',state)
        return state
    finally:
        page.close()

def structural(state):
    return [{'outerHTML':t['outerHTML'], 'parser':t['parser'], 'columns':t['columns'],
             'cells':[{k:c[k] for k in ('tag','html','text','rowSpan','colSpan')} for c in t['cells']]}
            for t in state['tables']]

def protected_geometry(state):
    result=[]
    for t in state['tables']:
        if t['parser'] and t['columns'] not in ('1','2'):
            continue
        result.append({'width':t['box']['width'],'height':t['box']['height'],'layout':t['layout'],
          'cells':[{'x':c['box']['x']-t['box']['x'],'y':c['box']['y']-t['box']['y'],
                    'width':c['box']['width'],'height':c['box']['height'],
                    **{k:c[k] for k in ('overflowWrap','wordBreak','whiteSpace')}} for c in t['cells']]})
    return result

def coverage(out, state):
    capture=state['capture']
    if capture['status']!='PASS':return {'pass':False,'reason':'No capture'}
    paths=([{'path':'document.png','sourceRectangle':{'x':0,'y':0,'width':state['width'],'height':state['height']}}]
           if 'documentPng' in capture else capture['documentCapture']['pages'])
    cursor=0;records=[]
    for item in paths:
        p=out/item['path'];box=item['sourceRectangle']
        with Image.open(p) as im:
            actual=im.size
        expected=(box['width'],box['height'])
        if actual!=expected or box['x']!=0 or box['y']!=cursor or box['width']!=state['width']:
            raise ValueError('Incomplete full-width coverage')
        cursor+=box['height'];records.append({'path':str(p),'sha256':sha(p.read_bytes()),'size':actual,'sourceRectangle':box})
    return {'pass':cursor==state['height'],'records':records,'coveredHeight':cursor,
            'expectedHeight':state['height'],'fullWidth':state['width']}

def main():
    before=integrity();candidate,copy_receipt=derived()
    write(HERE/'fixture.md',FIXTURE.encode('utf-8'))
    write(HERE/'candidate.css',CSS.encode('utf-8'))
    results=[];all_checks=[];blocked=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=str(CHROME),headless=True)
        try:
            for width in (1440,800):
                context=browser.new_context(java_script_enabled=False, viewport={'width':width,'height':1000},
                                           locale='ja-JP',service_workers='block')
                context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort())[1])
                try:
                    bdir=HERE/f'baseline-{width}';cdir=HERE/f'candidate-{width}'
                    old=measure(context,baseline,FIXTURE,bdir)
                    new=measure(context,candidate,FIXTURE,cdir)
                    image_same=ImageChops.difference(Image.open(bdir/'embedded.png').convert('RGBA'),
                                                    Image.open(cdir/'embedded.png').convert('RGBA')).getbbox() is None
                    checks={'domExact':structural(old)==structural(new),
                            'protectedTableGeometryExact':protected_geometry(old)==protected_geometry(new),
                            'embeddedLocalGeometryExact':old['embedded']['descendants']==new['embedded']['descendants'],
                            'embeddedPixelsExact':image_same,
                            'baselineBrokenTokenReproduced':any(not t['singleLine'] for t in old['tokens']),
                            'candidateAtomicTokensSingleLine':bool(new['tokens']) and all(t['singleLine'] for t in new['tokens']),
                            'candidateTokensInsideCells':all(t['withinCell'] for t in new['tokens']),
                            'candidateAllTextInsideCells':not new['overflows'],
                            'candidateCapturePassed':new['capture']['status']=='PASS'}
                    cov_b=coverage(bdir,old);cov_c=coverage(cdir,new)
                    checks['baselinePixelCoverage']=cov_b['pass'];checks['candidatePixelCoverage']=cov_c['pass']
                    all_checks.extend(checks.values())
                    results.append({'viewportWidth':width,'checks':checks,'baselineWidth':old['width'],
                                    'candidateWidth':new['width'],'baselineCoverage':cov_b,'candidateCoverage':cov_c,
                                    'baselineBrokenTokenCount':sum(not t['singleLine'] for t in old['tokens']),
                                    'candidateBrokenTokens':[t for t in new['tokens'] if not t['singleLine']],
                                    'candidateOverflowCount':len(new['overflows'])})
                finally:context.close()
            context=browser.new_context(java_script_enabled=False,viewport={'width':1440,'height':1000},service_workers='block')
            context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort())[1])
            try:
                long='W'*2500
                excessive=table(['分類ID','value','description'],[[long,'Synthetic','超長幅負例']])
                over=measure(context,candidate,excessive,HERE/'candidate-excessive-width',atomic=[long])
                over_ok=over['width']>16000 and over['capture']['status']=='REJECTED' and not list((HERE/'candidate-excessive-width').glob('*.png'))
                fixed=measure(context,baseline,table(['分類ID','value','description'],[[ATOMIC[0],ATOMIC[5],'合成負例']]),
                              HERE/'fixed-normal-only-negative',extra_css=NORMAL_ONLY_CSS)
                fixed_ok=bool(fixed['overflows']) and any(not t['withinCell'] for t in fixed['tokens'])
                authored=measure(context,candidate,table(['分類ID','value','description'],[['AuthoredAtomic<br>Token','1','明示改行負例']]),
                                 HERE/'authored-break-negative',atomic=['AuthoredAtomic','Token'])
                authored_ok='AuthoredAtomic<br>Token' in authored['tables'][0]['cells'][3]['html'] and len(set(
                    t['rects'][0]['y'] for t in authored['tokens']))==2
                all_checks.extend([over_ok,fixed_ok,authored_ok])
                negative={'excessiveWidth':{'pass':over_ok,'width':over['width'],'capture':over['capture']},
                          'fixedNormalOnly':{'pass':fixed_ok,'overflowCount':len(fixed['overflows'])},
                          'authoredBreakPreserved':{'pass':authored_ok,'noRepairOrAtomicApproval':True}}
            finally:context.close()
        finally:browser.close()
    after=integrity()
    summary={'schema':'trusted-synthetic-table-css-prototype/1','createdAt':datetime.now(timezone.utc).isoformat(),
             'scope':'SYNTHETIC_TABLE_CSS_GEOMETRY_ONLY','fixtureSha256':sha((HERE/'fixture.md').read_bytes()),
             'candidate':copy_receipt,'frozenRuntimeBefore':before,'frozenRuntimeAfter':after,
             'frozenRuntimeUnchanged':before==after,'inputApplicationExecuted':False,'aiProviderInvoked':False,
             'businessMaterialsRead':False,'staticContextJavaScriptEnabled':False,
             'trustedEvaluationOnly':True,'blockedRequests':blocked,'comparisons':results,'negativeCases':negative,
             'mechanicalPass':all(all_checks) and before==after,'nativeVisualReview':'PENDING',
             'mainCodeModified':False,'adopted':False}
    write(HERE/'result.json',summary)
    print(json.dumps({'result':str(HERE/'result.json'),'mechanicalPass':summary['mechanicalPass'],
                      'comparisons':[r['checks'] for r in results],'negativeCases':negative},ensure_ascii=False))

if __name__=='__main__':main()
