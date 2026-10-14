"""Isolated static-display experiment; no source/Markdown/renderer edits."""
from pathlib import Path
import hashlib
import json
import os
from contextbase.ai import rendering

report = Path(__file__).resolve().parents[1]
source = report/'render/search-basic-r07/diagram-013.svg'
destination = report/'render/cluster-label-probe-r02'
if destination.exists():
    raise ValueError('Fresh experiment required')
destination.mkdir()
raw = source.read_text(encoding='utf-8')
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
original_sha = digest(source)
results = []
overlay = '''() => {
 const svg = document.querySelector('svg');
 const labels = [...svg.querySelectorAll('g.cluster-label')];
 const before = labels.map(g => ({text:g.textContent,box:g.getBoundingClientRect().toJSON()}));
 for (const g of labels) {
   const box = g.getBBox();
   const matrix = svg.getCTM().inverse().multiply(g.getCTM());
   const layer = document.createElementNS('http://www.w3.org/2000/svg','g');
   layer.setAttribute('class','trusted-cluster-label-overlay');
   layer.setAttribute('transform',`matrix(${matrix.a},${matrix.b},${matrix.c},${matrix.d},${matrix.e},${matrix.f})`);
   const background = document.createElementNS('http://www.w3.org/2000/svg','rect');
   for (const [key,value] of Object.entries({x:box.x-3,y:box.y-2,width:box.width+6,height:box.height+4})) background.setAttribute(key,String(value));
   background.setAttribute('fill','#ffffff');
   background.setAttribute('data-trusted-label-background','true');
   const copy = g.cloneNode(true);
   copy.removeAttribute('transform');
   layer.append(background,copy);
   g.remove();
   svg.append(layer);
 }
 return {before,after:[...svg.querySelectorAll('g.cluster-label')].map(g=>({text:g.textContent,box:g.getBoundingClientRect().toJSON()})),svg:svg.outerHTML};
}'''
with rendering._playwright_runtime(destination/'runtime') as playwright:
    browser = playwright.chromium.launch(executable_path=os.environ['CONTEXTBASE_CHROMIUM_EXE'],headless=True)
    try:
        for name in ('baseline','stroke-only','overlay'):
            context = browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2400,'height':1800})
            context.route('**/*',lambda route:route.abort())
            page = context.new_page()
            page.set_default_timeout(15000)
            styles = '<style>.cluster-label text{paint-order:stroke;stroke:#ffffff;stroke-width:5px;stroke-linejoin:round}</style>' if name == 'stroke-only' else ''
            page.set_content(rendering._html(raw, styles=styles))
            metadata = None
            if name == 'overlay':
                metadata = page.evaluate(overlay)
                if any(a['text'] != b['text'] or any(abs(a['box'][k]-b['box'][k]) > .001 for k in ('x','y','width','height')) for a,b in zip(metadata['before'],metadata['after'])):
                    raise ValueError('Label text or position changed')
                (destination/'overlay.svg').write_text(metadata.pop('svg'),encoding='utf-8')
            output = destination/(name+'.png')
            output.write_bytes(rendering._capture(page,page.locator('svg')))
            results.append({'case':name,'path':str(output.resolve()),'sha256':digest(output),'metadata':metadata,'actuallyViewed':False})
            context.close()
    finally:
        browser.close()
if digest(source) != original_sha:
    raise ValueError('Original SVG changed')
(destination/'probe.json').write_text(json.dumps({'scope':'TRUSTED_NONSEMANTIC_STATIC_PROBE_ONLY','originalSvg':str(source),'originalSha256':original_sha,'sourceUnchanged':True,'results':results,'applicationExecuted':False,'published':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':3,'sourceUnchanged':True,'destination':str(destination)}))
