"""Offline renderer configuration probe; input Mermaid bytes are never edited."""
from pathlib import Path
import hashlib
import json
import re
import importlib.util
from playwright.sync_api import sync_playwright
from contextbase.ai import rendering

report = Path(__file__).resolve().parents[1]
destination = report/'render'/'mermaid-width-probe-r01'
destination.mkdir(exist_ok=False)
probe_path = report/'delivery'/'probe_mermaid_layout.py'
spec = importlib.util.spec_from_file_location('native_layout_signatures', probe_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
bundle = Path('D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js')
chromium = 'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cases = [ ('assisted-identifier', report/'render'/'assisted-search-basic-r04'/'diagram-002'),
          ('assisted-exception', report/'render'/'assisted-search-basic-r04'/'diagram-006'),
          ('source-numeric', report/'render'/'search-basic-r06'/'diagram-010') ]
before = {str(Path(str(stem)+ext)): digest(Path(str(stem)+ext)) for _, stem in cases for ext in ('.mmd','.svg','.png')}
before[str(Path(rendering.__file__))] = digest(Path(rendering.__file__))
records = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=chromium, headless=True)
    try:
        for role, stem in cases:
            text = Path(str(stem)+'.mmd').read_text(encoding='utf-8')
            expected = helper.signature(Path(str(stem)+'.svg').read_bytes())
            for width in (120,240,320,10000):
                context = browser.new_context(java_script_enabled=True, service_workers='block')
                context.route('**/*', lambda route: route.abort())
                page = context.new_page()
                page.set_content(rendering._html('', scripts=True))
                page.add_script_tag(path=str(bundle))
                config = {'startOnLoad':False, 'securityLevel':'strict', 'secure':rendering.SECURE_KEYS,
                    'htmlLabels':False, 'themeCSS':rendering.MERMAID_LABEL_STYLE,
                    'fontFamily':'sans-serif', 'maxTextSize':500000, 'maxEdges':10000,
                    'suppressErrorRendering':True, 'deterministicIds':True,
                    'deterministicIDSeed': hashlib.sha256(text.encode()).hexdigest(),
                    'flowchart':{'htmlLabels':False,'useMaxWidth':False,'wrappingWidth':width}}
                result = page.evaluate('''async ({text,config})=>{
                    mermaid.initialize(config);
                    const before=JSON.parse(JSON.stringify(mermaid.mermaidAPI.getConfig().flowchart));
                    const result=await mermaid.render('widthprobe',text);
                    return {svg:result.svg, before, after:mermaid.mermaidAPI.getConfig().flowchart};
                }''', {'text':text, 'config':config})
                context.close()
                safe = rendering._svg_safe(result['svg'])
                svg = destination/f'{role}-{width}.svg'
                svg.write_text(safe, encoding='utf-8')
                static = browser.new_context(java_script_enabled=False, service_workers='block',viewport={'width':2400,'height':1800})
                static.route('**/*',lambda route:route.abort())
                capture = static.new_page()
                capture.set_content(rendering._html(safe))
                png = destination/f'{role}-{width}.png'
                png.write_bytes(rendering._capture(capture, capture.locator('svg')))
                rows = capture.locator('g.node').evaluate_all('''nodes=>nodes.map(n=>({
                    text:n.textContent, rows:[...n.querySelectorAll('tspan.text-outer-tspan')].map(t=>t.textContent),
                    bounds:{width:n.getBBox().width,height:n.getBBox().height}}))''')
                dims = capture.locator('svg').bounding_box()
                static.close()
                equal = helper.signature(safe) == expected
                if not equal:
                    raise ValueError('Semantic node/edge/text signature changed')
                record = {'role':role,'requestedWrappingWidth':width,'configurationBefore':result['before'],
                    'configurationAfter':result['after'],'dimensions':dims,'nodes':rows,
                    'semanticSignatureEqual':equal,'svg':str(svg.resolve()),'svgSha256':digest(svg),
                    'png':str(png.resolve()),'pngSha256':digest(png),'actuallyViewed':False}
                records.append(record)
                print(json.dumps({'role':role,'width':width,'effectiveBefore':result['before'].get('wrappingWidth'),
                    'effectiveAfter':result['after'].get('wrappingWidth'),'dimensions':dims,
                    'rows':[n['rows'] for n in rows]},ensure_ascii=False),flush=True)
    finally:
        browser.close()
if any(digest(Path(path)) != expected for path,expected in before.items()):
    raise ValueError('Renderer or original diagram bytes changed')
(destination/'probe.json').write_text(json.dumps({'schema':'trusted-mermaid-width-probe/1',
    'scope':'NONSEMANTIC_CONFIG_EXPERIMENT_ONLY','inputsUnchanged':True,'inputHashes':before,
    'trustedMermaidJavaScriptOnly':True,'originalApplicationExecuted':False,'networkAborted':True,
    'staticJavaScriptEnabled':False,'published':False,'results':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
