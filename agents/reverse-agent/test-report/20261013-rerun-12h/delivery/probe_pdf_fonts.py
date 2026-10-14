"""Small trusted-font glyph extraction probe; no input application execution."""
from pathlib import Path
import json,io,html
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
root=Path(__file__).parent/'pdf-font-probe-r03';root.mkdir()
model=json.loads((Path(__file__).parent/'model-search-basic-r02.json').read_bytes())
text=model['documents'][0]['title']+'\n'+ '01～04 Staff specification 入力 生年月日 文 面 行 用 ：'
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe',headless=True,timeout=30000)
 context=browser.new_context(java_script_enabled=False,service_workers='block');context.route('**/*',lambda route:route.abort())
 for font in ['Meiryo','Yu Gothic','MS Gothic','MS Mincho','Arial']:
  page=context.new_page();page.set_content('<html><head><meta charset="UTF-8"><style>body{font-family:"'+font+'";font-size:14pt;white-space:pre; font-variant-ligatures:none}</style></head><body>'+html.escape(text)+'</body></html>',wait_until='domcontentloaded',timeout=30000)
  data=page.pdf();(root/(font.replace(' ','-')+'.pdf')).write_bytes(data)
  extracted=''.join(p.extract_text() for p in PdfReader(io.BytesIO(data)).pages)
  results.append({'font':font,'expected':text,'actual':extracted,'strictEqual':text.strip()==extracted.strip()});page.close()
 context.close();browser.close()
(root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(results,ensure_ascii=True))
