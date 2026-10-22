"""Preserve checks and mechanically inventory the delivered pilot."""
import ast, datetime, hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent; REV=W.parent.parent; R=REV/'report/20261015-scr014-pilot-01'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
pub=read(R/'publication-result.json');assert pub['status']=='PUBLISHED'
visual=read(W/'visual-review.json');assert visual['status']=='PASS'
receipts=['visual-review.json','workbook-native-check.json','pdf-html-check.json','pdf-render-receipt.json','pilot-qa-resolution.json','additional-qa.json','diagram-layout-change.json']
checks=[]
for name in receipts:
 source=W/name
 if not source.exists():source=R/name
 target=R/name
 if source!=target:shutil.copyfile(source,target)
 checks.append({'path':str(target),'sha256':sha(target)})
for name in ['review-handoff.json','review-verified.json']:
 target=R/('final-'+name);shutil.copyfile(W/'jobs/review-03'/name,target);checks.append({'path':str(target),'sha256':sha(target)})
helperNames=['build_workbook.mjs','prepare_views.py','export_pdf_html.py','finalize_workbook.py','publish_pilot.py','record_visual_review.py','finalize_report.py']
helpers=[]; (R/'tools').mkdir(exist_ok=True)
for name in helperNames:
 source=W/name
 if name.endswith('.py'):ast.parse(source.read_text(encoding='utf-8-sig'),filename=name)
 target=R/'tools'/name;shutil.copyfile(source,target)
 helpers.append({'executionPath':str(source),'evidenceCopy':str(target),'sha256':sha(source)})
outputs=[]
for rel in pub['changedOutputFiles']:
 f=REV/'output'/rel;assert sha(f)==visual['deliveredHashes'][rel]
 outputs.append({'path':str(f),'outputRelativePath':rel,'version':'1.2','sha256':sha(f),'bytes':f.stat().st_size})
policies=[REV/'PROMPT.md',REV/'src/contextbase/ai/prompts.py']
manifest={'schema':'scr014-final-artifact-manifest/1','finishedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projectId':'nenkin','documentId':'SCR-014','version':'1.2','status':'PUBLISHED','outputs':outputs,'sourceCapsuleManifestSha256':'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445','review':{'approved':True,'findings':0,'formal95Percentage':None},'checks':checks,'agentChecks':read(R/'agent-checks.json'),'genericPolicyFiles':[{'path':str(f),'sha256':sha(f)} for f in policies],'conversionHelpers':helpers,'scopeGuards':{k:pub[k] for k in ['otherOutputFilesUnchanged','originalInputsUnchanged','sourceQAResolved','additionalQA','allExistingHumanAnswersPreserved','otherQARecordsUnchanged']},'qaFiles':[{'path':str(REV/'QA'/n),'sha256':sha(REV/'QA'/n)} for n in ['questions.json','仕様確認.md']],'report':{'path':str(R/'実行報告.md'),'sha256':sha(R/'実行報告.md')},'unassessed':['application runtime','DB execution and production schema','Microsoft Excel application and physical printing','formal original-rubric 95 percent score'],'backup':str(W/'backup')}
save(R/'final-artifact-manifest.json',manifest)
print(json.dumps({'status':manifest['status'],'outputs':len(outputs),'receiptCount':len(checks),'helpersSyntax':'PASS','scopeGuards':manifest['scopeGuards']},ensure_ascii=False))
