"""Record actual root inspections and their unchanged source/canonical bindings."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from contextbase.ai import capsule

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
repo=agent.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
created=datetime.now(timezone.utc).isoformat()
pin_path=report/'training-assisted/state-basic-search-r04-v03-review-export-pin.json'
pin=load(pin_path)
capture_path=report/'render/assisted-search-basic-r04-state-r01/capture.json'
capture=load(capture_path)
diagrams_path=report/'visual-review/assisted-search-basic-r05-root-native.json'
diagrams=load(diagrams_path)
if (pin['independentReviewApproved'] is not True or pin['findings'] or pin['unresolved'] or
    capture['exportPinSha256']!=sha(pin_path) or capture['documentSha256']!=pin['parentSha256'] or
    capture['externalRequests'] or capture['javaScriptEnabled'] is not False or
    diagrams['displayStatus']!='DISPLAY_READABILITY_PASS' or not diagrams['coverageComplete'] or
    diagrams['documentSha256']!=pin['parentSha256'] or
    sha(Path(pin['canonicalMarkdown']))!=pin['parentSha256']):
    raise ValueError('An exact approved meaning, static capture, and complete prior diagram review are required')
snapshot=agent/'.tmp/20261013-rerun-12h/training-assisted/snapshot'
manifest=capsule.verify(snapshot)
if sha(snapshot/'manifest.json')!=pin['capsuleManifestSha256']:
    raise ValueError('Fixed snapshot changed')
source_hashes={f['path']:f['sha256'] for f in manifest['files']}
resources=[]
for relative in ('Views/Students/Search.cshtml','Views/Shared/_Layout.cshtml',
                 'Views/Shared/_MessagePanel.cshtml','wwwroot/css/site.css','wwwroot/js/site.js'):
    path=repo/'test-project1/srcs/CSharp_ASPNET'/relative
    if sha(path)!=source_hashes[relative]:
        raise ValueError('Actually read source resource changed')
    resources.append({'path':str(path),'sha256':sha(path),'actuallyRead':True})
images=[]
for entry in diagrams['reviewedImages']:
    if entry['actuallyReviewed'] is not True or sha(Path(entry['path']))!=entry['sha256']:
        raise ValueError('Previously actually reviewed diagram image changed')
    images.append(entry)
for entry in capture['images']:
    if sha(Path(entry['path']))!=entry['sha256'] or entry['sanitizerRemoved'] or not entry['textAndControlStructureUnchanged']:
        raise ValueError('Actually viewed state image changed')
    images.append({**entry,'actuallyReviewed':True})
assert {e['stateId'] for e in capture['images']}=={'initial','normal','error','view-edit'}
target=report/'visual-review/assisted-search-basic-r04-states-root-native-r01.json'
if target.exists():
    raise FileExistsError('Fresh immutable actual inspection record required')
record={'schema':'reverse-agent-native-visual-review/1','reviewedAt':created,'reviewer':'/root',
    'documentId':pin['documentId'],'canonicalDocumentPath':pin['canonicalMarkdown'],
    'documentSha256':pin['parentSha256'],'referenceMode':'training-assisted',
    'sourceSnapshotSha256':pin['capsuleManifestSha256'],'reviewScope':'STATIC_PROJECTION_VS_SOURCE_RESOURCES',
    'approved':True,'reviewedImages':images,'reviewedSourceResources':resources,
    'modesReviewed':['initial','normal','error','view-edit','empty','tooMany','viewer'],
    'independentMeaningReviewSha256':pin['independentReviewSha256'],
    'projectionSha256':pin['projectionSha256'],'captureReceiptSha256':sha(capture_path),
    'inheritedDiagramReviewSha256':sha(diagrams_path),'findings':[],
    'checks':['All four complete state PNGs actually viewed at original size.',
        'Fields, eleven result columns, condition grouping, disabled controls, role-dependent links, status/era display, warning/error panels, and pager remain readable.',
        'Empty and tooMany are separately labelled comparison panels in normal.png, rather than claims of simultaneous application output.',
        'CSS, shared layout/message panel, view branches, and unassigned-field JavaScript were read as text and bound to the fixed source capsule.',
        'No clipped labels, lost columns, text overlaps, or unreadable state controls were found in this capture set.'],
    'limitations':['Static offline projection only; invented demonstration values are explicitly labelled.',
        'No original application, Razor engine, JavaScript, SQL, or HTTP request was executed.',
        'Razor/TagHelper runtime output and pixel equivalence to a running application remain unavailable.',
        'Additional note panels and nonexecuting route metadata disclose projection assumptions.'],
    'fourStateMeaningReviewComplete':True,'originalApplicationExecuted':False,
    'pixelEquivalenceToRunningApplicationVerified':False,'formalQualityGatePassed':False,
    'finalQualified':False,'published':False}
target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest_path=report/'run-manifest.json'
run=load(manifest_path)
before=report/'checkpoints/run-manifest-before-search-state-native-r01.json'
if before.exists():
    raise FileExistsError('Manifest checkpoint already exists')
before.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
run['nativeVisualReview']['records'].append(target.relative_to(report).as_posix())
run['nativeVisualReview'].update(imagesActuallyReviewed=97,approved=False)
run['updatedAt']=created
run['screenStateReviewProgress']={'trainingAssistedBasicSearch':target.relative_to(report).as_posix(),
    'completedScreenDocuments':1,'requiredScreenDocumentsPerMode':4,'wholeSetComplete':False}
manifest_path.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':str(target),'sha256':sha(target),'reviewedStateImages':4,
    'rootActualImagesViewed':97,'finalQualified':False}))
