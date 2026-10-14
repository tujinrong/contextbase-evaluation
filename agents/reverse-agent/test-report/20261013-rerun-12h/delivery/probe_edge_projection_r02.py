"""Bounded offline public Mermaid rendering of generic insertion-only prototype."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,html,importlib.util,subprocess,sys,time
from collections import Counter
from playwright.sync_api import sync_playwright
from contextbase.ai import rendering
from delivery_model import safe_path
from edge_label_projection_r01 import project_flowchart_edges,reverse_projection,label_tokens,validate_visible_rows,IndivisibleTokenError
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent;REPO=HERE.parents[4]
OUT=HERE/'mermaid-edge-projection-r02'
BUNDLE=REPO/'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js'
CORE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-06/src/contextbase/ai/rendering.py'
CORE_SHA='5202a097b51e2a511b2209c19019f552d43b8eabfac6db0a018ba99d224f7be7'
CHROME='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
def digest(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def visible(text):
 text=re.sub(r'<br\s*/?\s*>',' ',text,flags=re.I)
 text=re.sub(r'#(\d+);',lambda m:chr(int(m[1])),text)
 text=re.sub(r'#([A-Za-z]+);',lambda m:html.unescape('&'+m[1]+';'),text)
 return html.unescape(text)
def normalize(text):return ''.join(text.split())
def worker():
 assert safe_path(rendering.__file__)==safe_path(CORE) and digest(CORE)==CORE_SHA
 spec=importlib.util.spec_from_file_location('generic_signature',HERE/'probe_mermaid_layout.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 OUT.mkdir(exist_ok=False)
 cases=[
  ('synthetic-pipe','flowchart TB\n A["nodeArgumentException -->|unchanged| B"] -->|InputValidationException・ArgumentException| B["終了"]\n B -->|数10001件| C["終了"]\n',False),
  ('synthetic-long','graph LR\n A -- 条件InputValidationException又はArgumentException --> B\n B -- "数10001件 | text --> literal" --> C\n',False),
  ('synthetic-quoted-pipe','flowchart TB\n A -->|"条件ArgumentException | text-->literal"| B\n',False),
  ('synthetic-entities','flowchart TB\n A -->|"条件ArgumentException#quot;#124;#quot;10001件"| B\n',False),
  ('synthetic-authored-breaks','flowchart TB\n A -->|"条件<br/>ArgumentException<br/>数10001件"| B\n',False),
  ('synthetic-nested-metadata','---\ntitle: "flowchart metadata ArgumentException"\n---\n%%{init: {"flowchart": {"wrappingWidth":320}}}%%\n%% A -->|条件ErrorCode| X\nflowchart TB\nsubgraph SG["titleArgumentException -->|ignored| X"]\n A(["nodeArgumentException -->|ignored| X"]) -->|条件ErrorCode| B[("nodeErrorCode")]\nend\n',False),
  ('synthetic-oversized','flowchart TB\n A -->|条件'+('OversizedIndivisibleIdentifier'*4)+'| B\n',True),
 ]
 paths=[CORE,BUNDLE,HERE/'edge_label_projection_r01.py',HERE/'test_edge_label_projection_r01.py',HERE/'probe_edge_projection_r02.py']
 ownroot=REPORT/'render/assisted-table-index-r01-delivery-r14'
 for n in [5,8,11]:
  source=ownroot/f'diagram-{n:03d}.mmd';paths.extend([source,source.with_suffix('.svg'),source.with_suffix('.png')]);cases.append((f'own-index{n:03d}',source.read_text(encoding='utf8'),False))
 primaries=[('chunk-2BW5OAIV.mjs',[320,341]),('chunk-E2ZNV5FY.mjs',[587,632]),('chunk-E2ZNV5FY.mjs',[738,819]),('chunk-XC4XBNZT.mjs',[192,204])]
 paths.extend(BUNDLE.parent/'chunks/mermaid.core'/p for p,_ in primaries)
 before={str(p):digest(p) for p in paths};records=[];attempts=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True,timeout=45000)
  trusted=browser.new_context(java_script_enabled=True,service_workers='block',viewport={'width':2400,'height':1800})
  static=browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2400,'height':1800})
  def abort(route):attempts.append(route.request.url);route.abort()
  trusted.route('**/*',abort);static.route('**/*',abort);trusted.set_default_timeout(20000);static.set_default_timeout(20000)
  try:
   for name,source,expectedfail in cases:
    p=project_flowchart_edges(source);assert reverse_projection(p)==source
    assert project_flowchart_edges(p.text).text==p.text and not project_flowchart_edges(p.text).insertions
    directory=OUT/name;directory.mkdir();(directory/'projection-receipt.json').write_text(json.dumps(p.receipt(),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    config={'startOnLoad':False,'securityLevel':'strict','secure':rendering.SECURE_KEYS,'htmlLabels':False,'themeCSS':rendering.MERMAID_LABEL_STYLE,'fontFamily':'sans-serif','maxTextSize':500000,'maxEdges':10000,'suppressErrorRendering':True,'deterministicIds':True,'deterministicIDSeed':hashlib.sha256(source.encode()).hexdigest(),'flowchart':{'htmlLabels':False,'useMaxWidth':False,'wrappingWidth':320}}
    expected=None;variantrecords=[]
    for variant,mmd in [('baseline',source),('projection',p.text)]:
     page=trusted.new_page()
     try:
      page.set_content(rendering._html('',scripts=True));page.add_script_tag(path=str(BUNDLE))
      result=page.evaluate('''async ({text,config})=>{mermaid.initialize(config);const result=await Promise.race([mermaid.render('edgeprojection',text),new Promise((_,reject)=>setTimeout(()=>reject(new Error('bounded render timeout')),30000))]);return {svg:result.svg,security:mermaid.mermaidAPI.getConfig().securityLevel};}''',{'text':mmd,'config':config})
      assert result['security']=='strict'
     finally:page.close()
     svg=rendering._svg_safe(result['svg']);signature=helper.signature(svg)
     if expected is None:expected=signature
     (directory/(variant+'-signature.json')).write_text(json.dumps(signature,ensure_ascii=False,indent=2),encoding='utf8')
     if signature!=expected:
      (directory/(variant+'-failure.svg')).write_text(svg,encoding='utf8')
      (directory/(variant+'-failure.mmd')).write_text(mmd,encoding='utf8')
     assert signature==expected,'Node/edge/label semantic signature changed'
     svgp=directory/(variant+'.svg');svgp.write_text(svg,encoding='utf8');mmdp=directory/(variant+'.mmd');mmdp.write_text(mmd,encoding='utf8')
     capture=static.new_page()
     try:
      capture.set_content(rendering._html(svg),wait_until='load');png=directory/(variant+'.png');png.write_bytes(rendering._capture(capture,capture.locator('svg')))
      rows=capture.locator('g.edgeLabel g.label[data-id]').evaluate_all('''nodes=>nodes.map(n=>({id:n.dataset.id,text:n.textContent,rows:[...n.querySelectorAll('tspan.text-outer-tspan')].map(t=>t.textContent),bounds:{x:n.getBBox().x,y:n.getBBox().y,width:n.getBBox().width,height:n.getBBox().height}}))''');dims=capture.locator('svg').bounding_box()
     finally:capture.close()
     validation=[]
     if variant=='projection':
      for label in p.labels:
       if label.markdown:continue
       raw=source[label.contentStart:label.contentEnd];plain=visible(raw);tokens=label_tokens(source,label);matches=[r for r in rows if normalize(r['text'])==normalize(plain)]
       assert matches,'Parsed source label not matched to actual SVG: '+raw
       for row in matches:
        error=None
        try:validate_visible_rows(tokens,row['rows'])
        except IndivisibleTokenError as exc:error=str(exc)
        validation.append({'labelSourceRange':[label.contentStart,label.contentEnd],'originalLiteral':raw,'tokens':tokens,'edgeId':row['id'],'rows':row['rows'],'status':'REQUIRES_AUTHOR_CHANGE' if error else 'PASS_WHOLE_TOKENS','error':error})
      errors=[x for x in validation if x['error']];assert bool(errors)==expectedfail,(name,errors)
     variantrecords.append({'variant':variant,'mmd':str(mmdp),'mmdSha256':digest(mmdp),'svg':str(svgp),'svgSha256':digest(svgp),'png':str(png),'pngSha256':digest(png),'dimensions':dims,'edgeLabels':rows,'semanticSvgSignatureEqual':True,'visibleTokenValidation':validation,'actuallyViewed':False})
    records.append({'case':name,'expectedOversizedTokenFailure':expectedfail,'insertions':len(p.insertions),'insertOnlyReversible':True,'idempotent':True,'results':variantrecords});print(json.dumps({'case':name,'insertions':len(p.insertions),'signatureEqual':True,'expectedOversizedFailure':expectedfail},ensure_ascii=False),flush=True)
  finally:static.close();trusted.close();browser.close()
 assert all(digest(p)==s for p,s in before.items()) and not attempts
 report={'schema':'trusted-mermaid-edge-projection-probe/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'MECHANICAL_PROTOTYPE_PASS_NATIVE_REVIEW_PENDING','mermaidVersion':'12.1.0','frozenRendererSha256':CORE_SHA,'configScope':'unchanged trusted r14 config320; only insertion-only temporary derived MMD layout','primarySources':[{'path':str(BUNDLE.parent/'chunks/mermaid.core'/p),'sha256':digest(BUNDLE.parent/'chunks/mermaid.core'/p),'lines':lines} for p,lines in primaries],'beforeAfterHashes':before,'allInputsUnchanged':True,'networkAttempts':attempts,'trustedMermaidJavaScriptOnly':True,'staticJavaScriptEnabled':False,'canonicalMarkdownChanged':False,'coreRendererEdited':False,'sourceSpecEvaluatorOrOtherModeRead':False,'providerInvoked':False,'productionIntegration':False,'published':False,'results':records,'limits':['Conservative flowchart lexer supports plain pipe and solid -- text --> label forms; Markdown labels are left unchanged.','A rendered edge label must match its original source span and fit whole identifiers in actual SVG rows; oversized indivisible identifiers require author change.','Native image review and root integration are separate required gates.']}
 (OUT/'probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
 if '--worker' in sys.argv:return worker()
 stdout=HERE/'edge-projection-r02-stage.log';stderr=HERE/'edge-projection-r02-stderr.log';start=time.monotonic()
 with stdout.open('xb') as out,stderr.open('xb') as err:
  child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=out,stderr=err)
  try:code=child.wait(timeout=180)
  except subprocess.TimeoutExpired:
   subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20);child.wait(timeout=10);code=-1
 result={'ownedWorkerPid':child.pid,'exitCode':code,'timeoutSeconds':180,'elapsedSeconds':round(time.monotonic()-start,3)}
 (HERE/'edge-projection-r02-worker.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result));return code
if __name__=='__main__':sys.exit(main() or 0)
