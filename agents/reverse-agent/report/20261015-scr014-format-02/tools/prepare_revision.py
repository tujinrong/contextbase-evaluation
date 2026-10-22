"""Mechanical relocation of citations and AI-declared numbering projection."""
import datetime,difflib,hashlib,json,re,shutil
from pathlib import Path
W=Path(__file__).resolve().parent; REV=W.parents[1];OLD=REV/'.tmp/20261015-scr014-pilot-01';R=REV/'report'/W.name
R.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
oldbase=json.loads((REV/'report/20261015-scr014-pilot-01/baseline.json').read_bytes())
baseline={'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input':inv(REV/'input'),'output':inv(REV/'output'),'qa':inv(REV/'QA'),'capsule':oldbase['capsule'],'scope':'SCR-014 formatting only'}
assert baseline['input']==oldbase['input345']
save(R/'baseline.json',baseline)
canonical='基本設計書/基本設計書_SCR-014_日次 _ 月次処理.md';source=REV/'output/md'/canonical
raw=source.read_text('utf8');save(R/'input-version.json',{'path':str(source),'version':'1.2','sha256':sha(source)})
original=raw.splitlines();out=[];citations=[];headings={}
for number,line in enumerate(original,1):
 if m:=re.match(r'^(#{2,4}) (.+)$',line):
  level=len(m[1]);headings={k:v for k,v in headings.items() if k<level};headings[level]=m[2]
 if line.startswith('根拠：'):
  citations.append({'originalLine':number,'section':' / '.join(headings.values()),'text':line});continue
 out.append(line)
text='\n'.join(out)+'\n';rules=json.loads((W/'hierarchy.json').read_bytes());maps=[]
for rule in rules['groups']:
 start=text.index('### '+rule['section']+'\n');end=text.find('\n### ',start+4)
 if end<0:end=len(text)
 portion=text[start:end];matches=list(re.finditer(r'(?m)^(\d+)\. (.+)$',portion));assert matches
 assert [int(m[1]) for m in matches]==list(range(1,len(matches)+1))
 assert [i for g in rule['groups'] for i in g['steps']]==list(range(1,len(matches)+1))
 replacement=[]
 for parent,g in enumerate(rule['groups'],1):
  replacement.append(f'**{parent}. {g["title"]}**\n')
  for child,old in enumerate(g['steps'],1):
   replacement.append(f'　**{parent}.{child}.** '+matches[old-1][2]+'\n')
   maps.append({'section':rule['section'],'oldNumber':old,'newNumber':f'{parent}.{child}','text':matches[old-1][2]})
 first,last=matches[0].start(),matches[-1].end()
 portion=portion[:first]+'\n'.join(replacement).rstrip()+'\n'+portion[last:]
 text=text[:start]+portion+text[end:]
for correction in rules['referenceCorrections']:
 assert text.count(correction['from'])==1;text=text.replace(correction['from'],correction['to'])
text=text.replace('"version":"1.2"','"version":"1.3"').replace('文書版：1.2','文書版：1.3')
assert '根拠：' not in text
dest=W/'draft'/canonical;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf8')
save(R/'source-evidence.json',{'schema':'scr014-relocated-evidence/1','previousVersion':'1.2','version':'1.3','previousMarkdownSha256':sha(source),'markdownSha256':sha(dest),'citations':citations})
lines=['# SCR-014 仕様記述の根拠','', '文書版1.3。成果物本文から移したソース位置を、節ごとに保持する。原ソースの新規解析ではなく、版1.2で確認済みの根拠の移設である。','']
for i,c in enumerate(citations,1):lines.extend([f'## {i}. {c["section"]}',f'旧MDの{c["originalLine"]}行目。','',c['text'],''])
(R/'根拠一覧.md').write_text('\n'.join(lines),encoding='utf8')
save(R/'numbering-map.json',{'groups':rules,'steps':maps,'originalStepTextPreserved':True,'version':'1.3'})
(R/'format-revision.diff').write_text(''.join(difflib.unified_diff(raw.splitlines(True),text.splitlines(True),'1.2','1.3')),encoding='utf8')
for name in ['prepare_views.py','build_workbook.mjs','export_pdf_html.py','finalize_workbook.py']:
 content=(OLD/name).read_text('utf8').replace('20261015-scr014-pilot-01','20261015-scr014-format-02')
 if name=='prepare_views.py':content=content.replace("REV/'report/20261015-scr014-format-02/baseline.json'","REV/'report/20261015-scr014-pilot-01/baseline.json'")
 (W/name).write_text(content,encoding='utf8')
(W/'jobs/plan').mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/'jobs/plan/plan-verified.json',W/'jobs/plan/plan-verified.json');shutil.copyfile(OLD/'cover-binding.json',W/'cover-binding.json')
save(W/'active-paths.json',{'draft':'draft','render':'render','revision':'1.3'})
print(json.dumps({'version':'1.3','evidenceParagraphsMoved':len(citations),'hierarchicalSteps':len(maps),'groups':len(rules['groups']),'sha256':sha(dest)}))
