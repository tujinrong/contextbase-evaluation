"""Publish only the reviewed pilot and its QA entries, with rollback and scope checks."""
import copy,datetime,hashlib,json,os,shutil
from pathlib import Path
REV=Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent');W=REV/'.tmp/20261015-scr014-pilot-01';R=REV/'report/20261015-scr014-pilot-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,v):
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def inv(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def safe(p,root):
 p=Path(os.path.abspath(p));assert p.is_relative_to(root) and p!=root
 for x in (p,*p.parents):
  if x.exists():assert not x.is_symlink() and not getattr(x.lstat(),'st_file_attributes',0)&0x400
 return p
active=read(W/'active-paths.json')
base=read(R/'baseline.json');model=read(W/'view-model.json');visual=read(W/'visual-review.json');review=read(W/'jobs'/active['reviewJob']/'review-verified.json')
assert review['approved'] is True
assert visual['status']=='PASS' and visual['markdownSha256']==model['markdownSha256']
assert inv(REV/'input')==base['input345']
assert inv(REV/'output')==base['preExistingOutputFiles']
assert inv(REV/'QA')==base['existingQA']
canonical=Path(model['canonicalDocumentPath']);stem=canonical.stem
native=read(W/'workbook-native-check.json');pdf=read(W/'pdf-html-check.json')
assert not pdf['missingTextSegments'] and native['literalCellsChecked']>0
sources={
 'md/'+canonical.as_posix():Path(model['markdown']),
 'html/'+canonical.with_suffix('.html').as_posix():Path(pdf['html']),
 'PDF/'+canonical.with_suffix('.pdf').as_posix():Path(pdf['pdf']),
 'Excel/'+canonical.with_suffix('.xlsx').as_posix():Path(native['path'])}
assert len(sources)==4 and all(p.name.startswith(stem) for p in sources.values())
assert sha(sources['md/'+canonical.as_posix()])==model['markdownSha256']
assert sha(Path(native['path']))==native['sha256'] and sha(Path(pdf['pdf']))==pdf['pdfSha256'] and sha(Path(pdf['html']))==pdf['htmlSha256']
for name,p in sources.items():assert sha(p)==visual['deliveredHashes'][name]
oldqa=read(REV/'QA/questions.json');newqa=copy.deepcopy(oldqa);res=read(W/'pilot-qa-resolution.json')
byid={q['id']:q for q in newqa['questions']};updated=[]
for item in res['resolutions']:
 for identity in item['ids']:
  q=byid[identity]
  # A new human answer/status arriving during this run must not be overwritten.
  assert q.get('answer','')=='' and q.get('status')=='open'
  q['analysisResolution']={'run':'20261015-scr014-pilot-01','basis':'observed-source','adopted':item['adopted'],'references':item['references'],'previousAssumption':q.get('assumption'),'previousStatus':q.get('status'),'applicationExecuted':False,'customerApproval':False}
  q['assumption']=item['adopted'];q['status']=item['status'];q['active']=False;updated.append(identity)
extra=read(W/'additional-qa.json')
for q in extra['questions']:
 assert q['id'] not in byid and q.get('answer','')==''
 newqa['questions'].append(q);byid[q['id']]=q
otherold=[q for q in oldqa['questions'] if q['id'] not in updated]
othernew=[q for q in newqa['questions'] if q['id'] not in updated and q['id'] not in {q['id'] for q in extra['questions']}]
assert otherold==othernew
oldmd=(REV/'QA/仕様確認.md').read_bytes();text=oldmd.decode('utf8');lineending='\r\n' if '\r\n' in text else '\n'
def cell(s):return str(s).replace('|','&#124;').replace('\r','').replace('\n','<br>')
def row(q):
 r=q.get('analysisResolution');e='; '.join(r['references']) if r else q.get('evidence','')
 return '| '+' | '.join(cell(v) for v in [q['id'],q['target'],q['question'],q.get('assumption',''),e,q['impact'],q['status'],q.get('answer','')])+' |'
seen=set();newlines=[]
for line in text.splitlines(keepends=True):
 identity=next((i for i in updated if line.startswith('| '+i+' |')),None)
 if identity:
  seen.add(identity);newlines.append(row(byid[identity])+lineending)
 else:newlines.append(line)
assert seen==set(updated)
if extra['questions']:
 newlines.extend([lineending+'## SCR-014 pilot追加確認（2026-10-15）'+lineending+lineending,
 '| QA ID | 対象 | 質問 | 暫定採用値 | 根拠 | 影響 | 状態 | 回答 |'+lineending,
 '| --- | --- | --- | --- | --- | --- | --- | --- |'+lineending])
 newlines.extend(row(q)+lineending for q in extra['questions'])
qa_new={REV/'QA/questions.json':(json.dumps(newqa,ensure_ascii=False,indent=2)+'\n').encode('utf8'),REV/'QA/仕様確認.md':''.join(newlines).encode('utf8')}
backup=W/'backup';backup.mkdir(exist_ok=False)
targets={safe(REV/'output'/rel,REV/'output'):source.read_bytes() for rel,source in sources.items()}
targets.update(qa_new)
journal={'schema':'scr014-pilot-publication/1','startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED','files':[],'otherSpecificationWritesAuthorized':False}
for target,data in targets.items():
 safe(target,REV);rel=target.relative_to(REV);copyto=backup/rel;copyto.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(target,copyto)
 journal['files'].append({'path':str(target),'backup':str(copyto),'oldSha256':sha(target),'newSha256':hashlib.sha256(data).hexdigest()})
save(R/'publication-before.json',journal);changed=[]
try:
 for target,data in targets.items():
  entry=next(x for x in journal['files'] if x['path']==str(target));assert sha(target)==entry['oldSha256']
  temporary=safe(target.with_name(target.name+'.scr014-pilot-new'),REV)
  with temporary.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  temporary.replace(target);changed.append(target);assert sha(target)==entry['newSha256']
 after=inv(REV/'output');diff={p for p in after if after[p]!=base['preExistingOutputFiles'].get(p)}
 assert set(after)==set(base['preExistingOutputFiles']) and diff==set(sources)
 assert inv(REV/'input')==base['input345']
 check=read(REV/'QA/questions.json');assert [q for q in check['questions'] if q['id'] not in updated and q['id'] not in {q['id'] for q in extra['questions']}]==otherold
 assert all(q.get('answer')==next(o.get('answer') for o in oldqa['questions'] if o['id']==q['id']) for q in check['questions'] if q['id'] in {o['id'] for o in oldqa['questions']})
 journal.update(status='PUBLISHED',finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),changedOutputFiles=sorted(diff),otherOutputFilesUnchanged=len(after)-len(diff),originalInputsUnchanged=len(base['input345']),sourceQAResolved=len(updated),additionalQA=len(extra['questions']),allExistingHumanAnswersPreserved=True,otherQARecordsUnchanged=len(otherold),formal95Percentage=None)
except BaseException as ex:
 for target in reversed(changed):
  entry=next(x for x in journal['files'] if x['path']==str(target))
  assert sha(target)==entry['newSha256'],'Refuse to overwrite intervening work during rollback'
  shutil.copyfile(entry['backup'],target)
 journal.update(status='ROLLED_BACK',error=type(ex).__name__)
 raise
finally:save(R/'publication-result.json',journal)
print(json.dumps({k:v for k,v in journal.items() if k!='files'},ensure_ascii=False))
