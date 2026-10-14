"""Record four already viewed state images without approving unfinished diagrams."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from contextbase.ai import capsule

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
repo = agent.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(path, value):
    if path.exists():
        raise FileExistsError(str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

pin_path = report/'training-assisted/state-basic-registration-r05-v02-root-normalized-pin.json'
if sha(pin_path) != 'a5294c3eb62be8dd1eeeb93d6a7382e1706d005c2b24cbdb3d65f373a8fe0737':
    raise ValueError('Reviewed state pin changed')
pin = load(pin_path)
capture_path = report/'render/assisted-registration-basic-r05-state-r02/capture.json'
capture = load(capture_path)
if (pin['independentReviewApproved'] is not True or pin['findings'] or pin['unresolved'] or
    capture['exportPinSha256'] != sha(pin_path) or capture['documentSha256'] != pin['parentSha256'] or
    capture['externalRequests'] or capture['javaScriptEnabled'] is not False or
    capture['inputHashesUnchanged'] is not True or sha(Path(pin['canonicalMarkdown'])) != pin['parentSha256']):
    raise ValueError('Exact approved static state projection required')
for path_key, hash_key in (('projectionFile','projectionSha256'), ('independentReview','independentReviewSha256'),
                          ('originalPin','originalPinSha256'), ('result','resultSha256')):
    if sha(Path(pin[path_key])) != pin[hash_key]:
        raise ValueError('State evidence changed')
manifest = capsule.verify(agent/'.tmp/20261013-rerun-12h/training-assisted/snapshot')
source_hashes = {f['path']:f['sha256'] for f in manifest['files']}
resources = []
for relative in ('Views/Students/Edit.cshtml','wwwroot/css/site.css'):
    path = repo/'test-project1/srcs/CSharp_ASPNET'/relative
    if sha(path) != source_hashes[relative]:
        raise ValueError('Actually read original source changed')
    resources.append({'path':str(path),'sha256':sha(path),'actuallyRead':True})
images = []
for entry in capture['images']:
    for path_key, hash_key in (('path','sha256'), ('aiHtmlPath','aiHtmlSha256'), ('sanitizedHtmlPath','sanitizedHtmlSha256')):
        if sha(Path(entry[path_key])) != entry[hash_key]:
            raise ValueError('Actually viewed state image or HTML changed')
    if entry['sanitizerRemoved'] or not entry['textAndControlStructureUnchanged']:
        raise ValueError('Projection structure changed')
    images.append({**entry,'actuallyReviewed':True})
if len(images) != 4 or {e['stateId'] for e in images} != {'initial','normal','error','view-edit'}:
    raise ValueError('Four distinct actually viewed states required')
target = report/'visual-review/assisted-registration-basic-r05-states-root-native-r01.json'
created = datetime.now(timezone.utc).isoformat()
record = {'schema':'reverse-agent-native-visual-review/1','reviewedAt':created,'reviewer':'/root',
    'documentId':pin['documentId'],'canonicalDocumentPath':pin['canonicalMarkdown'],
    'documentSha256':pin['parentSha256'],'referenceMode':'training-assisted',
    'sourceSnapshotSha256':pin['capsuleManifestSha256'],'reviewScope':'FOUR_STATIC_STATES_ONLY',
    'approved':True,'stateOnlyApproved':True,'completeDocumentVisualReview':False,
    'reviewedImages':images,'reviewedSourceResources':resources,
    'priorSharedResourceReview':'visual-review/assisted-search-basic-r04-states-root-native-r01.json',
    'modesReviewed':['initial','normal','error','view-edit'],
    'independentMeaningReviewSha256':pin['independentReviewSha256'],
    'projectionSha256':pin['projectionSha256'],'captureReceiptSha256':sha(capture_path),
    'findings':[],
    'checks':['All four complete state PNGs were actually viewed at original size by root.',
        'Field labels, era inputs, role-dependent controls, confirmation table and actions are readable without clipping or overlap.',
        'The error capture represents ConfirmationRequired, as labelled; it is not evidence of a validation-error or HTTP-error state.',
        'Edit.cshtml and site.css were read as source text and bound to the sealed capsule.'],
    'limitations':['Static offline projection with labelled demonstration values.',
        'Razor, original JavaScript, SQL and the application were not executed; runtime pixel equivalence is unavailable.',
        'Diagram review is incomplete: r16 rejected 22 valid dotted-link diagrams, pending the separately tested renderer correction.'],
    'fourStateMeaningReviewComplete':True,'originalApplicationExecuted':False,
    'pixelEquivalenceToRunningApplicationVerified':False,'formalQualityGatePassed':False,
    'finalQualified':False,'published':False}
fresh(target,record)
manifest_path = report/'run-manifest.json'
run = load(manifest_path)
if run['nativeVisualReview']['imagesActuallyReviewed'] != 99:
    raise ValueError('Root prior actual-view count differs')
fresh(report/'checkpoints/run-manifest-before-registration-state-native-r01.json',run)
run['nativeVisualReview']['records'].append(target.relative_to(report).as_posix())
run['nativeVisualReview'].update(imagesActuallyReviewed=103,approved=False)
run['screenStateReviewProgress'].update(trainingAssistedBasicRegistration=target.relative_to(report).as_posix(),
    completedScreenDocuments=2,wholeSetComplete=False,
    completionScope='Independent four-state meaning and static native review; not whole-document qualification')
run['updatedAt']=created
manifest_path.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':str(target),'sha256':sha(target),'rootActualImagesViewed':103,'wholeDocumentApproved':False}))
