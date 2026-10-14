"""Record two actually viewed synthetic images, without business approval."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json
from PIL import Image

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(p,obj):
    if p.exists(): raise FileExistsError(str(p))
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
root=agent/'.tmp/publication-r19-root-r02/node-token-positive'
images=[]
for name in ('diagram-001.png','document.png'):
    p=root/name
    with Image.open(p) as im: size=list(im.size)
    images.append({'path':str(p),'sha256':sha(p),'size':size,'detail':'original',
        'actuallyViewed':True,'reviewer':'/root','blockingFindings':[]})
log=report/'engine/all-ai-r19-root-r02.log'
if 'Ran 452 tests in 292.299s\n\nOK' not in log.read_text(encoding='utf-8-sig'):
    raise ValueError('Full suite proof differs')
native={'schema':'root-generic-native-review/1','scope':'SYNTHETIC_RENDERING_ONLY',
    'createdAt':datetime.now(timezone.utc).isoformat(),'images':images,
    'findings':'Alpha Beta, 400, 422, and ModelState are readable and whole; authored two rows, arrow, and terminal remain clear.',
    'testLogSha256':sha(log),'specificationQualityApproved':False,'businessSourceExecuted':False,
    'fourStateScreenDocumentCountChanged':False}
fresh(report/'engine/r19-root-synthetic-native-r01.json',native)
manifest_path=report/'run-manifest.json'
manifest=load(manifest_path)
old=manifest['nativeVisualReview']['imagesActuallyReviewed']
if old!=107: raise ValueError('Historical actual image count changed')
fresh(report/'checkpoints/run-manifest-before-r19-root-native-r01.json',manifest)
manifest['nativeVisualReview']['imagesActuallyReviewed']=109
manifest['nativeVisualReview']['latestSyntheticReview']='engine/r19-root-synthetic-native-r01.json'
manifest['protectedInputVerification']='checkpoints/protected-inputs-07.json'
manifest['updatedAt']=datetime.now(timezone.utc).isoformat()
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actualRootHistoricalImageCount':109,'reviewSha256':sha(report/'engine/r19-root-synthetic-native-r01.json')}))
