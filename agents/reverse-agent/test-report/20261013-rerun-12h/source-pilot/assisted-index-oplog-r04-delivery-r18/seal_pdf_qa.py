import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).absolute().parent
def safe(p):
 p=Path(os.path.abspath(p))
 for a in (p,*p.parents):
  if a.is_symlink() or (a.exists() and getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
 return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe(p).read_bytes())
inv=load(HERE/'format-inventory-before.json');log=load(HERE/'pdf-actual-view-log.json')
assert log['actualOwnPages']==list(range(1,50))
for p,d in inv['immutablePins'].items():assert sha(p)==d
for p in inv['pages']:assert sha(p['path'])==p['sha256']
manifest=load(HERE/'pdf-r01/delivery-manifest.json')
docs=[]
for doc in manifest['documents']:
 records=[p for p in inv['pages'] if p['documentId']==doc['documentId']]
 assert len(records)==doc['pages']
 docs.append({'documentId':doc['documentId'],'markdownSha256':doc['markdownSha256'],'pdf':doc['pdf'],'pdfSha256':doc['pdfSha256'],'actualOwnPageViews':len(records),'status':'PASS_WITH_NOTES_GEOMETRY_ONLY','blockingFindings':[],'notes':['Native-size diagram pages and explicit page breaks leave generous whitespace; every page has readable content and page numbering.','Complete ASCII/number tokens remain legible; repeated table headers preserve column continuity across pages.','Narrow Japanese heading/logical-name cells wrap vertically while retaining all characters.'],'pages':[dict(p,actuallyViewedBy='/root/source_pilot',actualViewCompleted=True) for p in records]})
report={'schema':'own-r04-assisted-pdf-native-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),'subject':'training-assisted delivery','status':'PASS_WITH_NOTES_GEOMETRY_ONLY','documents':docs,'actualOwnPageViews':49,'viewLogSha256':sha(HERE/'pdf-actual-view-log.json'),'preViewInventorySha256':sha(HERE/'format-inventory-before.json'),'immutablePins':inv['immutablePins'],'allPinsRecheckedAfterActualViews':True,'textCoverage':'PASS mechanical exporter scope only','inputOrArtifactChanged':0,'originalReferenceRubricExpectedRawAnswerRead':False,'providerOriginalApplicationDatabaseRuns':0,'sourceOnlyBaseline':'CLOSED','semanticApproval':False,'formalApproval':False,'adoptionApproval':False}
p=HERE/'pdf-review.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'pages':49,'reviewSha256':sha(p),'pdfs':[{k:d[k] for k in ['documentId','pdf','pdfSha256']} for d in docs]}))
