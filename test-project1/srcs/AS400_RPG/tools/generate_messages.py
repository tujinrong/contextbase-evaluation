from pathlib import Path
import re,json
B=Path(__file__).resolve().parents[1]
text=(B/'spec/共通/05_チェック・メッセージ設計.md').read_text('utf8')
rows=[];catalog={}
for line in text.splitlines():
 m=re.match(r'\| ([EIW]-[A-Z]+-\d{3}) \|',line)
 if m:
  c=[x.strip() for x in line.strip('|').split('|')]
  rows.append(dict(id=c[0],text=c[1]));catalog[c[0]]=c[1]
assert len(rows)==58,len(rows)
old=json.loads((B/'metadata/messages.json').read_text('utf8'))
# Preserve column layout selected from the full authoritative message grid.
if isinstance(old,list):
 for row in rows:
  prior=next(x for x in old if x.get('id',x.get('messageId'))==row['id'])
  prior_text=prior.get('text',prior.get('message'))
  if prior_text is not None and prior_text!=row['text']:
   # The third column is severity in some source schemas: find the textual template.
   line=next(x for x in text.splitlines() if x.startswith('| '+row['id']+' |'))
   cells=[x.strip() for x in line.strip('|').split('|')]
   row['text']=next((x for x in cells if x==prior_text),cells[2])
s='''dcl-proc StMessage export;
 dcl-pi *n varucs2(320) ccsid(1200);code char(16) const;end-pi;
 dcl-s text varucs2(320) ccsid(1200);select;
'''
for row in rows:s+=f" when code='{row['id']}';text=%ucs2('{row['text'].replace(chr(39),chr(39)*2)}');\n"
s+=" other;text=%ucs2('画面情報が無効です。画面を開き直してください。');endsl;return text;end-proc;\n"
p=B/'src/STUCOMMON.sqlrpgle';src=p.read_text('utf8');a=re.search(r'dcl-proc\s+StMessage\s+export\s*;',src,re.I).start();p.write_text(src[:a]+s,'utf8')
(B/'metadata/messages.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n','utf8')
print('58 message templates regenerated from local spec')
