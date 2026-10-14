"""Read-only actual export layout delta diagnostic."""
from pathlib import Path
import json,zipfile
from xml.etree import ElementTree as E
R=Path(__file__).parent;N='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
diff=[]
def compare(a,b,path):
 if a.tag!=b.tag:diff.append([path,'tag',a.tag,b.tag])
 if a.attrib!=b.attrib:diff.append([path,'attrs',a.attrib,b.attrib])
 if a.text!=b.text:diff.append([path,'text-different',len(a.text or ''),len(b.text or '')])
 if a.tail!=b.tail:diff.append([path,'tail-different'])
 if len(a)!=len(b):diff.append([path,'children',len(a),len(b)])
 for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+x.tag.split('}')[-1]+'['+str(i)+']')
for stem in ['01_m_student','04_m_code']:
 with zipfile.ZipFile(R/'xlsx-assisted-tables-r02/Excel/基本設計書/テーブル'/f'{stem}.xlsx') as a,zipfile.ZipFile(R/'xlsx-assisted-tables-r03/Excel/基本設計書/テーブル'/f'{stem}.xlsx') as b:
  x=E.fromstring(a.read('xl/worksheets/sheet1.xml'));y=E.fromstring(b.read('xl/worksheets/sheet1.xml'))
  for t in [x,y]:
   for row in t.findall(f'{N}sheetData/{N}row'):row.attrib.pop('ht',None)
  diff=[];compare(x,y,stem);print(json.dumps({'stem':stem,'diffCount':len(diff),'diff':diff[:20]},ensure_ascii=False))
