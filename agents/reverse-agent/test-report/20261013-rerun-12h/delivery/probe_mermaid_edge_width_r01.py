"""Isolated public Mermaid config experiment; originals and frozen code untouched."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,re
from playwright.sync_api import sync_playwright
from contextbase.ai import rendering
from delivery_model import safe_path
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent;REPO=HERE.parents[4]
OUT=HERE/'mermaid-edge-width-probe-r01'
BUNDLE=REPO/'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid/dist/mermaid.min.js'
CORE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-06/src/contextbase/ai/rendering.py'
CORE_SHA='5202a097b51e2a511b2209c19019f552d43b8eabfac6db0a018ba99d224f7be7'
INPUT=REPORT/'render/assisted-table-index-r01-delivery-r14/diagram-005.mmd'
CHROME='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
def digest(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def main():
 assert safe_path(rendering.__file__)==safe_path(CORE) and digest(CORE)==CORE_SHA
 signature_spec=importlib.util.spec_from_file_location('generic_svg_signature',HERE/'probe_mermaid_layout.py')
 helper=importlib.util.module_from_spec(signature_spec);signature_spec.loader.exec_module(helper)
 OUT.mkdir(exist_ok=False);before={str(p):digest(p) for p in [CORE,INPUT,BUNDLE]}
 own=INPUT.read_text(encoding='utf8')
 synthetic='flowchart TB\n A["開始"] -->|InputValidationException・ArgumentException| B["例外分類"]\n B -->|指定不正のArgumentException| C["終了"]\n'
 cases=[('synthetic',synthetic),('own-index005',own)]
 variants=[('baseline',{},None),('width640',{'flowchart':{'wrappingWidth':640}},None),('spacing200',{'flowchart':{'nodeSpacing':200,'rankSpacing':200}},None),('markdownAutoWrapFalse',{'markdownAutoWrap':False},None),('edgeFont12',{'themeCSS':rendering.MERMAID_LABEL_STYLE+' .edgeLabels text{font-size:12px!important}'},None),('derivedExplicitBreaks',{},'DERIVED_VIEW_ONLY')]
 records=[];blocked=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True,timeout=45000)
  script=browser.new_context(java_script_enabled=True,service_workers='block',viewport={'width':2400,'height':1800});static=browser.new_context(java_script_enabled=False,service_workers='block',viewport={'width':2400,'height':1800})
  def abort(route):blocked.append(route.request.url);route.abort()
  script.route('**/*',abort);static.route('**/*',abort);script.set_default_timeout(20000);static.set_default_timeout(20000)
  try:
   for case,text in cases:
    expected=None
    for name,delta,projection in variants:
     rendered_text=text
     if projection:
      # Fixture-only exact substitutions illustrate nonsemantic display breaks;
      # no generic MMD parser/transformation or production renderer change.
      rendered_text=rendered_text.replace('InputValidationException・ArgumentException','InputValidationException<br/>・ArgumentException').replace('指定不正のArgumentException','指定不正の<br/>ArgumentException')
     config={'startOnLoad':False,'securityLevel':'strict','secure':rendering.SECURE_KEYS,'htmlLabels':False,'themeCSS':rendering.MERMAID_LABEL_STYLE,'fontFamily':'sans-serif','maxTextSize':500000,'maxEdges':10000,'suppressErrorRendering':True,'deterministicIds':True,'deterministicIDSeed':hashlib.sha256(text.encode()).hexdigest(),'flowchart':{'htmlLabels':False,'useMaxWidth':False,'wrappingWidth':320}}
     for key,value in delta.items():
      if key=='flowchart':config[key].update(value)
      else:config[key]=value
     page=script.new_page()
     try:
      page.set_content(rendering._html('',scripts=True));page.add_script_tag(path=str(BUNDLE))
      result=page.evaluate('''async ({text,config})=>{mermaid.initialize(config);const result=await Promise.race([mermaid.render('edgeprobe',text),new Promise((_,reject)=>setTimeout(()=>reject(new Error('bounded render timeout')),30000))]);return {svg:result.svg,config:mermaid.mermaidAPI.getConfig()};}''',{'text':rendered_text,'config':config})
     finally:page.close()
     assert result['config']['securityLevel']=='strict'
     svg=rendering._svg_safe(result['svg']);sig=helper.signature(svg)
     if expected is None:expected=sig
     assert sig==expected,'Exact node/edge/label normalized-text signature drift'
     svg_path=OUT/f'{case}-{name}.svg';svg_path.write_text(svg,encoding='utf8');mmd_path=OUT/f'{case}-{name}.mmd';mmd_path.write_text(rendered_text,encoding='utf8')
     capture=static.new_page()
     try:
      capture.set_content(rendering._html(svg),wait_until='load');png=OUT/f'{case}-{name}.png';png.write_bytes(rendering._capture(capture,capture.locator('svg')))
      geom=capture.locator('g.edgeLabel g.label[data-id]').evaluate_all('''nodes=>nodes.map(n=>({id:n.dataset.id,text:n.textContent,rows:[...n.querySelectorAll('tspan.text-outer-tspan')].map(t=>t.textContent),bounds:{x:n.getBBox().x,y:n.getBBox().y,width:n.getBBox().width,height:n.getBBox().height}}))''')
      nodes=capture.locator('g.node').evaluate_all('''nodes=>nodes.map(n=>({id:n.id,text:n.textContent,rows:[...n.querySelectorAll('tspan.text-outer-tspan')].map(t=>t.textContent)}))''');dimensions=capture.locator('svg').bounding_box()
     finally:capture.close()
     record={'case':case,'variant':name,'config':config,'effectiveFlowchartConfig':result['config']['flowchart'],'dimensions':dimensions,'edgeLabels':geom,'nodes':nodes,'semanticSvgSignatureEqual':True,'svg':str(svg_path),'svgSha256':digest(svg_path),'png':str(png),'pngSha256':digest(png),'derivedMmd':str(mmd_path),'derivedMmdSha256':digest(mmd_path),'authoredSourceMmdChanged':False,'projection':projection,'actuallyViewed':False};records.append(record)
     print(json.dumps({'case':case,'variant':name,'rows':[g['rows'] for g in geom],'signatureEqual':True},ensure_ascii=False),flush=True)
  finally:static.close();script.close();browser.close()
 assert all(digest(p)==v for p,v in before.items()) and not blocked
 report={'schema':'trusted-mermaid-edge-width-probe/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'CONFIG_AND_SYNTHETIC_VIEW_PROJECTION_ONLY','originalsAndFrozenCodeUnchanged':True,'inputHashes':before,'mermaidVersion':'12.1.0','staticJavaScriptEnabled':False,'trustedMermaidJavaScriptOnly':True,'originalApplicationExecuted':False,'networkAborted':True,'mainRendererReadOrEdited':False,'specOrSpecEvalRead':False,'productionProjectionImplemented':False,'published':False,'visualReview':'PENDING','results':records,'primarySources':[{'path':str(BUNDLE.parent/'chunks/mermaid.core/chunk-2BW5OAIV.mjs'),'lines':[320,341],'finding':'edge-label width argument is undefined'},{'path':str(BUNDLE.parent/'chunks/mermaid.core/chunk-E2ZNV5FY.mjs'),'lines':[803,819],'finding':'createText width defaults to200'},{'path':str(BUNDLE.parent/'chunks/mermaid.core/chunk-XC4XBNZT.mjs'),'lines':[192,204],'finding':'node labels pass configured flowchart.wrappingWidth'}],'officialDocs':['https://mermaid.js.org/config/schema-docs/config-defs-flowchart-diagram-config.html','https://mermaid.js.org/config/theming.html']}
 (OUT/'probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
