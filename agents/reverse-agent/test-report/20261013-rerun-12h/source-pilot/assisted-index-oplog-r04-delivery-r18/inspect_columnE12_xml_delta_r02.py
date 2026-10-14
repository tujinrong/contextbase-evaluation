from pathlib import Path
import json, hashlib, zipfile, xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent
OLD=R/'xlsx-r01/Excel/基本設計書/テーブル/05_t_operation_log.xlsx'
NEW=R/'xlsx-oplog-columnE12-r02/Excel/基本設計書/テーブル/05_t_operation_log.xlsx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(OLD) as a, zipfile.ZipFile(NEW) as b:
 assert set(a.namelist())==set(b.namelist())
 differences=[]
 for n in a.namelist():
  if a.read(n)==b.read(n):continue
  x=ET.fromstring(a.read(n));y=ET.fromstring(b.read(n))
  def walk(p,q,path):
   if p.tag!=q.tag or p.text!=q.text or p.tail!=q.tail or len(p)!=len(q):
    differences.append({'part':n,'path':path,'difference':'structureOrText'});return
   for k in sorted(set(p.attrib)|set(q.attrib)):
    if p.get(k)!=q.get(k):differences.append({'part':n,'path':path,'attribute':k,'old':p.get(k),'new':q.get(k)})
   for i,(c,d) in enumerate(zip(p,q)):walk(c,d,path+'/'+c.tag.rsplit('}',1)[-1]+'['+str(i)+']')
  walk(x,y,x.tag.rsplit('}',1)[-1])
 out={'oldSha256':sha(OLD),'newSha256':sha(NEW),'differences':differences}
 target=R/'columnE12-xml-delta-inspection-r02.json';assert not target.exists();target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(out,ensure_ascii=False))
