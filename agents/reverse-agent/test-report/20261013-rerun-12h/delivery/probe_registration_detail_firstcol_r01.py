"""CSS-only native viewing projection of immutable reviewed safe renderer HTML."""
from pathlib import Path
import argparse,hashlib,json,sys,os,subprocess,time
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
REPORT=P.parent
CSS='table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th:first-child,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td:first-child{min-width:12em}'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stage(out,name,**details):
 event={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'stage':name,**details}
 with (out/'stages.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(event,ensure_ascii=False)+'\n')
 print(json.dumps(event,ensure_ascii=False),flush=True)
def worker(out):
 assert not out.exists();out.mkdir()
 source=REPORT/'render/assisted-registration-detail-r01-delivery-r19/document.html'
 md=Path('D:/開発/contextbase-evaluation/test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts/revision-registration-detail-r05/詳細仕様書/CSharp_ASPNET/02_学生登録画面.md')
 pins={str(source):'7902b27bf665aaf00633b40eb3ceb29eb3dc689efe79a2b7d21a10a138345813',str(md):'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd',
 str(source.parent/'render-pins.json'):'1684f46d512528883842d65d6fc7ebb464c63062a3649efa639a5f6ea0cdc9e1',
 str(source.parent/'manifest.json'):'edcb4efee50c36f76e2e12e7b62180d68d90b0ba217fe1511a643dbae8c51d9f',str(Path(__file__).resolve()):sha(__file__)}
 assert all(sha(p)==v for p,v in pins.items())
 original=source.read_text(encoding='utf8')
 assert original.startswith('<!doctype html><html ') and '</head>' in original
 projection=original.replace('</head>','<style data-delivery-firstcol-probe="1">'+CSS+'</style></head>',1)
 before=BeautifulSoup(original,'html.parser');after=BeautifulSoup(projection,'html.parser')
 assert str(before.body)==str(after.body)
 assert before.body.get_text()==after.body.get_text()
 assert [str(x) for x in before.find_all('table')]==[str(x) for x in after.find_all('table')]
 assert all(str(a)==str(b) for a,b in zip(before.find_all('img'),after.find_all('img')))
 dest=out/'02_学生登録画面.html';dest.write_text(projection,encoding='utf8')
 (out/'candidate.css').write_text(CSS+'\n',encoding='utf8')
 stage(out,'source-and-body-pins-verified',bodyExact=True,html=str(dest))
 requests=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe',headless=True,timeout=45000)
  try:
   context=browser.new_context(java_script_enabled=False,service_workers='block',locale='ja-JP',accept_downloads=False,viewport={'width':1440,'height':4000},device_scale_factor=1)
   context.route('**/*',lambda route:(requests.append(route.request.url),route.abort()))
   page=context.new_page();page.set_default_timeout(45000)
   page.set_content(projection,wait_until='domcontentloaded',timeout=45000)
   page.evaluate('() => document.fonts.ready.then(() => true)')
   dims=page.evaluate('() => ({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,bodyWidth:document.body.scrollWidth})')
   if dims['width']>1440:raise ValueError('CSS projection exceeds document width: '+repr(dims))
   pages=[]
   for y in range(0,dims['height'],4000):
    height=min(4000,dims['height']-y);target=out/f'document-page-{len(pages)+1:03}.png'
    page.screenshot(path=str(target),clip={'x':0,'y':y,'width':1440,'height':height},timeout=45000)
    pages.append({'path':str(target.resolve()),'sha256':sha(target),'x':0,'y':y,'width':1440,'height':height})
    stage(out,'native-page-captured',page=len(pages),y=y,height=height)
   # Trusted diagnostic only. No original application JavaScript is enabled.
   measurements=page.evaluate('''() => Array.from(document.querySelectorAll('table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) tr')).map(row=>{
     const cell=row.children[0];const rect=cell.getBoundingClientRect();
     return {text:cell.innerText,width:rect.width,height:rect.height,x:rect.x,y:rect.y};
   })''')
  finally:browser.close()
 assert not requests
 assert all(sha(p)==v for p,v in pins.items())
 result={'schema':'reverse-agent-css-only-view-probe/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'DERIVED_NATIVE_GEOMETRY_ONLY','status':'NATIVE_CAPTURED_VISUAL_REVIEW_PENDING',
 'sourceHtml':str(source),'sourceHtmlSha256':pins[str(source)],'projectionHtml':str(dest.resolve()),'projectionHtmlSha256':sha(dest),'css':CSS,'cssSha256':sha(out/'candidate.css'),
 'bodyDomBytesEqual':True,'bodyTextEqual':True,'allTablesEqual':True,'allImageElementsEqual':True,'dimensions':dims,'documentCapture':{'width':1440,'height':dims['height'],'pages':pages},
 'firstColumnMeasurements':measurements,'sourceBindings':pins,'allPinnedBytesUnchanged':True,'javascriptEnabled':False,'networkRequests':requests,
 'mainModified':False,'sourceModified':False,'businessContentAuthored':False,'originalApplicationExecuted':False,'formalApproval':False,'semanticApproval':False,'published':False}
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 stage(out,'complete',result=str(out/'result.json'),sha256=sha(out/'result.json'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args();out=a.output_root.resolve()
 if a.worker:return worker(out)
 assert not out.exists();command=[sys.executable,'-u',str(Path(__file__).resolve()),'--output-root',str(out),'--worker'];proc=subprocess.Popen(command);started=time.monotonic();last=started;size=-1
 try:
  while proc.poll() is None:
   sp=out/'stages.jsonl';current=sp.stat().st_size if sp.exists() else 0
   if current!=size:size=current;last=time.monotonic()
   if time.monotonic()-last>90 or time.monotonic()-started>600:
    subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=20);raise TimeoutError('Owned CSS probe worker timed out')
   time.sleep(.2)
 finally:
  if proc.poll() is None:subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=20)
 if proc.returncode:raise SystemExit(proc.returncode)
if __name__=='__main__':main()
