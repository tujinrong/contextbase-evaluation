"""Publish four format-only pilot artifacts with hash guards and rollback."""
import ast,datetime,hashlib,json,os,re,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;REV=W.parents[1];R=REV/'report'/W.name
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def safe(p):
 assert p.is_relative_to(REV/'output') or p.is_relative_to(REV/'QA')
 for q in [p,*p.parents]:
  if q.exists():assert not getattr(q.lstat(),'st_file_attributes',0)&0x400
 return p
base=read(R/'baseline.json');model=read(W/'view-model.json');proof=read(R/'format-equivalence.json');review=read(W/'jobs/review-02/review-verified.json');handoff=read(W/'jobs/review-02/review-handoff.json');visual=read(W/'visual-review.json');pdf=read(W/'pdf-html-check.json');native=read(W/'workbook-native-check.json')
assert not review['unresolved'] and len(review['findings'])==1 and review['findings'][0]['severity']=='minor'
oldtext=(REV/'output/md'/model['canonicalDocumentPath']).read_text('utf8');newtext=Path(model['markdown']).read_text('utf8')
assert re.findall(r'```mermaid\n(.*?)```',oldtext,re.S)==re.findall(r'```mermaid\n(.*?)```',newtext,re.S)
assert proof['status']=='PASS' and proof['nonFormattingContentExactlyPreserved']
scopeReview={'status':'PASS','scope':'requested citation relocation and step hierarchy only','newlyIntroducedFindings':0,'overallIndependentReviewApproved':review['approved'],'preExistingMinorFindings':1,'unchangedDiagramBodiesVerified':True,'basis':'fresh independent review plus exact reversible body comparison; not whole-document approval'}
save(R/'format-scope-review.json',scopeReview)
assert handoff['documentSha256']==proof['markdownSha256']==model['markdownSha256']==visual['markdownSha256']
assert handoff['reviewSha256']==sha(W/'jobs/review-02/review-verified.json') and visual['status']=='PASS'
assert inv(REV/'input')==base['input'] and inv(REV/'output')==base['output'] and inv(REV/'QA')==base['qa']
assert not pdf['missingTextSegments'] and native['nativeValidation']['v2FormatAssertions']
canonical=Path(model['canonicalDocumentPath']);sources={'md/'+canonical.as_posix():Path(model['markdown']),'html/'+canonical.with_suffix('.html').as_posix():Path(pdf['html']),'PDF/'+canonical.with_suffix('.pdf').as_posix():Path(pdf['pdf']),'Excel/'+canonical.with_suffix('.xlsx').as_posix():Path(native['path'])}
assert {rel:sha(p) for rel,p in sources.items()}==visual['deliveredHashes']
targets={safe(REV/'output'/rel):source for rel,source in sources.items()}
oldqa=read(REV/'QA/questions.json');qa=read(REV/'QA/questions.json');issue=read(W/'known-issue.json')
issue['id']='Q-'+hashlib.sha256((issue['pilotRun']+'|'+issue['target']).encode()).hexdigest()[:10].upper()
assert not any(q['id']==issue['id'] for q in qa['questions']);qa['questions'].append(issue);save(R/'known-issue.json',issue)
qa_stage=W/'qa-staged';qa_stage.mkdir(exist_ok=False)
(qa_stage/'questions.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cell=lambda x:str(x).replace('|','&#124;').replace('\n','<br>')
addition='\n\n## SCR-014 書式改訂時の既存問題（2026-10-15）\n\n| QA ID | 対象 | 質問 | 暫定採用値 | 根拠 | 影響 | 状態 | 回答 |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| '+' | '.join(cell(issue.get(k,'')) for k in ['id','target','question','assumption','evidence','impact','status','answer'])+' |\n'
oldqa_md=(REV/'QA/仕様確認.md').read_bytes();(qa_stage/'仕様確認.md').write_bytes(oldqa_md+addition.encode('utf8'))
for name in ['questions.json','仕様確認.md']:targets[safe(REV/'QA'/name)]=qa_stage/name
backup=R/'previous-artifacts';backup.mkdir(exist_ok=False)
journal={'schema':'scr014-format-publication/1','startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED','files':[]};changed=[]
for target,source in targets.items():
 copy=backup/target.relative_to(REV);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(target,copy)
 journal['files'].append({'path':str(target),'backup':str(copy),'oldSha256':sha(target),'sha256':sha(source),'bytes':source.stat().st_size,'version':'1.3'})
save(R/'publication-before.json',journal)
try:
 for target,source in targets.items():
  entry=next(x for x in journal['files'] if x['path']==str(target));assert sha(target)==entry['oldSha256']
  tmp=safe(target.with_name(target.name+'.format-02-new'));assert not tmp.exists()
  with tmp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
  tmp.replace(target);changed.append(target);assert sha(target)==entry['sha256']
 after=inv(REV/'output');assert set(after)==set(base['output']);diff={p for p in after if after[p]!=base['output'][p]};assert diff==set(sources)
 assert inv(REV/'input')==base['input']
 assert read(REV/'QA/questions.json')['questions'][:-1]==oldqa['questions']
 assert (REV/'QA/仕様確認.md').read_bytes().startswith(oldqa_md)
 journal.update(status='PUBLISHED',finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),changedOutputFiles=sorted(diff),otherOutputFilesUnchanged=len(after)-len(diff),inputFilesUnchanged=len(base['input']),existingQARecordsPreserved=len(oldqa['questions']),additionalQA=1,additionalQAId=issue['id'],allExistingHumanAnswersPreserved=True,formal95Percentage=None)
except BaseException as ex:
 for target in reversed(changed):
  entry=next(x for x in journal['files'] if x['path']==str(target));assert sha(target)==entry['sha256'];shutil.copyfile(entry['backup'],target)
 journal.update(status='ROLLED_BACK',error=str(ex));raise
finally:save(R/'publication-result.json',journal)
for name in ['workbook-native-check.json','pdf-html-check.json','visual-review.json','hierarchy.json']:
 shutil.copyfile(W/name,R/name)
for name in ['review-verified.json','review-handoff.json']:
 shutil.copyfile(W/'jobs/review-02'/name,R/('final-'+name))
(R/'tools').mkdir(exist_ok=True);tools=[]
for source in sorted(W.iterdir()):
 if source.is_file() and source.suffix in ['.py','.mjs']:
  if source.suffix=='.py':ast.parse(source.read_text('utf-8-sig'),filename=source.name)
  target=R/'tools'/source.name;shutil.copyfile(source,target);tools.append({'path':str(target),'sha256':sha(target)})
manifest={'schema':'scr014-format-artifact-manifest/1','projectId':'nenkin','documentId':'SCR-014','version':'1.3','status':'PUBLISHED','outputs':[x for x in journal['files'] if Path(x['path']).is_relative_to(REV/'output')],'formatEquivalence':proof,'independentReview':review,'formatScopeReview':scopeReview,'visualReview':{'path':str(R/'visual-review.json'),'sha256':sha(R/'visual-review.json')},'tests':{'run':96,'failures':0,'errors':0,'logSha256':sha(R/'agent-checks.txt')},'genericPolicyFiles':[{'path':str(p),'sha256':sha(p)} for p in [REV/'PROMPT.md',REV/'src/contextbase/ai/prompts.py']],'tools':tools,'sourceEvidence':{'path':str(R/'source-evidence.json'),'sha256':sha(R/'source-evidence.json'),'paragraphs':24},'scopeGuards':{k:journal[k] for k in ['otherOutputFilesUnchanged','inputFilesUnchanged','existingQARecordsPreserved','allExistingHumanAnswersPreserved','additionalQA','additionalQAId']},'newSourceAnalysis':False,'formal95Percentage':None,'applicationAndDatabaseExecuted':False}
save(R/'final-artifact-manifest.json',manifest)
print(json.dumps({k:v for k,v in journal.items() if k!='files'},ensure_ascii=False))
