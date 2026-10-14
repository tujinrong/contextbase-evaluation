"""Offline derivative layout experiments on two already-rendered diagrams.

No MD, source, reference specification, grade cap or renderer-core mutation.
Only trusted Mermaid runs JS; actual app JS/HTML/DB never runs.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from contextbase.ai import rendering

ROOT=Path(__file__).resolve().parent
REPORT=ROOT.parent
OUT=ROOT/'mermaid-layout-probe-r01'
BUNDLE=Path('D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js')
CHROMIUM='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
CSS='.edgeLabel rect{opacity:1!important;fill:#ffffff!important}.edgeLabel .labelBkg{background-color:#ffffff!important}'
SOURCES=[('source-search-detail-025',REPORT/'render/search-detail-r03','diagram-025'),
         ('assisted-register-basic-019',REPORT/'render/assisted-register-basic-r02','diagram-019')]
VARIANTS=[('wide-320',{'wrappingWidth':320,'minNodeWidth':120,'nodeSpacing':50,'rankSpacing':60,'padding':15}),
          ('compact-240',{'wrappingWidth':240,'minNodeWidth':100,'nodeSpacing':28,'rankSpacing':25,'padding':10})]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):return sha(Path(path).read_bytes())
def normalize(value):return ''.join(value.split())
def signature(raw):
    soup=BeautifulSoup(raw,'xml')
    node_key=lambda n:re.sub(r'^.*?-flowchart-','',n['id'])
    nodes=[{'key':node_key(n),'text':normalize(n.get_text()),
            'shapes':sorted(child.name for child in n.find_all(['rect','polygon','circle','ellipse','path'],recursive=False))}
           for n in soup.select('g.node')]
    edges=[{'key':n['data-id'],'style':sorted(c for c in n.get('class','').split() if c in {'edge-pattern-solid','edge-pattern-dotted','edge-pattern-dashed'}),
            'markerStart':bool(n.get('marker-start')),'markerEnd':bool(n.get('marker-end'))}
           for n in soup.select('path.flowchart-link')]
    labels=[{'key':n['data-id'],'text':normalize(n.get_text())} for n in soup.select('g.edgeLabel g.label[data-id]')]
    return {'nodes':nodes,'edges':edges,'edgeLabels':labels}

def geometry(raw):
    soup=BeautifulSoup(raw,'xml')
    return [{'tag':n.name,'id':n.get('id'),'transform':n.get('transform'),'d':n.get('d'),
             'points':n.get('points'),'x':n.get('x'),'y':n.get('y'),'width':n.get('width'),'height':n.get('height')}
            for n in soup.find_all(['svg','g','path','polygon','rect','circle','ellipse','text','tspan'])]

def opacity_css(raw):
    tree=ET.fromstring(raw)
    style=ET.SubElement(tree,'{http://www.w3.org/2000/svg}style')
    style.text=CSS
    return rendering._svg_safe(ET.tostring(tree,encoding='unicode'))

def main():
    OUT.mkdir(exist_ok=False)
    inputs={str(folder/(stem+suffix)):digest(folder/(stem+suffix)) for _,folder,stem in SOURCES for suffix in ['.mmd','.svg','.png']}
    inputs[str(Path(rendering.__file__))]=digest(rendering.__file__)
    records=[];blocked=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROMIUM,headless=True)
        script=browser.new_context(java_script_enabled=True,service_workers='block',viewport={'width':2400,'height':1600})
        static=browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2400,'height':1600})
        def abort(route):blocked.append(route.request.url);route.abort()
        script.route('**/*',abort);static.route('**/*',abort)
        script.set_default_timeout(20000);static.set_default_timeout(20000)
        try:
            page=script.new_page();page.set_content(rendering._html('',scripts=True));page.add_script_tag(path=str(BUNDLE))
            for role,folder,stem in SOURCES:
                text=(folder/(stem+'.mmd')).read_text(encoding='utf-8')
                original=(folder/(stem+'.svg')).read_bytes();expected=signature(original)
                config={'startOnLoad':False,'securityLevel':'strict','secure':rendering.SECURE_KEYS,
                        'htmlLabels':False,'themeCSS':CSS,'fontFamily':'sans-serif','maxTextSize':500000,'maxEdges':10000,
                        'suppressErrorRendering':True,'deterministicIds':True,'deterministicIDSeed':sha(text.encode()),
                        'flowchart':{'htmlLabels':False,'useMaxWidth':False}}
                variants=[('opaque-css-only',opacity_css(original),None)]
                for label,settings in VARIANTS:
                    cfg={**config,'flowchart':{**config['flowchart'],**settings}}
                    rendered=page.evaluate('''async ({id,text,config})=>{
                        mermaid.initialize(config);
                        const result=await Promise.race([mermaid.render(id,text),new Promise((_,reject)=>setTimeout(()=>reject(new Error('bounded render timeout')),30000))]);
                        return {svg:result.svg,securityLevel:mermaid.mermaidAPI.getConfig().securityLevel};
                    }''',{'id':stem,'text':text,'config':cfg})
                    assert rendered['securityLevel']=='strict'
                    variants.append((label,rendering._svg_safe(rendered['svg']),cfg))
                for label,svg,cfg in variants:
                    actual=signature(svg);equal=actual==expected
                    destination=OUT/role/label;destination.mkdir(parents=True)
                    path=destination/(stem+'.svg');path.write_text(svg,encoding='utf-8')
                    capture=static.new_page()
                    try:
                        capture.set_content(rendering._html(svg),wait_until='load')
                        computed=capture.locator('g.edgeLabel rect').evaluate_all('(nodes)=>nodes.map(n=>({opacity:getComputedStyle(n).opacity,fill:getComputedStyle(n).fill}))')
                        png=rendering._capture(capture,capture.locator('svg'))
                    finally:capture.close()
                    image=destination/(stem+'.png');image.write_bytes(png)
                    with Image.open(image) as im:width,height=im.size
                    source_soup=BeautifulSoup(original,'xml');source_dims=[float(source_soup.svg.get('width')),float(source_soup.svg.get('height'))]
                    record={'role':role,'variant':label,'config':cfg,'trustedCss':CSS,
                            'sourceMmd':str(folder/(stem+'.mmd')),'sourceMmdSha256':inputs[str(folder/(stem+'.mmd'))],
                            'sourceSvgSha256':sha(original),'sourceDimensions':source_dims,
                            'svg':str(path),'svgSha256':digest(path),'png':str(image),'pngSha256':digest(image),
                            'dimensions':[width,height],'semanticSvgSignatureEqual':equal,
                            'nodeCount':len(actual['nodes']),'edgeCount':len(actual['edges']),
                            'edgeLabelCount':len(actual['edgeLabels']),'signature':actual,
                            'sourceSignature':expected if not equal else None,
                            'allEdgeLabelBackgroundsOpaque':all(x['opacity']=='1' for x in computed),
                            'labelBackgroundComputed':computed,
                            'geometryExactlyUnchanged':geometry(original)==geometry(svg),
                            'visualReview':'PENDING','actuallyViewed':False}
                    records.append(record)
                    print(json.dumps({'role':role,'variant':label,'dimensions':[width,height],'signatureEqual':equal,'opaque':record['allEdgeLabelBackgroundsOpaque']}),flush=True)
            page.close()
        finally:static.close();script.close();browser.close()
    assert all(digest(path)==expected for path,expected in inputs.items())
    report={'scope':'DERIVED_DIAGRAM_LAYOUT_ONLY','published':False,'originalInputsAndCoreUnchanged':True,
            'mermaidVersion':'12.1.0','bundleSha256':digest(BUNDLE),'inputHashes':inputs,
            'trustedMermaidJavaScriptOnly':True,'inputApplicationExecuted':False,
            'staticPreviewJavaScriptEnabled':False,'allNetworkRequestsAborted':True,'blockedRequests':blocked,
            'officialDocs':[{'url':'https://mermaid.js.org/config/theming.html','scope':'themeCSS/site initialization and label backgrounds'},
                            {'url':'https://mermaid.js.org/config/schema-docs/config-defs-flowchart-diagram-config.html','scope':'spacing/padding/wrappingWidth/minNodeWidth'}],
            'results':records,'businessInterpretationAssessed':False,'formalRubricAssessed':False}
    (OUT/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
