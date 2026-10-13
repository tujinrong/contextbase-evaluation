"""Verify audit metadata and hashes only; no source application or AI/render execution."""
import hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator
from bs4 import BeautifulSoup

ROOT = Path.cwd().resolve()
REPORT = Path(__file__).resolve().parent
JOBS = ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-05'
CAPSULE = ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
RUNTIME = JOBS/'runtime-code/contextbase/ai'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path, value):
    with path.open('x', encoding='utf-8') as file:
        json.dump(value, file, ensure_ascii=False, indent=2); file.write('\n')
def local(relative):
    path=(ROOT/relative).resolve(); assert path.is_relative_to(ROOT); return path
def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
schema=load_module('round5_frozen_schema',RUNTIME/'schemas.py')
validation=load_module('round5_frozen_validation',RUNTIME/'validation.py')
viewed=read(REPORT/'viewed-images.json')['images']
assert len(viewed)==68==len({item['path'] for item in viewed})
view_map={Path(item['path']).resolve():item for item in viewed}
sources=read(REPORT/'source-pins-before.json')
source_pins=[]
for item in sources['files']:
    assert item['path'].startswith('sources/')
    path=(CAPSULE/item['path']).resolve(); assert path.is_relative_to(CAPSULE/'sources')
    assert sha(path)==item['sha256']
    source_pins.append({**item,'currentSha256':sha(path),'status':'UNCHANGED'})
assert len(source_pins)==32
preparation=read(REPORT/'preparation-validation.json')
launch_pins=[]
for item in preparation['pins']:
    path=local(item['path']); current=sha(path); assert current==item['sha256']
    launch_pins.append({**item,'currentSha256':current,'status':'UNCHANGED'})
cross=read(REPORT/'source-native-crosschecks.json')
reference_checks=[]
documents=[]; all_pins=[]; expected_png=set(); image_evidence=[]
for stem,document_id,count in [('student-search','SM-DET-STUDENT-SEARCH',29),('student-editor','SM-DET-STUDENT-EDITOR',39)]:
    record=read(REPORT/(stem+'-frozen-inputs.json'))
    for item in record['pins']:
        source=local(item['sourcePath']); frozen=local(item['frozenPath'])
        assert sha(source)==sha(frozen)==item['sha256']==item['sourceBefore']==item['sourceAfter']
        all_pins.append({**item,'sourceFinalSha256':sha(source),'frozenFinalSha256':sha(frozen),'status':'UNCHANGED'})
    directory=REPORT/'frozen'/stem
    manifest=read(directory/'manifest.json'); draft=read(directory/'draft-result.json')
    md=directory/(stem+'.md'); content=md.read_text(encoding='utf-8')
    assert sha(md)==manifest['sourceSha256']==draft['contentSha256']
    assert draft['documentId']==document_id and draft['aiAuthored'] is True
    assert draft['semanticProseAssembledByPython'] is False and manifest['originalModified'] is False
    findings=validation.validate_document(content,'spec/detail/'+stem+'.md',expected_document_id=document_id)
    assert not findings, findings
    review=read(REPORT/(stem+'-review.json')); Draft202012Validator(schema.REVIEW).validate(review)
    assert review['documentId']==document_id and review['approved'] is True and not review['findings']
    pngs=[]
    for category in ['layouts','diagrams']:
        for item in manifest[category]:
            pngs.append((category,item['id']+'.png',item['png'],item.get('sourceLines')))
    for item in manifest['display']['documentCapture']['pages']:
        pngs.append(('whole-document-tiles',item['path'],item['png'],item['sourceRectangle']))
    assert len(pngs)==count
    for category,name,png,position in pngs:
        path=(directory/name).resolve(); expected_png.add(path)
        assert sha(path)==png['sha256'] and path in view_map
        original=next(item for item in record['pins'] if local(item['frozenPath'])==path)
        image_evidence.append({'documentId':document_id,'category':category,'sourcePath':original['sourcePath'],'frozenPath':original['frozenPath'],'sha256':png['sha256'],'width':png['width'],'height':png['height'],'sourcePosition':position,**view_map[path]})
    documents.append({'documentId':document_id,'version':'5.0','canonicalPath':manifest['source'],'frozenPath':str(md),'mdSha256':sha(md),'draftResultSha256':sha(directory/'draft-result.json'),'canonicalManifestSha256':sha(directory/'manifest.json'),'reviewPath':str(REPORT/(stem+'-review.json')),'reviewSha256':sha(REPORT/(stem+'-review.json')),'boundedApproved':True,'findings':0,'imagesActuallyViewed':count,'diagramCount':len(manifest['diagrams']),'layoutCount':len(manifest['layouts']),'wholeDocumentTiles':len(manifest['display']['documentCapture']['pages']),'structureStatus':manifest['structure']['status'],'displayStatus':manifest['display']['status']})
    for item in cross['observations']:
        if item['documentId']!=document_id: continue
        assert item['references'] and all(1<=start<=end<=len(content.splitlines()) for start,end in item['documentRanges'])
        assert all((directory/name).resolve() in expected_png for name in item['images'])
        for ref in item['references']:
            assert ref['path'].startswith('sources/')
            path=(CAPSULE/ref['path']).resolve(); assert path.is_relative_to(CAPSULE/'sources')
            line_count=len(path.read_text(encoding='utf-8-sig').splitlines())
            assert 1<=ref['startLine']<=ref['endLine']<=line_count
            reference_checks.append({**ref,'sha256':sha(path),'lineCount':line_count,'observationId':item['id']})
assert expected_png==set(view_map)
html=BeautifulSoup((REPORT/'frozen/student-editor/document.html').read_text(encoding='utf-8'),'html.parser')
tx_table=next(table for table in html.find_all('table') if any('到達するcatch' in cell.get_text() for cell in table.find_all('th')))
tx_rows=[[cell.get_text(' ',strip=True) for cell in row.find_all(['th','td'],recursive=False)] for row in tx_table.find_all('tr')]
assert len(tx_rows)==6 and all(len(row)==3 and all(row) for row in tx_rows)
protected=read(REPORT.parent/'focus-protected-check-05-final.json')
assert protected['total']==protected['unchanged']==179 and protected['changed']==protected['missing']==0
manifest={'schema':'reverse-bounded-source-native-review-manifest/1','round':5,'finalizedAt':datetime.now(timezone.utc).isoformat(),'projectId':'test-project1','profile':'CSharp_ASPNET','snapshot':str(CAPSULE),'capsuleSchema':'reverse-ai-source-capsule/1','referenceMode':'training-assisted','snapshotScope':'legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest','capsuleManifestSha256':sha(CAPSULE/'manifest.json'),'reviewScope':'bounded-independent-source-and-actual-native-PNG','reviewArtifactShape':'frozen schemas.REVIEW, with independent bounded verdict semantics','unresolvedArraySemantics':'scope/preserve/unknown annotations; these are neither open questions nor confirmed major defects within the bounded approval','workflowTextApprovalGuardApplied':False,'workflowTextReviewUnresolvedGuardUnchanged':True,'notEquivalentToCliTextScopeApproval':True,'notAnOverallPass':True,'formalSemanticGradingPerformed':False,'referenceDesignSemanticComparisonPerformed':False,'sourceApplicationExecuted':False,'gradeExpectationsRead':False,'oldApprovalReused':False,'imagesActuallyViewed':68,'allCurrentPngFilesActuallyViewed':True,'visualFidelityVerdict':'APPROVED_ONLY_WITHIN_EXPLICIT_GENERATED_STATIC_PNG_AND_SOURCE_COMPARISON_SCOPE','unassessedScopes':['Unrendered full conditional mode compositions and dynamic school data','Viewport <=760 and print/accessibility','Actual browser DOM interaction and MVC/CSRF/auth binding','DB deployment/data and cancellation/concurrency/commit/rollback execution','Response delivery after state/write/Flash changes','Reference-design comparative section semantic verification','Formal complete semantic scoring and customer approval'],'documents':documents,'sourceHashesUnchanged':32,'completedArtifactPinsUnchanged':len(all_pins),'launchAndPreparationPinsUnchanged':len(launch_pins),'protectedOriginalPinsShaOnlyUnchanged':179,'images':image_evidence,'inputPins':all_pins,'sourcePins':source_pins,'launchPreparationPins':launch_pins}
save(REPORT/'review-manifest.json',manifest)
save(REPORT/'verification.json',{'schema':'reverse-bounded-native-review-verification/1','checkedAt':datetime.now(timezone.utc).isoformat(),'round':5,'status':'PASS_METADATA_STRUCTURE_AND_INTEGRITY_ONLY','reviewJsonSchemaValidated':2,'frozenValidatorDocumentIdAndStructureValidated':2,'sourceReferenceRangesValidated':len(reference_checks),'crosscheckObservations':len(cross['observations']),'exactViewedCoverage':{'search':29,'editor':39,'total':68},'sourcePinsUnchanged':32,'completedArtifactPinsUnchanged':len(all_pins),'launchPreparationPinsUnchanged':len(launch_pins),'protected179ShaOnlyUnchanged':True,'productionSourceModified':False,'specMarkdownModified':False,'AIOrRenderingStarted':False,'formalSemanticScoringPerformed':False,'txRenderedTableCells':tx_rows,'referenceChecks':reference_checks,'reviewManifestSha256':sha(REPORT/'review-manifest.json'),'protectedFinalSha256':sha(REPORT.parent/'focus-protected-check-05-final.json')})
print(json.dumps({'sourcePinsUnchanged':32,'completedArtifactPinsUnchanged':len(all_pins),'launchPreparationPinsUnchanged':len(launch_pins),'actualPngViewed':68,'sourceReferenceRangesValidated':len(reference_checks),'protectedShaOnlyUnchanged':179,'overallPassClaimed':False}))
