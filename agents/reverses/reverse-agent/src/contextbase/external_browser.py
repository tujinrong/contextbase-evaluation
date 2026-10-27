"""Inspect source-derived layout states without executing the target application."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def run(root:Path)->dict:
    report=root/'report/external-layout';report.mkdir(parents=True,exist_ok=True)
    (report/'browser.json').write_text('{"status":"running"}',encoding='utf-8')
    targets=[p for p in sorted((root/'output/html').rglob('*.html')) if 'class="ext-screen"' in p.read_text(encoding='utf-8')]
    results=[]
    if not targets:
        result={'status':'not_applicable','states':0,'results':[],'scope':'No source-derived external layout states.'}
        (report/'browser.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':2000,'height':1100},locale='ja-JP')
        for target in targets:
            text=target.read_text(encoding='utf-8');soup=BeautifulSoup(text,'html.parser')
            for state in soup.select('.screen-layout[data-screen]'):
                page=context.new_page();network=[];errors=[]
                def block(route):network.append(route.request.url);route.abort()
                page.route('https://**/*',block);page.route('http://**/*',block)
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.set_content(text,wait_until='load')
                ident=state['data-screen'];selector='[data-screen="'+ident+'"]'
                page.locator(selector).evaluate('(n)=>{for(let p=n.parentElement;p;p=p.parentElement){if(p.tagName==="DETAILS")p.open=true}}')
                frame=page.locator(selector+' .ext-screen')
                measurements=frame.evaluate('''n=>({width:n.getBoundingClientRect().width,expectedWidth:Number(n.dataset.width),fields:[...n.querySelectorAll('[data-field]')].map(f=>({id:f.dataset.field,mode:f.dataset.mode,width:f.getBoundingClientRect().width,height:f.getBoundingClientRect().height})),groups:[...n.querySelectorAll('.ext-group h4')].map(g=>g.textContent),rows:[...n.querySelectorAll('.ext-row')].map(r=>({width:r.getBoundingClientRect().width,columns:[...r.children].filter(c=>c.classList.contains('ext-col')).map(c=>({span:Number(c.dataset.span),x:c.getBoundingClientRect().x,y:c.getBoundingClientRect().y,width:c.getBoundingClientRect().width}))})),headers:[...n.querySelectorAll('.ext-grid th')].map(h=>({label:h.textContent,width:h.getBoundingClientRect().width})),buttons:[...n.querySelectorAll('.ext-footer button')].map(b=>b.textContent)})''')
                if abs(measurements['width']-measurements['expectedWidth'])>1:errors.append('declared screen width not retained')
                for f in measurements['fields']:
                    if f['width']<=0 or f['height']<=0:errors.append('zero-size field: '+f['id'])
                for row in measurements['rows']:
                    cols=row['columns']
                    for col in cols:
                        if abs(col['width']-row['width']*col['span']/24)>2:errors.append('column span width mismatch')
                    if cols and sum(c['span'] for c in cols)<=24 and max(c['y'] for c in cols)-min(c['y'] for c in cols)>2:errors.append('same-row columns wrapped unexpectedly')
                if page.evaluate('document.documentElement.scrollWidth>innerWidth+2'):errors.append('document horizontal overflow')
                if network:errors.append('external request attempted')
                page.add_style_tag(content='.page-shell{display:block!important;max-width:1900px!important}.toc{display:none!important}.document{padding:20px!important}.screen-layout{max-width:none!important;width:1520px!important}')
                frame.scroll_into_view_if_needed()
                image=report/(re.sub(r'[^\w-]','_',ident)+'.png');frame.screenshot(path=str(image))
                results.append({'file':target.relative_to(root).as_posix(),'html_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'state':ident,'measurements':measurements,'errors':errors,'screenshot':image.relative_to(root).as_posix()})
                page.close()
        browser.close()
    result={'status':'pass' if all(not r['errors'] for r in results) else 'failed','states':len(results),'failed_states':sum(bool(r['errors']) for r in results),'results':results,'scope':'Generated HTML geometry and source-declared dimensions only. No live application, real data, event execution or pixel comparison with production UI.'}
    (report/'browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    r=run(Path.cwd());print(json.dumps({k:v for k,v in r.items() if k!='results'},ensure_ascii=False,indent=2));raise SystemExit(int(r['status']=='failed'))
