"""Additional trusted fixture-only CSS exploration, without editing r01 output."""
from pathlib import Path
import importlib.util
import json
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('table_css_probe_original',HERE/'run_prototype.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
OUT=HERE/'css-variants-01';OUT.mkdir(exist_ok=False)
variants={
 'hyphens-none':probe.CSS+probe.SELECTOR+' th,'+probe.SELECTOR+' td{hyphens:none}',
 'keep-all':probe.CSS+probe.SELECTOR+' th,'+probe.SELECTOR+' td{word-break:keep-all}',
 'last-min-20em':probe.CSS+probe.SELECTOR+' th:last-child,'+probe.SELECTOR+' td:last-child{min-width:20em}',
 'last-col-40':probe.CSS+probe.SELECTOR+' col:last-child{width:40%!important}',
}
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=str(probe.CHROME),headless=True)
 try:
  context=browser.new_context(java_script_enabled=False,viewport={'width':1440,'height':1000},service_workers='block')
  context.route('**/*',lambda route:route.abort())
  try:
   for name,css in variants.items():
    m=probe.measure(context,probe.baseline,probe.FIXTURE,OUT/name,extra_css=css)
    result={'name':name,'css':css,'width':m['width'],'height':m['height'],
     'brokenTokens':[t['token'] for t in m['tokens'] if not t['singleLine']],
     'overflows':len(m['overflows']),'captureStatus':m['capture']['status'],
     'descriptionWidths':[t['cells'][-1]['box']['width'] for t in m['tables'] if t['parser'] and t['columns'] not in ('1','2')]}
    results.append(result)
  finally:context.close()
 finally:browser.close()
probe.write(OUT/'result.json',{'scope':'SYNTHETIC_ONLY','variants':results,'mainEdited':False,'frozenRuntime':probe.integrity()})
print(json.dumps(results,ensure_ascii=False))
