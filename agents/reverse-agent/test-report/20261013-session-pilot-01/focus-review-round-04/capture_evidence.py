"""Round4 capture of exact actually viewed evidence; no prose generation or external jobs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator
from contextbase.ai import capsule, schemas, workflow

ROOT=Path.cwd().resolve()
REPORT=Path(__file__).resolve().parent
SNAPSHOT=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
JOBS=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04'
OUTPUT=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail'
RUNREPORT=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-round-04'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def write(name,obj): (REPORT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

manifest=capsule.verify(SNAPSHOT)
starting=read(REPORT/'source-pins-before.json')['files']
for f in starting: assert sha(SNAPSHOT/f['path'])==f['sha256'],f['path']
for label in ('source-pins-before.json','source-pins-supplement.json'):
    for f in read(REPORT/'sql-source-audit'/label)['files']:
        assert sha(SNAPSHOT/'sources'/f['path'])==f['sha256'],f['path']
viewed=[Path(p) for p in read(REPORT/'viewed-images.paths.json')]
tiles=[Path(p) for p in read(REPORT/'viewed-tiles.paths.json')]
assert len(set(viewed))==len(viewed)==41
assert len(set(tiles))==len(tiles)==22
all_input_paths=[SNAPSHOT/'manifest.json',JOBS/'runner-source.py',RUNREPORT/'scope.json']+[SNAPSHOT/f['path'] for f in starting]
documents=[]; all_coverage=[]
for stem,jobid,counts in [('student-search','488af9821732c8f6',(3,15,10)),('student-editor','eebb51fa1eb2da8f',(3,20,12))]:
    doc=OUTPUT/(stem+'.md'); job=JOBS/jobid; render_dir=JOBS/'render'/stem
    rendering=read(render_dir/'manifest.json'); draft=read(job/'draft-result.json')
    assert sha(doc)==draft['contentSha256']==rendering['sourceSha256']
    assert Path(rendering['source']).resolve()==doc
    assert rendering['originalModified'] is False
    assert rendering['structure']['status']==rendering['display']['status']=='PASS'
    review_path=REPORT/(stem+'-review.json'); review=read(review_path)
    Draft202012Validator(schemas.REVIEW).validate(review); workflow.references_valid(review,manifest)
    required=[render_dir/(i['id']+'.png') for k in ('layouts','diagrams') for i in rendering[k]]
    required_tiles=[render_dir/i['path'] for i in rendering['display']['documentCapture']['pages']]
    actual=[p for p in viewed if p.parent==render_dir]; actual_tiles=[p for p in tiles if p.parent==render_dir]
    assert set(required)==set(actual) and set(required_tiles)==set(actual_tiles)
    assert (len(rendering['layouts']),len(rendering['diagrams']),len(actual_tiles))==counts
    coverage=[]
    for k in ('layouts','diagrams'):
        for i in rendering[k]:
            p=render_dir/(i['id']+'.png'); assert sha(p)==i['png']['sha256']
            coverage.append(dict(pin(p),category=k,actuallyViewed=True,detail='original',sourceLines=i['sourceLines'],width=i['png']['width'],height=i['png']['height']))
            all_input_paths.append(p)
            if k=='diagrams':
                mmd=render_dir/(i['id']+'.mmd'); assert sha(mmd)==i['sourceSha256']; all_input_paths.append(mmd)
    for i in rendering['display']['documentCapture']['pages']:
        p=render_dir/i['path']; assert sha(p)==i['png']['sha256']
        coverage.append(dict(pin(p),category='complete-vertical-document-tile',actuallyViewed=True,detail='original',sourceRectangle=i['sourceRectangle'],width=i['png']['width'],height=i['png']['height']))
        all_input_paths.append(p)
    all_input_paths.extend([doc,job/'draft-result.json',job/'analysis-handoff.json',job/'analysis-verified.json',job/'analysis/result.json',render_dir/'manifest.json',render_dir/'document.html',review_path])
    all_coverage.extend(coverage)
    documents.append({'documentId':review['documentId'],'document':pin(doc),'draftResult':pin(job/'draft-result.json'),'analysisHandoff':pin(job/'analysis-handoff.json'),'renderManifest':pin(render_dir/'manifest.json'),'generatedHtml':pin(render_dir/'document.html'),'review':pin(review_path),'boundedApproved':review['approved'],'findings':len(review['findings']),'coverage':coverage,'allCurrentLayoutsDiagramsAndWholeDocumentTilesActuallyViewed':True,'structureStatus':rendering['structure']['status'],'displayStatus':rendering['display']['status'],'blockedRequests':rendering['display']['blockedRequests']})

positive_refs=[{'path':p,'startLine':a,'endLine':b} for p,a,b in [
 ('sources/Web/Controllers/StudentsController.cs',23,25),('sources/Web/Controllers/StudentsController.cs',28,38),('sources/Web/Controllers/StudentsController.cs',41,41),('sources/Infrastructure/SearchContextStore.cs',13,14),('sources/Infrastructure/EditorSnapshotStore.cs',7,11),('sources/Infrastructure/WebStudentCoordinator.cs',6,19),('sources/Infrastructure/WebHostSetup.cs',14,24),('sources/Infrastructure/RequestIdentity.cs',7,16),('sources/Views/Students/Edit.cshtml',1,17),('sources/Views/Shared/_Layout.cshtml',1,1),('sources/Views/Shared/_MessagePanel.cshtml',1,3),('sources/wwwroot/css/site.css',1,1),('sources/wwwroot/js/site.js',2,9),('sources/Web/Inputs/StudentSaveInput.cs',34,60),('sources/Core/JapaneseDateService.cs',17,59),('sources/Core/StudentNormalizer.cs',119,168),('sources/Core/SqlServerStudentService.cs',227,329),('sources/Core/SqlServerStudentService.cs',344,416),('sources/database/001_schema.sql',189,201),('sources/Infrastructure/WebPresentation.cs',20,30)]]
workflow.references_valid({'findings':[{'references':positive_refs}]},manifest)
all_input_paths=list(dict.fromkeys(all_input_paths))
before=[pin(p) for p in all_input_paths]
write('inputs-before-final-record.json',{'pins':before})
crosschecks=[
 {'id':'search-pre-sql-waitcancel','result':'CONFIRMED_FIXED','sourceReferences':[{'path':'sources/Infrastructure/SearchContextStore.cs','startLine':14,'endLine':14},{'path':'sources/Web/Controllers/StudentsController.cs','startLine':13,'endLine':16}],'document':'student-search.md','documentLines':[447,470,488,502],'images':['student-search/diagram-006.png'],'notes':'Wait is before acquisition try/operation: no SQL, state/TTL update, or Release for failed acquire; common response attempted, not delivery guarantee.'},
 {'id':'editor-late-context409','result':'REJECTION_FIXED_NORMAL_VALUE_NEW_DEFECT','sourceReferences':[{'path':'sources/Web/Controllers/StudentsController.cs','startLine':25,'endLine':25},{'path':'sources/Infrastructure/SearchContextStore.cs','startLine':13,'endLine':13}],'document':'student-editor.md','documentLines':[271,287,289,317,333,350,352,389],'images':['student-editor/diagram-001.png','student-editor/diagram-003.png'],'notes':'Late rejection retains409 before snapshot; normal nonempty success incorrectly merges into ReturnRevision=NULL in two diagrams; prose retains correct revision.'},
 {'id':'reset-formguard400','result':'CONFIRMED_FIXED','sourceReferences':[{'path':'sources/Web/Controllers/StudentsController.cs','startLine':35,'endLine':35},{'path':'sources/Web/Controllers/StudentsController.cs','startLine':41,'endLine':41}],'document':'student-editor.md','documentLines':[775,792,826],'images':['student-editor/diagram-013.png'],'notes':'Prior filters precede action FormGuard; invalid form400 prevents ID conversion, snapshot get, clear/clone/lookup.'},
 {'id':'date-null-and-catch-boundary','result':'SOURCE_CONSISTENT','sourceReferences':[{'path':'sources/Core/JapaneseDateService.cs','startLine':19,'endLine':24},{'path':'sources/Core/JapaneseDateService.cs','startLine':52,'endLine':59},{'path':'sources/Core/StudentNormalizer.cs','startLine':162,'endLine':168}],'document':'student-editor.md','documentLines':[460,489,980,989,992,1008],'images':['student-editor/diagram-007.png','student-editor/document-011.png'],'notes':'Valid era then numeric null and admission null may cause NRE outside normal input catches; HTTP omission=>null unverified. End null/empty skips parse; blank parses.'},
 {'id':'rendered-tx-classification-table','result':'NEW_DISPLAY_MEANING_DEFECT','sourceReferences':[{'path':'sources/Core/SqlServerStudentService.cs','startLine':319,'endLine':329},{'path':'sources/Core/SqlServerStudentService.cs','startLine':416,'endLine':416}],'document':'student-editor.md','documentLines':[1064,1069],'generatedHtmlLines':[1946,1950],'images':['student-editor/document-011.png'],'notes':'Unescaped || splits inline code in GFM table: condition truncated and result cell empty. Raw MD/source right, rendered classification lost despite PASS.'}
]
result={'schema':'reverse-ai-focus-source-visual-review/1','createdAt':datetime.now(timezone.utc).isoformat(),'projectId':'test-project1','round':4,'snapshot':capsule.verification_state(SNAPSHOT),'referenceMode':'training-assisted','reviewScope':'New raw-source/MD/full-current-static-PNG review; exact coverage, not all dynamic modes or runtime','sourceStartingPins':starting,'sourceStartingPinsVerifiedUnchanged':len(starting),'sourceReadCoverageNotes':'Starting pins are not by themselves read assertions. Current UI/controller/coordinator/date source reads and independent SQL source-only map are recorded separately; no reference design contents or evaluator expectation reads in native review.','sqlSourceAudit':{'map':pin(REPORT/'sql-source-audit/source-map.md'),'beforePins':pin(REPORT/'sql-source-audit/source-pins-before.json'),'supplementPins':pin(REPORT/'sql-source-audit/source-pins-supplement.json'),'preparedBeforeDraft':True,'comparisonPerformedByNativeReviewParent':True},'documents':documents,'actuallyViewedImageCount':len(all_coverage),'actuallyViewedCategoryCounts':{'layouts':6,'diagrams':35,'wholeDocumentTiles':22},'positiveRawReferences':positive_refs,'positiveRawReferencesValid':True,'crossChecks':crosschecks,'formalGrade':None,'limits':{'applicationExecuted':False,'databaseExecuted':False,'binderVerified':False,'allInteractiveModesVerified':False,'narrowViewportViewed':False,'referenceDesignContentsReadForThisNativeReview':False,'formallyEvaluatedByOriginalRubric':False,'evaluatorExpectationsRead':False,'priorApprovalReused':False,'sourceOrGeneratedMdOrProductionEdited':False,'additionalAiOrRenderJobsStarted':False},'inputsPinned':len(before)}
after=[pin(p) for p in all_input_paths]; assert before==after
write('inputs-after-final-record.json',{'pins':after})
write('review-manifest.json',result)
write('validation-result.json',{'reviewsSchemaValid':2,'findingRawReferencesValid':7,'positiveRawReferencesValid':len(positive_refs),'inputsUnchanged':True,'sourceStartingPinsUnchanged':len(starting),'allCurrentLayoutsAndDiagramsActuallyViewed':True,'allCurrentWholeDocumentTilesActuallyViewed':True,'nativeImagesActuallyViewed':len(all_coverage),'inputPins':len(before),'boundedSearchApproved':True,'editorApproved':False,'newEditorMajorFindings':2})
print(json.dumps({'imagesActuallyViewed':len(all_coverage),'inputPins':len(before),'inputsUnchanged':True,'search':'BOUNDED_APPROVED','editor':'2_MAJOR_FINDINGS'},ensure_ascii=False))
