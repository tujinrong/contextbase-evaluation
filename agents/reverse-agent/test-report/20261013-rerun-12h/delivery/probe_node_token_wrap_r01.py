"""Nonsemantic, bounded trusted Mermaid config probe; no canonical authoring."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,sys,subprocess,os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;REPORT=HERE.parent
RUNTIME=REPORT/'training-assisted/runtime-code-assisted-10.json'
EXPECTED='54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
OUT=HERE/'node-token-wrap-probe-r01'
AGENT=HERE.parents[2]
BUNDLE=AGENT/'.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js'
PRIMARY=BUNDLE.parent/'chunks/mermaid.core/chunk-E2ZNV5FY.mjs'
LABEL_PRIMARY=BUNDLE.parent/'chunks/mermaid.core/chunk-XC4XBNZT.mjs'
INPUT=REPORT/'render/assisted-code-design-r01-delivery-r18/diagram-014.mmd'
SVG=INPUT.with_suffix('.svg')
CHROME='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def rows(svg):
 soup=BeautifulSoup(svg,'xml')
 return [{'id':n['id'],'text':n.get_text(),'rows':[r.get_text() for r in n.select('tspan.text-outer-tspan')]} for n in soup.select('g.node')]
def fragments(records):
 findings=[]
 for n in records:
  concatenated=''.join(n['rows']);ends=[];total=0
  for row in n['rows'][:-1]:total+=len(row);ends.append(total)
  for token in re.finditer(r'[A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*',concatenated):
   if any(token.start()<end<token.end() for end in ends):findings.append({'id':n['id'],'token':token.group(),'rows':n['rows']})
 return findings
def worker():
 assert digest(RUNTIME)==EXPECTED
 receipt=json.loads(RUNTIME.read_text(encoding='utf8'));root=Path(receipt['destination'])
 assert inventory(root)==receipt['files'];sys.path.insert(0,str(root))
 from contextbase.ai import rendering
 assert Path(rendering.__file__).resolve()==(root/'contextbase/ai/rendering.py').resolve()
 paths=[RUNTIME,INPUT,SVG,BUNDLE,PRIMARY,LABEL_PRIMARY,Path(__file__),Path(rendering.__file__)]
 before={str(p):digest(p) for p in paths};OUT.mkdir(exist_ok=False)
 own=INPUT.read_text(encoding='utf8')
 fixtures=[('approved-code014',own),('synthetic-mixed','flowchart TD\n A["検査開始"] --> B["400・422等の捕捉statusまたはModelStateの422を保持<br/>原入力の確認値も保持"]\n B --> C["Identifier1234567890を保持"]\n'),('synthetic-indivisible','flowchart LR\n A["'+'A'*180+'"] --> B["終端"]\n')]
 baseline_original=rows(SVG.read_text(encoding='utf8'));records=[];blocked=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True,timeout=40000)
  script=browser.new_context(java_script_enabled=True,service_workers='block',viewport={'width':2600,'height':1800});static=browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2600,'height':1800})
  def abort(route):blocked.append(route.request.url);route.abort()
  script.route('**/*',abort);static.route('**/*',abort);script.set_default_timeout(25000);static.set_default_timeout(25000)
  try:
   for name,text in fixtures:
    expected=None
    for width in [320,360,400,480,640]:
     page=script.new_page()
     config={'startOnLoad':False,'securityLevel':'strict','secure':rendering.SECURE_KEYS,'htmlLabels':False,'themeCSS':rendering.MERMAID_LABEL_STYLE,'fontFamily':'sans-serif','maxTextSize':500000,'maxEdges':10000,'suppressErrorRendering':True,'deterministicIds':True,'deterministicIDSeed':hashlib.sha256(text.encode()).hexdigest(),'flowchart':{'htmlLabels':False,'useMaxWidth':False,'wrappingWidth':width}}
     try:
      page.set_content(rendering._html('',scripts=True));page.add_script_tag(path=str(BUNDLE))
      result=page.evaluate('''async ({text,config})=>{mermaid.initialize(config);const r=await Promise.race([mermaid.render('nodeprobe',text),new Promise((_,rej)=>setTimeout(()=>rej(new Error('bounded')),25000))]);return {svg:r.svg,config:mermaid.mermaidAPI.getConfig()};}''',{'text':text,'config':config})
     finally:page.close()
     assert result['config']['securityLevel']=='strict'
     svg=rendering._svg_safe(result['svg']);signature=rendering._flowchart_svg_signature(svg)
     if expected is None:expected=signature
     assert signature==expected,'Semantic node/edge/cluster/label signature drift'
     rr=rows(svg);findings=fragments(rr);svgpath=OUT/f'{name}-width{width}.svg';svgpath.write_text(svg,encoding='utf8')
     page=static.new_page()
     try:
      page.set_content(rendering._html(svg),wait_until='load');png=OUT/f'{name}-width{width}.png';png.write_bytes(rendering._capture(page,page.locator('svg')))
      visible=page.locator('g.node tspan.text-outer-tspan').evaluate_all('''ns=>ns.map(n=>({text:n.textContent,bounds:{x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y,width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height},display:getComputedStyle(n).display,visibility:getComputedStyle(n).visibility}))''')
     finally:page.close()
     record={'case':name,'width':width,'nodeRows':rr,'fragmentedWholeTokens':findings,'signatureEqual':True,'svgPath':str(svgpath),'svgSha256':digest(svgpath),'pngPath':str(png),'pngSha256':digest(png),'visibleRows':visible,'actuallyViewed':False};records.append(record)
     print(json.dumps({'case':name,'width':width,'fragments':[f['token'] for f in findings]},ensure_ascii=False),flush=True)
  finally:static.close();script.close();browser.close()
 assert not blocked and all(digest(p)==v for p,v in before.items()) and inventory(root)==receipt['files']
 report={'schema':'node-token-wrap-probe/1','createdUtc':datetime.now(timezone.utc).isoformat(),'sourceBindings':before,'existingApprovedSvgRows':baseline_original,'existingApprovedSvgFragments':fragments(baseline_original),'results':records,'runtimeUnchanged':True,'canonicalEdited':False,'mainEdited':False,'appExecuted':False,'networkBlocked':True,'staticJavaScriptEnabled':False,'primarySources':[{'path':str(PRIMARY),'sha256':digest(PRIMARY),'lines':[578,652],'finding':'createText splits an over-width nonMarkdown word into grapheme chars and creates SVG tspan rows before capture; CSS cannot recombine them'},{'path':str(LABEL_PRIMARY),'sha256':digest(LABEL_PRIMARY),'lines':[192,204],'finding':'node labels pass flowchart wrappingWidth to createText'}],'limits':['Larger width is a measured layout remedy, not a universal whole-token guarantee.','Indivisible over-bound tokens still require a rendering ERROR or author revision.','No production core change or final native approval is made.']}
 (OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':
 if '--worker' in sys.argv:worker()
 else:
  process=subprocess.Popen([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--worker'])
  try:raise SystemExit(process.wait(timeout=180))
  except subprocess.TimeoutExpired:
   subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],check=False);raise SystemExit('Owned probe tree timed out')
