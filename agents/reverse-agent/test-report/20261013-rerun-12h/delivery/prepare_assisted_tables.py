"""Pin two authorized assisted TABLE manuscripts and their immutable renders."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
from PIL import Image, ImageChops
from delivery_model import load_bound, safe_path, sha

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
REPORT=ROOT.parent
BASE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
MDROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
CAP='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CASES=[
    ('03_m_code_category','batch-01','assisted-m-code-category-r01',
     'abf9dfb20de0e68223d75ace8f9fdb78fa6069b470c2265c5c7d18404246cd06',
     'batch-01/2152d5f7e821bc29','batch-01/2152d5f7e821bc29/independent-review'),
    ('02_m_class','revision-pending-r02-ba83a6b83f9065e3','assisted-m-class-r02',
     '713c201ef07b7b815fcae3b19468990097d3feca39da9263910272c1570b9384',
     'revision-pending-r02-ba83a6b83f9065e3','revision-pending-r02-ba83a6b83f9065e3-independent-review'),
]
def read(path):return json.loads(safe_path(path).read_bytes())
def digest(path):return sha(safe_path(path).read_bytes())
def fresh(path,value):
    if path.exists():raise FileExistsError('Fresh preparation required')
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    binding_path=ROOT/'binding-assisted-tables-r01.json';qa_dir=ROOT/'html-assisted-tables-r01'
    if binding_path.exists() or qa_dir.exists():raise FileExistsError('Fresh preparation required')
    documents=[];qa_docs=[]
    for stem,batch,render_name,expected,job_name,review_name in CASES:
        canonical='基本設計書/テーブル/'+stem+'.md'
        md=safe_path(MDROOT/batch/canonical);render=safe_path(REPORT/'render'/render_name)
        pins=read(render/'render-pins.json');draft_path=BASE/'jobs'/job_name/'draft-result.json';draft=read(draft_path)
        review_path=BASE/'jobs'/review_name/'review-verified.json';handoff_path=review_path.with_name('review-handoff.json');handoff=read(handoff_path)
        assert digest(md)==pins['sourceSha256']==draft['contentSha256']==handoff['documentSha256']==expected
        assert pins['sourceSnapshotManifestSha256']==draft['snapshot']['manifestSha256']==handoff['snapshot']['manifestSha256']==CAP
        assert pins['referenceMode']==draft['referenceMode']==handoff['referenceMode']=='training-assisted'
        assert pins['documentId']==draft['documentId'] and pins['canonicalDocumentPath']==canonical==draft['path']
        assert draft['aiAuthored'] is True and draft['semanticProseAssembledByPython'] is False
        assert handoff['approved'] is True and handoff['reviewSha256']==digest(review_path)
        assert safe_path(handoff['documentFile'])==md
        assert digest(draft_path)==pins['draftResultSha256']
        doc={'documentId':pins['documentId'],'canonicalDocumentPath':canonical,'markdown':str(md),'markdownSha256':expected,
             'renderDirectory':str(render),'renderPinsSha256':digest(render/'render-pins.json'),'renderManifestSha256':digest(render/'manifest.json'),
             'draftResult':str(draft_path),'draftResultSha256':digest(draft_path),
             'separateApprovedReview':{'handoff':str(handoff_path),'handoffSha256':digest(handoff_path),'review':str(review_path),'reviewSha256':digest(review_path),'approved':True,
                                       'scope':'text-source-and-structure; no original rubric or runtime review'}}
        documents.append(doc)
        qa_docs.append({'documentId':doc['documentId'],'canonicalDocumentPath':canonical,'markdownSha256':expected,
                        'canonicalHtmlSha256':pins['canonicalHtmlSha256'],'renderDocumentPngSha256':digest(render/'document.png'),
                        'crops':[],'visualReview':'PENDING','formalQualityGatePassed':False,'published':False})
    binding={'schema':'reverse-agent-delivery-binding/1','referenceMode':'training-assisted','permittedMarkdownRoot':str(MDROOT),
             'permittedRenderRoot':str(REPORT/'render'),'sourceSnapshotManifestSha256':CAP,'formalQualityGatePassed':False,'documents':documents}
    fresh(binding_path,binding);load_bound(binding_path)
    qa_dir.mkdir()
    for document,record in zip(documents,qa_docs,strict=True):
        png=Path(document['renderDirectory'])/'document.png';target=qa_dir/Path(document['canonicalDocumentPath']).stem;target.mkdir()
        with Image.open(png) as image:
            record['dimensions']=list(image.size);end=0
            for ordinal,y in enumerate(range(0,image.height,1120),1):
                box=(0,y,image.width,min(y+1200,image.height));crop=target/f'document-{ordinal:03d}.png';image.crop(box).save(crop)
                with Image.open(crop) as rendered:assert ImageChops.difference(image.crop(box),rendered).getbbox() is None
                assert y<=end;end=max(end,box[3])
                record['crops'].append({'path':str(crop),'sha256':digest(crop),'sourceRectangle':list(box),
                                        'sourcePngSha256':digest(png),'overlapPixels':80,'actuallyViewed':False})
            assert end==image.height
            record['cropFullCanvasCoverage']=True;record['cropPixelEquality']=True
    record={'schema':'reverse-agent-table-html-preparation/1','createdUtc':datetime.now(timezone.utc).isoformat(),
            'binding':str(binding_path),'bindingSha256':digest(binding_path),'referenceMode':'training-assisted','sourceSnapshotManifestSha256':CAP,
            'rendererCoreAtPreparationSha256':digest(REPO/'agents/reverse-agent/src/contextbase/ai/rendering.py'),
            'rootReportedRendererRevision':'r12','rootReportedFullTests':337,
            'r12TestRecord':str(REPORT/'engine/all-ai-r12-result.json'),'r12TestRecordSha256':digest(REPORT/'engine/all-ai-r12-result.json'),
            'originalsModified':False,'specAndSpecEvalRead':False,'applicationExecuted':False,
            'visualReview':'PENDING','formalQualityGatePassed':False,'published':False,'documents':qa_docs}
    fresh(qa_dir/'qa.json',record)
    print(json.dumps({'binding':str(binding_path),'bindingSha256':digest(binding_path),'documents':len(documents),'htmlCropCount':sum(len(d['crops']) for d in qa_docs)},ensure_ascii=False))

if __name__=='__main__':main()
