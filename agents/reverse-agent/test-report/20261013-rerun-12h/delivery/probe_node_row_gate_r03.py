"""Fresh candidate-only node400 + actual-SVG whole-token/error proof.

Public bundled Mermaid APIs/types parse expected vertices. Canonical bytes,
original MMD and frozen main remain unchanged. No application execution.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,subprocess
from playwright.sync_api import sync_playwright
from node_label_row_gate_r02 import prove_node_rows, NodeLabelProofError, bind_svg_node_ids

HERE=Path(__file__).resolve().parent;REPORT=HERE.parent
RUNTIME=REPORT/'training-assisted/runtime-code-assisted-10.json'
EXPECTED='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
OUT=HERE/'node-token-row-gate-probe-r03'
AGENT=HERE.parents[2]
BUNDLE=AGENT/'.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js'
INPUT=REPORT/'render/assisted-code-design-r01-delivery-r18/diagram-014.mmd'
CHROME='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}

def worker():
 assert digest(RUNTIME)==EXPECTED
 receipt=json.loads(RUNTIME.read_text(encoding='utf8'));root=Path(receipt['destination'])
 assert inventory(root)==receipt['files'];sys.path.insert(0,str(root))
 from contextbase.ai import rendering
 assert Path(rendering.__file__).resolve()==(root/'contextbase/ai/rendering.py').resolve()
 public=[BUNDLE.parent/'mermaidAPI.d.ts',BUNDLE.parent/'diagrams/flowchart/flowDb.d.ts',BUNDLE.parent/'diagrams/flowchart/types.d.ts',BUNDLE.parent/'chunks/mermaid.core/chunk-E2ZNV5FY.mjs',BUNDLE.parent/'chunks/mermaid.core/chunk-XC4XBNZT.mjs']
 paths=[RUNTIME,INPUT,INPUT.with_suffix('.svg'),BUNDLE,Path(__file__),HERE/'node_label_row_gate_r02.py',*public]
 before={str(p):digest(p) for p in paths};OUT.mkdir(exist_ok=False)
 fixtures=[('approved-code014',INPUT.read_text(encoding='utf8')),
           ('synthetic-spaced','flowchart TD\nA["Alpha Beta Gamma Delta"] --> B["日本語400・422のModelStateを保持"]\n'),
           ('synthetic-oversized','flowchart LR\nA["'+'A'*180+'"] --> B["終端"]\n')]
 records=[];blocked=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True,timeout=40000)
  script=browser.new_context(java_script_enabled=True,service_workers='block',viewport={'width':2600,'height':1800})
  static=browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2600,'height':1800})
  def abort(route):blocked.append(route.request.url);route.abort()
  script.route('**/*',abort);static.route('**/*',abort)
  try:
   for name,text in fixtures:
    baseline=None
    for width in [320,400]:
     page=script.new_page();config={'startOnLoad':False,'securityLevel':'strict','secure':rendering.SECURE_KEYS,'htmlLabels':False,'themeCSS':rendering.MERMAID_LABEL_STYLE,'fontFamily':'sans-serif','maxTextSize':500000,'maxEdges':10000,'suppressErrorRendering':True,'deterministicIds':True,'deterministicIDSeed':hashlib.sha256(text.encode()).hexdigest(),'flowchart':{'htmlLabels':False,'useMaxWidth':False,'wrappingWidth':width}}
     try:
      page.set_content(rendering._html('',scripts=True));page.add_script_tag(path=str(BUNDLE))
      result=page.evaluate('''async ({text,config})=>{mermaid.initialize(config);const d=await mermaid.mermaidAPI.getDiagramFromText(text);const vertices=[...d.db.getVertices().values()].map(v=>({id:v.id,domId:v.domId,text:v.text,labelType:v.labelType,icon:v.icon,img:v.img}));const r=await Promise.race([mermaid.render('rowprobe',text),new Promise((_,rej)=>setTimeout(()=>rej(new Error('bounded')),25000))]);return {svg:r.svg,vertices};}''',{'text':text,'config':config})
     finally:page.close()
     svg=rendering._svg_safe(result['svg']);signature=rendering._flowchart_svg_signature(svg)
     if baseline is None:baseline=signature
     assert signature==baseline,'Node/edge/label/cluster semantic signature differs'
     svgpath=OUT/f'{name}-width{width}.svg';svgpath.write_text(svg,encoding='utf8')
     page=static.new_page()
     try:
      page.set_content(rendering._html(svg),wait_until='load')
      measured=page.locator('svg').evaluate('''svg=>{const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};return {canvas:rect(svg),nodes:[...svg.querySelectorAll('g.node')].map(n=>({id:n.id,bounds:rect(n),rows:[...n.querySelectorAll('tspan.text-outer-tspan')].map(r=>({text:r.textContent,bounds:rect(r),display:getComputedStyle(r).display,visibility:getComputedStyle(r).visibility,opacity:getComputedStyle(r).opacity}))}))}}''')
      png=OUT/f'{name}-width{width}.png';png.write_bytes(rendering._capture(page,page.locator('svg')))
     finally:page.close()
     try:proof=prove_node_rows(bind_svg_node_ids(result['vertices'],measured['nodes']),measured['nodes'],measured['canvas']);status='PASS'
     except NodeLabelProofError as exc:proof={'error':str(exc)};status='ERROR_REQUIRES_LAYOUT_OR_AUTHOR_REVISION'
     expected_error=name=='synthetic-oversized' or (name=='approved-code014' and width==320)
     assert (status!='PASS')==expected_error,(name,width,proof)
     record={'case':name,'width':width,'vertices':result['vertices'],'visibleMeasurement':measured,'proof':proof,'status':status,'expectedNegative':expected_error,'semanticSignatureEqual':True,'svgPath':str(svgpath),'svgSha256':digest(svgpath),'pngPath':str(png),'pngSha256':digest(png),'actuallyViewed':False};records.append(record)
     print(json.dumps({'case':name,'width':width,'status':status},ensure_ascii=False),flush=True)
  finally:static.close();script.close();browser.close()
 assert not blocked and all(digest(p)==v for p,v in before.items()) and inventory(root)==receipt['files']
 report={'schema':'node-visible-row-gate-candidate/1','createdUtc':datetime.now(timezone.utc).isoformat(),'sourceBindings':before,'results':records,'runtimeUnchanged':True,'canonicalEdited':False,'originalMmdEdited':False,'mainEdited':False,'appExecuted':False,'networkBlocked':True,'staticJavaScriptEnabled':False,'trustedParserApi':'mermaidAPI.getDiagramFromText + published FlowDB.getVertices','limits':['Candidate technical gates only; no main integration or document approval.','Unsupported literal mappings are ERROR; width400 alone is not a guarantee.','Each production document using a future renderer needs fresh native pixel QA.']}
 (OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
 if '--worker' in sys.argv:worker()
 else:
  process=subprocess.Popen([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--worker'])
  try:raise SystemExit(process.wait(timeout=180))
  except subprocess.TimeoutExpired:
   subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],check=False);raise SystemExit('Owned probe tree timed out')
