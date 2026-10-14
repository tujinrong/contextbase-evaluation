"""Synthetic static SVG measurements only; never a business input/provider."""
from pathlib import Path
import hashlib,json,sys,subprocess
from playwright.sync_api import sync_playwright
from node_label_row_gate_r05 import prove_node_rows, NodeLabelProofError
HERE=Path(__file__).resolve().parent
OUT=HERE/'node-effective-fill-probe-r06.json'
MEASURE=HERE/'measure_node_rows_r06.js'
CHROME='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worker():
 assert not OUT.exists();before={str(p):digest(p) for p in [Path(__file__),MEASURE,HERE/'node_label_row_gate_r05.py']};records=[];blocked=[]
 cases=[('fill-transparent','','fill:transparent',True),('fill-rgba-alpha-zero','','fill:rgba(17,34,51,0)',True),('fill-rgba-partial','','fill:rgba(17,34,51,0.4)',False)]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True,timeout=30000)
  context=browser.new_context(java_script_enabled=False,service_workers='block')
  def abort(route):blocked.append(route.request.url);route.abort()
  context.route('**/*',abort)
  try:
   for name,parent_style,row_style,expected_error in cases:
    page=context.new_page()
    try:
     page.set_content(f'<html><body><svg xmlns="http://www.w3.org/2000/svg" width="400" height="100"><g class="node" id="p-flowchart-A-0" style="{parent_style}"><rect x="1" y="1" width="300" height="80" fill="white"/><text x="20" y="30"><tspan class="text-outer-tspan" style="{row_style}">Identifier422</tspan></text></g></svg></body></html>')
     measured=page.locator('svg').evaluate(MEASURE.read_text(encoding='utf8'))
    finally:page.close()
    try:proof=prove_node_rows([{'id':'A','domId':'p-flowchart-A-0','text':'Identifier422','labelType':'text'}],measured['nodes'],measured['canvas']);status='PASS'
    except NodeLabelProofError as exc:proof={'error':str(exc)};status='ERROR'
    assert (status=='ERROR')==expected_error,(name,status,proof)
    records.append({'case':name,'expectedError':expected_error,'status':status,'measurement':measured,'proof':proof})
  finally:context.close();browser.close()
 assert not blocked and all(digest(Path(p))==value for p,value in before.items())
 OUT.write_text(json.dumps({'schema':'synthetic-node-effective-visibility/1','sourceBindings':before,'cases':records,'passed':len(records),'providerCalls':0,'productionInputsRead':False,'networkCalls':0,'staticJavaScriptEnabled':False,'mainEdited':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'passed':len(records),'report':str(OUT),'sha256':digest(OUT)}))
if __name__=='__main__':
 if '--worker' in sys.argv:worker()
 else:
  process=subprocess.Popen([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--worker'])
  try:raise SystemExit(process.wait(timeout=60))
  except subprocess.TimeoutExpired:subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],check=False);raise SystemExit('Owned synthetic probe tree timeout')
