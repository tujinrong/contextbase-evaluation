"""Capture only hashes, exact native viewing coverage and positive source checks."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator
from contextbase.ai import capsule, schemas, workflow

ROOT=Path.cwd().resolve()
REPORT=Path(__file__).resolve().parent
SNAPSHOT=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
JOB=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04/488af9821732c8f6'
RENDER=JOB.parent/'render/student-search'
DOC=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail/student-search.md'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def write(name,obj): (REPORT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

manifest=capsule.verify(SNAPSHOT)
starting=read(REPORT/'source-pins-before.json')['files']
for p in starting: assert sha(SNAPSHOT/p['path'])==p['sha256'],p['path']
render=read(RENDER/'manifest.json')
draft=read(JOB/'draft-result.json')
assert sha(DOC)==draft['contentSha256']==render['sourceSha256']
assert Path(render['source']).resolve()==DOC
assert render['originalModified'] is False
assert render['structure']['status']==render['display']['status']=='PASS'
viewed=[Path(p) for p in read(REPORT/'viewed-images.paths.json') if '/student-search/' in p]
tiles=[Path(p) for p in read(REPORT/'viewed-tiles.paths.json') if '/student-search/' in p]
required=[RENDER/(x['id']+'.png') for k in ('layouts','diagrams') for x in render[k]]
required_tiles=[RENDER/x['path'] for x in render['display']['documentCapture']['pages']]
assert set(viewed)==set(required) and len(viewed)==18
assert set(tiles)==set(required_tiles) and len(tiles)==10
coverage=[]
for kind in ('layouts','diagrams'):
    for item in render[kind]:
        path=RENDER/(item['id']+'.png'); assert sha(path)==item['png']['sha256']
        coverage.append(dict(pin(path),category=kind,actuallyViewed=True,detail='original',sourceLines=item['sourceLines'],width=item['png']['width'],height=item['png']['height']))
for item in render['display']['documentCapture']['pages']:
    path=RENDER/item['path']; assert sha(path)==item['png']['sha256']
    coverage.append(dict(pin(path),category='complete-vertical-document-tile',actuallyViewed=True,detail='original',sourceRectangle=item['sourceRectangle'],width=item['png']['width'],height=item['png']['height']))
review_path=REPORT/'student-search-review.json'
review=read(review_path); Draft202012Validator(schemas.REVIEW).validate(review)
refs=[{'path':p,'startLine':a,'endLine':b} for p,a,b in [
 ('sources/Infrastructure/SearchContextStore.cs',13,14),('sources/Web/Controllers/StudentsController.cs',13,22),('sources/Infrastructure/WebStudentCoordinator.cs',7,17),('sources/Infrastructure/WebHostSetup.cs',22,24),
 ('sources/Views/Students/Search.cshtml',4,8),('sources/Views/Shared/_Layout.cshtml',1,1),('sources/wwwroot/css/site.css',1,1),('sources/Web/Inputs/StudentSearchInput.cs',7,22),('sources/Core/StudentNormalizer.cs',47,70),('sources/Core/SqlServerStudentService.cs',103,171),('sources/database/001_schema.sql',9,13),('sources/Core/SqlServerStudentService.cs',196,216),('sources/Infrastructure/EditorSnapshotStore.cs',7,11),('sources/Infrastructure/FlashMessageStore.cs',6,9),('sources/Infrastructure/WebPresentation.cs',20,23)]]
workflow.references_valid({'findings':[{'references':refs}]},manifest)
inputs=[DOC,JOB/'draft-result.json',JOB/'analysis-handoff.json',JOB/'analysis-verified.json',JOB/'analysis/result.json',RENDER/'manifest.json',review_path,JOB.parent/'runner-source.py']
before=[pin(p) for p in inputs]+[pin(SNAPSHOT/p['path']) for p in starting]
write('student-search-inputs-before.json',{'pins':before})
result={'schema':'reverse-ai-focus-source-visual-review/1','capturedAt':datetime.now(timezone.utc).isoformat(),'projectId':'test-project1','round':4,'snapshot':capsule.verification_state(SNAPSHOT),'referenceMode':'training-assisted','reviewScope':'Raw source + current search MD + exactly listed actually viewed PNGs','document':pin(DOC),'draftResult':pin(JOB/'draft-result.json'),'renderManifest':pin(RENDER/'manifest.json'),'review':pin(review_path),'sourceStartingPinsVerifiedUnchanged':len(starting),'allSearchLayoutsViewed':True,'allSearchDiagramsViewed':True,'allSearchWholeDocumentTilesViewed':True,'coverage':coverage,'positiveRawReferences':refs,'positiveRawReferencesValidated':True,'crossChecks':[{'id':'pre-sql-wait-cancel','documentLines':[447,470,488,502],'diagram':'diagram-006','result':'CONFIRMED_FIXED','claim':'WaitAsync before try/operation can cancel before SQL; no acquired-gate Release/state/TTL update; WebFault-only action catch bypassed; common delivery is attempted, not guaranteed.'},{'id':'page-original-webfault-status','documentLines':[579,626],'diagram':'diagram-008','result':'PRESERVED','claim':'403/409/422 e.Status preserved in local redisplay; late reconstruction failures route separately.'},{'id':'state-snapshot-and-sql-boundaries','documentLines':[228,232,254,389,946,952],'diagrams':['diagram-002','diagram-003','diagram-004','diagram-015'],'result':'CONSISTENT_WITH_READ_SOURCE','claim':'Search/lookup snapshots distinct; Web memory state not runtime_state table; JOIN not physical FK; Saved+audit commit precedes303 and does not guarantee resumed delivery.'}],'limits':{'applicationExecuted':False,'databaseExecuted':False,'binderVerified':False,'allInteractiveModesVerified':False,'narrowViewportViewed':False,'referenceDesignContentsReadForThisNativeReview':False,'formallyEvaluatedByOriginalRubric':False,'evaluatorExpectationsRead':False,'priorApprovalReused':False,'productionEdited':False}}
after=[pin(p) for p in inputs]+[pin(SNAPSHOT/p['path']) for p in starting]
assert before==after
write('student-search-inputs-after.json',{'pins':after})
write('student-search-evidence.json',result)
write('student-search-validation.json',{'reviewSchemaValid':True,'positiveRawReferencesValid':len(refs),'inputsUnchanged':True,'nativeImagesActuallyViewed':len(coverage),'newFindings':len(review['findings']),'boundedApproval':review['approved']})
print(json.dumps({'nativeImagesActuallyViewed':len(coverage),'positiveRawReferencesValid':len(refs),'inputsUnchanged':True}))
