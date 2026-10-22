"""Mechanical views of the sealed SCR-014 Markdown. No business prose authoring."""
import argparse,hashlib,importlib.util,json,re,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
REV=Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent')
W=REV/'.tmp/20261015-scr014-format-02'
sys.dont_write_bytecode=True
sys.path[:0]=[str(REV/'.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src'),str(REV/'.tmp/20261013-rerun-12h/engine-runtime-deps'),str(REV/'.tmp/session-python-deps')]
from contextbase.ai.rendering import render_document
from PIL import Image,ImageChops
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('w',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['render','model']);a=ap.parse_args()
definition=json.loads((W/'jobs/plan/plan-verified.json').read_text('utf8'))['documents'][0]
active=json.loads((W/'active-paths.json').read_text('utf8'))
canonical=definition['path'];draftroot=W/active['draft'];md=draftroot/canonical;render=W/active['render']
if a.stage=='render':
 result=render_document(md,render,mermaid_package=REV/'.tmp/render-tools/node_modules/mermaid',chromium_executable=Path(r'C:/Users/tujin/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'),document_path=canonical,asset_root=draftroot)
 print(json.dumps({k:result[k] for k in ['structure','display','safety']},ensure_ascii=False))
 assert result['structure']['status']=='PASS' and result['display']['status']=='PASS' and not result['safety']['removed']
else:
 manifest=json.loads((render/'manifest.json').read_text('utf8'))
 assert manifest['sourceSha256']==sha(md) and manifest['display']['status']=='PASS'
 helper=REV.parent/'spec-agent/.tmp/20261014-nenkin-high-01/delivery/delivery_model_v2_62_r10.py'
 spec=importlib.util.spec_from_file_location('mechanical_model',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 images=[]
 for kind in ['layouts','diagrams']:
  for item in manifest[kind]:
   p=render/(item['id']+'.png')
   projection={}
   with Image.open(p) as im:
    width,height=im.size
    if kind=='layouts':
     original=p;original_sha=sha(p);rgb=im.convert('RGB');background=rgb.getpixel((0,height-1));difference=ImageChops.difference(rgb,Image.new('RGB',rgb.size,background));box=difference.getbbox()
     if box and box[3]+16<height:
      bottom=box[3]+16
      assert difference.crop((0,bottom,width,height)).getbbox() is None
      asset_dir=W/'projection-assets';asset_dir.mkdir(exist_ok=True);p=asset_dir/(item['id']+'-'+original_sha[:12]+'-content.png')
      if not p.exists():im.crop((0,0,width,bottom)).save(p)
      projection={'originalRaster':str(original),'originalRasterSha256':original_sha,'crop':[0,0,width,bottom],'discardedArea':'uniform bottom background only','allNonBackgroundPixelsRetained':True}
      height=bottom
   images.append({'id':item['id'],'kind':kind[:-1],'sourceLines':item['sourceLines'],'path':str(p),'sha256':sha(p),'width':width,'height':height,**projection})
 entry={'documentId':'SCR-014','canonicalDocumentPath':canonical,'canonicalKind':'basic-design','rawMarkdown':md.read_text('utf8'),'images':images,'markdown':str(md),'markdownSha256':sha(md),'renderDirectory':str(render),'renderPinsSha256':None,'renderManifestSha256':sha(render/'manifest.json')}
 model=m.document_model(entry,preview_max_height=1200)
 # Keep hierarchical ordinals beside their text instead of wrapping alone.
 # Split literal display content only; the Markdown remains authoritative.
 hierarchy_cells=0
 for sheet in model['sheets']:
  if sheet['role']!='normal':continue
  operations=[]
  for op in sheet['operations']:
   match=re.fullmatch(r'(\d+\.\d+\.) (.+)',op['value'],re.S) if op['style']=='body' else None
   if match:
    row=int(re.search(r'\d+',op['range']).group())
    operations.extend([{**op,'range':f'B{row}:D{row}','value':match[1]},{**op,'range':f'E{row}:BJ{row}','value':match[2]}])
    sheet['rowHeights'][str(row)]=max(sheet['rowHeights'].get(str(row),24),m.cell_height(match[2],58*3*13/18))
    hierarchy_cells+=1
   else:operations.append(op)
  sheet['operations']=operations
 model['hierarchicalOrdinalProjection']={'splitRows':hierarchy_cells,'ordinalColumns':'B:D','descriptionColumns':'E:BJ','businessTextChanged':False}
 # Preserve the existing LIST's unframed title row and row-2 table header.
 for sheet in model['sheets']:
  if sheet['role']!='list':continue
  assert sheet['columns']==10 and len(sheet['tables'])==1
  # Keep reference proportions: a narrow ordinal/IO and a wide explanation.
  # Grow the identifier/DB/format columns only where the new detail needs it.
  sheet['columnWidths']=[6,16,22,28,8,32,22.53,20,28,61]
  sheet['rowHeights']={}
  for op in sheet['operations']:
   number=int(re.search(r'\d+',op['range']).group());index=ord(op['range'][0])-ord('A')
   sheet['rowHeights'][str(number)]=max(sheet['rowHeights'].get(str(number),24),m.cell_height(op['value'],max(8,sheet['columnWidths'][index]*13/18)))
  shift=lambda ref:re.sub(r'\d+',lambda v:str(int(v.group())+1),ref)
  for op in sheet['operations']:op['range']=shift(op['range'])
  for table in sheet['tables']:table['range']=shift(table['range']);table['headerRow']+=1
  sheet['rowHeights']={str(int(row)+1):height for row,height in sheet['rowHeights'].items()};sheet['lastRow']+=1
  sheet['operations'].insert(0,{'range':'A1:J1','value':next(d['heading'] for d in model['sourceMetadata']['sheets'] if d['sheet']==sheet['name']),'style':'title','sourceLines':None});sheet['rowHeights']['1']=30
  sheet['printArea']='A1:J'+str(sheet['lastRow'])
  sheet['previewTiles']=[];begin=1;pixels=0
  for row in range(1,sheet['lastRow']+1):
   height=sheet['rowHeights'].get(str(row),15)*4/3
   if row>begin and pixels+height>1200:
    sheet['previewTiles'].append({'range':f'A{begin}:J{row-1}'});begin=row;pixels=0
   pixels+=height
  sheet['previewTiles'].append({'range':f'A{begin}:J{sheet["lastRow"]}'})
  sheet['existingListTitleAndHeaderPreserved']=True
  sheet['geometryProjection']={'kind':'reference-proportions-with-expanded-long-text-columns','widths':sheet['columnWidths'],'sourceValueChanges':False}
 # The original cover is a presentation template, retained literally.
 old=REV/'output/Excel'/Path(canonical).with_suffix('.xlsx')
 ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 with zipfile.ZipFile(old) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   strings=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
  root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
  cells={c.attrib['r']:c for c in root.findall('.//s:sheetData/s:row/s:c',ns)}
  operations=[]
  for merger in root.findall('s:mergeCells/s:mergeCell',ns):
   ref=merger.attrib['ref'];c=cells.get(ref.split(':')[0]);value=''
   if c is not None:
    v=c.find('s:v',ns)
    if c.attrib.get('t')=='s' and v is not None:value=strings[int(v.text)]
    elif c.attrib.get('t')=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
    elif v is not None:value=v.text or ''
   operations.append({'range':ref,'value':value,'style':'cover-title' if ref=='O6:AU9' else 'cover-company-band' if ref=='O36:AU36' else 'cover-cell','sourceLines':None})
  assert len(operations)==14
 model['sheets'][0]['operations']=operations
 binding=json.loads((W/'cover-binding.json').read_text('utf8'))
 from bs4 import BeautifulSoup
 nav=BeautifulSoup(entry['rawMarkdown'],'html.parser').select_one('.app-nav__title')
 assert nav is not None and nav.get_text(strip=True)==binding['value']
 next(op for op in operations if op['range']==binding['range'])['value']=binding['value']
 model['coverBinding']=binding
 model['sheets'][0]['rowHeights']={str(i):18 for i in range(1,37)}
 model['sheets'][0]['previewTiles']=[{'range':'O6:AU36'}]
 model['formatProfile'].pop('referencePins',None)
 model.update(schema='scr014-pilot-view-model/1',businessContentAuthored=False,modelHelperSha256=sha(helper),renderManifestSha256=sha(render/'manifest.json'),sourceManifestSha256=json.loads((REV/'report/20261015-scr014-pilot-01/baseline.json').read_text('utf8'))['capsule']['sha256'])
 save(W/'view-model.json',model)
 print(json.dumps({'model':str(W/'view-model.json'),'sheets':[{k:s[k] for k in ['name','columns','lastRow']} for s in model['sheets']],'images':len(images)},ensure_ascii=False))
