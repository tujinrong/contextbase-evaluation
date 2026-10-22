"""Mechanical HTML/PDF projection with trusted raster diagrams, no input execution."""
import base64,hashlib,html,json,re,sys,unicodedata
from pathlib import Path
W=Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261015-scr014-pilot-01');REV=W.parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(REV/'.tmp/20261013-rerun-12h/engine-runtime-deps'),str(REV/'.tmp/session-python-deps')]
sys.path.insert(0,str(W/'pdf-deps'))
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
model=json.loads((W/'view-model.json').read_text('utf8'));manifest=json.loads((Path(model['renderDirectory'])/'manifest.json').read_text('utf8'))
raw=Path(model['markdown']).read_bytes();assert hashlib.sha256(raw).hexdigest()==model['markdownSha256']
# Restrict the font cmap to used source characters. This prevents Chromium's
# PDF ToUnicode map selecting unused radical/compatibility aliases of a glyph.
# All text, glyph outlines and the original installed font remain unchanged.
from fontTools.ttLib import TTFont
from fontTools import subset
font_source=Path(r'C:/Windows/Fonts/NotoSansJP-VF.ttf')
font_path=W/('pdf-font-'+model['markdownSha256'][:12]+'.ttf')
if not font_path.exists():
 options=subset.Options();font=TTFont(font_source)
 subsetter=subset.Subsetter(options=options);subsetter.populate(unicodes={ord(c) for c in raw.decode('utf8')}|set(range(32,127)))
 subsetter.subset(font);font.save(font_path);font.close()
font_data=base64.b64encode(font_path.read_bytes()).decode('ascii')
mapping={tuple(im['sourceLines']):im for s in model['sheets'] for im in s['images']}
parser=MarkdownIt('commonmark',{'html':True}).enable('table')
fence_orig=parser.renderer.rules['fence']
def picture(im,diagram=False):
 data=Path(im['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==im['sha256']
 return '<figure class="'+('diagram-page' if diagram else 'screen')+'"><img alt="'+im['id']+'" data-native-width="'+str(im['width'])+'" data-native-height="'+str(im['height'])+'" src="data:image/png;base64,'+base64.b64encode(data).decode('ascii')+'"></figure>'
def fence(tokens,index,options,env):
 t=tokens[index]
 if t.info.strip()!='mermaid':return fence_orig(tokens,index,options,env)
 return picture(mapping[(t.map[0]+1,t.map[1])],True)
def raw_html(tokens,index,options,env):
 t=tokens[index];im=mapping.get((t.map[0]+1,t.map[1]))
 if im:return picture(im)
 if re.fullmatch(r'\s*<!--\s*spec-meta:.*?-->\s*',t.content,re.S):return ''
 return t.content
parser.renderer.rules['fence']=fence;parser.renderer.rules['html_block']=raw_html
body=parser.render(raw.decode('utf8'))
soup=BeautifulSoup(body,'html.parser')
assert not soup.find(['script','iframe','object','embed'])
for a in soup.find_all(True):assert not any(str(k).lower().startswith('on') for k in a.attrs)
def caption_heading(node):
 return node.name in ['h4','h5'] or (node.name=='p' and node.find('strong') is not None and node.get_text(strip=True)==node.find('strong').get_text(strip=True))
for figure in soup.select('figure.diagram-page'):
 # Keep an existing flow heading/explanation on the same page as its figure.
 # The text sequence is unchanged; only a pagination container is introduced.
 prior=[];cursor=figure.previous_sibling
 while cursor is not None:
  if isinstance(cursor,str) and not cursor.strip():cursor=cursor.previous_sibling;continue
  if getattr(cursor,'name',None) not in ['p','h4','h5']:break
  prior.insert(0,cursor)
  if cursor.name=='h4':break
  cursor=cursor.previous_sibling
 if any(caption_heading(x) for x in prior):
  for node in reversed(prior):figure.insert(0,node.extract())
 else:prior=[]
 # Keep immediate explanatory paragraphs/citations with the preceding figure.
 following=[];cursor=figure.next_sibling
 while cursor is not None:
  if isinstance(cursor,str) and not cursor.strip():cursor=cursor.next_sibling;continue
  if getattr(cursor,'name',None)!='p' or caption_heading(cursor):break
  following.append(cursor);cursor=cursor.next_sibling
 for node in following:figure.append(node.extract())
 caption_height=sum(55 if caption_heading(node) else 40+24*((len(node.get_text())+55)//56) for node in prior+following)
 im=figure.find('img')
 if int(im['data-native-height'])+caption_height>1420 or int(im['data-native-width'])>1200:figure['class'].append('large-diagram')
for table in soup.find_all('table'):
 headers=[x.get_text() for x in table.select('thead th')]
 if headers==['No','グループ','項目名','種類','入出力','DB連携項目','候補取得元','必須','形式・桁','説明']:
  table['class']=['item-list'];group=soup.new_tag('colgroup');weights=[3,6,10,12,4,16,10,9,14,22]
  for weight in weights:
   c=soup.new_tag('col');c['style']='width:'+str(100*weight/sum(weights))+'%';group.append(c)
  table.insert(0,group)
  # Markup only: preserve indivisible identifier strings in the item LIST.
  for td in table.select('th,td'):
   for textnode in list(td.find_all(string=True)):
    if textnode.parent.name=='code':continue
    text=str(textnode);parts=[];last=0
    for match in re.finditer(r'[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*',text):
     parts.append(text[last:match.start()]);span=soup.new_tag('span');span['class']='whole-token';span.string=match.group();parts.append(span);last=match.end()
    if parts:parts.append(text[last:]);textnode.replace_with(*parts)
body=str(soup)
style='''
body{font-family:PilotJP,sans-serif;color:#202020;line-height:1.65;margin:26px;font-size:14px}
h1{font-size:28px;border-bottom:3px solid #444;padding-bottom:12px}h2{font-size:23px;border-bottom:2px solid #777;margin-top:36px}h3{font-size:19px;margin-top:30px}h4{font-size:16px;background:#ededed;padding:5px 9px}
p,li{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:12px;font-size:12px}code{font-family:PilotJP,monospace}
table{width:100%;border-collapse:collapse;margin:16px 0;table-layout:auto}th,td{border:1px solid #999;padding:7px;vertical-align:top;overflow-wrap:anywhere;word-break:normal}th{background:#ddd;font-weight:bold}td:last-child{min-width:16em}
table.item-list{table-layout:fixed}table.item-list td:last-child{min-width:0}table.item-list th:first-child,table.item-list td:first-child{white-space:nowrap}table.item-list .whole-token,table.item-list code{white-space:nowrap}
figure{margin:18px 0}img{display:block;max-width:100%;height:auto}figure.diagram-page img{max-width:100%;max-height:none}
@page{size:A3 landscape;margin:15mm 13mm}
@page diagram{size:A3 portrait;margin:15mm 13mm}
@page diagram-large{size:420mm 594mm;margin:15mm 13mm}
@media print{body{margin:0;font-size:11pt;line-height:1.55}h2{break-before:page}h3,h4,h5{break-after:avoid-page}h1{font-size:24pt}table{font-size:9pt;line-height:1.45}thead{display:table-header-group}tr{break-inside:avoid-page}th,td{padding:5px}pre{font-size:9pt}figure{break-inside:avoid-page}figure.diagram-page{page:diagram;margin:0}figure.diagram-page.large-diagram{page:diagram-large}figure.diagram-page img{max-height:none;max-width:100%;width:auto;height:auto}.screen img{max-height:235mm;width:auto}a{color:inherit;text-decoration:none}}
'''
style='@font-face{font-family:PilotJP;src:url(data:font/ttf;base64,'+font_data+');font-weight:100 900;font-style:normal}\n'+style
document='<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; font-src data:; style-src \'unsafe-inline\'; script-src \'none\'; connect-src \'none\'"><title>'+html.escape(model['title'])+'</title><style>'+style+'</style></head><body>'+body+'</body></html>'
out=W/'staged';out.mkdir(exist_ok=True);stem=Path(model['canonicalDocumentPath']).stem
ht=out/(stem+'.html');pdf=out/(stem+'.pdf')
ht.write_text(document,encoding='utf8')
runtime=W/'pdf-browser';runtime.mkdir(exist_ok=True)
with sync_playwright() as p:
 context=p.chromium.launch_persistent_context(str(runtime),executable_path=r'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe',headless=True,java_script_enabled=False,service_workers='block',locale='ja-JP',viewport={'width':1500,'height':1100})
 blocked=[];context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()))
 try:
  page=context.new_page();page.set_content(document,wait_until='load');page.evaluate('document.fonts.ready')
  page.pdf(path=str(pdf),prefer_css_page_size=True,print_background=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:8px;color:#666;width:100%;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
 finally:context.close()
assert not blocked
reader=PdfReader(pdf);extracted='\n'.join(page.extract_text() or '' for page in reader.pages)
(W/'pdf-extracted.txt').write_text(extracted,encoding='utf8')
normalize=lambda t:re.sub(r'\s+','',t)
alltext=normalize(extracted)
missing=[t for t in model['visibleCoverage'] if normalize(t) and normalize(t) not in alltext]
receipt={'schema':'scr014-pdf-html-check/1','markdownSha256':model['markdownSha256'],'html':str(ht),'htmlSha256':hashlib.sha256(ht.read_bytes()).hexdigest(),'pdf':str(pdf),'pdfSha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':len(reader.pages),'textSegmentsChecked':len(model['visibleCoverage']),'textComparisonNormalization':'Whitespace only; literal Unicode preserved through used-character font cmap','fontSourceSha256':hashlib.sha256(font_source.read_bytes()).hexdigest(),'embeddedFontSha256':hashlib.sha256(font_path.read_bytes()).hexdigest(),'missingTextSegments':missing,'rasterImages':len(mapping),'originalApplicationExecuted':False,'inputJavaScriptExecuted':False,'networkRequests':blocked,'visualReview':'PENDING'}
(W/'pdf-html-check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='missingTextSegments'},ensure_ascii=False));print('Missing segments:',len(missing))
assert not missing,'PDF text coverage incomplete; inspect exact missing segments before publication'
