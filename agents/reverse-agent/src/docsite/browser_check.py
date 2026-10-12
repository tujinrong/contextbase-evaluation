"""In-memory browser verification; external navigation is blocked."""
from __future__ import annotations
import argparse
import base64
import mimetypes
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
from pathlib import Path
from playwright.sync_api import sync_playwright
from .common import js,write,sha


def browser_html(target: Path, root: Path) -> str:
    """Embed verified local image bytes for browser environments blocking file://."""
    soup=BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser')
    allowed=(root/'output/html').resolve()
    for image in soup.find_all('img',src=True):
        uri=urlsplit(image['src'])
        if uri.scheme or uri.netloc:continue
        path=target.parent/unquote(uri.path)
        if path.is_symlink() or not path.resolve().is_relative_to(allowed):raise ValueError('Image outside HTML output')
        if not path.is_file() or path.stat().st_size>20_000_000:raise ValueError('Missing or oversized HTML image')
        mime=mimetypes.guess_type(path.name)[0]
        if mime not in {'image/png','image/jpeg','image/gif','image/webp','image/svg+xml'}:raise ValueError('Unsupported HTML image')
        image['src']='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
    return str(soup)


def run(root:Path,executable:str|None=None) -> dict:
    root=root.resolve();results=[]
    write(root/'report/docsite/browser.json',js({'status':'running'}))
    screenshots=root/'report/docsite/screenshots';screenshots.mkdir(parents=True,exist_ok=True)
    targets=sorted((root/'output/html').rglob('*.html'))
    if not targets:raise ValueError('No HTML pages to inspect')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1000},locale='ja-JP')
        for target in targets:
            page=context.new_page();errors=[];network=[]
            def route(request):
                network.append(request.request.url);request.abort()
            page.route('https://**/*',route);page.route('http://**/*',route)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.set_content(browser_html(target,root),wait_until='load',timeout=60000)
            image_errors=page.locator('article img, .doc-body img').evaluate_all('(images)=>images.filter(i=>!i.complete || i.naturalWidth===0).map(i=>i.getAttribute("src"))')
            if image_errors:errors.append('unloaded images: '+str(image_errors))
            state=page.evaluate('({expected:document.querySelectorAll("figure.diagram").length,rendered:document.querySelectorAll("figure.diagram svg.flowchart-svg").length,errors:[]})')
            blank=page.locator('figure.diagram svg.flowchart-svg').evaluate_all('(nodes)=>nodes.filter(n=>n.getBoundingClientRect().width===0 || n.getBoundingClientRect().height===0).length')
            if blank:state['errors'].append('zero-size SVG: '+str(blank))
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
            count=page.locator('.screen-layout [data-item]').count()
            if count and len(list(screenshots.glob('*.png'))) < 3:
                page.locator('.screen-layout').scroll_into_view_if_needed()
                page.evaluate('window.scrollTo(0,document.querySelector(".screen-layout").getBoundingClientRect().top+scrollY-85)')
                page.screenshot(path=str(screenshots/(target.stem+'.png')))
            results.append({'file':target.relative_to(root).as_posix(),'html_sha256':sha(target.read_bytes()),'layout_items':count,'mermaid':state,
                'page_errors':errors,'external_requests':network,'horizontal_overflow':overflow})
            page.close()
        browser.close()
    failed=[r for r in results if r['page_errors'] or r['external_requests'] or r['horizontal_overflow'] or r['mermaid']['errors'] or r['mermaid']['rendered']!=r['mermaid']['expected']]
    report={'status':'pass' if not failed else 'error','pages':len(results),
        'mermaid_expected':sum(r['mermaid']['expected'] for r in results),'mermaid_rendered':sum(r['mermaid']['rendered'] for r in results),
        'layout_items':sum(r['layout_items'] for r in results),'failed_pages':len(failed),'results':results,
        'scope':'Chromium in-memory rendering; referenced local image bytes are verified and embedded as data URLs. Network is blocked; image decoding and geometry are checked. File opening and click navigation are not exercised.'}
    write(root/'report/docsite/browser.json',js(report));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--executable');a=parser.parse_args()
    report=run(Path(a.root),a.executable)
    print(js({k:v for k,v in report.items() if k!='results'}))
    raise SystemExit(int(report['status']!='pass'))
