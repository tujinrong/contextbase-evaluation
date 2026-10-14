"""Attach completed human/agent observations to derivative manifests only."""
import json
from pathlib import Path
from delivery_model import sha

root = Path(__file__).resolve().parent
report = root/'repair-qa-final-r09.json'
record = json.loads(report.read_bytes())
assert record['pdfVisualReviews'][1]['actuallyViewedPages'] == list(range(1,107))
assert record['xlsxReview']['tilesActuallyViewed'] == 42
for candidate, status, visual in [
    ('pdf-search-basic-r08','TEXT_VERIFIED_VISUAL_REVIEW_FAILED','FAIL_FOR_PUBLICATION'),
    ('pdf-search-basic-r09','TEXT_VERIFIED_VISUAL_REVIEW_FAILED','FAIL_FOR_PUBLICATION'),
    ('xlsx-search-basic-r04','MECHANICALLY_VERIFIED_VISUAL_REVIEW_REQUIRED','REVIEW_REQUIRED')]:
    path = root/candidate/'delivery-manifest.json'
    backup = path.with_name('delivery-manifest.before-visual-review.json')
    if backup.exists():
        raise FileExistsError('Visual review transition already recorded')
    raw = path.read_bytes()
    manifest = json.loads(raw)
    backup.write_bytes(raw)
    manifest.update(status=status, visualReview=visual, published=False, formalQualityGatePassed=False,
                    sourceCandidateFinalFormat='FAILED', converterQaCandidate=True,
                    visualReviewReport=str(report), visualReviewReportSha256=sha(report.read_bytes()))
    for document in manifest['documents']:
        document.update(visualReview=visual, semanticApproval=False)
        if 'readbackChecks' in document:
            document['readbackChecks']['visualReview'] = visual
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'candidate':candidate,'status':status,'manifestSha256':sha(path.read_bytes())},ensure_ascii=False))
