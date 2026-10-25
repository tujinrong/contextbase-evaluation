"""Generate native DDS from this method's current fixed-cell panel contracts."""
import sys
sys.dont_write_bytecode = True
from html.parser import HTMLParser
from pathlib import Path
import json,unicodedata

class Panels(HTMLParser):
 def __init__(self):super().__init__();self.panels={};self.panel=None;self.row=0;self.active=False;self.text=''
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'data-panel' in d:
   self.panel=d['data-panel'];self.panels.setdefault(self.panel,dict(rows={},fields=[]))
  if tag=='pre' and self.panel:
   self.row=int(d.get('data-row',1));self.active=True;self.text=''
  if self.active and 'data-dds-name' in d:self.panels[self.panel]['fields'].append(dict(row=self.row,**d))
 def handle_endtag(self,tag):
  if tag=='pre' and self.active:self.panels[self.panel]['rows'][self.row]=self.text;self.active=False
 def handle_data(self,text):
  if self.active:self.text+=text

def generate(base,header,record,field,literal,keyword,aux):
 spec=base.parent.parent/'spec'/base.name
 sources={}
 for name in ['01_学生検索画面.md','02_学生登録画面.md']:
  parser=Panels();parser.feed((spec/'詳細仕様書'/name).read_text('utf8'));sources.update(parser.panels)
 def hidden(name,n=10,typ='A'):
  lines=field(name,n,0,0,'H',typ)
  if typ=='S':lines[0]=lines[0][:35]+'0'+lines[0][36:]
  return lines
 def cursor():
  return [keyword('RTNCSRLOC(&CSRRCD &CSRFLD &CSRPOS)'),keyword('CSRLOC(&CSRROW &CSRCOL)')]+hidden('CSRRCD')+hidden('CSRFLD')+hidden('CSRPOS',4,'S')+hidden('CSRROW',3,'S')+hidden('CSRCOL',3,'S')
 def native(f):
  name=f['data-dds-name'];n=int(f['data-program-bytes']);mode=f['data-mode'];dtype=f['data-dds-type']
  # New student number is editable; ordinary read-only mode is conditional.
  if name=='ESTUNO':mode='B'
  lines=field(name,n,f['row'],int(f['data-col']),mode,dtype,readonly=mode=='B')
  if mode=='B':lines.append(keyword('DSPATR(UL)'))
  if name=='ESTUNO':lines.append(keyword('DSPATR(PR)','76'))
  return lines
 def constants(panel,fields,skip=()):
  lines=[]
  for row,text in panel['rows'].items():
   if row in skip:continue
   cells=[]
   for ch in text:
    width=0 if unicodedata.combining(ch) else 2 if unicodedata.east_asian_width(ch) in 'WF' else 1
    cells.append(ch);cells.extend(['']*(width-1))
   for f in fields:
    if f['row']!=row:continue
    start=int(f['data-col'])-2;end=int(f['data-col'])+int(f['data-width'])
    for i in range(max(0,start),min(len(cells),end)):cells[i]=' '
   i=0
   while i<len(cells):
    if cells[i] in [' ','']:i+=1;continue
    start=i;chunk=''
    while i<len(cells) and cells[i]!=' ':chunk+=cells[i];i+=1
    if chunk:lines.append(literal(chunk,row,start+1))
  return lines
 def extra(name,n,row,col,mode='O',typ='O'):
  return dict(row=row,**{'data-dds-name':name,'data-program-bytes':str(n),'data-width':str(n),'data-mode':mode,'data-dds-type':typ,'data-col':str(col)})
 search=header()+record('COND','OVERLAY')+[literal('学生管理 / 学生検索',1,2)]
 panel=sources['COND_SFLCTL'];rowfields=[f for f in panel['fields'] if f['data-control'].startswith('SFLROW.') and f['row'] in [8,9]]
 search+=record('SFLROW','SFL')
 for f in rowfields:search+=native(f)
 search+=hidden('SROWID',19)
 search+=record('SFLCTL','SFLCTL(SFLROW)','OVERLAY','SFLSIZ(101)','SFLPAG(8)')
 search+=[keyword('SFLDSP','90'),keyword('SFLDSPCTL','91'),keyword('SFLCLR','92'),keyword('SFLCSRRRN(&CSRREL)')]+hidden('CSRREL',5,'S')+cursor()
 sf=[f for f in panel['fields'] if not f['data-control'].startswith('SFLROW.')]
 sf+=[extra('QMSG',128,6,2),extra('DBPAGE',54,5,72),extra('PAGING',100,24,2)]
 for f in sf:search+=native(f)
 search+=constants(panel,sf,skip=range(8,24))
 edit=header()+record('EDSTUDENT')+cursor()
 ef=sources['EDSTUDENT']['fields']+[extra('EMSG1',128,20,2),extra('EMSG2',128,21,2),extra('EMODE',8,2,40),extra('ESTATNAM',30,3,99),extra('EGENDNAM',8,6,86),extra('EPREFNAM',20,7,47),extra('EGRADNAM',26,7,102),extra('ERELNAM',8,12,49)]
 for f in ef:edit+=native(f)
 edit+=constants(sources['EDSTUDENT'],ef)
 # Only one auxiliary record is displayed at a time. Physical buffers are bounded
 # independently of raw Unicode, including complete SI/SO sequences.
 def auxiliaries(lines):
  lines+=record('PICK')+cursor()+field('PTITLE',124,1,2,'O')+field('PMSG',128,21,2,'O')
  for i in range(1,9):
   lines+=field('PSEL'+str(i),1,3+(i-1)*2,2,'B','A')+[keyword('DSPATR(UL)')]
   lines+=field('PVAL'+str(i),124,3+(i-1)*2,6,'O')
  lines+=[literal('Enter=選択1を1件確定 F8=カーソル候補全文',25,2),literal('F12=取消 PageUp/Down=8候補',26,2)]
  lines+=record('LONGTXT')+cursor()+field('LTITLE',124,1,2,'O')+field('LPOS',124,2,2,'O')+field('TEXT',128,5,2,'B','A',True)+[keyword('DSPATR(UL)')]+field('LMSG',128,21,2,'O')
  lines+=[literal('F6=通常/Unicode F10=原入力へ反映 F12=補助取消',25,2),literal('PageUp/Down=文字範囲 Enter=補助内反映・保存しない',26,2)]
  lines+=record('CNFRM')+cursor()+field('CTITLE',124,1,2,'O')+field('DUPCNT',124,2,2,'O')
  lines+=field('DELREAS1',112,3,14,'B','O',True)+[keyword('DSPATR(ND)','74')]+field('DELREAS2',112,4,14,'B','O',True)+[keyword('DSPATR(ND)','74')]
  for i in range(1,9):lines+=field(f'C{i:02d}',124,5+(i-1)*2,2,'O')
  lines+=field('CMSG',128,22,2,'O')+field('CKEYS',128,25,2,'O')+[literal('F12=取消（既定） Enterでは続行しない F8=全文',26,2)]
  return lines
 search=auxiliaries(search);edit=auxiliaries(edit)
 for name,lines in [('STUSCHD',search),('STUEDTD',edit)]:
  (base/'dds'/f'{name}.dspf').write_text('\n'.join(lines)+'\n','utf8')
 # Publish bindings, never copy the specification's example records into source.
 bindings={name:panel['fields'] for name,panel in sources.items()}
 (base/'metadata/text-panels.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n','utf8')
 print('DDS updated: EDSTUDENT + PICK/LONGTXT/CNFRM; exact visible windows and attribute reservations; native compile NOT_RUN')
