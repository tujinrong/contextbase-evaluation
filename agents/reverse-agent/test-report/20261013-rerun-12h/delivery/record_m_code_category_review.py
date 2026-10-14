"""Attach completed layout observations to derivative candidate manifests."""
import json
from pathlib import Path
from delivery_model import sha

root=Path(__file__).resolve().parent
report=root/'m-code-category-delivery-r05-qa.json'
record=json.loads(report.read_bytes())
assert record['status']=='PASS_DERIVATIVE_FORMAT_CANDIDATE_ONLY'
assert record['pdf']['actuallyViewedPages']==list(range(1,11))
assert record['xlsx']['actuallyViewedTiles']==5
assert len(record['rendererR10']['actuallyViewedCrops'])==5
for folder,status,visual in [
    ('pdf-m-code-category-r05','TEXT_AND_LAYOUT_VERIFIED_CANDIDATE_ONLY','PASS_DERIVATIVE_LAYOUT'),
    ('xlsx-m-code-category-r05','CELLS_AND_NATIVE_LAYOUT_VERIFIED_CANDIDATE_ONLY','PASS_NATIVE_DERIVATIVE_LAYOUT')]:
    path=root/folder/'delivery-manifest.json'
    backup=path.with_name('delivery-manifest.before-visual-review.json')
    if backup.exists():raise FileExistsError('Review transition already recorded')
    raw=path.read_bytes();manifest=json.loads(raw);backup.write_bytes(raw)
    manifest.update(status=status,visualReview=visual,published=False,formalQualityGatePassed=False,
                    converterQaCandidate=True,formalScoring='PENDING_ROOT_PROCESS',
                    visualReviewReport=str(report),visualReviewReportSha256=sha(report.read_bytes()))
    for document in manifest['documents']:
        document['visualReview']=visual
        if 'readbackChecks' in document:document['readbackChecks']['visualReview']=visual
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'candidate':folder,'status':status,'manifestSha256':sha(path.read_bytes())}))
path=root/'html-m-code-category-r04/qa.json'
assert (path.parent/'qa.before-visual-review.json').read_bytes()==path.read_bytes()
html=json.loads(path.read_bytes())
html.update(visualReview='PASS_DERIVATIVE_LAYOUT',visualReviewReport=str(report),
            visualReviewReportSha256=sha(report.read_bytes()))
html['crops']=record['rendererR10']['actuallyViewedCrops']
path.write_text(json.dumps(html,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
